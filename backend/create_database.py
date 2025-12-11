"""
Fed Liquidity Tracker - Database Creation Script

Creates SQLite database with schema for storing:
- Daily repo market data (SOFR, EFFR, SRF, ON RRP)
- Weekly Fed data (Balance Sheet, Reserves)
- Policy rate changes (IORB, Target Range)
- Historical crisis events

Usage:
    python create_database.py

Output:
    fed_liquidity.db (SQLite database file)
"""

import sqlite3
from datetime import datetime
from pathlib import Path

# Database configuration
DB_NAME = "fed_liquidity.db"
DB_PATH = Path(__file__).parent / DB_NAME

def create_database():
    """Create database and all tables"""

    # Check if database already exists
    if DB_PATH.exists():
        response = input(f"{DB_NAME} already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted. No changes made.")
            return
        DB_PATH.unlink()
        print(f"Deleted existing {DB_NAME}")

    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Creating database: {DB_PATH}")

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create tables
    create_repo_rates_table(cursor)
    create_fed_weekly_table(cursor)
    create_policy_rates_table(cursor)
    # create_crisis_events_table(cursor)

    # Insert initial reference data
    # insert_crisis_events(cursor)

    # Commit changes
    conn.commit()

    # Verify tables created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"\nTables created: {[t[0] for t in tables]}")

    # Close connection
    conn.close()

    print(f"\n✓ Database created successfully: {DB_PATH}")
    print(f"✓ Size: {DB_PATH.stat().st_size / 1024:.2f} KB")

def create_repo_rates_table(cursor):
    """Create repo_rates table for daily data"""

    sql = """
    CREATE TABLE repo_rates (
        date DATE PRIMARY KEY,
        sofr REAL,
        effr REAL,
        srf_usage REAL,
        onrrp REAL,

        sofr_iorb_spread REAL,
        effr_target_mid REAL,

        is_quarter_end BOOLEAN DEFAULT 0,
        is_month_end BOOLEAN DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(sql)

    # Create indexes
    cursor.execute("CREATE INDEX idx_repo_rates_date ON repo_rates(date DESC);")
    cursor.execute("CREATE INDEX idx_repo_rates_quarter_end ON repo_rates(is_quarter_end) WHERE is_quarter_end = 1;")

    print("✓ Created table: repo_rates")

def create_fed_weekly_table(cursor):
    """Create fed_weekly table for weekly Fed data"""

    sql = """
    CREATE TABLE fed_weekly (
        date DATE PRIMARY KEY,
        balance_sheet REAL,
        reserves REAL,
        tga REAL,

        balance_sheet_change REAL,
        reserves_change REAL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(sql)

    # Create index
    cursor.execute("CREATE INDEX idx_fed_weekly_date ON fed_weekly(date DESC);")

    print("✓ Created table: fed_weekly")

def create_policy_rates_table(cursor):
    """Create policy_rates table for IORB and target range"""

    sql = """
    CREATE TABLE policy_rates (
        effective_date DATE PRIMARY KEY,
        iorb REAL NOT NULL,
        target_lower REAL NOT NULL,
        target_upper REAL NOT NULL,

        fomc_meeting_date DATE,
        notes TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(sql)

    # Create index
    cursor.execute("CREATE INDEX idx_policy_rates_date ON policy_rates(effective_date DESC);")

    print("✓ Created table: policy_rates")

def create_crisis_events_table(cursor):
    """Create crisis_events table for historical reference"""

    sql = """
    CREATE TABLE crisis_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,

        peak_sofr REAL,
        peak_spread REAL,
        effr_broke_range BOOLEAN,

        fed_response TEXT,
        announcement_date DATE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(sql)

    # Create index
    cursor.execute("CREATE INDEX idx_crisis_events_dates ON crisis_events(start_date, end_date);")

    print("✓ Created table: crisis_events")

def insert_crisis_events(cursor):
    """Insert September 2019 crisis reference data"""

    sql = """
    INSERT INTO crisis_events
    (event_name, start_date, end_date, peak_sofr, peak_spread, effr_broke_range, fed_response, announcement_date)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?);
    """

    cursor.execute(sql, (
        'September 2019 Repo Crisis',
        '2019-09-16',
        '2019-09-20',
        5.25,
        2.82,
        1,  # TRUE
        'Emergency $75B repo operations, T-bill purchases ($60B/month)',
        '2019-09-17'
    ))

    print("✓ Inserted reference data: September 2019 crisis")

if __name__ == "__main__":
    create_database()
