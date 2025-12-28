#!/usr/bin/env python3
"""
Research data sources for token-based networks: Worldcoin, Hivemapper, DIMO
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

sys.path.insert(0, str(Path(__file__).parent / 'src'))
load_dotenv()

from src.data_collection.coingecko_safe import CoinGeckoSafe

# Networks with confirmed tokens
TOKEN_NETWORKS = {
    'worldcoin': {
        'coingecko_id': 'worldcoin-wld',
        'token': 'WLD',
        'user_metric': 'Unique humans verified (Orb operators)',
        'data_sources_to_check': [
            'Worldcoin API',
            'Worldcoin dashboard',
            'On-chain data (if applicable)',
            'Dune Analytics queries'
        ]
    },
    'hivemapper': {
        'coingecko_id': 'hivemapper',
        'token': 'HONEY',
        'user_metric': 'Active mappers (road segment contributors)',
        'data_sources_to_check': [
            'Hivemapper API',
            'Hivemapper dashboard',
            'On-chain data',
            'Dune Analytics queries'
        ]
    },
    'dimo': {
        'coingecko_id': 'dimo',
        'token': 'DIMO',
        'user_metric': 'Active vehicles/devices',
        'data_sources_to_check': [
            'DIMO API',
            'DIMO dashboard',
            'On-chain data',
            'Dune Analytics queries'
        ]
    }
}

def research_network(network_name, network_config):
    """Research data sources for a network."""
    
    print(f'\n{"="*80}')
    print(f'RESEARCHING: {network_name.upper()} ({network_config["token"]})')
    print(f'{"="*80}')
    
    print(f'\n📊 Token Info:')
    print(f'   CoinGecko ID: {network_config["coingecko_id"]}')
    print(f'   Token: {network_config["token"]}')
    
    print(f'\n👥 User Metric:')
    print(f'   {network_config["user_metric"]}')
    
    print(f'\n🔍 Data Sources to Check:')
    for i, source in enumerate(network_config['data_sources_to_check'], 1):
        print(f'   {i}. {source}')
    
    print(f'\n✅ Market Cap: Available via CoinGecko')
    
    print(f'\n⏳ User Activity: Need to research')
    print(f'   Action items:')
    print(f'   1. Check official API documentation')
    print(f'   2. Check dashboard/explorer')
    print(f'   3. Check for Dune queries')
    print(f'   4. Check on-chain data availability')

def main():
    """Research all token-based networks."""
    
    print("="*80)
    print("TOKEN-BASED NETWORKS RESEARCH")
    print("="*80)
    print("\nNetworks with confirmed tokens:")
    print("  ✅ Worldcoin (WLD)")
    print("  ✅ Hivemapper (HONEY)")
    print("  ✅ DIMO (DIMO)")
    print("\nThese networks have market cap data available.")
    print("Need to find user activity data sources.")
    
    coingecko = CoinGeckoSafe(api_key=os.getenv('COINGECKO_API_KEY'))
    
    # Check market cap data availability
    print(f'\n{"="*80}')
    print("MARKET CAP DATA STATUS")
    print(f'{"="*80}')
    
    for network_name, network_config in TOKEN_NETWORKS.items():
        coin_id = network_config['coingecko_id']
        cache_file = coingecko.cache_dir / f'{coin_id}_market_chart_3650.csv'
        
        if cache_file.exists():
            print(f'\n✅ {network_name.upper()}: Market cap data cached')
        else:
            print(f'\n⏳ {network_name.upper()}: Need to collect market cap data')
            print(f'   Run: python collect_coingecko_safe.py')
    
    # Research each network
    print(f'\n{"="*80}')
    print("USER ACTIVITY DATA RESEARCH")
    print(f'{"="*80}')
    
    for network_name, network_config in TOKEN_NETWORKS.items():
        research_network(network_name, network_config)
    
    print(f'\n{"="*80}')
    print("NEXT STEPS")
    print(f'{"="*80}')
    print("\n1. Collect full historical market cap data (if not cached)")
    print("2. Research user activity data sources for each network")
    print("3. Test API access (if available)")
    print("4. Create data collectors for accessible networks")
    print("5. Run analysis once data is collected")

if __name__ == '__main__':
    main()


