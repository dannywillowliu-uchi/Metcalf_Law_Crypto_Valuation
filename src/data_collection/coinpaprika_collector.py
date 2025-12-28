"""
CoinPaprika Data Collector

CoinPaprika provides free API access with historical data.
Free tier: 10,000 credits/month (1 credit per call)
"""

import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
import requests
import time
from pathlib import Path


class CoinPaprikaCollector:
    """Collect historical market cap data from CoinPaprika API"""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize CoinPaprika collector.
        
        Parameters
        ----------
        api_key : str, optional
            CoinPaprika API key (optional for free tier)
            Get at: https://coinpaprika.com/api/
        cache_dir : str, optional
            Directory to cache API responses
        """
        self.api_key = api_key
        self.base_url = "https://api.coinpaprika.com/v1"
        
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting (free tier: 10k credits/month)
        self.last_call = 0
        self.min_interval = 0.1  # 10 calls/second max
    
    def get_ethereum_market_cap_history(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get Ethereum historical market cap from CoinPaprika.
        
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
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Check cache
        cache_file = self.cache_dir / f"market_cap_coinpaprika_{start_date}_{end_date}.csv"
        if cache_file.exists():
            df = pd.read_csv(cache_file, parse_dates=['date'])
            print(f"Loaded market cap data from cache: {len(df)} records")
            return df
        
        # CoinPaprika uses coin ID: eth-ethereum
        # Use OHLCV endpoint for historical data
        coin_id = "eth-ethereum"
        
        # Convert dates to timestamps
        start_ts = int(pd.to_datetime(start_date).timestamp())
        end_ts = int(pd.to_datetime(end_date).timestamp())
        
        url = f"{self.base_url}/coins/{coin_id}/ohlcv/historical"
        params = {
            "start": start_ts,
            "end": end_ts,
            "quote": "usd"
        }
        
        if self.api_key:
            headers = {"Authorization": f"Bearer {self.api_key}"}
        else:
            headers = {}
        
        # Rate limiting
        time_since_last = time.time() - self.last_call
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self.last_call = time.time()
            
            if not data:
                raise ValueError("CoinPaprika returned empty dataset")
            
            # Parse OHLCV data
            # Format: [{"time_open": "2018-11-02T00:00:00Z", "time_close": "...", "open": ..., "high": ..., "low": ..., "close": ..., "volume": ..., "market_cap": ...}, ...]
            records = []
            for item in data:
                date = pd.to_datetime(item.get("time_open", item.get("time_close")))
                market_cap = item.get("market_cap")
                price = item.get("close")  # Use close price
                
                if market_cap is not None and price is not None:
                    records.append({
                        "date": date,
                        "market_cap": market_cap,
                        "price": price
                    })
            
            if not records:
                raise ValueError("No market cap data found in CoinPaprika response")
            
            df = pd.DataFrame(records)
            df = df.sort_values("date").reset_index(drop=True)
            
            # Filter by date range
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)]
            
            # Normalize timezone
            if df["date"].dt.tz is not None:
                df["date"] = df["date"].dt.tz_localize(None)
            
            # Cache result
            df.to_csv(cache_file, index=False)
            print(f"Fetched {len(df)} records from CoinPaprika API")
            
            return df.reset_index(drop=True)
            
        except Exception as e:
            raise Exception(f"Error fetching market cap data from CoinPaprika: {e}\n"
                          f"Tip: Check API documentation at https://api.coinpaprika.com/")

