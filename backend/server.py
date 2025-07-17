from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import json
import tempfile
import fitz  # PyMuPDF
import re
from collections import defaultdict
import numpy as np
from transformers import pipeline
import asyncio
from concurrent.futures import ThreadPoolExecutor


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="PDF Intelligence System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

# Global model cache
model_cache = {}

def get_heading_classifier():
    """Get or create heading classification model"""
    if 'heading_classifier' not in model_cache:
        # Using a lightweight model for heading classification
        model_cache['heading_classifier'] = pipeline(
            "text-classification",
            model="microsoft/DialoGPT-small",
            device=-1  # CPU only
        )
    return model_cache['heading_classifier']

# Define Models
class HeadingInfo(BaseModel):
    text: str
    level: int  # 1 for H1, 2 for H2, 3 for H3
    page_number: int
    confidence: float
    position: Dict[str, float]  # x, y coordinates

class PDFAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    headings: List[HeadingInfo]
    total_pages: int
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PersonaAnalysisRequest(BaseModel):
    persona: str  # e.g., "PhD student", "investor"
    job_to_be_done: str  # e.g., "write literature review", "analyze revenue trends"

class RelevantSection(BaseModel):
    document_name: str
    section_title: str
    page_number: int
    importance_rank: int
    relevance_score: float
    key_text: str

class MultiPDFAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    persona: str
    job_to_be_done: str
    relevant_sections: List[RelevantSection]
    total_documents: int
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PDFProcessor:
    def __init__(self):
        self.heading_patterns = [
            # Common heading patterns
            r'^\d+\.\s+[A-Z][^.]*$',  # 1. Introduction
            r'^[A-Z][^.]*:$',         # Introduction:
            r'^[A-Z\s]+$',            # ALL CAPS
            r'^\d+\.\d+\s+[A-Z][^.]*$',  # 1.1 Subsection
            r'^[IVX]+\.\s+[A-Z][^.]*$',  # I. Roman numerals
        ]
        
    def extract_text_with_formatting(self, pdf_path: str) -> List[Dict]:
        """Extract text with detailed formatting information"""
        doc = fitz.open(pdf_path)
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            page_data = {
                'page_number': page_num + 1,
                'blocks': []
            }
            
            for block in blocks['blocks']:
                if 'lines' in block:
                    for line in block['lines']:
                        for span in line['spans']:
                            text = span['text'].strip()
                            if text:
                                page_data['blocks'].append({
                                    'text': text,
                                    'font_size': span['size'],
                                    'font_flags': span['flags'],
                                    'font_name': span['font'],
                                    'bbox': span['bbox'],
                                    'color': span['color']
                                })
            
            pages_data.append(page_data)
        
        doc.close()
        return pages_data
    
    def detect_title(self, pages_data: List[Dict]) -> str:
        """Detect document title from first page"""
        if not pages_data:
            return "Untitled Document"
        
        first_page = pages_data[0]
        title_candidates = []
        
        for block in first_page['blocks']:
            # Look for large text at the top of the page
            if (block['font_size'] > 14 and 
                block['bbox'][1] < 200 and  # Top of page
                len(block['text']) > 10):
                title_candidates.append({
                    'text': block['text'],
                    'font_size': block['font_size'],
                    'y_position': block['bbox'][1]
                })
        
        if title_candidates:
            # Sort by font size and position
            title_candidates.sort(key=lambda x: (-x['font_size'], x['y_position']))
            return title_candidates[0]['text']
        
        return "Untitled Document"
    
    def is_heading_by_structure(self, text: str, font_size: float, 
                               avg_font_size: float, font_flags: int) -> tuple:
        """Determine if text is a heading based on structure analysis"""
        confidence = 0.0
        level = 0
        
        # Font size analysis
        if font_size > avg_font_size * 1.5:
            confidence += 0.3
            level = 1
        elif font_size > avg_font_size * 1.2:
            confidence += 0.2
            level = 2
        elif font_size > avg_font_size * 1.1:
            confidence += 0.1
            level = 3
        
        # Bold text (font flags)
        if font_flags & 2**4:  # Bold flag
            confidence += 0.2
        
        # Pattern matching
        for pattern in self.heading_patterns:
            if re.match(pattern, text):
                confidence += 0.3
                break
        
        # Text characteristics
        if len(text) < 100 and text.count('.') <= 1:
            confidence += 0.1
        
        # Position and formatting
        if text.isupper() and len(text) < 50:
            confidence += 0.2
        
        return confidence, level if level > 0 else 3
    
    def detect_headings(self, pages_data: List[Dict]) -> List[HeadingInfo]:
        """Detect headings using multi-signal approach"""
        headings = []
        
        # Calculate average font size
        all_font_sizes = []
        for page in pages_data:
            for block in page['blocks']:
                all_font_sizes.append(block['font_size'])
        
        avg_font_size = np.mean(all_font_sizes) if all_font_sizes else 12
        
        for page in pages_data:
            for block in page['blocks']:
                text = block['text'].strip()
                if len(text) < 5:  # Skip very short text
                    continue
                
                confidence, level = self.is_heading_by_structure(
                    text, block['font_size'], avg_font_size, block['font_flags']
                )
                
                if confidence > 0.4:  # Threshold for heading detection
                    headings.append(HeadingInfo(
                        text=text,
                        level=level,
                        page_number=page['page_number'],
                        confidence=confidence,
                        position={
                            'x': block['bbox'][0],
                            'y': block['bbox'][1],
                            'width': block['bbox'][2] - block['bbox'][0],
                            'height': block['bbox'][3] - block['bbox'][1]
                        }
                    ))
        
        # Sort by confidence and remove duplicates
        headings.sort(key=lambda x: (-x.confidence, x.page_number))
        
        # Remove near-duplicate headings
        filtered_headings = []
        for heading in headings:
            is_duplicate = False
            for existing in filtered_headings:
                if (heading.text.lower() == existing.text.lower() or
                    (abs(heading.position['y'] - existing.position['y']) < 10 and
                     heading.page_number == existing.page_number)):
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered_headings.append(heading)
        
        return filtered_headings[:50]  # Limit to 50 headings

class IntelligentAnalyzer:
    def __init__(self):
        self.persona_keywords = {
            "PhD student": ["research", "methodology", "literature", "analysis", "theory", "study"],
            "investor": ["revenue", "growth", "market", "financial", "investment", "returns"],
            "researcher": ["data", "results", "findings", "conclusion", "experiment", "hypothesis"],
            "manager": ["strategy", "performance", "objectives", "implementation", "management"],
            "student": ["introduction", "overview", "summary", "basics", "fundamentals"]
        }
        
        self.job_keywords = {
            "write literature review": ["related work", "previous studies", "research", "literature"],
            "analyze revenue trends": ["revenue", "sales", "growth", "financial", "trends"],
            "prepare presentation": ["summary", "key points", "overview", "highlights"],
            "conduct research": ["methodology", "data", "analysis", "findings", "results"]
        }
    
    def calculate_relevance_score(self, text: str, persona: str, job: str) -> float:
        """Calculate relevance score based on persona and job"""
        score = 0.0
        text_lower = text.lower()
        
        # Persona-based scoring
        persona_words = self.persona_keywords.get(persona.lower(), [])
        for word in persona_words:
            if word in text_lower:
                score += 0.2
        
        # Job-based scoring
        job_words = self.job_keywords.get(job.lower(), [])
        for word in job_words:
            if word in text_lower:
                score += 0.3
        
        # General relevance indicators
        if any(indicator in text_lower for indicator in ["conclusion", "summary", "results"]):
            score += 0.1
        
        return min(score, 1.0)
    
    def rank_sections(self, all_sections: List[Dict], persona: str, job: str) -> List[RelevantSection]:
        """Rank sections based on relevance to persona and job"""
        scored_sections = []
        
        for section in all_sections:
            relevance_score = self.calculate_relevance_score(
                section['text'], persona, job
            )
            
            if relevance_score > 0.1:  # Minimum relevance threshold
                scored_sections.append(RelevantSection(
                    document_name=section['document_name'],
                    section_title=section['text'][:100] + "..." if len(section['text']) > 100 else section['text'],
                    page_number=section['page_number'],
                    importance_rank=0,  # Will be set after sorting
                    relevance_score=relevance_score,
                    key_text=section['text'][:500] + "..." if len(section['text']) > 500 else section['text']
                ))
        
        # Sort by relevance score
        scored_sections.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Assign ranks
        for i, section in enumerate(scored_sections):
            section.importance_rank = i + 1
        
        return scored_sections[:20]  # Return top 20 sections

# Initialize processors
pdf_processor = PDFProcessor()
intelligent_analyzer = IntelligentAnalyzer()

# API Routes
@api_router.post("/analyze-pdf", response_model=PDFAnalysisResult)
async def analyze_single_pdf(file: UploadFile = File(...)):
    """Analyze a single PDF and extract headings"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    start_time = datetime.now()
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process PDF in thread pool
        loop = asyncio.get_event_loop()
        pages_data = await loop.run_in_executor(
            executor, pdf_processor.extract_text_with_formatting, tmp_file_path
        )
        
        # Extract title and headings
        title = pdf_processor.detect_title(pages_data)
        headings = pdf_processor.detect_headings(pages_data)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = PDFAnalysisResult(
            title=title,
            headings=headings,
            total_pages=len(pages_data),
            processing_time=processing_time
        )
        
        # Store in database
        await db.pdf_analyses.insert_one(result.dict())
        
        return result
        
    except Exception as e:
        # Clean up temp file on error
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@api_router.post("/analyze-multiple-pdfs", response_model=MultiPDFAnalysisResult)
async def analyze_multiple_pdfs(
    files: List[UploadFile] = File(...),
    persona: str = "researcher",
    job_to_be_done: str = "conduct research"
):
    """Analyze multiple PDFs with persona-based relevance ranking"""
    if len(files) < 3 or len(files) > 10:
        raise HTTPException(
            status_code=400, 
            detail="Please upload between 3 and 10 PDF files"
        )
    
    start_time = datetime.now()
    all_sections = []
    
    try:
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Process PDF in thread pool
            loop = asyncio.get_event_loop()
            pages_data = await loop.run_in_executor(
                executor, pdf_processor.extract_text_with_formatting, tmp_file_path
            )
            
            # Extract headings and convert to sections
            headings = pdf_processor.detect_headings(pages_data)
            
            for heading in headings:
                all_sections.append({
                    'document_name': file.filename,
                    'text': heading.text,
                    'page_number': heading.page_number,
                    'level': heading.level
                })
            
            # Clean up temp file
            os.unlink(tmp_file_path)
        
        # Rank sections based on persona and job
        relevant_sections = intelligent_analyzer.rank_sections(
            all_sections, persona, job_to_be_done
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = MultiPDFAnalysisResult(
            persona=persona,
            job_to_be_done=job_to_be_done,
            relevant_sections=relevant_sections,
            total_documents=len(files),
            processing_time=processing_time
        )
        
        # Store in database
        await db.multi_pdf_analyses.insert_one(result.dict())
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

@api_router.get("/")
async def root():
    return {"message": "PDF Intelligence System API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    executor.shutdown(wait=True)