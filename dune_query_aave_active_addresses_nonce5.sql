-- Aave (AAVE) Daily Active Addresses (nonce >= 5)
-- Tracks addresses that have transferred AAVE token at least 5 times
-- AAVE Contract: 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9

WITH aave_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9  -- AAVE token
    AND evt_block_time >= DATE '2020-09-24'  -- AAVE token launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'aave' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM aave_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
