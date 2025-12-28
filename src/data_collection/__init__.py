"""
Data Collection Module

Provides collectors for different network types:
- EthereumDataCollector: Payment/transaction networks
- NetworkDataCollector: Generic collector for all network categories
"""

from .ethereum_collector import EthereumDataCollector
from .network_collector import NetworkDataCollector

__all__ = ['EthereumDataCollector', 'NetworkDataCollector']
