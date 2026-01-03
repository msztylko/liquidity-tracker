#!/usr/bin/env python3
"""
Quick database inspection utility
"""

import sqlite3
from pathlib import Path


def inspect_database():
    """Show database contents summary"""
    db_path = Path(__file__).parent / "liquidity_tracker.db"

    if not db_path.exists():
        print(f"✗ Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("DATABASE CONTENTS")
    print("=" * 80)

    # Table counts
    print("\nTable Record Counts:")
    print("-" * 80)
    tables = ['policy_rates', 'daily_rates', 'daily_operations', 'weekly_balance_sheet', 'data_update_log']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()['count']
        print(f"  {table:25} {count:>6} records")

    # Latest data dates
    print("\nLatest Data:")
    print("-" * 80)

    # Latest policy rate
    cursor.execute("SELECT effective_date, iorb, target_lower, target_upper FROM policy_rates ORDER BY effective_date DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"  Policy Rates: {row['effective_date']} - IORB {row['iorb']*100:.2f}%, Target {row['target_lower']*100:.2f}%-{row['target_upper']*100:.2f}%")
    else:
        print("  Policy Rates: No data")

    # Latest daily rates
    cursor.execute("SELECT date, sofr, effr FROM daily_rates ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"  Daily Rates:  {row['date']} - SOFR {row['sofr']*100:.2f}%, EFFR {row['effr']*100:.2f}%")
    else:
        print("  Daily Rates: No data")

    # Latest daily operations
    cursor.execute("SELECT date, onrrp_usage_billions, srf_usage_billions FROM daily_operations ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"  Daily Ops:    {row['date']} - ON RRP ${row['onrrp_usage_billions']:.1f}B, SRF ${row['srf_usage_billions']:.1f}B")
    else:
        print("  Daily Ops: No data")

    # Latest weekly balance sheet
    cursor.execute("SELECT date, total_assets_billions, reserve_balances_billions FROM weekly_balance_sheet ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"  Weekly BS:    {row['date']} - Assets ${row['total_assets_billions']:.1f}B, Reserves ${row['reserve_balances_billions']:.1f}B")
    else:
        print("  Weekly BS: No data")

    # Date ranges
    print("\nData Coverage:")
    print("-" * 80)

    for table in ['daily_rates', 'daily_operations', 'weekly_balance_sheet', 'policy_rates']:
        date_col = 'effective_date' if table == 'policy_rates' else 'date'
        cursor.execute(f"SELECT MIN({date_col}) as min_date, MAX({date_col}) as max_date FROM {table}")
        row = cursor.fetchone()
        if row['min_date']:
            print(f"  {table:25} {row['min_date']} to {row['max_date']}")
        else:
            print(f"  {table:25} No data")

    print("\n" + "=" * 80 + "\n")

    conn.close()


if __name__ == "__main__":
    inspect_database()
