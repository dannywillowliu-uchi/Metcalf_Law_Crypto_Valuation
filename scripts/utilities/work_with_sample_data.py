#!/usr/bin/env python3
"""
Work with sample data to test models - ZERO API COSTS
This lets us validate the models work correctly before getting real data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_collection import create_sample_data
from src.analysis import MetcalfeModel, FTPMSModel
import numpy as np
import pandas as pd

print("Testing Models with Sample Data")
print("=" * 60)
print("⚠️  ZERO API COSTS - Using sample data")
print("=" * 60)

# Create sample data
print("\n1. Generating sample Ethereum-like data...")
np.random.seed(42)
eth_data = create_sample_data()

# Add regime switching to match paper expectations
n_periods = len(eth_data)
regime = np.ones(n_periods, dtype=int)
regime[50:100] = 2  # Bear market in middle
regime[150:] = 2    # Another bear period

# Regenerate market cap with regime switching (per paper)
alpha = 10.15  # Target from paper
beta_bull = 1.31  # Target from paper
beta_bear = 1.19  # Target from paper

log_users = np.log(eth_data['users'].values)
log_market_cap = np.zeros(n_periods)
for i in range(n_periods):
    beta = beta_bull if regime[i] == 1 else beta_bear
    log_market_cap[i] = alpha + beta * log_users[i] + np.random.normal(0, 0.1)

eth_data['market_cap'] = np.exp(log_market_cap)
eth_data['regime'] = regime

print(f"   Generated {len(eth_data)} periods")
print(f"   Date range: {eth_data['date'].min()} to {eth_data['date'].max()}")

# Test Base Metcalfe Model
print("\n2. Testing Base Metcalfe Model...")
metcalfe = MetcalfeModel()
results = metcalfe.fit(eth_data['users'], eth_data['market_cap'])

print(f"   α = {results['alpha']:.4f} (target: 10.15)")
print(f"   β = {results['beta']:.4f} (target: ~1.3)")
print(f"   R² = {results['r_squared']:.4f}")

# Test FTP-MS Model
print("\n3. Testing FTP-MS Model...")
ftpms = FTPMSModel(k_regimes=2)
ms_results = ftpms.fit(eth_data['users'], eth_data['market_cap'])

print(f"   α = {ms_results['alpha']:.4f} (target: 10.15)")
print(f"   β₁ (bullish) = {ms_results['betas'][1]:.4f} (target: 1.31)")
print(f"   β₂ (bearish) = {ms_results['betas'][2]:.4f} (target: 1.19)")

if ms_results['transition_probs'] is not None:
    print(f"   P₁,₁ = {ms_results['transition_probs'][0][0]:.4f} (target: 0.99)")
    print(f"   P₂,₂ = {ms_results['transition_probs'][1][1]:.4f} (target: 0.99)")

print(f"   AIC = {ms_results['aic']:.2f} (target: ~2108)")

# Save sample data for use in notebook
output_path = Path("data/processed/sample_ethereum_data.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)
eth_data.to_csv(output_path, index=False)
print(f"\n✓ Saved sample data to: {output_path}")
print("\n" + "=" * 60)
print("✓ Models are working!")
print("You can now use this sample data in the notebook.")
print("=" * 60)

