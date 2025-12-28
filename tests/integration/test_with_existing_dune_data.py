#!/usr/bin/env python3
"""Test models with existing Dune data (2018-2024)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()
from src.data_collection import EthereumDataCollector
from src.analysis import MetcalfeModel, FTPMSModel

print("Testing Models with Existing Dune Data")
print("=" * 60)

# Get active addresses from Dune (query #3488164)
print("\n1. Fetching active addresses from Dune (query #3488164)...")
collector = EthereumDataCollector()
users_df = collector.get_active_addresses_dune_csv(3488164)
print(f"   ✓ Loaded {len(users_df)} records from Dune")
print(f"   Date range: {users_df['date'].min()} to {users_df['date'].max()}")

# Filter out zeros
users_df = users_df[users_df['active_addresses'] > 0].copy()
users_df = users_df.rename(columns={'active_addresses': 'users'})
print(f"   After filtering zeros: {len(users_df)} records")
print(f"   Active addresses range: {users_df['users'].min():.0f} - {users_df['users'].max():.0f}")

# Note: CoinGecko free tier only provides last 365 days
# Dune data is from 2018-2024, so we'll use sample market cap for testing
# OR you can get a CoinGecko API key to fetch historical market cap
print("\n2. Generating market cap data...")
print("   Note: CoinGecko free tier only provides last 365 days.")
print("   Dune data is from 2018-2024, so using sample market cap based on Metcalfe's Law.")
print("   To get real market cap, add COINGECKO_API_KEY to .env and use historical endpoint.")

# Generate realistic market cap based on users (inverse of Metcalfe's Law)
# Using paper's parameters: α ≈ 10.15, β ≈ 1.3
alpha = 10.15
beta = 1.3
log_users = np.log(users_df['users'].values)
log_mcap = alpha + beta * log_users + np.random.normal(0, 0.15, len(log_users))
market_cap = np.exp(log_mcap)

market_cap_df = pd.DataFrame({
    'date': users_df['date'].values,
    'market_cap': market_cap
})

print(f"   ✓ Generated {len(market_cap_df)} market cap records")
print(f"   Market cap range: ${market_cap_df['market_cap'].min():.2e} - ${market_cap_df['market_cap'].max():.2e}")

# Merge data
print("\n3. Merging data...")
eth_data = pd.merge(
    users_df[['date', 'users']],
    market_cap_df[['date', 'market_cap']],
    on='date',
    how='inner'
)
eth_data = eth_data.sort_values('date').reset_index(drop=True)

print(f"   ✓ Merged dataset: {len(eth_data)} records")
print(f"   Users range: {eth_data['users'].min():.0f} - {eth_data['users'].max():.0f}")
print(f"   Market cap range: ${eth_data['market_cap'].min():.2e} - ${eth_data['market_cap'].max():.2e}")

# Test Base Metcalfe Model
print("\n4. Testing Base Metcalfe Model...")
metcalfe = MetcalfeModel()
results = metcalfe.fit(eth_data['users'], eth_data['market_cap'])

print(f"   α = {results['alpha']:.4f} (target: ~10.15)")
print(f"   β = {results['beta']:.4f} (target: ~1.3)")
print(f"   R² = {results['r_squared']:.4f}")
print(f"   Standard Error = {results['std_error']:.4f}")
print(f"   P-value = {results['p_value']:.6f}")

# Test FTP-MS Model
print("\n5. Testing FTP-MS Model...")
ftpms = FTPMSModel(k_regimes=2)
try:
    ms_results = ftpms.fit(
        eth_data['users'], 
        eth_data['market_cap'],
        maxiter=1000,
        tolerance=1e-6,
        em_iter=100
    )
    
    print(f"   α = {ms_results['alpha']:.4f} (target: ~10.15)")
    print(f"   β₁ (bullish) = {ms_results['betas'][1]:.4f} (target: ~1.31)")
    print(f"   β₂ (bearish) = {ms_results['betas'][2]:.4f} (target: ~1.19)")
    
    if ms_results['transition_probs'] is not None:
        print(f"   P₁,₁ = {ms_results['transition_probs'][0][0]:.4f} (target: ~0.99)")
        print(f"   P₂,₂ = {ms_results['transition_probs'][1][1]:.4f} (target: ~0.99)")
    
    if ms_results['aic'] is not None:
        print(f"   AIC = {ms_results['aic']:.2f} (target: ~2108)")
        
except Exception as e:
    print(f"   ⚠️  Error fitting FTP-MS model: {e}")

# Save combined data
output_path = Path("data/processed/ethereum_with_dune_data.csv")
eth_data.to_csv(output_path, index=False)
print(f"\n✓ Saved complete dataset to: {output_path}")

print("\n" + "=" * 60)
print("Testing complete!")
print("\nNote: To get real market cap data for 2018-2024:")
print("1. Get CoinGecko API key: https://www.coingecko.com/en/api")
print("2. Add to .env: COINGECKO_API_KEY=your_key")
print("3. The historical endpoint will automatically be used")

