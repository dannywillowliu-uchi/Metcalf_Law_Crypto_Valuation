#!/usr/bin/env python3
"""
Analyze Compute & AI Marketplace Networks

Tests the framework on compute networks to answer:
"Do these networks have real network effects or just token incentives?"

Networks to analyze:
- Render Network (RNDR)
- Akash Network (AKT)
- Bittensor (TAO)
- Gensyn
- io.net
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import numpy as np
from analysis.markov_switching import FTPMSModel
from analysis.metcalfe_model import MetcalfeModel
import warnings
warnings.filterwarnings('ignore')

# Compute network configurations
COMPUTE_NETWORKS = {
    'render': {
        'coingecko_id': 'render-token',
        'token_symbol': 'RNDR',
        'launch_date': '2020-06-01',  # Approximate
        'user_definition': 'weighted_composite',  # providers × 1.5 + consumers × 1.0
        'value_metric': 'market_cap',  # Can also use revenue/compute hours if available
        'expected_beta_range': [1.8, 2.5]  # From research direction doc
    },
    'akash': {
        'coingecko_id': 'akash-network',
        'token_symbol': 'AKT',
        'launch_date': '2021-03-01',  # Approximate
        'user_definition': 'weighted_composite',
        'value_metric': 'market_cap',
        'expected_beta_range': [1.8, 2.5]
    },
    'bittensor': {
        'coingecko_id': 'bittensor',
        'token_symbol': 'TAO',
        'launch_date': '2021-01-01',  # Approximate
        'user_definition': 'weighted_composite',
        'value_metric': 'market_cap',
        'expected_beta_range': [1.8, 2.5]
    }
}

def calculate_weighted_users(providers: np.ndarray, consumers: np.ndarray) -> np.ndarray:
    """
    Calculate weighted composite users for compute networks.
    
    Formula: providers × 1.5 + consumers × 1.0
    
    This weights providers more heavily as they're more critical to network value.
    """
    return providers * 1.5 + consumers * 1.0

def analyze_compute_network(network_name: str, network_config: dict):
    """
    Analyze a compute network using the framework.
    
    For compute networks:
    - Users: Weighted composite (providers × 1.5 + consumers × 1.0)
    - Value: Market cap (or revenue/compute hours if available)
    """
    
    print(f'\n{"="*80}')
    print(f'ANALYZING COMPUTE NETWORK: {network_name.upper()}')
    print(f'{"="*80}')
    
    # TODO: Collect data
    # For now, this is a placeholder structure
    print(f'\nNetwork Configuration:')
    print(f'  CoinGecko ID: {network_config["coingecko_id"]}')
    print(f'  Token: {network_config["token_symbol"]}')
    print(f'  Launch: {network_config["launch_date"]}')
    print(f'  User definition: {network_config["user_definition"]}')
    print(f'  Value metric: {network_config["value_metric"]}')
    print(f'  Expected β range: {network_config["expected_beta_range"]}')
    
    print(f'\n⚠️  Data collection not yet implemented')
    print(f'   Need to collect:')
    print(f'   1. Provider count (daily)')
    print(f'   2. Consumer count (daily)')
    print(f'   3. Market cap (daily) - from CoinGecko')
    print(f'   4. Optional: Revenue, compute hours, fees')
    
    print(f'\nOnce data is collected, will:')
    print(f'  1. Calculate weighted users: providers × 1.5 + consumers × 1.0')
    print(f'  2. Fit base Metcalfe model: ln(value) = α + β ln(users)')
    print(f'  3. Fit Markov-switching model')
    print(f'  4. Check if β > 1.0 (real network effects) or β < 1.0 (token incentives)')
    
    return None

def main():
    """Analyze compute networks"""
    
    print('='*80)
    print('COMPUTE NETWORK ANALYSIS')
    print('='*80)
    print('\nResearch Question:')
    print('  Do compute networks have real network effects (β > 1.0)')
    print('  or are they just token incentive schemes (β < 1.0)?')
    
    print('\nExpected Results (from research direction):')
    print('  If real network effects: β in range [1.8, 2.5]')
    print('  If token incentives: β < 1.0 (like Layer 2s)')
    
    results = []
    
    for network_name, network_config in COMPUTE_NETWORKS.items():
        result = analyze_compute_network(network_name, network_config)
        if result:
            results.append(result)
    
    print(f'\n{"="*80}')
    print('NEXT STEPS')
    print(f'{"="*80}')
    print('\nTo complete compute network analysis:')
    print('  1. Identify data sources for each network')
    print('     - On-chain data (provider/consumer counts)')
    print('     - APIs (if available)')
    print('     - Blockchain explorers')
    print('  2. Implement data collection')
    print('  3. Run analysis')
    print('  4. Compare results with Layer 2s')

if __name__ == '__main__':
    main()

