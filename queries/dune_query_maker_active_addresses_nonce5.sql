-- MakerDAO (MKR) Daily Active Addresses (nonce >= 5)
-- Tracks addresses that have transferred MKR token at least 5 times
-- MKR Contract: 0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2

WITH mkr_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2  -- MKR token
    AND evt_block_time >= DATE '2017-12-01'  -- MKR token launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'maker' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM mkr_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
