-- Polygon Daily Active Addresses (nonce >= 5)
-- Matches paper's methodology for L2 networks
-- Filters to addresses that have performed at least 5 transactions on Polygon

WITH address_txns AS (
  SELECT
    "from" AS address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY block_time) as nonce
  FROM polygon.transactions
  WHERE block_time >= DATE '2020-05-01'  -- Polygon mainnet launch
    AND block_time < NOW()
    AND success = true
)
SELECT
  DATE(block_time) AS day,
  'polygon' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM address_txns
WHERE nonce >= 5
GROUP BY DATE(block_time)
ORDER BY DATE(block_time);
