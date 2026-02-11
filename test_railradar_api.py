"""
Test script to debug RailRadar API calls
Simulates the exact request made by GitHub Actions
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RAILRADAR_API_KEY_ONE_DAY")
TRAIN_NO = "61631"
JOURNEY_DATE = datetime.now().strftime("%Y-%m-%d")

print("=" * 70)
print("Testing RailRadar API Call")
print("=" * 70)
print(f"Train Number: {TRAIN_NO}")
print(f"Journey Date: {JOURNEY_DATE}")
print(f"API Key: {API_KEY[:10]}...{API_KEY[-5:]}")
print()

# Test 1: Original request (like GitHub Actions)
print("TEST 1: Original request (python-requests User-Agent)")
print("-" * 70)

url = f"https://api.railradar.in/api/v1/trains/{TRAIN_NO}"
headers = {
    "X-API-Key": API_KEY,
    "Accept": "*/*"
}
params = {
    "journeyDate": JOURNEY_DATE,
    "dataType": "live",
    "dataProvider": "railradar",
    "userId": ""
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"Response Length: {len(response.text)} bytes")
    
    if response.status_code == 403:
        print("❌ BLOCKED by Cloudflare")
        if "Just a moment" in response.text:
            print("   Cloudflare challenge detected")
    elif response.status_code == 200:
        print("✅ SUCCESS")
        try:
            data = response.json()
            print(f"   Data keys: {list(data.keys())}")
        except:
            print("   Response is not JSON")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")

print()

# Test 2: With browser-like User-Agent
print("TEST 2: With browser User-Agent")
print("-" * 70)

headers_browser = {
    "X-API-Key": API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://railradar.in/",
    "Origin": "https://railradar.in",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

try:
    session = requests.Session()
    response = session.get(url, headers=headers_browser, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"Response Length: {len(response.text)} bytes")
    
    if response.status_code == 403:
        print("❌ BLOCKED by Cloudflare")
        if "Just a moment" in response.text:
            print("   Cloudflare challenge detected")
    elif response.status_code == 200:
        print("✅ SUCCESS")
        try:
            data = response.json()
            print(f"   Data keys: {list(data.keys())}")
            print(f"   Train: {data.get('trainNo', 'N/A')} - {data.get('trainName', 'N/A')}")
        except:
            print("   Response is not JSON")
            print(f"   First 200 chars: {response.text[:200]}")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")

print()
print("=" * 70)
print("RECOMMENDATION:")
print("If TEST 2 succeeds, update railradar.py to use browser-like headers")
print("=" * 70)
