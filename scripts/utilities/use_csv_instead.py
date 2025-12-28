#!/usr/bin/env python3
"""
Use CSV data instead of expensive Dune queries.
This avoids credit usage.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()

print("CSV Data Import")
print("=" * 60)
print("\nTo avoid Dune credit costs, you can use CSV data.")
print("\nCSV Format Required:")
print("  date,users,market_cap")
print("  2017-01-01,10000,1000000000")
print("  2017-01-02,12000,1200000000")
print("  ...")
print("\nExample usage:")
print("""
from src.data_collection import EthereumDataCollector

collector = EthereumDataCollector()
df = collector.load_from_csv("data/raw/ethereum_data.csv")
print(df.head())
""")

print("\n" + "=" * 60)
print("Alternative: Use sample data for testing")
print("=" * 60)
print("""
from src.data_collection import create_sample_data

df = create_sample_data()
# This creates realistic sample data for testing models
""")

