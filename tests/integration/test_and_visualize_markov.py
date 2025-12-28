#!/usr/bin/env python3
"""
Test, visualize, and analyze Markov regime-switching model results
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from analysis.markov_switching import FTPMSModel
from analysis.metcalfe_model import MetcalfeModel
import warnings
warnings.filterwarnings('ignore')

def test_and_visualize():
    """Test model, create visualizations, and analyze regimes"""
    
    print('='*80)
    print('MARKOV REGIME-SWITCHING: TEST, VISUALIZE & ANALYZE')
    print('='*80)
    
    # Load data - try original repository data first
    data_path_orig = Path(__file__).parent.parent / 'Blockchain_NetworkValue' / 'Data_Dune_MktCap' / 'ethereum_all_trend.csv'
    data_path_ours = Path(__file__).parent / 'data' / 'processed' / 'ethereum_correlated_data_nonce5_paper_range.csv'
    
    if data_path_orig.exists():
        print(f'\n1. Loading original repository data...')
        df = pd.read_csv(data_path_orig, parse_dates=['day'])
        df = df[(df['day'] >= '2017-01-01') & (df['day'] <= '2024-12-31')].copy()
        df = df.sort_values('day').reset_index(drop=True)
        users = df['dau_nonce_5'].values
        mcap = df['Market_cap'].values
        dates = df['day'].values
        data_source = "Original Repository"
    elif data_path_ours.exists():
        print(f'\n1. Loading our processed data...')
        df = pd.read_csv(data_path_ours, parse_dates=['date'])
        df = df.sort_values('date').reset_index(drop=True)
        users = df['users'].values
        mcap = df['market_cap'].values
        dates = df['date'].values
        data_source = "Our Processed Data"
    else:
        print(f'\n✗ No data file found!')
        return
    
    # Clean data
    valid = (users > 0) & (mcap > 0) & np.isfinite(users) & np.isfinite(mcap)
    users = users[valid]
    mcap = mcap[valid]
    dates = dates[valid]
    
    print(f'   Data source: {data_source}')
    print(f'   Records: {len(users):,}')
    print(f'   Date range: {pd.Timestamp(dates[0]).date()} to {pd.Timestamp(dates[-1]).date()}')
    print(f'   Users: {users.min():,.0f} to {users.max():,.0f}')
    print(f'   Market cap: ${mcap.min()/1e9:.2f}B to ${mcap.max()/1e9:.2f}B')
    
    # Fit base Metcalfe model
    print(f'\n2. Fitting base Metcalfe model...')
    metcalfe = MetcalfeModel()
    metcalfe_results = metcalfe.fit(users, mcap)
    print(f'   α = {metcalfe_results["alpha"]:.4f}')
    print(f'   β = {metcalfe_results["beta"]:.4f}')
    print(f'   R² = {metcalfe_results["r_squared"]:.4f}')
    
    # Fit Markov-switching model
    print(f'\n3. Fitting Markov-switching model...')
    ftpms = FTPMSModel(k_regimes=2)
    ms_results = ftpms.fit(users, mcap, maxiter=500, em_iter=20)
    
    print(f'\n4. Model Results:')
    print(f'   α = {ms_results["alpha"]:.4f} (target: 10.15)')
    print(f'   β₁ (regime 1) = {ms_results["betas"][1]:.4f} (target: 1.31)')
    print(f'   β₂ (regime 2) = {ms_results["betas"][2]:.4f} (target: 1.19)')
    
    tp = ms_results['transition_probs']
    if isinstance(tp, dict):
        p11 = tp['P11']
        p22 = tp['P22']
    else:
        p11 = tp[0][0]
        p22 = tp[1][1]
    
    print(f'   P₁₁ = {p11:.4f} (target: 0.99)')
    print(f'   P₂₂ = {p22:.4f} (target: 0.99)')
    if ms_results['aic']:
        print(f'   AIC = {ms_results["aic"]:.2f} (target: ~2108)')
    
    # Get regime probabilities
    if hasattr(ftpms, 'smoothed_probabilities'):
        sp = ftpms.smoothed_probabilities
        regime1_prob = sp[:, 0] if sp.ndim > 1 else sp
        regime1_periods = regime1_prob > 0.5
        regime1_days = np.sum(regime1_periods)
        regime2_days = len(regime1_periods) - regime1_days
        
        print(f'\n5. Regime Distribution:')
        print(f'   Regime 1: {regime1_days} days ({100*regime1_days/len(regime1_periods):.1f}%)')
        print(f'   Regime 2: {regime2_days} days ({100*regime2_days/len(regime1_periods):.1f}%)')
        
        if regime1_days == 0 or regime2_days == 0:
            print(f'\n   ⚠️  Model collapsed to one regime - cannot visualize')
            return
        
        # Analyze regime periods
        print(f'\n6. Regime Period Analysis:')
        dates_pd = pd.to_datetime(dates)
        regime1_dates = dates_pd[regime1_periods]
        regime2_dates = dates_pd[~regime1_periods]
        
        # Find regime switches
        regime_changes = np.diff(regime1_periods.astype(int))
        switch_indices = np.where(np.abs(regime_changes) > 0)[0]
        
        print(f'   Number of regime switches: {len(switch_indices)}')
        print(f'\n   Regime 1 periods (bullish):')
        if len(regime1_dates) > 0:
            print(f'     Start: {regime1_dates.min().date()}')
            print(f'     End: {regime1_dates.max().date()}')
            print(f'     Duration: {(regime1_dates.max() - regime1_dates.min()).days} days')
        
        print(f'\n   Regime 2 periods (bearish):')
        if len(regime2_dates) > 0:
            print(f'     Start: {regime2_dates.min().date()}')
            print(f'     End: {regime2_dates.max().date()}')
            print(f'     Duration: {(regime2_dates.max() - regime2_dates.min()).days} days')
        
        # Check alignment with known market periods
        print(f'\n7. Alignment with Known Market Periods:')
        known_bull_1 = (pd.Timestamp('2017-04-01'), pd.Timestamp('2018-01-31'))  # ICO boom
        known_bull_2 = (pd.Timestamp('2020-01-01'), pd.Timestamp('2022-08-31'))  # DeFi summer
        
        regime1_in_bull1 = ((regime1_dates >= known_bull_1[0]) & (regime1_dates <= known_bull_1[1])).sum()
        regime1_in_bull2 = ((regime1_dates >= known_bull_2[0]) & (regime1_dates <= known_bull_2[1])).sum()
        bull1_total = ((dates_pd >= known_bull_1[0]) & (dates_pd <= known_bull_1[1])).sum()
        bull2_total = ((dates_pd >= known_bull_2[0]) & (dates_pd <= known_bull_2[1])).sum()
        
        print(f'   2017 ICO boom (Apr 2017 - Jan 2018):')
        print(f'     Regime 1 coverage: {regime1_in_bull1}/{bull1_total} days ({100*regime1_in_bull1/bull1_total:.1f}%)')
        print(f'   2020-2022 DeFi summer (Jan 2020 - Aug 2022):')
        print(f'     Regime 1 coverage: {regime1_in_bull2}/{bull2_total} days ({100*regime1_in_bull2/bull2_total:.1f}%)')
        
        # Create visualizations
        print(f'\n8. Creating visualizations...')
        
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # 1. Time series with regime shading
        ax1 = fig.add_subplot(gs[0, :])
        ax1_twin = ax1.twinx()
        
        # Plot market cap
        ax1.plot(dates_pd, mcap / 1e9, color='red', alpha=0.7, linewidth=1.5, label='Market Cap')
        ax1_twin.plot(dates_pd, users / 1000, color='blue', alpha=0.7, linewidth=1.5, label='Active Users (K)')
        
        # Shade regime 1 periods
        for i in range(len(regime1_periods)):
            if regime1_periods[i]:
                ax1.axvspan(dates_pd[i], dates_pd[i], alpha=0.3, color='green', linewidth=0)
        
        # Add vertical lines for regime switches
        for idx in switch_indices:
            if idx < len(dates_pd):
                ax1.axvline(dates_pd[idx], color='black', linestyle='--', alpha=0.5, linewidth=1)
        
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Market Cap (Billions USD)', fontsize=12, color='red')
        ax1_twin.set_ylabel('Active Users (Thousands)', fontsize=12, color='blue')
        ax1.set_title('Ethereum: Market Cap & Active Users with Regime Periods', fontsize=14, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='red')
        ax1_twin.tick_params(axis='y', labelcolor='blue')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        ax1_twin.legend(loc='upper right')
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax1.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 2. Log-log plot with regime-specific lines
        ax2 = fig.add_subplot(gs[1, 0])
        log_users = np.log(users)
        log_mcap = np.log(mcap)
        
        # Color points by regime
        colors = ['green' if r else 'red' for r in regime1_periods]
        ax2.scatter(log_users, log_mcap, c=colors, alpha=0.5, s=10)
        
        # Plot regime-specific regression lines
        regime1_mask = regime1_periods
        regime2_mask = ~regime1_periods
        
        if np.sum(regime1_mask) > 10:
            # Regime 1 line
            x_regime1 = np.linspace(log_users[regime1_mask].min(), log_users[regime1_mask].max(), 100)
            y_regime1 = ms_results['alpha'] + ms_results['betas'][1] * x_regime1
            ax2.plot(x_regime1, y_regime1, 'g-', linewidth=2, label=f'Regime 1: β={ms_results["betas"][1]:.3f}')
        
        if np.sum(regime2_mask) > 10:
            # Regime 2 line
            x_regime2 = np.linspace(log_users[regime2_mask].min(), log_users[regime2_mask].max(), 100)
            y_regime2 = ms_results['alpha'] + ms_results['betas'][2] * x_regime2
            ax2.plot(x_regime2, y_regime2, 'r-', linewidth=2, label=f'Regime 2: β={ms_results["betas"][2]:.3f}')
        
        # Base Metcalfe line
        x_base = np.linspace(log_users.min(), log_users.max(), 100)
        y_base = metcalfe_results['alpha'] + metcalfe_results['beta'] * x_base
        ax2.plot(x_base, y_base, 'b--', linewidth=1.5, alpha=0.7, label=f'Base: β={metcalfe_results["beta"]:.3f}')
        
        ax2.set_xlabel('log(Active Users)', fontsize=12)
        ax2.set_ylabel('log(Market Cap)', fontsize=12)
        ax2.set_title('Log-Log Plot: Regime-Specific Network Effects', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Regime probabilities over time
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.plot(dates_pd, regime1_prob, color='green', linewidth=2, label='Regime 1 (Bullish)')
        ax3.plot(dates_pd, 1 - regime1_prob, color='red', linewidth=2, label='Regime 2 (Bearish)')
        ax3.axhline(y=0.5, color='black', linestyle='--', alpha=0.5, linewidth=1)
        ax3.fill_between(dates_pd, 0, 0.5, alpha=0.1, color='red')
        ax3.fill_between(dates_pd, 0.5, 1, alpha=0.1, color='green')
        ax3.set_xlabel('Date', fontsize=12)
        ax3.set_ylabel('Regime Probability', fontsize=12)
        ax3.set_title('Smoothed Regime Probabilities Over Time', fontsize=12, fontweight='bold')
        ax3.set_ylim([0, 1])
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax3.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 4. Regime periods timeline
        ax4 = fig.add_subplot(gs[2, :])
        # Create a timeline showing regime periods
        y_pos = 0.5
        ax4.barh([y_pos], [len(dates_pd)], height=0.3, color='lightgray', alpha=0.5, label='Full Period')
        
        # Plot regime 1 periods
        regime1_ranges = []
        current_start = None
        for i, is_regime1 in enumerate(regime1_periods):
            if is_regime1 and current_start is None:
                current_start = i
            elif not is_regime1 and current_start is not None:
                regime1_ranges.append((current_start, i-1))
                current_start = None
        if current_start is not None:
            regime1_ranges.append((current_start, len(regime1_periods)-1))
        
        for start_idx, end_idx in regime1_ranges:
            start_date = dates_pd[start_idx]
            end_date = dates_pd[end_idx]
            width = (end_date - start_date).days
            ax4.barh([y_pos], [width], left=start_date, height=0.3, color='green', alpha=0.7, label='Regime 1 (Bullish)')
        
        # Add known market period markers
        ax4.axvline(known_bull_1[0], color='blue', linestyle=':', alpha=0.7, linewidth=2, label='2017 ICO Boom')
        ax4.axvline(known_bull_1[1], color='blue', linestyle=':', alpha=0.7, linewidth=2)
        ax4.axvline(known_bull_2[0], color='purple', linestyle=':', alpha=0.7, linewidth=2, label='2020-2022 DeFi Summer')
        ax4.axvline(known_bull_2[1], color='purple', linestyle=':', alpha=0.7, linewidth=2)
        
        ax4.set_xlabel('Date', fontsize=12)
        ax4.set_ylabel('', fontsize=12)
        ax4.set_title('Regime Timeline vs Known Market Periods', fontsize=12, fontweight='bold')
        ax4.set_yticks([y_pos])
        ax4.set_yticklabels(['Regime Periods'])
        ax4.set_xlim([dates_pd.min(), dates_pd.max()])
        ax4.legend(loc='upper right')
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax4.xaxis.set_major_locator(mdates.YearLocator())
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.suptitle('Ethereum Markov Regime-Switching Analysis (nonce ≥ 5)', fontsize=16, fontweight='bold', y=0.995)
        
        # Save figure
        output_path = Path(__file__).parent / 'data' / 'processed' / 'markov_regime_analysis.png'
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f'   ✓ Saved to: {output_path}')
        
        # Create summary table
        print(f'\n9. Regime Period Summary:')
        print(f'\n   Major Regime 1 Periods (Bullish):')
        for i, (start_idx, end_idx) in enumerate(regime1_ranges[:5], 1):
            start_date = dates_pd[start_idx].date()
            end_date = dates_pd[end_idx].date()
            duration = (dates_pd[end_idx] - dates_pd[start_idx]).days
            avg_prob = regime1_prob[start_idx:end_idx+1].mean()
            print(f'     Period {i}: {start_date} to {end_date} ({duration} days, avg prob={avg_prob:.3f})')
        
        print(f'\n   ✓ Analysis complete!')
        
    else:
        print(f'\n   ⚠️  No smoothed probabilities available')

if __name__ == '__main__':
    test_and_visualize()

