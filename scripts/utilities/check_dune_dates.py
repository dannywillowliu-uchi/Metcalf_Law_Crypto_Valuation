#!/usr/bin/env python3
import pandas as pd
from pathlib import Path

df = pd.read_csv('data/processed/ethereum_active_addresses_3488164.csv', parse_dates=['date'])

print(f'Total records: {len(df)}')
print(f'Date range: {df["date"].min()} to {df["date"].max()}')
print(f'\nFirst 5 rows:')
print(df.head())
print(f'\nLast 5 rows:')
print(df.tail())

print(f'\nAny dates > 2024-01-01:')
future = df[df['date'] > '2024-01-01']
print(f'Count: {len(future)}')
if len(future) > 0:
    print(future.head(10))

print(f'\nDate distribution by year:')
df['year'] = df['date'].dt.year
print(df['year'].value_counts().sort_index())

