# Repository Structure

This document describes the organization of the Network Effects Analyzer repository.

## Top-Level Directories

### paper/
Academic paper and all associated figures.
- `paper.tex` - LaTeX source
- `paper.pdf` - Compiled PDF
- `references.bib` - Bibliography
- `figures/` - All paper figures including per-token visualizations

### src/
Core framework code (installable Python package).
- `analysis/` - Metcalfe's Law and Markov-switching models
- `data_collection/` - Data collection utilities
- `utils/` - Helper functions
- `visualization/` - Plotting utilities

### reproducibility/
Framework usage documentation and scripts. Contains complete guide to using the framework.
- `README.md` - Framework usage guide with API documentation
- `scripts/` - Analysis and data collection scripts
- `queries/` - SQL queries for data collection

### scripts/
Analysis and utility scripts organized by function.
- Root level: Main analysis scripts
  - `run_full_regression.py` - Generates Table 1
  - `create_time_series_figure.py` - Generates Figure 6
  - `generate_per_token_graphs.py` - Creates per-token visualizations
  - `robustness_analysis.py` - Robustness checks
- `analysis/` - Network-specific analysis scripts
- `data_collection/` - Data gathering and processing scripts
- `utilities/` - Helper and utility scripts

### queries/
Dune Analytics SQL queries for extracting on-chain data.
- `dune_query_*.sql` - Network-specific queries
- `dune_query_ids.json` - Query ID mapping

### data/
All data files.
- `processed/` - Cleaned, merged datasets
- `raw/` - Raw data sources (gitignored)
- `cache/` - API response cache (gitignored)

### tests/
Test suite.
- `unit/` - Unit tests for framework components
- `integration/` - Integration tests for scripts

### docs/
Additional documentation.
- `api.md` - API documentation

## Key Files

### Root Level
- `README.md` - Main repository README
- `REPRODUCTION_GUIDE.md` - Complete reproduction instructions
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Package configuration
- `LICENSE` - MIT License
- `.gitignore` - Git ignore rules

## Navigation Guide

To reproduce the paper:
1. See `REPRODUCTION_GUIDE.md`
2. Run `scripts/run_full_regression.py`
3. Generate figures with `scripts/create_time_series_figure.py`

To use the framework:
1. See `README.md` Framework section
2. See `reproducibility/README.md` for complete framework usage guide
3. Import from `src.analysis.metcalfe_model`
4. See `examples/analyze_ethereum.py` for example usage

To collect new data:
1. Use queries in `queries/`
2. Run scripts in `scripts/data_collection/`
3. See `REPRODUCTION_GUIDE.md` Step 1

To run tests:
```bash
pytest tests/
```

