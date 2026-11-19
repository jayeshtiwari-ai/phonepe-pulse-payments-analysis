-- ==============================================================================
-- PhonePe Platform Payments Growth & Opportunity Analysis
-- queries.sql: 14 Analytical Queries across Transactions, Users, Insurance, and Growth
-- Database Engine: MySQL 8.0+ / SQLite 3
-- All metrics reflect data recorded strictly on the PhonePe platform.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUERY 1: Top 10 States by Total Transaction Value on PhonePe Platform (All-Time)
-- Objective: Shows leading states driving transaction value and volume on PhonePe,
-- along with overall average ticket size.
-- ------------------------------------------------------------------------------
SELECT 
    state, 
    ROUND(SUM(amount) / 1e12, 2) AS total_amount_trillion_inr,
    SUM(count) AS total_transactions,
    ROUND(SUM(amount) / SUM(count), 2) AS avg_ticket_size_inr
FROM agg_transaction
GROUP BY state
ORDER BY total_amount_trillion_inr DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 2: Quarter-over-Quarter (QoQ) Growth per Top State (Window Function)
-- Objective: Shows QoQ transaction value growth rates for top digital economies
-- (Karnataka, Maharashtra, Telangana) using LAG() window functions across 2023-2024.
-- ------------------------------------------------------------------------------
WITH state_quarterly AS (
    SELECT 
        state, 
        year, 
        quarter, 
        period,
        SUM(amount) AS total_amount
    FROM agg_transaction
    WHERE state IN ('Karnataka', 'Maharashtra', 'Telangana') 
      AND year >= 2023
    GROUP BY state, year, quarter, period
)
SELECT 
    state, 
    period,
    ROUND(total_amount / 1e9, 2) AS amount_billion_inr,
    ROUND((total_amount - LAG(total_amount) OVER (PARTITION BY state ORDER BY year, quarter)) 
          / LAG(total_amount) OVER (PARTITION BY state ORDER BY year, quarter) * 100, 2) AS qoq_growth_pct
FROM state_quarterly
ORDER BY state, period;


-- ------------------------------------------------------------------------------
-- QUERY 3: Average Ticket Size by Payment Category on PhonePe Platform (2024)
-- Objective: Shows average transaction sizes across P2P, Merchant, Recharges,
-- and Financial Services on the PhonePe platform.
-- ------------------------------------------------------------------------------
SELECT 
    category,
    ROUND(SUM(amount) / 1e9, 2) AS total_amount_billion_inr,
    SUM(count) AS total_count,
    ROUND(SUM(amount) / SUM(count), 2) AS avg_ticket_size_inr
FROM agg_transaction
WHERE year = 2024
GROUP BY category
ORDER BY avg_ticket_size_inr DESC;


-- ------------------------------------------------------------------------------
-- QUERY 4: User Engagement Ratio (App Opens / Registered Users) by State (2024-Q4)
-- Objective: Shows states where registered users interact most frequently with
-- the PhonePe platform on a per-user basis.
-- ------------------------------------------------------------------------------
SELECT 
    state, 
    registered_users, 
    app_opens,
    ROUND(CAST(app_opens AS FLOAT) / registered_users, 2) AS app_opens_per_user
FROM agg_user
WHERE period = '2024-Q4'
ORDER BY app_opens_per_user DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 5: Untapped Growth Opportunities: High Registered Users, Low Tx per User (2024-Q4)
-- Objective: Shows districts with substantial user adoption (>=500,000 registered users)
-- but lower transaction frequency (<17 tx/user/quarter) on the PhonePe platform.
-- ------------------------------------------------------------------------------
SELECT 
    u.state, 
    u.district,
    u.registered_users,
    t.count AS total_transactions,
    ROUND(CAST(t.count AS FLOAT) / u.registered_users, 2) AS tx_per_user,
    ROUND(t.amount / 1e7, 2) AS amount_crore_inr
FROM map_user u
JOIN map_transaction t 
  ON u.state = t.state 
 AND u.district = t.district 
 AND u.period = t.period
WHERE u.period = '2024-Q4' 
  AND u.registered_users >= 500000
ORDER BY tx_per_user ASC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 6: PhonePe Insurance Policy & Value Growth YoY (2023-Q4 vs 2024-Q4)
-- Objective: Shows expansion in insurance policy issuance and premium volume
-- on the PhonePe platform across top performing states over 12 months.
-- ------------------------------------------------------------------------------
WITH ins_2023 AS (
    SELECT state, SUM(count) AS policies_2023, SUM(amount) AS amount_2023
    FROM agg_insurance
    WHERE period = '2023-Q4'
    GROUP BY state
),
ins_2024 AS (
    SELECT state, SUM(count) AS policies_2024, SUM(amount) AS amount_2024
    FROM agg_insurance
    WHERE period = '2024-Q4'
    GROUP BY state
)
SELECT 
    i24.state,
    i23.policies_2023, 
    i24.policies_2024,
    ROUND((CAST(i24.policies_2024 AS FLOAT) - i23.policies_2023) / i23.policies_2023 * 100, 2) AS policy_growth_pct,
    ROUND(i23.amount_2023 / 1e7, 2) AS amount_2023_cr,
    ROUND(i24.amount_2024 / 1e7, 2) AS amount_2024_cr,
    ROUND((i24.amount_2024 - i23.amount_2023) / i23.amount_2023 * 100, 2) AS value_growth_pct
FROM ins_2024 i24
JOIN ins_2023 i23 ON i24.state = i23.state
ORDER BY i24.policies_2024 DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 7: National Device Brand Share on PhonePe (2022-Q1 Benchmark)
-- Objective: Shows smartphone OEM distribution among PhonePe users before the
-- platform deprecated hardware brand reporting in 2022-Q2.
-- ------------------------------------------------------------------------------
SELECT 
    brand,
    SUM(count) AS total_devices,
    ROUND(SUM(count) * 100.0 / (SELECT SUM(count) FROM agg_user_device WHERE period = '2022-Q1'), 2) AS national_market_share_pct
FROM agg_user_device
WHERE period = '2022-Q1'
GROUP BY brand
ORDER BY total_devices DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 8: Festive Season Seasonality: Q4 Surge vs Baseline (2018 - 2024)
-- Objective: Shows annual Q4 holiday / festive shopping surges in payment value
-- on the PhonePe platform compared against the average of Q1-Q3 of the same year.
-- ------------------------------------------------------------------------------
SELECT 
    year,
    ROUND(AVG(CASE WHEN quarter != 4 THEN quarter_amount END) / 1e9, 2) AS avg_q1_q3_amount_billion,
    ROUND(MAX(CASE WHEN quarter = 4 THEN quarter_amount END) / 1e9, 2) AS q4_festive_amount_billion,
    ROUND((MAX(CASE WHEN quarter = 4 THEN quarter_amount END) - 
           AVG(CASE WHEN quarter != 4 THEN quarter_amount END)) 
           / AVG(CASE WHEN quarter != 4 THEN quarter_amount END) * 100, 2) AS q4_festive_surge_pct
FROM (
    SELECT year, quarter, SUM(amount) AS quarter_amount
    FROM agg_transaction
    GROUP BY year, quarter
)
GROUP BY year
HAVING q4_festive_amount_billion IS NOT NULL
ORDER BY year;


-- ------------------------------------------------------------------------------
-- QUERY 9: Top Reported Pincodes per State Ranked by Amount (2024-Q4)
-- Rules: level = 'state', entity_type = 'pincode', exclude entity_name = 'Unknown'
-- Objective: Shows top hyper-local transaction clusters recorded on PhonePe in 2024-Q4.
-- NOTE: Pincode localities are not in the Pulse dataset and can be checked via India Post.
-- ------------------------------------------------------------------------------
SELECT 
    state, 
    entity_name AS pincode,
    count AS transactions,
    ROUND(amount / 1e9, 2) AS amount_billion_inr
FROM top_transaction
WHERE level = 'state' 
  AND entity_type = 'pincode' 
  AND period = '2024-Q4'
  AND entity_name != 'Unknown'
ORDER BY amount DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 10: Top 10 Districts in India by Transaction Value on PhonePe (2024-Q4)
-- Rules: level = 'state', entity_type = 'district'
-- Objective: Shows India's dominant urban metropolitan economic hubs on PhonePe.
-- ------------------------------------------------------------------------------
SELECT 
    state, 
    entity_name AS district,
    count AS transactions,
    ROUND(amount / 1e9, 2) AS amount_billion_inr
FROM top_transaction
WHERE level = 'state' 
  AND entity_type = 'district' 
  AND period = '2024-Q4'
ORDER BY amount DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 11: PhonePe Payments Mix: P2P vs Merchant (2018 - 2024)
-- Objective: Shows the structural transition between peer transfers (P2P) and
-- merchant payments (P2M) on the PhonePe platform across all recorded years.
-- NOTE: Shares are computed over (P2P + Merchant) only, excluding recharge & bill
-- payments, financial services, and others.
-- ------------------------------------------------------------------------------
SELECT 
    year,
    SUM(CASE WHEN category = 'Peer-to-peer payments' THEN count ELSE 0 END) AS p2p_count,
    SUM(CASE WHEN category = 'Merchant payments' THEN count ELSE 0 END) AS merchant_count,
    ROUND(SUM(CASE WHEN category = 'Merchant payments' THEN count ELSE 0 END) * 100.0 / 
          SUM(CASE WHEN category IN ('Peer-to-peer payments', 'Merchant payments') THEN count ELSE 0 END), 2) AS merchant_volume_share_pct,
    ROUND(SUM(CASE WHEN category = 'Peer-to-peer payments' THEN amount ELSE 0 END) / 1e12, 2) AS p2p_val_trillion_inr,
    ROUND(SUM(CASE WHEN category = 'Merchant payments' THEN amount ELSE 0 END) / 1e12, 2) AS merchant_val_trillion_inr,
    ROUND(SUM(CASE WHEN category = 'Merchant payments' THEN amount ELSE 0 END) * 100.0 / 
          SUM(CASE WHEN category IN ('Peer-to-peer payments', 'Merchant payments') THEN amount ELSE 0 END), 2) AS merchant_value_share_pct,
    ROUND(SUM(CASE WHEN category = 'Peer-to-peer payments' THEN amount ELSE 0 END) / 
          SUM(CASE WHEN category = 'Peer-to-peer payments' THEN count ELSE 0 END), 2) AS p2p_avg_ticket_size_inr,
    ROUND(SUM(CASE WHEN category = 'Merchant payments' THEN amount ELSE 0 END) / 
          SUM(CASE WHEN category = 'Merchant payments' THEN count ELSE 0 END), 2) AS merchant_avg_ticket_size_inr
FROM agg_transaction
GROUP BY year
ORDER BY year;


-- ------------------------------------------------------------------------------
-- QUERY 12: Premium Hardware Adoption: Apple Share in Major States on PhonePe (2022-Q1)
-- Objective: Shows states with the highest concentration of iOS users on PhonePe
-- for evaluating premium digital financial services adoption.
-- ------------------------------------------------------------------------------
SELECT 
    state,
    SUM(CASE WHEN brand = 'Apple' THEN count ELSE 0 END) AS apple_users,
    SUM(count) AS total_users,
    ROUND(SUM(CASE WHEN brand = 'Apple' THEN count ELSE 0 END) * 100.0 / SUM(count), 2) AS apple_share_pct
FROM agg_user_device
WHERE period = '2022-Q1'
GROUP BY state
HAVING total_users >= 5000000
ORDER BY apple_share_pct DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 13: Insurance Penetration per 10,000 Registered Users on PhonePe (2024-Q4)
-- Objective: Shows insurance product density across state user bases on PhonePe.
-- ------------------------------------------------------------------------------
SELECT 
    i.state,
    u.registered_users,
    i.count AS insurance_policies,
    ROUND(CAST(i.count AS FLOAT) * 10000 / u.registered_users, 2) AS policies_per_10k_users,
    ROUND(i.amount / 1e7, 2) AS premium_crore_inr
FROM agg_insurance i
JOIN agg_user u 
  ON i.state = u.state 
 AND i.period = u.period
WHERE i.period = '2024-Q4'
ORDER BY policies_per_10k_users DESC
LIMIT 10;


-- ------------------------------------------------------------------------------
-- QUERY 14: Annual Digital Payments Growth on PhonePe Platform (2018 - 2024)
-- Objective: Shows annual growth in transaction volume and aggregate value
-- on the PhonePe platform from 2018 through 2024.
-- ------------------------------------------------------------------------------
SELECT 
    year,
    SUM(count) AS annual_transactions,
    ROUND(SUM(amount) / 1e12, 2) AS annual_amount_trillion_inr,
    ROUND(SUM(amount) / SUM(count), 2) AS national_avg_ticket_size_inr
FROM agg_transaction
GROUP BY year
ORDER BY year;
