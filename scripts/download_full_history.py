#!/usr/bin/env python3
"""
Download FULL historical data from existing Dune queries.

The queries already have complete data - this script just downloads it all
and merges with market cap data.

Usage:
    python scripts/download_full_history.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
import requests
import time
from datetime import datetime

project_root = Path(__file__).parent.parent

# Dune query IDs (already executed with full history)
QUERIES = {
    "livepeer": {
        "query_id": 6384048,
        "coingecko_id": "livepeer",
        "start_date": "2018-04-01",
    },
    "uniswap": {
        "query_id": 6384049,
        "coingecko_id": "uniswap",
        "start_date": "2020-05-01",
    },
    "thegraph": {
        "query_id": 6384050,
        "coingecko_id": "the-graph",
        "start_date": "2020-12-17",
    },
}

DUNE_API_KEY = os.getenv("DUNE_API_KEY", "N4FR6rr5eSbLKSJTZ2oI74XuWU7N8WyY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "CG-tRzuahSykiNCNpTxJV4ndtzu")


def download_dune_results(query_id: int) -> pd.DataFrame:
    """Download all results from a Dune query."""
    print(f"  Downloading query {query_id}...")

    url = f"https://api.dune.com/api/v1/query/{query_id}/results"
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY}

    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()

    data = response.json()
    rows = data.get("result", {}).get("rows", [])

    if not rows:
        print(f"  No rows returned")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    print(f"  Got {len(df)} rows")
    return df


def download_coingecko_history(coin_id: str, start_date: str) -> pd.DataFrame:
    """Download full market cap history from CoinGecko."""
    print(f"  Downloading {coin_id} market cap...")

    # Check cache first
    cache_dir = project_root / "data" / "cache"
    cache_files = list(cache_dir.glob(f"market_cap_{coin_id}*.csv"))

    if cache_files:
        # Use most recent cache file
        cache_file = sorted(cache_files)[-1]
        print(f"  Using cached: {cache_file.name}")
        df = pd.read_csv(cache_file)

        # Normalize column names
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])

        return df[['date', 'market_cap']].dropna()

    # Fetch from API
    start_dt = pd.to_datetime(start_date)
    end_dt = datetime.now()

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": int(start_dt.timestamp()),
        "to": int(end_dt.timestamp()),
    }
    if COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_API_KEY

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    if "market_caps" not in data:
        print(f"  No market cap data")
        return pd.DataFrame()

    df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Cache result
    end_str = end_dt.strftime("%Y-%m-%d")
    cache_file = cache_dir / f"market_cap_{coin_id}_{start_date}_{end_str}.csv"
    df.to_csv(cache_file, index=False)

    return df[['date', 'market_cap']]


def process_network(name: str, config: dict) -> pd.DataFrame:
    """Process a single network: download and merge data."""
    print(f"\n{'='*50}")
    print(f"Processing {name.upper()}")
    print(f"{'='*50}")

    # Download Dune data
    addr_df = download_dune_results(config["query_id"])
    if addr_df.empty:
        return pd.DataFrame()

    # Normalize columns
    if 'day' in addr_df.columns:
        addr_df['date'] = pd.to_datetime(addr_df['day'])
    elif 'date' in addr_df.columns:
        addr_df['date'] = pd.to_datetime(addr_df['date'])

    if 'active_addresses' in addr_df.columns:
        addr_df['users'] = addr_df['active_addresses']

    addr_df = addr_df[['date', 'users']].copy()
    addr_df['date'] = addr_df['date'].dt.tz_localize(None) if addr_df['date'].dt.tz else addr_df['date']
    addr_df['date'] = addr_df['date'].dt.normalize()

    print(f"  Users: {addr_df['date'].min().date()} to {addr_df['date'].max().date()}")

    # Download market cap data
    mcap_df = download_coingecko_history(config["coingecko_id"], config["start_date"])
    if mcap_df.empty:
        return pd.DataFrame()

    mcap_df['date'] = pd.to_datetime(mcap_df['date']).dt.tz_localize(None) if mcap_df['date'].dt.tz is not None else pd.to_datetime(mcap_df['date'])
    mcap_df['date'] = mcap_df['date'].dt.normalize()

    print(f"  Market cap: {mcap_df['date'].min().date()} to {mcap_df['date'].max().date()}")

    # Merge
    df = pd.merge(addr_df, mcap_df, on='date', how='inner')
    df = df.sort_values('date').reset_index(drop=True)

    print(f"  Merged: {len(df)} observations ({df['date'].min().date()} to {df['date'].max().date()})")

    # Save
    output_dir = project_root / "data" / "processed"
    output_file = output_dir / f"{name}_correlated_data.csv"
    df.to_csv(output_file, index=False)
    print(f"  Saved: {output_file.name}")

    return df


def main():
    print("="*50)
    print("Downloading Full Historical Data")
    print("="*50)

    results = {}

    for name, config in QUERIES.items():
        try:
            df = process_network(name, config)
            results[name] = len(df) if not df.empty else 0
        except Exception as e:
            print(f"  ERROR: {e}")
            results[name] = 0

    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    for name, count in results.items():
        old_count = {"livepeer": 365, "uniswap": 365, "thegraph": 365}.get(name, 0)
        improvement = f"(was {old_count})" if count > old_count else ""
        print(f"  {name}: {count} observations {improvement}")

    print("\nNOTE: Chainlink needs a Dune query created first.")
    print("      Use: dune_query_chainlink_active_addresses_nonce5.sql")


if __name__ == "__main__":
    main()
