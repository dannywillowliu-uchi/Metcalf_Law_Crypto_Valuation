#!/usr/bin/env python3
"""
Collect fresh data for Layer 2 networks (Arbitrum, Optimism, Polygon)
from Dune Analytics and CoinGecko
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / 'src'))
load_dotenv()

from src.data_collection.ethereum_collector import EthereumDataCollector
from src.data_collection.coingecko_safe import CoinGeckoSafe

# Layer 2 network configurations
# Dune query IDs from original repository
LAYER2_NETWORKS = {
    'arbitrum': {
        'coingecko_id': 'arbitrum',
        'dune_query_id': 3523740,  # From original repository
        'chain_name': 'arbitrum',
        'start_date': '2021-08-01'  # Arbitrum launched Aug 2021
    },
    'optimism': {
        'coingecko_id': 'optimism',
        'dune_query_id': 3524566,  # From original repository
        'chain_name': 'optimism',
        'start_date': '2021-10-01'  # Optimism launched Oct 2021
    },
    'polygon': {
        'coingecko_id': 'matic-network',
        'dune_query_id': 3524574,  # From original repository
        'chain_name': 'matic-network',
        'start_date': '2019-05-01'  # Polygon launched May 2019
    }
}

def collect_layer2_data(network_name, network_config):
    """Collect data for a single Layer 2 network"""
    
    print(f'\n{"="*80}')
    print(f'COLLECTING DATA: {network_name.upper()}')
    print(f'{"="*80}')
    
    collector = EthereumDataCollector()
    coingecko_safe = CoinGeckoSafe(api_key=os.getenv('COINGECKO_API_KEY'))
    
    # Get date range
    start_date = network_config['start_date']
    end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 1. Get market cap from CoinGecko
    print(f'\n1. Fetching market cap from CoinGecko...')
    print(f'   Date range: {start_date} to {end_date}')
    print(f'   CoinGecko ID: {network_config["coingecko_id"]}')
    
    try:
        # Calculate days
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        days = min((end_dt - start_dt).days, 3650)  # Max 10 years for Analyst Plan
        
        mcap_df = coingecko_safe.get_market_chart(
            coin_id=network_config['coingecko_id'],
            days=days,
            use_cache=True,
            force_refresh=False
        )
        
        if mcap_df is not None and not mcap_df.empty:
            # Filter to date range
            mcap_df['date'] = pd.to_datetime(mcap_df['date'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            mcap_df = mcap_df[(mcap_df['date'] >= start_dt) & (mcap_df['date'] <= end_dt)]
            mcap_df['date'] = mcap_df['date'].dt.date
            
            print(f'   ✓ Fetched {len(mcap_df)} market cap records')
            print(f'   Date range: {mcap_df["date"].min()} to {mcap_df["date"].max()}')
            print(f'   Market cap range: ${mcap_df["market_cap"].min()/1e9:.2f}B to ${mcap_df["market_cap"].max()/1e9:.2f}B')
        else:
            print(f'   ⚠️  No market cap data returned')
            mcap_df = None
            
    except Exception as e:
        print(f'   ✗ Error fetching from CoinGecko: {e}')
        mcap_df = None
    
    # 2. Get active addresses from Dune
    print(f'\n2. Fetching active addresses from Dune...')
    
    query_id = network_config.get('dune_query_id')
    if query_id:
        print(f'   Using Dune query #{query_id}')
        print(f'   ⚠️  Attempting to fetch CSV results (no execution cost)')
        print(f'   If query hasn\'t been run, you may need to execute it once')
        print(f'   Query URL: https://dune.com/queries/{query_id}')
        
        try:
            # First try CSV endpoint (no cost)
            users_df = collector.get_active_addresses_dune_csv(
                query_id=query_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if users_df is not None and not users_df.empty:
                print(f'   ✓ Fetched {len(users_df)} active address records from CSV')
                print(f'   Date range: {users_df["date"].min()} to {users_df["date"].max()}')
                
                # Check column names and standardize
                if 'active_addresses' in users_df.columns:
                    users_df = users_df.rename(columns={'active_addresses': 'users'})
                elif 'dau_nonce_5' in users_df.columns:
                    users_df = users_df.rename(columns={'dau_nonce_5': 'users'})
                elif 'dau' in users_df.columns:
                    users_df = users_df.rename(columns={'dau': 'users'})
                elif 'users' not in users_df.columns:
                    # Try to find any numeric column that might be users
                    numeric_cols = users_df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        users_df = users_df.rename(columns={numeric_cols[0]: 'users'})
                        print(f'   ⚠️  Using column "{numeric_cols[0]}" as users')
                
                if 'users' in users_df.columns:
                    print(f'   Active addresses range: {users_df["users"].min():,.0f} to {users_df["users"].max():,.0f}')
            else:
                print(f'   ⚠️  No data returned from Dune CSV endpoint')
                print(f'   Query may need to be executed first: https://dune.com/queries/{query_id}')
                print(f'   ⚠️  Executing query will cost ~300 credits!')
                users_df = None
            
        except Exception as e:
            print(f'   ✗ CSV fetch failed: {e}')
            print(f'   Query may need to be executed first: https://dune.com/queries/{query_id}')
            print(f'   ⚠️  Executing query will cost ~300 credits!')
            users_df = None
    else:
        print(f'   ✗ No Dune query ID specified for {network_name}')
        users_df = None
    
    # 3. Combine data
    if mcap_df is not None and users_df is not None:
        print(f'\n3. Combining data...')
        
        # Ensure date columns are same type
        if 'date' in users_df.columns:
            users_df['date'] = pd.to_datetime(users_df['date']).dt.date
        if 'date' in mcap_df.columns:
            mcap_df['date'] = pd.to_datetime(mcap_df['date']).dt.date
        
        # Merge on date
        combined_df = pd.merge(
            users_df[['date', 'users']],
            mcap_df[['date', 'market_cap', 'price']],
            on='date',
            how='inner'
        )
        
        # Sort by date
        combined_df = combined_df.sort_values('date').reset_index(drop=True)
        
        print(f'   ✓ Combined {len(combined_df)} records')
        print(f'   Date range: {combined_df["date"].min()} to {combined_df["date"].max()}')
        
        # Save to CSV
        output_path = Path(__file__).parent / 'data' / 'processed' / f'{network_name}_correlated_data.csv'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_csv(output_path, index=False)
        print(f'   ✓ Saved to: {output_path}')
        
        return combined_df
    else:
        print(f'\n   ⚠️  Could not combine data (missing market cap or users data)')
        if mcap_df is None:
            print(f'      - Market cap data missing')
        if users_df is None:
            print(f'      - User activity data missing')
        return None

def main():
    """Collect data for all Layer 2 networks"""
    
    print('='*80)
    print('LAYER 2 DATA COLLECTION')
    print('='*80)
    print('\nThis script collects fresh data from:')
    print('  - CoinGecko: Market cap data')
    print('  - Dune Analytics: Active addresses (nonce >= 5)')
    print('\n⚠️  Note: You need to:')
    print('  1. Set COINGECKO_API_KEY in .env (optional but recommended)')
    print('  2. Set DUNE_API_KEY in .env')
    print('  3. Create Dune queries for each network (or provide query IDs)')
    
    results = {}
    
    for network_name, network_config in LAYER2_NETWORKS.items():
        result = collect_layer2_data(network_name, network_config)
        if result is not None:
            results[network_name] = result
    
    # Summary
    print(f'\n{"="*80}')
    print('SUMMARY')
    print(f'{"="*80}')
    
    if results:
        print(f'\n✓ Successfully collected data for {len(results)} networks:')
        for network_name, df in results.items():
            print(f'  {network_name}: {len(df)} records ({df["date"].min()} to {df["date"].max()})')
    else:
        print(f'\n⚠️  No data collected. Check:')
        print(f'  - API keys are set in .env')
        print(f'  - Dune queries exist for each network')
        print(f'  - Network configurations are correct')

if __name__ == '__main__':
    main()

