# Dune Analytics Queries

This directory contains SQL queries for extracting on-chain user activity data from Dune Analytics.

## Query Files

Each network has a corresponding SQL query file:
- `dune_query_ethereum_active_addresses_nonce5.sql`
- `dune_query_uniswap_active_addresses_nonce5.sql`
- etc.

## Query Configuration

- **`dune_query_ids.json`** - Maps network names to Dune query IDs

## Active User Definition

All queries use the **nonce ≥ 5** threshold to filter out:
- Airdrop farmers
- Bot transactions
- Testing/exploration addresses
- Sybil attacks

This ensures we count only genuine network participants.

## Usage

1. Execute queries on [Dune Analytics](https://dune.com)
2. Export results as CSV
3. Use data collection scripts to merge with market cap data

See [REPRODUCTION_GUIDE.md](../REPRODUCTION_GUIDE.md) for detailed instructions.

