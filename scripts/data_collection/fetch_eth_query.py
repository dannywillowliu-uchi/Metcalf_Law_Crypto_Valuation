#!/usr/bin/env python3
"""Fetch Ethereum data from query #3488164 - ONE QUERY ONLY"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()

print("Fetching Ethereum Data - Query #3488164")
print("=" * 60)
print("⚠️  This will execute ONE query (50 credit limit)")
print("=" * 60)

try:
    df = collector.get_active_addresses_dune(
        query_id=3488164,
        start_date="2017-01-01",
        end_date="2024-01-01"
    )
    
    print(f"\n✓ SUCCESS! Fetched {len(df)} records")
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Active addresses range: {df['active_addresses'].min():.0f} - {df['active_addresses'].max():.0f}")
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nLast 5 rows:")
    print(df.tail())
    
    # Save to processed data
    output_path = Path("data/processed/ethereum_active_addresses.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved to: {output_path}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

