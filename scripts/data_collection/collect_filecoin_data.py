#!/usr/bin/env python3
"""
Collect Filecoin Data

Collects both user activity data (from Dune) and market cap data (from CoinGecko)
for Filecoin network analysis.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / 'src'))
load_dotenv()

from src.data_collection.filecoin_collector import FilecoinCollector
from src.data_collection.coingecko_safe import CoinGeckoSafe
import pandas as pd

def main():
    print("="*80)
    print("COLLECTING FILECOIN DATA")
    print("="*80)
    
    # Initialize collectors
    dune_api_key = os.getenv("DUNE_API_KEY")
    coingecko_api_key = os.getenv("COINGECKO_API_KEY")
    
    if not dune_api_key:
        print("❌ Error: DUNE_API_KEY not found")
        return
    
    if not coingecko_api_key:
        print("⚠️  Warning: COINGECKO_API_KEY not found - will use free tier (last 365 days)")
    
    filecoin_collector = FilecoinCollector(dune_api_key=dune_api_key)
    coingecko_safe = CoinGeckoSafe(api_key=coingecko_api_key)
    
    # Date range
    start_date = "2020-10-01"  # Filecoin mainnet launch
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\n📅 Date range: {start_date} to {end_date}")
    
    # 1. Collect user activity data from Dune
    print("\n" + "="*80)
    print("STEP 1: Collecting User Activity Data (Dune Analytics)")
    print("="*80)
    
    users_df = filecoin_collector.get_historical_provider_data(
        start_date=start_date,
        end_date=end_date
    )
    
    if users_df is None or users_df.empty:
        print("❌ Failed to collect user activity data")
        return
    
    print(f"✅ Collected {len(users_df)} user activity records")
    print(f"   Date range: {users_df['date'].min()} to {users_df['date'].max()}")
    print(f"   Users range: {users_df['users'].min():,.0f} to {users_df['users'].max():,.0f}")
    
    # 2. Collect market cap data from CoinGecko
    print("\n" + "="*80)
    print("STEP 2: Collecting Market Cap Data (CoinGecko)")
    print("="*80)
    
    mcap_df = coingecko_safe.get_market_chart(
        coin_id='filecoin',
        days=3650,  # 10 years (Analyst Plan limit)
        use_cache=True,
        force_refresh=False
    )
    
    if mcap_df is None or mcap_df.empty:
        print("❌ Failed to collect market cap data")
        return
    
    print(f"✅ Collected {len(mcap_df)} market cap records")
    print(f"   Date range: {mcap_df['date'].min()} to {mcap_df['date'].max()}")
    print(f"   Market cap range: ${mcap_df['market_cap'].min():,.0f} to ${mcap_df['market_cap'].max():,.0f}")
    
    # 3. Merge datasets
    print("\n" + "="*80)
    print("STEP 3: Merging Datasets")
    print("="*80)
    
    # Ensure date columns are datetime
    users_df['date'] = pd.to_datetime(users_df['date']).dt.date
    mcap_df['date'] = pd.to_datetime(mcap_df['date']).dt.date
    
    # Merge on date
    combined_df = pd.merge(
        users_df,
        mcap_df[['date', 'market_cap', 'price']],
        on='date',
        how='inner'
    )
    
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    print(f"✅ Merged datasets: {len(combined_df)} records")
    print(f"   Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    print(f"   Overlap: {len(combined_df)} / {len(users_df)} user records matched")
    
    # 4. Save combined data
    output_dir = Path(__file__).parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "filecoin_correlated_data.csv"
    combined_df.to_csv(output_file, index=False)
    
    print(f"\n💾 Saved combined data to: {output_file}")
    
    # 5. Summary
    print("\n" + "="*80)
    print("DATA COLLECTION SUMMARY")
    print("="*80)
    print(f"\n✅ User Activity Data:")
    print(f"   Source: Dune Analytics (Query #3302707)")
    print(f"   Metric: active_address_count_daily")
    print(f"   Records: {len(users_df)}")
    print(f"   Note: This is active addresses WITHOUT nonce filtering")
    print(f"   Decision needed: Use as-is OR create query with nonce ≥ 5")
    
    print(f"\n✅ Market Cap Data:")
    print(f"   Source: CoinGecko")
    print(f"   Records: {len(mcap_df)}")
    
    print(f"\n✅ Combined Dataset:")
    print(f"   Records: {len(combined_df)}")
    print(f"   File: {output_file}")
    
    print(f"\n📊 Preview:")
    print(combined_df.head(10).to_string())
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. Review the data to ensure quality
2. Decide on filtering methodology:
   - Use active_address_count_daily as-is (no nonce filter)
   - OR create new Dune query with nonce ≥ 5 filtering
3. Run analysis with Metcalfe's Law and FTP-MS models
4. Document filtering decision in NETWORK_FILTERING_METHODOLOGY.md
    """)

if __name__ == '__main__':
    main()


