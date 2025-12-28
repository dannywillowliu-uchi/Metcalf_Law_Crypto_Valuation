-- Lido (LDO) Daily Active Addresses (nonce >= 5)
-- Tracks addresses that have transferred LDO token at least 5 times
-- LDO Contract: 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32

WITH ldo_transfers AS (
  SELECT
    "from" AS address,
    evt_block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY evt_block_time) as nonce
  FROM erc20_ethereum.evt_Transfer
  WHERE contract_address = 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32  -- LDO token
    AND evt_block_time >= DATE '2021-01-05'  -- LDO token launch
    AND evt_block_time < NOW()
)
SELECT
  DATE(evt_block_time) AS day,
  'lido' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM ldo_transfers
WHERE nonce >= 5
GROUP BY DATE(evt_block_time)
ORDER BY DATE(evt_block_time);
