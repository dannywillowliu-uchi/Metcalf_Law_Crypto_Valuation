#!/usr/bin/env python3
"""Fetch multi-chain data from Dune query #4062489 - CSV endpoint (no execution cost)"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()

print("Fetching Multi-Chain Data - Query #4062489")
print("=" * 60)
print("⚠️  Using CSV endpoint - NO execution cost!")
print("=" * 60)

try:
    # Fetch data using CSV endpoint (cheap - just downloads results, NO execution)
    df = collector.get_active_addresses_dune_csv(
        query_id=4062489,
        start_date="2017-01-01",
        end_date="2024-01-01"
    )
    
    print(f"\n✓ SUCCESS! Fetched {len(df)} records")
    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Active addresses range: {df['active_addresses'].min():.0f} - {df['active_addresses'].max():.0f}")
    
    # Check if we have multiple chains
    if 'blockchain' in df.columns or 'chain' in df.columns:
        chain_col = 'blockchain' if 'blockchain' in df.columns else 'chain'
        print(f"\nChains found: {df[chain_col].unique()}")
        print(f"\nRecords per chain:")
        print(df[chain_col].value_counts())
    
    print("\nFirst 10 rows:")
    print(df.head(10))
    
    # Save to processed data
    output_path = Path("data/processed/multi_chain_active_addresses.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved to: {output_path}")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

