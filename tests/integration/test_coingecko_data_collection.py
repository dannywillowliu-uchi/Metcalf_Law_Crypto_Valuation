#!/usr/bin/env python3
"""
Test CoinGecko Data Collection (Last 365 Days - Free Tier)

Tests collecting market cap data for all networks using free tier (365 days limit).
This helps verify data quality before committing to paid plan.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import numpy as np
import requests
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

load_dotenv()

# Networks to test (with CoinGecko IDs)
TEST_NETWORKS = {
    'render': 'render-token',
    'akash': 'akash-network',
    'bittensor': 'bittensor',
    'helium': 'helium',
    'filecoin': 'filecoin',
    'arweave': 'arweave',
}

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
BASE_URL = "https://api.coingecko.com/api/v3"

def get_market_chart(coin_id, days=365):
    """
    Get market chart data for a coin (last 365 days - free tier limit).
    
    Returns DataFrame with columns: date, market_cap, price
    """
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }
    
    headers = {}
    if COINGECKO_API_KEY:
        headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
    
    print(f"  Fetching {coin_id}...", end=" ", flush=True)
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract market cap data
            market_caps = data.get('market_caps', [])
            prices = data.get('prices', [])
            
            if not market_caps:
                print(f"❌ No market cap data")
                return None
            
            # Convert to DataFrame
            records = []
            for i, (timestamp, mcap) in enumerate(market_caps):
                date = datetime.fromtimestamp(timestamp / 1000)
                price = prices[i][1] if i < len(prices) else None
                records.append({
                    'date': date,
                    'market_cap': mcap,
                    'price': price
                })
            
            df = pd.DataFrame(records)
            df = df.sort_values('date').reset_index(drop=True)
            
            print(f"✅ {len(df)} records ({df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')})")
            return df
            
        elif response.status_code == 429:
            print(f"❌ Rate limit hit - waiting 60s...")
            time.sleep(60)
            return get_market_chart(coin_id, days)  # Retry
            
        else:
            print(f"❌ Error {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_batch_simple_price():
    """Test batch request for current prices"""
    print(f"\n{'='*60}")
    print("TEST: Batch Simple Price (Current Market Caps)")
    print(f"{'='*60}")
    
    coin_ids = list(TEST_NETWORKS.values())
    ids_param = ','.join(coin_ids)
    
    url = f"{BASE_URL}/simple/price"
    params = {
        'ids': ids_param,
        'vs_currencies': 'usd',
        'include_market_cap': 'true'
    }
    
    headers = {}
    if COINGECKO_API_KEY:
        headers['x-cg-demo-api-key'] = COINGECKO_API_KEY
    
    print(f"Fetching current prices for {len(coin_ids)} networks...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully retrieved {len(data)} networks in 1 call\n")
            
            for network_name, coin_id in TEST_NETWORKS.items():
                if coin_id in data:
                    price = data[coin_id].get('usd', 0)
                    mcap = data[coin_id].get('usd_market_cap', 0)
                    print(f"  {network_name:15} - Price: ${price:,.2f}, Market Cap: ${mcap:,.0f}")
            
            return data
        else:
            print(f"❌ Error {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def collect_all_networks():
    """Collect market cap data for all test networks"""
    print(f"\n{'='*60}")
    print("COLLECTING MARKET CAP DATA (Last 365 Days)")
    print(f"{'='*60}")
    print(f"\nNetworks: {len(TEST_NETWORKS)}")
    print(f"Date range: Last 365 days (free tier limit)")
    print(f"API Key: {'✅ Found' if COINGECKO_API_KEY else '⚠️  Not found (using free tier)'}")
    
    results = {}
    output_dir = Path(__file__).parent / "data" / "test_coingecko"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for network_name, coin_id in TEST_NETWORKS.items():
        print(f"\n[{network_name.upper()}]")
        df = get_market_chart(coin_id, days=365)
        
        if df is not None:
            results[network_name] = df
            
            # Save to CSV
            output_file = output_dir / f"{network_name}_market_cap_365d.csv"
            df.to_csv(output_file, index=False)
            print(f"  💾 Saved to: {output_file}")
            
            # Show summary stats
            print(f"  📊 Summary:")
            print(f"     Records: {len(df)}")
            print(f"     Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"     Market cap range: ${df['market_cap'].min():,.0f} to ${df['market_cap'].max():,.0f}")
            print(f"     Missing data: {df['market_cap'].isna().sum()} days")
        
        # Rate limiting - be conservative
        time.sleep(2)  # 2 second delay between calls
    
    return results

def analyze_data_quality(results):
    """Analyze collected data quality"""
    print(f"\n{'='*60}")
    print("DATA QUALITY ANALYSIS")
    print(f"{'='*60}")
    
    if not results:
        print("❌ No data collected")
        return
    
    summary = []
    for network_name, df in results.items():
        total_days = (df['date'].max() - df['date'].min()).days
        missing_days = total_days - len(df)
        completeness = (len(df) / 365) * 100 if total_days > 0 else 0
        
        summary.append({
            'network': network_name,
            'records': len(df),
            'date_range_days': total_days,
            'missing_days': missing_days,
            'completeness_%': completeness,
            'min_mcap': df['market_cap'].min(),
            'max_mcap': df['market_cap'].max(),
            'latest_mcap': df['market_cap'].iloc[-1] if len(df) > 0 else None,
        })
    
    summary_df = pd.DataFrame(summary)
    
    print("\nSummary Statistics:")
    print(summary_df.to_string(index=False))
    
    print(f"\n✅ Data Quality:")
    print(f"   Average completeness: {summary_df['completeness_%'].mean():.1f}%")
    print(f"   Networks with >95% completeness: {(summary_df['completeness_%'] > 95).sum()}/{len(summary_df)}")
    
    return summary_df

def main():
    print("="*60)
    print("COINGECKO DATA COLLECTION TEST (Last 365 Days)")
    print("="*60)
    print("\nThis test collects market cap data using free tier (365 days limit)")
    print("Goal: Verify data quality before committing to paid plan")
    
    # Test 1: Batch simple price
    print(f"\n{'='*60}")
    print("TEST 1: Batch Simple Price")
    print(f"{'='*60}")
    test_batch_simple_price()
    
    # Test 2: Collect historical data
    print(f"\n{'='*60}")
    print("TEST 2: Historical Market Cap Data")
    print(f"{'='*60}")
    results = collect_all_networks()
    
    # Test 3: Analyze data quality
    if results:
        analyze_data_quality(results)
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("\n✅ If data quality is good:")
    print("   1. Review collected CSV files in data/test_coingecko/")
    print("   2. Verify date ranges and completeness")
    print("   3. If satisfied, can upgrade to paid plan for full history")
    print("\n⚠️  If data quality is poor:")
    print("   1. Check for missing dates")
    print("   2. Verify CoinGecko IDs are correct")
    print("   3. Consider paid plan for better data access")
    
    print(f"\n📊 Files saved to: data/test_coingecko/")
    print(f"   Review these files to assess data quality")

if __name__ == '__main__':
    main()

