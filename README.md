# Network Effects Analyzer

A Metcalfe's Law Framework for Assessing Token Value Sustainability Across Crypto Categories

This repository contains two primary components:

1. **Academic Paper**: Complete research paper analyzing network effects across 15 blockchain networks
2. **Open-Source Framework**: Python framework for analyzing network effects in any blockchain network

## Paper

**"Network Effects Across Crypto Categories: A Metcalfe's Law Framework for Assessing Sustainability"**

[Read the paper](paper/paper.pdf) | [View LaTeX source](paper/paper.tex)

### Key Findings

- 100% success rate: All five networks with beta > 1 (Ethereum, Render, Livepeer, Chainlink, Optimism) delivered strong returns (43-132%/year)
- Token-utility coupling matters: Networks where tokens are required for usage show sustainable network effects
- Protocol success does not imply token success: Major DeFi protocols (Aave, Uniswap, Compound) show low beta despite protocol success

### Results Summary

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

## Framework

The open-source framework enables analysis of network effects for any blockchain network using Metcalfe's Law.

### Quick Start

```python
from src.analysis.metcalfe_model import MetcalfeModel
import pandas as pd

# Load your data
df = pd.read_csv('your_network_data.csv')

# Fit model
model = MetcalfeModel()
results = model.fit(df['users'], df['market_cap'])

print(f"Beta = {results['beta']:.2f}")
print(f"R² = {results['r_squared']:.2f}")

# Classify
if results['beta'] > 1.0:
    print("Sustainable network effects")
elif results['beta'] < 1.0:
    print("Unsustainable network effects")
```

### Example: Analyze Ethereum

```bash
python examples/analyze_ethereum.py
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

### Framework Usage Documentation

Complete framework usage information, including data collection workflows and analysis scripts, is available in the [reproducibility](reproducibility/) folder:

- [Framework Usage Guide](reproducibility/README.md) - Complete guide to using the framework
- [Reproduction Scripts](reproducibility/scripts/) - Scripts for data collection and analysis
- [SQL Queries](reproducibility/queries/) - Dune Analytics queries for on-chain data

## Installation

```bash
git clone https://github.com/yourusername/network-effects-analyzer.git
cd network-effects-analyzer
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Reproducing Paper Results

To reproduce all results from the paper:

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
├── paper/                          # Academic paper (LaTeX source and PDF)
│   ├── paper.tex                  # Main paper source
│   ├── paper.pdf                  # Compiled paper
│   ├── references.bib             # Bibliography
│   └── figures/                   # All paper figures
│       ├── fig1_network_effects_comparison.pdf
│       ├── fig4_sustainable_vs_unsustainable.pdf
│       ├── fig6_time_series_users_mcap.pdf
│       └── per_token/             # Per-token visualizations
├── src/                           # Framework code (installable package)
│   ├── analysis/
│   │   ├── metcalfe_model.py      # Core Metcalfe's Law model
│   │   └── markov_switching.py    # Markov-switching extension
│   └── data_collection/           # Data collection utilities
├── reproducibility/               # Framework usage documentation and scripts
│   ├── README.md                  # Framework usage guide
│   ├── scripts/                   # Analysis and data collection scripts
│   └── queries/                   # SQL queries for data collection
├── examples/                      # Example scripts
│   └── analyze_ethereum.py        # Ethereum analysis example
├── scripts/                       # Main analysis scripts
│   ├── run_full_regression.py     # Main regression analysis
│   ├── create_time_series_figure.py
│   ├── generate_per_token_graphs.py
│   └── robustness_analysis.py
├── queries/                       # Dune Analytics SQL queries
├── data/                          # Data files
└── tests/                         # Test suite
```

## Documentation

- [Paper](paper/paper.pdf) - Full academic paper
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide for beginners
- [REPRODUCTION_GUIDE.md](REPRODUCTION_GUIDE.md) - Complete reproduction instructions
- [Framework Usage](reproducibility/README.md) - Framework usage documentation
- [STRUCTURE.md](STRUCTURE.md) - Repository structure guide

## Data Sources

- On-Chain Data: [Dune Analytics](https://dune.com) (SQL queries included)
- Market Data: [CoinGecko API](https://www.coingecko.com/en/api)


**Note**: This framework measures *token value* sustainability, not protocol quality. A successful protocol can have low-beta tokens if users don't need to hold the token to participate.
