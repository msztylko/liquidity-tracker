"""
Daily Update Script for Repo Rates

Updates database with latest daily repo market data:
- Fetches data from NY Fed APIs
- Inserts/updates repo_rates table
- Marks quarter-end and month-end dates
- Runs automatically via cron/scheduler

Usage:
    python update_daily.py [--days N] [--verbose]

    --days N     : Fetch last N days (default: 7)
    --verbose    : Show detailed output

Schedule with cron (daily at 10 AM ET):
    0 10 * * * cd /path/to/backend && python update_daily.py
"""

import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from calendar import monthrange

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fetch_nyfed import fetch_latest_repo_rates


DB_PATH = Path(__file__).parent / "fed_liquidity.db"


def is_quarter_end(date_str: str) -> bool:
    """Check if date is a quarter-end (Mar 31, Jun 30, Sep 30, Dec 31)"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if date.month in [3, 6, 9, 12]:
            last_day = monthrange(date.year, date.month)[1]
            return date.day == last_day
        return False
    except ValueError:
        return False


def is_month_end(date_str: str) -> bool:
    """Check if date is a month-end"""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        last_day = monthrange(date.year, date.month)[1]
        return date.day == last_day
    except ValueError:
        return False


def upsert_repo_rates(data: list, verbose: bool = False) -> tuple:
    """
    Insert or update repo rates in database

    Args:
        data: List of repo rate records from NY Fed API
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
        sofr = record['sofr']
        effr = record['effr']
        srf_usage = record['srf_usage']
        onrrp = record['onrrp']

        # Check if record exists
        cursor.execute("SELECT date FROM repo_rates WHERE date = ?", (date,))
        exists = cursor.fetchone() is not None

        # Calculate date flags
        is_qtr_end = is_quarter_end(date)
        is_mon_end = is_month_end(date)

        if exists:
            # Update existing record
            sql = """
            UPDATE repo_rates
            SET sofr = ?,
                effr = ?,
                srf_usage = ?,
                onrrp = ?,
                is_quarter_end = ?,
                is_month_end = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
            """
            cursor.execute(sql, (sofr, effr, srf_usage, onrrp, is_qtr_end, is_mon_end, date))
            updated += 1

            if verbose:
                print(f"  Updated: {date}")

        else:
            # Insert new record
            sql = """
            INSERT INTO repo_rates
            (date, sofr, effr, srf_usage, onrrp, is_quarter_end, is_month_end)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (date, sofr, effr, srf_usage, onrrp, is_qtr_end, is_mon_end))
            inserted += 1

            if verbose:
                qtr_flag = " [QTR END]" if is_qtr_end else ""
                mon_flag = " [MONTH END]" if is_mon_end and not is_qtr_end else ""
                print(f"  Inserted: {date}{qtr_flag}{mon_flag}")

    conn.commit()
    conn.close()

    return (inserted, updated)


def main():
    """Main update function"""
    parser = argparse.ArgumentParser(description='Update database with daily repo rates')
    parser.add_argument('--days', type=int, default=7, help='Number of days to fetch (default: 7)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()

    print(f"Fed Liquidity Tracker - Daily Update")
    print(f"{'=' * 50}\n")

    # Fetch data from NY Fed
    print(f"Fetching last {args.days} days from NY Fed...\n")
    data = fetch_latest_repo_rates(days_back=args.days)

    if not data:
        print("✗ No data fetched")
        return 1

    print(f"\n{'=' * 50}")
    print(f"Updating database...\n")

    # Insert/update database
    inserted, updated = upsert_repo_rates(data, verbose=args.verbose)

    print(f"\n{'=' * 50}")
    print(f"Update complete:")
    print(f"  ✓ Inserted: {inserted} records")
    print(f"  ✓ Updated: {updated} records")
    print(f"  ✓ Total processed: {len(data)} records")
    print(f"  ✓ Database: {DB_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
