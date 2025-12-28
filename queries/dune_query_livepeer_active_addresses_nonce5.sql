-- Livepeer (LPT) Daily Active Addresses (nonce >= 5)
-- Matches paper's methodology for compute networks
-- Filters to addresses that have transferred LPT at least 5 times
-- LPT Contract: 0x58b6A8A3302369DAEc383334672404Ee733aB239

WITH lpt_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x58b6A8A3302369DAEc383334672404Ee733aB239  -- LPT token
    AND evt_block_time >= DATE '2018-04-01'  -- LPT mainnet launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'livepeer' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM lpt_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
