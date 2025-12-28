#!/usr/bin/env python3
"""
Check status of all Dune queries
"""

import sys
from pathlib import Path
import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

# Import DuneQueryManager
import importlib.util
dune_manager_path = Path(__file__).parent / 'src' / 'data_collection' / 'dune_query_manager.py'
spec = importlib.util.spec_from_file_location("dune_query_manager", dune_manager_path)
dune_query_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dune_query_manager)
DuneQueryManager = dune_query_manager.DuneQueryManager

def check_query_status(query_id, manager):
    """Check if a query has results available."""
    print(f"\nQuery #{query_id}:")
    print(f"   URL: https://dune.com/queries/{query_id}")
    
    # Try to get CSV results (will return 404 if not executed or no results)
    csv = manager.get_query_results_csv(query_id)
    
    if csv:
        lines = csv.strip().split('\n')
        print(f"   ✅ Status: Has results ({len(lines)} lines)")
        if len(lines) > 1:
            print(f"   📊 First row: {lines[0]}")
            print(f"   📊 Sample data: {lines[1][:100]}...")
        return "has_results"
    else:
        print(f"   ⚠️  Status: No results (query may not be executed or failed)")
        return "no_results"

def main():
    """Check status of all queries."""
    
    print("="*80)
    print("CHECKING DUNE QUERY STATUS")
    print("="*80)
    
    # Initialize manager
    try:
        manager = DuneQueryManager()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("   Set DUNE_API_KEY in .env file")
        sys.exit(1)
    
    # Load query IDs from both files
    query_ids = {}
    
    # Check data/dune_query_ids.json
    data_file = Path(__file__).parent / 'data' / 'dune_query_ids.json'
    if data_file.exists():
        with open(data_file, 'r') as f:
            data_queries = json.load(f)
            query_ids.update(data_queries)
            print(f"\n📁 Loaded from data/dune_query_ids.json: {len(data_queries)} queries")
    
    # Check root dune_query_ids.json
    root_file = Path(__file__).parent / 'dune_query_ids.json'
    if root_file.exists():
        with open(root_file, 'r') as f:
            root_queries = json.load(f)
            query_ids.update(root_queries)
            print(f"📁 Loaded from dune_query_ids.json: {len(root_queries)} queries")
    
    if not query_ids:
        print("\n⚠️  No query IDs found in JSON files")
        print("   Checked:")
        print(f"   - {data_file}")
        print(f"   - {root_file}")
        return
    
    print(f"\n📊 Found {len(query_ids)} queries to check")
    print("\n" + "="*80)
    
    # Check each query
    status_summary = {
        "has_results": [],
        "no_results": []
    }
    
    for network, query_id in query_ids.items():
        status = check_query_status(query_id, manager)
        if status == "has_results":
            status_summary["has_results"].append((network, query_id))
        else:
            status_summary["no_results"].append((network, query_id))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if status_summary["has_results"]:
        print(f"\n✅ Queries with results ({len(status_summary['has_results'])}):")
        for network, query_id in status_summary["has_results"]:
            print(f"   - {network}: Query #{query_id}")
    
    if status_summary["no_results"]:
        print(f"\n⚠️  Queries without results ({len(status_summary['no_results'])}):")
        for network, query_id in status_summary["no_results"]:
            print(f"   - {network}: Query #{query_id}")
            print(f"     → Check at: https://dune.com/queries/{query_id}")
    
    print("\n💡 Note: Queries without results may:")
    print("   1. Not have been executed yet")
    print("   2. Have failed during execution")
    print("   3. Still be running (check on Dune website)")

if __name__ == '__main__':
    main()

