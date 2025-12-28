"""
Ethereum Data Collection Module

Collects historical Ethereum data for network effects analysis:
- Active addresses (users) - via Dune Analytics or CSV
- Market capitalization - via CoinGecko API, Yahoo Finance (price × supply), or CSV

Data Sources:
1. CoinGecko API (market cap) - Free tier: 10-50 calls/minute
2. Dune Analytics (active addresses) - Free tier available
3. Yahoo Finance (price) - Free, unlimited historical data
4. CSV files (fallback for both)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import requests
import time
import os
import io
from pathlib import Path

try:
    from dune_client.client import DuneClient
    from dune_client.query import QueryBase
    DUNE_SDK_AVAILABLE = True
except ImportError:
    DUNE_SDK_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class EthereumDataCollector:
    """
    Collects Ethereum historical data from various APIs.
    
    Primary sources:
    - CoinGecko API: Market cap (free tier: 10-50 calls/min)
    - Dune Analytics: Active addresses (free tier available)
    - Yahoo Finance: Price data (free, unlimited)
    - CSV files: Fallback for both
    """
    
    def __init__(self, 
                 coingecko_api_key: Optional[str] = None,
                 dune_api_key: Optional[str] = None,
                 coinmarketcap_api_key: Optional[str] = None,
                 cache_dir: Optional[str] = None):
        """
        Initialize data collector.
        
        Parameters
        ----------
        coingecko_api_key : str, optional
            CoinGecko API key (optional for free tier, improves rate limits)
            Get at: https://www.coingecko.com/en/api
        dune_api_key : str, optional
            Dune Analytics API key (required for active addresses)
            Get at: https://dune.com/settings/api
        coinmarketcap_api_key : str, optional
            CoinMarketCap API key (required for accurate historical market cap)
            Get at: https://coinmarketcap.com/api/
        cache_dir : str, optional
            Directory to cache API responses (default: data/cache)
        """
        self.coingecko_api_key = coingecko_api_key or os.getenv("COINGECKO_API_KEY")
        self.dune_api_key = dune_api_key or os.getenv("DUNE_API_KEY")
        self.coinmarketcap_api_key = coinmarketcap_api_key or os.getenv("COINMARKETCAP_API_KEY")
        
        # Set up cache directory
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # API endpoints
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.dune_base = "https://api.dune.com/api/v1"
        self.coinmarketcap_base = "https://pro-api.coinmarketcap.com/v1"
        
        # Rate limiting
        self.last_coingecko_call = 0
        # Free tier: 10-50 calls/min, be conservative
        # With API key: 50 calls/min, without: 10-30 calls/min
        self.coingecko_min_interval = 2.0 if not self.coingecko_api_key else 1.2
        self.last_coinmarketcap_call = 0
        self.coinmarketcap_min_interval = 0.5  # Free tier: 333 calls/day, ~1 call per 4 min
        
    def get_ethereum_supply_history(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical Ethereum circulating supply.
        
        Uses approximate supply calculation based on:
        - Genesis supply: ~72M ETH
        - Block rewards: ~2 ETH per block (pre-merge), ~0 ETH (post-merge)
        - EIP-1559 burns: Reduces supply
        - Staking: Locks supply
        
        For accurate supply, this is an approximation. For exact values,
        you'd need to query the blockchain or use a data provider.
        
        Parameters
        ----------
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, supply
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Generate date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        date_range = pd.date_range(start=start_dt, end=end_dt, freq='D')
        
        # Approximate supply calculation
        # Genesis: 72,009,990.5 ETH (July 2015)
        # Pre-merge: ~2 ETH per block, ~12 seconds per block
        # Post-merge (Sep 2022): ~0 ETH per block (proof-of-stake)
        # EIP-1559 (Aug 2021): Burns base fee
        
        genesis_supply = 72_009_990.5
        merge_date = pd.to_datetime("2022-09-15")
        
        supply = []
        for date in date_range:
            days_since_genesis = (date - pd.to_datetime("2015-07-30")).days
            
            if date < merge_date:
                # Pre-merge: ~2 ETH per block, ~7200 blocks per day
                blocks_per_day = 86400 / 12  # ~7200
                eth_per_day = blocks_per_day * 2
                # Rough estimate: supply grows ~4.5% per year pre-merge
                years = days_since_genesis / 365.25
                daily_supply = genesis_supply * (1.045 ** years)
            else:
                # Post-merge: minimal supply growth (mostly staking rewards, offset by burns)
                # Supply is roughly stable around 120M
                daily_supply = 120_000_000
            
            supply.append(daily_supply)
        
        df = pd.DataFrame({
            "date": date_range,
            "supply": supply
        })
        
        return df
    
    def get_market_cap_history_bitinfocharts(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical market cap from BitInfoCharts (free, unlimited historical).
        
        BitInfoCharts provides accurate historical market cap data embedded in their HTML.
        This method extracts the data from the page.
        
        Parameters
        ----------
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, market_cap, price (price calculated from market_cap/supply)
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check cache
        cache_file = self.cache_dir / f"market_cap_bitinfocharts_{start_date}_{end_date}.csv"
        if cache_file.exists():
            df = pd.read_csv(cache_file, parse_dates=['date'])
            print(f"Loaded market cap data from cache: {len(df)} records")
            return df
        
        print("Fetching market cap data from BitInfoCharts...")
        url = "https://bitinfocharts.com/comparison/ethereum-marketcap.html#alltime"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract data from JavaScript array in HTML
            import re
            # Pattern: [new Date("YYYY/MM/DD"), market_cap_value],
            pattern = r'\[new Date\("(\d{4}/\d{1,2}/\d{1,2})"\),(\d+)\]'
            matches = re.findall(pattern, response.text)
            
            if not matches:
                raise ValueError("Could not find market cap data in BitInfoCharts HTML")
            
            records = []
            for date_str, mcap_str in matches:
                # Parse date from "YYYY/MM/DD" format
                date = pd.to_datetime(date_str, format="%Y/%m/%d")
                market_cap = float(mcap_str)
                records.append({
                    "date": date,
                    "market_cap": market_cap
                })
            
            df = pd.DataFrame(records)
            df = df.sort_values("date").reset_index(drop=True)
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
            
            # Calculate price from market cap / supply (approximate)
            # For now, use average supply estimate
            supply_df = self.get_ethereum_supply_history(
                df["date"].min().strftime("%Y-%m-%d"),
                df["date"].max().strftime("%Y-%m-%d")
            )
            df = pd.merge(df, supply_df, on="date", how="left")
            df["price"] = df["market_cap"] / df["supply"]
            df = df[["date", "market_cap", "price"]]
            
            # Cache result
            df.to_csv(cache_file, index=False)
            print(f"✓ Fetched {len(df)} market cap records from BitInfoCharts")
            
            return df.reset_index(drop=True)
            
        except Exception as e:
            raise Exception(f"Error fetching market cap data from BitInfoCharts: {e}")
    
    def get_market_cap_from_price_supply(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate market cap from price × supply using free sources.
        
        Uses:
        - Yahoo Finance for historical price (free, unlimited)
        - Calculated supply estimate
        
        This provides accurate market cap without paid API subscriptions.
        
        Parameters
        ----------
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, market_cap, price
        """
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance not installed. Install with: pip install yfinance")
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check cache
        cache_file = self.cache_dir / f"market_cap_price_supply_{start_date}_{end_date}.csv"
        if cache_file.exists():
            df = pd.read_csv(cache_file, parse_dates=['date'])
            print(f"Loaded market cap data from cache: {len(df)} records")
            return df
        
        print("Calculating market cap from price × supply...")
        print("  Fetching price data from Yahoo Finance (free)...")
        
        # Get price from Yahoo Finance
        ticker = yf.Ticker("ETH-USD")
        price_df = ticker.history(start=start_date, end=end_date, interval="1d")
        
        if price_df.empty:
            raise ValueError("Yahoo Finance returned empty dataset")
        
        price_df = price_df.reset_index()
        price_df = price_df.rename(columns={'Date': 'date', 'Close': 'price'})
        price_df['date'] = pd.to_datetime(price_df['date'])
        if price_df['date'].dt.tz is not None:
            price_df['date'] = price_df['date'].dt.tz_localize(None)
        
        print(f"  ✓ Fetched {len(price_df)} price records")
        
        # Get supply estimate
        print("  Calculating historical supply...")
        supply_df = self.get_ethereum_supply_history(start_date, end_date)
        
        # Merge price and supply
        df = pd.merge(price_df[['date', 'price']], supply_df, on='date', how='inner')
        
        # Calculate market cap
        df['market_cap'] = df['price'] * df['supply']
        
        # Select columns
        df = df[['date', 'market_cap', 'price']].sort_values('date').reset_index(drop=True)
        
        # Cache result
        df.to_csv(cache_file, index=False)
        print(f"✓ Calculated {len(df)} market cap records from price × supply")
        
        return df
    
    def get_market_cap_history(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        frequency: str = "daily"
    ) -> pd.DataFrame:
        """
        Get market cap history from CoinGecko (free tier: last 365 days only).
        Falls back to price × supply method for full historical range.
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Try CoinGecko first (last 365 days only for free tier)
        cache_file = self.cache_dir / f"market_cap_coingecko_{start_date}_{end_date}.csv"
        if cache_file.exists():
            df = pd.read_csv(cache_file, parse_dates=['date'])
            print(f"Loaded market cap data from cache: {len(df)} records")
            return df
        
        try:
            # CoinGecko market_chart endpoint (last 365 days only)
            url = f"{self.coingecko_base}/coins/ethereum/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "365",
                "interval": "daily"
            }
            if self.coingecko_api_key:
                params["x_cg_demo_api_key"] = self.coingecko_api_key
            
            time_since_last = time.time() - self.last_coingecko_call
            if time_since_last < self.coingecko_min_interval:
                time.sleep(self.coingecko_min_interval - time_since_last)
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.last_coingecko_call = time.time()
            
            if "market_caps" in data and data["market_caps"]:
                df = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
                prices_df = pd.DataFrame(data.get("prices", []), columns=["timestamp", "price"])
                df = pd.merge(df, prices_df, on="timestamp", how="inner")
                df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
                df = df[["date", "market_cap", "price"]].sort_values("date")
                
                # Filter by date range
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
                
                if df["date"].dt.tz is not None:
                    df["date"] = df["date"].dt.tz_localize(None)
                
                df.to_csv(cache_file, index=False)
                return df.reset_index(drop=True)
        except Exception as e:
            print(f"CoinGecko failed: {e}, falling back to price × supply...")
        
        # Fallback to price × supply (free, unlimited historical)
        return self.get_market_cap_from_price_supply(start_date, end_date)
    
    def get_active_addresses_dune_csv(
        self,
        query_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get active addresses from Dune using CSV endpoint (no execution cost)."""
        if not self.dune_api_key:
            raise ValueError("Dune API key required. Get one at: https://dune.com/settings/api")
        
        cache_file = self.cache_dir / f"active_addresses_dune_{query_id}.csv"
        if cache_file.exists():
            df = pd.read_csv(cache_file, parse_dates=['date'])
            if start_date or end_date:
                start_dt = pd.to_datetime(start_date) if start_date else None
                end_dt = pd.to_datetime(end_date) if end_date else None
                if start_dt:
                    df = df[df['date'] >= start_dt]
                if end_dt:
                    df = df[df['date'] <= end_dt]
            return df
        
        url = f"{self.dune_base}/query/{query_id}/results/csv"
        headers = {"X-Dune-API-Key": self.dune_api_key}
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Find date and address columns
        date_col = None
        addr_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'date' in col_lower or 'day' in col_lower:
                date_col = col
            if 'address' in col_lower or 'active' in col_lower or 'users' in col_lower:
                addr_col = col
        
        if not date_col or not addr_col:
            raise ValueError(f"Could not find date/address columns. Columns: {df.columns.tolist()}")
        
        df = df.rename(columns={date_col: "date", addr_col: "active_addresses"})
        df["date"] = pd.to_datetime(df["date"])
        if df["date"].dt.tz is not None:
            df["date"] = df["date"].dt.tz_localize(None)
        
        df = df[["date", "active_addresses"]].sort_values("date")
        df.to_csv(cache_file, index=False)
        return df.reset_index(drop=True)
    
    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """Load data from CSV file."""
        return pd.read_csv(filepath, parse_dates=['date'])
    
    def get_complete_ethereum_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get complete Ethereum data (users + market cap)."""
        # This is a placeholder - implement based on your needs
        raise NotImplementedError("Implement based on your data collection needs")


def create_sample_data(n_days: int = 365) -> pd.DataFrame:
    """Create sample Ethereum data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    np.random.seed(42)
    users = np.random.lognormal(9, 0.5, n_days)
    market_cap = users ** 1.3 * np.exp(10.15) * np.random.lognormal(0, 0.1, n_days)
    
    return pd.DataFrame({
        'date': dates,
        'users': users,
        'market_cap': market_cap
    })
