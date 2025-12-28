#!/usr/bin/env python3
"""Test query #6200338 and validate against paper targets"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from src.data_collection import EthereumDataCollector
from src.analysis import MetcalfeModel, FTPMSModel

print("="*80)
print("TESTING QUERY #6200338 - Ethereum Active Addresses (nonce >= 5)")
print("="*80)

# Fetch active addresses
print("\n1. Fetching active addresses from Dune (query #6200338)...")
collector = EthereumDataCollector()
users_df = collector.get_active_addresses_dune_csv(6200338)
print(f"   ✓ Loaded {len(users_df)} records from Dune")
print(f"   Date range: {users_df['date'].min()} to {users_df['date'].max()}")

# Filter out zeros
users_df = users_df[users_df['active_addresses'] > 0].copy()
users_df = users_df.rename(columns={'active_addresses': 'users'})
print(f"   After filtering zeros: {len(users_df)} records")
print(f"   Active addresses range: {users_df['users'].min():.0f} - {users_df['users'].max():.0f}")
print(f"   Mean active addresses: {users_df['users'].mean():.0f}")

# Get market cap data for the same date range
start_date = users_df['date'].min().strftime('%Y-%m-%d')
end_date = users_df['date'].max().strftime('%Y-%m-%d')

print(f"\n2. Fetching market cap data from BitInfoCharts...")
print(f"   Date range: {start_date} to {end_date}")

try:
    market_cap_df = collector.get_market_cap_history_bitinfocharts(
        start_date=start_date,
        end_date=end_date
    )
    print(f"   ✓ Fetched {len(market_cap_df)} market cap records")
    print(f"   Market cap range: ${market_cap_df['market_cap'].min():.2e} - ${market_cap_df['market_cap'].max():.2e}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")
    market_cap_df = pd.DataFrame()

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
    
    # Correlation
    print("\n4. Correlation Analysis:")
    correlation = np.corrcoef(np.log(eth_data['users']), np.log(eth_data['market_cap']))[0, 1]
    print(f"   Log-log correlation: {correlation:.4f}")
    
    # Base Metcalfe Model
    print("\n5. Testing Base Metcalfe Model...")
    print("   Paper targets: α ≈ 10.15, β ≈ 1.3, R² > 0.95")
    metcalfe = MetcalfeModel()
    results_base = metcalfe.fit(eth_data['users'], eth_data['market_cap'])
    
    print(f"\n   Our Results:")
    print(f"   α = {results_base['alpha']:.4f} (target: ~10.15, diff: {results_base['alpha'] - 10.15:+.2f})")
    print(f"   β = {results_base['beta']:.4f} (target: ~1.3, diff: {results_base['beta'] - 1.3:+.2f})")
    print(f"   R² = {results_base['r_squared']:.4f} (target: >0.95)")
    print(f"   Standard Error = {results_base['std_error']:.4f}")
    print(f"   P-value = {results_base['p_value']:.6f}")
    
    # Validation
    print("\n6. Validation against paper:")
    alpha_ok = abs(results_base['alpha'] - 10.15) <= 0.5
    beta_ok = abs(results_base['beta'] - 1.3) <= 0.1
    r2_ok = results_base['r_squared'] > 0.95
    
    print(f"   α within range (±0.5): {'✅' if alpha_ok else '❌'}")
    print(f"   β within range (±0.1): {'✅' if beta_ok else '❌'}")
    print(f"   R² > 0.95: {'✅' if r2_ok else '❌'}")
    
    if alpha_ok and beta_ok and r2_ok:
        print("\n   🎉 SUCCESS! Results match paper targets!")
    else:
        print("\n   ⚠️  Results don't fully match paper targets")
        print("   This could be due to:")
        print("   - Different date range")
        print("   - Different market cap source")
        print("   - Data quality differences")
    
    # Save results
    output_path = Path("data/processed/ethereum_correlated_data_nonce5.csv")
    eth_data.to_csv(output_path, index=False)
    print(f"\n✓ Saved correlated data to: {output_path}")
    
    # Try FTP-MS model
    print("\n7. Testing FTP-MS Model (this may take a moment)...")
    print("   Paper targets: β₁ ≈ 1.31, β₂ ≈ 1.19")
    try:
        ftpms = FTPMSModel()
        results_ms = ftpms.fit(eth_data['users'], eth_data['market_cap'], maxiter=1000)
        
        print(f"\n   Our Results:")
        print(f"   α = {results_ms['alpha']:.4f} (target: ~10.15)")
        print(f"   β₁ (Bullish) = {results_ms['betas'][1]:.4f} (target: ~1.31, diff: {results_ms['betas'][1] - 1.31:+.2f})")
        print(f"   β₂ (Bearish) = {results_ms['betas'][2]:.4f} (target: ~1.19, diff: {results_ms['betas'][2] - 1.19:+.2f})")
        if 'transition_probs' in results_ms:
            print(f"   P₁₁ = {results_ms['transition_probs'].get('P11', 'N/A')}")
            print(f"   P₂₂ = {results_ms['transition_probs'].get('P22', 'N/A')}")
    except Exception as e:
        print(f"   ⚠️  FTP-MS model error: {e}")
        print("   This may need more iterations or different initialization")
    
else:
    print("   ⚠️  No market cap data available for correlation")

print("\n" + "="*80)
print("Analysis complete!")
print("="*80)

