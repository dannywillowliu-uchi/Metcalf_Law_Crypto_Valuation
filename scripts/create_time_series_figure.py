#!/usr/bin/env python3
"""
Create time series figure showing daily users and market cap over time
for representative networks with high β (sustainable) vs low β (unsustainable)
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

def load_network_data(network_name: str) -> pd.DataFrame:
    """Load processed data for a network"""
    data_file = project_root / 'data' / 'processed' / f'{network_name}_correlated_data.csv'
    
    if not data_file.exists():
        # Try alternative naming
        if network_name == 'ethereum':
            data_file = project_root / 'data' / 'processed' / 'ethereum_correlated_data_nonce5_paper_range.csv'
        elif network_name == 'chainlink':
            data_file = project_root / 'data' / 'processed' / 'chainlink_correlated_data.csv'
        elif network_name == 'arbitrum':
            data_file = project_root / 'data' / 'processed' / 'arbitrum_correlated_data.csv'
    
    if not data_file.exists():
        print(f"⚠️  Data file not found for {network_name}")
        return None
    
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Filter valid data
    df = df[(df['users'] > 0) & (df['market_cap'] > 0)].copy()
    
    return df

def create_time_series_figure():
    """Create figure comparing high β vs low β networks"""
    
    # Load data for representative networks
    print("Loading data...")
    
    # High β networks (sustainable)
    eth_df = load_network_data('ethereum')
    chainlink_df = load_network_data('chainlink')
    
    # Low β networks (unsustainable)
    uniswap_df = load_network_data('uniswap')
    arbitrum_df = load_network_data('arbitrum')
    
    # Select best examples based on data availability
    high_beta_df = eth_df if eth_df is not None else chainlink_df
    low_beta_df = uniswap_df if uniswap_df is not None else arbitrum_df
    
    if high_beta_df is None or low_beta_df is None:
        print("❌ Could not load required data files")
        return
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25)
    
    # High β network (Ethereum)
    ax1 = fig.add_subplot(gs[0, :])
    ax1_twin = ax1.twinx()
    
    # Plot market cap (left axis)
    ax1.plot(high_beta_df['date'], high_beta_df['market_cap'] / 1e9, 
             color='#2E86AB', linewidth=2, alpha=0.8, label='Market Cap (USD billions)')
    
    # Plot users (right axis)
    ax1_twin.plot(high_beta_df['date'], high_beta_df['users'] / 1000, 
                  color='#A23B72', linewidth=2, alpha=0.8, label='Active Users (thousands)')
    
    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Market Cap (USD billions)', fontsize=11, color='#2E86AB', fontweight='bold')
    ax1_twin.set_ylabel('Active Users (thousands)', fontsize=11, color='#A23B72', fontweight='bold')
    ax1.set_title('High β Network (Sustainable): Ethereum (β = 1.52)\nUsers and Market Cap Move Together', 
                  fontsize=13, fontweight='bold', pad=15)
    
    ax1.tick_params(axis='y', labelcolor='#2E86AB')
    ax1_twin.tick_params(axis='y', labelcolor='#A23B72')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper left', fontsize=10)
    ax1_twin.legend(loc='upper right', fontsize=10)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=0)
    
    # Low β network (Uniswap)
    ax2 = fig.add_subplot(gs[1, :])
    ax2_twin = ax2.twinx()
    
    # Plot market cap (left axis)
    ax2.plot(low_beta_df['date'], low_beta_df['market_cap'] / 1e9, 
             color='#2E86AB', linewidth=2, alpha=0.8, label='Market Cap (USD billions)')
    
    # Plot users (right axis)
    ax2_twin.plot(low_beta_df['date'], low_beta_df['users'] / 1000, 
                  color='#A23B72', linewidth=2, alpha=0.8, label='Active Users (thousands)')
    
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Market Cap (USD billions)', fontsize=11, color='#2E86AB', fontweight='bold')
    ax2_twin.set_ylabel('Active Users (thousands)', fontsize=11, color='#A23B72', fontweight='bold')
    
    network_name = 'Uniswap' if uniswap_df is not None else 'Arbitrum'
    beta_val = 0.36 if uniswap_df is not None else 0.39
    ax2.set_title(f'Low β Network (Unsustainable): {network_name} (β = {beta_val})\nUsers and Market Cap Decoupled', 
                  fontsize=13, fontweight='bold', pad=15)
    
    ax2.tick_params(axis='y', labelcolor='#2E86AB')
    ax2_twin.tick_params(axis='y', labelcolor='#A23B72')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(loc='upper left', fontsize=10)
    ax2_twin.legend(loc='upper right', fontsize=10)
    
    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=0)
    
    # Add overall title
    fig.suptitle('Network Effects Over Time: Token-Utility Coupling Drives Co-movement', 
                 fontsize=15, fontweight='bold', y=0.98)
    
    # Save figure
    output_dir = project_root / 'paper' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path_pdf = output_dir / 'fig6_time_series_users_mcap.pdf'
    output_path_png = output_dir / 'fig6_time_series_users_mcap.png'
    
    plt.savefig(output_path_pdf, dpi=300, bbox_inches='tight')
    plt.savefig(output_path_png, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ Figure saved:")
    print(f"   PDF: {output_path_pdf}")
    print(f"   PNG: {output_path_png}")
    
    # Print summary statistics
    print(f"\n📊 Summary Statistics:")
    print(f"\nHigh β Network (Ethereum):")
    print(f"   Date range: {high_beta_df['date'].min().date()} to {high_beta_df['date'].max().date()}")
    print(f"   Users: {high_beta_df['users'].min():,.0f} to {high_beta_df['users'].max():,.0f}")
    print(f"   Market cap: ${high_beta_df['market_cap'].min()/1e9:.2f}B to ${high_beta_df['market_cap'].max()/1e9:.2f}B")
    
    print(f"\nLow β Network ({network_name}):")
    print(f"   Date range: {low_beta_df['date'].min().date()} to {low_beta_df['date'].max().date()}")
    print(f"   Users: {low_beta_df['users'].min():,.0f} to {low_beta_df['users'].max():,.0f}")
    print(f"   Market cap: ${low_beta_df['market_cap'].min()/1e9:.2f}B to ${low_beta_df['market_cap'].max()/1e9:.2f}B")

if __name__ == '__main__':
    print("="*80)
    print("Creating Time Series Figure: Users and Market Cap Over Time")
    print("="*80)
    create_time_series_figure()

