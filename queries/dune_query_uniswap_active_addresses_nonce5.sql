-- Uniswap Daily Active Addresses (nonce >= 5)
-- Matches paper's methodology for DeFi/DEX networks
-- Filters to addresses that have performed at least 5 swaps
-- Uses Uniswap v2 and v3 swap events

WITH swaps AS (
  -- Uniswap V2 swaps
  SELECT
    "to" AS address,
    evt_block_time
  FROM uniswap_v2_ethereum.Pair_evt_Swap
  WHERE evt_block_time >= DATE '2020-05-01'  -- V2 launch

  UNION ALL

  -- Uniswap V3 swaps
  SELECT
    recipient AS address,
    evt_block_time
  FROM uniswap_v3_ethereum.Pair_evt_Swap
  WHERE evt_block_time >= DATE '2021-05-01'  -- V3 launch
),
address_nonce AS (
  SELECT
    address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY address ORDER BY evt_block_time) as nonce
  FROM swaps
  WHERE evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'uniswap' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM address_nonce
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
