#!/usr/bin/env python3
"""
Test Filecoin Data Collector

Tests the FilecoinCollector to retrieve user activity data from Dune Analytics.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent / 'src'))
load_dotenv()

from src.data_collection.filecoin_collector import FilecoinCollector
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("="*80)
    print("TESTING FILECOIN DATA COLLECTOR (Dune Analytics)")
    print("="*80)
    
    dune_api_key = os.getenv("DUNE_API_KEY")
    if not dune_api_key:
        print("❌ Error: DUNE_API_KEY not found in environment variables")
        print("   Please set DUNE_API_KEY in your .env file")
        return
    
    collector = FilecoinCollector(dune_api_key=dune_api_key)
    
    # Test: Get historical user activity data from Dune
    print("\n[Test] Getting historical user activity data from Dune Analytics...")
    print("   Query: #3302707 (dune.kalen.dataset_filecoin_daily_metrics)")
    print("   Date range: 2020-10-01 (mainnet launch) to present")
    
    start_date = "2020-10-01"  # Filecoin mainnet launch
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")  # Include some future for Dune
    
    df = collector.get_historical_provider_data(
        start_date=start_date,
        end_date=end_date
    )
    
    if df is not None and not df.empty:
        print(f"\n✅ Success! Retrieved {len(df)} records")
        print(f"\n📊 Data Summary:")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Users range: {df['users'].min():,.0f} to {df['users'].max():,.0f}")
        
        print(f"\n📋 First 5 records:")
        print(df.head().to_string())
        
        print(f"\n📋 Last 5 records:")
        print(df.tail().to_string())
        
        print(f"\n📈 Data Statistics:")
        print(df.describe())
        
        # Check what type of data we got
        print(f"\n🔍 Data Type Analysis:")
        if 'active_addresses' in str(df.columns).lower() or 'dau' in str(df.columns).lower():
            print("   ✅ Appears to be active addresses data")
            print("   → Can apply nonce ≥ 5 filtering (match paper methodology)")
        elif 'provider' in str(df.columns).lower() or 'miner' in str(df.columns).lower():
            print("   ✅ Appears to be storage provider/miner data")
            print("   → May not need nonce filtering (providers are real infrastructure)")
        else:
            print("   ⚠️  Unknown data type - need to inspect columns")
        
    else:
        print("\n❌ Failed to retrieve historical data")
        print("\nPossible reasons:")
        print("   1. Dune query #3302707 has not been executed yet")
        print("   2. Query execution required (costs ~300 credits)")
        print("   3. API key invalid or expired")
        print("\nNext steps:")
        print("   1. Execute query at: https://dune.com/queries/3302707")
        print("   2. Wait for query to complete")
        print("   3. Re-run this test script")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

