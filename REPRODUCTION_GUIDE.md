# Reproduction Guide: Network Effects Across Crypto Categories

This guide explains how to reproduce all results, figures, and tables from the paper "Network Effects Across Crypto Categories: A Metcalfe's Law Framework for Assessing Sustainability."

## Repository Structure

```
network-effects-analyzer/
├── paper/                          # LaTeX paper and figures
│   ├── paper.tex                  # Main paper source
│   ├── paper.pdf                  # Compiled paper
│   ├── references.bib             # Bibliography
│   └── figures/                   # All paper figures
│       ├── fig1_network_effects_comparison.pdf
│       ├── fig4_sustainable_vs_unsustainable.pdf
│       ├── fig6_time_series_users_mcap.pdf
│       └── per_token/             # Per-token visualizations
├── data/                          # All data files
│   ├── processed/                 # Cleaned, merged data
│   │   ├── *_correlated_data.csv  # Network data (users + market cap)
│   │   └── regression_results_expanded.csv
│   └── raw/                       # Raw data sources
├── scripts/                       # Analysis scripts
│   ├── run_full_regression.py     # Main regression analysis
│   ├── create_time_series_figure.py
│   ├── generate_per_token_graphs.py
│   └── robustness_analysis.py
├── src/                           # Framework code
│   ├── analysis/
│   │   ├── metcalfe_model.py      # Core Metcalfe's Law model
│   │   └── markov_switching.py    # Markov-switching extension
│   └── data_collection/           # Data collection utilities
└── dune_query_*.sql               # Dune Analytics queries
```

## Quick Start

### 1. Install Dependencies

```bash
cd network-effects-analyzer
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Reproduce Main Results

```bash
# Run regression analysis (generates Table 1)
python scripts/run_full_regression.py

# Output: data/processed/regression_results_expanded.csv
```

### 3. Generate Paper Figures

```bash
# Generate time series figure (Figure 6)
python scripts/create_time_series_figure.py

# Generate per-token visualizations
python scripts/generate_per_token_graphs.py

# Output: paper/figures/
```

### 4. Compile Paper

```bash
cd paper
latexmk -pdf paper.tex
```

## Detailed Reproduction Steps

### Step 1: Data Collection

The paper uses two data sources:

#### A. On-Chain User Data (Dune Analytics)

1. **Execute Dune Queries**: Each network has a SQL query file:
   - `dune_query_ethereum_active_addresses_nonce5.sql`
   - `dune_query_uniswap_active_addresses_nonce5.sql`
   - etc.

2. **Export Results**: For each query:
   - Execute on Dune Analytics
   - Export CSV results
   - Save to `data/raw/dune/`

3. **Alternative**: Use provided scripts (requires Dune API key):
   ```bash
   python scripts/collect_defi_data.py
   python scripts/collect_new_networks.py
   ```

#### B. Market Cap Data (CoinGecko)

Market cap data is collected via CoinGecko API:

```bash
python scripts/download_full_history.py
```

**Note**: CoinGecko API requires a free API key. Set in `.env`:
```
COINGECKO_API_KEY=your_key_here
```

### Step 2: Data Processing

Merge user and market cap data:

```bash
python scripts/correlate_dune_coingecko.py
```

This creates `*_correlated_data.csv` files in `data/processed/` with columns:
- `date`: Date
- `users`: Active users (nonce ≥ 5)
- `market_cap`: Market capitalization (USD)

### Step 3: Regression Analysis

Run the main analysis:

```bash
python scripts/run_full_regression.py
```

**Outputs**:
- `data/processed/regression_results_expanded.csv`: Full results table
- Console output: Summary statistics

**This reproduces Table 1** from the paper.

### Step 4: Performance Validation

Calculate annualized returns:

```bash
python scripts/run_full_regression.py  # Includes returns calculation
```

**This reproduces Table 4** (performance by classification).

### Step 5: Generate Figures

#### Figure 1: Network Effects Comparison
```bash
# Uses regression results
python scripts/create_comparison_figure.py  # If exists
# Or manually from regression_results_expanded.csv
```

#### Figure 4: Performance Comparison
```bash
# Uses performance data
python scripts/create_performance_figure.py  # If exists
```

#### Figure 6: Time Series
```bash
python scripts/create_time_series_figure.py
```

#### Per-Token Graphs
```bash
python scripts/generate_per_token_graphs.py
```

Generates:
- `{network}_time_series.pdf`: Users and market cap over time
- `{network}_log_log_scatter.pdf`: Log-log scatter with regression line

### Step 6: Robustness Checks (Optional)

```bash
python scripts/robustness_analysis.py
```

Tests:
- Alternative nonce thresholds (3, 5, 10)
- Rolling window regressions
- Subsample analysis

## Data Files

### Required Data Files

All networks require `{network}_correlated_data.csv` with:
- `date`: datetime
- `users`: float (active users)
- `market_cap`: float (USD)

### Available Networks

| Network | Data File | Status |
|---------|-----------|--------|
| Ethereum | `ethereum_correlated_data_nonce5_paper_range.csv` | ✅ |
| Render | `render_correlated_data.csv` | ✅ |
| Livepeer | `livepeer_correlated_data.csv` | ✅ |
| Chainlink | `chainlink_correlated_data.csv` | ✅ |
| Optimism | `optimism_correlated_data.csv` | ✅ |
| SushiSwap | `sushiswap_correlated_data.csv` | ✅ |
| Aave | `aave_correlated_data.csv` | ✅ |
| Compound | `compound_correlated_data.csv` | ✅ |
| Polygon | `polygon_correlated_data.csv` | ✅ |
| Arbitrum | `arbitrum_correlated_data.csv` | ✅ |
| MakerDAO | `maker_correlated_data.csv` | ✅ |
| Uniswap | `uniswap_correlated_data.csv` | ✅ |
| The Graph | `thegraph_correlated_data.csv` | ✅ |
| DIMO | `dimo_correlated_data.csv` | ✅ |
| ENS | `ens_correlated_data.csv` | ✅ |

## Key Scripts Explained

### `scripts/run_full_regression.py`

Main analysis script that:
1. Loads data for each network
2. Runs OLS regression: `log(market_cap) = α + β * log(users)`
3. Calculates standard errors (HC3 robust)
4. Computes annualized returns
5. Classifies networks (Sustainable/Borderline/Unsustainable)

**Output**: `regression_results_expanded.csv`

### `scripts/generate_per_token_graphs.py`

Generates visualizations for each network:
- Time series: Users and market cap over time
- Log-log scatter: Shows Metcalfe's Law fit

**Output**: `paper/figures/per_token/{network}_*.pdf`

## Framework Usage

The framework can be used to analyze any blockchain network:

```python
from src.analysis.metcalfe_model import MetcalfeModel
import pandas as pd

# Load your data
df = pd.read_csv('your_network_data.csv')

# Fit model
model = MetcalfeModel()
results = model.fit(df['users'], df['market_cap'])

print(f"β = {results['beta']:.2f}")
print(f"R² = {results['r_squared']:.2f}")

# Classify
if results['beta'] > 1.0:
    print("Sustainable network effects")
elif results['beta'] < 1.0:
    print("Unsustainable network effects")
```

## Troubleshooting

### Missing Data Files

If a data file is missing:
1. Check `data/processed/` for alternative filenames
2. Re-run data collection scripts
3. Check Dune query execution status

### API Keys

Required API keys (set in `.env`):
- `DUNE_API_KEY`: For Dune Analytics queries
- `COINGECKO_API_KEY`: For market cap data

### LaTeX Compilation

If paper won't compile:
```bash
cd paper
latexmk -pdf -interaction=nonstopmode paper.tex
# Check paper.log for errors
```

## Citation

If you use this code or reproduce results, please cite:

```bibtex
@article{liu2025network,
  title={Network Effects Across Crypto Categories: A Metcalfe's Law Framework for Assessing Sustainability},
  author={Liu, Danny},
  journal={...},
  year={2025}
}
```

## License

See LICENSE file for details.

