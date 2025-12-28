-- SushiSwap (SUSHI) Daily Active Addresses (nonce >= 5)
-- Tracks addresses that have transferred SUSHI token at least 5 times
-- SUSHI Contract: 0x6B3595068778DD592e39A122f4f5a5cF09C90fE2

WITH sushi_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x6B3595068778DD592e39A122f4f5a5cF09C90fE2  -- SUSHI token
    AND evt_block_time >= DATE '2020-08-28'  -- SUSHI token launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'sushiswap' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM sushi_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
