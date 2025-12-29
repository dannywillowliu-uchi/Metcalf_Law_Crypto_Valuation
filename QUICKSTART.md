# Quick Start Guide

This guide walks you through analyzing a blockchain network using Metcalfe's Law. We'll use Ethereum as an example.

## Prerequisites

- Python 3.9 or higher
- Basic command-line knowledge

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Get Your Data

You need two types of data:
1. **Active users** - from on-chain data (Dune Analytics)
2. **Market capitalization** - from CoinGecko API

### Option A: Use Pre-existing Data

If you have CSV files with columns `date`, `users`, and `market_cap`, skip to Step 3.

### Option B: Collect Data Yourself

#### Get Active Users from Dune Analytics

1. Go to [Dune Analytics](https://dune.com) and create a free account
2. Open the query file: `queries/dune_query_ethereum_active_addresses_nonce5.sql`
3. Copy and paste the SQL into Dune Analytics
4. Run the query
5. Export results as CSV
6. Save as `data/raw/dune/ethereum_active_addresses.csv`

#### Get Market Cap from CoinGecko

1. Get a free API key from [CoinGecko](https://www.coingecko.com/en/api)
2. Create a `.env` file in the project root:
   ```
   COINGECKO_API_KEY=your_api_key_here
   ```
3. Run the data collection script:
   ```bash
   python scripts/data_collection/collect_coingecko_safe.py ethereum
   ```

#### Merge the Data

```bash
python scripts/data_collection/correlate_dune_coingecko.py ethereum
```

This creates `data/processed/ethereum_correlated_data.csv` with columns:
- `date` - Date
- `users` - Active users (nonce >= 5)
- `market_cap` - Market capitalization in USD

## Step 3: Run the Analysis

### Simple Example Script

Run the Ethereum example:

```bash
python examples/analyze_ethereum.py
```

This will:
1. Load the Ethereum data
2. Fit the Metcalfe's Law model
3. Calculate beta coefficient
4. Classify the network (Sustainable/Borderline/Unsustainable)
5. Generate visualizations

### Using the Framework Directly

```python
from src.analysis.metcalfe_model import MetcalfeModel
import pandas as pd

# Load your data
df = pd.read_csv('data/processed/ethereum_correlated_data.csv')
df = df[(df['users'] > 0) & (df['market_cap'] > 0)]

# Fit the model
model = MetcalfeModel()
results = model.fit(df['users'], df['market_cap'])

# View results
print(f"Beta coefficient: {results['beta']:.2f}")
print(f"R-squared: {results['r_squared']:.2f}")
print(f"Standard error: {results['std_error']:.4f}")

# Classify
if results['beta'] > 1.0:
    print("Classification: Sustainable network effects")
elif results['beta'] < 1.0:
    print("Classification: Unsustainable network effects")
else:
    print("Classification: Borderline")
```

## Step 4: Interpret Results

### Beta Coefficient Meaning

- **Beta > 1.0**: Sustainable network effects. Token value scales super-linearly with users.
- **Beta = 1.0**: Linear scaling (Metcalfe's Law baseline).
- **Beta < 1.0**: Unsustainable. Token value doesn't scale well with user growth.

### Example: Ethereum Results

```
Beta coefficient: 1.52
R-squared: 0.85
Classification: Sustainable network effects
```

This means:
- For every 1% increase in active users, market cap increases by ~1.52%
- The model explains 85% of the variation in market cap
- Ethereum shows sustainable network effects

## Step 5: Generate Visualizations

```bash
python scripts/generate_per_token_graphs.py
```

This creates visualizations in `paper/figures/per_token/`:
- `ethereum_time_series.pdf` - Users and market cap over time
- `ethereum_log_log_scatter.pdf` - Log-log plot showing Metcalfe's Law fit

## Troubleshooting

### "File not found" errors

Make sure your data file is in `data/processed/` with the correct name format:
- `{network}_correlated_data.csv`

### "No module named" errors

Install dependencies:
```bash
pip install -r requirements.txt
```

### API rate limits

CoinGecko free tier has rate limits. If you hit limits:
- Wait a few minutes between requests
- Use the `collect_coingecko_safe.py` script which includes delays

## Next Steps

- Analyze other networks: See `REPRODUCTION_GUIDE.md` for full list
- Run robustness checks: `python scripts/robustness_analysis.py`
- Read the full paper: `paper/paper.pdf`

## Need Help?

- See `REPRODUCTION_GUIDE.md` for detailed instructions
- Check `STRUCTURE.md` for repository organization
- Review `examples/` directory for more examples

