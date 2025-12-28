-- Chainlink (LINK) Daily Active Addresses (nonce >= 5)
-- Matches paper's methodology for oracle networks
-- Filters to addresses that have transferred LINK at least 5 times
-- LINK Contract: 0x514910771AF9Ca656af840dff83E8264EcF986CA

WITH link_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x514910771AF9Ca656af840dff83E8264EcF986CA  -- LINK token
    AND evt_block_time >= DATE '2017-09-01'  -- LINK launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'chainlink' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM link_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
