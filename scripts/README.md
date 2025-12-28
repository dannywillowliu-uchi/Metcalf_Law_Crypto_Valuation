# Scripts Directory

This directory contains all analysis and utility scripts organized by function.

## Directory Structure

- **`analysis/`** - Network analysis scripts
  - `analyze_*.py` - Individual network analysis scripts
  - `validate_*.py` - Validation and testing scripts
  
- **`data_collection/`** - Data gathering scripts
  - `collect_*.py` - Network-specific data collection
  - `create_and_execute*.py` - Dune query execution
  - `fetch_*.py` - API data fetching utilities
  - `correlate_*.py` - Data merging scripts

- **`utilities/`** - Helper and utility scripts
  - `check_*.py` - Status checking scripts
  - `find_*.py` - Search utilities
  - Other utility scripts

## Main Analysis Scripts

- **`run_full_regression.py`** - Main regression analysis (generates Table 1)
- **`create_time_series_figure.py`** - Generates Figure 6 (time series)
- **`generate_per_token_graphs.py`** - Creates per-token visualizations
- **`robustness_analysis.py`** - Robustness checks and sensitivity analysis

## Usage

See [REPRODUCTION_GUIDE.md](../REPRODUCTION_GUIDE.md) for detailed usage instructions.

