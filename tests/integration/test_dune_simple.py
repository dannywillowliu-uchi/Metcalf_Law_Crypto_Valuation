#!/usr/bin/env python3
"""
Simple test to verify Dune API works and help find the right query.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import time

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

api_key = os.getenv("DUNE_API_KEY")
if not api_key:
    print("❌ DUNE_API_KEY not found")
    sys.exit(1)

print("Testing Dune API Connection")
print("=" * 60)
print(f"API Key: {api_key[:10]}...{api_key[-5:]}")
print()

headers = {
    "X-Dune-API-Key": api_key,
    "Content-Type": "application/json"
}

# Test 1: Check API key validity
print("Test 1: Checking API key validity...")
try:
    # Try to get user info or a simple endpoint
    response = requests.get(
        "https://api.dune.com/api/v1/user",
        headers=headers,
        timeout=10
    )
    if response.status_code == 200:
        print("✓ API key is valid!")
        user_info = response.json()
        print(f"  User: {user_info.get('user_name', 'N/A')}")
    elif response.status_code == 401:
        print("❌ API key is invalid")
        sys.exit(1)
    else:
        print(f"⚠ Status {response.status_code}: {response.text[:100]}")
except Exception as e:
    print(f"⚠ Could not verify API key: {e}")

print()

# Test 2: Try to execute a simple query
print("Test 2: Testing query execution...")
print("(This will help us find a working query)")

# Try a few common query IDs
test_queries = [
    (2, "Example: Dai daily transfer volume"),
    (107, "BuyOrders"),
]

for query_id, name in test_queries:
    print(f"\nTrying Query #{query_id} ({name})...")
    
    try:
        # Execute query
        execute_url = f"https://api.dune.com/api/v1/query/{query_id}/execute"
        response = requests.post(execute_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            execution = response.json()
            exec_id = execution.get("execution_id")
            print(f"  ✓ Query execution started (ID: {exec_id})")
            
            # Check status
            status_url = f"https://api.dune.com/api/v1/execution/{exec_id}/status"
            for i in range(5):
                time.sleep(2)
                status_resp = requests.get(status_url, headers=headers, timeout=10)
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    state = status_data.get("state")
                    print(f"  Status: {state}")
                    if state == "QUERY_STATE_COMPLETED":
                        print(f"  ✓ Query #{query_id} works! But it's not for active addresses.")
                        print(f"  You'll need to find/create a query for Ethereum active addresses.")
                        break
                    elif state == "QUERY_STATE_FAILED":
                        print(f"  ✗ Query failed")
                        break
        elif response.status_code == 400:
            print(f"  ✗ Bad request - query might not exist or be inaccessible")
        elif response.status_code == 404:
            print(f"  ✗ Query not found")
        else:
            print(f"  ⚠ Status {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
print("Next Steps:")
print("1. Go to https://dune.com")
print("2. Search for 'Ethereum daily active addresses'")
print("3. Find or create a query that returns: date, active_addresses")
print("4. Copy the query ID and use it in get_active_addresses_dune(query_id=YOUR_ID)")

