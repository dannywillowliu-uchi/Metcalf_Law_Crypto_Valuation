#!/usr/bin/env python3
"""
Test Explorer APIs

Tests various API endpoints for Filecoin and Arweave explorers
to find the correct way to access data.
"""

import requests
import json

def test_filfox_endpoints():
    """Test various Filfox API endpoints"""
    print("="*60)
    print("TESTING FILFOX API ENDPOINTS")
    print("="*60)
    
    base = "https://filfox.info"
    endpoints = [
        "/api/v1/stats",
        "/api/v1/miners",
        "/api/v1/statistics",
        "/api/v1/network/stats",
        "/api/v1/network/statistics",
        "/api/v1/storage-providers",
        "/api/v1/miners/count",
    ]
    
    for endpoint in endpoints:
        url = f"{base}{endpoint}"
        print(f"\nTesting: {endpoint}")
        try:
            r = requests.get(url, timeout=5)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  ✅ Success! Keys: {list(data.keys())[:5]}")
                    if 'minerCount' in data or 'miners' in data or 'count' in data:
                        print(f"  📊 Found data!")
                except:
                    print(f"  ⚠️  Not JSON: {r.text[:100]}")
            else:
                print(f"  ❌ Error: {r.text[:50]}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")

def test_viewblock_endpoints():
    """Test various ViewBlock API endpoints"""
    print("\n" + "="*60)
    print("TESTING VIEWBLOCK API ENDPOINTS")
    print("="*60)
    
    base = "https://api.viewblock.io"
    endpoints = [
        "/v1/arweave/stats",
        "/v1/arweave/network",
        "/v1/arweave/miners",
        "/v1/arweave/statistics",
        "/arweave/stats",
        "/arweave/network",
    ]
    
    for endpoint in endpoints:
        url = f"{base}{endpoint}"
        print(f"\nTesting: {endpoint}")
        try:
            r = requests.get(url, timeout=5)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"  ✅ Success! Keys: {list(data.keys())[:5]}")
                except:
                    print(f"  ⚠️  Not JSON: {r.text[:100]}")
            else:
                print(f"  ❌ Error: {r.text[:50]}")
        except Exception as e:
            print(f"  ❌ Exception: {e}")

def test_alternative_sources():
    """Test alternative data sources"""
    print("\n" + "="*60)
    print("TESTING ALTERNATIVE DATA SOURCES")
    print("="*60)
    
    # Filecoin - try Messari, CoinGecko, etc.
    print("\nFilecoin alternatives:")
    alt_sources = [
        ("Messari", "https://api.messari.io/api/v1/assets/filecoin/metrics"),
        ("Filecoin Foundation", "https://stats.filecoin.io/api/v1/stats"),
    ]
    
    for name, url in alt_sources:
        print(f"\n  {name}: {url}")
        try:
            r = requests.get(url, timeout=5)
            print(f"    Status: {r.status_code}")
            if r.status_code == 200:
                print(f"    ✅ Works!")
        except Exception as e:
            print(f"    ❌ {e}")

if __name__ == '__main__':
    test_filfox_endpoints()
    test_viewblock_endpoints()
    test_alternative_sources()

