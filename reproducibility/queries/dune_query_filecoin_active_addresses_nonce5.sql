-- Filecoin Daily Active Addresses (nonce ≥ 5)
-- Matches paper's methodology for payment networks
-- Filters to only addresses that have made at least 5 transactions

-- This query counts active addresses on Filecoin blockchain
-- with nonce filtering to match the original paper's approach

WITH address_nonce AS (
  SELECT 
    "from" AS address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY block_time) as nonce
  FROM filecoin.transactions
  WHERE block_time >= TIMESTAMP '2020-10-15 00:00:00'  -- Filecoin mainnet launch
    AND block_time < NOW()
)
SELECT
  DATE(block_time) AS day,
  'filecoin' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM address_nonce
WHERE nonce >= 5
GROUP BY DATE(block_time)
ORDER BY DATE(block_time);


