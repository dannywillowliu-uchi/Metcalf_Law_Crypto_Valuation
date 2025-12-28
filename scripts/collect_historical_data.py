"""
Collect FULL historical data for networks with limited data.

This script executes Dune queries (not just fetches cached results) to get complete history.

Networks to update:
- Chainlink: needs 2017-09 to present (currently only has 1 year)
- Livepeer: needs 2018-04 to present
- Uniswap: needs 2020-05 to present
- The Graph: needs 2020-12 to present

Usage:
    DUNE_API_KEY=xxx COINGECKO_API_KEY=xxx python scripts/collect_historical_data.py
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


# Network configurations with Dune query IDs
# You'll need to create these queries on Dune first using the SQL files
NETWORKS = {
    "chainlink": {
        "coingecko_id": "chainlink",
        "symbol": "LINK",
        "category": "oracle",
        "start_date": "2017-09-01",
        "dune_query_id": None,  # Will be set after creating query
        "sql_file": "dune_query_chainlink_active_addresses_nonce5.sql",
    },
    "livepeer": {
        "coingecko_id": "livepeer",
        "symbol": "LPT",
        "category": "compute",
        "start_date": "2018-04-01",
        "dune_query_id": 6384048,
        "sql_file": "dune_query_livepeer_active_addresses_nonce5.sql",
    },
    "uniswap": {
        "coingecko_id": "uniswap",
        "symbol": "UNI",
        "category": "defi",
        "start_date": "2020-09-17",  # UNI token launch
        "dune_query_id": 6384049,
        "sql_file": "dune_query_uniswap_active_addresses_nonce5.sql",
    },
    "thegraph": {
        "coingecko_id": "the-graph",
        "symbol": "GRT",
        "category": "indexing",
        "start_date": "2020-12-17",
        "dune_query_id": 6384050,
        "sql_file": "dune_query_thegraph_active_addresses_nonce5.sql",
    },
}


def execute_dune_query(query_id: int, api_key: str) -> str:
    """
    Execute a Dune query and return the execution ID.
    """
    url = f"https://api.dune.com/api/v1/query/{query_id}/execute"
    headers = {"X-DUNE-API-KEY": api_key}

    response = requests.post(url, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data.get("execution_id")


def get_execution_status(execution_id: str, api_key: str) -> dict:
    """
    Get the status of a query execution.
    """
    url = f"https://api.dune.com/api/v1/execution/{execution_id}/status"
    headers = {"X-DUNE-API-KEY": api_key}

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return response.json()


def get_execution_results(execution_id: str, api_key: str) -> pd.DataFrame:
    """
    Get results from a completed execution.
    """
    url = f"https://api.dune.com/api/v1/execution/{execution_id}/results/csv"
    headers = {"X-DUNE-API-KEY": api_key}

    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()

    df = pd.read_csv(io.StringIO(response.text))
    return df


def run_dune_query_full(query_id: int, api_key: str, max_wait_minutes: int = 30) -> pd.DataFrame:
    """
    Execute a Dune query and wait for full results.
    """
    print(f"  Executing Dune query #{query_id}...")

    # Start execution
    execution_id = execute_dune_query(query_id, api_key)
    print(f"  Execution ID: {execution_id}")

    # Poll for completion
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_seconds:
            raise TimeoutError(f"Query execution timed out after {max_wait_minutes} minutes")

        status = get_execution_status(execution_id, api_key)
        state = status.get("state", "UNKNOWN")

        if state == "QUERY_STATE_COMPLETED":
            print(f"  Query completed in {elapsed:.0f} seconds")
            break
        elif state in ["QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"]:
            raise RuntimeError(f"Query failed with state: {state}")
        else:
            print(f"  Status: {state} (waiting... {elapsed:.0f}s)")
            time.sleep(10)

    # Fetch results
    print(f"  Fetching results...")
    df = get_execution_results(execution_id, api_key)
    print(f"  Got {len(df)} rows")

    return df


def get_cached_dune_results(query_id: int, api_key: str) -> pd.DataFrame:
    """
    Get cached results from a Dune query (no re-execution).
    """
    url = f"https://api.dune.com/api/v1/query/{query_id}/results/csv"
    headers = {"X-DUNE-API-KEY": api_key}

    response = requests.get(url, headers=headers, timeout=60)

    if response.status_code == 404:
        return pd.DataFrame()

    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    return df


def get_market_cap_coingecko(
    coin_id: str,
    start_date: str,
    end_date: str = None,
    api_key: str = None
) -> pd.DataFrame:
    """
    Fetch market cap data from CoinGecko with full history.
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    cache_dir = project_root / "data" / "cache" / "coingecko_historical"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{coin_id}_{start_date}_{end_date}.csv"

    if cache_file.exists():
        print(f"  Loading {coin_id} from cache...")
        return pd.read_csv(cache_file, parse_dates=["date"])

    print(f"  Fetching {coin_id} market cap from CoinGecko...")

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # Use /market_chart/range endpoint for historical data
    start_unix = int(start_dt.timestamp())
    end_unix = int(end_dt.timestamp())

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": start_unix,
        "to": end_unix,
    }
    if api_key:
        params["x_cg_demo_api_key"] = api_key

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if "market_caps" not in data or not data["market_caps"]:
            print(f"  No market cap data for {coin_id}")
            return pd.DataFrame()

        df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
        prices_df = pd.DataFrame(data.get("prices", []), columns=["timestamp", "price"])
        df = pd.merge(df, prices_df, on="timestamp", how="inner")
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.date
        df["date"] = pd.to_datetime(df["date"])

        # Remove duplicates (keep first of each day)
        df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
        df = df[["date", "market_cap", "price"]]

        df.to_csv(cache_file, index=False)
        print(f"  Cached {len(df)} days of market cap data")

        return df

    except Exception as e:
        print(f"  Error fetching market cap: {e}")
        return pd.DataFrame()


def collect_network_historical(
    network_name: str,
    config: dict,
    dune_api_key: str,
    coingecko_api_key: str = None,
    force_execute: bool = False
) -> pd.DataFrame:
    """
    Collect complete historical data for a network.
    """
    print(f"\n{'='*60}")
    print(f"Collecting historical data for {network_name.upper()}")
    print(f"{'='*60}")

    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get active addresses from Dune
    print(f"\n1. Active Addresses (Dune):")
    query_id = config.get("dune_query_id")

    if not query_id:
        print(f"  No query ID set. Create query on Dune using:")
        print(f"  {config['sql_file']}")
        return pd.DataFrame()

    if force_execute:
        addr_df = run_dune_query_full(query_id, dune_api_key)
    else:
        # Try cached first
        addr_df = get_cached_dune_results(query_id, dune_api_key)
        if addr_df.empty or len(addr_df) < 500:
            print(f"  Cached results insufficient ({len(addr_df)} rows), executing fresh...")
            addr_df = run_dune_query_full(query_id, dune_api_key)

    if addr_df.empty:
        print(f"  No address data available")
        return pd.DataFrame()

    # Normalize column names
    date_col = None
    addr_col = None
    for col in addr_df.columns:
        col_lower = str(col).lower()
        if "day" in col_lower or "date" in col_lower:
            date_col = col
        if "address" in col_lower or "active" in col_lower:
            addr_col = col

    if date_col and addr_col:
        addr_df = addr_df.rename(columns={date_col: "date", addr_col: "active_addresses"})

    addr_df["date"] = pd.to_datetime(addr_df["date"])
    if addr_df["date"].dt.tz is not None:
        addr_df["date"] = addr_df["date"].dt.tz_localize(None)

    print(f"  Got {len(addr_df)} days: {addr_df['date'].min().date()} to {addr_df['date'].max().date()}")

    # Get market cap from CoinGecko
    print(f"\n2. Market Cap (CoinGecko):")
    mcap_df = get_market_cap_coingecko(
        config["coingecko_id"],
        config["start_date"],
        api_key=coingecko_api_key
    )

    if mcap_df.empty:
        print(f"  No market cap data")
        return pd.DataFrame()

    print(f"  Got {len(mcap_df)} days: {mcap_df['date'].min().date()} to {mcap_df['date'].max().date()}")

    # Merge
    print(f"\n3. Merging:")
    df = pd.merge(
        addr_df[["date", "active_addresses"]],
        mcap_df[["date", "market_cap"]],
        on="date",
        how="inner"
    )

    df = df.rename(columns={"active_addresses": "users"})
    df = df.sort_values("date").reset_index(drop=True)

    print(f"  Combined: {len(df)} observations")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Save
    output_file = output_dir / f"{network_name}_correlated_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\n  Saved: {output_file}")

    return df


def main():
    print("="*60)
    print("Historical Data Collection")
    print("="*60)

    dune_api_key = os.getenv("DUNE_API_KEY")
    coingecko_api_key = os.getenv("COINGECKO_API_KEY")

    if not dune_api_key:
        print("ERROR: DUNE_API_KEY required")
        print("Usage: DUNE_API_KEY=xxx python scripts/collect_historical_data.py")
        sys.exit(1)

    print(f"\nAPI Keys:")
    print(f"  DUNE_API_KEY: Set")
    print(f"  COINGECKO_API_KEY: {'Set' if coingecko_api_key else 'Not set (free tier)'}")

    # Collect data for each network
    results = {}

    for network_name, config in NETWORKS.items():
        try:
            df = collect_network_historical(
                network_name,
                config,
                dune_api_key,
                coingecko_api_key,
                force_execute=True  # Always execute fresh for full history
            )
            results[network_name] = len(df) if not df.empty else 0
        except Exception as e:
            print(f"\nError collecting {network_name}: {e}")
            results[network_name] = 0

    # Summary
    print("\n" + "="*60)
    print("Collection Summary")
    print("="*60)

    for network, count in results.items():
        status = f"{count} observations" if count > 0 else "FAILED"
        print(f"  {network}: {status}")


if __name__ == "__main__":
    main()
