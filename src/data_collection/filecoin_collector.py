"""
Filecoin Data Collector

Collects Filecoin storage provider data from Filfox explorer.
"""

import pandas as pd
import requests
import time
import re
import io
import os
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

class FilecoinCollector:
    """
    Collects Filecoin network data from Filfox explorer.
    """
    
    def __init__(self, dune_api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache" / "filecoin"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://filfox.info"
        self.api_url = "https://api.filfox.info/api/v1"
        
        # Dune Analytics API
        self.dune_api_key = dune_api_key or os.getenv("DUNE_API_KEY")
        self.dune_base = "https://api.dune.com/api/v1"
        self.dune_query_id = 3302707  # Filecoin daily metrics query
    
    def get_storage_provider_count(self, date: Optional[str] = None) -> Optional[int]:
        """
        Get current storage provider count from Filfox homepage.
        
        Parameters
        ----------
        date : str, optional
            Date in YYYY-MM-DD format (for historical data if available)
            Currently only supports current date - historical data needs different approach
            
        Returns
        -------
        int
            Number of active storage providers
        """
        try:
            # Scrape Filfox homepage for current data
            url = f"{self.base_url}/en"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Look for activeMiners in the page
                # Try multiple patterns
                patterns = [
                    r'activeMiners[:\"\\s]+(\d+)',
                    r'\"activeMiners\"[:\"\\s]+(\d+)',
                    r'Active Miners[^>]*>(\d+)',
                    r'active.*miners[^>]*>(\d+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text, re.IGNORECASE)
                    if match:
                        count = int(match.group(1))
                        print(f"  ✅ Found activeMiners: {count}")
                        return count
                
                # Try to find in JSON data embedded in page
                json_match = re.search(r'window\.__NUXT__\s*=\s*({.*?});', response.text, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        # Navigate through the nested structure
                        if 'data' in data and len(data['data']) > 0:
                            overview = data['data'][0].get('overview', {})
                            if 'activeMiners' in overview:
                                count = int(overview['activeMiners'])
                                print(f"  ✅ Found activeMiners in JSON: {count}")
                                return count
                    except:
                        pass
                
                print(f"  ⚠️  Could not extract activeMiners from Filfox homepage")
                return None
            else:
                print(f"  ❌ HTTP error {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None
    
    def get_storage_capacity(self) -> Optional[dict]:
        """
        Get current storage capacity statistics.
        
        Returns
        -------
        dict
            Dictionary with capacity metrics
        """
        try:
            url = f"{self.base_url}/stats"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None
    
    def get_historical_provider_data(
        self,
        start_date: str,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical storage provider count from Dune Analytics.
        
        Uses Dune query #3302707 which queries the Filecoin daily metrics dataset.
        This is much more reliable than scraping and provides complete historical data.
        
        Parameters
        ----------
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
            
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, users
            Note: 'users' may be active_addresses or storage_providers depending on dataset
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_file = self.cache_dir / f"users_dune_{start_date}_{end_date}.csv"
        if cache_file.exists():
            df = pd.read_csv(cache_file, parse_dates=['date'])
            print(f"  ✅ Loaded from cache: {len(df)} records")
            return df
        
        # Try Dune Analytics first (preferred method)
        if self.dune_api_key:
            print(f"  📡 Fetching historical storage provider data from Dune Analytics...")
            print(f"  📊 Using query #{self.dune_query_id} (Filecoin daily metrics)")
            df = self._get_provider_data_from_dune(start_date, end_date)
            if df is not None and not df.empty:
                df.to_csv(cache_file, index=False)
                print(f"  ✅ Fetched {len(df)} historical records from Dune")
                print(f"  💾 Cached: {cache_file.name}")
                return df
        
        # Fallback to scraping if Dune fails
        print(f"  ⚠️  Dune fetch failed, trying Filfox scraping...")
        return self._get_current_as_placeholder()
    
    def _get_provider_data_from_dune(
        self,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch user activity data from Dune Analytics CSV endpoint.
        
        Uses query #3302707 which queries dune.kalen.dataset_filecoin_daily_metrics
        
        Strategy:
        - First try: Active addresses (if available) - can apply nonce filtering if needed
        - Second try: Active storage providers/miners
        - Matches paper methodology by preferring active addresses
        """
        try:
            # Use CSV endpoint (no execution cost if query already run)
            url = f"{self.dune_base}/query/{self.dune_query_id}/results/csv"
            headers = {"X-DUNE-API-KEY": self.dune_api_key}
            
            print(f"  📡 Fetching CSV results from Dune...")
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Parse CSV
                df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
                
                # Check what columns we have
                print(f"  📊 Columns available: {list(df.columns)}")
                
                # Look for date column
                date_col = None
                for col in ['date', 'day', 'timestamp', 'time']:
                    if col in df.columns:
                        date_col = col
                        break
                
                if not date_col:
                    print(f"  ⚠️  Could not find date column in Dune results")
                    return None
                
                # Convert date column
                df[date_col] = pd.to_datetime(df[date_col])
                
                # Strategy: Prefer active addresses (matches paper methodology)
                # If not available, fall back to storage providers
                
                # Priority 1: Active addresses (for nonce filtering if needed)
                user_col = None
                user_col_candidates = [
                    'active_address_count_daily',  # Filecoin dataset uses this
                    'active_addresses', 'dau', 'daily_active_users', 'active_users',
                    'addresses', 'unique_addresses', 'active_address_count'
                ]
                
                for col in user_col_candidates:
                    if col in df.columns:
                        user_col = col
                        print(f"  ✅ Found active addresses column: {col}")
                        break
                
                # Priority 2: Storage providers/miners (if no active addresses)
                if not user_col:
                    provider_col_candidates = [
                        'providers_with_active_deals',  # Filecoin dataset uses this
                        'unique_deal_making_providers',  # Alternative
                        'active_miners', 'miners', 'storage_providers', 'provider_count',
                        'active_storage_providers', 'miner_count', 'active_providers',
                        'providers_with_power'  # Providers with storage power
                    ]
                    for col in provider_col_candidates:
                        if col in df.columns:
                            user_col = col
                            print(f"  ✅ Found storage provider column: {col}")
                            print(f"  ⚠️  Note: Using providers instead of addresses (different from paper)")
                            break
                
                if not user_col:
                    print(f"  ⚠️  Could not find user/activity column")
                    print(f"  Available columns: {list(df.columns)}")
                    print(f"  Returning full dataset for inspection...")
                    return df
                
                # Filter by date range
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]
                
                # Rename columns to standard format
                result_df = pd.DataFrame({
                    'date': df[date_col],
                    'users': df[user_col]  # Generic 'users' column name
                })
                
                result_df = result_df.sort_values('date').reset_index(drop=True)
                
                # Note about validation and filtering methodology
                if 'active_address' in user_col.lower() or 'dau' in user_col.lower() or 'address' in user_col.lower():
                    print(f"  ℹ️  Using active addresses - matches paper methodology")
                    print(f"  ℹ️  Filtering: Check if nonce ≥ 5 filtering is needed")
                    print(f"  ℹ️  Rationale: Filecoin has transaction addresses (may have fake users)")
                    print(f"  ℹ️  Note: This dataset has active addresses but may not have nonce filtering")
                    print(f"  ℹ️  Decision: Use as-is (no nonce filter) OR create new query with nonce ≥ 5")
                else:
                    print(f"  ℹ️  Using {user_col} - different from paper's active addresses approach")
                    print(f"  ℹ️  Filtering: May not need nonce filtering (providers are real infrastructure)")
                    print(f"  ℹ️  Rationale: Storage providers require hardware/capital (lower fake user risk)")
                
                return result_df
                
            elif response.status_code == 404:
                print(f"  ⚠️  Query results not found. Query may need to be executed first.")
                print(f"  📊 Execute query at: https://dune.com/queries/{self.dune_query_id}")
                print(f"  ⚠️  Executing query will cost credits!")
                return None
            else:
                print(f"  ❌ Dune API error {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"  ❌ Error fetching from Dune: {e}")
            return None
    
    
    def _get_current_as_placeholder(self) -> pd.DataFrame:
        """Get current data as placeholder when historical scraping fails."""
        provider_count = self.get_storage_provider_count()
        if provider_count is not None:
            df = pd.DataFrame([{
                'date': datetime.now(),
                'provider_count': provider_count
            }])
            return df
        return pd.DataFrame()
    
    def get_current_stats(self) -> Optional[dict]:
        """
        Get current network statistics from Filfox homepage.
        
        Returns
        -------
        dict
            Dictionary with network stats including activeMiners
        """
        try:
            url = f"{self.base_url}/en"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Try to extract JSON data from page
                json_match = re.search(r'window\.__NUXT__\s*=\s*({.*?});', response.text, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        if 'data' in data and len(data['data']) > 0:
                            overview = data['data'][0].get('overview', {})
                            return overview
                    except Exception as e:
                        print(f"  ⚠️  Could not parse JSON: {e}")
                
                # Fallback: extract individual values
                stats = {}
                provider_count = self.get_storage_provider_count()
                if provider_count:
                    stats['activeMiners'] = provider_count
                return stats if stats else None
            else:
                return None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None

