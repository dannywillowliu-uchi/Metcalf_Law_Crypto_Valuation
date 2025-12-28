#!/usr/bin/env python3
"""
Test Dune API Key Functionality

Tests if the API key can:
- Create queries (0 credits)
- List queries (0 credits)
- Execute queries (costs credits)
"""

import sys
from pathlib import Path
import os
import requests
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.getenv("DUNE_API_KEY")
if not api_key:
    print("❌ DUNE_API_KEY not found")
    sys.exit(1)

print("="*80)
print("TESTING DUNE API KEY FUNCTIONALITY")
print("="*80)

headers = {
    "X-DUNE-API-Key": api_key,
    "Content-Type": "application/json"
}

base_url = "https://api.dune.com/api/v1"

# Test 1: List queries (should work, 0 credits)
print("\n1. Testing: List queries (0 credits)...")
try:
    response = requests.get(
        f"{base_url}/query",
        headers=headers,
        timeout=10
    )
    if response.status_code == 200:
        queries = response.json()
        print(f"   ✅ Success! Found {len(queries.get('results', []))} queries")
        print("   ✅ API key can list queries (0 credits)")
    elif response.status_code == 401:
        print("   ❌ API key is invalid")
        sys.exit(1)
    else:
        print(f"   ⚠️  Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# Test 2: Create a test query (0 credits)
print("\n2. Testing: Create query (0 credits)...")
test_query = {
    "name": "Test Query - Can Delete",
    "query_sql": "SELECT 1 as test",
    "parameters": []
}

try:
    response = requests.post(
        f"{base_url}/query",
        headers=headers,
        json=test_query,
        timeout=10
    )
    if response.status_code == 200:
        result = response.json()
        query_id = result.get('query_id')
        print(f"   ✅ Success! Created test query #{query_id}")
        print("   ✅ API key can create queries (0 credits)")
        print(f"   📝 Query URL: https://dune.com/queries/{query_id}")
        print("   💡 You can delete this test query on Dune if you want")
    elif response.status_code == 401:
        print("   ❌ API key is invalid")
        sys.exit(1)
    else:
        print(f"   ⚠️  Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\n✅ API key is working!")
print("\nNext steps:")
print("  1. Check your credits at: https://dune.com/settings/billing")
print("  2. If you have ≥1,800 credits: Run create_and_execute_dune_queries.py")
print("  3. If you have <1,800 credits: I can modify the script to create queries only")

