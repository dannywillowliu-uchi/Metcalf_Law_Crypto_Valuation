#!/usr/bin/env python3
import requests
import pandas as pd
import io
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('DUNE_API_KEY')
url = f'https://api.dune.com/api/v1/query/3488164/results/csv?limit=1000'
headers = {'X-Dune-API-Key': api_key}

r = requests.get(url, headers=headers)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    df = pd.read_csv(io.StringIO(r.text))
    print(f'\nRecords: {len(df)}')
    print(f'Columns: {list(df.columns)}')
    
    # Check date column (might be 'day' or 'date')
    date_col = 'day' if 'day' in df.columns else 'date' if 'date' in df.columns else None
    
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
        print(f'\nDate range: {df[date_col].min()} to {df[date_col].max()}')
        print(f'\nYears in data: {sorted(df[date_col].dt.year.unique())}')
        
        # Check for 2025 dates
        future = df[df[date_col] > '2024-12-31']
        print(f'\nDates > 2024-12-31: {len(future)}')
        if len(future) > 0:
            print('\nFuture dates found:')
            print(future[[date_col] + [c for c in df.columns if c != date_col][:3]].head(10))
        
        print('\nLast 10 rows:')
        print(df.tail(10))
        
        print('\nFirst 10 rows:')
        print(df.head(10))
    else:
        print('\nNo date column found')
        print(df.head())
else:
    print(f'Error: {r.text[:500]}')

