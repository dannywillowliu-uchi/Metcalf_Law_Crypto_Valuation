#!/usr/bin/env python3
"""Correlate Dune active addresses with CoinGecko market cap data"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from src.data_collection import EthereumDataCollector
from src.analysis import MetcalfeModel, FTPMSModel

print("Correlating Dune Active Addresses with CoinGecko Market Cap")
print("=" * 60)

# Get Dune active addresses data
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

# Get market cap data for the same date range
start_date = users_df['date'].min().strftime('%Y-%m-%d')
end_date = users_df['date'].max().strftime('%Y-%m-%d')

print(f"\n2. Fetching market cap data from BitInfoCharts...")
print(f"   Date range: {start_date} to {end_date}")
print(f"   (Using BitInfoCharts - free, unlimited historical, accurate market cap)")

try:
    market_cap_df = collector.get_market_cap_history_bitinfocharts(
        start_date=start_date,
        end_date=end_date
    )
    print(f"   ✓ Fetched {len(market_cap_df)} market cap records")
    print(f"   Market cap range: ${market_cap_df['market_cap'].min():.2e} - ${market_cap_df['market_cap'].max():.2e}")
except Exception as e:
    print(f"   ⚠️  BitInfoCharts failed: {e}")
    print("   Falling back to price × supply method...")
    try:
        market_cap_df = collector.get_market_cap_from_price_supply(
            start_date=start_date,
            end_date=end_date
        )
        print(f"   ✓ Fetched {len(market_cap_df)} market cap records using price × supply")
    except Exception as e2:
        print(f"   ⚠️  Fallback also failed: {e2}")
        market_cap_df = pd.DataFrame()  # Empty for now

# Merge data
print("\n3. Merging data...")
if len(market_cap_df) > 0:
    eth_data = pd.merge(
        users_df[['date', 'users']],
        market_cap_df[['date', 'market_cap']],
        on='date',
        how='inner'
    )
    eth_data = eth_data.sort_values('date').reset_index(drop=True)
    
    print(f"   ✓ Merged dataset: {len(eth_data)} records")
    print(f"   Date range: {eth_data['date'].min()} to {eth_data['date'].max()}")
    print(f"   Users range: {eth_data['users'].min():.0f} - {eth_data['users'].max():.0f}")
    print(f"   Market cap range: ${eth_data['market_cap'].min():.2e} - ${eth_data['market_cap'].max():.2e}")
    
    # Show correlation
    print("\n4. Correlation Analysis:")
    correlation = np.corrcoef(np.log(eth_data['users']), np.log(eth_data['market_cap']))[0, 1]
    print(f"   Log-log correlation: {correlation:.4f}")
    
    # Test Base Metcalfe Model
    print("\n5. Testing Base Metcalfe Model...")
    metcalfe = MetcalfeModel()
    results = metcalfe.fit(eth_data['users'], eth_data['market_cap'])
    
    print(f"   α = {results['alpha']:.4f} (target: ~10.15)")
    print(f"   β = {results['beta']:.4f} (target: ~1.3)")
    print(f"   R² = {results['r_squared']:.4f}")
    print(f"   Standard Error = {results['std_error']:.4f}")
    print(f"   P-value = {results['p_value']:.6f}")
    
    # Show sample of merged data
    print("\n6. Sample of merged data:")
    print(eth_data.head(10).to_string())
    print("\n   ...")
    print(eth_data.tail(10).to_string())
    
    # Save
    output_path = Path("data/processed/ethereum_correlated_data.csv")
    eth_data.to_csv(output_path, index=False)
    print(f"\n✓ Saved correlated data to: {output_path}")
    
else:
    print("   ⚠️  No market cap data available for correlation")
    print("   Dune data available but CoinGecko data is missing")
    print("   Date range needed: 2018-11-02 to 2025-11-13")
    print("   CoinGecko free tier only provides last 365 days")

print("\n" + "=" * 60)
print("Correlation complete!")

