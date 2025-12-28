#!/usr/bin/env python3
"""
Test script to implement and verify Markov regime-switching model
Uses original data from repository to match paper's methodology
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import pandas as pd
import numpy as np
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

def test_markov_switching():
    """Test Markov-switching model with original data"""
    
    print('='*80)
    print('MARKOV REGIME-SWITCHING MODEL IMPLEMENTATION TEST')
    print('='*80)
    
    # Load original data
    data_path = Path(__file__).parent.parent / 'Blockchain_NetworkValue' / 'Data_Dune_MktCap' / 'ethereum_all_trend.csv'
    df = pd.read_csv(data_path, parse_dates=['day'])
    
    # Filter to paper's date range and use nonce_5 (paper's best model)
    df = df[(df['day'] >= '2017-01-01') & (df['day'] <= '2024-12-31')].copy()
    df = df.sort_values('day').reset_index(drop=True)
    
    # Use nonce_5 data
    users = df['dau_nonce_5'].values
    mcap = df['Market_cap'].values
    
    # Clean data
    valid = (users > 0) & (mcap > 0) & np.isfinite(users) & np.isfinite(mcap)
    users = users[valid]
    mcap = mcap[valid]
    
    print(f'\nData loaded:')
    print(f'  Records: {len(users):,}')
    print(f'  Date range: {df.loc[valid, "day"].min().date()} to {df.loc[valid, "day"].max().date()}')
    print(f'  Users: {users.min():,.0f} to {users.max():,.0f}')
    print(f'  Market cap: ${mcap.min()/1e9:.2f}B to ${mcap.max()/1e9:.2f}B')
    
    # Try both raw and STL-smoothed data (original code uses STL smoothing)
    from statsmodels.tsa.seasonal import STL
    
    # STL smoothing (like original code)
    print(f'\nApplying STL smoothing (period=15, like original code)...')
    try:
        stl = STL(users, period=15, robust=True)
        stl_res = stl.fit()
        users_trend = stl_res.trend
        users_seasonal = stl_res.seasonal
        users_resid = stl_res.resid
        
        # Remove NaN values from STL (beginning/end)
        valid_stl = np.isfinite(users_trend) & (users_trend > 0)
        users_trend_clean = users_trend[valid_stl]
        mcap_clean = mcap[valid_stl]
        
        print(f'  STL smoothed: {len(users_trend_clean)} valid points')
        print(f'  Trend range: {users_trend_clean.min():.0f} to {users_trend_clean.max():.0f}')
        
        use_stl = True
        users_final = users_trend_clean
        mcap_final = mcap_clean
    except Exception as e:
        print(f'  ⚠️  STL smoothing failed: {e}')
        print(f'  Using raw data instead')
        use_stl = False
        users_final = users
        mcap_final = mcap
    
    # Log transform
    log_users = np.log(users_final)
    log_mcap = np.log(mcap_final)
    
    # Base OLS for comparison
    X = sm.add_constant(log_users)
    ols_model = sm.OLS(log_mcap, X).fit()
    base_alpha = ols_model.params[0]
    base_beta = ols_model.params[1]
    
    data_type = "STL-smoothed" if use_stl else "raw"
    print(f'\nBase OLS Regression ({data_type} data):')
    print(f'  α = {base_alpha:.4f} (target: ~10.15)')
    print(f'  β = {base_beta:.4f} (target: ~1.3)')
    print(f'  R² = {ols_model.rsquared:.4f}')
    
    # Try split-sample initialization (like original code does)
    print(f'\nSplit-sample analysis (like original code):')
    half_idx = len(log_users) // 2
    first_half_X = sm.add_constant(log_users[:half_idx])
    first_half_y = log_mcap[:half_idx]
    second_half_X = sm.add_constant(log_users[half_idx:])
    second_half_y = log_mcap[half_idx:]
    
    ols_first = sm.OLS(first_half_y, first_half_X).fit()
    ols_second = sm.OLS(second_half_y, second_half_X).fit()
    
    print(f'  First half: β = {ols_first.params[1]:.4f}, α = {ols_first.params[0]:.4f}')
    print(f'  Second half: β = {ols_second.params[1]:.4f}, α = {ols_second.params[0]:.4f}')
    print(f'  β difference: {abs(ols_first.params[1] - ols_second.params[1]):.4f}')
    
    # Use split-sample betas for initialization
    beta_first = ols_first.params[1]
    beta_second = ols_second.params[1]
    alpha_avg = (ols_first.params[0] + ols_second.params[0]) / 2
    
    # Try multiple initialization strategies
    strategies = [
        {
            'name': 'Default initialization',
            'start_params': None,
            'maxiter': 1000,
            'em_iter': 50
        },
        {
            'name': 'Base model initialization (small variation)',
            'start_params': None,  # Will set below
            'maxiter': 1000,
            'em_iter': 50
        },
        {
            'name': 'Paper target initialization',
            'start_params': None,  # Will set below
            'maxiter': 1000,
            'em_iter': 50
        }
    ]
    
    # Create model
    X_exog = log_users.reshape(-1, 1)
    model = MarkovRegression(
        endog=log_mcap,
        exog=X_exog,
        k_regimes=2,
        order=0,
        switching_trend=False,
        switching_exog=True,
        switching_variance=False
    )
    
    print(f'\nModel structure:')
    print(f'  k_params: {model.k_params}')
    if hasattr(model, 'param_names'):
        print(f'  param_names: {model.param_names}')
    
    # Set up initialization strategies
    default_start = model.start_params.copy()
    
    # Strategy 2: Split-sample initialization (use different betas from each half)
    strategy2_start = default_start.copy()
    strategy2_start[0] = 2.94  # P₁₁ in log-odds (p=0.95)
    strategy2_start[1] = -2.94  # P₂₁ in log-odds (p=0.05, so P₂₂=0.95)
    strategy2_start[2] = 0.0  # const[1] - should be 0 with switching_trend=False
    # Use split-sample betas - assign higher to regime 1, lower to regime 2
    if beta_first > beta_second:
        strategy2_start[3] = beta_first  # β₁ from first half (higher)
        strategy2_start[4] = beta_second  # β₂ from second half (lower)
    else:
        strategy2_start[3] = beta_second  # β₁ from second half (higher)
        strategy2_start[4] = beta_first  # β₂ from first half (lower)
    strategy2_start[5] = np.log(np.var(ols_model.resid))  # Log variance
    
    # Strategy 3: Paper target values
    strategy3_start = default_start.copy()
    strategy3_start[0] = 4.6  # P₁₁ in log-odds (p=0.99)
    strategy3_start[1] = -4.6  # P₂₁ in log-odds (p=0.01, so P₂₂=0.99)
    strategy3_start[2] = 0.0  # const[1]
    strategy3_start[3] = 1.31  # β₁ from paper
    strategy3_start[4] = 1.19  # β₂ from paper
    strategy3_start[5] = np.log(np.var(ols_model.resid))
    
    strategies[1]['start_params'] = strategy2_start
    strategies[2]['start_params'] = strategy3_start
    
    best_result = None
    best_aic = np.inf
    
    for i, strategy in enumerate(strategies, 1):
        print(f'\n{"="*80}')
        print(f'Strategy {i}: {strategy["name"]}')
        print(f'{"="*80}')
        
        try:
            fit_kwargs = {
                'maxiter': strategy['maxiter'],
                'em_iter': strategy['em_iter']
            }
            if strategy['start_params'] is not None:
                fit_kwargs['start_params'] = strategy['start_params']
            
            results = model.fit(**fit_kwargs)
            
            # Extract parameters
            params = model.untransform_params(results.params)
            param_names = results.param_names if hasattr(results, 'param_names') else None
            
            # Get transition matrix
            tm = results.regime_transition
            p11 = float(tm[0, 0])
            p22 = float(tm[1, 1])
            
            # Extract betas using parameter names
            beta0_idx = None
            beta1_idx = None
            if param_names:
                for j, name in enumerate(param_names):
                    if 'x1[0]' in name:
                        beta0_idx = j
                    elif 'x1[1]' in name:
                        beta1_idx = j
            
            if beta0_idx is not None and beta1_idx is not None:
                beta1 = params[beta0_idx]
                beta2 = params[beta1_idx]
            elif len(params) >= 5:
                beta1 = params[3]
                beta2 = params[4]
            else:
                beta1 = beta2 = base_beta
            
            # Extract alpha
            alpha_idx = None
            if param_names:
                for j, name in enumerate(param_names):
                    if 'const' in name.lower():
                        alpha_idx = j
                        break
            
            if alpha_idx is not None:
                alpha = params[alpha_idx]
            else:
                # With switching_trend=False, alpha should be constant
                # Might need to calculate from regime-specific constants
                alpha = base_alpha  # Use OLS alpha as approximation
            
            # Check regime distribution
            sp = results.smoothed_marginal_probabilities
            regime1_days = np.sum(sp[:, 0] > 0.5) if sp.ndim > 1 else 0
            regime2_days = len(sp) - regime1_days
            
            print(f'\nResults:')
            print(f'  α = {alpha:.4f} (target: 10.15)')
            print(f'  β₁ = {beta1:.4f} (target: 1.31)')
            print(f'  β₂ = {beta2:.4f} (target: 1.19)')
            print(f'  P₁₁ = {p11:.4f} (target: 0.99)')
            print(f'  P₂₂ = {p22:.4f} (target: 0.99)')
            print(f'  AIC = {results.aic:.2f} (target: ~2108)')
            print(f'\nRegime distribution:')
            print(f'  Regime 1: {regime1_days} days ({100*regime1_days/len(sp):.1f}%)')
            print(f'  Regime 2: {regime2_days} days ({100*regime2_days/len(sp):.1f}%)')
            
            # Check if this is the best result
            if results.aic < best_aic and regime1_days > 0 and regime2_days > 0:
                best_aic = results.aic
                best_result = {
                    'strategy': strategy['name'],
                    'alpha': alpha,
                    'beta1': beta1,
                    'beta2': beta2,
                    'p11': p11,
                    'p22': p22,
                    'aic': results.aic,
                    'regime1_days': regime1_days,
                    'regime2_days': regime2_days,
                    'results': results
                }
            
            if regime1_days > 0 and regime2_days > 0:
                print(f'  ✓ Two regimes identified!')
            else:
                print(f'  ⚠️  Model collapsed to one regime')
                
        except Exception as e:
            print(f'  ✗ Failed: {e}')
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f'\n{"="*80}')
    print('SUMMARY')
    print(f'{"="*80}')
    if best_result:
        print(f'\nBest result (Strategy: {best_result["strategy"]}):')
        print(f'  α = {best_result["alpha"]:.4f}')
        print(f'  β₁ = {best_result["beta1"]:.4f}')
        print(f'  β₂ = {best_result["beta2"]:.4f}')
        print(f'  P₁₁ = {best_result["p11"]:.4f}')
        print(f'  P₂₂ = {best_result["p22"]:.4f}')
        print(f'  AIC = {best_result["aic"]:.2f}')
        print(f'  Regime 1: {best_result["regime1_days"]} days')
        print(f'  Regime 2: {best_result["regime2_days"]} days')
    else:
        print('\n⚠️  No strategy successfully identified two regimes')
        print('   Model is collapsing to one regime in all cases')
        print('   This suggests:')
        print('   1. Data may not have clear regime structure')
        print('   2. Need different initialization approach')
        print('   3. May need to check data quality or preprocessing')

if __name__ == '__main__':
    test_markov_switching()

