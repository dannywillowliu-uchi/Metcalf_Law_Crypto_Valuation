#!/usr/bin/env python3
"""Test the Dune query #6199564"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()

print("Testing Dune Query #6199564")
print("=" * 60)

try:
    # Test with a small date range first
    print("Fetching data for 2023...")
    df = collector.get_active_addresses_dune(
        query_id=6199564,
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    print(f"\n✓ Success! Fetched {len(df)} records")
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Active addresses range: {df['active_addresses'].min():.0f} - {df['active_addresses'].max():.0f}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nLast 5 rows:")
    print(df.tail())
    
    print("\n" + "=" * 60)
    print("✓ Query works! You can now use it for full historical data.")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

