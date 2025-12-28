#!/usr/bin/env python3
"""
Safe CoinGecko Data Collection

Uses the safe wrapper to collect data while tracking API usage.
Always checks cache first to minimize API calls.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.data_collection.coingecko_safe import CoinGeckoSafe
import pandas as pd
from datetime import datetime

# Networks to collect (with CoinGecko IDs)
NETWORKS = {
    'render': 'render-token',
    'akash': 'akash-network',
    'bittensor': 'bittensor',
    'helium': 'helium',
    'filecoin': 'filecoin',
    'arweave': 'arweave',
    # Token-based networks
    'worldcoin': 'worldcoin-wld',
    'hivemapper': 'hivemapper',
    'dimo': 'dimo',
}

def collect_all_networks(days='max', use_cache=True, force_refresh=False):
    """
    Collect market cap data for all networks.
    
    Parameters
    ----------
    days : int or str
        Number of days or 'max' for full history (requires paid plan)
    use_cache : bool
        Use cached data if available (default: True)
    force_refresh : bool
        Force refresh even if cache exists (default: False)
    """
    print("="*60)
    print("SAFE COINGECKO DATA COLLECTION")
    print("="*60)
    print(f"\nNetworks: {len(NETWORKS)}")
    print(f"Days: {days}")
    print(f"Use Cache: {use_cache}")
    print(f"Force Refresh: {force_refresh}")
    print(f"\n⚠️  This will make API calls. Each call is logged and cached.")
    
    # Initialize safe wrapper
    cg = CoinGeckoSafe()
    
    # Show current usage
    cg.print_usage_stats()
    
    # Confirm before proceeding
    if force_refresh:
        print("\n⚠️  WARNING: Force refresh is enabled - will make API calls even if cache exists!")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    results = {}
    output_dir = Path(__file__).parent / "data" / "processed" / "coingecko"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("COLLECTING DATA")
    print(f"{'='*60}\n")
    
    for network_name, coin_id in NETWORKS.items():
        print(f"[{network_name.upper()}] {coin_id}")
        
        df = cg.get_market_chart(
            coin_id=coin_id,
            days=days,
            use_cache=use_cache,
            force_refresh=force_refresh
        )
        
        if df is not None:
            results[network_name] = df
            
            # Save to processed directory
            output_file = output_dir / f"{network_name}_market_cap.csv"
            df.to_csv(output_file, index=False)
            print(f"  💾 Saved: {output_file.name}")
            
            # Show summary
            print(f"  📊 Records: {len(df)}")
            print(f"  📅 Range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
            print(f"  💰 Market Cap: ${df['market_cap'].min():,.0f} to ${df['market_cap'].max():,.0f}")
        else:
            print(f"  ❌ Failed to collect data")
        
        print()  # Blank line
    
    # Show final usage stats
    print(f"{'='*60}")
    cg.print_usage_stats()
    
    # Summary
    print(f"\n{'='*60}")
    print("COLLECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Networks collected: {len(results)}/{len(NETWORKS)}")
    print(f"Total API calls made: {cg.call_count}")
    print(f"Files saved to: {output_dir}")
    
    if results:
        print(f"\n✅ Successfully collected data for:")
        for name in results.keys():
            print(f"   - {name}")
    
    return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Safe CoinGecko data collection')
    parser.add_argument('--days', type=str, default='max',
                       help='Number of days or "max" for full history (default: max)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Disable cache (force API calls)')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Force refresh even if cache exists')
    
    args = parser.parse_args()
    
    # Convert days to int if not 'max'
    days = args.days if args.days == 'max' else int(args.days)
    
    collect_all_networks(
        days=days,
        use_cache=not args.no_cache,
        force_refresh=args.force_refresh
    )

if __name__ == '__main__':
    main()

