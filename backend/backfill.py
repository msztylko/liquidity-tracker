"""
Backfill Historical Data

Backfills database with historical data from 2018 to present:
- Daily repo rates from NY Fed
- Weekly Fed balance sheet data from FRED

This should be run once to populate the database with historical data,
then use update_daily.py and update_weekly.py for ongoing updates.

Usage:
    python backfill.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--skip-repo] [--skip-fed] [--verbose]

    --start-date  : Start date (default: 2018-01-01)
    --end-date    : End date (default: today)
    --skip-repo   : Skip repo rates backfill
    --skip-fed    : Skip Fed weekly data backfill
    --verbose     : Show detailed output

Requirements:
    - FRED API key for Fed data: export FRED_API_KEY='your_key_here'
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fetch_nyfed import fetch_repo_rates
from fetch_fred import fetch_fed_weekly
from update_daily import upsert_repo_rates
from update_weekly import upsert_fed_weekly


def backfill_in_chunks(start_date: str, end_date: str, chunk_days: int,
                       fetch_func, upsert_func, data_name: str, verbose: bool = False):
    """
    Backfill data in chunks to avoid overwhelming APIs

    Args:
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        chunk_days: Number of days per chunk
        fetch_func: Function to fetch data
        upsert_func: Function to insert data
        data_name: Name of data being backfilled (for logging)
        verbose: Show detailed output
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    total_inserted = 0
    total_updated = 0
    chunk_num = 0

    current = start
    while current <= end:
        chunk_end = min(current + timedelta(days=chunk_days), end)

        chunk_start_str = current.strftime('%Y-%m-%d')
        chunk_end_str = chunk_end.strftime('%Y-%m-%d')

        chunk_num += 1
        print(f"\n[Chunk {chunk_num}] {chunk_start_str} to {chunk_end_str}")

        # Fetch data
        try:
            data = fetch_func(chunk_start_str, chunk_end_str)
        except Exception as e:
            print(f"  ✗ Error fetching data: {e}")
            current = chunk_end + timedelta(days=1)
            continue

        if not data:
            print(f"  ⚠ No data fetched")
            current = chunk_end + timedelta(days=1)
            continue

        # Insert data
        try:
            inserted, updated = upsert_func(data, verbose=verbose)
            total_inserted += inserted
            total_updated += updated

            if not verbose:
                print(f"  ✓ Inserted: {inserted}, Updated: {updated}")

        except Exception as e:
            print(f"  ✗ Error inserting data: {e}")

        current = chunk_end + timedelta(days=1)

    print(f"\n{data_name} backfill complete:")
    print(f"  Total inserted: {total_inserted}")
    print(f"  Total updated: {total_updated}")
    print(f"  Total records: {total_inserted + total_updated}")


def backfill_repo_rates(start_date: str, end_date: str, verbose: bool = False):
    """Backfill daily repo rates from NY Fed"""
    print(f"\n{'=' * 60}")
    print(f"BACKFILLING REPO RATES (NY Fed)")
    print(f"{'=' * 60}")
    print(f"Period: {start_date} to {end_date}")

    # Backfill in 90-day chunks to be nice to the API
    backfill_in_chunks(
        start_date=start_date,
        end_date=end_date,
        chunk_days=90,
        fetch_func=fetch_repo_rates,
        upsert_func=upsert_repo_rates,
        data_name="Repo rates",
        verbose=verbose
    )


def backfill_fed_weekly(start_date: str, end_date: str, verbose: bool = False):
    """Backfill weekly Fed balance sheet data from FRED"""
    print(f"\n{'=' * 60}")
    print(f"BACKFILLING FED WEEKLY DATA (FRED)")
    print(f"{'=' * 60}")
    print(f"Period: {start_date} to {end_date}")

    # FRED is more lenient, can do larger chunks
    def fetch_wrapper(start: str, end: str):
        return fetch_fed_weekly(start, end, include_tga=False)

    backfill_in_chunks(
        start_date=start_date,
        end_date=end_date,
        chunk_days=365,  # 1 year chunks
        fetch_func=fetch_wrapper,
        upsert_func=upsert_fed_weekly,
        data_name="Fed weekly data",
        verbose=verbose
    )


def main():
    """Main backfill function"""
    parser = argparse.ArgumentParser(description='Backfill historical Fed liquidity data')
    parser.add_argument('--start-date', default='2018-01-01', help='Start date (default: 2018-01-01)')
    parser.add_argument('--end-date', default=datetime.now().strftime('%Y-%m-%d'),
                       help='End date (default: today)')
    parser.add_argument('--skip-repo', action='store_true', help='Skip repo rates backfill')
    parser.add_argument('--skip-fed', action='store_true', help='Skip Fed weekly backfill')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()

    print(f"\n{'#' * 60}")
    print(f"# FED LIQUIDITY TRACKER - HISTORICAL DATA BACKFILL")
    print(f"{'#' * 60}")
    print(f"\nBackfill period: {args.start_date} to {args.end_date}")
    print(f"\nThis will fetch historical data from:")
    if not args.skip_repo:
        print(f"  • NY Fed (SOFR, EFFR, ON RRP)")
    if not args.skip_fed:
        print(f"  • FRED (Balance Sheet, Reserves)")
    print(f"\nThis may take several minutes depending on date range...")

    # Confirm before proceeding
    response = input("\nProceed with backfill? (yes/no): ")
    if response.lower() != 'yes':
        print("Backfill cancelled")
        return 1

    start_time = datetime.now()

    # Backfill repo rates
    if not args.skip_repo:
        try:
            backfill_repo_rates(args.start_date, args.end_date, verbose=args.verbose)
        except Exception as e:
            print(f"\n✗ Repo rates backfill failed: {e}")

    # Backfill Fed weekly data
    if not args.skip_fed:
        try:
            backfill_fed_weekly(args.start_date, args.end_date, verbose=args.verbose)
        except ValueError as e:
            print(f"\n✗ Fed weekly backfill failed: {e}")
            print("  Hint: Set FRED_API_KEY environment variable")
        except Exception as e:
            print(f"\n✗ Fed weekly backfill failed: {e}")

    # Summary
    elapsed = datetime.now() - start_time
    print(f"\n{'#' * 60}")
    print(f"# BACKFILL COMPLETE")
    print(f"{'#' * 60}")
    print(f"\nTotal time: {elapsed.total_seconds():.1f} seconds")
    print(f"\nNext steps:")
    print(f"  1. Run update_daily.py daily to fetch new repo rates")
    print(f"  2. Run update_weekly.py weekly to fetch new Fed data")
    print(f"  3. Query database to verify data quality")

    return 0


if __name__ == "__main__":
    sys.exit(main())
