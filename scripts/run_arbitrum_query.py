#!/usr/bin/env python3
"""
Run Arbitrum active addresses query on Dune and save results.
Usage: python scripts/run_arbitrum_query.py
"""

import os
import sys
import time
import io
from pathlib import Path
import pandas as pd
import requests
from datetime import datetime

# Config
DUNE_API_KEY = os.getenv("DUNE_API_KEY", "N4FR6rr5eSbLKSJTZ2oI74XuWU7N8WyY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "CG-6MtB6MpJvL93fbAXryMW822G")
PROJECT_ROOT = Path(__file__).parent.parent

# Arbitrum config
ARB_START_DATE = "2023-03-23"  # ARB token launch
ARB_COINGECKO_ID = "arbitrum"


def create_and_execute_query(sql: str) -> tuple:
    """Create query on Dune and execute it. Returns (query_id, execution_id)."""
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY, "Content-Type": "application/json"}

    # Create
    print("Creating Dune query...")
    resp = requests.post(
        "https://api.dune.com/api/v1/query",
        headers=headers,
        json={
            "name": f"arbitrum_nonce5_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "query_sql": sql,
            "is_private": False
        },
        timeout=60
    )

    if resp.status_code != 200:
        print(f"Failed to create: {resp.status_code} - {resp.text[:300]}")
        return None, None

    query_id = resp.json().get("query_id")
    print(f"Created query #{query_id}")

    # Execute
    print("Executing query...")
    resp = requests.post(
        f"https://api.dune.com/api/v1/query/{query_id}/execute",
        headers={"X-DUNE-API-KEY": DUNE_API_KEY},
        timeout=60
    )

    if resp.status_code != 200:
        print(f"Failed to execute: {resp.status_code}")
        return query_id, None

    execution_id = resp.json().get("execution_id")
    print(f"Execution ID: {execution_id}")

    return query_id, execution_id


def wait_for_results(execution_id: str, max_minutes: int = 20) -> pd.DataFrame:
    """Poll for query completion and return results."""
    print(f"Waiting for results (up to {max_minutes} minutes)...")

    status_url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"
    headers = {"X-DUNE-API-KEY": DUNE_API_KEY}

    for i in range(max_minutes * 6):  # Check every 10 seconds
        time.sleep(10)
        elapsed = (i + 1) * 10

        resp = requests.get(status_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"[{elapsed}s] Status check failed: {resp.status_code}")
            continue

        state = resp.json().get("state")
        print(f"[{elapsed}s] {state}")

        if state == "QUERY_STATE_COMPLETED":
            # Get CSV results
            results_url = f"https://api.dune.com/api/v1/execution/{execution_id}/results/csv"
            resp = requests.get(results_url, headers=headers, timeout=120)

            if resp.status_code == 200:
                return pd.read_csv(io.StringIO(resp.text))
            else:
                print(f"Failed to get results: {resp.status_code}")
                return pd.DataFrame()

        elif state == "QUERY_STATE_FAILED":
            print("Query failed!")
            print(resp.json())
            return pd.DataFrame()

    print("Timeout!")
    return pd.DataFrame()


def get_market_cap() -> pd.DataFrame:
    """Fetch Arbitrum market cap from CoinGecko."""
    print("\nFetching market cap from CoinGecko...")

    start_ts = int(pd.to_datetime(ARB_START_DATE).timestamp())
    end_ts = int(datetime.now().timestamp())

    # Use pro API
    url = f"https://pro-api.coingecko.com/api/v3/coins/{ARB_COINGECKO_ID}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": start_ts,
        "to": end_ts,
        "x_cg_pro_api_key": COINGECKO_API_KEY
    }

    resp = requests.get(url, params=params, timeout=60)

    if resp.status_code != 200:
        print(f"Failed: {resp.status_code} - {resp.text[:200]}")
        return pd.DataFrame()

    data = resp.json()
    if "market_caps" not in data:
        print("No market cap data")
        return pd.DataFrame()

    df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.normalize()
    df = df.drop_duplicates(subset=["date"], keep="first")

    print(f"Got {len(df)} days of market cap")
    return df[["date", "market_cap"]]


def main():
    print("=" * 60)
    print("ARBITRUM DATA REFRESH")
    print("=" * 60)

    # Read SQL
    sql_file = PROJECT_ROOT / "dune_query_arbitrum_active_addresses_nonce5.sql"
    if not sql_file.exists():
        print(f"SQL file not found: {sql_file}")
        sys.exit(1)

    sql = sql_file.read_text()
    print(f"SQL file: {sql_file.name}")

    # Create and execute
    query_id, execution_id = create_and_execute_query(sql)

    if not execution_id:
        print("Failed to start query")
        sys.exit(1)

    # Wait for results
    addr_df = wait_for_results(execution_id, max_minutes=20)

    if addr_df.empty:
        print("No results returned")
        sys.exit(1)

    # Process
    addr_df["date"] = pd.to_datetime(addr_df["day"]).dt.tz_localize(None).dt.normalize()
    addr_df["users"] = addr_df["active_addresses"]
    addr_df = addr_df[["date", "users"]]

    print(f"\nUser data: {len(addr_df)} rows")
    print(f"Date range: {addr_df['date'].min().date()} to {addr_df['date'].max().date()}")

    # Get market cap
    mcap_df = get_market_cap()

    if mcap_df.empty:
        print("No market cap data")
        sys.exit(1)

    mcap_df["date"] = pd.to_datetime(mcap_df["date"]).dt.tz_localize(None).dt.normalize()

    # Merge
    df = pd.merge(addr_df, mcap_df, on="date", how="inner")
    df = df.sort_values("date").reset_index(drop=True)

    print(f"\nCombined: {len(df)} observations")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Save
    output_file = PROJECT_ROOT / "data" / "processed" / "arbitrum_correlated_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved: {output_file}")

    print("\n" + "=" * 60)
    print("SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    main()
