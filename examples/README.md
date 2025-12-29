# Examples

This directory contains example scripts demonstrating how to use the framework.

## Available Examples

### analyze_ethereum.py

Complete example analyzing Ethereum's network effects.

**Usage:**
```bash
python examples/analyze_ethereum.py
```

**What it does:**
1. Loads Ethereum data from `data/processed/`
2. Fits Metcalfe's Law model
3. Displays beta coefficient, R-squared, and classification
4. Compares results to published values

**Requirements:**
- Ethereum data file: `data/processed/ethereum_correlated_data.csv`
- See `QUICKSTART.md` for instructions on collecting data

## Creating Your Own Example

To analyze a different network:

1. **Get the data:**
   ```bash
   # Collect on-chain data from Dune Analytics
   # Collect market cap from CoinGecko
   # Merge using: python scripts/data_collection/correlate_dune_coingecko.py {network}
   ```

2. **Create analysis script:**
   ```python
   from src.analysis.metcalfe_model import MetcalfeModel
   import pandas as pd
   
   # Load data
   df = pd.read_csv('data/processed/{network}_correlated_data.csv')
   df = df[(df['users'] > 0) & (df['market_cap'] > 0)]
   
   # Fit model
   model = MetcalfeModel()
   results = model.fit(df['users'], df['market_cap'])
   
   # Display results
   print(f"Beta: {results['beta']:.2f}")
   print(f"R²: {results['r_squared']:.2f}")
   
   # Classify
   if results['beta'] > 1.0:
       print("Sustainable network effects")
   else:
       print("Unsustainable network effects")
   ```

3. **Run your script:**
   ```bash
   python examples/analyze_{network}.py
   ```

## Need Help?

- See [QUICKSTART.md](../QUICKSTART.md) for detailed instructions
- See [REPRODUCTION_GUIDE.md](../REPRODUCTION_GUIDE.md) for complete documentation

