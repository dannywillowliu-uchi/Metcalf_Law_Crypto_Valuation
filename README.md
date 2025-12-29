# Network Effects Analyzer

A Metcalfe's Law Framework for Assessing Token Value Sustainability Across Crypto Categories

An open-source Python framework for analyzing network effects in blockchain networks using Metcalfe's Law. This repository contains the complete code, data, and analysis for the paper:

**"Network Effects Across Crypto Categories: A Metcalfe's Law Framework for Assessing Sustainability"**

## Key Findings

- 100% success rate: All five networks with beta > 1 (Ethereum, Render, Livepeer, Chainlink, Optimism) delivered strong returns (43-132%/year)
- Token-utility coupling matters: Networks where tokens are required for usage show sustainable network effects
- Protocol success does not imply token success: Major DeFi protocols (Aave, Uniswap, Compound) show low beta despite protocol success

## Results Summary

| Network | Category | Beta | Classification | Returns |
|---------|----------|------|----------------|---------|
| Ethereum | Payment (L1) | 1.52 | Sustainable | +68%/yr |
| Render | Compute | 1.39 | Sustainable | +132%/yr |
| Livepeer | Compute | 1.32 | Sustainable | +89%/yr |
| Chainlink | Oracle | 1.21 | Sustainable | +76%/yr |
| Optimism | Payment (L2) | 1.11 | Sustainable | +43%/yr |
| Uniswap | DEX | 0.36 | Unsustainable | +43%/yr* |
| Arbitrum | Payment (L2) | 0.39 | Unsustainable | -13%/yr |
| ENS | Identity | -0.25 | Unsustainable | -21%/yr |

*Uniswap's returns were market-driven, not network-effect driven

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/network-effects-analyzer.git
cd network-effects-analyzer
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Analyze Ethereum (Example)

The easiest way to get started is with the Ethereum example:

```bash
python examples/analyze_ethereum.py
```

This will:
- Load Ethereum data
- Fit the Metcalfe's Law model
- Display beta coefficient and classification
- Compare to published results

See [QUICKSTART.md](QUICKSTART.md) for step-by-step instructions.

### Reproduce Paper Results

```bash
# Run main regression analysis (generates Table 1)
python scripts/run_full_regression.py

# Generate paper figures
python scripts/create_time_series_figure.py
python scripts/generate_per_token_graphs.py

# Compile paper
cd paper && latexmk -pdf paper.tex
```

See [REPRODUCTION_GUIDE.md](REPRODUCTION_GUIDE.md) for detailed instructions.

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
├── scripts/                       # Analysis and utility scripts
│   ├── run_full_regression.py     # Main regression analysis
│   ├── create_time_series_figure.py
│   ├── generate_per_token_graphs.py
│   ├── robustness_analysis.py
│   ├── analysis/                  # Network analysis scripts
│   ├── data_collection/           # Data gathering scripts
│   └── utilities/                 # Helper scripts
├── queries/                       # Dune Analytics SQL queries
│   ├── dune_query_*.sql          # Network-specific queries
│   └── dune_query_ids.json       # Query ID mapping
├── src/                           # Framework code
│   ├── analysis/
│   │   ├── metcalfe_model.py      # Core Metcalfe's Law model
│   │   └── markov_switching.py    # Markov-switching extension
│   └── data_collection/           # Data collection utilities
└── tests/                         # Test suite
    ├── unit/                      # Unit tests
    └── integration/               # Integration tests
```

## Framework Usage

Analyze any blockchain network:

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
    print("✅ Sustainable network effects")
elif results['beta'] < 1.0:
    print("❌ Unsustainable network effects")
```

## Per-Token Visualizations

The repository includes detailed visualizations for each network:

- **Time Series**: Users and market cap over time
- **Log-Log Scatter**: Metcalfe's Law fit visualization

Located in `paper/figures/per_token/`:
- `{network}_time_series.pdf`
- `{network}_log_log_scatter.pdf`

## Documentation

- [REPRODUCTION_GUIDE.md](REPRODUCTION_GUIDE.md): Complete guide to reproducing all results
- [paper/paper.pdf](paper/paper.pdf): Full academic paper
- [docs/](docs/): Additional documentation

## Data Sources

- On-Chain Data: [Dune Analytics](https://dune.com) (SQL queries included)
- Market Data: [CoinGecko API](https://www.coingecko.com/en/api)

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

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Dune Analytics for on-chain data access
- CoinGecko for market data
- The open-source crypto data community

---

**Note**: This framework measures *token value* sustainability, not protocol quality. A successful protocol can have low-β tokens if users don't need to hold the token to participate.
