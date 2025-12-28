"""
Safe CoinGecko API Wrapper

Tracks API calls and ensures we don't overuse credits.
Always checks cache first, uses batch requests when possible.
"""

import requests
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pandas as pd
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system env vars

class CoinGeckoSafe:
    """
    Safe wrapper for CoinGecko API that tracks usage and minimizes calls.
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY", "")
        # Use Pro API endpoint if API key is present (for premium plans)
        if self.api_key:
            self.base_url = "https://pro-api.coingecko.com/api/v3"
        else:
            self.base_url = "https://api.coingecko.com/api/v3"
        
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache" / "coingecko"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Track API calls
        self.call_count = 0
        self.call_log = []
        self.last_call_time = 0
        self.min_interval = 1.2  # Minimum seconds between calls (50 calls/min = 1.2s)
        
        # Load call history
        self.history_file = self.cache_dir / "api_call_history.json"
        self.load_history()
    
    def load_history(self):
        """Load API call history from disk"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.call_count = data.get('total_calls', 0)
                    self.call_log = data.get('call_log', [])
            except:
                self.call_count = 0
                self.call_log = []
    
    def save_history(self):
        """Save API call history to disk"""
        data = {
            'total_calls': self.call_count,
            'call_log': self.call_log[-100:],  # Keep last 100 calls
            'last_updated': datetime.now().isoformat()
        }
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _check_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Check if data exists in cache"""
        cache_file = self.cache_dir / f"{cache_key}.csv"
        if cache_file.exists():
            try:
                df = pd.read_csv(cache_file, parse_dates=['date'])
                print(f"  ✅ Using cached data: {cache_file.name}")
                return df
            except Exception as e:
                print(f"  ⚠️  Cache read error: {e}")
        return None
    
    def _save_cache(self, cache_key: str, df: pd.DataFrame):
        """Save data to cache"""
        cache_file = self.cache_dir / f"{cache_key}.csv"
        try:
            df.to_csv(cache_file, index=False)
            print(f"  💾 Cached: {cache_file.name}")
        except Exception as e:
            print(f"  ⚠️  Cache save error: {e}")
    
    def _rate_limit_check(self):
        """Ensure we respect rate limits"""
        now = time.time()
        time_since_last = now - self.last_call_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            print(f"  ⏳ Rate limiting: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self.last_call_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict, description: str) -> Optional[Dict]:
        """
        Make API request with safety checks.
        
        Returns None if request fails or should be skipped.
        """
        # Rate limit check
        self._rate_limit_check()
        
        # Build URL
        url = f"{self.base_url}/{endpoint}"
        
        # Headers - use correct header name for Pro API
        headers = {}
        if self.api_key:
            # Pro API uses x-cg-pro-api-key, demo uses x-cg-demo-api-key
            # Try pro first, fallback to demo
            headers['x-cg-pro-api-key'] = self.api_key
        
        # Log the call
        call_info = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'description': description,
            'params': params.copy()
        }
        
        print(f"  📡 API Call #{self.call_count + 1}: {description}")
        print(f"     Endpoint: {endpoint}")
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Update call count
            self.call_count += 1
            call_info['status_code'] = response.status_code
            call_info['success'] = response.status_code == 200
            
            if response.status_code == 200:
                data = response.json()
                call_info['data_keys'] = list(data.keys()) if isinstance(data, dict) else 'list'
                self.call_log.append(call_info)
                self.save_history()
                print(f"     ✅ Success")
                return data
                
            elif response.status_code == 429:
                print(f"     ❌ Rate limit hit! Waiting 60s...")
                time.sleep(60)
                # Don't retry automatically - let user decide
                call_info['error'] = 'rate_limit'
                self.call_log.append(call_info)
                self.save_history()
                return None
                
            else:
                print(f"     ❌ Error {response.status_code}: {response.text[:100]}")
                call_info['error'] = f"status_{response.status_code}"
                call_info['error_message'] = response.text[:200]
                self.call_log.append(call_info)
                self.save_history()
                return None
                
        except Exception as e:
            print(f"     ❌ Exception: {e}")
            call_info['error'] = str(e)
            self.call_log.append(call_info)
            self.save_history()
            return None
    
    def get_market_chart(
        self, 
        coin_id: str, 
        days: int = 365,
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Get market chart data with caching.
        
        Parameters
        ----------
        coin_id : str
            CoinGecko coin ID
        days : int or str
            Number of days. Use 3650 for 10 years (Analyst Plan max).
            'max' is converted to 3650.
        use_cache : bool
            Check cache first (default: True)
        force_refresh : bool
            Force API call even if cache exists (default: False)
        """
        # Convert 'max' to 3650 (10 years - Analyst Plan limit)
        if days == 'max' or days == 'Max':
            days = 3650
        """
        Get market chart data with caching.
        
        Parameters
        ----------
        coin_id : str
            CoinGecko coin ID
        days : int
            Number of days (365 for free tier, 'max' for paid)
        use_cache : bool
            Check cache first (default: True)
        force_refresh : bool
            Force API call even if cache exists (default: False)
        """
        cache_key = f"{coin_id}_market_chart_{days}"
        
        # Check cache first
        if use_cache and not force_refresh:
            cached = self._check_cache(cache_key)
            if cached is not None:
                return cached
        
        # Make API call
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        data = self._make_request(
            f"coins/{coin_id}/market_chart",
            params,
            f"Market chart for {coin_id} ({days} days)"
        )
        
        if data is None:
            return None
        
        # Parse response
        market_caps = data.get('market_caps', [])
        prices = data.get('prices', [])
        
        if not market_caps:
            print(f"  ⚠️  No market cap data in response")
            return None
        
        # Convert to DataFrame
        records = []
        for i, (timestamp, mcap) in enumerate(market_caps):
            date = datetime.fromtimestamp(timestamp / 1000)
            price = prices[i][1] if i < len(prices) else None
            records.append({
                'date': date,
                'market_cap': mcap,
                'price': price
            })
        
        df = pd.DataFrame(records)
        df = df.sort_values('date').reset_index(drop=True)
        
        # Save to cache
        self._save_cache(cache_key, df)
        
        return df
    
    def get_batch_simple_price(
        self,
        coin_ids: List[str],
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> Optional[Dict]:
        """
        Get current prices for multiple coins in one API call (efficient!).
        
        Parameters
        ----------
        coin_ids : List[str]
            List of CoinGecko coin IDs
        use_cache : bool
            Check cache first (default: True)
        force_refresh : bool
            Force API call even if cache exists (default: False)
        """
        # Create cache key from sorted IDs
        cache_key = f"batch_price_{'_'.join(sorted(coin_ids))}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # Check cache
        if use_cache and not force_refresh and cache_file.exists():
            try:
                # Check if cache is recent (within 1 hour)
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < 3600:  # 1 hour
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    print(f"  ✅ Using cached batch price data (age: {cache_age/60:.1f} min)")
                    return data
            except Exception as e:
                print(f"  ⚠️  Cache read error: {e}")
        
        # Make API call
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': 'usd',
            'include_market_cap': 'true'
        }
        
        data = self._make_request(
            "simple/price",
            params,
            f"Batch price for {len(coin_ids)} coins"
        )
        
        if data is None:
            return None
        
        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  💾 Cached batch price data")
        except Exception as e:
            print(f"  ⚠️  Cache save error: {e}")
        
        return data
    
    def get_usage_stats(self) -> Dict:
        """Get API usage statistics"""
        recent_calls = [c for c in self.call_log if c.get('success', False)]
        failed_calls = [c for c in self.call_log if not c.get('success', False)]
        
        return {
            'total_calls': self.call_count,
            'successful_calls': len(recent_calls),
            'failed_calls': len(failed_calls),
            'last_call': self.call_log[-1]['timestamp'] if self.call_log else None,
            'call_log_file': str(self.history_file)
        }
    
    def print_usage_stats(self):
        """Print API usage statistics"""
        stats = self.get_usage_stats()
        print(f"\n{'='*60}")
        print("COINGECKO API USAGE STATISTICS")
        print(f"{'='*60}")
        print(f"Total API Calls: {stats['total_calls']}")
        print(f"Successful: {stats['successful_calls']}")
        print(f"Failed: {stats['failed_calls']}")
        if stats['last_call']:
            print(f"Last Call: {stats['last_call']}")
        print(f"History File: {stats['call_log_file']}")
        print(f"{'='*60}\n")

