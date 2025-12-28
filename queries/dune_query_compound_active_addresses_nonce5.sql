-- Compound (COMP) Daily Active Addresses (nonce >= 5)
-- Tracks addresses that have transferred COMP token at least 5 times
-- COMP Contract: 0xc00e94Cb662C3520282E6f5717214004A7f26888

WITH comp_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0xc00e94Cb662C3520282E6f5717214004A7f26888  -- COMP token
    AND evt_block_time >= DATE '2020-06-15'  -- COMP token launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'compound' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM comp_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
