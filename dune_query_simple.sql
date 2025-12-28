-- Simple version without nonce filtering (for testing)
-- This will be much faster and we can add nonce filtering later

SELECT 
    DATE(block_time) as date,
    COUNT(DISTINCT "from") as active_addresses
FROM ethereum.transactions
WHERE block_time >= CAST('2017-01-01' AS TIMESTAMP)
  AND block_time < NOW()
GROUP BY DATE(block_time)
ORDER BY date;

