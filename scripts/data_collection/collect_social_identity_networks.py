#!/usr/bin/env python3
"""
Collect Data for Social and Identity Networks

These networks don't have tokens, so we'll use alternative value metrics:
- Social: Engagement metrics, content value, or skip market cap
- Identity: Active resolution count, adoption metrics
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / 'src'))
load_dotenv()

from src.data_collection.ethereum_collector import EthereumDataCollector

# Social/Identity network configurations
SOCIAL_IDENTITY_NETWORKS = {
    'farcaster': {
        'type': 'social',
        'chain': 'ethereum',  # Farcaster is on Ethereum
        'dune_query_id': None,  # Need to find or create
        'value_metric': 'engagement',  # No token, use engagement
        'start_date': '2020-01-01'  # Approximate launch
    },
    'lens': {
        'type': 'social',
        'chain': 'polygon',  # Lens is on Polygon
        'dune_query_id': None,  # Need to find or create
        'value_metric': 'engagement',  # No token, use engagement
        'start_date': '2022-05-01'  # Approximate launch
    },
    'ens': {
        'type': 'identity',
        'chain': 'ethereum',  # ENS is on Ethereum
        'dune_query_id': None,  # Need to find or create
        'value_metric': 'resolutions',  # No token, use resolution count
        'start_date': '2017-05-01'  # ENS launch
    }
}

def collect_network_data(network_name, network_config):
    """Collect data for a social/identity network."""
    
    print(f'\n{"="*80}')
    print(f'COLLECTING DATA: {network_name.upper()} ({network_config["type"].upper()})')
    print(f'{"="*80}')
    
    collector = EthereumDataCollector()
    
    print(f'\n⚠️  Note: {network_name} does not have a token')
    print(f'   Value metric: {network_config["value_metric"]}')
    print(f'   Need to find Dune query or alternative data source')
    
    # Check if we have a Dune query
    query_id = network_config.get('dune_query_id')
    if query_id:
        print(f'\n📊 Dune Query: #{query_id}')
        print(f'   Attempting to fetch CSV results...')
        
        start_date = network_config['start_date']
        end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        try:
            users_df = collector.get_active_addresses_dune_csv(
                query_id=query_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if users_df is not None and not users_df.empty:
                print(f'   ✅ Fetched {len(users_df)} records')
                return users_df
            else:
                print(f'   ⚠️  Query may need execution: https://dune.com/queries/{query_id}')
                return None
        except Exception as e:
            print(f'   ❌ Error: {e}')
            return None
    else:
        print(f'\n⚠️  No Dune query ID available')
        print(f'   Need to:')
        print(f'   1. Find existing Dune query for {network_name}')
        print(f'   2. Create new Dune query')
        print(f'   3. Use alternative data source')
        return None

def main():
    """Collect data for social/identity networks."""
    
    print("="*80)
    print("SOCIAL & IDENTITY NETWORK DATA COLLECTION")
    print("="*80)
    print("\nThese networks don't have tokens, so we need:")
    print("  - User activity data (on-chain)")
    print("  - Alternative value metrics (engagement, resolutions, etc.)")
    
    results = {}
    
    for network_name, network_config in SOCIAL_IDENTITY_NETWORKS.items():
        result = collect_network_data(network_name, network_config)
        if result is not None:
            results[network_name] = result
    
    print(f'\n{"="*80}')
    print("SUMMARY")
    print(f'{"="*80}')
    
    if results:
        print(f'\n✅ Collected data for {len(results)} networks')
    else:
        print(f'\n⚠️  No data collected')
        print(f'   Need to find/create Dune queries for these networks')

if __name__ == '__main__':
    main()


