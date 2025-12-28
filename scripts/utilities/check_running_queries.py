#!/usr/bin/env python3
"""
Check if any Dune queries are currently running
"""

import sys
from pathlib import Path
import os
import json
import requests
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check_query_execution_status(query_id, api_key):
    """Check if a query has any recent executions."""
    headers = {
        "X-DUNE-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Try to get query info
    url = f"https://api.dune.com/api/v1/query/{query_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            query_info = response.json()
            return query_info
        else:
            return None
    except Exception as e:
        print(f"   ⚠️  Error checking query: {e}")
        return None

def main():
    """Check status of queries."""
    
    api_key = os.getenv("DUNE_API_KEY")
    if not api_key:
        print("❌ DUNE_API_KEY not found")
        sys.exit(1)
    
    print("="*80)
    print("CHECKING FOR RUNNING QUERIES")
    print("="*80)
    
    # Load query IDs
    query_ids = {}
    
    data_file = Path(__file__).parent / 'data' / 'dune_query_ids.json'
    if data_file.exists():
        with open(data_file, 'r') as f:
            query_ids.update(json.load(f))
    
    root_file = Path(__file__).parent / 'dune_query_ids.json'
    if root_file.exists():
        with open(root_file, 'r') as f:
            query_ids.update(json.load(f))
    
    if not query_ids:
        print("⚠️  No query IDs found")
        return
    
    print(f"\n📊 Checking {len(query_ids)} queries...")
    print("\n💡 Note: 409 errors may indicate:")
    print("   - Query is still running")
    print("   - Query failed")
    print("   - Query hasn't been executed")
    print("   - Rate limiting")
    print("\n   Check queries directly on Dune to see actual status:")
    
    for network, query_id in query_ids.items():
        print(f"\n{network.upper()}: Query #{query_id}")
        print(f"   URL: https://dune.com/queries/{query_id}")
        
        # Try to get query info
        query_info = check_query_execution_status(query_id, api_key)
        if query_info:
            print(f"   ✅ Query exists")
            # Check if we can get more info
            if 'name' in query_info:
                print(f"   Name: {query_info.get('name', 'N/A')}")
        else:
            print(f"   ⚠️  Could not fetch query info")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)
    print("\nTo check if queries are running:")
    print("1. Visit each query URL above")
    print("2. Look for execution status (Running, Completed, Failed)")
    print("3. If running: Wait for completion")
    print("4. If failed: Check error message and fix SQL")
    print("5. If not executed: Execute via API or Dune website")

if __name__ == '__main__':
    main()

