"""
Verify database schema created correctly

Usage:
    python verify_schema.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "fed_liquidity.db"

def verify_schema():
    """Verify database structure"""

    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        print("Run create_database.py first")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Verifying database: {DB_PATH}\n")

    # Check tables exist
    expected_tables = ['repo_rates', 'fed_weekly', 'policy_rates'] # , 'crisis_events']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]

    print("Tables:")
    for table in expected_tables:
        exists = table in tables
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")

    # Check indexes
    print("\nIndexes:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';")
    indexes = cursor.fetchall()
    print(f"  ✓ {len(indexes)} indexes created")

    # Check each table structure
    for table in expected_tables:
        if table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            print(f"\n{table} ({len(columns)} columns):")
            for col in columns:
                col_name, col_type = col[1], col[2]
                print(f"  - {col_name}: {col_type}")

    # # Check crisis_events has data
    # cursor.execute("SELECT COUNT(*) FROM crisis_events;")
    # count = cursor.fetchone()[0]
    # print(f"\nReference data:")
    # print(f"  ✓ {count} crisis event(s) loaded")

    # # Show September 2019 crisis
    # cursor.execute("SELECT event_name, start_date, peak_sofr FROM crisis_events WHERE event_name LIKE '%2019%';")
    # crisis = cursor.fetchone()
    # if crisis:
    #     print(f"  ✓ Sept 2019 crisis: peak SOFR {crisis[2]}%")

    # conn.close()

    print(f"\n✓ Verification complete")

if __name__ == "__main__":
    verify_schema()
