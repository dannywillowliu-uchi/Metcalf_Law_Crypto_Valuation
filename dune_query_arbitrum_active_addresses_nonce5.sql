-- Arbitrum Daily Active Addresses (nonce >= 5)
-- Matches paper's methodology for L2 networks
-- Filters to addresses that have performed at least 5 transactions on Arbitrum

WITH address_txns AS (
  SELECT
    "from" AS address,
    block_time,
    ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY block_time) as nonce
  FROM arbitrum.transactions
  WHERE block_time >= DATE '2021-08-01'  -- Arbitrum mainnet launch
    AND block_time < NOW()
    AND success = true
)
SELECT
  DATE(block_time) AS day,
  'arbitrum' AS blockchain,
  COUNT(DISTINCT CASE WHEN nonce >= 5 THEN address END) AS active_addresses
FROM address_txns
WHERE nonce >= 5
GROUP BY DATE(block_time)
ORDER BY DATE(block_time);
