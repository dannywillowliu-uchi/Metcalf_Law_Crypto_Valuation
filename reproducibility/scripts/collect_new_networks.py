"""
Collect data for new networks: Livepeer, Uniswap, The Graph

This script collects:
1. Active addresses from Dune Analytics (requires API key and query execution)
2. Market cap data from CoinGecko

Usage:
    python scripts/collect_new_networks.py

Before running:
1. Create queries on Dune using the SQL files in the project root:
   - dune_query_livepeer_active_addresses_nonce5.sql
   - dune_query_uniswap_active_addresses_nonce5.sql
   - dune_query_thegraph_active_addresses_nonce5.sql
2. Execute the queries on Dune (costs credits)
3. Set DUNE_API_KEY and COINGECKO_API_KEY environment variables
4. Run this script
"""

import os
import sys
from pathlib import Path
import pandas as pd
import requests
import time
from datetime import datetime
import io

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


# Network configurations
NETWORKS = {
    "livepeer": {
        "coingecko_id": "livepeer",
        "symbol": "LPT",
        "category": "compute",
        "start_date": "2018-04-01",
        "dune_query_id": 6384048,
    },
    "uniswap": {
        "coingecko_id": "uniswap",
        "symbol": "UNI",
        "category": "defi",
        "start_date": "2020-09-17",  # UNI token launch
        "dune_query_id": 6384049,
    },
    "thegraph": {
        "coingecko_id": "the-graph",
        "symbol": "GRT",
        "category": "indexing",
        "start_date": "2020-12-17",
        "dune_query_id": 6384050,
    }
}


def get_market_cap_coingecko(
    coin_id: str,
    start_date: str,
    end_date: str = None,
    cache_dir: Path = None
) -> pd.DataFrame:
    """
    Fetch market cap data from CoinGecko.

    Parameters
    ----------
    coin_id : str
        CoinGecko coin ID
    start_date : str
        Start date in YYYY-MM-DD format
    end_date : str, optional
        End date in YYYY-MM-DD format
    cache_dir : Path, optional
        Directory to cache results

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: date, market_cap, price
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    if cache_dir is None:
        cache_dir = project_root / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / f"market_cap_{coin_id}_{start_date}_{end_date}.csv"
    if cache_file.exists():
        print(f"  Loading {coin_id} market cap from cache...")
        return pd.read_csv(cache_file, parse_dates=["date"])

    print(f"  Fetching {coin_id} market cap from CoinGecko...")

    # Calculate days between dates
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    days = (end_dt - start_dt).days + 1

    # CoinGecko free tier: max 365 days per request
    # For longer periods, we need multiple requests
    api_key = os.getenv("COINGECKO_API_KEY", "")

    all_data = []

    # Chunk into 365-day periods
    current_start = start_dt
    while current_start < end_dt:
        chunk_end = min(current_start + pd.Timedelta(days=364), end_dt)
        chunk_days = (chunk_end - current_start).days + 1

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": str(chunk_days),
            "interval": "daily"
        }
        if api_key:
            params["x_cg_demo_api_key"] = api_key

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "market_caps" in data and data["market_caps"]:
                df_chunk = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
                prices_df = pd.DataFrame(data.get("prices", []), columns=["timestamp", "price"])
                df_chunk = pd.merge(df_chunk, prices_df, on="timestamp", how="inner")
                df_chunk["date"] = pd.to_datetime(df_chunk["timestamp"], unit="ms")
                all_data.append(df_chunk[["date", "market_cap", "price"]])

                print(f"    Fetched {len(df_chunk)} days ending {chunk_end.strftime('%Y-%m-%d')}")

            # Rate limiting
            time.sleep(1.5)

        except Exception as e:
            print(f"    Error fetching chunk: {e}")

        current_start = chunk_end + pd.Timedelta(days=1)

    if not all_data:
        print(f"    No data fetched for {coin_id}")
        return pd.DataFrame()

    df = pd.concat(all_data, ignore_index=True)
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    # Filter by date range
    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]

    # Remove timezone if present
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_localize(None)

    # Cache result
    df.to_csv(cache_file, index=False)
    print(f"    Cached {len(df)} records")

    return df


def get_active_addresses_dune(
    query_id: int,
    cache_dir: Path = None
) -> pd.DataFrame:
    """
    Fetch active addresses from Dune Analytics.

    Parameters
    ----------
    query_id : int
        Dune query ID
    cache_dir : Path, optional
        Directory to cache results

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: date, active_addresses
    """
    api_key = os.getenv("DUNE_API_KEY")
    if not api_key:
        raise ValueError("DUNE_API_KEY environment variable required")

    if cache_dir is None:
        cache_dir = project_root / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / f"active_addresses_dune_{query_id}.csv"
    if cache_file.exists():
        print(f"  Loading query #{query_id} results from cache...")
        return pd.read_csv(cache_file, parse_dates=["date"])

    print(f"  Fetching query #{query_id} results from Dune...")

    url = f"https://api.dune.com/api/v1/query/{query_id}/results/csv"
    headers = {"X-DUNE-API-KEY": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=60)

        if response.status_code == 404:
            print(f"    Query #{query_id} results not found. Execute the query on Dune first.")
            return pd.DataFrame()

        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text))

        # Find date and address columns
        date_col = None
        addr_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if "date" in col_lower or "day" in col_lower:
                date_col = col
            if "address" in col_lower or "active" in col_lower:
                addr_col = col

        if not date_col or not addr_col:
            print(f"    Could not find date/address columns. Columns: {df.columns.tolist()}")
            return pd.DataFrame()

        df = df.rename(columns={date_col: "date", addr_col: "active_addresses"})
        df["date"] = pd.to_datetime(df["date"])
        if df["date"].dt.tz is not None:
            df["date"] = df["date"].dt.tz_localize(None)

        df = df[["date", "active_addresses"]].sort_values("date").reset_index(drop=True)

        # Cache result
        df.to_csv(cache_file, index=False)
        print(f"    Cached {len(df)} records")

        return df

    except Exception as e:
        print(f"    Error fetching from Dune: {e}")
        return pd.DataFrame()


def collect_network_data(
    network_name: str,
    config: dict,
    output_dir: Path = None
) -> pd.DataFrame:
    """
    Collect complete data for a network.

    Parameters
    ----------
    network_name : str
        Network name
    config : dict
        Network configuration
    output_dir : Path, optional
        Directory to save output

    Returns
    -------
    pd.DataFrame
        Combined DataFrame with date, users, market_cap
    """
    print(f"\n{'='*60}")
    print(f"Collecting data for {network_name.upper()}")
    print(f"{'='*60}")

    if output_dir is None:
        output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get market cap data
    print(f"\n1. Market Cap Data:")
    mcap_df = get_market_cap_coingecko(
        config["coingecko_id"],
        config["start_date"]
    )

    if mcap_df.empty:
        print(f"   No market cap data available")
        return pd.DataFrame()

    print(f"   Got {len(mcap_df)} days of market cap data")

    # Get active addresses (if query ID is set)
    print(f"\n2. Active Addresses Data:")
    if config.get("dune_query_id"):
        addr_df = get_active_addresses_dune(config["dune_query_id"])
    else:
        print(f"   Dune query ID not set - skipping")
        print(f"   To collect active addresses:")
        print(f"   1. Create query on Dune using: dune_query_{network_name}_active_addresses_nonce5.sql")
        print(f"   2. Execute the query")
        print(f"   3. Update NETWORKS config with query ID")
        addr_df = pd.DataFrame()

    # If we don't have address data, just save market cap for now
    if addr_df.empty:
        output_file = output_dir / f"{network_name}_market_cap_only.csv"
        mcap_df.to_csv(output_file, index=False)
        print(f"\n   Saved market cap only: {output_file.name}")
        return mcap_df

    # Merge data
    print(f"\n3. Merging Data:")
    df = pd.merge(
        addr_df,
        mcap_df,
        on="date",
        how="inner"
    )

    # Rename columns to standard format
    df = df.rename(columns={
        "active_addresses": "users",
        "market_cap": "market_cap"
    })

    df = df[["date", "users", "market_cap"]].sort_values("date").reset_index(drop=True)

    print(f"   Combined: {len(df)} observations")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Users range: {df['users'].min():,.0f} to {df['users'].max():,.0f}")
    print(f"   Market cap range: ${df['market_cap'].min()/1e9:.2f}B to ${df['market_cap'].max()/1e9:.2f}B")

    # Save output
    output_file = output_dir / f"{network_name}_correlated_data.csv"
    df.to_csv(output_file, index=False)
    print(f"\n   Saved: {output_file.name}")

    return df


def main():
    """Main function to collect all network data."""
    print("="*60)
    print("Network Effects Data Collection")
    print("="*60)
    print(f"\nNetworks to collect: {list(NETWORKS.keys())}")

    # Check environment variables
    dune_key = os.getenv("DUNE_API_KEY")
    coingecko_key = os.getenv("COINGECKO_API_KEY")

    print(f"\nAPI Keys:")
    print(f"  DUNE_API_KEY: {'Set' if dune_key else 'Not set'}")
    print(f"  COINGECKO_API_KEY: {'Set' if coingecko_key else 'Not set (using free tier)'}")

    if not dune_key:
        print("\nWarning: DUNE_API_KEY not set. Cannot fetch active addresses.")
        print("Will collect market cap data only.")

    results = {}

    for network_name, config in NETWORKS.items():
        try:
            df = collect_network_data(network_name, config)
            results[network_name] = df
        except Exception as e:
            print(f"\nError collecting {network_name}: {e}")
            results[network_name] = pd.DataFrame()

    # Summary
    print("\n" + "="*60)
    print("Collection Summary")
    print("="*60)

    for network_name, df in results.items():
        if df.empty:
            print(f"  {network_name}: No data collected")
        else:
            print(f"  {network_name}: {len(df)} observations")

    print("\nNext steps:")
    print("1. Create Dune queries using the SQL files in the project root")
    print("2. Execute the queries on Dune")
    print("3. Update the NETWORKS config with query IDs")
    print("4. Re-run this script to fetch active addresses")
    print("5. Run analysis: python scripts/run_analysis.py")


if __name__ == "__main__":
    main()
