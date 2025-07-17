#!/usr/bin/env python3
"""
Health Check Test with Extended Timeout
"""

import requests
import time

BACKEND_URL = "https://eeeb658f-5f92-4c32-9db3-27e8a20bce60.preview.emergentagent.com/api"

def test_health_with_retry():
    """Test health endpoint with retries and longer timeout"""
    print("🏥 Testing Health Endpoints with Extended Timeout...")
    print("=" * 60)
    
    # Test health endpoint
    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1}/3 - Testing /health endpoint...")
            response = requests.get(f"{BACKEND_URL}/health", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Check PASSED - Status: {data.get('status')}")
                break
            else:
                print(f"❌ Health Check FAILED - Status code: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"⏰ Health Check TIMEOUT on attempt {attempt + 1}")
            if attempt < 2:
                time.sleep(5)
        except Exception as e:
            print(f"❌ Health Check ERROR: {str(e)}")
            if attempt < 2:
                time.sleep(5)
    
    # Test root endpoint
    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1}/3 - Testing / endpoint...")
            response = requests.get(f"{BACKEND_URL}/", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root Endpoint PASSED - Message: {data.get('message')}")
                break
            else:
                print(f"❌ Root Endpoint FAILED - Status code: {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"⏰ Root Endpoint TIMEOUT on attempt {attempt + 1}")
            if attempt < 2:
                time.sleep(5)
        except Exception as e:
            print(f"❌ Root Endpoint ERROR: {str(e)}")
            if attempt < 2:
                time.sleep(5)

if __name__ == "__main__":
    test_health_with_retry()