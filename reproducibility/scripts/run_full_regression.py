#!/usr/bin/env python3
"""
Run Metcalfe's Law regression on all networks.

Outputs:
- Regression results table
- Classification of network effects
- Performance validation data
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).parent.parent
PROCESSED_DIR = project_root / "data" / "processed"

# All networks with their data files and categories
NETWORKS = {
    # Layer 1
    "ethereum": {"file": "ethereum_correlated_data_nonce5.csv", "category": "L1"},

    # Utility tokens (expected high beta)
    "render": {"file": "render_correlated_data.csv", "category": "Compute"},
    "livepeer": {"file": "livepeer_correlated_data.csv", "category": "Compute"},
    "thegraph": {"file": "thegraph_correlated_data.csv", "category": "Indexing"},
    "chainlink": {"file": "chainlink_correlated_data.csv", "category": "Oracle"},

    # Layer 2s
    "optimism": {"file": "optimism_correlated_data.csv", "category": "L2"},
    "arbitrum": {"file": "arbitrum_correlated_data.csv", "category": "L2"},
    "polygon": {"file": "polygon_correlated_data.csv", "category": "L2"},

    # Governance tokens (expected low beta)
    "ens": {"file": "ens_correlated_data.csv", "category": "Governance"},
    "dimo": {"file": "dimo_correlated_data.csv", "category": "IoT"},
    "uniswap": {"file": "uniswap_correlated_data.csv", "category": "DEX"},

    # New DeFi networks
    "aave": {"file": "aave_correlated_data.csv", "category": "DeFi"},
    "compound": {"file": "compound_correlated_data.csv", "category": "DeFi"},
    "maker": {"file": "maker_correlated_data.csv", "category": "DeFi"},
    "sushiswap": {"file": "sushiswap_correlated_data.csv", "category": "DEX"},
    # Note: Lido excluded - LDO token transfers don't measure Lido stakers
}


def load_data(network: str, config: dict) -> pd.DataFrame:
    """Load network data."""
    filepath = PROCESSED_DIR / config["file"]
    if not filepath.exists():
        return pd.DataFrame()

    df = pd.read_csv(filepath)

    # Standardize columns
    if 'active_users' in df.columns:
        df = df.rename(columns={'active_users': 'users'})

    # Handle date column - prefer 'date' if both exist
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'day' in df.columns:
        df['date'] = pd.to_datetime(df['day'])

    df = df.sort_values('date').reset_index(drop=True)

    # Ensure users column exists
    if 'users' not in df.columns:
        return pd.DataFrame()

    return df[['date', 'users', 'market_cap']].dropna()


def run_regression(users: np.ndarray, market_cap: np.ndarray) -> dict:
    """Run Metcalfe's Law regression: ln(P) = α + β ln(u)"""

    # Filter valid data
    valid = (users > 0) & (market_cap > 0)
    users = users[valid]
    market_cap = market_cap[valid]

    if len(users) < 10:
        return None

    # Log transform
    log_users = np.log(users)
    log_mcap = np.log(market_cap)

    # OLS regression
    X = log_users.reshape(-1, 1)
    y = log_mcap

    reg = LinearRegression()
    reg.fit(X, y)

    beta = reg.coef_[0]
    alpha = reg.intercept_
    r_squared = reg.score(X, y)

    # Standard error and confidence interval
    n = len(y)
    y_pred = reg.predict(X)
    residuals = y - y_pred
    mse = np.sum(residuals ** 2) / (n - 2)
    var_beta = mse / np.sum((log_users - np.mean(log_users)) ** 2)
    std_error = np.sqrt(var_beta)

    # T-statistic for H0: beta = 1
    t_stat = (beta - 1) / std_error
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))

    # 95% CI for beta
    t_crit = stats.t.ppf(0.975, n - 2)
    ci_lower = beta - t_crit * std_error
    ci_upper = beta + t_crit * std_error

    return {
        'alpha': alpha,
        'beta': beta,
        'r_squared': r_squared,
        'std_error': std_error,
        'p_value': p_value,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'n_obs': n
    }


def calculate_performance(df: pd.DataFrame) -> dict:
    """Calculate performance metrics including annualized returns."""
    if df.empty or len(df) < 30:
        return {}

    # Filter to only rows with valid (non-zero) market cap
    valid_df = df[df['market_cap'] > 0].copy()

    if len(valid_df) < 60:  # Need at least 60 valid rows for first/last 30
        return {}

    # First and last 30 observations with valid market cap
    first = valid_df.iloc[:30].mean()
    last = valid_df.iloc[-30:].mean()

    # Market cap return (total)
    if first['market_cap'] > 0:
        mcap_return = (last['market_cap'] - first['market_cap']) / first['market_cap'] * 100
    else:
        mcap_return = np.nan

    # User growth
    if first['users'] > 0:
        user_growth = (last['users'] - first['users']) / first['users'] * 100
    else:
        user_growth = np.nan

    # Calculate annualized return using valid data date range
    start_date = valid_df['date'].min()
    end_date = valid_df['date'].max()
    years = (end_date - start_date).days / 365.25

    if years > 0 and not np.isnan(mcap_return) and mcap_return > -100:
        total_return_ratio = 1 + (mcap_return / 100)
        if total_return_ratio > 0:
            annualized_return = (total_return_ratio ** (1 / years) - 1) * 100
        else:
            annualized_return = np.nan
    else:
        annualized_return = np.nan

    return {
        'mcap_return': mcap_return,
        'annualized_return': annualized_return,
        'years': years,
        'user_growth': user_growth,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }


def classify_network(beta: float, ci_lower: float, ci_upper: float) -> str:
    """Classify network based on beta."""
    if ci_lower > 1.0:
        return "Sustainable (β > 1)"
    elif ci_upper < 1.0:
        return "Unsustainable (β < 1)"
    else:
        return "Borderline (β ≈ 1)"


def main():
    print("="*80)
    print("METCALFE'S LAW REGRESSION ANALYSIS")
    print("="*80)

    results = []

    for network, config in NETWORKS.items():
        print(f"\nProcessing {network.upper()}...")

        df = load_data(network, config)
        if df.empty:
            print(f"  No data found")
            continue

        reg_results = run_regression(
            df['users'].values,
            df['market_cap'].values
        )

        if reg_results is None:
            print(f"  Insufficient data for regression")
            continue

        perf = calculate_performance(df)
        classification = classify_network(
            reg_results['beta'],
            reg_results['ci_lower'],
            reg_results['ci_upper']
        )

        results.append({
            'network': network.capitalize(),
            'category': config['category'],
            'beta': reg_results['beta'],
            'se': reg_results['std_error'],
            'r_squared': reg_results['r_squared'],
            'ci_lower': reg_results['ci_lower'],
            'ci_upper': reg_results['ci_upper'],
            'classification': classification,
            'n_obs': reg_results['n_obs'],
            'mcap_return': perf.get('mcap_return', np.nan),
            'annualized_return': perf.get('annualized_return', np.nan),
            'years': perf.get('years', np.nan),
            'user_growth': perf.get('user_growth', np.nan),
            'start_date': perf.get('start_date', ''),
            'end_date': perf.get('end_date', '')
        })

        print(f"  β = {reg_results['beta']:.3f} (±{reg_results['std_error']:.3f}), R² = {reg_results['r_squared']:.3f}")
        print(f"  Classification: {classification}")

    # Create results DataFrame
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('beta', ascending=False)

    # Save results
    output_file = PROCESSED_DIR / "regression_results_expanded.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n\nSaved results to: {output_file}")

    # Print summary tables
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    print("\n--- Regression Results (sorted by β) ---")
    print(f"{'Network':<12} {'Category':<10} {'β':>8} {'SE':>8} {'R²':>8} {'95% CI':>18} {'Classification':<25}")
    print("-"*95)

    for _, row in results_df.iterrows():
        ci_str = f"[{row['ci_lower']:.2f}, {row['ci_upper']:.2f}]"
        print(f"{row['network']:<12} {row['category']:<10} {row['beta']:>8.3f} {row['se']:>8.3f} {row['r_squared']:>8.3f} {ci_str:>18} {row['classification']:<25}")

    # Classification summary
    print("\n--- Classification Summary ---")
    sustainable = results_df[results_df['classification'].str.contains('Sustainable')]
    borderline = results_df[results_df['classification'].str.contains('Borderline')]
    unsustainable = results_df[results_df['classification'].str.contains('Unsustainable')]

    print(f"Sustainable (β > 1):   {len(sustainable)} networks")
    if len(sustainable) > 0:
        print(f"  Networks: {', '.join(sustainable['network'].tolist())}")

    print(f"Borderline (β ≈ 1):    {len(borderline)} networks")
    if len(borderline) > 0:
        print(f"  Networks: {', '.join(borderline['network'].tolist())}")

    print(f"Unsustainable (β < 1): {len(unsustainable)} networks")
    if len(unsustainable) > 0:
        print(f"  Networks: {', '.join(unsustainable['network'].tolist())}")

    # Performance validation
    print("\n--- Performance Validation (Annualized Returns) ---")
    print(f"{'Classification':<25} {'Avg β':>8} {'Avg R²':>8} {'Median Ann. Ret':>16} {'Positive Returns':>18}")
    print("-"*90)

    for group_name, group_df in [
        ("Sustainable (β > 1)", sustainable),
        ("Borderline (β ≈ 1)", borderline),
        ("Unsustainable (β < 1)", unsustainable)
    ]:
        if len(group_df) == 0:
            continue
        avg_beta = group_df['beta'].mean()
        avg_r2 = group_df['r_squared'].mean()
        valid_returns = group_df['annualized_return'].dropna()
        valid_total = group_df['mcap_return'].dropna()
        if len(valid_returns) > 0:
            median_ann_return = valid_returns.median()
            positive_pct = (valid_total > 0).sum() / len(valid_total) * 100
        else:
            median_ann_return = np.nan
            positive_pct = np.nan

        print(f"{group_name:<25} {avg_beta:>8.2f} {avg_r2:>8.2f} {median_ann_return:>15.1f}% {positive_pct:>17.0f}%")

    # Individual network returns
    print("\n--- Individual Network Annualized Returns ---")
    print(f"{'Network':<12} {'β':>8} {'Years':>6} {'Ann. Return':>12} {'Total Return':>14}")
    print("-"*55)
    for _, row in results_df.iterrows():
        ann_ret = row['annualized_return']
        total_ret = row['mcap_return']
        years = row['years']
        ann_str = f"{ann_ret:>10.1f}%" if not np.isnan(ann_ret) else "N/A"
        total_str = f"{total_ret:>12.0f}%" if not np.isnan(total_ret) else "N/A"
        print(f"{row['network']:<12} {row['beta']:>8.2f} {years:>6.1f} {ann_str:>12} {total_str:>14}")

    print("\n" + "="*80)
    print(f"Total networks analyzed: {len(results_df)}")
    print("="*80)

    return results_df


if __name__ == "__main__":
    main()
