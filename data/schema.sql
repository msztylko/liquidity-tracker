-- Fed Liquidity Monitor - Database Schema
-- SQLite Database for Federal Reserve liquidity metrics
-- Data retention: January 2018 onwards
-- Created: 2026-01-03

-- ============================================================================
-- Table 1: daily_rates
-- Purpose: Store daily interest rates (SOFR, EFFR)
-- Update: Daily at 8:00 AM ET
-- Source: NY Fed API (https://markets.newyorkfed.org/api)
-- ============================================================================

CREATE TABLE daily_rates (
    -- Primary key
    date DATE PRIMARY KEY,

    -- SOFR (Secured Overnight Financing Rate)
    sofr REAL,                          -- Rate as decimal (e.g., 0.0457 = 4.57%)
    sofr_1st_percentile REAL,           -- 1st percentile of transactions
    sofr_25th_percentile REAL,          -- 25th percentile (bottom of IQR)
    sofr_75th_percentile REAL,          -- 75th percentile (top of IQR)
    sofr_99th_percentile REAL,          -- 99th percentile (outliers)
    sofr_volume_billions REAL,          -- Transaction volume in billions USD

    -- EFFR (Effective Federal Funds Rate)
    effr REAL,                          -- Rate as decimal (e.g., 0.0433 = 4.33%)
    effr_volume_billions REAL,          -- Transaction volume in billions USD

    -- Calculated fields (computed after data insert)
    sofr_iorb_spread REAL,              -- SOFR - IORB (requires join to policy_rates)
    effr_target_deviation REAL,         -- EFFR - target midpoint (requires join to policy_rates)

    -- Date metadata (computed after insert)
    is_quarter_end BOOLEAN DEFAULT 0,  -- TRUE if Mar 31, Jun 30, Sep 30, Dec 31
    is_month_end BOOLEAN DEFAULT 0,    -- TRUE if last business day of month
    is_tax_date BOOLEAN DEFAULT 0,     -- TRUE if 15th of Apr, Jun, Sep, Dec
    day_of_week INTEGER,                -- 0=Monday, 6=Sunday

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for daily_rates
CREATE INDEX idx_daily_rates_date_desc ON daily_rates(date DESC);
CREATE INDEX idx_daily_rates_quarter_end ON daily_rates(is_quarter_end) WHERE is_quarter_end = 1;
CREATE INDEX idx_daily_rates_sofr_spread ON daily_rates(sofr_iorb_spread);

-- ============================================================================
-- Table 2: daily_operations
-- Purpose: Store daily Fed facility usage (ON RRP, SRF)
-- Update: Daily at 1:30 PM ET
-- Source: NY Fed API (https://markets.newyorkfed.org/api)
-- ============================================================================

CREATE TABLE daily_operations (
    -- Primary key
    date DATE PRIMARY KEY,

    -- ON RRP (Overnight Reverse Repo Program)
    onrrp_usage_billions REAL,          -- Dollar amount parked at Fed (e.g., 345.0)

    -- SRF (Standing Repo Facility)
    srf_usage_billions REAL,            -- Dollar amount borrowed from Fed (e.g., 12.0)

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for daily_operations
CREATE INDEX idx_daily_ops_date_desc ON daily_operations(date DESC);
CREATE INDEX idx_daily_ops_onrrp ON daily_operations(onrrp_usage_billions);
CREATE INDEX idx_daily_ops_srf ON daily_operations(srf_usage_billions);

-- ============================================================================
-- Table 3: weekly_balance_sheet
-- Purpose: Store weekly Fed balance sheet data from H.4.1 report
-- Update: Weekly, Thursday at 4:30 PM ET
-- Source: Federal Reserve H.4.1 Report
-- ============================================================================

CREATE TABLE weekly_balance_sheet (
    -- Primary key
    date DATE PRIMARY KEY,              -- Always Wednesday date

    -- Assets (Fed's balance sheet)
    total_assets_billions REAL NOT NULL,           -- Total Fed assets
    treasury_securities_billions REAL,             -- Treasury securities held
    mbs_billions REAL,                             -- Mortgage-backed securities

    -- Liabilities / Reserve balances
    reserve_balances_billions REAL NOT NULL,       -- Total reserves held by banks
    tga_billions REAL,                             -- Treasury General Account

    -- Calculated week-over-week changes (computed after insert)
    total_assets_wow_change REAL,                  -- Change from previous week
    reserves_wow_change REAL,                      -- Change from previous week
    tga_wow_change REAL,                           -- Change from previous week

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for weekly_balance_sheet
CREATE INDEX idx_weekly_bs_date_desc ON weekly_balance_sheet(date DESC);
CREATE INDEX idx_weekly_bs_assets ON weekly_balance_sheet(total_assets_billions);
CREATE INDEX idx_weekly_bs_reserves ON weekly_balance_sheet(reserve_balances_billions);

-- ============================================================================
-- Table 4: policy_rates
-- Purpose: Store FOMC policy decisions on interest rates
-- Update: After each FOMC meeting (~8 times per year)
-- Source: FOMC statements (manual entry or scraped)
-- ============================================================================

CREATE TABLE policy_rates (
    -- Primary key
    effective_date DATE PRIMARY KEY,

    -- Core policy rates (from FOMC)
    iorb REAL NOT NULL,                            -- Interest on Reserve Balances
    target_lower REAL NOT NULL,                    -- Fed Funds target lower bound
    target_upper REAL NOT NULL,                    -- Fed Funds target upper bound

    -- Fed facility offering rates (calculated from IORB)
    onrrp_offering_rate REAL,                      -- ON RRP rate (typically IORB - 10 bps)
    srf_offering_rate REAL,                        -- SRF rate (typically IORB + 10 bps)

    -- Calculated helpers
    target_midpoint REAL,                          -- (target_lower + target_upper) / 2

    -- FOMC metadata
    fomc_meeting_date DATE,                        -- Actual FOMC meeting date
    notes TEXT,                                    -- Optional notes about decision

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for policy_rates
CREATE INDEX idx_policy_rates_date_desc ON policy_rates(effective_date DESC);
CREATE INDEX idx_policy_rates_fomc_date ON policy_rates(fomc_meeting_date);

-- ============================================================================
-- Table 5: data_update_log
-- Purpose: Track data fetch operations for monitoring and debugging
-- Update: Every data fetch attempt
-- Source: Backend data fetchers
-- ============================================================================

CREATE TABLE data_update_log (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- What was fetched
    data_type TEXT NOT NULL CHECK(data_type IN ('daily_rates', 'daily_operations', 'weekly_balance_sheet', 'policy_rates')),

    -- When it was fetched
    update_timestamp TIMESTAMP NOT NULL,
    data_date DATE,                     -- The date of data being fetched (not fetch time)

    -- Status
    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'partial')),
    records_updated INTEGER,            -- How many records inserted/updated

    -- Error tracking
    error_message TEXT,                 -- Error details if failed
    api_response_code INTEGER,          -- HTTP response code

    -- Performance
    fetch_duration_ms INTEGER,          -- How long the fetch took in milliseconds

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for data_update_log
CREATE INDEX idx_update_log_type_time ON data_update_log(data_type, update_timestamp DESC);
CREATE INDEX idx_update_log_status ON data_update_log(status);
CREATE INDEX idx_update_log_date ON data_update_log(data_date DESC);
