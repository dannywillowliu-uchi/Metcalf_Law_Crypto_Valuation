#!/usr/bin/env python3
"""
Test Credit Usage for Data Collection

This script tests API calls to understand credit consumption
before purchasing any plans. We want to ensure we don't accidentally
use too many credits.

Tests:
1. CoinGecko API - Check credit usage per call
2. Rate limits and throttling
3. Historical data collection efficiency
4. Batch requests if available
"""

import requests
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

# CoinGecko API key (if available)
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

# Networks to test
TEST_NETWORKS = {
    'render': 'render-token',
    'akash': 'akash-network',
    'filecoin': 'filecoin',
    'arweave': 'arweave',
    'bittensor': 'bittensor',
}

def test_coingecko_api_call(coin_id, endpoint_type='simple'):
    """
    Test a single CoinGecko API call and check response headers
    for credit usage information.
    """
    base_url = "https://api.coingecko.com/api/v3"
    
    # Test different endpoints
    endpoints = {
        'simple': f"{base_url}/simple/price?ids={coin_id}&vs_currencies=usd&include_market_cap=true",
        'coin': f"{base_url}/coins/{coin_id}",
        'market_chart': f"{base_url}/coins/{coin_id}/market_chart?vs_currency=usd&days=365",
        'history': f"{base_url}/coins/{coin_id}/history?date=01-01-2024",
    }
    
    url = endpoints.get(endpoint_type, endpoints['simple'])
    
    headers = {}
    if COINGECKO_API_KEY:
        headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
    
    print(f"\n{'='*60}")
    print(f"Testing: {coin_id} - {endpoint_type}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        
        # Check response headers for rate limit info
        print(f"\nResponse Headers:")
        relevant_headers = [
            'x-ratelimit-limit',
            'x-ratelimit-remaining',
            'x-ratelimit-reset',
            'x-api-call-credits',
            'x-api-call-credits-remaining',
        ]
        
        for header in relevant_headers:
            if header in response.headers:
                print(f"  {header}: {response.headers[header]}")
        
        # Check for rate limit errors
        if response.status_code == 429:
            print(f"\n⚠️  RATE LIMIT HIT!")
            if 'retry-after' in response.headers:
                print(f"  Retry after: {response.headers['retry-after']} seconds")
            return None
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success")
            
            # Show sample data structure
            if endpoint_type == 'simple':
                if coin_id in data:
                    print(f"  Price: ${data[coin_id].get('usd', 'N/A')}")
                    print(f"  Market Cap: ${data[coin_id].get('usd_market_cap', 'N/A'):,.0f}" if data[coin_id].get('usd_market_cap') else "  Market Cap: N/A")
            elif endpoint_type == 'market_chart':
                if 'prices' in data:
                    print(f"  Data points: {len(data['prices'])}")
                    print(f"  Date range: {datetime.fromtimestamp(data['prices'][0][0]/1000).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(data['prices'][-1][0]/1000).strftime('%Y-%m-%d')}")
            
            return response
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        return None

def test_rate_limits():
    """Test rate limits by making multiple calls quickly"""
    print(f"\n{'='*60}")
    print("TESTING RATE LIMITS")
    print(f"{'='*60}")
    
    coin_id = 'ethereum'  # Use Ethereum as test
    calls = 10
    delay = 0.1  # 100ms between calls
    
    print(f"Making {calls} rapid calls with {delay}s delay...")
    
    remaining_limits = []
    for i in range(calls):
        response = test_coingecko_api_call(coin_id, 'simple')
        if response and 'x-ratelimit-remaining' in response.headers:
            remaining = response.headers['x-ratelimit-remaining']
            remaining_limits.append(int(remaining))
            print(f"  Call {i+1}: {remaining} remaining")
        time.sleep(delay)
    
    if remaining_limits:
        print(f"\nRate limit tracking:")
        print(f"  Initial: {remaining_limits[0]}")
        print(f"  Final: {remaining_limits[-1]}")
        print(f"  Used: {remaining_limits[0] - remaining_limits[-1]} credits")

def test_historical_data_collection(coin_id):
    """Test collecting historical data efficiently"""
    print(f"\n{'='*60}")
    print(f"TESTING HISTORICAL DATA COLLECTION: {coin_id}")
    print(f"{'='*60}")
    
    # Test market_chart endpoint (last 365 days)
    print("\n1. Testing market_chart (last 365 days)...")
    response = test_coingecko_api_call(coin_id, 'market_chart')
    
    # Test history endpoint (specific date)
    print("\n2. Testing history (specific date)...")
    response = test_coingecko_api_call(coin_id, 'history')
    
    # Estimate credits needed for full history
    print("\n3. Estimating credits for full historical collection...")
    print("   (Assuming daily data collection)")
    
    # Example: If we need daily data from 2020-01-01 to 2024-12-31
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    days = (end_date - start_date).days
    
    print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   Total days: {days}")
    print(f"   Estimated API calls (if using history endpoint): {days}")
    print(f"   Estimated API calls (if using market_chart): ~1-5 (depending on range)")
    
    # Better approach: use market_chart with max range
    print(f"\n   ✅ RECOMMENDED: Use market_chart with 'max' days parameter")
    print(f"      This gives all available historical data in 1 call")

def test_multiple_networks():
    """Test API calls for multiple networks"""
    print(f"\n{'='*60}")
    print("TESTING MULTIPLE NETWORKS")
    print(f"{'='*60}")
    
    results = {}
    
    for network_name, coin_id in TEST_NETWORKS.items():
        print(f"\nTesting {network_name} ({coin_id})...")
        response = test_coingecko_api_call(coin_id, 'simple')
        
        if response:
            if 'x-ratelimit-remaining' in response.headers:
                results[network_name] = {
                    'remaining': response.headers['x-ratelimit-remaining'],
                    'status': 'success'
                }
            else:
                results[network_name] = {'status': 'success (no rate limit info)'}
        else:
            results[network_name] = {'status': 'failed'}
        
        # Small delay between networks
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for network, result in results.items():
        print(f"{network:15} - {result['status']}")

def main():
    print("="*60)
    print("CREDIT USAGE TEST - Data Collection")
    print("="*60)
    print("\nThis script tests API calls to understand credit consumption.")
    print("Goal: Ensure we don't accidentally use too many credits.")
    
    if COINGECKO_API_KEY:
        print(f"\n✅ CoinGecko API key found")
    else:
        print(f"\n⚠️  No CoinGecko API key - using free tier")
        print("   Free tier: 10-50 calls/minute (varies)")
    
    # Test 1: Single API call
    print(f"\n{'='*60}")
    print("TEST 1: Single API Call")
    print(f"{'='*60}")
    test_coingecko_api_call('ethereum', 'simple')
    
    # Test 2: Historical data collection
    print(f"\n{'='*60}")
    print("TEST 2: Historical Data Collection")
    print(f"{'='*60}")
    test_historical_data_collection('ethereum')
    
    # Test 3: Multiple networks
    print(f"\n{'='*60}")
    print("TEST 3: Multiple Networks")
    print(f"{'='*60}")
    test_multiple_networks()
    
    # Test 4: Rate limits (be careful!)
    print(f"\n{'='*60}")
    print("TEST 4: Rate Limit Testing")
    print(f"{'='*60}")
    print("⚠️  This will make multiple API calls - proceed? (y/n)")
    # Uncomment to test rate limits
    # test_rate_limits()
    
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    print("1. Use market_chart endpoint with 'max' days for historical data")
    print("2. Batch requests when possible (multiple coin IDs in one call)")
    print("3. Respect rate limits (10-50 calls/min for free tier)")
    print("4. Monitor x-ratelimit-remaining header")
    print("5. Cache responses to avoid duplicate calls")
    print("6. Use CSV exports from Dune Analytics (no execution cost)")

if __name__ == '__main__':
    main()

