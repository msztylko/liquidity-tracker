"""
FRED API Data Fetcher

Fetches weekly Fed balance sheet data from FRED (Federal Reserve Economic Data):
- WALCL: Total Fed Assets (Balance Sheet)
- WRESBAL: Reserve Balances with Federal Reserve Banks
- WTREGEN: Treasury General Account (optional)

API Documentation: https://fred.stlouisfed.org/docs/api/fred/

Requirements:
    - FRED API key (free): https://fred.stlouisfed.org/docs/api/api_key.html
    - Set environment variable: FRED_API_KEY

Usage:
    export FRED_API_KEY="your_api_key_here"
    from fetch_fred import fetch_fed_weekly
    data = fetch_fed_weekly(start_date='2024-01-01', end_date='2024-12-11')
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class FREDAPI:
    """FRED (Federal Reserve Economic Data) API client"""

    BASE_URL = "https://api.stlouisfed.org/fred"

    SERIES = {
        'balance_sheet': 'WALCL',    # Assets: Total Assets: Total Assets (Less Eliminations from Consolidation): Wednesday Level
        'reserves': 'WRESBAL',        # Reserve Balances with Federal Reserve Banks: Wednesday Level
        'tga': 'WTREGEN'              # Treasury General Account: Wednesday Level
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FRED API client

        Args:
            api_key: FRED API key (if not provided, reads from FRED_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('FRED_API_KEY')

        if not self.api_key:
            raise ValueError(
                "FRED API key required. Set FRED_API_KEY environment variable or pass api_key parameter.\n"
                "Get free API key at: https://fred.stlouisfed.org/docs/api/api_key.html"
            )

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Fed-Liquidity-Tracker/1.0',
            'Accept': 'application/json'
        })

    def fetch_series(self, series_id: str, start_date: str, end_date: str) -> Dict[str, float]:
        """
        Fetch data for a FRED series

        Args:
            series_id: FRED series ID (e.g., 'WALCL')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary mapping date -> value
        """
        url = f"{self.BASE_URL}/series/observations"

        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            observations = data.get('observations', [])

            result = {}
            for obs in observations:
                date = obs.get('date')
                value = obs.get('value')

                # Skip missing values (represented as '.')
                if date and value and value != '.':
                    result[date] = float(value)

            return result

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {series_id}: {e}")
            return {}

    def fetch_balance_sheet(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Fetch Fed total assets (balance sheet)"""
        return self.fetch_series(self.SERIES['balance_sheet'], start_date, end_date)

    def fetch_reserves(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Fetch reserve balances with Federal Reserve Banks"""
        return self.fetch_series(self.SERIES['reserves'], start_date, end_date)

    def fetch_tga(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Fetch Treasury General Account balance"""
        return self.fetch_series(self.SERIES['tga'], start_date, end_date)


def fetch_fed_weekly(start_date: str, end_date: str, include_tga: bool = False) -> List[Dict]:
    """
    Fetch all Fed weekly data for date range

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        include_tga: Whether to include Treasury General Account data

    Returns:
        List of dictionaries with date and all Fed data

    Example:
        >>> data = fetch_fed_weekly('2024-12-01', '2024-12-11')
        >>> print(data[0])
        {
            'date': '2024-12-04',
            'balance_sheet': 6873.2,
            'reserves': 1420.5,
            'tga': 234.1
        }
    """
    api = FREDAPI()

    print(f"Fetching FRED data from {start_date} to {end_date}...")

    # Fetch all data sources
    balance_sheet_data = api.fetch_balance_sheet(start_date, end_date)
    reserves_data = api.fetch_reserves(start_date, end_date)

    tga_data = {}
    if include_tga:
        tga_data = api.fetch_tga(start_date, end_date)

    print(f"✓ Balance Sheet: {len(balance_sheet_data)} records")
    print(f"✓ Reserves: {len(reserves_data)} records")
    if include_tga:
        print(f"✓ TGA: {len(tga_data)} records")

    # Merge all data by date (Wednesday dates)
    all_dates = set(balance_sheet_data.keys()) | set(reserves_data.keys())
    if include_tga:
        all_dates |= set(tga_data.keys())

    result = []
    for date in sorted(all_dates):
        record = {
            'date': date,
            'balance_sheet': balance_sheet_data.get(date),
            'reserves': reserves_data.get(date)
        }

        if include_tga:
            record['tga'] = tga_data.get(date)

        result.append(record)

    return result


def fetch_latest_fed_weekly(weeks_back: int = 4, include_tga: bool = False) -> List[Dict]:
    """
    Fetch latest Fed weekly data (last N weeks)

    Args:
        weeks_back: Number of weeks to look back (default 4)
        include_tga: Whether to include Treasury General Account data

    Returns:
        List of dictionaries with date and all Fed data
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(weeks=weeks_back)).strftime('%Y-%m-%d')

    return fetch_fed_weekly(start_date, end_date, include_tga=include_tga)


if __name__ == "__main__":
    # Test: Fetch last 4 weeks
    print("Testing FRED API fetcher...\n")

    try:
        data = fetch_latest_fed_weekly(weeks_back=4)

        print(f"\nFetched {len(data)} weeks of data")

        if data:
            print("\nSample (most recent 3 weeks):")
            for record in data[-3:]:
                bs = record['balance_sheet']
                res = record['reserves']
                print(f"  {record['date']}: Balance Sheet={bs:,.1f}B, Reserves={res:,.1f}B")

    except ValueError as e:
        print(f"\n✗ Error: {e}")
        print("\nTo use this script, you need a free FRED API key:")
        print("1. Get API key: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Set environment variable: export FRED_API_KEY='your_key_here'")
