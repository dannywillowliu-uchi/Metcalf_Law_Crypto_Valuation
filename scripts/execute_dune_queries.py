#!/usr/bin/env python3
"""
Execute Dune queries and collect data for new networks.

This script:
1. Creates new queries on Dune (or uses existing ones)
2. Executes the queries
3. Downloads results
4. Merges with CoinGecko market cap data

Usage:
    python scripts/execute_dune_queries.py
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

# Networks to collect - L2s need fresh data through Dec 2025
NEW_NETWORKS = {
    "arbitrum": {
        "coingecko_id": "arbitrum",
        "symbol": "ARB",
        "category": "l2",
        "start_date": "2021-08-01",
        "sql_file": "dune_query_arbitrum_active_addresses_nonce5.sql",
    },
    "optimism": {
        "coingecko_id": "optimism",
        "symbol": "OP",
        "category": "l2",
        "start_date": "2021-11-01",
        "sql_file": "dune_query_optimism_active_addresses_nonce5.sql",
    },
    "polygon": {
        "coingecko_id": "matic-network",
        "symbol": "MATIC",
        "category": "l2",
        "start_date": "2020-05-01",
        "sql_file": "dune_query_polygon_active_addresses_nonce5.sql",
    },
}


def create_dune_query(name: str, sql: str) -> int:
    """Create a new query on Dune and return the query ID."""
    url = "https://api.dune.com/api/v1/query"
    headers = {
        "X-DUNE-API-KEY": DUNE_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "name": f"{name}_active_addresses_nonce5",
        "query_sql": sql,
        "is_private": False
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code == 200:
        data = response.json()
        query_id = data.get("query_id")
        print(f"  Created query #{query_id}")
        return query_id
    else:
        print(f"  Failed to create query: {response.status_code} - {response.text}")
        return None


def execute_dune_query(query_id: int) -> str:
    """Execute a Dune query and return the execution ID."""
    url = f"https://api.dune.com/api/v1/query/{query_id}/execute"
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY}

    response = requests.post(url, headers=headers, timeout=60)

    if response.status_code == 200:
        data = response.json()
        execution_id = data.get("execution_id")
        print(f"  Execution started: {execution_id}")
        return execution_id
    else:
        print(f"  Failed to execute: {response.status_code} - {response.text}")
        return None


def wait_for_execution(execution_id: str, max_wait: int = 600) -> bool:
    """Wait for a Dune query execution to complete."""
    url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY}

    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            state = data.get("state")

            if state == "QUERY_STATE_COMPLETED":
                print(f"  Execution completed!")
                return True
            elif state == "QUERY_STATE_FAILED":
                print(f"  Execution failed: {data}")
                return False
            else:
                elapsed = int(time.time() - start_time)
                print(f"  Status: {state} (elapsed: {elapsed}s)")
                time.sleep(10)
        else:
            print(f"  Error checking status: {response.status_code}")
            time.sleep(5)

    print(f"  Timeout waiting for execution")
    return False


def get_execution_results(execution_id: str) -> pd.DataFrame:
    """Get results from a completed Dune execution."""
    url = f"https://api.dune.com/api/v1/execution/{execution_id}/results/csv"
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY}

    response = requests.get(url, headers=headers, timeout=120)

    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text))
        return df
    else:
        print(f"  Failed to get results: {response.status_code}")
        return pd.DataFrame()


def get_query_results(query_id: int) -> pd.DataFrame:
    """Get cached results from an existing Dune query."""
    url = f"https://api.dune.com/api/v1/query/{query_id}/results/csv"
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY}

    response = requests.get(url, headers=headers, timeout=120)

    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.text))
        return df
    else:
        return pd.DataFrame()


def get_market_cap_coingecko(coin_id: str, start_date: str) -> pd.DataFrame:
    """Fetch market cap data from CoinGecko."""
    print(f"  Fetching {coin_id} market cap from CoinGecko...")

    cache_dir = project_root / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check cache - look for any existing cache file for this coin
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

    # Fetch from API using range endpoint for full history
    start_ts = int(pd.to_datetime(start_date).timestamp())
    end_ts = int(datetime.now().timestamp())

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": start_ts,
        "to": end_ts,
    }
    if COINGECKO_API_KEY:
        params["x_cg_demo_api_key"] = COINGECKO_API_KEY

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if "market_caps" not in data or not data["market_caps"]:
            print(f"  No market cap data returned")
            return pd.DataFrame()

        df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["date"] = df["date"].dt.normalize()

        # Remove duplicates (keep first of each day)
        df = df.drop_duplicates(subset=["date"], keep="first")
        df = df[["date", "market_cap"]].dropna()

        # Cache result
        end_date = datetime.now().strftime("%Y-%m-%d")
        cache_file = cache_dir / f"market_cap_{coin_id}_{start_date}_{end_date}.csv"
        df.to_csv(cache_file, index=False)
        print(f"  Got {len(df)} days of market cap data")

        return df

    except Exception as e:
        print(f"  Error fetching market cap: {e}")
        return pd.DataFrame()


def process_network(name: str, config: dict) -> pd.DataFrame:
    """Process a single network: execute query, merge with market cap."""
    print(f"\n{'='*60}")
    print(f"Processing {name.upper()}")
    print(f"{'='*60}")

    # Read SQL file
    sql_file = project_root / config["sql_file"]
    if not sql_file.exists():
        print(f"  SQL file not found: {sql_file}")
        return pd.DataFrame()

    sql = sql_file.read_text()

    # Create and execute query on Dune
    print(f"\n1. Creating Dune query...")
    query_id = create_dune_query(name, sql)

    if not query_id:
        print(f"  Failed to create query")
        return pd.DataFrame()

    print(f"\n2. Executing query...")
    execution_id = execute_dune_query(query_id)

    if not execution_id:
        print(f"  Failed to execute query")
        return pd.DataFrame()

    print(f"\n3. Waiting for results...")
    if not wait_for_execution(execution_id, max_wait=600):
        print(f"  Execution did not complete")
        return pd.DataFrame()

    print(f"\n4. Downloading results...")
    addr_df = get_execution_results(execution_id)

    if addr_df.empty:
        print(f"  No results returned")
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

    print(f"  Got {len(addr_df)} days of user data")
    print(f"  Date range: {addr_df['date'].min().date()} to {addr_df['date'].max().date()}")

    # Get market cap data
    print(f"\n5. Getting market cap data...")
    mcap_df = get_market_cap_coingecko(config["coingecko_id"], config["start_date"])

    if mcap_df.empty:
        print(f"  No market cap data")
        return pd.DataFrame()

    mcap_df['date'] = pd.to_datetime(mcap_df['date']).dt.tz_localize(None) if mcap_df['date'].dt.tz is not None else pd.to_datetime(mcap_df['date'])
    mcap_df['date'] = mcap_df['date'].dt.normalize()

    # Merge
    print(f"\n6. Merging data...")
    df = pd.merge(addr_df, mcap_df, on='date', how='inner')
    df = df.sort_values('date').reset_index(drop=True)

    print(f"  Combined: {len(df)} observations")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Save
    output_dir = project_root / "data" / "processed"
    output_file = output_dir / f"{name}_correlated_data.csv"
    df.to_csv(output_file, index=False)
    print(f"  Saved: {output_file.name}")

    # Save query ID for future use
    config_file = project_root / "data" / "cache" / f"{name}_query_id.txt"
    config_file.write_text(str(query_id))

    return df


def main():
    print("="*60)
    print("Dune Query Execution for New Networks")
    print("="*60)
    print(f"\nNetworks to process: {list(NEW_NETWORKS.keys())}")
    print(f"DUNE_API_KEY: {'Set' if DUNE_API_KEY else 'Not set'}")
    print(f"COINGECKO_API_KEY: {'Set' if COINGECKO_API_KEY else 'Not set'}")

    results = {}

    for name, config in NEW_NETWORKS.items():
        try:
            df = process_network(name, config)
            results[name] = len(df) if not df.empty else 0

            # Rate limiting between networks
            time.sleep(2)

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results[name] = 0

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for name, count in results.items():
        status = "OK" if count > 0 else "FAILED"
        print(f"  {name}: {count} observations [{status}]")

    successful = sum(1 for c in results.values() if c > 0)
    print(f"\n  Total: {successful}/{len(results)} networks collected successfully")


if __name__ == "__main__":
    main()
