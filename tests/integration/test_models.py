#!/usr/bin/env python3
"""
Quick test script to verify the models work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import numpy as np
import pandas as pd
from src.analysis import MetcalfeModel, FTPMSModel

print("Testing Network Effects Models")
print("=" * 60)

# Generate test data
np.random.seed(42)
n_periods = 100

# Simulate user growth
base_users = 10000
growth_rate = 0.02
users = base_users * np.exp(growth_rate * np.arange(n_periods))
users += np.random.normal(0, users * 0.05, n_periods)
users = np.maximum(users, 1000)

# Simulate market cap with known beta
alpha = 10.0
beta_true = 1.3
log_users = np.log(users)
log_market_cap = alpha + beta_true * log_users + np.random.normal(0, 0.1, n_periods)
market_cap = np.exp(log_market_cap)

print(f"\nGenerated {n_periods} periods of test data")
print(f"Users range: {users.min():.0f} - {users.max():.0f}")
print(f"Market cap range: ${market_cap.min():.2e} - ${market_cap.max():.2e}")

# Test 1: Base Metcalfe Model
print("\n" + "=" * 60)
print("Test 1: Base Metcalfe Model")
print("=" * 60)

try:
    metcalfe = MetcalfeModel()
    results = metcalfe.fit(users, market_cap)
    
    print(f"✓ Model fitted successfully")
    print(f"  α (alpha): {results['alpha']:.4f}")
    print(f"  β (beta): {results['beta']:.4f} (expected ≈ {beta_true})")
    print(f"  R²: {results['r_squared']:.4f}")
    print(f"  Standard Error: {results['std_error']:.4f}")
    print(f"  P-value: {results['p_value']:.6f}")
    
    # Check if beta is close to expected
    if abs(results['beta'] - beta_true) < 0.2:
        print(f"  ✓ Beta is close to expected value")
    else:
        print(f"  ⚠ Beta differs from expected (difference: {abs(results['beta'] - beta_true):.4f})")
    
    # Test prediction
    test_users = np.array([50000, 100000, 200000])
    predictions = metcalfe.predict(test_users)
    print(f"\n  Prediction test:")
    for u, p in zip(test_users, predictions):
        print(f"    {u:,} users → ${p:,.2e} market cap")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: FTP-MS Model
print("\n" + "=" * 60)
print("Test 2: FTP-MS Markov-Switching Model")
print("=" * 60)

try:
    # Create data with regime switching
    regime = np.ones(n_periods, dtype=int)
    regime[30:70] = 2  # Bear market in middle
    
    beta_bull = 1.31
    beta_bear = 1.19
    
    log_market_cap_ms = np.zeros(n_periods)
    for i in range(n_periods):
        beta = beta_bull if regime[i] == 1 else beta_bear
        log_market_cap_ms[i] = alpha + beta * log_users[i] + np.random.normal(0, 0.1)
    
    market_cap_ms = np.exp(log_market_cap_ms)
    
    ftpms = FTPMSModel(k_regimes=2)
    ms_results = ftpms.fit(users, market_cap_ms)
    
    print(f"✓ Model fitted successfully")
    print(f"  α (alpha): {ms_results['alpha']:.4f}")
    print(f"  β₁ (bullish): {ms_results['betas'][1]:.4f} (expected ≈ {beta_bull})")
    print(f"  β₂ (bearish): {ms_results['betas'][2]:.4f} (expected ≈ {beta_bear})")
    
    if ms_results['transition_probs'] is not None:
        print(f"\n  Transition Probabilities:")
        print(f"    P(st+1=1 | st=1): {ms_results['transition_probs'][0][0]:.4f}")
        print(f"    P(st+1=2 | st=2): {ms_results['transition_probs'][1][1]:.4f}")
    
    if ms_results['aic'] is not None:
        print(f"\n  Model Fit:")
        print(f"    AIC: {ms_results['aic']:.2f}")
        print(f"    BIC: {ms_results['bic']:.2f}")
        print(f"    Log-Likelihood: {ms_results['log_likelihood']:.2f}")
    
    if ms_results['current_regime'] is not None:
        regime_name = 'Bullish' if ms_results['current_regime'] == 1 else 'Bearish'
        print(f"\n  Current Regime: {ms_results['current_regime']} ({regime_name})")
    
    # Check if betas are reasonable
    beta1_diff = abs(ms_results['betas'][1] - beta_bull)
    beta2_diff = abs(ms_results['betas'][2] - beta_bear)
    
    if beta1_diff < 0.3 and beta2_diff < 0.3:
        print(f"\n  ✓ Betas are close to expected values")
    else:
        print(f"\n  ⚠ Beta differences: β₁={beta1_diff:.4f}, β₂={beta2_diff:.4f}")
    
    # Test prediction
    test_users = np.array([50000, 100000])
    pred_bull = ftpms.predict(test_users, regime=1)
    pred_bear = ftpms.predict(test_users, regime=2)
    print(f"\n  Prediction test (regime-specific):")
    for u, p1, p2 in zip(test_users, pred_bull, pred_bear):
        print(f"    {u:,} users → Bull: ${p1:,.2e}, Bear: ${p2:,.2e}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing Complete")
print("=" * 60)

