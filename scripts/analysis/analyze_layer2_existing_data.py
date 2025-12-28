#!/usr/bin/env python3
"""
Analyze Layer 2 Networks Using Existing Data

Uses data from Blockchain_NetworkValue repository to analyze Arbitrum, Optimism, and Polygon.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from analysis.metcalfe_model import MetcalfeModel
from analysis.markov_switching import FTPMSModel
import warnings
warnings.filterwarnings('ignore')

# Layer 2 network configurations
LAYER2_NETWORKS = {
    'arbitrum': {
        'file': Path(__file__).parent.parent / 'Blockchain_NetworkValue' / 'New_filtering _conditions' / 'arbitrum_all_trend.csv',
        'users_col': 'dau_nonce_5_gas_dot001',  # Use nonce >= 5 with gas filter
        'paper_beta1': None,
        'paper_beta2': None,
    },
    'optimism': {
        'file': Path(__file__).parent.parent / 'Blockchain_NetworkValue' / 'Data_Dune_MktCap' / 'optimism_all_trend.csv',
        'users_col': 'dau_nonce_5',  # Use nonce >= 5
        'paper_beta1': 0.98,
        'paper_beta2': -12.57,
    },
    'polygon': {
        'file': Path(__file__).parent.parent / 'Blockchain_NetworkValue' / 'New_filtering _conditions' / 'polygon_all_trend.csv',
        'users_col': 'dau_nonce_5',  # Use nonce >= 5
        'paper_beta1': 0.81,
        'paper_beta2': 0.67,
    }
}

def analyze_layer2_network(network_name, network_config):
    """Analyze a Layer 2 network using existing data."""
    
    print(f'\n{"="*80}')
    print(f'ANALYZING: {network_name.upper()}')
    print(f'{"="*80}')
    
    # Load data
    data_file = network_config['file']
    users_col = network_config['users_col']
    
    if not data_file.exists():
        print(f'❌ Error: Data file not found: {data_file}')
        return None
    
    df = pd.read_csv(data_file)
    
    # Find date column
    date_col = 'day' if 'day' in df.columns else 'date'
    if date_col not in df.columns:
        print(f'❌ Error: Could not find date column')
        return None
    
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Check for users column
    if users_col not in df.columns:
        # Try alternatives
        alternatives = ['dau_nonce_5', 'dau_nonce_10', 'dau', 'active_addresses']
        for alt in alternatives:
            if alt in df.columns:
                users_col = alt
                print(f'⚠️  Using alternative column: {users_col}')
                break
        else:
            print(f'❌ Error: Could not find users column')
            print(f'   Available columns: {list(df.columns)}')
            return None
    
    # Check for market cap column
    mcap_col = None
    for col in ['Market_cap', 'market_cap', 'mcap']:
        if col in df.columns:
            mcap_col = col
            break
    
    if mcap_col is None:
        print(f'❌ Error: Could not find market cap column')
        print(f'   Available columns: {list(df.columns)}')
        return None
    
    print(f'\n📊 Data Summary:')
    print(f'   File: {data_file.name}')
    print(f'   Records: {len(df)}')
    print(f'   Date range: {df[date_col].min()} to {df[date_col].max()}')
    print(f'   Users column: {users_col}')
    print(f'   Market cap column: {mcap_col}')
    
    # Clean data
    df = df[[date_col, users_col, mcap_col]].copy()
    df = df.dropna()
    
    # Convert to numeric
    df[users_col] = pd.to_numeric(df[users_col], errors='coerce')
    df[mcap_col] = pd.to_numeric(df[mcap_col], errors='coerce')
    
    # Filter valid values
    df = df[(df[users_col] > 0) & (df[mcap_col] > 0)]
    df = df[df[users_col].notna() & df[mcap_col].notna()]
    
    users = df[users_col].values
    mcap = df[mcap_col].values
    
    print(f'   Valid records: {len(df)}')
    print(f'   Users range: {users.min():,.0f} to {users.max():,.0f}')
    print(f'   Market cap range: ${mcap.min()/1e9:.2f}B to ${mcap.max()/1e9:.2f}B')
    
    if len(df) < 100:
        print(f'⚠️  Warning: Only {len(df)} records, may not be enough for reliable analysis')
    
    # 1. Base Metcalfe Model (PRIMARY)
    print(f'\n{"="*80}')
    print(f'STEP 1: Base Metcalfe Model (PRIMARY)')
    print(f'{"="*80}')
    
    metcalfe_model = MetcalfeModel()
    metcalfe_results = metcalfe_model.fit(users, mcap)
    
    print(f'\n📈 Results:')
    print(f'   α (intercept): {metcalfe_results["alpha"]:.4f}')
    print(f'   β (network effect): {metcalfe_results["beta"]:.4f}')
    print(f'   R²: {metcalfe_results["r_squared"]:.4f}')
    print(f'   P-value: {metcalfe_results["p_value"]:.4e}')
    
    # Interpretation
    if metcalfe_results['beta'] > 1.0:
        status = "✅ SUSTAINABLE"
        interpretation = "Super-linear network effects"
    elif metcalfe_results['beta'] < 1.0:
        status = "⚠️  UNSUSTAINABLE"
        interpretation = "Sub-linear network effects"
    else:
        status = "📊 LINEAR"
        interpretation = "Linear network effects"
    
    print(f'\n   {status}')
    print(f'   {interpretation}')
    
    # Compare with paper (if available)
    if network_config.get('paper_beta1') is not None:
        print(f'\n   Paper results (Regime 1): β = {network_config["paper_beta1"]:.2f}')
        if network_config.get('paper_beta2') is not None:
            print(f'   Paper results (Regime 2): β = {network_config["paper_beta2"]:.2f}')
    
    # 2. Save results
    output_dir = Path(__file__).parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save combined data
    output_df = df[[date_col, users_col, mcap_col]].copy()
    output_df = output_df.rename(columns={users_col: 'users', mcap_col: 'market_cap', date_col: 'date'})
    output_file = output_dir / f"{network_name}_correlated_data.csv"
    output_df.to_csv(output_file, index=False)
    print(f'\n💾 Saved data to: {output_file}')
    
    # Return results
    results = {
        'network': network_name,
        'beta': metcalfe_results['beta'],
        'alpha': metcalfe_results['alpha'],
        'r_squared': metcalfe_results['r_squared'],
        'p_value': metcalfe_results['p_value'],
        'status': status,
        'interpretation': interpretation,
        'records': len(df),
        'date_range': (df[date_col].min(), df[date_col].max())
    }
    
    return results

def main():
    """Analyze all Layer 2 networks."""
    
    print("="*80)
    print("LAYER 2 NETWORK EFFECTS ANALYSIS")
    print("="*80)
    print("\nUsing existing data from Blockchain_NetworkValue repository")
    print("Methodology: Base Metcalfe's Law (primary)")
    print("Filtering: nonce >= 5 (matches paper methodology)")
    
    results = []
    
    for network_name, network_config in LAYER2_NETWORKS.items():
        result = analyze_layer2_network(network_name, network_config)
        if result:
            results.append(result)
    
    # Summary
    print(f'\n{"="*80}')
    print("ANALYSIS SUMMARY")
    print(f'{"="*80}')
    
    if results:
        print(f'\n📊 Results for {len(results)} networks:')
        print(f'\n{"Network":<15} {"β":<10} {"R²":<8} {"Status":<20}')
        print("-" * 60)
        
        for r in results:
            print(f'{r["network"]:<15} {r["beta"]:<10.4f} {r["r_squared"]:<8.4f} {r["status"]:<20}')
        
        print(f'\n💡 Key Findings:')
        sustainable = [r for r in results if r['beta'] > 1.0]
        unsustainable = [r for r in results if r['beta'] < 1.0]
        
        if sustainable:
            print(f'   ✅ Sustainable networks (β > 1.0): {len(sustainable)}')
            for r in sustainable:
                print(f'      - {r["network"]}: β = {r["beta"]:.4f}')
        
        if unsustainable:
            print(f'   ⚠️  Unsustainable networks (β < 1.0): {len(unsustainable)}')
            for r in unsustainable:
                print(f'      - {r["network"]}: β = {r["beta"]:.4f}')
        
        print(f'\n📁 Data files saved to: data/processed/')
        print(f'   Ready for visualization and further analysis')
    else:
        print(f'\n⚠️  No networks analyzed successfully')

if __name__ == '__main__':
    main()


