#!/usr/bin/env python3
"""
Database Integration Test for PDF Intelligence System
"""

import pymongo
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

def test_database_integration():
    """Test MongoDB integration and data storage"""
    try:
        # Connect to MongoDB
        mongo_url = os.environ['MONGO_URL']
        db_name = os.environ['DB_NAME']
        
        client = pymongo.MongoClient(mongo_url)
        db = client[db_name]
        
        print("🔍 Testing Database Integration...")
        print("=" * 50)
        
        # Test connection
        try:
            client.admin.command('ping')
            print("✅ MongoDB connection successful")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
        
        # Check collections
        collections = db.list_collection_names()
        print(f"📁 Available collections: {collections}")
        
        # Check pdf_analyses collection
        pdf_analyses_count = db.pdf_analyses.count_documents({})
        print(f"📄 Single PDF analyses stored: {pdf_analyses_count}")
        
        if pdf_analyses_count > 0:
            # Show sample document
            sample_doc = db.pdf_analyses.find_one()
            print("📋 Sample PDF analysis document structure:")
            for key in sample_doc.keys():
                if key != '_id':
                    print(f"  - {key}: {type(sample_doc[key])}")
        
        # Check multi_pdf_analyses collection
        multi_pdf_analyses_count = db.multi_pdf_analyses.count_documents({})
        print(f"🧠 Multi-PDF analyses stored: {multi_pdf_analyses_count}")
        
        if multi_pdf_analyses_count > 0:
            # Show sample document
            sample_doc = db.multi_pdf_analyses.find_one()
            print("📋 Sample Multi-PDF analysis document structure:")
            for key in sample_doc.keys():
                if key != '_id':
                    print(f"  - {key}: {type(sample_doc[key])}")
        
        # Test data integrity
        if pdf_analyses_count > 0:
            # Check if documents have required fields
            required_fields = ['id', 'title', 'headings', 'total_pages', 'processing_time', 'timestamp']
            sample_doc = db.pdf_analyses.find_one()
            missing_fields = [field for field in required_fields if field not in sample_doc]
            
            if missing_fields:
                print(f"❌ Missing required fields in PDF analysis: {missing_fields}")
                return False
            else:
                print("✅ PDF analysis documents have all required fields")
        
        if multi_pdf_analyses_count > 0:
            # Check if documents have required fields
            required_fields = ['id', 'persona', 'job_to_be_done', 'relevant_sections', 'total_documents', 'processing_time', 'timestamp']
            sample_doc = db.multi_pdf_analyses.find_one()
            missing_fields = [field for field in required_fields if field not in sample_doc]
            
            if missing_fields:
                print(f"❌ Missing required fields in Multi-PDF analysis: {missing_fields}")
                return False
            else:
                print("✅ Multi-PDF analysis documents have all required fields")
        
        print("\n🎉 Database integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    success = test_database_integration()
    exit(0 if success else 1)