#!/usr/bin/env python3
"""Execute Dune query #4062489 ONCE - Multi-chain DAU data"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import time

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from dune_client.client import DuneClient
from dune_client.query import QueryBase
import pandas as pd

api_key = os.getenv("DUNE_API_KEY")
if not api_key:
    print("❌ DUNE_API_KEY not found in .env")
    sys.exit(1)

print("Executing Dune Query #4062489 - ONE TIME ONLY")
print("=" * 60)
print("⚠️  This will execute the query (50 credit limit)")
print("=" * 60)

dune = DuneClient(api_key=api_key)

# Execute query ONCE
query = QueryBase(query_id=4062489, name="Multi-Chain DAU")
print(f"\nExecuting query #{4062489}...")
execution = dune.execute_query(query)

execution_id = execution.execution_id
print(f"Execution ID: {execution_id}")
print(f"Waiting for query to complete...")

# Poll for results (up to 10 minutes)
max_attempts = 300  # 10 minutes
for attempt in range(max_attempts):
    if attempt > 0:
        time.sleep(2)
    
    result_data = dune.get_result(execution_id)
    state = result_data.state if hasattr(result_data, 'state') else str(result_data)
    
    if attempt % 30 == 0:  # Print every minute
        print(f"  Status: {state} (attempt {attempt+1}/{max_attempts})")
    
    if state == "QUERY_STATE_COMPLETED":
        print(f"\n✓ Query completed!")
        
        # Get results
        try:
            df = dune.get_result_dataframe(execution_id)
            print(f"✓ Fetched {len(df)} records")
            print(f"\nColumns: {df.columns.tolist()}")
            print(f"\nFirst 5 rows:")
            print(df.head())
            
            # Save to file
            output_path = Path("data/processed/multi_chain_dau.csv")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"\n✓ Saved to: {output_path}")
            break
            
        except Exception as e:
            print(f"✗ Error getting results: {e}")
            break
            
    elif state == "QUERY_STATE_FAILED":
        error_msg = result_data.error if hasattr(result_data, 'error') else 'Unknown error'
        print(f"\n✗ Query failed: {error_msg}")
        break
else:
    print(f"\n⚠️  Query still running after {max_attempts * 2} seconds")
    print(f"Check status at: https://dune.com/queries/4062489")

print("\n" + "=" * 60)
print("Execution complete. Check Dune dashboard for credit usage.")

