"""
Generic Network Data Collector

Extends the Ethereum-specific collector to handle multiple network types:
- Payment networks (Ethereum, L2s)
- Compute networks (Render, Akash, etc.)
- DePIN networks (Helium, Filecoin, etc.)
- Social protocols (Farcaster, Lens, etc.)
- Identity systems (ENS, Unstoppable, etc.)
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pathlib import Path
import os

from .ethereum_collector import EthereumDataCollector


class NetworkDataCollector(EthereumDataCollector):
    """
    Generic network data collector that extends EthereumDataCollector
    to handle multiple network types with category-specific adaptations.
    """
    
    # Network category definitions
    NETWORK_CATEGORIES = {
        'payment': {
            'user_metric': 'active_addresses',
            'user_filter': 'nonce_threshold',  # nonce >= threshold
            'value_metric': 'market_cap',
            'abandonment_days': 90,
            'examples': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'base']
        },
        'compute': {
            'user_metric': 'weighted_users',  # providers × 1.5 + consumers × 1.0
            'user_filter': 'active_providers_consumers',
            'value_metric': 'revenue_or_compute_hours',
            'abandonment_days': 30,
            'examples': ['render', 'akash', 'bittensor', 'gensyn', 'io.net']
        },
        'depin': {
            'user_metric': 'weighted_nodes',  # geographic/capacity weighted
            'user_filter': 'active_nodes',
            'value_metric': 'coverage_capacity',
            'abandonment_days': 30,
            'examples': ['helium', 'filecoin', 'arweave', 'hivemapper', 'dimo']
        },
        'social': {
            'user_metric': 'engagement_weighted',  # creators > consumers
            'user_filter': 'active_engagement',
            'value_metric': 'engagement_metrics',
            'abandonment_days': 90,
            'examples': ['farcaster', 'lens', 'deso']
        },
        'identity': {
            'user_metric': 'active_resolutions',
            'user_filter': 'resolution_frequency',
            'value_metric': 'resolution_count',
            'abandonment_days': 180,
            'examples': ['ens', 'unstoppable', 'worldcoin']
        }
    }
    
    def __init__(self, network_category: str = 'payment', **kwargs):
        """
        Initialize network data collector.
        
        Parameters
        ----------
        network_category : str
            Category of network: 'payment', 'compute', 'depin', 'social', 'identity'
        **kwargs
            Passed to EthereumDataCollector (API keys, cache_dir, etc.)
        """
        super().__init__(**kwargs)
        
        if network_category not in self.NETWORK_CATEGORIES:
            raise ValueError(
                f"Unknown network category: {network_category}. "
                f"Must be one of: {list(self.NETWORK_CATEGORIES.keys())}"
            )
        
        self.network_category = network_category
        self.category_config = self.NETWORK_CATEGORIES[network_category]
    
    def get_user_metric_name(self) -> str:
        """Get the user metric name for this network category"""
        return self.category_config['user_metric']
    
    def get_value_metric_name(self) -> str:
        """Get the value metric name for this network category"""
        return self.category_config['value_metric']
    
    def collect_compute_network_data(
        self,
        network_name: str,
        start_date: str,
        end_date: Optional[str] = None,
        data_sources: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Collect data for compute/AI marketplace networks.
        
        For compute networks:
        - Users: Weighted composite (providers × 1.5 + consumers × 1.0)
        - Value: Revenue, fees, or compute hours delivered
        
        Parameters
        ----------
        network_name : str
            Name of the network (e.g., 'render', 'akash')
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
        data_sources : dict, optional
            Custom data sources (APIs, on-chain, etc.)
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, users (weighted), value (revenue/compute hours)
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # This is a placeholder - will need to implement based on actual data sources
        # For now, return structure
        print(f"Collecting compute network data for {network_name}")
        print(f"  Category: {self.network_category}")
        print(f"  User metric: {self.get_user_metric_name()}")
        print(f"  Value metric: {self.get_value_metric_name()}")
        print(f"  Date range: {start_date} to {end_date}")
        
        # TODO: Implement actual data collection
        # - On-chain data for providers/consumers
        # - Revenue/fee data
        # - Compute hours delivered
        
        return pd.DataFrame()  # Placeholder
    
    def collect_depin_network_data(
        self,
        network_name: str,
        start_date: str,
        end_date: Optional[str] = None,
        data_sources: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Collect data for DePIN (physical infrastructure) networks.
        
        For DePIN networks:
        - Users: Geographic/capacity-weighted active nodes
        - Value: Coverage + capacity utilization
        
        Parameters
        ----------
        network_name : str
            Name of the network (e.g., 'helium', 'filecoin')
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
        data_sources : dict, optional
            Custom data sources
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, users (weighted nodes), value (coverage/capacity)
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Collecting DePIN network data for {network_name}")
        print(f"  Category: {self.network_category}")
        print(f"  User metric: {self.get_user_metric_name()}")
        print(f"  Value metric: {self.get_value_metric_name()}")
        print(f"  Date range: {start_date} to {end_date}")
        
        # TODO: Implement actual data collection
        # - Node count and geographic distribution
        # - Coverage metrics
        # - Capacity utilization
        
        return pd.DataFrame()  # Placeholder
    
    def collect_social_network_data(
        self,
        network_name: str,
        start_date: str,
        end_date: Optional[str] = None,
        data_sources: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Collect data for social protocol networks.
        
        For social networks:
        - Users: Engagement-weighted (creators > consumers)
        - Value: Engagement metrics or content value
        
        Parameters
        ----------
        network_name : str
            Name of the network (e.g., 'farcaster', 'lens')
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
        data_sources : dict, optional
            Custom data sources
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, users (engagement-weighted), value (engagement metrics)
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Collecting social network data for {network_name}")
        print(f"  Category: {self.network_category}")
        print(f"  User metric: {self.get_user_metric_name()}")
        print(f"  Value metric: {self.get_value_metric_name()}")
        print(f"  Date range: {start_date} to {end_date}")
        
        # TODO: Implement actual data collection
        # - Active users (creators vs consumers)
        # - Engagement metrics (posts, interactions)
        # - Content value
        
        return pd.DataFrame()  # Placeholder
    
    def collect_identity_network_data(
        self,
        network_name: str,
        start_date: str,
        end_date: Optional[str] = None,
        data_sources: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Collect data for identity/reputation system networks.
        
        For identity networks:
        - Users: Active resolution frequency
        - Value: Active resolution count
        
        Parameters
        ----------
        network_name : str
            Name of the network (e.g., 'ens', 'unstoppable')
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (default: today)
        data_sources : dict, optional
            Custom data sources
        
        Returns
        -------
        pd.DataFrame
            DataFrame with columns: date, users (active resolutions), value (resolution count)
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Collecting identity network data for {network_name}")
        print(f"  Category: {self.network_category}")
        print(f"  User metric: {self.get_user_metric_name()}")
        print(f"  Value metric: {self.get_value_metric_name()}")
        print(f"  Date range: {start_date} to {end_date}")
        
        # TODO: Implement actual data collection
        # - Active domain/identity count
        # - Resolution frequency
        # - Market cap or revenue
        
        return pd.DataFrame()  # Placeholder
    
    def collect_network_data(
        self,
        network_name: str,
        start_date: str,
        end_date: Optional[str] = None,
        data_sources: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Generic method to collect data based on network category.
        
        Routes to appropriate collection method based on category.
        """
        if self.network_category == 'payment':
            # Use existing Ethereum collector methods
            return self.get_complete_ethereum_data(start_date, end_date)
        elif self.network_category == 'compute':
            return self.collect_compute_network_data(network_name, start_date, end_date, data_sources)
        elif self.network_category == 'depin':
            return self.collect_depin_network_data(network_name, start_date, end_date, data_sources)
        elif self.network_category == 'social':
            return self.collect_social_network_data(network_name, start_date, end_date, data_sources)
        elif self.network_category == 'identity':
            return self.collect_identity_network_data(network_name, start_date, end_date, data_sources)
        else:
            raise ValueError(f"Unknown network category: {self.network_category}")

