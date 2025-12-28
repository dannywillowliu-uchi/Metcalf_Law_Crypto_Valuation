#!/usr/bin/env python3
"""
Generate per-token visualizations similar to sections 5 and 6.2
Creates:
1. Time series graphs (users + market cap over time)
2. Performance visualization (if returns data available)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Network metadata from paper
NETWORKS = {
    'ethereum': {'beta': 1.52, 'category': 'Payment (L1)', 'classification': 'Sustainable'},
    'render': {'beta': 1.39, 'category': 'Compute', 'classification': 'Sustainable'},
    'livepeer': {'beta': 1.32, 'category': 'Compute', 'classification': 'Sustainable'},
    'chainlink': {'beta': 1.21, 'category': 'Oracle', 'classification': 'Sustainable'},
    'optimism': {'beta': 1.11, 'category': 'Payment (L2)', 'classification': 'Sustainable'},
    'sushiswap': {'beta': 1.03, 'category': 'DEX', 'classification': 'Borderline'},
    'aave': {'beta': 0.93, 'category': 'DeFi', 'classification': 'Unsustainable'},
    'compound': {'beta': 0.77, 'category': 'DeFi', 'classification': 'Unsustainable'},
    'polygon': {'beta': 0.43, 'category': 'Payment (L2)', 'classification': 'Unsustainable'},
    'arbitrum': {'beta': 0.39, 'category': 'Payment (L2)', 'classification': 'Unsustainable'},
    'maker': {'beta': 0.37, 'category': 'DeFi', 'classification': 'Unsustainable'},
    'uniswap': {'beta': 0.36, 'category': 'DEX', 'classification': 'Unsustainable'},
    'thegraph': {'beta': 0.28, 'category': 'Indexing', 'classification': 'Unsustainable'},
    'dimo': {'beta': 0.12, 'category': 'DePIN', 'classification': 'Unsustainable'},
    'ens': {'beta': -0.25, 'category': 'Identity', 'classification': 'Unsustainable'},
}

def load_network_data(network_name: str) -> pd.DataFrame:
    """Load processed data for a network"""
    data_file = project_root / 'data' / 'processed' / f'{network_name}_correlated_data.csv'
    
    # Handle special cases
    if network_name == 'ethereum' and not data_file.exists():
        data_file = project_root / 'data' / 'processed' / 'ethereum_correlated_data_nonce5_paper_range.csv'
    elif network_name == 'maker':
        data_file = project_root / 'data' / 'processed' / 'maker_correlated_data.csv'
    
    if not data_file.exists():
        return None
    
    df = pd.read_csv(data_file)
    
    # Normalize column names
    if 'day' in df.columns:
        df['date'] = pd.to_datetime(df['day'])
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        return None
    
    # Find users column
    users_col = None
    for col in ['users', 'active_users', 'active_addresses', 'dau_nonce_5', 'dau_nonce_10']:
        if col in df.columns:
            users_col = col
            break
    
    # Find market cap column
    mcap_col = None
    for col in ['market_cap', 'Market_cap', 'marketCap']:
        if col in df.columns:
            mcap_col = col
            break
    
    if users_col is None or mcap_col is None:
        return None
    
    # Rename for consistency
    df = df.rename(columns={users_col: 'users', mcap_col: 'market_cap'})
    df = df[['date', 'users', 'market_cap']].copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Filter valid data
    df = df[(df['users'] > 0) & (df['market_cap'] > 0)].copy()
    
    return df

def create_time_series_graph(network_name: str, network_info: dict, output_dir: Path):
    """Create time series graph for a single network"""
    df = load_network_data(network_name)
    
    if df is None or len(df) < 10:
        print(f"  ⚠️  Skipping {network_name}: insufficient data")
        return False
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax_twin = ax.twinx()
    
    # Plot market cap (left axis)
    ax.plot(df['date'], df['market_cap'] / 1e9, 
            color='#2E86AB', linewidth=2, alpha=0.8, label='Market Cap (USD billions)')
    
    # Plot users (right axis)
    ax_twin.plot(df['date'], df['users'] / 1000, 
                 color='#A23B72', linewidth=2, alpha=0.8, label='Active Users (thousands)')
    
    # Formatting
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Market Cap (USD billions)', fontsize=11, color='#2E86AB', fontweight='bold')
    ax_twin.set_ylabel('Active Users (thousands)', fontsize=11, color='#A23B72', fontweight='bold')
    
    classification = network_info['classification']
    beta = network_info['beta']
    title = f"{network_name.upper()}: Users and Market Cap Over Time\n"
    title += f"β = {beta:.2f} ({classification})"
    
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    
    ax.tick_params(axis='y', labelcolor='#2E86AB')
    ax_twin.tick_params(axis='y', labelcolor='#A23B72')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=10)
    ax_twin.legend(loc='upper right', fontsize=10)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    
    plt.tight_layout()
    
    # Save
    output_file = output_dir / f'{network_name}_time_series.pdf'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created: {output_file.name}")
    return True

def create_log_log_scatter(network_name: str, network_info: dict, output_dir: Path):
    """Create log-log scatter plot with regression line"""
    df = load_network_data(network_name)
    
    if df is None or len(df) < 10:
        return False
    
    # Calculate log values
    log_users = np.log(df['users'].values)
    log_mcap = np.log(df['market_cap'].values)
    
    # Simple regression for visualization
    beta = network_info['beta']
    alpha = np.mean(log_mcap) - beta * np.mean(log_users)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(log_users, log_mcap, alpha=0.5, s=20, color='#2E86AB')
    
    # Regression line
    x_line = np.linspace(log_users.min(), log_users.max(), 100)
    y_line = alpha + beta * x_line
    ax.plot(x_line, y_line, 'r-', linewidth=2.5, label=f'β = {beta:.2f}')
    
    # Reference line (β = 1.0)
    y_ref = alpha + 1.0 * x_line
    ax.plot(x_line, y_ref, 'g--', linewidth=1.5, alpha=0.6, label='β = 1.0 (linear)')
    
    ax.set_xlabel('log(Active Users)', fontsize=12, fontweight='bold')
    ax.set_ylabel('log(Market Cap)', fontsize=12, fontweight='bold')
    
    classification = network_info['classification']
    title = f"{network_name.upper()}: Metcalfe's Law Fit\n"
    title += f"β = {beta:.2f} ({classification})"
    
    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_file = output_dir / f'{network_name}_log_log_scatter.pdf'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Created: {output_file.name}")
    return True

def main():
    """Generate graphs for all networks"""
    print("="*80)
    print("Generating Per-Token Visualizations")
    print("="*80)
    
    # Create output directory
    output_dir = project_root / 'paper' / 'figures' / 'per_token'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nOutput directory: {output_dir}\n")
    
    success_count = 0
    for network_name, network_info in NETWORKS.items():
        print(f"Processing {network_name.upper()}...")
        
        # Time series graph
        if create_time_series_graph(network_name, network_info, output_dir):
            success_count += 1
        
        # Log-log scatter plot
        create_log_log_scatter(network_name, network_info, output_dir)
    
    print(f"\n{'='*80}")
    print(f"✅ Generated graphs for {success_count}/{len(NETWORKS)} networks")
    print(f"📁 Output directory: {output_dir}")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()

