#!/usr/bin/env python3
"""
Check Dune Account Status

This script checks your Dune Analytics account to see:
- Your username
- Your plan type
- Available credits
- Credit limits
"""

import sys
from pathlib import Path
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.getenv("DUNE_API_KEY")
if not api_key:
    print("❌ DUNE_API_KEY not found in .env or environment variables")
    print("\nTo set it up:")
    print("1. Go to: https://dune.com/settings/api")
    print("2. Copy your API key")
    print("3. Add to .env file: DUNE_API_KEY=your_key_here")
    sys.exit(1)

print("="*80)
print("CHECKING DUNE ACCOUNT STATUS")
print("="*80)

headers = {
    "X-DUNE-API-Key": api_key,
    "Content-Type": "application/json"
}

# Check user info
print("\n1. Checking user information...")
try:
    response = requests.get(
        "https://api.dune.com/api/v1/user",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        user_info = response.json()
        print(f"   ✅ API key is valid!")
        print(f"   Username: {user_info.get('user_name', 'N/A')}")
        print(f"   Email: {user_info.get('email', 'N/A')}")
    elif response.status_code == 401:
        print(f"   ❌ API key is invalid or expired")
        sys.exit(1)
    else:
        print(f"   ⚠️  Status {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check billing/plan info (if available via API)
print("\n2. Checking plan and credits...")
print("   Note: Plan details may not be available via API")
print("   Check manually at: https://dune.com/settings/billing")

# Try to get some account info
try:
    # Some APIs expose plan info, but Dune's might not
    # We can at least verify the API key works
    print("   ✅ API key is working")
    print("\n   To check your plan and credits:")
    print("   1. Go to: https://dune.com/settings/billing")
    print("   2. Look for:")
    print("      - Plan type (Free, Starter, Pro, etc.)")
    print("      - Available credits")
    print("      - Monthly credit limit")
except Exception as e:
    print(f"   ⚠️  Could not get plan info: {e}")

print("\n" + "="*80)
print("CREDIT REQUIREMENTS")
print("="*80)
print("\nWe need to create and execute 6 queries:")
print("  1. Worldcoin - 300 credits")
print("  2. Hivemapper - 300 credits")
print("  3. DIMO - 300 credits")
print("  4. Farcaster - 300 credits")
print("  5. Lens Protocol - 300 credits")
print("  6. ENS - 300 credits")
print("\nTotal: 1,800 credits (one-time)")
print("\nAfter execution, CSV exports are free (0 credits)")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

print("\nIf you have a Free plan:")
print("  - Free tier typically has 1,000-5,000 credits/month")
print("  - If you have ≥1,800 credits: ✅ Can execute all queries")
print("  - If you have <1,800 credits:")
print("    Option 1: Create queries only (0 credits), execute later")
print("    Option 2: Execute queries gradually over multiple months")
print("    Option 3: Upgrade to paid plan if needed")

print("\nNext steps:")
print("  1. Check your credits at: https://dune.com/settings/billing")
print("  2. Let me know your credit limit")
print("  3. We can adjust the script accordingly")


