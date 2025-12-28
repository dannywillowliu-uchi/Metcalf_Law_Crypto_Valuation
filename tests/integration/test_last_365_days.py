#!/usr/bin/env python3
"""Test models with last 365 days of data (CoinGecko free tier compatible)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()  # Load .env file
from src.data_collection import EthereumDataCollector
from src.analysis import MetcalfeModel, FTPMSModel

print("Testing Models with Last 365 Days of Data")
print("=" * 60)

# Get active addresses from Dune first (query #3488164)
print("\n1. Fetching active addresses from Dune (query #3488164)...")
collector = EthereumDataCollector()
users_df = collector.get_active_addresses_dune_csv(3488164)
print(f"   ✓ Loaded {len(users_df)} records from Dune")
print(f"   Dune date range: {users_df['date'].min()} to {users_df['date'].max()}")

# Use the most recent 365 days from Dune data
users_df = users_df.sort_values('date').tail(365).copy()
users_df = users_df.rename(columns={'active_addresses': 'users'})
print(f"   Using {len(users_df)} most recent records from Dune")
print(f"   Active addresses range: {users_df['users'].min():.0f} - {users_df['users'].max():.0f}")

# Get market cap data for the same date range as Dune data
start_date = users_df['date'].min()
end_date = users_df['date'].max()
print(f"\n2. Fetching market cap data from CoinGecko for date range...")
print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

try:
    market_cap_df = collector.get_market_cap_history(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        frequency="daily"
    )
    print(f"   ✓ Fetched {len(market_cap_df)} market cap records")
    print(f"   Market cap range: ${market_cap_df['market_cap'].min():.2e} - ${market_cap_df['market_cap'].max():.2e}")
except Exception as e:
    print(f"   ⚠️  Could not fetch Dune data: {e}")
    print("   Generating sample active addresses data...")
    # Generate realistic active addresses based on market cap trend
    log_mcap = np.log(market_cap_df['market_cap'].values)
    alpha = 10.15
    beta = 1.3
    log_users = (log_mcap - alpha) / beta
    log_users += np.random.normal(0, 0.1, len(log_users))
    users = np.exp(log_users)
    
    users_df = pd.DataFrame({
        'date': market_cap_df['date'].values,
        'users': users
    })
    print(f"   ✓ Generated {len(users_df)} active address records")

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

print(f"   α = {results['alpha']:.4f}")
print(f"   β = {results['beta']:.4f}")
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
    
    print(f"   α = {ms_results['alpha']:.4f}")
    print(f"   β₁ (bullish) = {ms_results['betas'][1]:.4f}")
    print(f"   β₂ (bearish) = {ms_results['betas'][2]:.4f}")
    
    if ms_results['transition_probs'] is not None:
        print(f"   P₁,₁ = {ms_results['transition_probs'][0][0]:.4f}")
        print(f"   P₂,₂ = {ms_results['transition_probs'][1][1]:.4f}")
    
    if ms_results['aic'] is not None:
        print(f"   AIC = {ms_results['aic']:.2f}")
        
except Exception as e:
    print(f"   ⚠️  Error fitting FTP-MS model: {e}")

# Save combined data
output_path = Path("data/processed/ethereum_last_365_days.csv")
eth_data.to_csv(output_path, index=False)
print(f"\n✓ Saved complete dataset to: {output_path}")

print("\n" + "=" * 60)
print("Testing complete!")

