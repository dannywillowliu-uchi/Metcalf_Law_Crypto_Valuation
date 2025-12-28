#!/usr/bin/env python3
"""
Fetch Dune query results when ready.
Run this script periodically to check if the query has completed.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()

# Try both query IDs
query_ids = [6199647, 6199564]

for query_id in query_ids:
    print(f"\n{'='*60}")
    print(f"Checking Query #{query_id}")
    print('='*60)
    
    try:
        # Try to get cached results first
        cache_file = collector.cache_dir / f"active_addresses_dune_{query_id}.csv"
        if cache_file.exists():
            print(f"✓ Found cached results!")
            import pandas as pd
            df = pd.read_csv(cache_file, parse_dates=['date'])
            print(f"  Records: {len(df)}")
            print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
            continue
        
        # Try fetching (will be quick if query completed)
        print("Attempting to fetch...")
        df = collector.get_active_addresses_dune(
            query_id=query_id,
            start_date="2017-01-01",
            end_date="2024-01-01"
        )
        
        print(f"\n✓ SUCCESS! Got {len(df)} records")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Active addresses: {df['active_addresses'].min():.0f} - {df['active_addresses'].max():.0f}")
        print(f"\n  Saved to: {cache_file}")
        break
        
    except TimeoutError:
        print(f"⏳ Query still running. Check: https://dune.com/queries/{query_id}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "="*60)
print("Tip: Run this script periodically to check if queries completed.")

