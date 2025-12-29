# Framework Usage Guide

This folder contains complete documentation and scripts for using the Network Effects Analyzer framework. The framework enables analysis of network effects for any blockchain network using Metcalfe's Law.

## Contents

- **Framework Usage Documentation**: This README provides complete instructions for using the framework
- **Analysis Scripts**: Python scripts for data collection, regression analysis, and robustness checks
- **SQL Queries**: Dune Analytics queries for extracting on-chain user activity data

## Quick Start

### Using the Framework

```python
from src.analysis.metcalfe_model import MetcalfeModel
import pandas as pd

# Load your data (must have 'users' and 'market_cap' columns)
df = pd.read_csv('your_network_data.csv')
df = df[(df['users'] > 0) & (df['market_cap'] > 0)]

# Fit the model
model = MetcalfeModel()
results = model.fit(df['users'], df['market_cap'])

# View results
print(f"Beta: {results['beta']:.2f}")
print(f"R-squared: {results['r_squared']:.2f}")

# Classify network
if results['beta'] > 1.0:
    print("Sustainable network effects")
else:
    print("Unsustainable network effects")
```

### Example Script

See `examples/analyze_ethereum.py` for a complete example.

## Data Collection Workflow

### Step 1: Collect On-Chain User Data

The `queries/` folder contains SQL queries for extracting active user data from Dune Analytics.

**For each network:**

1. Go to [Dune Analytics](https://dune.com)
2. Create a new query
3. Paste the SQL from the appropriate query file
4. Execute the query
5. Export results as CSV
6. Save to `data/raw/dune/`

**Query Files:**

| Network | Query File |
|---------|------------|
| Ethereum | `queries/dune_query_ethereum_active_addresses_nonce5.sql` |
| Arbitrum | `queries/dune_query_arbitrum_active_addresses_nonce5.sql` |
| Optimism | `queries/dune_query_optimism_active_addresses_nonce5.sql` |
| Polygon | `queries/dune_query_polygon_active_addresses_nonce5.sql` |
| Uniswap | `queries/dune_query_uniswap_active_addresses_nonce5.sql` |
| Aave | `queries/dune_query_aave_active_addresses_nonce5.sql` |
| Compound | `queries/dune_query_compound_active_addresses_nonce5.sql` |
| MakerDAO | `queries/dune_query_maker_active_addresses_nonce5.sql` |
| SushiSwap | `queries/dune_query_sushiswap_active_addresses_nonce5.sql` |
| Chainlink | `queries/dune_query_chainlink_active_addresses_nonce5.sql` |
| Livepeer | `queries/dune_query_livepeer_active_addresses_nonce5.sql` |
| The Graph | `queries/dune_query_thegraph_active_addresses_nonce5.sql` |

### Step 2: Collect Market Cap Data

Market cap data is collected via CoinGecko API:

```bash
python scripts/data_collection/collect_coingecko_safe.py {network}
```

**Requirements:**
- CoinGecko API key (free tier available)
- Set in `.env`: `COINGECKO_API_KEY=your_key_here`

### Step 3: Merge Data

Merge user and market cap data:

```bash
python scripts/data_collection/correlate_dune_coingecko.py {network}
```

This creates `data/processed/{network}_correlated_data.csv` with columns:
- `date`: Date
- `users`: Active users (nonce >= 5)
- `market_cap`: Market capitalization (USD)

### Step 4: Run Analysis

```bash
python scripts/run_full_regression.py
```

This outputs:
- Regression results table (beta, SE, R-squared, classification)
- Performance validation (annualized returns by beta group)
- Saves results to `data/processed/regression_results_expanded.csv`

## Analysis Scripts

### run_full_regression.py

Main regression analysis script. Generates Table 1 from the paper.

**Usage:**
```bash
python scripts/run_full_regression.py
```

**Output:**
- Console: Summary statistics and results
- CSV: `data/processed/regression_results_expanded.csv`

### robustness_analysis.py

Robustness checks and sensitivity analysis.

**Usage:**
```bash
python scripts/robustness_analysis.py
```

**Tests:**
- Alternative nonce thresholds (3, 5, 10)
- Rolling window regressions
- Subsample analysis

### collect_defi_data.py

Collects data for DeFi networks (Aave, Compound, Maker, SushiSwap).

**Usage:**
```bash
python scripts/data_collection/collect_defi_data.py
```

### collect_new_networks.py

Collects data for other networks (Livepeer, Uniswap, The Graph).

**Usage:**
```bash
python scripts/data_collection/collect_new_networks.py
```

## Framework API

### MetcalfeModel

Core model class for Metcalfe's Law regression.

```python
from src.analysis.metcalfe_model import MetcalfeModel

model = MetcalfeModel()
results = model.fit(users, market_cap)
```

**Parameters:**
- `users`: Array-like of active user counts
- `market_cap`: Array-like of market capitalization values

**Returns:**
Dictionary with keys:
- `beta`: Beta coefficient (elasticity of market cap w.r.t. users)
- `alpha`: Alpha coefficient (intercept)
- `r_squared`: R-squared (model fit)
- `std_error`: Standard error of beta
- `n`: Number of observations

**Methods:**
- `fit(users, market_cap)`: Fit the model
- `predict(users)`: Predict market cap for given user counts
- `classify()`: Classify network (Sustainable/Borderline/Unsustainable)

## Methodology

### User Metric (nonce >= 5)

We filter to addresses with at least 5 interactions to exclude:
- Temporary/one-time addresses
- Spam accounts
- Airdrop farmers
- Bot transactions

This threshold was selected via AIC model selection in the original Metcalfe's Law paper.

### Classification

- **Sustainable (beta > 1)**: Token value scales super-linearly with users
- **Borderline (beta ≈ 1)**: Token value scales linearly with users
- **Unsustainable (beta < 1)**: Token value scales sub-linearly with users

### Model Specification

The model estimates:

```
log(market_cap) = alpha + beta * log(users) + error
```

Where:
- `beta` measures the elasticity of market cap with respect to users
- `beta > 1` indicates super-linear scaling (sustainable network effects)
- `beta = 1` indicates linear scaling (Metcalfe's Law baseline)
- `beta < 1` indicates sub-linear scaling (unsustainable)

## Output Format

### Regression Results

The main output is `data/processed/regression_results_expanded.csv`:

| Column | Description |
|--------|-------------|
| network | Network name |
| category | Network category (L1, L2, DeFi, etc.) |
| beta | Metcalfe's Law coefficient |
| se | Standard error |
| r_squared | Model fit (R-squared) |
| classification | Sustainable/Borderline/Unsustainable |
| annualized_return | Annualized price return |

## Requirements

### Python Dependencies

```bash
pip install -r requirements.txt
```

### API Keys

- **Dune Analytics**: For executing queries (optional, can use CSV exports)
- **CoinGecko**: For market cap data (free tier available)

Set in `.env`:
```
DUNE_API_KEY=your_dune_api_key
COINGECKO_API_KEY=your_coingecko_api_key
```

## Troubleshooting

### Data File Not Found

Ensure data files are in `data/processed/` with format:
- `{network}_correlated_data.csv`

### API Rate Limits

CoinGecko free tier has rate limits. Use `collect_coingecko_safe.py` which includes delays.

### Import Errors

Ensure you're in the project root and dependencies are installed:
```bash
pip install -r requirements.txt
```

## Additional Resources

- [QUICKSTART.md](../QUICKSTART.md) - Beginner-friendly quick start guide
- [REPRODUCTION_GUIDE.md](../REPRODUCTION_GUIDE.md) - Complete reproduction instructions
- [Paper](../paper/paper.pdf) - Full academic paper

## Citation

If you use this framework, please cite:

```bibtex
@article{liu2025network,
  title={Network Effects Across Crypto Categories: A Metcalfe's Law Framework for Assessing Sustainability},
  author={Liu, Danny},
  journal={...},
  year={2025}
}
```

## License

MIT License
