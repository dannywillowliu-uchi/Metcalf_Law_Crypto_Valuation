#!/usr/bin/env python3
"""
Collect data for new DeFi networks using already-executed Dune queries.

The Dune queries have been executed - this script:
1. Downloads results from executed queries
2. Fetches market cap from CoinGecko
3. Merges and saves the data

Usage:
    python scripts/collect_defi_data.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
import requests
import time
from datetime import datetime
import io

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

DUNE_API_KEY = os.getenv("DUNE_API_KEY", "N4FR6rr5eSbLKSJTZ2oI74XuWU7N8WyY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "CG-6MtB6MpJvL93fbAXryMW822G")

# Query IDs from successful execution
NETWORKS = {
    "aave": {
        "query_id": 6420515,
        "coingecko_id": "aave",
        "start_date": "2020-09-24",
    },
    "compound": {
        "query_id": 6420519,
        "coingecko_id": "compound-governance-token",
        "start_date": "2020-06-15",
    },
    "lido": {
        "query_id": 6420520,
        "coingecko_id": "lido-dao",
        "start_date": "2021-01-05",
    },
    "maker": {
        "query_id": 6420524,
        "coingecko_id": "maker",
        "start_date": "2017-12-01",
    },
    "sushiswap": {
        "query_id": 6420526,
        "coingecko_id": "sushi",
        "start_date": "2020-08-28",
    },
}


def download_dune_results(query_id: int) -> pd.DataFrame:
    """Download results from an executed Dune query."""
    print(f"  Downloading query #{query_id}...")

    url = f"https://api.dune.com/api/v1/query/{query_id}/results/csv"
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY}

    response = requests.get(url, headers=headers, timeout=120)

    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text))
        print(f"  Got {len(df)} rows")
        return df
    else:
        print(f"  Error: {response.status_code}")
        return pd.DataFrame()


def download_market_cap(coin_id: str, start_date: str) -> pd.DataFrame:
    """Download market cap from CoinGecko using the days endpoint."""
    print(f"  Downloading {coin_id} market cap...")

    cache_dir = project_root / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check cache
    cache_files = list(cache_dir.glob(f"market_cap_{coin_id}*.csv"))
    if cache_files:
        cache_file = sorted(cache_files)[-1]
        print(f"  Using cached: {cache_file.name}")
        df = pd.read_csv(cache_file)
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df[['date', 'market_cap']].dropna()

    # Calculate days since start
    start_dt = pd.to_datetime(start_date)
    days = (datetime.now() - start_dt).days + 1
    days = min(days, 2000)  # CoinGecko limit

    # Use Pro API endpoint with days parameter
    url = f"https://pro-api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily",
        "x_cg_pro_api_key": COINGECKO_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if "market_caps" not in data:
            print(f"  No market cap data")
            return pd.DataFrame()

        df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["date"] = df["date"].dt.normalize()
        df = df.drop_duplicates(subset=["date"], keep="first")

        # Cache result
        end_date = datetime.now().strftime("%Y-%m-%d")
        cache_file = cache_dir / f"market_cap_{coin_id}_{start_date}_{end_date}.csv"
        df.to_csv(cache_file, index=False)

        print(f"  Got {len(df)} days of market cap")
        return df[['date', 'market_cap']]

    except Exception as e:
        print(f"  Error: {e}")
        return pd.DataFrame()


def process_network(name: str, config: dict) -> pd.DataFrame:
    """Process a single network."""
    print(f"\n{'='*60}")
    print(f"Processing {name.upper()}")
    print(f"{'='*60}")

    # Download Dune data
    print("\n1. Active addresses from Dune:")
    addr_df = download_dune_results(config["query_id"])

    if addr_df.empty:
        return pd.DataFrame()

    # Normalize columns
    if 'day' in addr_df.columns:
        addr_df['date'] = pd.to_datetime(addr_df['day'])
    addr_df['users'] = addr_df['active_addresses']
    addr_df = addr_df[['date', 'users']].copy()
    addr_df['date'] = addr_df['date'].dt.tz_localize(None) if addr_df['date'].dt.tz else addr_df['date']
    addr_df['date'] = addr_df['date'].dt.normalize()

    print(f"  Date range: {addr_df['date'].min().date()} to {addr_df['date'].max().date()}")

    # Download market cap
    print("\n2. Market cap from CoinGecko:")
    mcap_df = download_market_cap(config["coingecko_id"], config["start_date"])

    if mcap_df.empty:
        # Save user data only
        output_dir = project_root / "data" / "processed"
        output_file = output_dir / f"{name}_users_only.csv"
        addr_df.to_csv(output_file, index=False)
        print(f"  Saved users only: {output_file.name}")
        return pd.DataFrame()

    mcap_df['date'] = pd.to_datetime(mcap_df['date'])
    mcap_df['date'] = mcap_df['date'].dt.tz_localize(None) if mcap_df['date'].dt.tz else mcap_df['date']
    mcap_df['date'] = mcap_df['date'].dt.normalize()

    # Merge
    print("\n3. Merging data:")
    df = pd.merge(addr_df, mcap_df, on='date', how='inner')
    df = df.sort_values('date').reset_index(drop=True)

    print(f"  Combined: {len(df)} observations")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Save
    output_dir = project_root / "data" / "processed"
    output_file = output_dir / f"{name}_correlated_data.csv"
    df.to_csv(output_file, index=False)
    print(f"  Saved: {output_file.name}")

    return df


def main():
    print("="*60)
    print("DeFi Network Data Collection")
    print("="*60)

    results = {}

    for name, config in NETWORKS.items():
        try:
            df = process_network(name, config)
            results[name] = len(df) if not df.empty else 0
            time.sleep(2)  # Rate limiting
        except Exception as e:
            print(f"  ERROR: {e}")
            results[name] = 0

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for name, count in results.items():
        status = "OK" if count > 0 else "FAILED"
        print(f"  {name}: {count} observations [{status}]")

    successful = sum(1 for c in results.values() if c > 0)
    print(f"\n  Total: {successful}/{len(results)} networks collected")


if __name__ == "__main__":
    main()
