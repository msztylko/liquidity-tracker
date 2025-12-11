# Fed Liquidity Tracker - Backend

Database and data collection scripts for tracking Federal Reserve liquidity indicators.

## Quick Start

### 1. Create Database

```bash
python create_database.py
```

Creates `fed_liquidity.db` with 3 tables:
- `repo_rates` - Daily repo market data (SOFR, EFFR, ON RRP)
- `fed_weekly` - Weekly Fed balance sheet and reserves
- `policy_rates` - FOMC policy rate changes (manual entry)

### 2. Backfill Historical Data

```bash
# NY Fed data only (no API key needed)
python backfill.py --start-date 2018-01-01 --skip-fed

# Or with FRED data (requires API key)
export FRED_API_KEY='your_key_here'
python backfill.py --start-date 2018-01-01
```

Get free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html

### 3. Daily Updates

```bash
# Fetch last 7 days
python update_daily.py

# Or specify number of days
python update_daily.py --days 30 --verbose
```

Schedule with cron (daily at 10 AM ET):
```
0 10 * * * cd /path/to/backend && python update_daily.py
```

### 4. Weekly Updates

```bash
# Fetch last 4 weeks
export FRED_API_KEY='your_key_here'
python update_weekly.py

# Or specify number of weeks
python update_weekly.py --weeks 8 --verbose
```

Schedule with cron (Thursdays at 10 AM ET):
```
0 10 * * 4 cd /path/to/backend && python update_weekly.py
```

## Files

### Database Scripts
- **[create_database.py](create_database.py)** - Create SQLite database with schema
- **[verify_schema.py](verify_schema.py)** - Verify database structure

### Data Fetchers
- **[fetch_nyfed.py](fetch_nyfed.py)** - Fetch daily repo data from NY Fed APIs
  - SOFR (Secured Overnight Financing Rate)
  - EFFR (Effective Federal Funds Rate)
  - ON RRP (Overnight Reverse Repo usage)
  - SRF (Standing Repo Facility) - *currently unavailable via API*

- **[fetch_fred.py](fetch_fred.py)** - Fetch weekly Fed data from FRED API
  - WALCL: Total Fed Assets (Balance Sheet)
  - WRESBAL: Reserve Balances
  - WTREGEN: Treasury General Account (optional)

### Update Scripts
- **[update_daily.py](update_daily.py)** - Update database with latest daily repo rates
- **[update_weekly.py](update_weekly.py)** - Update database with latest weekly Fed data
- **[backfill.py](backfill.py)** - Backfill historical data from 2018-present

## Database Schema

### Table: repo_rates (Daily Data)

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Primary key |
| sofr | REAL | SOFR rate (%) |
| effr | REAL | EFFR rate (%) |
| srf_usage | REAL | SRF usage (billions) - currently NULL |
| onrrp | REAL | ON RRP usage (billions) |
| sofr_iorb_spread | REAL | Calculated: SOFR - IORB |
| effr_target_mid | REAL | Calculated: EFFR - target midpoint |
| is_quarter_end | BOOLEAN | Quarter-end flag |
| is_month_end | BOOLEAN | Month-end flag |

### Table: fed_weekly (Weekly Data)

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Wednesday date |
| balance_sheet | REAL | Total Fed assets (billions) |
| reserves | REAL | Reserve balances (billions) |
| tga | REAL | Treasury General Account (optional) |
| balance_sheet_change | REAL | Week-over-week change |
| reserves_change | REAL | Week-over-week change |

### Table: policy_rates (Policy Changes)

| Column | Type | Description |
|--------|------|-------------|
| effective_date | DATE | Date rate change takes effect |
| iorb | REAL | Interest on Reserve Balances (%) |
| target_lower | REAL | Fed Funds target lower bound (%) |
| target_upper | REAL | Fed Funds target upper bound (%) |
| fomc_meeting_date | DATE | FOMC meeting date |
| notes | TEXT | Optional notes |

**Note:** Policy rates require manual entry from FOMC statements.

## Data Sources

### NY Fed Markets API (No API Key Required)
- **SOFR:** https://markets.newyorkfed.org/api/rates/secured/sofr/search.json
- **EFFR:** https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json
- **ON RRP:** https://markets.newyorkfed.org/api/rp/reverserepo/propositions/search.json
- Documentation: https://markets.newyorkfed.org/static/docs/markets-api.html

### FRED API (Free API Key Required)
- **WALCL** (Balance Sheet): https://fred.stlouisfed.org/series/WALCL
- **WRESBAL** (Reserves): https://fred.stlouisfed.org/series/WRESBAL
- Get API key: https://fred.stlouisfed.org/docs/api/api_key.html

## Usage Examples

### Fetch Last Week of Repo Data
```python
from fetch_nyfed import fetch_latest_repo_rates

data = fetch_latest_repo_rates(days_back=7)
for record in data:
    print(f"{record['date']}: SOFR={record['sofr']}, ONRRP={record['onrrp']}")
```

### Fetch Specific Date Range
```python
from fetch_nyfed import fetch_repo_rates

data = fetch_repo_rates('2024-01-01', '2024-12-31')
print(f"Fetched {len(data)} days of data")
```

### Query Database
```python
import sqlite3

conn = sqlite3.connect('fed_liquidity.db')
cursor = conn.cursor()

# Get latest repo rates
cursor.execute("""
    SELECT date, sofr, effr, onrrp
    FROM repo_rates
    ORDER BY date DESC
    LIMIT 5
""")

for row in cursor.fetchall():
    print(row)
```

## Current Status

**Database:** ✓ Created with 3 tables
**Repo Rates:** ✓ Working (SOFR, EFFR, ON RRP)
**Fed Weekly:** Ready (requires FRED API key)
**Policy Rates:** Manual entry required

**Test Data Loaded:** 19 records from Nov 25, 2024 to Dec 10, 2025

## Known Issues

1. **SRF Data Not Available:** The Standing Repo Facility endpoint returns 400 errors. SRF usage will remain NULL until a working endpoint is found.

2. **Policy Rates Manual Entry:** FOMC policy rates must be entered manually as there's no API. Consider automating via web scraping FOMC statements.

3. **Weekend/Holiday Gaps:** Repo markets are closed on weekends and holidays, so those dates will have NULL values for rates.

## Next Steps

1. **Backfill Historical Data:**
   ```bash
   python backfill.py --start-date 2018-01-01
   ```

2. **Set Up Cron Jobs:**
   - Daily: `python update_daily.py`
   - Weekly: `python update_weekly.py`

3. **Add Policy Rates:**
   Manually insert FOMC rate decisions:
   ```sql
   INSERT INTO policy_rates (effective_date, iorb, target_lower, target_upper)
   VALUES ('2024-12-01', 4.40, 4.25, 4.50);
   ```

4. **Calculate Spreads:**
   After loading policy rates, calculate derived fields:
   ```sql
   UPDATE repo_rates
   SET sofr_iorb_spread = sofr - (
       SELECT iorb FROM policy_rates
       WHERE effective_date <= repo_rates.date
       ORDER BY effective_date DESC LIMIT 1
   );
   ```

## Dependencies

- Python 3.7+
- `requests` - HTTP library for API calls
- `sqlite3` - Built-in Python SQLite support

Install dependencies:
```bash
pip install requests
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

## License

MIT
