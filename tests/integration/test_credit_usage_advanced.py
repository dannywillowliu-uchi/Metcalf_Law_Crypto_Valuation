#!/usr/bin/env python3
"""
Advanced Credit Usage Testing

Tests efficient data collection methods to minimize credit usage:
1. Batch requests (multiple coins in one call)
2. market_chart with 'max' days parameter
3. Credit tracking
"""

import requests
import time
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
BASE_URL = "https://api.coingecko.com/api/v3"

def make_request(url, description):
    """Make API request and track credit usage"""
    headers = {}
    if COINGECKO_API_KEY:
        headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
    
    print(f"\n{description}")
    print(f"  URL: {url[:80]}...")
    
    try:
        start = time.time()
        response = requests.get(url, headers=headers, timeout=30)
        elapsed = time.time() - start
        
        print(f"  Status: {response.status_code}")
        print(f"  Time: {elapsed:.2f}s")
        
        # Check for rate limit info
        if 'x-ratelimit-remaining' in response.headers:
            print(f"  Rate Limit Remaining: {response.headers['x-ratelimit-remaining']}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  Error: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None

def test_batch_simple_price():
    """Test batch request for multiple coins"""
    print(f"\n{'='*60}")
    print("TEST: Batch Simple Price (Multiple Coins in One Call)")
    print(f"{'='*60}")
    
    # Test with multiple coin IDs
    coin_ids = ['render-token', 'akash-network', 'filecoin', 'arweave', 'bittensor']
    ids_param = ','.join(coin_ids)
    
    url = f"{BASE_URL}/simple/price?ids={ids_param}&vs_currencies=usd&include_market_cap=true"
    
    data = make_request(url, f"Batch request for {len(coin_ids)} coins")
    
    if data:
        print(f"\n  ✅ Successfully retrieved {len(data)} coins in 1 call")
        print(f"  Credit savings: {len(coin_ids) - 1} calls saved")
        for coin_id in coin_ids:
            if coin_id in data:
                mcap = data[coin_id].get('usd_market_cap', 0)
                print(f"    {coin_id:20} - Market Cap: ${mcap:,.0f}")

def test_market_chart_max():
    """Test market_chart with 'max' days parameter"""
    print(f"\n{'='*60}")
    print("TEST: Market Chart with 'max' Days (All Historical Data)")
    print(f"{'='*60}")
    
    coin_id = 'ethereum'
    url = f"{BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days=max"
    
    data = make_request(url, f"Market chart with 'max' days for {coin_id}")
    
    if data and 'prices' in data:
        prices = data['prices']
        print(f"\n  ✅ Retrieved {len(prices)} data points")
        
        if len(prices) > 0:
            first_date = datetime.fromtimestamp(prices[0][0]/1000)
            last_date = datetime.fromtimestamp(prices[-1][0]/1000)
            print(f"  Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
            print(f"  Total days: {(last_date - first_date).days}")
            print(f"  ✅ This is MUCH more efficient than daily calls!")

def test_multiple_networks_efficient():
    """Test efficient collection for multiple networks"""
    print(f"\n{'='*60}")
    print("TEST: Efficient Collection for Multiple Networks")
    print(f"{'='*60}")
    
    networks = {
        'render': 'render-token',
        'akash': 'akash-network',
        'filecoin': 'filecoin',
        'arweave': 'arweave',
        'bittensor': 'bittensor',
    }
    
    print(f"\nMethod 1: Batch simple price (current prices)")
    coin_ids = list(networks.values())
    ids_param = ','.join(coin_ids)
    url = f"{BASE_URL}/simple/price?ids={ids_param}&vs_currencies=usd&include_market_cap=true"
    data = make_request(url, f"Batch request for {len(coin_ids)} networks")
    
    if data:
        print(f"  ✅ 1 API call for {len(coin_ids)} networks")
    
    print(f"\nMethod 2: Individual market_chart calls (historical data)")
    total_calls = 0
    for name, coin_id in networks.items():
        url = f"{BASE_URL}/coins/{coin_id}/market_chart?vs_currency=usd&days=max"
        data = make_request(url, f"Historical data for {name}")
        if data:
            total_calls += 1
        time.sleep(1)  # Rate limit protection
    
    print(f"\n  Total calls needed: {total_calls}")
    print(f"  Estimated credits: {total_calls} (1 credit per call with API key)")

def estimate_total_credits():
    """Estimate total credits needed for all networks"""
    print(f"\n{'='*60}")
    print("CREDIT ESTIMATION FOR ALL NETWORKS")
    print(f"{'='*60}")
    
    # Networks with tokens (need CoinGecko)
    tokenized_networks = [
        'render-token',
        'akash-network',
        'bittensor',
        'helium',
        'filecoin',
        'arweave',
        # 'hivemapper',  # needs verification
        # 'dimo',  # needs verification
        # 'worldcoin-wld',  # needs verification
        # 'decentralized-social',  # DeSo, needs verification
    ]
    
    print(f"\nNetworks to collect: {len(tokenized_networks)}")
    
    # Efficient method: market_chart with 'max' days
    print(f"\nEfficient Method (market_chart with 'max' days):")
    print(f"  - 1 call per network for all historical data")
    print(f"  - Total calls: {len(tokenized_networks)}")
    
    # With API key (Analyst Plan)
    print(f"\nWith CoinGecko Analyst Plan ($129/month):")
    print(f"  - Credits per call: 1")
    print(f"  - Total credits needed: {len(tokenized_networks)}")
    print(f"  - Monthly credit limit: 500,000")
    print(f"  - Usage: {len(tokenized_networks) / 500000 * 100:.4f}% of monthly limit")
    print(f"  - ✅ Well within limits!")
    
    # Free tier
    print(f"\nFree Tier (no API key):")
    print(f"  - Rate limit: 10-50 calls/min")
    print(f"  - Total calls needed: {len(tokenized_networks)}")
    print(f"  - Time needed: ~{len(tokenized_networks) / 30:.1f} minutes (at 30 calls/min)")
    print(f"  - ⚠️  May hit rate limits if done too quickly")
    
    # Daily updates (if needed)
    print(f"\nDaily Updates (if keeping subscription):")
    print(f"  - Batch simple price: 1 call for all networks")
    print(f"  - Credits per day: 1")
    print(f"  - Credits per month: 30")
    print(f"  - Usage: 0.006% of monthly limit")

def test_rate_limit_protection():
    """Test rate limit protection strategies"""
    print(f"\n{'='*60}")
    print("RATE LIMIT PROTECTION STRATEGIES")
    print(f"{'='*60}")
    
    print("\n1. Batch Requests:")
    print("   ✅ Use batch endpoints when available")
    print("   ✅ Reduces API calls significantly")
    
    print("\n2. Caching:")
    print("   ✅ Cache API responses to disk")
    print("   ✅ Avoid duplicate calls for same data")
    
    print("\n3. Rate Limiting:")
    print("   ✅ Add delays between calls")
    print("   ✅ Monitor rate limit headers")
    print("   ✅ Implement exponential backoff on 429 errors")
    
    print("\n4. Efficient Endpoints:")
    print("   ✅ Use market_chart with 'max' days (1 call for all history)")
    print("   ✅ Use batch simple price (multiple coins in 1 call)")
    print("   ❌ Avoid history endpoint (requires paid plan)")

def main():
    print("="*60)
    print("ADVANCED CREDIT USAGE TEST")
    print("="*60)
    print("\nTesting efficient data collection methods to minimize credit usage")
    
    if COINGECKO_API_KEY:
        print(f"\n✅ CoinGecko API key found (Analyst Plan)")
    else:
        print(f"\n⚠️  No API key - using free tier")
    
    # Test 1: Batch requests
    test_batch_simple_price()
    
    # Test 2: Market chart with max days
    test_market_chart_max()
    
    # Test 3: Multiple networks efficient collection
    test_multiple_networks_efficient()
    
    # Test 4: Credit estimation
    estimate_total_credits()
    
    # Test 5: Rate limit protection
    test_rate_limit_protection()
    
    print(f"\n{'='*60}")
    print("FINAL RECOMMENDATIONS")
    print(f"{'='*60}")
    print("\n✅ SAFE TO PROCEED:")
    print("   1. Use batch requests when possible")
    print("   2. Use market_chart with 'max' days for historical data")
    print("   3. Cache all responses to avoid duplicate calls")
    print("   4. Add rate limiting (1-2 second delays between calls)")
    print("   5. Monitor rate limit headers if available")
    print("\n📊 CREDIT USAGE:")
    print(f"   - Initial collection: ~{len(['render-token', 'akash-network', 'bittensor', 'helium', 'filecoin', 'arweave'])} credits")
    print("   - Daily updates: 1 credit (batch request)")
    print("   - Well within Analyst Plan limits (500,000/month)")
    print("\n⚠️  SAFETY MEASURES:")
    print("   1. Implement credit tracking in code")
    print("   2. Set maximum credit usage limits")
    print("   3. Alert if approaching limits")
    print("   4. Use CSV exports from Dune (no execution cost)")

if __name__ == '__main__':
    main()

