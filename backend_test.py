#!/usr/bin/env python3
"""
Backend Testing Suite for PDF Intelligence System
Tests all API endpoints and core functionality
"""

import requests
import json
import time
import os
from pathlib import Path
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

# Backend URL from environment
BACKEND_URL = "https://eeeb658f-5f92-4c32-9db3-27e8a20bce60.preview.emergentagent.com/api"

class PDFTestGenerator:
    """Generate test PDF files for testing"""
    
    def create_simple_pdf(self, filename: str, title: str, headings: list) -> str:
        """Create a simple PDF with title and headings"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        title_style = styles['Title']
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Add headings and content
        for i, heading in enumerate(headings):
            # Add heading
            heading_style = styles['Heading1'] if i % 3 == 0 else styles['Heading2']
            story.append(Paragraph(heading, heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Add some content
            content = f"This is the content for section '{heading}'. It contains relevant information about the topic and provides detailed analysis and insights."
            story.append(Paragraph(content, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        doc.build(story)
        return filename
    
    def create_research_paper_pdf(self, filename: str) -> str:
        """Create a research paper style PDF"""
        headings = [
            "1. Introduction",
            "1.1 Background",
            "1.2 Problem Statement", 
            "2. Literature Review",
            "2.1 Previous Studies",
            "2.2 Research Gap",
            "3. Methodology",
            "3.1 Data Collection",
            "3.2 Analysis Methods",
            "4. Results",
            "4.1 Findings",
            "4.2 Statistical Analysis",
            "5. Discussion",
            "6. Conclusion"
        ]
        return self.create_simple_pdf(filename, "Advanced Machine Learning Research Paper", headings)
    
    def create_business_report_pdf(self, filename: str) -> str:
        """Create a business report style PDF"""
        headings = [
            "Executive Summary",
            "1. Market Analysis",
            "1.1 Revenue Trends",
            "1.2 Growth Projections",
            "2. Financial Performance",
            "2.1 Quarterly Results",
            "2.2 Investment Returns",
            "3. Strategic Recommendations",
            "3.1 Implementation Plan",
            "3.2 Risk Assessment",
            "4. Conclusion"
        ]
        return self.create_simple_pdf(filename, "Q4 2024 Business Performance Report", headings)
    
    def create_technical_manual_pdf(self, filename: str) -> str:
        """Create a technical manual style PDF"""
        headings = [
            "Overview",
            "1. System Architecture",
            "1.1 Components",
            "1.2 Data Flow",
            "2. Installation Guide",
            "2.1 Prerequisites",
            "2.2 Setup Instructions",
            "3. Configuration",
            "3.1 Basic Settings",
            "3.2 Advanced Options",
            "4. Troubleshooting",
            "5. API Reference"
        ]
        return self.create_simple_pdf(filename, "Technical Documentation v2.1", headings)

class BackendTester:
    """Main testing class for backend API endpoints"""
    
    def __init__(self):
        self.base_url = BACKEND_URL
        self.pdf_generator = PDFTestGenerator()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Root Endpoint", True, f"Message: {data.get('message')}")
                return True
            else:
                self.log_test("Root Endpoint", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_single_pdf_analysis(self):
        """Test single PDF analysis endpoint"""
        try:
            # Create test PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                pdf_path = self.pdf_generator.create_research_paper_pdf(tmp_file.name)
            
            # Test the API
            with open(pdf_path, 'rb') as pdf_file:
                files = {'file': ('test_research.pdf', pdf_file, 'application/pdf')}
                response = requests.post(f"{self.base_url}/analyze-pdf", files=files, timeout=30)
            
            # Clean up
            os.unlink(pdf_path)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ['id', 'title', 'headings', 'total_pages', 'processing_time']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Single PDF Analysis - Structure", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Validate headings structure
                if data['headings']:
                    heading = data['headings'][0]
                    heading_fields = ['text', 'level', 'page_number', 'confidence', 'position']
                    missing_heading_fields = [field for field in heading_fields if field not in heading]
                    
                    if missing_heading_fields:
                        self.log_test("Single PDF Analysis - Heading Structure", False, f"Missing heading fields: {missing_heading_fields}")
                        return False
                
                self.log_test("Single PDF Analysis", True, 
                            f"Title: {data['title'][:50]}..., Headings: {len(data['headings'])}, Pages: {data['total_pages']}, Time: {data['processing_time']:.2f}s")
                return True
            else:
                self.log_test("Single PDF Analysis", False, f"Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Single PDF Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_heading_detection_quality(self):
        """Test the quality of heading detection"""
        try:
            # Create test PDF with known headings
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                pdf_path = self.pdf_generator.create_research_paper_pdf(tmp_file.name)
            
            # Test the API
            with open(pdf_path, 'rb') as pdf_file:
                files = {'file': ('test_headings.pdf', pdf_file, 'application/pdf')}
                response = requests.post(f"{self.base_url}/analyze-pdf", files=files, timeout=30)
            
            # Clean up
            os.unlink(pdf_path)
            
            if response.status_code == 200:
                data = response.json()
                headings = data['headings']
                
                # Check if we detected reasonable number of headings
                if len(headings) < 3:
                    self.log_test("Heading Detection Quality", False, f"Too few headings detected: {len(headings)}")
                    return False
                
                # Check confidence scores
                low_confidence_count = sum(1 for h in headings if h['confidence'] < 0.4)
                if low_confidence_count > len(headings) * 0.5:
                    self.log_test("Heading Detection Quality", False, f"Too many low confidence headings: {low_confidence_count}/{len(headings)}")
                    return False
                
                # Check heading levels
                levels = [h['level'] for h in headings]
                if not any(level in [1, 2, 3] for level in levels):
                    self.log_test("Heading Detection Quality", False, f"Invalid heading levels: {set(levels)}")
                    return False
                
                self.log_test("Heading Detection Quality", True, 
                            f"Detected {len(headings)} headings with avg confidence: {sum(h['confidence'] for h in headings)/len(headings):.2f}")
                return True
            else:
                self.log_test("Heading Detection Quality", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Heading Detection Quality", False, f"Error: {str(e)}")
            return False
    
    def test_multi_pdf_analysis(self):
        """Test multi-PDF analysis endpoint"""
        try:
            # Create multiple test PDFs
            pdf_paths = []
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp1:
                pdf_paths.append(self.pdf_generator.create_research_paper_pdf(tmp1.name))
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp2:
                pdf_paths.append(self.pdf_generator.create_business_report_pdf(tmp2.name))
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp3:
                pdf_paths.append(self.pdf_generator.create_technical_manual_pdf(tmp3.name))
            
            # Prepare files for upload
            files = []
            file_handles = []
            for i, pdf_path in enumerate(pdf_paths):
                file_handle = open(pdf_path, 'rb')
                file_handles.append(file_handle)
                files.append(('files', (f'test_doc_{i+1}.pdf', file_handle, 'application/pdf')))
            
            # Test the API
            data = {
                'persona': 'PhD student',
                'job_to_be_done': 'write literature review'
            }
            
            response = requests.post(f"{self.base_url}/analyze-multiple-pdfs", 
                                   files=files, data=data, timeout=60)
            
            # Clean up
            for file_handle in file_handles:
                file_handle.close()
            for pdf_path in pdf_paths:
                os.unlink(pdf_path)
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                required_fields = ['id', 'persona', 'job_to_be_done', 'relevant_sections', 'total_documents', 'processing_time']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_test("Multi-PDF Analysis - Structure", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Validate relevant sections structure
                if result['relevant_sections']:
                    section = result['relevant_sections'][0]
                    section_fields = ['document_name', 'section_title', 'page_number', 'importance_rank', 'relevance_score', 'key_text']
                    missing_section_fields = [field for field in section_fields if field not in section]
                    
                    if missing_section_fields:
                        self.log_test("Multi-PDF Analysis - Section Structure", False, f"Missing section fields: {missing_section_fields}")
                        return False
                
                self.log_test("Multi-PDF Analysis", True, 
                            f"Persona: {result['persona']}, Sections: {len(result['relevant_sections'])}, Docs: {result['total_documents']}, Time: {result['processing_time']:.2f}s")
                return True
            else:
                self.log_test("Multi-PDF Analysis", False, f"Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Multi-PDF Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_persona_based_ranking(self):
        """Test different persona and job combinations"""
        personas = ["PhD student", "investor", "researcher", "manager", "student"]
        jobs = ["write literature review", "analyze revenue trends", "prepare presentation", "conduct research"]
        
        success_count = 0
        total_tests = 0
        
        try:
            # Create test PDFs
            pdf_paths = []
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp1:
                pdf_paths.append(self.pdf_generator.create_research_paper_pdf(tmp1.name))
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp2:
                pdf_paths.append(self.pdf_generator.create_business_report_pdf(tmp2.name))
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp3:
                pdf_paths.append(self.pdf_generator.create_technical_manual_pdf(tmp3.name))
            
            # Test different combinations
            for persona in personas[:3]:  # Test first 3 personas
                for job in jobs[:2]:  # Test first 2 jobs
                    total_tests += 1
                    
                    # Prepare files for upload
                    files = []
                    file_handles = []
                    for i, pdf_path in enumerate(pdf_paths):
                        file_handle = open(pdf_path, 'rb')
                        file_handles.append(file_handle)
                        files.append(('files', (f'test_doc_{i+1}.pdf', file_handle, 'application/pdf')))
                    
                    # Test the API
                    data = {
                        'persona': persona,
                        'job_to_be_done': job
                    }
                    
                    response = requests.post(f"{self.base_url}/analyze-multiple-pdfs", 
                                           files=files, data=data, timeout=60)
                    
                    # Clean up file handles
                    for file_handle in file_handles:
                        file_handle.close()
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result['relevant_sections'] and len(result['relevant_sections']) > 0:
                            success_count += 1
                    
                    time.sleep(1)  # Brief pause between requests
            
            # Clean up PDF files
            for pdf_path in pdf_paths:
                os.unlink(pdf_path)
            
            success_rate = success_count / total_tests if total_tests > 0 else 0
            if success_rate >= 0.8:
                self.log_test("Persona-Based Ranking", True, f"Success rate: {success_rate:.1%} ({success_count}/{total_tests})")
                return True
            else:
                self.log_test("Persona-Based Ranking", False, f"Low success rate: {success_rate:.1%} ({success_count}/{total_tests})")
                return False
                
        except Exception as e:
            self.log_test("Persona-Based Ranking", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        try:
            # Test invalid file type
            files = {'file': ('test.txt', b'This is not a PDF', 'text/plain')}
            response = requests.post(f"{self.base_url}/analyze-pdf", files=files, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Error Handling - Invalid File Type", True, "Correctly rejected non-PDF file")
            else:
                self.log_test("Error Handling - Invalid File Type", False, f"Unexpected status: {response.status_code}")
                return False
            
            # Test multi-PDF with too few files
            files = [('files', ('test1.pdf', b'fake pdf content', 'application/pdf'))]
            data = {'persona': 'researcher', 'job_to_be_done': 'research'}
            response = requests.post(f"{self.base_url}/analyze-multiple-pdfs", files=files, data=data, timeout=10)
            
            if response.status_code == 400:
                self.log_test("Error Handling - Too Few Files", True, "Correctly rejected insufficient files")
            else:
                self.log_test("Error Handling - Too Few Files", False, f"Unexpected status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for PDF Intelligence System")
        print("=" * 60)
        
        # Basic connectivity tests
        print("\n📡 Testing Basic Connectivity...")
        self.test_health_endpoint()
        self.test_root_endpoint()
        
        # Core functionality tests
        print("\n📄 Testing PDF Processing...")
        self.test_single_pdf_analysis()
        self.test_heading_detection_quality()
        
        print("\n🧠 Testing Multi-PDF Intelligence...")
        self.test_multi_pdf_analysis()
        self.test_persona_based_ranking()
        
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)