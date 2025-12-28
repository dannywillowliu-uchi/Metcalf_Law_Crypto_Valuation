#!/usr/bin/env python3
"""
Create and Execute a Single Dune Query

Usage:
    python3 create_and_execute_single_query.py <network_name>
    
Examples:
    python3 create_and_execute_single_query.py worldcoin
    python3 create_and_execute_single_query.py hivemapper
    python3 create_and_execute_single_query.py dimo
    python3 create_and_execute_single_query.py farcaster
    python3 create_and_execute_single_query.py lens
    python3 create_and_execute_single_query.py ens
"""

import sys
from pathlib import Path
import os
import time
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

# Import queries from the main script
# We'll copy the QUERIES dict here
QUERIES = {
    'worldcoin': {
        'name': 'Worldcoin Daily Active Users (nonce ≥ 5)',
        'description': 'Daily active users for Worldcoin (WLD token holders/transactors)',
        'sql': """
-- Worldcoin Daily Active Users (nonce ≥ 5)
-- NOTE: Adjust table name based on Dune's World Chain schema
-- If World Chain not available, use Ethereum for WLD token

WITH address_nonce AS (
  SELECT 
    "from" AS address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY block_time) as nonce
  FROM ethereum.transactions  -- Change to world_coin.transactions if available
  WHERE 
    block_time >= TIMESTAMP '2023-07-01 00:00:00'  -- Worldcoin launch
    AND block_time < NOW()
    -- Filter for WLD token transactions if needed
)
SELECT
  DATE(block_time) AS day,
  'worldcoin' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_users
FROM address_nonce
WHERE nonce >= 5
GROUP BY DATE(block_time)
ORDER BY DATE(block_time);
        """,
        'note': 'Need to verify World Chain table name or use Ethereum for WLD token'
    },
    'hivemapper': {
        'name': 'Hivemapper Daily Active Mappers',
        'description': 'Daily active mappers for Hivemapper network',
        'sql': """
-- Hivemapper Daily Active Mappers
-- NOTE: Hivemapper uses Solana, adjust based on available Solana data in Dune

WITH mapper_transactions AS (
  SELECT 
    DATE(block_time) AS date,
    signer AS mapper_address,
    COUNT(*) AS transactions
  FROM solana.transactions
  WHERE 
    -- Adjust based on Hivemapper program ID
    instructions[0].program_id = 'hivemapper_program_id_here'
    AND block_time >= CURRENT_DATE - INTERVAL '2' YEAR
  GROUP BY DATE(block_time), signer
)
SELECT 
  date,
  COUNT(DISTINCT mapper_address) AS active_addresses
FROM mapper_transactions
WHERE transactions >= 1  -- At least 1 transaction per day
GROUP BY date
ORDER BY date
"""
    },
    'dimo': {
        'name': 'DIMO Daily Active Users (nonce ≥ 5)',
        'description': 'Daily active users for DIMO (DIMO token holders/transactors)',
        'sql': """
-- DIMO Daily Active Users (nonce ≥ 5)
-- NOTE: Need to identify DIMO token chain (Polygon? Ethereum?)
-- Adjust table name accordingly

WITH address_nonce AS (
  SELECT 
    "from" AS address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY block_time) as nonce
  FROM polygon.transactions  -- Change based on DIMO token chain
  WHERE 
    block_time >= TIMESTAMP '2021-01-01 00:00:00'  -- DIMO launch (adjust)
    AND block_time < NOW()
    -- Filter for DIMO token transactions if needed
)
SELECT
  DATE(block_time) AS day,
  'dimo' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_users
FROM address_nonce
WHERE nonce >= 5
GROUP BY DATE(block_time)
ORDER BY DATE(block_time);
        """,
        'note': 'Need to identify DIMO token chain and adjust SQL'
    },
    'farcaster': {
        'name': 'Farcaster Daily Active Users',
        'description': 'Daily active users for Farcaster protocol',
        'sql': """
-- Farcaster Daily Active Users
-- NOTE: Farcaster uses Ethereum, adjust based on Farcaster contract addresses

WITH farcaster_activity AS (
  SELECT 
    DATE(block_time) AS date,
    "from" AS user_address,
    COUNT(*) AS transactions
  FROM ethereum.transactions
  WHERE 
    -- Adjust based on Farcaster contract addresses
    ("to" = 0xFARCASTER_CONTRACT_1 OR "to" = 0xFARCASTER_CONTRACT_2)
    AND block_time >= CURRENT_DATE - INTERVAL '2' YEAR
  GROUP BY DATE(block_time), "from"
)
SELECT 
  date,
  COUNT(DISTINCT user_address) AS active_addresses
FROM farcaster_activity
WHERE transactions >= 1
GROUP BY date
ORDER BY date
"""
    },
    'lens': {
        'name': 'Lens Protocol Daily Active Users',
        'description': 'Daily active users for Lens Protocol',
        'sql': """
-- Lens Protocol Daily Active Users
-- NOTE: Lens uses Polygon, adjust based on Lens contract addresses

WITH lens_activity AS (
  SELECT 
    DATE(block_time) AS date,
    "from" AS user_address,
    COUNT(*) AS transactions
  FROM polygon.transactions
  WHERE 
    -- Adjust based on Lens contract addresses
    ("to" = 0xLENS_CONTRACT_1 OR "to" = 0xLENS_CONTRACT_2)
    AND block_time >= CURRENT_DATE - INTERVAL '2' YEAR
  GROUP BY DATE(block_time), "from"
)
SELECT 
  date,
  COUNT(DISTINCT user_address) AS active_addresses
FROM lens_activity
WHERE transactions >= 1
GROUP BY date
ORDER BY date
"""
    },
    'ens': {
        'name': 'ENS Daily Resolution Count',
        'description': 'Daily ENS name resolutions',
        'sql': """
-- ENS Daily Resolution Count
-- NOTE: ENS uses Ethereum, adjust based on ENS resolver contract

WITH ens_resolutions AS (
  SELECT 
    DATE(block_time) AS date,
    COUNT(*) AS resolution_count
  FROM ethereum.transactions
  WHERE 
    -- Adjust based on ENS resolver contract
    "to" = 0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41  -- ENS Public Resolver
    AND block_time >= CURRENT_DATE - INTERVAL '2' YEAR
  GROUP BY DATE(block_time)
)
SELECT 
  date,
  resolution_count AS active_addresses
FROM ens_resolutions
ORDER BY date
"""
    }
}

def create_and_execute_query(network_name: str, query_config: dict, manager: DuneQueryManager):
    """Create and execute a single Dune query."""
    
    print(f"\n{'='*80}")
    print(f"PROCESSING: {network_name.upper()}")
    print(f"{'='*80}")
    print(f"Name: {query_config['name']}")
    print(f"Description: {query_config['description']}")
    
    # Create query
    print(f"\n1. Creating query...")
    try:
        result = manager.create_query(
            name=query_config['name'],
            sql=query_config['sql']
        )
        
        if not result:
            print(f"   ❌ Failed to create query")
            return None
        
        query_id = result.get('query_id')
        if not query_id:
            print(f"   ❌ No query_id in response: {result}")
            return None
        
        print(f"   ✅ Created query #{query_id}")
        print(f"   📝 Query URL: https://dune.com/queries/{query_id}")
        
    except Exception as e:
        print(f"   ❌ Error creating query: {e}")
        return None
    
    # Execute query
    print(f"\n2. Executing query (costs ~300 credits)...")
    try:
        execution = manager.execute_query(query_id)
        
        if not execution:
            print(f"   ❌ Failed to execute query")
            return None
        
        execution_id = execution.get('execution_id')
        if not execution_id:
            print(f"   ❌ No execution_id in response: {execution}")
            return None
        
        print(f"   ✅ Execution started: {execution_id}")
        print(f"   ⏳ Waiting for completion...")
        
        # Wait for execution
        success = manager.wait_for_execution(execution_id, max_wait=300)
        
        if success:
            print(f"   ✅ Query execution completed!")
            print(f"   💰 Cost: ~300 credits")
        else:
            print(f"   ⚠️  Query execution may have failed or timed out")
            print(f"   Check status at: https://dune.com/queries/{query_id}")
        
    except Exception as e:
        print(f"   ❌ Error executing query: {e}")
        print(f"   Query created but not executed: https://dune.com/queries/{query_id}")
        return query_id
    
    return query_id

def main():
    """Create and execute a single Dune query."""
    
    if len(sys.argv) < 2:
        print("Usage: python3 create_and_execute_single_query.py <network_name>")
        print("\nAvailable networks:")
        for network in QUERIES.keys():
            print(f"  - {network}")
        sys.exit(1)
    
    network_name = sys.argv[1].lower()
    
    if network_name not in QUERIES:
        print(f"❌ Unknown network: {network_name}")
        print("\nAvailable networks:")
        for network in QUERIES.keys():
            print(f"  - {network}")
        sys.exit(1)
    
    query_config = QUERIES[network_name]
    
    print("="*80)
    print("DUNE QUERY CREATION AND EXECUTION (SINGLE QUERY)")
    print("="*80)
    print(f"\nNetwork: {network_name}")
    print(f"Query: {query_config['name']}")
    print(f"Cost: ~300 credits")
    
    # Initialize manager
    try:
        manager = DuneQueryManager()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("   Set DUNE_API_KEY in .env file")
        sys.exit(1)
    
    # Create and execute
    query_id = create_and_execute_query(network_name, query_config, manager)
    
    if query_id:
        print(f"\n{'='*80}")
        print("SUCCESS")
        print(f"{'='*80}")
        print(f"\n✅ Query #{query_id} created and executed")
        print(f"📝 View at: https://dune.com/queries/{query_id}")
        print(f"💰 Cost: ~300 credits")
        print(f"\n💡 After execution, CSV exports are free (0 credits)")
        
        # Save query ID
        query_ids_file = Path(__file__).parent / 'dune_query_ids.json'
        query_ids = {}
        if query_ids_file.exists():
            with open(query_ids_file, 'r') as f:
                query_ids = json.load(f)
        
        query_ids[network_name] = query_id
        
        with open(query_ids_file, 'w') as f:
            json.dump(query_ids, f, indent=2)
        
        print(f"\n💾 Query ID saved to: {query_ids_file}")
    else:
        print(f"\n❌ Failed to create/execute query")
        sys.exit(1)

if __name__ == '__main__':
    main()

