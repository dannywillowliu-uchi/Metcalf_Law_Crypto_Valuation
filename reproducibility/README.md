# Reproducibility Package

This folder contains all code necessary to reproduce the analysis in "Valuing Blockchain Networks via Metcalfe's Law."

## Directory Structure

```
reproducibility/
├── queries/          # Dune Analytics SQL queries for user data
├── scripts/          # Python scripts for data collection and analysis
└── README.md         # This file
```

## Requirements

### Python Dependencies
```bash
pip install pandas numpy scipy scikit-learn requests python-dotenv
```

### API Keys
You'll need:
- **Dune Analytics API key**: For executing queries and downloading results
- **CoinGecko API key** (optional): For market cap data (free tier works but has rate limits)

Set environment variables:
```bash
export DUNE_API_KEY="your_dune_api_key"
export COINGECKO_API_KEY="your_coingecko_api_key"  # Optional
```

## Data Collection Workflow

### Step 1: Execute Dune Queries

The `queries/` folder contains SQL queries for each network. To collect user data:

1. Go to [Dune Analytics](https://dune.com)
2. Create a new query and paste the SQL from the appropriate file
3. Execute the query (costs ~300 credits per query)
4. Note the query ID for use in the collection scripts

**Query Files:**

| Network | Query File | Metric |
|---------|------------|--------|
| Ethereum | `dune_query_ethereum_active_addresses_nonce5.sql` | Addresses with ≥5 transactions |
| Arbitrum | `dune_query_arbitrum_active_addresses_nonce5.sql` | Addresses with ≥5 transactions |
| Optimism | `dune_query_optimism_active_addresses_nonce5.sql` | Addresses with ≥5 transactions |
| Polygon | `dune_query_polygon_active_addresses_nonce5.sql` | Addresses with ≥5 transactions |
| Uniswap | `dune_query_uniswap_active_addresses_nonce5.sql` | Addresses with ≥5 swaps |
| Aave | `dune_query_aave_active_addresses_nonce5.sql` | Addresses with ≥5 AAVE transfers |
| Compound | `dune_query_compound_active_addresses_nonce5.sql` | Addresses with ≥5 COMP transfers |
| MakerDAO | `dune_query_maker_active_addresses_nonce5.sql` | Addresses with ≥5 MKR transfers |
| SushiSwap | `dune_query_sushiswap_active_addresses_nonce5.sql` | Addresses with ≥5 SUSHI transfers |
| Chainlink | `dune_query_chainlink_active_addresses_nonce5.sql` | Addresses with ≥5 LINK transfers |
| Livepeer | `dune_query_livepeer_active_addresses_nonce5.sql` | Addresses with ≥5 LPT transfers |
| The Graph | `dune_query_thegraph_active_addresses_nonce5.sql` | Addresses with ≥5 GRT transfers |
| Render | (via Token Terminal) | Addresses with ≥5 RNDR transfers |
| ENS | (via Dune) | Addresses with ≥5 ENS interactions |
| DIMO | (via Dune) | Addresses with ≥5 DIMO transfers |

### Step 2: Collect Data

After executing queries on Dune:

```bash
# Collect DeFi network data (Aave, Compound, Maker, SushiSwap)
python scripts/collect_defi_data.py

# Collect other networks (Livepeer, Uniswap, The Graph)
python scripts/collect_new_networks.py
```

These scripts:
1. Download user data from executed Dune queries (free via CSV export)
2. Fetch market cap data from CoinGecko
3. Merge and save to `data/processed/`

### Step 3: Run Regression Analysis

```bash
python scripts/run_full_regression.py
```

This outputs:
- Regression results table (β, SE, R², classification)
- Performance validation (annualized returns by β group)
- Saves results to `data/processed/regression_results_expanded.csv`

### Step 4: Robustness Analysis (Optional)

```bash
python scripts/robustness_analysis.py
```

Tests sensitivity to:
- Alternative nonce thresholds (3, 5, 10)
- Rolling window regressions
- Subsample analysis

## Output

The main output is `data/processed/regression_results_expanded.csv` containing:

| Column | Description |
|--------|-------------|
| network | Network name |
| category | Network category (L1, L2, DeFi, etc.) |
| beta | Metcalfe's Law coefficient |
| se | Standard error |
| r_squared | Model fit |
| ci_lower, ci_upper | 95% confidence interval |
| classification | Sustainable/Borderline/Unsustainable |
| annualized_return | Annualized price return |

## Methodology Notes

### User Metric (nonce ≥ 5)
We filter to addresses with at least 5 interactions to exclude:
- Temporary/one-time addresses
- Spam accounts
- Airdrop farmers

This follows the methodology in the original Metcalfe's Law paper which found nonce ≥ 5 optimal via AIC model selection.

### Classification
- **Sustainable (β > 1)**: 95% CI entirely above 1
- **Borderline (β ≈ 1)**: CI includes 1
- **Unsustainable (β < 1)**: 95% CI entirely below 1

## Citation

If you use this code, please cite:
```
[Paper citation to be added]
```

## License

MIT License
