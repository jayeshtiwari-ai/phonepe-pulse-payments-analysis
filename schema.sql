-- ==============================================================================
-- PhonePe Pulse Analytics Schema
-- Compatible with MySQL 8.0+ and SQLite 3
-- Defines 10 relational tables with Composite Primary Keys and Composite Indexes
-- ==============================================================================

-- 1. Aggregated Transactions
CREATE TABLE IF NOT EXISTS agg_transaction (
    state VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    category VARCHAR(100) NOT NULL,
    count BIGINT NOT NULL,
    amount DOUBLE NOT NULL,
    PRIMARY KEY (state, year, quarter, category)
);
CREATE INDEX idx_agg_tx_syq ON agg_transaction (state, year, quarter);

-- 2. Aggregated Users
CREATE TABLE IF NOT EXISTS agg_user (
    state VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    registered_users BIGINT NOT NULL,
    app_opens BIGINT NOT NULL,
    PRIMARY KEY (state, year, quarter)
);
CREATE INDEX idx_agg_u_syq ON agg_user (state, year, quarter);

-- 3. Aggregated User Devices
CREATE TABLE IF NOT EXISTS agg_user_device (
    state VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    count BIGINT NOT NULL,
    percentage DOUBLE NOT NULL,
    PRIMARY KEY (state, year, quarter, brand)
);
CREATE INDEX idx_agg_dev_syq ON agg_user_device (state, year, quarter);

-- 4. Aggregated Insurance
CREATE TABLE IF NOT EXISTS agg_insurance (
    state VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    category VARCHAR(100) NOT NULL,
    count BIGINT NOT NULL,
    amount DOUBLE NOT NULL,
    PRIMARY KEY (state, year, quarter, category)
);
CREATE INDEX idx_agg_ins_syq ON agg_insurance (state, year, quarter);

-- 5. Map Transactions (District Level)
CREATE TABLE IF NOT EXISTS map_transaction (
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    count BIGINT NOT NULL,
    amount DOUBLE NOT NULL,
    PRIMARY KEY (state, district, year, quarter)
);
CREATE INDEX idx_map_tx_syq ON map_transaction (state, year, quarter);

-- 6. Map Users (District Level)
CREATE TABLE IF NOT EXISTS map_user (
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    registered_users BIGINT NOT NULL,
    app_opens BIGINT NOT NULL,
    PRIMARY KEY (state, district, year, quarter)
);
CREATE INDEX idx_map_u_syq ON map_user (state, year, quarter);

-- 7. Map Insurance (District Level)
CREATE TABLE IF NOT EXISTS map_insurance (
    state VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    count BIGINT NOT NULL,
    amount DOUBLE NOT NULL,
    PRIMARY KEY (state, district, year, quarter)
);
CREATE INDEX idx_map_ins_syq ON map_insurance (state, year, quarter);

-- 8. Top Transactions (Districts & Pincodes)
CREATE TABLE IF NOT EXISTS top_transaction (
    level VARCHAR(20) NOT NULL,
    state VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    count BIGINT NOT NULL,
    amount DOUBLE NOT NULL,
    PRIMARY KEY (level, state, entity_type, entity_name, year, quarter)
);
CREATE INDEX idx_top_tx_syq ON top_transaction (state, year, quarter);

-- 9. Top Users (Districts & Pincodes)
CREATE TABLE IF NOT EXISTS top_user (
    level VARCHAR(20) NOT NULL,
    state VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    registered_users BIGINT NOT NULL,
    PRIMARY KEY (level, state, entity_type, entity_name, year, quarter)
);
CREATE INDEX idx_top_u_syq ON top_user (state, year, quarter);

-- 10. Top Insurance (Districts & Pincodes)
CREATE TABLE IF NOT EXISTS top_insurance (
    level VARCHAR(20) NOT NULL,
    state VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    period VARCHAR(10) NOT NULL,
    count BIGINT NOT NULL,
    amount DOUBLE NOT NULL,
    PRIMARY KEY (level, state, entity_type, entity_name, year, quarter)
);
CREATE INDEX idx_top_ins_syq ON top_insurance (state, year, quarter);
