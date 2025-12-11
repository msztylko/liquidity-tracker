"""
NY Fed Data Fetcher

Fetches daily repo market data from NY Fed APIs:
- SOFR (Secured Overnight Financing Rate)
- EFFR (Effective Federal Funds Rate)
- SRF (Standing Repo Facility usage)
- ON RRP (Overnight Reverse Repo usage)

API Documentation:
- SOFR: https://markets.newyorkfed.org/api/rates/secured/sofr/search.json
- EFFR: https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json
- SRF: https://markets.newyorkfed.org/api/srf/all/search.json
- ON RRP: https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json

Usage:
    from fetch_nyfed import fetch_repo_rates
    data = fetch_repo_rates(start_date='2024-01-01', end_date='2024-12-11')
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class NYFedAPI:
    """NY Fed Markets API client"""

    BASE_URL = "https://markets.newyorkfed.org/api"

    ENDPOINTS = {
        'sofr': '/rates/secured/sofr/search.json',
        'effr': '/rates/unsecured/effr/search.json',
        'srf': '/srf/all/search.json',
        'onrrp': '/rp/reverserepo/propositions/search.json'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Fed-Liquidity-Tracker/1.0',
            'Accept': 'application/json'
        })

    def fetch_data(self, endpoint: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetch data from NY Fed API

        Args:
            endpoint: API endpoint key (sofr, effr, srf, onrrp)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of data records
        """
        url = f"{self.BASE_URL}{self.ENDPOINTS[endpoint]}"

        params = {
            'startDate': start_date,
            'endDate': end_date,
            'format': 'json'
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Handle different response structures
            if endpoint in ['sofr', 'effr']:
                return data.get('refRates', [])
            elif endpoint == 'srf':
                return data.get('srf', {}).get('operations', [])
            elif endpoint == 'onrrp':
                return data.get('repo', {}).get('operations', [])
            else:
                return []

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            return []

    def fetch_sofr(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Fetch SOFR rates"""
        data = self.fetch_data('sofr', start_date, end_date)

        result = {}
        for record in data:
            date = record.get('effectiveDate')
            rate = record.get('percentRate')
            if date and rate is not None:
                result[date] = float(rate)

        return result

    def fetch_effr(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Fetch EFFR rates"""
        data = self.fetch_data('effr', start_date, end_date)

        result = {}
        for record in data:
            date = record.get('effectiveDate')
            rate = record.get('percentRate')
            if date and rate is not None:
                result[date] = float(rate)

        return result

    def fetch_srf(self, start_date: str, end_date: str) -> Dict[str, float]:
        """
        Fetch SRF (Standing Repo Facility) usage

        Note: SRF started in July 2021, will return empty for earlier dates
        """
        data = self.fetch_data('srf', start_date, end_date)

        result = {}
        for record in data:
            date = record.get('opDate')
            amount = record.get('totalAmtAccepted')
            if date and amount is not None:
                # Convert millions to billions
                result[date] = float(amount) / 1000.0

        return result

    def fetch_onrrp(self, start_date: str, end_date: str) -> Dict[str, float]:
        """Fetch ON RRP (Overnight Reverse Repo) usage"""
        data = self.fetch_data('onrrp', start_date, end_date)

        result = {}
        for record in data:
            date = record.get('operationDate')
            amount = record.get('totalAmtAccepted')
            if date and amount is not None:
                # Amount is already in dollars, convert to billions
                result[date] = float(amount) / 1_000_000_000.0

        return result


def fetch_repo_rates(start_date: str, end_date: str) -> List[Dict]:
    """
    Fetch all repo market data for date range

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of dictionaries with date and all rates/usage data

    Example:
        >>> data = fetch_repo_rates('2024-12-01', '2024-12-10')
        >>> print(data[0])
        {
            'date': '2024-12-02',
            'sofr': 4.56,
            'effr': 4.58,
            'srf_usage': 0.0,
            'onrrp': 234.5
        }
    """
    api = NYFedAPI()

    print(f"Fetching NY Fed data from {start_date} to {end_date}...")

    # Fetch all data sources
    sofr_data = api.fetch_sofr(start_date, end_date)
    effr_data = api.fetch_effr(start_date, end_date)
    srf_data = api.fetch_srf(start_date, end_date)
    onrrp_data = api.fetch_onrrp(start_date, end_date)

    print(f"✓ SOFR: {len(sofr_data)} records")
    print(f"✓ EFFR: {len(effr_data)} records")
    print(f"✓ SRF: {len(srf_data)} records")
    print(f"✓ ON RRP: {len(onrrp_data)} records")

    # Merge all data by date
    all_dates = set(sofr_data.keys()) | set(effr_data.keys()) | set(srf_data.keys()) | set(onrrp_data.keys())

    result = []
    for date in sorted(all_dates):
        record = {
            'date': date,
            'sofr': sofr_data.get(date),
            'effr': effr_data.get(date),
            'srf_usage': srf_data.get(date),
            'onrrp': onrrp_data.get(date)
        }
        result.append(record)

    return result


def fetch_latest_repo_rates(days_back: int = 7) -> List[Dict]:
    """
    Fetch latest repo market data (last N days)

    Args:
        days_back: Number of days to look back (default 7)

    Returns:
        List of dictionaries with date and all rates/usage data
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

    return fetch_repo_rates(start_date, end_date)


if __name__ == "__main__":
    # Test: Fetch last 7 days
    print("Testing NY Fed API fetcher...\n")

    data = fetch_latest_repo_rates(days_back=7)

    print(f"\nFetched {len(data)} days of data")

    if data:
        print("\nSample (most recent 3 days):")
        for record in data[-3:]:
            print(f"  {record['date']}: SOFR={record['sofr']}, EFFR={record['effr']}, "
                  f"SRF={record['srf_usage']}, ONRRP={record['onrrp']}")
