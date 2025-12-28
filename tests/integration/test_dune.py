#!/usr/bin/env python3
"""
Test script for Dune Analytics integration.

Run this after setting up your Dune API key to verify everything works.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent))

from src.data_collection import EthereumDataCollector

def test_dune_connection():
    """Test Dune Analytics API connection."""
    print("Testing Dune Analytics Connection")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    dune_key = os.getenv("DUNE_API_KEY")
    if not dune_key:
        print("❌ DUNE_API_KEY not found in environment")
        print("\nPlease:")
        print("1. Get your API key from: https://dune.com/settings/api")
        print("2. Add it to .env file: DUNE_API_KEY=your_key_here")
        return False
    
    print(f"✓ Found Dune API key (length: {len(dune_key)})")
    
    # Initialize collector
    try:
        collector = EthereumDataCollector(dune_api_key=dune_key)
        print("✓ Collector initialized")
    except Exception as e:
        print(f"❌ Error initializing collector: {e}")
        return False
    
    # Test fetching active addresses
    print("\nTesting active addresses fetch...")
    print("Fetching data for 2023 (this may take 30-60 seconds)...")
    
    try:
        users_df = collector.get_active_addresses_dune(
            start_date="2023-01-01",
            end_date="2023-12-31",
            query_id=2  # Default public query
        )
        
        print(f"\n✓ Success! Fetched {len(users_df)} records")
        print(f"\nDate range: {users_df['date'].min()} to {users_df['date'].max()}")
        print(f"Active addresses range: {users_df['active_addresses'].min():.0f} - {users_df['active_addresses'].max():.0f}")
        print("\nFirst 5 rows:")
        print(users_df.head())
        print("\nLast 5 rows:")
        print(users_df.tail())
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error fetching data: {e}")
        print("\nPossible issues:")
        print("1. Query ID #2 might not exist or be outdated")
        print("2. API key might be invalid")
        print("3. Network connection issue")
        print("\nLet me know the error and I can help troubleshoot!")
        return False

if __name__ == "__main__":
    success = test_dune_connection()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Dune Analytics is working!")
        print("You can now use it in your analysis.")
    else:
        print("\n" + "=" * 60)
        print("❌ Setup incomplete. Please check the errors above.")

