#!/usr/bin/env python3
"""
Arweave Data Collector

Collects Arweave network data including:
- Active miners
- Active addresses
- Market cap (from CoinGecko)
"""

import pandas as pd
import requests
import time
import os
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

# Import existing collectors
from .coingecko_safe import CoinGeckoSafe

class ArweaveCollector:
    """
    Collects Arweave network data from ViewBlock API and CoinGecko.
    """
    
    def __init__(self, coingecko_api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache" / "arweave"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.viewblock_base = "https://api.viewblock.io/v1/arweave"
        self.coingecko_safe = CoinGeckoSafe(api_key=coingecko_api_key)
    
    def get_current_stats(self) -> Optional[dict]:
        """
        Get current Arweave network statistics from ViewBlock.
        
        Returns
        -------
        dict
            Dictionary with current network stats
        """
        cache_file = self.cache_dir / "current_stats.json"
        
        # Check cache (1 hour expiry)
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(hours=1):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        try:
            # ViewBlock API endpoint for Arweave stats
            url = f"{self.viewblock_base}/stats"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache the result
                with open(cache_file, 'w') as f:
                    json.dump(data, f)
                
                return data
            else:
                print(f"⚠️  ViewBlock API returned {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching current stats: {e}")
            return None
    
    def get_active_miners(self) -> Optional[int]:
        """
        Get current number of active miners.
        
        Returns
        -------
        int or None
            Number of active miners
        """
        stats = self.get_current_stats()
        if stats:
            # ViewBlock API structure may vary - need to check actual response
            # Common fields: miners, activeMiners, minerCount
            for key in ['activeMiners', 'miners', 'minerCount', 'active_miners']:
                if key in stats:
                    return int(stats[key])
        return None
    
    def get_active_addresses_history(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical active addresses data.
        
        Note: ViewBlock API may not have historical data directly.
        This is a placeholder that needs to be implemented based on
        actual API capabilities or alternative data sources.
        
        Parameters
        ----------
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, users (active addresses)
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_file = self.cache_dir / f"active_addresses_{start_date}_{end_date}.csv"
        if cache_file.exists():
            df = pd.read_csv(cache_file, parse_dates=['date'])
            print(f"  ✅ Loaded from cache: {len(df)} records")
            return df
        
        print(f"  ⚠️  Historical active addresses data collection not yet implemented")
        print(f"  📊 Need to identify data source for Arweave historical active addresses")
        print(f"  💡 Options:")
        print(f"     1. ViewBlock API (if historical endpoints available)")
        print(f"     2. Arweave blockchain explorer APIs")
        print(f"     3. Dune Analytics (if query exists)")
        print(f"     4. Web scraping from Arweave stats pages")
        
        # Return empty DataFrame as placeholder
        return pd.DataFrame(columns=['date', 'users'])
    
    def get_market_cap_history(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical market cap data from CoinGecko.
        
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
        
        # Calculate days
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        days = (end_dt - start_dt).days
        
        # Use CoinGecko safe wrapper
        df = self.coingecko_safe.get_market_chart(
            coin_id='arweave',
            days=min(days, 3650),  # Max 10 years for Analyst Plan
            use_cache=True,
            force_refresh=False
        )
        
        if df is not None and not df.empty:
            # Filter by date range
            df['date'] = pd.to_datetime(df['date'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            return df[['date', 'market_cap', 'price']]
        
        return pd.DataFrame(columns=['date', 'market_cap', 'price'])
    
    def get_data(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get combined user activity and market cap data.
        
        Parameters
        ----------
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
            
        Returns
        -------
        pd.DataFrame or None
            Combined DataFrame with columns: date, users, market_cap, price
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get market cap data
        mcap_df = self.get_market_cap_history(start_date, end_date)
        
        # Get user activity data
        users_df = self.get_active_addresses_history(start_date, end_date)
        
        if mcap_df.empty:
            print("❌ Could not collect market cap data")
            return None
        
        if users_df.empty:
            print("⚠️  Could not collect user activity data")
            print("   Returning market cap data only (cannot run analysis without users)")
            return None
        
        # Merge datasets
        mcap_df['date'] = pd.to_datetime(mcap_df['date']).dt.date
        users_df['date'] = pd.to_datetime(users_df['date']).dt.date
        
        combined_df = pd.merge(
            mcap_df,
            users_df,
            on='date',
            how='inner'
        )
        
        combined_df = combined_df.sort_values('date').reset_index(drop=True)
        
        return combined_df
