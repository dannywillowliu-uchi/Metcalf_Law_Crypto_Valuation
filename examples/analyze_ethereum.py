#!/usr/bin/env python3
"""
Example: Analyze Ethereum Network Effects

This script demonstrates how to use the Metcalfe's Law framework
to analyze Ethereum's network effects.

Usage:
    python examples/analyze_ethereum.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.metcalfe_model import MetcalfeModel


def load_ethereum_data():
    """Load Ethereum data from processed files."""
    # Try different possible file locations
    possible_files = [
        project_root / 'data' / 'processed' / 'ethereum_correlated_data.csv',
        project_root / 'data' / 'processed' / 'ethereum_correlated_data_nonce5_paper_range.csv',
    ]
    
    for file_path in possible_files:
        if file_path.exists():
            print(f"Loading data from: {file_path}")
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            return df
    
    raise FileNotFoundError(
        "Ethereum data file not found. Please ensure you have:\n"
        "  - data/processed/ethereum_correlated_data.csv\n"
        "  OR\n"
        "  - data/processed/ethereum_correlated_data_nonce5_paper_range.csv\n\n"
        "See QUICKSTART.md for instructions on collecting data."
    )


def analyze_ethereum():
    """Run Metcalfe's Law analysis on Ethereum."""
    print("=" * 70)
    print("Ethereum Network Effects Analysis")
    print("=" * 70)
    print()
    
    # Load data
    print("Step 1: Loading Ethereum data...")
    try:
        df = load_ethereum_data()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return
    
    # Filter valid data
    df = df[(df['users'] > 0) & (df['market_cap'] > 0)].copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"  Loaded {len(df)} data points")
    print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"  Users range: {df['users'].min():,.0f} to {df['users'].max():,.0f}")
    print(f"  Market cap range: ${df['market_cap'].min()/1e9:.2f}B to ${df['market_cap'].max()/1e9:.2f}B")
    print()
    
    # Fit model
    print("Step 2: Fitting Metcalfe's Law model...")
    model = MetcalfeModel()
    results = model.fit(df['users'], df['market_cap'])
    print("  Model fitted successfully")
    print()
    
    # Display results
    print("Step 3: Results")
    print("-" * 70)
    print(f"Beta coefficient (β):     {results['beta']:.4f}")
    print(f"Alpha coefficient (α):    {results['alpha']:.4f}")
    print(f"R-squared:                {results['r_squared']:.4f}")
    print(f"Standard error:           {results['std_error']:.4f}")
    print(f"Number of observations:   {len(df)}")
    print()
    
    # Classification
    print("Step 4: Classification")
    print("-" * 70)
    beta = results['beta']
    if beta > 1.0:
        classification = "Sustainable"
        explanation = (
            "Ethereum shows sustainable network effects. Token value scales "
            "super-linearly with user growth, indicating strong token-utility coupling."
        )
    elif beta < 1.0:
        classification = "Unsustainable"
        explanation = (
            "Ethereum shows unsustainable network effects. Token value does not "
            "scale well with user growth, suggesting weak token-utility coupling."
        )
    else:
        classification = "Borderline"
        explanation = (
            "Ethereum shows linear scaling (baseline Metcalfe's Law). "
            "Token value scales proportionally with user growth."
        )
    
    print(f"Classification: {classification}")
    print(f"\nInterpretation:")
    print(f"  {explanation}")
    print()
    
    # Comparison to paper
    print("Step 5: Comparison to Published Results")
    print("-" * 70)
    paper_beta = 1.52
    paper_r2 = 0.85
    print(f"Published beta:  {paper_beta:.2f}")
    print(f"Your beta:       {results['beta']:.2f}")
    print(f"Difference:      {abs(results['beta'] - paper_beta):.2f}")
    print()
    print(f"Published R²:   {paper_r2:.2f}")
    print(f"Your R²:         {results['r_squared']:.2f}")
    print(f"Difference:      {abs(results['r_squared'] - paper_r2):.2f}")
    print()
    
    if abs(results['beta'] - paper_beta) < 0.1:
        print("✓ Your results closely match the published results!")
    else:
        print("⚠ Note: Your results differ from published results.")
        print("  This may be due to:")
        print("    - Different date ranges")
        print("    - Different data sources")
        print("    - Data updates since publication")
    print()
    
    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Ethereum exhibits {classification.lower()} network effects with β = {results['beta']:.2f}.")
    print(f"The model explains {results['r_squared']*100:.1f}% of the variation in market cap.")
    print()
    print("To generate visualizations, run:")
    print("  python scripts/generate_per_token_graphs.py")
    print("=" * 70)


if __name__ == '__main__':
    try:
        analyze_ethereum()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

