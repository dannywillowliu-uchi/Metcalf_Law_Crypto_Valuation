#!/usr/bin/env python3
"""
Test Dune SDK integration with a sample query.

This will help us find a working query for Ethereum active addresses.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

try:
    from dune_client.client import DuneClient
except ImportError:
    print("❌ dune-client not installed. Run: pip install dune-client")
    sys.exit(1)

api_key = os.getenv("DUNE_API_KEY")
if not api_key:
    print("❌ DUNE_API_KEY not found in .env")
    sys.exit(1)

print("Testing Dune SDK")
print("=" * 60)
print(f"API Key: {api_key[:10]}...{api_key[-5:]}\n")

# Initialize client
dune = DuneClient(api_key=api_key)
print("✓ Dune client initialized\n")

# Test with the example query from Dune docs
print("Testing with example query from Dune docs (3493826)...")
print("(This is just to verify the SDK works)\n")

try:
    results = dune.execute_query(query_id=3493826)
    print(f"✓ Query executed successfully!")
    print(f"  Rows returned: {len(results.result.rows)}")
    print(f"  Columns: {list(results.result.rows.to_pandas().columns)[:5]}...")
    print("\n✓ Dune SDK is working!\n")
except Exception as e:
    print(f"⚠ Query 3493826 failed: {e}")
    print("(This is okay - we just need to find the right query for active addresses)\n")

print("=" * 60)
print("Next Steps:")
print("1. Go to https://dune.com")
print("2. Search for 'Ethereum daily active addresses'")
print("3. Find a query that returns: date, active_addresses")
print("4. Copy the query ID from the URL")
print("5. Use it: collector.get_active_addresses_dune(query_id=YOUR_ID)")

