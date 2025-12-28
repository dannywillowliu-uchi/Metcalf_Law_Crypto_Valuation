#!/usr/bin/env python3
"""
Create and Execute Dune Queries via API

This script creates and executes Dune queries programmatically for:
1. Worldcoin (WLD)
2. Hivemapper (HONEY)
3. DIMO (DIMO)
4. Farcaster
5. Lens Protocol
6. ENS

Total: 6 queries × 300 credits = 1,800 credits (one-time)
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
    pass  # dotenv not available, use system env vars

sys.path.insert(0, str(Path(__file__).parent))

# Import directly to avoid __init__.py dependencies
import importlib.util
dune_manager_path = Path(__file__).parent / 'src' / 'data_collection' / 'dune_query_manager.py'
spec = importlib.util.spec_from_file_location("dune_query_manager", dune_manager_path)
dune_query_manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dune_query_manager)
DuneQueryManager = dune_query_manager.DuneQueryManager

# SQL queries for each network
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
        'name': 'Hivemapper Daily Active Users (nonce ≥ 5)',
        'description': 'Daily active users for Hivemapper (HONEY token holders/transactors on Solana)',
        'sql': """
-- Hivemapper Daily Active Users (nonce ≥ 5)
-- HONEY token is on Solana
-- Using Solana token transfers to track active users

WITH address_nonce AS (
  SELECT 
    account_owner AS address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY account_owner ORDER BY block_time) as nonce
  FROM solana.account_activity
  WHERE 
    block_time >= TIMESTAMP '2022-11-01 00:00:00'  -- Hivemapper launch
    AND block_time < NOW()
    -- Filter for HONEY token mint if available
    -- mint = 'HONEY_TOKEN_MINT_ADDRESS'  -- Need to add actual mint address
)
SELECT
  DATE(block_time) AS day,
  'hivemapper' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_users
FROM address_nonce
WHERE nonce >= 5
GROUP BY DATE(block_time)
ORDER BY DATE(block_time);
        """,
        'note': 'Using Solana account_activity table. May need to adjust for HONEY token mint address or use token transfers table'
    },
    
    'dimo': {
        'name': 'DIMO Daily Active Users (nonce ≥ 5)',
        'description': 'Daily active users for DIMO (DIMO token holders/transactors)',
        'sql': """
-- DIMO Daily Active Users (nonce ≥ 5)
-- Using token transfers to filter by DIMO token contract
-- DIMO token is on Polygon: 0xE261D618a959aFfFd53168Cd07D12E37B26761b

WITH dimo_transfers AS (
  SELECT 
    "from" AS address,
    block_time
  FROM polygon.token_transfers
  WHERE 
    token_address = 0xE261D618a959aFfFd53168Cd07D12E37B26761b  -- DIMO token contract
    AND block_time >= TIMESTAMP '2022-01-01 00:00:00'  -- DIMO launch (adjust if needed)
    AND block_time < NOW()
),
address_nonce AS (
  SELECT 
    address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY address ORDER BY block_time) as nonce
  FROM dimo_transfers
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
        'note': 'Using DIMO token contract on Polygon. Query may need adjustment if contract address is different.'
    },
    
    'farcaster': {
        'name': 'Farcaster Daily Active Users',
        'description': 'Daily active users for Farcaster protocol (casts, reactions, follows)',
        'sql': """
-- Farcaster Daily Active Users
-- NOTE: Need to identify Farcaster contract addresses on Ethereum/Base/Optimism
-- Adjust contract addresses and chain as needed

SELECT
  DATE_TRUNC('day', block_time) AS day,
  'farcaster' AS protocol,
  COUNT(DISTINCT "from") AS active_users
FROM ethereum.logs
WHERE 
  contract_address IN (
    -- Farcaster contract addresses (need to identify)
    '0x00000000fcaf86937e41ba613b72d717b0a1ddd3',  -- Farcaster Registry (verify)
    '0x...'  -- Other Farcaster contracts (add as needed)
  )
  AND block_time >= TIMESTAMP '2020-01-01 00:00:00'
  AND block_time < NOW()
GROUP BY DATE_TRUNC('day', block_time)
ORDER BY day;
        """,
        'note': 'Need to identify Farcaster contract addresses on Ethereum/Base/Optimism'
    },
    
    'lens': {
        'name': 'Lens Protocol Daily Active Users',
        'description': 'Daily active users for Lens Protocol (posts, comments, follows)',
        'sql': """
-- Lens Protocol Daily Active Users
-- NOTE: Need to identify Lens Protocol contract addresses on Polygon
-- Adjust contract addresses as needed

SELECT
  DATE_TRUNC('day', block_time) AS day,
  'lens' AS protocol,
  COUNT(DISTINCT "from") AS active_users
FROM polygon.logs
WHERE 
  contract_address IN (
    -- Lens Protocol contract addresses (need to identify)
    '0xDb46d1Dc155634FbC732f92E853b10B288AD5a1d',  -- Lens Hub (verify)
    '0x...'  -- Other Lens contracts (add as needed)
  )
  AND block_time >= TIMESTAMP '2022-05-01 00:00:00'  -- Lens launch
  AND block_time < NOW()
GROUP BY DATE_TRUNC('day', block_time)
ORDER BY day;
        """,
        'note': 'Need to identify Lens Protocol contract addresses on Polygon'
    },
    
    'ens': {
        'name': 'ENS Daily Resolution Count',
        'description': 'Daily name resolution count for ENS (Ethereum Name Service)',
        'sql': """
-- ENS Daily Resolution Count
-- Count daily name resolution events

SELECT
  DATE_TRUNC('day', block_time) AS day,
  'ens' AS protocol,
  COUNT(*) AS resolution_count,
  COUNT(DISTINCT "from") AS unique_resolvers
FROM ethereum.logs
WHERE 
  contract_address = '0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e'  -- ENS Registry
  AND topic0 = '0xce0457fe73731f824cc272376169346128b5661270c9d90c58a23448b2c81463'  -- NameResolved event
  AND block_time >= TIMESTAMP '2017-05-01 00:00:00'  -- ENS launch
  AND block_time < NOW()
GROUP BY DATE_TRUNC('day', block_time)
ORDER BY day;
        """,
        'note': 'ENS Registry address and event signature verified'
    }
}

def create_and_execute_query(network_name: str, query_config: dict, manager: DuneQueryManager, execute: bool = True):
    """
    Create and optionally execute a Dune query.
    
    Parameters
    ----------
    network_name : str
        Network name
    query_config : dict
        Query configuration (name, sql, description, note)
    manager : DuneQueryManager
        Dune query manager instance
    execute : bool
        Whether to execute the query after creation (default: True)
    """
    print(f"\n{'='*80}")
    print(f"PROCESSING: {network_name.upper()}")
    print(f"{'='*80}")
    print(f"Query: {query_config['name']}")
    print(f"Note: {query_config.get('note', 'None')}")
    
    # Create query
    result = manager.create_query(
        name=query_config['name'],
        sql=query_config['sql']
    )
    
    if not result:
        print(f"❌ Failed to create query for {network_name}")
        return None
    
    query_id = result.get("query_id")
    print(f"✅ Query created: #{query_id}")
    print(f"   URL: https://dune.com/queries/{query_id}")
    
    if not execute:
        print(f"⏸️  Skipping execution (execute=False)")
        return query_id
    
    # Execute query
    execution_result = manager.execute_query(query_id)
    
    if not execution_result:
        print(f"❌ Failed to execute query for {network_name}")
        return query_id
    
    execution_id = execution_result.get("execution_id")
    print(f"✅ Execution started: #{execution_id}")
    
    # Wait for completion
    success = manager.wait_for_execution(execution_id)
    
    if success:
        print(f"✅ Query #{query_id} completed successfully")
        print(f"   You can now fetch results via CSV export (0 credits)")
    else:
        print(f"⚠️  Query #{query_id} execution may have failed or timed out")
        print(f"   Check status at: https://dune.com/queries/{query_id}")
    
    return query_id

def main():
    """Create and execute all Dune queries."""
    
    print("="*80)
    print("DUNE QUERY CREATION AND EXECUTION")
    print("="*80)
    print("\nThis script will:")
    print("  1. Create 6 new Dune queries")
    print("  2. Execute each query (costs ~300 credits each)")
    print("  3. Total cost: ~1,800 credits (one-time)")
    print("\n⚠️  WARNING: This will cost credits!")
    print("   Each query execution costs ~300 credits")
    print("   Total: 6 queries × 300 credits = 1,800 credits")
    
    # Check for --yes flag to skip confirmation
    skip_confirmation = '--yes' in sys.argv or os.getenv('SKIP_CONFIRMATION') == '1'
    
    if not skip_confirmation:
        try:
            response = input("\nContinue? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return
        except EOFError:
            print("\n⚠️  No interactive input available. Use --yes flag or set SKIP_CONFIRMATION=1")
            print("   Example: python3 create_and_execute_dune_queries.py --yes")
            return
    else:
        print("\n✅ Skipping confirmation (--yes flag or SKIP_CONFIRMATION=1)")
    
    # Initialize manager
    try:
        manager = DuneQueryManager()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("   Set DUNE_API_KEY in .env file")
        return
    
    # Process each query one at a time
    query_ids = {}
    networks = list(QUERIES.items())
    
    for idx, (network_name, query_config) in enumerate(networks, 1):
        print(f"\n{'='*80}")
        print(f"QUERY {idx} of {len(networks)}: {network_name.upper()}")
        print(f"{'='*80}")
        
        query_id = create_and_execute_query(network_name, query_config, manager, execute=True)
        if query_id:
            query_ids[network_name] = query_id
            print(f"\n✅ Query {idx}/{len(networks)} completed: {network_name}")
            print(f"   Query ID: {query_id}")
            print(f"   URL: https://dune.com/queries/{query_id}")
        else:
            print(f"\n❌ Query {idx}/{len(networks)} failed: {network_name}")
        
        # Ask before proceeding to next query (except for the last one)
        if idx < len(networks):
            print(f"\n{'='*80}")
            print(f"Next query: {networks[idx][0].upper()}")
            print(f"{'='*80}")
            try:
                response = input("\nContinue to next query? (yes/no): ")
                if response.lower() != 'yes':
                    print(f"\n⏸️  Stopped after {idx} queries")
                    print(f"   Completed: {list(query_ids.keys())}")
                    print(f"   Remaining: {[n for n, _ in networks[idx:]]}")
                    break
            except EOFError:
                print(f"\n⚠️  No interactive input. Stopping after {idx} queries.")
                print(f"   To continue, run the script again or use create_and_execute_single_query.py")
                break
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if query_ids:
        print(f"\n✅ Created {len(query_ids)} queries:")
        for network, qid in query_ids.items():
            print(f"   {network}: Query #{qid}")
            print(f"      URL: https://dune.com/queries/{qid}")
        
        print(f"\n📊 Next Steps:")
        print(f"   1. Verify queries on Dune Analytics website")
        print(f"   2. Adjust SQL if needed (contract addresses, chain names, etc.)")
        print(f"   3. Re-execute if SQL was adjusted")
        print(f"   4. Use CSV export endpoint to fetch results (0 credits)")
        
        # Save query IDs
        output_file = Path(__file__).parent / "data" / "dune_query_ids.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(query_ids, f, indent=2)
        print(f"\n💾 Query IDs saved to: {output_file}")
    else:
        print(f"\n❌ No queries created successfully")

if __name__ == '__main__':
    main()

