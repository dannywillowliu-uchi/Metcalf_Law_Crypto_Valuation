#!/usr/bin/env python3
"""
Refresh L2 data (Arbitrum, Optimism, Polygon) through Dec 2025.
Creates queries, executes them, and merges with market cap data.
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

DUNE_API_KEY = os.getenv("DUNE_API_KEY", "N4FR6rr5eSbLKSJTZ2oI74XuWU7N8WyY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "CG-6MtB6MpJvL93fbAXryMW822G")

# Only L2s that need refresh
L2_NETWORKS = {
    "arbitrum": {
        "coingecko_id": "arbitrum",
        "start_date": "2023-03-23",  # ARB token launch
        "sql_file": "dune_query_arbitrum_active_addresses_nonce5.sql",
    },
    "optimism": {
        "coingecko_id": "optimism",
        "start_date": "2022-05-31",  # OP token launch
        "sql_file": "dune_query_optimism_active_addresses_nonce5.sql",
    },
    "polygon": {
        "coingecko_id": "matic-network",
        "start_date": "2021-08-01",
        "sql_file": "dune_query_polygon_active_addresses_nonce5.sql",
    },
}


def create_and_execute_query(name: str, sql: str) -> pd.DataFrame:
    """Create query, execute it, wait for results, return DataFrame."""
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY, "Content-Type": "application/json"}

    # 1. Create query
    print(f"  Creating query...")
    create_url = "https://api.dune.com/api/v1/query"
    payload = {
        "name": f"{name}_active_addresses_nonce5_{datetime.now().strftime('%Y%m%d')}",
        "query_sql": sql,
        "is_private": False
    }
    resp = requests.post(create_url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        print(f"  Failed to create: {resp.status_code} - {resp.text[:200]}")
        return pd.DataFrame()

    query_id = resp.json().get("query_id")
    print(f"  Created query #{query_id}")

    # 2. Execute query
    print(f"  Executing query...")
    exec_url = f"https://api.dune.com/api/v1/query/{query_id}/execute"
    resp = requests.post(exec_url, headers={"X-DUNE-API-KEY": DUNE_API_KEY}, timeout=60)
    if resp.status_code != 200:
        print(f"  Failed to execute: {resp.status_code}")
        return pd.DataFrame()

    execution_id = resp.json().get("execution_id")
    print(f"  Execution ID: {execution_id}")

    # 3. Wait for completion
    print(f"  Waiting for results", end="", flush=True)
    status_url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"

    for _ in range(60):  # Max 10 minutes
        time.sleep(10)
        print(".", end="", flush=True)

        resp = requests.get(status_url, headers={"X-DUNE-API-KEY": DUNE_API_KEY}, timeout=30)
        if resp.status_code == 200:
            state = resp.json().get("state")
            if state == "QUERY_STATE_COMPLETED":
                print(" Done!")
                break
            elif state == "QUERY_STATE_FAILED":
                print(f" Failed!")
                return pd.DataFrame()
    else:
        print(" Timeout!")
        return pd.DataFrame()

    # 4. Get results
    print(f"  Downloading results...")
    results_url = f"https://api.dune.com/api/v1/execution/{execution_id}/results/csv"
    resp = requests.get(results_url, headers={"X-DUNE-API-KEY": DUNE_API_KEY}, timeout=120)

    if resp.status_code != 200:
        print(f"  Failed to get results: {resp.status_code}")
        return pd.DataFrame()

    df = pd.read_csv(io.StringIO(resp.text))
    print(f"  Got {len(df)} rows")
    return df


def get_market_cap(coin_id: str, start_date: str) -> pd.DataFrame:
    """Fetch market cap from CoinGecko."""
    print(f"  Fetching market cap for {coin_id}...")

    start_ts = int(pd.to_datetime(start_date).timestamp())
    end_ts = int(datetime.now().timestamp())

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {"vs_currency": "usd", "from": start_ts, "to": end_ts}
    if COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_API_KEY

    resp = requests.get(url, params=params, timeout=60)
    if resp.status_code != 200:
        print(f"  Failed: {resp.status_code}")
        return pd.DataFrame()

    data = resp.json()
    if "market_caps" not in data:
        return pd.DataFrame()

    df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.normalize()
    df = df.drop_duplicates(subset=["date"], keep="first")

    print(f"  Got {len(df)} days of market cap")
    return df[["date", "market_cap"]]


def process_network(name: str, config: dict) -> bool:
    """Process a single L2 network."""
    print(f"\n{'='*60}")
    print(f"Processing {name.upper()}")
    print(f"{'='*60}")

    # Read SQL
    sql_file = project_root / config["sql_file"]
    if not sql_file.exists():
        print(f"  SQL file not found: {sql_file}")
        return False

    sql = sql_file.read_text()

    # Execute query
    addr_df = create_and_execute_query(name, sql)
    if addr_df.empty:
        return False

    # Normalize columns
    if 'day' in addr_df.columns:
        addr_df['date'] = pd.to_datetime(addr_df['day']).dt.tz_localize(None).dt.normalize()
    addr_df['users'] = addr_df['active_addresses']
    addr_df = addr_df[['date', 'users']]

    print(f"  Users: {addr_df['date'].min().date()} to {addr_df['date'].max().date()}")

    # Get market cap
    mcap_df = get_market_cap(config["coingecko_id"], config["start_date"])
    if mcap_df.empty:
        return False

    mcap_df['date'] = pd.to_datetime(mcap_df['date']).dt.tz_localize(None).dt.normalize()

    # Merge
    df = pd.merge(addr_df, mcap_df, on='date', how='inner')
    df = df.sort_values('date').reset_index(drop=True)

    print(f"  Combined: {len(df)} observations")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Save
    output_file = project_root / "data" / "processed" / f"{name}_correlated_data.csv"
    df.to_csv(output_file, index=False)
    print(f"  Saved: {output_file}")

    return True


def main():
    print("="*60)
    print("Refreshing L2 Data (Arbitrum, Optimism, Polygon)")
    print("="*60)

    results = {}
    for name, config in L2_NETWORKS.items():
        try:
            results[name] = process_network(name, config)
            time.sleep(2)  # Rate limiting
        except Exception as e:
            print(f"  ERROR: {e}")
            results[name] = False

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")


if __name__ == "__main__":
    main()
