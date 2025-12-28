#!/usr/bin/env python3
"""
Quick Network Data Availability Check

Checks which networks have market cap data and tests basic data collection.
"""

import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / 'src'))
load_dotenv()

from src.data_collection.coingecko_safe import CoinGeckoSafe

# Networks to check
NETWORKS = {
    'render': 'render-token',
    'akash': 'akash-network',
    'bittensor': 'bittensor',
    'helium': 'helium',
    'filecoin': 'filecoin',
    'arweave': 'arweave',
}

def check_network(network_name, coin_id):
    """Check if we can get market cap data for a network."""
    print(f"\n[{network_name.upper()}]")
    print("-" * 60)
    
    coingecko = CoinGeckoSafe(api_key=os.getenv('COINGECKO_API_KEY'))
    
    # Check cache first
    cache_file = coingecko.cache_dir / f"{coin_id}_market_chart_3650.csv"
    if cache_file.exists():
        df = pd.read_csv(cache_file, parse_dates=['date'])
        print(f"✅ Market cap data cached: {len(df)} records")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        return True
    else:
        print(f"⚠️  No cached market cap data")
        return False

def main():
    print("="*80)
    print("QUICK NETWORK DATA AVAILABILITY CHECK")
    print("="*80)
    
    results = {}
    for network_name, coin_id in NETWORKS.items():
        has_data = check_network(network_name, coin_id)
        results[network_name] = {
            'coin_id': coin_id,
            'market_cap': has_data,
            'user_activity': 'unknown'
        }
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("\nNetworks with market cap data:")
    for name, info in results.items():
        status = "✅" if info['market_cap'] else "❌"
        print(f"  {status} {name}: {info['coin_id']}")
    
    print("\nNext: Need to find user activity data sources for each network")

if __name__ == '__main__':
    main()


