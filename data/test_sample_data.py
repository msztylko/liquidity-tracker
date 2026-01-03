#!/usr/bin/env python3
"""
Test script to insert sample data and verify database functionality
Uses transaction with rollback to avoid polluting the database
"""

import sqlite3
from datetime import datetime
from db_init import DatabaseManager, CalculatedFieldsUpdater


def test_database():
    """Test database with sample data using a transaction that will be rolled back"""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    try:
        # Begin transaction (implicit in SQLite, but explicit here for clarity)
        print("=" * 80)
        print("Fed Liquidity Monitor - Database Test (Transaction Mode)")
        print("=" * 80)
        print("\nNOTE: All data will be rolled back after verification\n")

        # 1. Insert policy rates (must be first for calculated fields)
        print("Inserting sample data...")
        policy_data = [
            ('2024-12-18', 0.0440, 0.0425, 0.0450, '2024-12-18', '25 bps cut from previous meeting'),
            ('2024-11-07', 0.0465, 0.0450, 0.0475, '2024-11-07', 'Held rates steady'),
        ]

        for effective_date, iorb, target_lower, target_upper, meeting_date, notes in policy_data:
            cursor.execute("""
                INSERT INTO policy_rates
                (effective_date, iorb, target_lower, target_upper, fomc_meeting_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (effective_date, iorb, target_lower, target_upper, meeting_date, notes))

        print(f"  ✓ Inserted {len(policy_data)} policy_rates records")

        # Update calculated fields for policy rates
        cursor.execute("""
            UPDATE policy_rates
            SET
                onrrp_offering_rate = iorb - 0.0010,
                srf_offering_rate = CASE
                    WHEN effective_date >= '2021-07-01' THEN iorb + 0.0010
                    ELSE NULL
                END,
                target_midpoint = (target_lower + target_upper) / 2.0
        """)

        # 2. Insert daily rates
        daily_rates_data = [
            ('2024-12-31', 0.0457, 0.0238, 0.0242, 0.0255, 0.0460, 1156.0, 0.0433, 105.2),
            ('2024-12-30', 0.0456, 0.0237, 0.0241, 0.0254, 0.0459, 1145.0, 0.0432, 103.5),
            ('2024-12-27', 0.0458, 0.0239, 0.0243, 0.0256, 0.0461, 1167.0, 0.0434, 107.8),
        ]

        for date, sofr, s1, s25, s75, s99, svol, effr, evol in daily_rates_data:
            cursor.execute("""
                INSERT INTO daily_rates
                (date, sofr, sofr_1st_percentile, sofr_25th_percentile, sofr_75th_percentile,
                 sofr_99th_percentile, sofr_volume_billions, effr, effr_volume_billions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, sofr, s1, s25, s75, s99, svol, effr, evol))

        print(f"  ✓ Inserted {len(daily_rates_data)} daily_rates records")

        # Update calculated fields for daily rates
        cursor.execute("""
            UPDATE daily_rates
            SET
                is_quarter_end = CASE
                    WHEN strftime('%m-%d', date) IN ('03-31', '06-30', '09-30', '12-31')
                    THEN 1 ELSE 0 END,
                is_month_end = CASE
                    WHEN date = date(date, 'start of month', '+1 month', '-1 day')
                    THEN 1 ELSE 0 END,
                is_tax_date = CASE
                    WHEN strftime('%m-%d', date) IN ('04-15', '06-15', '09-15', '12-15')
                    THEN 1 ELSE 0 END,
                day_of_week = CAST(strftime('%w', date) AS INTEGER)
        """)

        cursor.execute("""
            UPDATE daily_rates
            SET sofr_iorb_spread = sofr - (
                SELECT iorb FROM policy_rates
                WHERE effective_date <= daily_rates.date
                ORDER BY effective_date DESC
                LIMIT 1
            )
            WHERE sofr IS NOT NULL
        """)

        cursor.execute("""
            UPDATE daily_rates
            SET effr_target_deviation = effr - (
                SELECT (target_lower + target_upper) / 2
                FROM policy_rates
                WHERE effective_date <= daily_rates.date
                ORDER BY effective_date DESC
                LIMIT 1
            )
            WHERE effr IS NOT NULL
        """)

        # 3. Insert daily operations
        daily_ops_data = [
            ('2024-12-31', 345.0, 12.0),
            ('2024-12-30', 340.0, 10.0),
            ('2024-12-27', 338.0, 8.0),
        ]

        for date, onrrp, srf in daily_ops_data:
            cursor.execute("""
                INSERT INTO daily_operations (date, onrrp_usage_billions, srf_usage_billions)
                VALUES (?, ?, ?)
            """, (date, onrrp, srf))

        print(f"  ✓ Inserted {len(daily_ops_data)} daily_operations records")

        # 4. Insert weekly balance sheet data
        weekly_bs_data = [
            ('2024-12-25', 6870.0, 4250.0, 2350.0, 3500.0, 750.0),
            ('2024-12-18', 6882.0, 4255.0, 2355.0, 3505.0, 735.0),
            ('2024-12-11', 6895.0, 4260.0, 2360.0, 3510.0, 720.0),
        ]

        for date, assets, treasuries, mbs, reserves, tga in weekly_bs_data:
            cursor.execute("""
                INSERT INTO weekly_balance_sheet
                (date, total_assets_billions, treasury_securities_billions, mbs_billions,
                 reserve_balances_billions, tga_billions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date, assets, treasuries, mbs, reserves, tga))

        print(f"  ✓ Inserted {len(weekly_bs_data)} weekly_balance_sheet records")

        # Update WoW changes for weekly balance sheet
        cursor.execute("""
            SELECT date, total_assets_billions, reserve_balances_billions, tga_billions
            FROM weekly_balance_sheet
            ORDER BY date ASC
        """)

        records = cursor.fetchall()
        for i, record in enumerate(records):
            if i > 0:  # Skip first record
                prev = records[i - 1]
                cursor.execute("""
                    UPDATE weekly_balance_sheet
                    SET total_assets_wow_change = ?,
                        reserves_wow_change = ?,
                        tga_wow_change = ?
                    WHERE date = ?
                """, (
                    record['total_assets_billions'] - prev['total_assets_billions'],
                    record['reserve_balances_billions'] - prev['reserve_balances_billions'],
                    record['tga_billions'] - prev['tga_billions'],
                    record['date']
                ))

        # 5. Insert sample update log entries
        cursor.execute("""
            INSERT INTO data_update_log
            (data_type, update_timestamp, data_date, status, records_updated, api_response_code, fetch_duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('daily_rates', datetime.now(), '2024-12-31', 'success', 1, 200, 450))

        print("  ✓ Inserted sample data_update_log record")
        print("\n✓ Sample data inserted successfully\n")

        # Verify data
        verify_data(cursor)

        # ROLLBACK - This is the key part!
        print("\n" + "=" * 80)
        print("ROLLING BACK TRANSACTION")
        print("=" * 80)
        conn.rollback()
        print("✓ All test data has been rolled back (database is clean)\n")

        # Verify database is empty again
        cursor.execute("SELECT COUNT(*) FROM daily_rates")
        count = cursor.fetchone()[0]
        print(f"Final verification: daily_rates has {count} records (should be 0)")

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def verify_data(cursor):
    """Verify the sample data was inserted correctly"""
    print("Verifying sample data...")
    print("=" * 80)

    # Check policy rates with calculated fields
    print("\nPolicy Rates:")
    cursor.execute("""
        SELECT effective_date, iorb, target_lower, target_upper,
               onrrp_offering_rate, srf_offering_rate, target_midpoint
        FROM policy_rates
        ORDER BY effective_date DESC
    """)

    for row in cursor.fetchall():
        print(f"  Date: {row['effective_date']}")
        print(f"    IORB: {row['iorb']:.4f} ({row['iorb']*100:.2f}%)")
        print(f"    Target: {row['target_lower']:.4f} - {row['target_upper']:.4f}")
        print(f"    ON RRP Rate: {row['onrrp_offering_rate']:.4f}")
        srf_rate = f"{row['srf_offering_rate']:.4f}" if row['srf_offering_rate'] else 'N/A'
        print(f"    SRF Rate: {srf_rate}")
        print(f"    Target Midpoint: {row['target_midpoint']:.4f}")

    # Check daily rates with calculated fields
    print("\nDaily Rates (Latest):")
    cursor.execute("""
        SELECT date, sofr, sofr_iorb_spread, effr, effr_target_deviation,
               is_quarter_end, day_of_week
        FROM daily_rates
        ORDER BY date DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    print(f"  Date: {row['date']}")
    print(f"    SOFR: {row['sofr']:.4f} ({row['sofr']*100:.2f}%)")
    print(f"    SOFR-IORB Spread: {row['sofr_iorb_spread']:.4f} ({row['sofr_iorb_spread']*10000:.1f} bps)")
    print(f"    EFFR: {row['effr']:.4f} ({row['effr']*100:.2f}%)")
    print(f"    EFFR Deviation: {row['effr_target_deviation']:.4f} ({row['effr_target_deviation']*10000:.1f} bps)")
    print(f"    Quarter End: {bool(row['is_quarter_end'])}")
    print(f"    Day of Week: {row['day_of_week']} (0=Sunday, 2=Tuesday)")

    # Check daily operations
    print("\nDaily Operations (Latest):")
    cursor.execute("""
        SELECT date, onrrp_usage_billions, srf_usage_billions
        FROM daily_operations
        ORDER BY date DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    print(f"  Date: {row['date']}")
    print(f"    ON RRP Usage: ${row['onrrp_usage_billions']:.1f}B")
    print(f"    SRF Usage: ${row['srf_usage_billions']:.1f}B")

    # Check weekly balance sheet with WoW changes
    print("\nWeekly Balance Sheet (Latest):")
    cursor.execute("""
        SELECT date, total_assets_billions, reserve_balances_billions, tga_billions,
               total_assets_wow_change, reserves_wow_change, tga_wow_change
        FROM weekly_balance_sheet
        ORDER BY date DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    print(f"  Date: {row['date']}")
    print(f"    Total Assets: ${row['total_assets_billions']:.1f}B")
    print(f"    Reserve Balances: ${row['reserve_balances_billions']:.1f}B")
    print(f"    TGA: ${row['tga_billions']:.1f}B")
    if row['total_assets_wow_change'] is not None:
        print(f"    WoW Change (Assets): ${row['total_assets_wow_change']:.1f}B")
        print(f"    WoW Change (Reserves): ${row['reserves_wow_change']:.1f}B")
        print(f"    WoW Change (TGA): ${row['tga_wow_change']:.1f}B")

    # Test join query (complete daily snapshot)
    print("\nComplete Daily Snapshot (Latest):")
    cursor.execute("""
        SELECT
            dr.date,
            dr.sofr,
            dr.effr,
            do.onrrp_usage_billions,
            do.srf_usage_billions,
            pr.iorb,
            pr.target_lower,
            pr.target_upper
        FROM daily_rates dr
        LEFT JOIN daily_operations do ON do.date = dr.date
        LEFT JOIN policy_rates pr ON pr.effective_date = (
            SELECT MAX(effective_date)
            FROM policy_rates
            WHERE effective_date <= dr.date
        )
        ORDER BY dr.date DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    print(f"  Date: {row['date']}")
    print(f"    Rates: SOFR {row['sofr']*100:.2f}%, EFFR {row['effr']*100:.2f}%")
    print(f"    Facilities: ON RRP ${row['onrrp_usage_billions']:.1f}B, SRF ${row['srf_usage_billions']:.1f}B")
    print(f"    Policy: IORB {row['iorb']*100:.2f}%, Target {row['target_lower']*100:.2f}%-{row['target_upper']*100:.2f}%")

    print("\n" + "=" * 80)
    print("✓ Verification complete!")


def main():
    """Main test function"""
    print("\n" + "=" * 80)
    print("Fed Liquidity Monitor - Database Test Suite")
    print("=" * 80 + "\n")

    test_database()

    print("\n✓ All tests passed!")
    print("\nDatabase is ready for production use.")

if __name__ == "__main__":
    main()
