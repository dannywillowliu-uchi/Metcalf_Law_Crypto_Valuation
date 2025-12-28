-- Ethereum Daily Active Addresses Query for Dune Analytics
-- This query counts unique addresses that sent or received transactions each day
-- Use this in Dune Analytics to get historical active addresses data

-- Option 1: Simple version (counts unique addresses from transactions)
SELECT 
    DATE(block_time) as date,
    COUNT(DISTINCT "from") as active_addresses
FROM ethereum.transactions
WHERE block_time >= '2017-01-01'
  AND block_time < CURRENT_DATE
GROUP BY DATE(block_time)
ORDER BY date;

-- Option 2: More comprehensive (includes both senders and receivers)
-- This counts all unique addresses that were involved in transactions
SELECT 
    DATE(block_time) as date,
    COUNT(DISTINCT "from") as active_addresses_senders,
    COUNT(DISTINCT "to") as active_addresses_receivers,
    COUNT(DISTINCT CASE 
        WHEN "from" IS NOT NULL AND "to" IS NOT NULL THEN "from"
        WHEN "from" IS NOT NULL THEN "from"
        WHEN "to" IS NOT NULL THEN "to"
    END) as active_addresses_total
FROM ethereum.transactions
WHERE block_time >= '2017-01-01'
  AND block_time < CURRENT_DATE
GROUP BY DATE(block_time)
ORDER BY date;

-- Option 3: Recommended - Counts all unique addresses (union of senders and receivers)
-- This is the most accurate measure of "active addresses"
SELECT 
    DATE(block_time) as date,
    COUNT(DISTINCT address) as active_addresses
FROM (
    SELECT 
        block_time,
        "from" as address
    FROM ethereum.transactions
    WHERE block_time >= '2017-01-01'
      AND block_time < CURRENT_DATE
    
    UNION
    
    SELECT 
        block_time,
        "to" as address
    FROM ethereum.transactions
    WHERE block_time >= '2017-01-01'
      AND block_time < CURRENT_DATE
      AND "to" IS NOT NULL
) combined
GROUP BY DATE(block_time)
ORDER BY date;

-- Option 4: With additional metrics (for analysis)
-- Includes transaction count and value for context
SELECT 
    DATE(block_time) as date,
    COUNT(DISTINCT address) as active_addresses,
    COUNT(*) as total_transactions,
    SUM(value) / 1e18 as total_eth_volume
FROM (
    SELECT 
        block_time,
        "from" as address,
        value
    FROM ethereum.transactions
    WHERE block_time >= '2017-01-01'
      AND block_time < CURRENT_DATE
    
    UNION ALL
    
    SELECT 
        block_time,
        "to" as address,
        CAST(0 AS DECIMAL) as value
    FROM ethereum.transactions
    WHERE block_time >= '2017-01-01'
      AND block_time < CURRENT_DATE
      AND "to" IS NOT NULL
) combined
GROUP BY DATE(block_time)
ORDER BY date;

