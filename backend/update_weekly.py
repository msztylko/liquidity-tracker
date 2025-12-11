"""
Weekly Update Script for Fed Balance Sheet Data

Updates database with latest weekly Fed data:
- Fetches data from FRED API
- Inserts/updates fed_weekly table
- Calculates week-over-week changes
- Runs automatically via cron/scheduler

Usage:
    python update_weekly.py [--weeks N] [--verbose]

    --weeks N    : Fetch last N weeks (default: 4)
    --verbose    : Show detailed output

Requirements:
    - FRED API key: export FRED_API_KEY='your_key_here'
    - Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html

Schedule with cron (weekly on Thursday at 10 AM ET):
    0 10 * * 4 cd /path/to/backend && python update_weekly.py
"""

import sys
import sqlite3
import argparse
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fetch_fred import fetch_latest_fed_weekly


DB_PATH = Path(__file__).parent / "fed_liquidity.db"


def calculate_weekly_changes(cursor: sqlite3.Cursor, date: str) -> tuple:
    """
    Calculate week-over-week changes for balance sheet and reserves

    Args:
        cursor: Database cursor
        date: Current date (YYYY-MM-DD)

    Returns:
        Tuple of (balance_sheet_change, reserves_change) or (None, None)
    """
    # Get previous week's data
    sql = """
    SELECT balance_sheet, reserves
    FROM fed_weekly
    WHERE date < ?
    ORDER BY date DESC
    LIMIT 1
    """
    cursor.execute(sql, (date,))
    prev_week = cursor.fetchone()

    if not prev_week:
        return (None, None)

    # Get current week's data
    cursor.execute("SELECT balance_sheet, reserves FROM fed_weekly WHERE date = ?", (date,))
    curr_week = cursor.fetchone()

    if not curr_week:
        return (None, None)

    prev_bs, prev_res = prev_week
    curr_bs, curr_res = curr_week

    bs_change = (curr_bs - prev_bs) if (curr_bs and prev_bs) else None
    res_change = (curr_res - prev_res) if (curr_res and prev_res) else None

    return (bs_change, res_change)


def upsert_fed_weekly(data: list, verbose: bool = False) -> tuple:
    """
    Insert or update Fed weekly data in database

    Args:
        data: List of Fed weekly records from FRED API
        verbose: Print detailed output

    Returns:
        Tuple of (inserted_count, updated_count)
    """
    if not DB_PATH.exists():
        print(f"✗ Database not found: {DB_PATH}")
        print("Run create_database.py first")
        return (0, 0)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    updated = 0

    for record in data:
        date = record['date']
        balance_sheet = record['balance_sheet']
        reserves = record['reserves']
        tga = record.get('tga')  # Optional

        # Check if record exists
        cursor.execute("SELECT date FROM fed_weekly WHERE date = ?", (date,))
        exists = cursor.fetchone() is not None

        if exists:
            # Update existing record
            sql = """
            UPDATE fed_weekly
            SET balance_sheet = ?,
                reserves = ?,
                tga = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
            """
            cursor.execute(sql, (balance_sheet, reserves, tga, date))
            updated += 1

            if verbose:
                print(f"  Updated: {date}")

        else:
            # Insert new record
            sql = """
            INSERT INTO fed_weekly
            (date, balance_sheet, reserves, tga)
            VALUES (?, ?, ?, ?)
            """
            cursor.execute(sql, (date, balance_sheet, reserves, tga))
            inserted += 1

            if verbose:
                print(f"  Inserted: {date} (BS: {balance_sheet:,.1f}B, Reserves: {reserves:,.1f}B)")

        # Calculate and update weekly changes
        bs_change, res_change = calculate_weekly_changes(cursor, date)

        if bs_change is not None or res_change is not None:
            sql = """
            UPDATE fed_weekly
            SET balance_sheet_change = ?,
                reserves_change = ?
            WHERE date = ?
            """
            cursor.execute(sql, (bs_change, res_change, date))

            if verbose and bs_change:
                sign = "+" if bs_change > 0 else ""
                print(f"    Change: BS {sign}{bs_change:,.1f}B, Reserves {sign}{res_change:,.1f}B")

    conn.commit()
    conn.close()

    return (inserted, updated)


def main():
    """Main update function"""
    parser = argparse.ArgumentParser(description='Update database with weekly Fed data')
    parser.add_argument('--weeks', type=int, default=4, help='Number of weeks to fetch (default: 4)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()

    print(f"Fed Liquidity Tracker - Weekly Update")
    print(f"{'=' * 50}\n")

    # Fetch data from FRED
    print(f"Fetching last {args.weeks} weeks from FRED...\n")

    try:
        data = fetch_latest_fed_weekly(weeks_back=args.weeks, include_tga=False)
    except ValueError as e:
        print(f"✗ Error: {e}\n")
        print("FRED API key required:")
        print("1. Get free API key: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Set environment variable: export FRED_API_KEY='your_key_here'")
        return 1

    if not data:
        print("✗ No data fetched")
        return 1

    print(f"\n{'=' * 50}")
    print(f"Updating database...\n")

    # Insert/update database
    inserted, updated = upsert_fed_weekly(data, verbose=args.verbose)

    print(f"\n{'=' * 50}")
    print(f"Update complete:")
    print(f"  ✓ Inserted: {inserted} records")
    print(f"  ✓ Updated: {updated} records")
    print(f"  ✓ Total processed: {len(data)} records")
    print(f"  ✓ Database: {DB_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
