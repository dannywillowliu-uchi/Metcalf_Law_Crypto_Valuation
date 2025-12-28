# Ethereum Data Collection Guide

## Overview

This module provides multiple ways to collect Ethereum historical data for network effects analysis.

## Data Sources

### 1. CoinGecko API (Market Cap) ✅ Recommended
- **Free tier**: 10-50 calls/minute
- **API key**: Optional (improves rate limits)
- **Get key**: https://www.coingecko.com/en/api
- **What it provides**: Historical market cap and prices

### 2. Dune Analytics (Active Addresses) ✅ Recommended
- **Free tier**: Available
- **API key**: Required
- **Get key**: https://dune.com/settings/api
- **What it provides**: Daily active addresses (uses public query #2)

### 3. CSV Files (Fallback)
- Load pre-collected data from CSV
- Format: `date, users, market_cap`

## Quick Start

### Option 1: Using APIs (Recommended)

```python
from src.data_collection import EthereumDataCollector

# Initialize (API keys from environment variables or parameters)
collector = EthereumDataCollector(
    coingecko_api_key="your_key_here",  # Optional
    dune_api_key="your_key_here"        # Required for active addresses
)

# Get complete data
df = collector.get_complete_ethereum_data(
    start_date="2017-01-01",
    end_date="2024-01-01"
)
```

### Option 2: Using Environment Variables

```bash
export COINGECKO_API_KEY="your_key"
export DUNE_API_KEY="your_key"
```

Then in Python:
```python
from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()  # Reads from environment
df = collector.get_complete_ethereum_data()
```

### Option 3: CSV Import

```python
from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()
df = collector.load_from_csv("data/raw/ethereum_historical.csv")
```

## API Setup Instructions

### CoinGecko API Key (Optional)

1. Go to https://www.coingecko.com/en/api
2. Sign up for free account
3. Get your API key from dashboard
4. Free tier: 10-50 calls/minute

### Dune Analytics API Key (Required for Active Addresses)

1. Go to https://dune.com and create account
2. Go to Settings → API
3. Create new API key
4. Free tier available

**Note**: Dune uses public query #2 for Ethereum active addresses by default. You can specify a different query_id if needed.

## Data Format

The collector returns a DataFrame with:
- `date`: DateTime index
- `users`: Active addresses (daily)
- `market_cap`: Market capitalization in USD

## Caching

API responses are automatically cached in `data/cache/` to avoid repeated calls:
- Market cap: `market_cap_YYYY-MM-DD_YYYY-MM-DD.csv`
- Active addresses: `active_addresses_dune_<query_id>.csv`

Delete cache files to force fresh data fetch.

## Error Handling

If APIs fail, the collector will:
1. Show clear error messages
2. Suggest using CSV fallback
3. Provide instructions for API setup

## Example: Complete Workflow

```python
from src.data_collection import EthereumDataCollector
from src.analysis import MetcalfeModel, FTPMSModel

# Collect data
collector = EthereumDataCollector()
eth_data = collector.get_complete_ethereum_data(
    start_date="2017-01-01",
    end_date="2024-01-01"
)

# Analyze
metcalfe = MetcalfeModel()
results = metcalfe.fit(eth_data['users'], eth_data['market_cap'])
print(f"β = {results['beta']:.4f}")
```

## Troubleshooting

**"Dune API key required"**
- Get API key from https://dune.com/settings/api
- Set environment variable: `export DUNE_API_KEY="your_key"`

**"Rate limit exceeded"**
- CoinGecko: Wait or get API key for higher limits
- Dune: Check your tier limits

**"Query returned no results"**
- Dune query might be outdated
- Try a different query_id or use CSV

**"Could not fetch data"**
- Check internet connection
- Verify API keys are correct
- Use CSV fallback as temporary solution

