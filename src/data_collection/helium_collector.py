#!/usr/bin/env python3
"""
Helium Data Collector

Collects Helium network data including hotspot count.
Helium migrated to Solana, so data may be available via Solana explorers.
"""

import pandas as pd
import requests
import os
from typing import Optional
from datetime import datetime
from pathlib import Path

from .coingecko_safe import CoinGeckoSafe

class HeliumCollector:
    """Collects Helium network data."""
    
    def __init__(self, coingecko_api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache" / "helium"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.coingecko_safe = CoinGeckoSafe(api_key=coingecko_api_key)
        # Helium API endpoints (may need to verify)
        self.helium_api = "https://api.helium.io/v1"
        self.solana_explorer = "https://api.solana.com"  # May need different endpoint
    
    def get_market_cap_history(self, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get market cap from CoinGecko."""
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        days = min((end_dt - start_dt).days, 3650)
        
        df = self.coingecko_safe.get_market_chart(
            coin_id='helium',
            days=days,
            use_cache=True,
            force_refresh=False
        )
        
        if df is not None and not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
            return df[['date', 'market_cap', 'price']]
        
        return pd.DataFrame(columns=['date', 'market_cap', 'price'])
    
    def get_hotspot_count(self) -> Optional[int]:
        """Get current hotspot count - needs API research."""
        # TODO: Research Helium API endpoints
        # Helium migrated to Solana, may need Solana-based explorer
        return None
    
    def get_active_addresses_history(self, start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get historical active addresses/hotspots - needs data source."""
        # TODO: Research data source for historical hotspot count
        return pd.DataFrame(columns=['date', 'users'])


