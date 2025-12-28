#!/usr/bin/env python3
"""
Example script for collecting Ethereum data.

This demonstrates how to use the EthereumDataCollector to gather
historical data for network effects analysis.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_collection import EthereumDataCollector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    print("Ethereum Data Collection Example")
    print("=" * 60)
    
    # Initialize collector
    # API keys can be:
    # 1. Set in .env file (recommended)
    # 2. Passed as parameters
    # 3. Set as environment variables
    collector = EthereumDataCollector(
        coingecko_api_key=os.getenv("COINGECKO_API_KEY"),  # Optional
        dune_api_key=os.getenv("DUNE_API_KEY")             # Required for active addresses
    )
    
    print("\nOption 1: Get complete data from APIs")
    print("-" * 60)
    try:
        # This requires both APIs to be set up
        df = collector.get_complete_ethereum_data(
            start_date="2020-01-01",  # Start from 2020 for faster testing
            end_date="2023-12-31"
        )
        print(f"\n✓ Successfully collected {len(df)} records")
        print(f"\nFirst few rows:")
        print(df.head())
        
        # Save to CSV
        output_path = Path("data/processed/ethereum_data.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✓ Saved to {output_path}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTip: Set up API keys or use CSV import (see Option 2)")
    
    print("\n" + "=" * 60)
    print("\nOption 2: Load from CSV file")
    print("-" * 60)
    print("If you have a CSV file with columns: date, users, market_cap")
    print("You can load it like this:")
    print("""
    df = collector.load_from_csv("data/raw/ethereum_historical.csv")
    """)
    
    print("\n" + "=" * 60)
    print("\nOption 3: Get market cap only (no API key needed)")
    print("-" * 60)
    try:
        market_cap_df = collector.get_market_cap_history(
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        print(f"✓ Fetched {len(market_cap_df)} market cap records")
        print(market_cap_df.head())
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("\nSetup Instructions:")
    print("-" * 60)
    print("1. CoinGecko API (optional): https://www.coingecko.com/en/api")
    print("2. Dune Analytics API (required): https://dune.com/settings/api")
    print("3. Create .env file with your keys:")
    print("   COINGECKO_API_KEY=your_key")
    print("   DUNE_API_KEY=your_key")
    print("\nSee src/data_collection/README.md for details")

if __name__ == "__main__":
    main()

