-- Ethereum Daily Active Addresses (nonce >= 5)
-- Matches paper's best model specification
-- Filters to only addresses that have made at least 5 transactions

WITH address_nonce AS (
  SELECT 
    "from" AS address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY block_time) as nonce
  FROM ethereum.transactions
  WHERE block_time >= DATE '2017-01-01'
    AND block_time < NOW()
)
SELECT
  DATE(block_time) AS day,
  'ethereum' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM address_nonce
WHERE nonce >= 5
GROUP BY DATE(block_time)
ORDER BY DATE(block_time);

