"""
Test updated RailRadar API client with cloudscraper
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.railradar import RailRadarAPI

load_dotenv()

API_KEY = os.getenv("RAILRADAR_API_KEY_ONE_DAY")
TRAIN_NO = 61631
JOURNEY_DATE = datetime.now().strftime("%Y-%m-%d")

print("=" * 70)
print("Testing Updated RailRadar API Client with Cloudscraper")
print("=" * 70)
print(f"Train: {TRAIN_NO}")
print(f"Date: {JOURNEY_DATE}")
print()

# Test the updated API client
client = RailRadarAPI(API_KEY)
print()

print("Fetching train data...")
data = client.get_train_data(TRAIN_NO, JOURNEY_DATE)

if data:
    print("✅ SUCCESS! Data retrieved")
    print(f"   Keys: {list(data.keys())[:5]}...")  # Show first 5 keys
    
    # Test is_journey_started
    started = client.is_journey_started(data, JOURNEY_DATE)
    print(f"   Journey started: {started}")
    
else:
    print("❌ FAILED - No data returned")

print()
print("=" * 70)
print("If test succeeds, push to GitHub and test Actions workflow")
print("=" * 70)
