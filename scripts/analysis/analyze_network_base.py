#!/usr/bin/env python3
"""
Base Network Analysis Script

Analyzes any network using base Metcalfe's Law (primary) and optionally FTP-MS (secondary).
Follows the recommended approach: base Metcalfe for all networks, 2 regimes when it adds value.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from analysis.metcalfe_model import MetcalfeModel
from analysis.markov_switching import FTPMSModel

warnings.filterwarnings('ignore')

def analyze_network(
    network_name: str,
    data_file: Path,
    use_regimes: bool = False,
    output_dir: Path = None
):
    """
    Analyze a network using base Metcalfe's Law and optionally FTP-MS.
    
    Parameters
    ----------
    network_name : str
        Name of the network (e.g., "Filecoin", "Ethereum")
    data_file : Path
        Path to CSV file with columns: date, users, market_cap (or value)
    use_regimes : bool
        Whether to also run 2-regime model (default: False)
    output_dir : Path
        Directory to save results (default: data/processed)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print(f"ANALYZING: {network_name.upper()}")
    print("="*80)
    
    # Load data
    if not data_file.exists():
        print(f"❌ Error: Data file not found: {data_file}")
        return None
    
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    
    # Check for required columns
    if 'users' not in df.columns:
        print(f"❌ Error: 'users' column not found in data")
        return None
    
    # Value column might be 'market_cap' or 'value'
    value_col = 'market_cap' if 'market_cap' in df.columns else 'value'
    if value_col not in df.columns:
        print(f"❌ Error: 'market_cap' or 'value' column not found in data")
        return None
    
    print(f"\n📊 Data Summary:")
    print(f"   Records: {len(df)}")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Users range: {df['users'].min():,.0f} to {df['users'].max():,.0f}")
    print(f"   Value range: ${df[value_col].min():,.0f} to ${df[value_col].max():,.0f}")
    
    # Filter out zeros and invalid values
    df = df[(df['users'] > 0) & (df[value_col] > 0)]
    df = df.dropna(subset=['users', value_col])
    
    users = df['users'].values
    value = df[value_col].values
    
    print(f"✅ Valid records after filtering: {len(df)}")
    
    # 1. Base Metcalfe's Law Model (PRIMARY)
    print("\n" + "="*80)
    print("STEP 1: Base Metcalfe's Law Model (PRIMARY)")
    print("="*80)
    
    metcalfe_model = MetcalfeModel()
    metcalfe_results = metcalfe_model.fit(users, value)
    
    print(f"\n📈 Results:")
    print(f"   α (intercept): {metcalfe_results['alpha']:.4f}")
    print(f"   β (network effect): {metcalfe_results['beta']:.4f}")
    print(f"   R²: {metcalfe_results['r_squared']:.4f}")
    print(f"   Std Error: {metcalfe_results['std_error']:.4f}")
    print(f"   P-value: {metcalfe_results['p_value']:.4e}")
    
    # Interpretation
    if metcalfe_results['beta'] > 1.0:
        status = "✅ SUSTAINABLE"
        interpretation = "Super-linear network effects - value grows more than proportionally to users"
    elif metcalfe_results['beta'] < 1.0:
        status = "⚠️  UNSUSTAINABLE"
        interpretation = "Sub-linear network effects - value grows less than proportionally to users"
    else:
        status = "📊 LINEAR"
        interpretation = "Linear network effects - value grows proportionally to users"
    
    print(f"\n   {status}")
    print(f"   {interpretation}")
    
    # 2. FTP-MS Model (SECONDARY - Optional)
    ftpms_results = None
    if use_regimes:
        print("\n" + "="*80)
        print("STEP 2: Fixed Transition Probabilities Markov-Switching (FTP-MS) Model (SECONDARY)")
        print("="*80)
        
        try:
            ftpms_model = FTPMSModel()
            ftpms_results = ftpms_model.fit(users, value, maxiter=500, em_iter=20)
            
            print(f"\n📈 Results:")
            print(f"   α (intercept): {ftpms_results['alpha']:.4f}")
            print(f"   β₁ (Regime 1): {ftpms_results['betas'][1]:.4f}")
            print(f"   β₂ (Regime 2): {ftpms_results['betas'][2]:.4f}")
            
            # Check if regimes are meaningfully different
            beta_diff = abs(ftpms_results['betas'][1] - ftpms_results['betas'][2])
            if beta_diff > 0.2:
                print(f"   ✅ Regimes are meaningfully different (Δβ = {beta_diff:.4f})")
            else:
                print(f"   ⚠️  Regimes are similar (Δβ = {beta_diff:.4f}) - base Metcalfe is sufficient")
            
        except Exception as e:
            print(f"   ⚠️  2-regime model failed: {e}")
            print(f"   → Using base Metcalfe results only")
            ftpms_results = None
    
    # 3. Visualization
    print("\n" + "="*80)
    print("STEP 3: Creating Visualization")
    print("="*80)
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
    
    # Panel 1: Time series
    ax1 = axes[0]
    ax1.plot(df['date'], value / 1e9, label=f'Market Cap (USD billions)', color='blue', alpha=0.7, linewidth=1.5)
    ax1_twin = ax1.twinx()
    ax1_twin.plot(df['date'], users / 1e3, label='Active Users (thousands)', color='green', alpha=0.7, linewidth=1.5)
    
    ax1.set_title(f'{network_name}: Market Cap & Active Users Over Time', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Market Cap (USD billions)', fontsize=12)
    ax1_twin.set_ylabel('Active Users (thousands)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Log-log plot with regression line
    ax2 = axes[1]
    log_users = np.log(users)
    log_value = np.log(value)
    
    ax2.scatter(log_users, log_value, alpha=0.5, s=10, color='blue')
    
    # Base Metcalfe line
    x_vals = np.linspace(log_users.min(), log_users.max(), 100)
    y_vals_base = metcalfe_results['alpha'] + metcalfe_results['beta'] * x_vals
    ax2.plot(x_vals, y_vals_base, '--', color='red', linewidth=2, 
             label=f"Base Metcalfe (β={metcalfe_results['beta']:.2f})")
    
    # Regime-specific lines (if available)
    if ftpms_results is not None:
        y_vals_reg1 = ftpms_results['alpha'] + ftpms_results['betas'][1] * x_vals
        y_vals_reg2 = ftpms_results['alpha'] + ftpms_results['betas'][2] * x_vals
        ax2.plot(x_vals, y_vals_reg1, '--', color='green', linewidth=1.5, alpha=0.7,
                 label=f"Regime 1 (β={ftpms_results['betas'][1]:.2f})")
        ax2.plot(x_vals, y_vals_reg2, '--', color='orange', linewidth=1.5, alpha=0.7,
                 label=f"Regime 2 (β={ftpms_results['betas'][2]:.2f})")
    
    ax2.set_title(f'Log(Market Cap) vs Log(Active Users)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Log(Active Users)', fontsize=12)
    ax2.set_ylabel('Log(Market Cap)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_file = output_dir / f"{network_name.lower().replace(' ', '_')}_network_effects.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved visualization to: {output_file}")
    
    # 4. Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"\n📊 Base Metcalfe's Law (PRIMARY):")
    print(f"   β = {metcalfe_results['beta']:.4f} (R² = {metcalfe_results['r_squared']:.4f})")
    print(f"   Status: {status}")
    print(f"   Interpretation: {interpretation}")
    
    if ftpms_results is not None:
        print(f"\n📊 FTP-MS Model (SECONDARY):")
        print(f"   Regime 1: β = {ftpms_results['betas'][1]:.4f}")
        print(f"   Regime 2: β = {ftpms_results['betas'][2]:.4f}")
        beta_diff = abs(ftpms_results['betas'][1] - ftpms_results['betas'][2])
        if beta_diff > 0.2:
            print(f"   ✅ Regimes are meaningfully different (Δβ = {beta_diff:.4f})")
        else:
            print(f"   ⚠️  Regimes are similar - base Metcalfe is sufficient")
    
    print(f"\n📁 Files:")
    print(f"   Data: {data_file}")
    print(f"   Visualization: {output_file}")
    
    # Return results
    results = {
        'network': network_name,
        'beta': metcalfe_results['beta'],
        'alpha': metcalfe_results['alpha'],
        'r_squared': metcalfe_results['r_squared'],
        'p_value': metcalfe_results['p_value'],
        'status': status,
        'interpretation': interpretation,
        'ftpms': ftpms_results if ftpms_results else None
    }
    
    return results

def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze network effects for a blockchain network")
    parser.add_argument('network', type=str, help='Network name (e.g., filecoin, ethereum)')
    parser.add_argument('--data', type=str, help='Path to data CSV file')
    parser.add_argument('--regimes', action='store_true', help='Also run 2-regime model')
    args = parser.parse_args()
    
    # Default data file location
    if args.data:
        data_file = Path(args.data)
    else:
        data_file = Path(__file__).parent / "data" / "processed" / f"{args.network}_correlated_data.csv"
    
    results = analyze_network(
        network_name=args.network.title(),
        data_file=data_file,
        use_regimes=args.regimes
    )
    
    if results:
        print("\n" + "="*80)
        print("✅ Analysis complete!")
        print("="*80)

if __name__ == '__main__':
    main()


