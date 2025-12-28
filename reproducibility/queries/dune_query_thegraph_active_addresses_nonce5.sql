-- The Graph (GRT) Daily Active Addresses (nonce >= 5)
-- Matches paper's methodology for indexing/data networks
-- Filters to addresses that have transferred GRT at least 5 times
-- GRT Contract: 0xc944E90C64B2c07662A292be6244BDf05Cda44a7

WITH grt_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0xc944E90C64B2c07662A292be6244BDf05Cda44a7  -- GRT token
    AND evt_block_time >= DATE '2020-12-17'  -- GRT mainnet launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'thegraph' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM grt_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
