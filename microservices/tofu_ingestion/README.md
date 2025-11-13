# TOFU Leads Ingestion Microservice

## Overview

This microservice fetches marketing leads (Top of Funnel) from Google Sheets and stores them incrementally in Supabase. It processes three Google Sheets sources and ensures data quality through validation, deduplication, and incremental loading.

## Data Flow

```
Google Sheets (3 sources)
         ↓
   Fetch via gspread
         ↓
   Normalize columns
         ↓
   Validate dates & phones
         ↓
   Generate UserID (91 + 10-digit phone)
         ↓
   Incremental filter (created_date > last ingestion)
         ↓
   Deduplicate by UserID
         ↓
   Upsert to Supabase (tofu_leads table)
```

## Prerequisites

### 1. Google Service Account Setup

✅ **Already completed!** Your service account JSON should be at:
```
credentials/google_service_account.json
```

Make sure all three Google Sheets are shared with your service account email (found in the JSON file under `client_email`).

### 2. Supabase Database

✅ **Already completed!** Your database table `tofu_leads` has been created with:
- All required columns (name, email, phone_number, city, question_1, utm_source, utm_medium, utm_camp, created_date, ad_name)
- `user_id` column with UNIQUE constraint
- `source_sheet` column to track data origin
- Proper indexes for performance

### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## Configuration

All configuration is in `.env` and `config.py`.

### Google Sheets Sources

Three sheets are configured:

1. **Sheet1** - `1iDNfIXXjBFGIhBCkKbKcYZmR9ykbZ2mPQS_X121_od8`
2. **ACCA** - `14zQQHYrcPHXkXLPGCmZ9J4Ito_Hc9ye8By5JaQL9bQM`
3. **Bootcamp_30_March** - `1MiLdV6cYc2LaBqG_0WzYqjNBxcVkDIK_erz-OdZeQZ8`

### Expected Columns in Google Sheets

Each sheet should have these columns:
- Name
- Email
- Phone number
- City
- Question 1
- utmSource
- utmMedium
- utmCamp
- created date
- ad name

## Usage

### Basic Commands

```bash
# Test with dry-run (no database writes)
python cli.py tofu-ingestion --dry-run

# Run for real
python cli.py tofu-ingestion

# Run with verbose logging
python cli.py tofu-ingestion --verbose

# Process only one sheet
python cli.py tofu-ingestion --sheet Sheet1
```

### Direct Execution

You can also run the microservice directly:

```bash
cd microservices/tofu_ingestion
python main.py --dry-run
python main.py --verbose
python main.py --sheet ACCA
```

## How It Works

### 1. Incremental Loading

The microservice tracks the latest `created_date` for each source sheet. On subsequent runs, it only processes records newer than the last ingestion.

### 2. Phone Number Validation

- Extracts 10-digit phone numbers (handles various formats)
- Generates `UserID` as `91` + 10-digit number (e.g., `919876543210`)
- Skips records with invalid phone numbers

### 3. Date Parsing

- Handles multiple date formats (DD/MM/YYYY, DD-MM-YYYY, etc.)
- Converts all dates to UTC
- Skips records with invalid dates

### 4. Deduplication

- Uses `user_id` (phone-based) as unique identifier
- If multiple records exist for same phone, keeps the most recent
- Database upsert handles updates for existing records

### 5. Error Handling

- Each sheet is processed independently
- One sheet's failure doesn't stop others
- Detailed logging for troubleshooting

## Output

### Success Example

```
============================================================
Starting TOFU Leads Ingestion
============================================================
Processing 3 sheet(s)
Processing sheet: Sheet1 (tab: Sheet1)
Fetched 150 rows from Sheet1
Incremental filter: keeping 25 new records (filtered out 125 existing)
After deduplication: 24 unique records
✓ Completed Sheet1: 25 new, 24 upserted, 0 failed
============================================================
INGESTION SUMMARY
============================================================
✓ Sheet1              | Fetched:  150 | New:   25 | Upserted:   24 | Failed:  0
✓ ACCA                | Fetched:   80 | New:   12 | Upserted:   12 | Failed:  0
✓ Bootcamp_30_March   | Fetched:   45 | New:    8 | Upserted:    8 | Failed:  0
------------------------------------------------------------
TOTAL                 | Fetched:  275 | New:   45 | Upserted:   44 | Failed:  0
============================================================
```

## Troubleshooting

### Google Sheets Authentication Error

**Error:** `Failed to initialize Google Sheets client`

**Solution:**
1. Check that `credentials/google_service_account.json` exists
2. Verify the JSON file is valid
3. Ensure sheets are shared with the service account email

### Worksheet Not Found

**Error:** `Worksheet 'Sheet1' not found in spreadsheet`

**Solution:**
1. Verify the tab name in `.env` matches exactly (case-sensitive)
2. Check you have access to the sheet
3. For "Bootcamp | 30_March", use the exact tab name with spaces and pipe

### RLS/Permission Errors

**Error:** `new row violates row-level security policy`

**Solution:**
The migration already set up RLS policies. If you still get errors:
1. In Supabase dashboard, go to Authentication > Policies
2. Ensure the policy "Enable all operations for service role" exists
3. Or temporarily disable RLS on the `tofu_leads` table

### Invalid Phone Numbers

**Warning:** `Dropping X rows with invalid phone numbers`

**What it means:** Some records don't have valid 10-digit Indian phone numbers.

**Action:** Review the Google Sheets data. The script will skip these records.

### Invalid Dates

**Warning:** `Dropping X rows with invalid dates`

**What it means:** The `created date` column has invalid date formats.

**Action:** Ensure dates are in DD/MM/YYYY or DD-MM-YYYY format.

## Logs

Logs are saved to: `logs/tofu_ingestion.log`

View recent logs:
```bash
tail -f logs/tofu_ingestion.log
```

## Daily Scheduling

### Option 1: Cron (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6 AM
0 6 * * * cd /Users/classplus/My\ Projects/Plutus-data-warehouse && /Users/classplus/My\ Projects/Plutus-data-warehouse/venv/bin/python cli.py tofu-ingestion >> logs/cron.log 2>&1
```

### Option 2: GitHub Actions

Create `.github/workflows/tofu-ingestion.yml`:
```yaml
name: TOFU Ingestion
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python cli.py tofu-ingestion
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
```

## Database Schema

Table: `tofu_leads`

| Column | Type | Constraints |
|--------|------|-------------|
| id | bigint | PRIMARY KEY |
| user_id | text | UNIQUE, NOT NULL |
| name | text | |
| email | text | |
| phone_number | text | |
| city | text | |
| question_1 | text | |
| utm_source | text | |
| utm_medium | text | |
| utm_camp | text | |
| created_date | timestamp | |
| ad_name | text | |
| source_sheet | text | |
| ingested_at | timestamp | DEFAULT now() |
| updated_at | timestamp | DEFAULT now() |

## Next Steps

1. **Test with dry-run:** `python cli.py tofu-ingestion --dry-run --verbose`
2. **Run for real:** `python cli.py tofu-ingestion`
3. **Verify in Supabase:** Check the `tofu_leads` table has data
4. **Re-run to test incremental:** Should show "0 new records" on second run
5. **Set up daily scheduling:** Choose cron or GitHub Actions

## Support

For issues or questions, check:
1. Logs in `logs/tofu_ingestion.log`
2. Run with `--verbose` flag for detailed output
3. Use `--dry-run` to test without database writes
