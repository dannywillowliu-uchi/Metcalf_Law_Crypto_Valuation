#!/usr/bin/env python3
"""
Analyze Filecoin Network Effects

Fits Metcalfe's Law and FTP-MS models to Filecoin data to determine network effects.
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

def main():
    print("="*80)
    print("FILECOIN NETWORK EFFECTS ANALYSIS")
    print("="*80)
    
    # Load data
    data_file = Path(__file__).parent / "data" / "processed" / "filecoin_correlated_data.csv"
    
    if not data_file.exists():
        print(f"❌ Error: Data file not found: {data_file}")
        print("   Please run collect_filecoin_data.py first")
        return
    
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"\n📊 Data Summary:")
    print(f"   Records: {len(df)}")
    print(f"   Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Users range: {df['users'].min():,.0f} to {df['users'].max():,.0f}")
    print(f"   Market cap range: ${df['market_cap'].min():,.0f} to ${df['market_cap'].max():,.0f}")
    
    # Filter out zeros and invalid values
    df = df[(df['users'] > 0) & (df['market_cap'] > 0)]
    df = df.dropna(subset=['users', 'market_cap'])
    
    users = df['users'].values
    mcap = df['market_cap'].values
    
    print(f"\n✅ Valid records after filtering: {len(df)}")
    
    # 1. Base Metcalfe's Law Model
    print("\n" + "="*80)
    print("STEP 1: Base Metcalfe's Law Model")
    print("="*80)
    
    metcalfe_model = MetcalfeModel()
    metcalfe_results = metcalfe_model.fit(users, mcap)
    
    print(f"\n📈 Results:")
    print(f"   α (intercept): {metcalfe_results['alpha']:.4f}")
    print(f"   β (network effect): {metcalfe_results['beta']:.4f}")
    print(f"   R²: {metcalfe_results['r_squared']:.4f}")
    print(f"   Std Error: {metcalfe_results['std_error']:.4f}")
    print(f"   P-value: {metcalfe_results['p_value']:.4e}")
    
    if metcalfe_results['beta'] > 1.0:
        print(f"\n   ✅ Super-linear network effects (β > 1.0)")
        print(f"      Value grows more than proportionally to users")
    elif metcalfe_results['beta'] < 1.0:
        print(f"\n   ⚠️  Sub-linear network effects (β < 1.0)")
        print(f"      Value grows less than proportionally to users")
    else:
        print(f"\n   📊 Linear network effects (β ≈ 1.0)")
        print(f"      Value grows proportionally to users")
    
    # 2. FTP-MS Model (Markov-Switching)
    print("\n" + "="*80)
    print("STEP 2: Fixed Transition Probabilities Markov-Switching (FTP-MS) Model")
    print("="*80)
    
    ftpms_model = FTPMSModel()
    ftpms_results = ftpms_model.fit(users, mcap, maxiter=500, em_iter=20)
    
    print(f"\n📈 Results:")
    print(f"   α (intercept): {ftpms_results['alpha']:.4f}")
    print(f"   β₁ (Regime 1 - Bullish): {ftpms_results['betas'][1]:.4f}")
    print(f"   β₂ (Regime 2 - Bearish): {ftpms_results['betas'][2]:.4f}")
    print(f"   Transition Probabilities:")
    # Handle transition_probs as array or dict
    if isinstance(ftpms_results['transition_probs'], np.ndarray):
        print(f"      P(1→1): {ftpms_results['transition_probs'][0, 0]:.4f}")
        print(f"      P(2→2): {ftpms_results['transition_probs'][1, 1]:.4f}")
    elif isinstance(ftpms_results['transition_probs'], dict):
        print(f"      P(1→1): {ftpms_results['transition_probs'].get(1, {}).get(1, 'N/A')}")
        print(f"      P(2→2): {ftpms_results['transition_probs'].get(2, {}).get(2, 'N/A')}")
    else:
        print(f"      Transition matrix: {ftpms_results['transition_probs']}")
    if 'regime_distribution' in ftpms_results:
        print(f"   Regime Distribution:")
        print(f"      Regime 1: {ftpms_results['regime_distribution'].get(1, 0):.1f}%")
        print(f"      Regime 2: {ftpms_results['regime_distribution'].get(2, 0):.1f}%")
    else:
        print(f"   Regime Distribution: Not available")
    
    # Interpret regimes
    if ftpms_results['betas'][1] > ftpms_results['betas'][2]:
        print(f"\n   ✅ Regime 1 (Bullish): β = {ftpms_results['betas'][1]:.4f}")
        print(f"   ⚠️  Regime 2 (Bearish): β = {ftpms_results['betas'][2]:.4f}")
    else:
        print(f"\n   ⚠️  Regime 1: β = {ftpms_results['betas'][1]:.4f}")
        print(f"   ✅ Regime 2: β = {ftpms_results['betas'][2]:.4f}")
    
    # Check for sub-linear effects
    regime1_sublinear = ftpms_results['betas'][1] < 1.0
    regime2_sublinear = ftpms_results['betas'][2] < 1.0
    
    if regime1_sublinear and regime2_sublinear:
        print(f"\n   ⚠️  Both regimes show sub-linear network effects (β < 1.0)")
    elif regime1_sublinear or regime2_sublinear:
        print(f"\n   ⚠️  One regime shows sub-linear network effects")
    else:
        print(f"\n   ✅ Both regimes show super-linear network effects (β > 1.0)")
    
    # 3. Visualization
    print("\n" + "="*80)
    print("STEP 3: Creating Visualizations")
    print("="*80)
    
    output_dir = Path(__file__).parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get smoothed probabilities for regime visualization
    try:
        smoothed_probs = ftpms_model.results.smoothed_marginal_probabilities
        if hasattr(smoothed_probs, 'idxmax'):
            regime_assignments = smoothed_probs.idxmax(axis=1).values
        else:
            regime_assignments = np.argmax(smoothed_probs.values, axis=1)
    except:
        # Fallback: assign based on which beta is higher
        regime_assignments = np.ones(len(df)) if ftpms_results['betas'][1] > ftpms_results['betas'][2] else np.zeros(len(df))
    
    # Create comprehensive visualization
    fig, axes = plt.subplots(4, 1, figsize=(14, 18), sharex=True)
    
    # Panel 1: Time series with regimes
    ax1 = axes[0]
    ax1.plot(df['date'], mcap / 1e9, label='Market Cap (USD billions)', color='blue', alpha=0.7, linewidth=1.5)
    ax1_twin = ax1.twinx()
    ax1_twin.plot(df['date'], users / 1e3, label='Active Users (thousands)', color='green', alpha=0.7, linewidth=1.5)
    
    # Shade regimes
    current_regime = None
    start_idx = 0
    for i, regime in enumerate(regime_assignments):
        if current_regime is None:
            current_regime = regime
            start_idx = i
        elif regime != current_regime:
            if current_regime == 0:  # Regime 1 (bullish)
                ax1.axvspan(df['date'].iloc[start_idx], df['date'].iloc[i-1], 
                           color='gray', alpha=0.2, label='Regime 1' if start_idx == 0 else "")
            else:  # Regime 2 (bearish)
                ax1.axvspan(df['date'].iloc[start_idx], df['date'].iloc[i-1], 
                           color='red', alpha=0.1, label='Regime 2' if start_idx == 0 else "")
            current_regime = regime
            start_idx = i
    
    # Last regime
    if current_regime == 0:
        ax1.axvspan(df['date'].iloc[start_idx], df['date'].iloc[-1], color='gray', alpha=0.2)
    else:
        ax1.axvspan(df['date'].iloc[start_idx], df['date'].iloc[-1], color='red', alpha=0.1)
    
    ax1.set_title('Filecoin: Market Cap & Active Users Over Time (No Nonce Filtering)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Market Cap (USD billions)', fontsize=12)
    ax1_twin.set_ylabel('Active Users (thousands)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1_twin.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    # Panel 2: Log-log plot with regression lines
    ax2 = axes[1]
    log_users = np.log(users)
    log_mcap = np.log(mcap)
    
    ax2.scatter(log_users, log_mcap, alpha=0.5, s=10, c=regime_assignments, cmap='viridis')
    
    # Base Metcalfe line
    x_vals = np.linspace(log_users.min(), log_users.max(), 100)
    y_vals_base = metcalfe_results['alpha'] + metcalfe_results['beta'] * x_vals
    ax2.plot(x_vals, y_vals_base, '--', color='blue', linewidth=2, 
             label=f"Base Metcalfe (β={metcalfe_results['beta']:.2f})")
    
    # Regime-specific lines
    y_vals_reg1 = ftpms_results['alpha'] + ftpms_results['betas'][1] * x_vals
    y_vals_reg2 = ftpms_results['alpha'] + ftpms_results['betas'][2] * x_vals
    ax2.plot(x_vals, y_vals_reg1, '--', color='green', linewidth=2, 
             label=f"Regime 1 (β={ftpms_results['betas'][1]:.2f})")
    ax2.plot(x_vals, y_vals_reg2, '--', color='red', linewidth=2, 
             label=f"Regime 2 (β={ftpms_results['betas'][2]:.2f})")
    
    ax2.set_title('Log(Market Cap) vs Log(Active Users)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Log(Active Users)', fontsize=12)
    ax2.set_ylabel('Log(Market Cap)', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Panel 3: Regime probabilities
    ax3 = axes[2]
    try:
        smoothed_probs = ftpms_model.results.smoothed_marginal_probabilities
        ax3.plot(df['date'], smoothed_probs[0], label='P(Regime 1)', color='green', linewidth=2)
        ax3.plot(df['date'], smoothed_probs[1], label='P(Regime 2)', color='red', linewidth=2)
    except:
        pass
    ax3.set_title('Smoothed Regime Probabilities', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Probability', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim([0, 1])
    
    # Panel 4: Regime timeline
    ax4 = axes[3]
    try:
        ax4.plot(df['date'], regime_assignments, drawstyle='steps-post', color='purple', linewidth=2)
    except:
        pass
    ax4.set_title('Regime Timeline', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Date', fontsize=12)
    ax4.set_ylabel('Regime', fontsize=12)
    ax4.set_yticks([0, 1])
    ax4.set_yticklabels(['Regime 1', 'Regime 2'])
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_file = output_dir / "filecoin_network_effects_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved visualization to: {output_file}")
    
    # 4. Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(f"\n📊 Base Metcalfe's Law:")
    print(f"   β = {metcalfe_results['beta']:.4f} (R² = {metcalfe_results['r_squared']:.4f})")
    
    print(f"\n📊 FTP-MS Model (Markov-Switching):")
    print(f"   Regime 1 (Bullish): β = {ftpms_results['betas'][1]:.4f}")
    print(f"   Regime 2 (Bearish): β = {ftpms_results['betas'][2]:.4f}")
    if 'regime_distribution' in ftpms_results:
        print(f"   Regime Distribution: {ftpms_results['regime_distribution'].get(1, 0):.1f}% / {ftpms_results['regime_distribution'].get(2, 0):.1f}%")
    else:
        print(f"   Regime Distribution: Not available")
    
    print(f"\n💡 Interpretation:")
    if metcalfe_results['beta'] > 1.0:
        print(f"   Filecoin shows SUPER-LINEAR network effects (β = {metcalfe_results['beta']:.2f})")
        print(f"   → Value grows more than proportionally to users")
        print(f"   → Strong network effects, sustainable growth")
    elif metcalfe_results['beta'] < 1.0:
        print(f"   Filecoin shows SUB-LINEAR network effects (β = {metcalfe_results['beta']:.2f})")
        print(f"   → Value grows less than proportionally to users")
        print(f"   → Weak network effects, may struggle to maintain value")
    else:
        print(f"   Filecoin shows LINEAR network effects (β ≈ 1.0)")
        print(f"   → Value grows proportionally to users")
    
    print(f"\n📁 Files:")
    print(f"   Data: {data_file}")
    print(f"   Visualization: {output_file}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

