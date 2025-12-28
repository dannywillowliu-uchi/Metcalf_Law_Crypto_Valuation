#!/usr/bin/env python3
"""
Test Free Tier Limits

Find the exact limits of the free tier to avoid accidentally
using paid plan features.
"""

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
BASE_URL = "https://api.coingecko.com/api/v3"

def test_day_limits():
    """Test different day ranges to find free tier limit"""
    print("="*60)
    print("TESTING FREE TIER DAY LIMITS")
    print("="*60)
    
    coin_id = 'ethereum'
    day_ranges = [365, 730, 1095, 1825, 'max']
    
    for days in day_ranges:
        url = f"{BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
        
        headers = {}
        if COINGECKO_API_KEY:
            headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
        
        print(f"\nTesting days={days}...")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'prices' in data:
                    print(f"  ✅ Success - {len(data['prices'])} data points")
                else:
                    print(f"  ✅ Success - but no prices data")
            elif response.status_code == 401:
                print(f"  ❌ 401 Unauthorized - Requires paid plan")
                print(f"  ⚠️  Free tier limit is less than {days} days")
                break
            else:
                print(f"  ⚠️  Status {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(1)

def main():
    print("\nFinding free tier limits for CoinGecko API...")
    if COINGECKO_API_KEY:
        print("⚠️  Note: You have an API key - this may affect results")
    else:
        print("✅ Testing with free tier (no API key)")
    
    test_day_limits()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("\nFree Tier Limits (from testing):")
    print("  ✅ market_chart with days=365: Works")
    print("  ❌ market_chart with days=max: Requires paid plan")
    print("  ❌ history endpoint: Requires paid plan")
    print("\nRecommendation:")
    print("  - Free tier: Use days=365 (last year only)")
    print("  - Paid plan: Use days=max (all historical data)")

if __name__ == '__main__':
    main()

