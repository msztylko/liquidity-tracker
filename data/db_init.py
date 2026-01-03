#!/usr/bin/env python3
"""
Fed Liquidity Monitor - Database Initialization
Initializes SQLite database with schema and provides utility functions
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional


class DatabaseManager:
    """Manages database initialization and operations"""

    def __init__(self, db_path: str = "liquidity_tracker.db"):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file (relative to data directory)
        """
        self.db_dir = Path(__file__).parent
        self.db_path = self.db_dir / db_path
        self.schema_path = self.db_dir / "schema.sql"

    def create_database(self) -> None:
        """Create database from schema.sql file"""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        # Read schema
        with open(self.schema_path, 'r') as f:
            schema_sql = f.read()

        # Create database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Execute schema (SQLite allows multiple statements with executescript)
            cursor.executescript(schema_sql)
            conn.commit()
            print(f"✓ Database created successfully: {self.db_path}")

            # Verify tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✓ Created {len(tables)} tables: {', '.join(tables)}")

        except sqlite3.Error as e:
            print(f"✗ Error creating database: {e}")
            raise
        finally:
            conn.close()

    def database_exists(self) -> bool:
        """Check if database file exists"""
        return self.db_path.exists()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def reset_database(self) -> None:
        """Delete and recreate database (USE WITH CAUTION)"""
        if self.db_path.exists():
            self.db_path.unlink()
            print(f"✓ Deleted existing database: {self.db_path}")
        self.create_database()


class CalculatedFieldsUpdater:
    """Updates calculated fields in database tables"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def update_daily_rates_spreads(self, date: Optional[str] = None) -> int:
        """
        Update sofr_iorb_spread and effr_target_deviation for daily_rates

        Args:
            date: Specific date to update (YYYY-MM-DD) or None for all records

        Returns:
            Number of records updated
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        try:
            # Update SOFR-IORB spread
            if date:
                cursor.execute("""
                    UPDATE daily_rates
                    SET sofr_iorb_spread = sofr - (
                        SELECT iorb FROM policy_rates
                        WHERE effective_date <= daily_rates.date
                        ORDER BY effective_date DESC
                        LIMIT 1
                    )
                    WHERE date = ? AND sofr IS NOT NULL
                """, (date,))
            else:
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

            sofr_updates = cursor.rowcount

            # Update EFFR target deviation
            if date:
                cursor.execute("""
                    UPDATE daily_rates
                    SET effr_target_deviation = effr - (
                        SELECT (target_lower + target_upper) / 2
                        FROM policy_rates
                        WHERE effective_date <= daily_rates.date
                        ORDER BY effective_date DESC
                        LIMIT 1
                    )
                    WHERE date = ? AND effr IS NOT NULL
                """, (date,))
            else:
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

            effr_updates = cursor.rowcount
            conn.commit()

            total_updates = sofr_updates + effr_updates
            print(f"✓ Updated {sofr_updates} SOFR spreads and {effr_updates} EFFR deviations")
            return total_updates

        except sqlite3.Error as e:
            conn.rollback()
            print(f"✗ Error updating spreads: {e}")
            raise
        finally:
            conn.close()

    def update_daily_rates_metadata(self, date: Optional[str] = None) -> int:
        """
        Update date metadata fields (is_quarter_end, day_of_week, etc.)

        Args:
            date: Specific date to update (YYYY-MM-DD) or None for all records

        Returns:
            Number of records updated
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        try:
            where_clause = "WHERE date = ?" if date else ""
            params = (date,) if date else ()

            cursor.execute(f"""
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
                {where_clause}
            """, params)

            updated = cursor.rowcount
            conn.commit()
            print(f"✓ Updated metadata for {updated} daily_rates records")
            return updated

        except sqlite3.Error as e:
            conn.rollback()
            print(f"✗ Error updating metadata: {e}")
            raise
        finally:
            conn.close()

    def update_weekly_balance_sheet_changes(self, date: Optional[str] = None) -> int:
        """
        Update week-over-week changes for balance sheet data

        Args:
            date: Specific date to update (YYYY-MM-DD) or None for all records

        Returns:
            Number of records updated
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        try:
            # Build query based on whether we're updating one date or all
            if date:
                # Update specific date
                cursor.execute("""
                    UPDATE weekly_balance_sheet
                    SET
                        total_assets_wow_change = total_assets_billions - (
                            SELECT total_assets_billions
                            FROM weekly_balance_sheet AS prev
                            WHERE prev.date < weekly_balance_sheet.date
                            ORDER BY prev.date DESC
                            LIMIT 1
                        ),
                        reserves_wow_change = reserve_balances_billions - (
                            SELECT reserve_balances_billions
                            FROM weekly_balance_sheet AS prev
                            WHERE prev.date < weekly_balance_sheet.date
                            ORDER BY prev.date DESC
                            LIMIT 1
                        ),
                        tga_wow_change = tga_billions - (
                            SELECT tga_billions
                            FROM weekly_balance_sheet AS prev
                            WHERE prev.date < weekly_balance_sheet.date
                            ORDER BY prev.date DESC
                            LIMIT 1
                        )
                    WHERE date = ?
                """, (date,))
            else:
                # Update all records (more complex, requires iterating)
                cursor.execute("""
                    SELECT date, total_assets_billions, reserve_balances_billions, tga_billions
                    FROM weekly_balance_sheet
                    ORDER BY date ASC
                """)

                records = cursor.fetchall()
                updated = 0

                for i, record in enumerate(records):
                    if i == 0:
                        # First record has no previous week
                        cursor.execute("""
                            UPDATE weekly_balance_sheet
                            SET total_assets_wow_change = NULL,
                                reserves_wow_change = NULL,
                                tga_wow_change = NULL
                            WHERE date = ?
                        """, (record['date'],))
                    else:
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
                            record['tga_billions'] - prev['tga_billions'] if record['tga_billions'] and prev['tga_billions'] else None,
                            record['date']
                        ))
                    updated += 1

            conn.commit()
            updated = cursor.rowcount if date else len(records)
            print(f"✓ Updated WoW changes for {updated} weekly_balance_sheet records")
            return updated

        except sqlite3.Error as e:
            conn.rollback()
            print(f"✗ Error updating WoW changes: {e}")
            raise
        finally:
            conn.close()

    def update_policy_rates_calculated(self, effective_date: Optional[str] = None) -> int:
        """
        Update calculated fields for policy_rates (facility rates and midpoint)

        Args:
            effective_date: Specific date to update (YYYY-MM-DD) or None for all records

        Returns:
            Number of records updated
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        try:
            where_clause = "WHERE effective_date = ?" if effective_date else ""
            params = (effective_date,) if effective_date else ()

            cursor.execute(f"""
                UPDATE policy_rates
                SET
                    onrrp_offering_rate = iorb - 0.0010,
                    srf_offering_rate = CASE
                        WHEN effective_date >= '2021-07-01' THEN iorb + 0.0010
                        ELSE NULL
                    END,
                    target_midpoint = (target_lower + target_upper) / 2.0
                {where_clause}
            """, params)

            updated = cursor.rowcount
            conn.commit()
            print(f"✓ Updated calculated fields for {updated} policy_rates records")
            return updated

        except sqlite3.Error as e:
            conn.rollback()
            print(f"✗ Error updating policy rates: {e}")
            raise
        finally:
            conn.close()

    def update_all_calculated_fields(self) -> None:
        """Update all calculated fields in all tables"""
        print("\nUpdating all calculated fields...")
        self.update_policy_rates_calculated()
        self.update_daily_rates_metadata()
        self.update_daily_rates_spreads()
        self.update_weekly_balance_sheet_changes()
        print("✓ All calculated fields updated")


def main():
    """Initialize database and run basic checks"""
    print("Fed Liquidity Monitor - Database Initialization")
    print("=" * 60)

    # Initialize database manager
    db_manager = DatabaseManager()

    # Check if database exists
    if db_manager.database_exists():
        print(f"⚠ Database already exists: {db_manager.db_path}")
        response = input("Delete and recreate? (yes/no): ").strip().lower()
        if response == 'yes':
            db_manager.reset_database()
        else:
            print("Keeping existing database")
            return
    else:
        db_manager.create_database()

    # Verify database structure
    print("\nVerifying database structure...")
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    # Check each table
    for table in ['daily_rates', 'daily_operations', 'weekly_balance_sheet', 'policy_rates', 'data_update_log']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")

    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"\n✓ Created {len(indexes)} indexes")

    conn.close()
    print("\n✓ Database initialization complete!")
    print(f"Database location: {db_manager.db_path}")


if __name__ == "__main__":
    main()
