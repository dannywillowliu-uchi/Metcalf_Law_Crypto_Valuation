#!/usr/bin/env python3
"""
Helper script to find the right Dune query for Ethereum active addresses.

This helps identify which query ID to use if the default doesn't work.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import requests

sys.path.insert(0, str(Path(__file__).parent))

def search_dune_queries():
    """Search for Ethereum active addresses queries on Dune."""
    print("Finding Dune Queries for Ethereum Active Addresses")
    print("=" * 60)
    
    load_dotenv()
    api_key = os.getenv("DUNE_API_KEY")
    
    if not api_key:
        print("❌ DUNE_API_KEY not found in .env file")
        print("\nPlease add your key to .env file first:")
        print("  DUNE_API_KEY=your_key_here")
        return
    
    print(f"✓ Found API key\n")
    
    # Dune API doesn't have a direct search endpoint
    # But we can test common query IDs
    print("Testing common query IDs for Ethereum active addresses...")
    print("(If these don't work, you'll need to find/create a query on Dune.com)\n")
    
    headers = {
        "X-Dune-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Common query IDs to try
    test_queries = [2, 107, 1911, 1912]  # Common Ethereum metrics queries
    
    for query_id in test_queries:
        print(f"Testing Query ID {query_id}...", end=" ")
        
        try:
            # Get query metadata
            query_url = f"https://api.dune.com/api/v1/query/{query_id}"
            response = requests.get(query_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                query_info = response.json()
                print(f"✓ Found!")
                print(f"  Name: {query_info.get('name', 'N/A')}")
                print(f"  Description: {query_info.get('description', 'N/A')[:100]}...")
                print(f"  URL: https://dune.com/queries/{query_id}")
                print()
            elif response.status_code == 404:
                print("✗ Not found")
            else:
                print(f"✗ Error {response.status_code}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("How to find the right query:")
    print("1. Go to https://dune.com")
    print("2. Search for 'Ethereum daily active addresses'")
    print("3. Find a query that returns date and active_addresses columns")
    print("4. Copy the query ID from the URL (e.g., dune.com/queries/12345)")
    print("5. Use that query_id in get_active_addresses_dune(query_id=12345)")

if __name__ == "__main__":
    search_dune_queries()

