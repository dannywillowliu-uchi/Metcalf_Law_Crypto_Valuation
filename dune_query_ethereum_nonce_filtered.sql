-- Ethereum Daily Active Addresses (nonce ≥ 5)
-- This matches the paper's best model specification
-- Filters to only addresses that have made at least 5 transactions

SELECT 
    DATE(block_time) as date,
    COUNT(DISTINCT address) as active_addresses
FROM (
    -- Get all addresses that sent transactions, with their transaction count up to that date
    SELECT 
        block_time,
        "from" as address,
        ROW_NUMBER() OVER (PARTITION BY "from" ORDER BY block_time) as nonce
    FROM ethereum.transactions
    WHERE block_time >= '2017-01-01'::timestamp
      AND block_time < NOW()
) t
WHERE nonce >= 5  -- Filter by nonce threshold (per paper: nonce ≥ 5 is optimal)
GROUP BY DATE(block_time)
ORDER BY date;

