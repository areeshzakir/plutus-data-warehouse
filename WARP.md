# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Plutus Data Warehouse is a **modular data pipeline** that centralizes marketing and sales funnel data from multiple sources (Google Sheets, Zoom CSVs, CRM) into Supabase. The architecture follows a **microservices pattern** where each data source has an independent ingestion microservice.

**Status:** Microservice #1 (TOFU Leads Ingestion) is complete and operational.

## Common Commands

### Environment Setup
```bash
# Activate virtual environment (ALWAYS do this first)
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt
```

### Running Microservices
```bash
# TOFU ingestion - dry run (no database writes)
python cli.py tofu-ingestion --dry-run

# TOFU ingestion - production run
python cli.py tofu-ingestion

# Debug mode with verbose logging
python cli.py tofu-ingestion --dry-run --verbose

# Process only one specific sheet
python cli.py tofu-ingestion --sheet Sheet1
```

### Testing Individual Microservices
```bash
# Run microservice directly (without CLI wrapper)
cd microservices/tofu_ingestion
python main.py --dry-run --verbose
```

### Logs and Debugging
```bash
# View real-time logs
tail -f logs/tofu_ingestion.log

# Check last 50 lines
tail -50 logs/tofu_ingestion.log

# Search for errors
grep -i error logs/tofu_ingestion.log
```

### Database Operations
```python
# Quick database check (run in Python)
from services.supabase_db import SupabaseClient
db = SupabaseClient()
result = db.client.table('tofu_leads').select('id', count='exact').execute()
print(f"Total records: {result.count:,}")
```

## Architecture

### Core Design Principles

1. **Microservices Architecture**: Each data source = independent microservice
2. **Shared Services Layer**: Common clients (Google Sheets, Supabase) used by all microservices
3. **Centralized Configuration**: All config in `config.py` and `.env`
4. **CLI-Based Execution**: Single entry point (`cli.py`) for running any microservice

### Directory Structure Logic

```
microservices/         # Independent data ingestion services
├── tofu_ingestion/    # Each microservice has main.py with main() function
│   ├── main.py        # Orchestrator class + main() entry point
│   └── README.md      # Microservice-specific documentation

services/              # Shared clients (reusable across microservices)
├── google_sheets.py   # GoogleSheetsClient - fetches data from Google Sheets
└── supabase_db.py     # SupabaseClient - handles database operations

utils/                 # Shared utilities
├── phone_utils.py     # Phone normalization & UserID generation
└── logging_utils.py   # Logging configuration

supabase/migrations/   # Database schema migrations (SQL files)
```

### Data Flow Pattern (TOFU Microservice)

Each microservice follows this orchestration pattern:

1. **Initialize clients** (Google Sheets, Supabase)
2. **Fetch last ingestion timestamp** (for incremental loading)
3. **Fetch raw data** from source
4. **Normalize columns** (map sheet columns → database columns)
5. **Validate & clean data** (dates, phone numbers)
6. **Generate computed fields** (e.g., user_id from phone)
7. **Apply incremental filter** (only new records)
8. **Remove in-memory duplicates**
9. **Upsert to database** (insert with duplicate handling)
10. **Log summary statistics**

### Key Architectural Patterns

**Orchestrator Pattern**: Each microservice has an Orchestrator class (e.g., `TOFUIngestionOrchestrator`) that:
- Manages the overall workflow
- Processes multiple data sources in sequence
- Handles errors per-source (one failure doesn't stop others)
- Returns summary statistics

**Client Abstraction**: Service clients (`GoogleSheetsClient`, `SupabaseClient`) encapsulate API interactions, making microservices focus on business logic.

**Column Mapping**: `DB_COLUMN_MAP` in `config.py` maps external column names (from Google Sheets) to database column names, allowing flexible schema evolution.

## Data Deduplication Logic (Critical)

**Understanding duplicates is critical when working with this codebase.**

### Duplicate Definition
A record is considered a **duplicate** only if ALL these fields match:
- name, email, phone_number, city, question_1
- utm_source, utm_medium, utm_camp, ad_name
- **created_date**
- source_sheet

**Important:** Same user (phone) with different campaign/date = **separate records** (NOT duplicates).

### Database Constraint
```sql
-- Unique index on ALL 11 fields (see NEXT_STEPS.md)
CREATE UNIQUE INDEX idx_tofu_leads_all_fields_unique 
ON public.tofu_leads (
  COALESCE(name, ''), 
  COALESCE(email, ''), 
  -- ... all fields
);
```

### Handling in Code
- **In-memory deduplication**: `df.drop_duplicates()` before inserting (reduces API calls)
- **Database-level**: Upsert with duplicate detection - records violating constraint are skipped
- **Result tracking**: `{attempted, succeeded, skipped}` (NOT failed)

See `docs/DEDUPLICATION_LOGIC.md` and `docs/EXACT_DUPLICATE_DETECTION.md` for details.

## Phone Number & UserID Generation

**UserID format:** `91` + 10-digit phone number (e.g., `919876543210`)

### Normalization Logic (`utils/phone_utils.py`)
```python
# Handles various formats:
"+91-98765-43210" → "919876543210"
"9876543210"      → "919876543210"
"91 9876543210"   → "919876543210"

# Takes LAST 10 digits (removes country code if present)
"919876543210"    → "919876543210"
```

Invalid phone numbers (non-10-digit after normalization) are **dropped** with warning log.

## Incremental Loading

**Critical for preventing re-processing of old data.**

### How It Works
1. Query database: `SELECT MAX(created_date) FROM tofu_leads WHERE source_sheet = 'Sheet1'`
2. Filter dataframe: `df[df['created_date'] > last_timestamp]`
3. Result: Only **new** records since last run are processed

### Expected Behavior
- **First run**: All records processed (no last_timestamp)
- **Second run**: Only records with `created_date > last run's max date`
- **Third run**: If no new data, `0 new records` (expected, not an error)

This means **the script is safe to run multiple times** without duplicating data.

## Date Parsing (Critical Fix Applied)

**Context:** An issue with date parsing caused 63k+ records to be incorrectly dropped (see `docs/DATE_PARSING_FIX.md`).

### Current Implementation
```python
# Uses ISO 8601 parsing (YYYY-MM-DD) without dayfirst=True
df['created_date'] = pd.to_datetime(
    df['created_date'],
    errors='coerce',
    utc=True  # Always convert to UTC
)
```

**Why this matters:** Google Sheets exports dates in ISO format (YYYY-MM-DD). Previous code used `dayfirst=True` which incorrectly parsed "2025-01-10" as "October 1st" instead of "January 10th", making records appear "in the future" and get filtered out.

### Validation
- Empty dates → dropped (logged)
- Unparseable dates → dropped (logged)
- Valid dates → converted to UTC timestamps

## Configuration Management

### Two-Layer Config
1. **`.env`** - Environment-specific (credentials, URLs, sheet IDs)
2. **`config.py`** - Application logic (column mappings, constants)

### Adding a New Google Sheet Source
```python
# In config.py
TOFU_SHEETS = [
    {
        "id": os.getenv("SHEET_4_ID"),      # Add to .env
        "tab": os.getenv("SHEET_4_TAB"),    # Tab name
        "name": os.getenv("SHEET_4_NAME", "DefaultName"),
    },
]
```

### Column Mapping Pattern
```python
# Maps Google Sheets columns → Supabase columns
DB_COLUMN_MAP = {
    "Phone number": "phone_number",   # Handles spaces in sheet headers
    "utmSource": "utm_source",        # Camel case → snake_case
    "Full name": "name",              # Alternative column names
}
```

## Adding a New Microservice

Follow this template (see existing `microservices/tofu_ingestion/` as reference):

1. **Create directory**: `microservices/your_service/`
2. **Implement `main.py`**:
   ```python
   class YourServiceOrchestrator:
       def __init__(self):
           # Initialize clients
       
       def run(self, dry_run=False, **kwargs):
           # Main logic
           return summaries  # List of dicts
   
   def main(dry_run=False, verbose=False, **kwargs):
       # Setup logging
       # Run orchestrator
       # Return exit code (0=success, 1=failure)
   ```
3. **Add CLI command** in `cli.py`:
   ```python
   def run_your_service(args):
       from microservices.your_service.main import main
       return main(dry_run=args.dry_run, verbose=args.verbose)
   
   # In main():
   your_parser = subparsers.add_parser("your-service", help="...")
   your_parser.add_argument("--dry-run", action="store_true")
   your_parser.set_defaults(func=run_your_service)
   ```
4. **Write README.md** documenting the microservice
5. **Add database migrations** if needed in `supabase/migrations/`

## Database Migrations

### Naming Convention
`YYYYMMDD_description.sql` (e.g., `20250112_create_tofu_leads_table.sql`)

### Applying Migrations
**Manual (via Supabase Dashboard):**
1. Go to SQL Editor in Supabase Dashboard
2. Copy SQL from migration file
3. Execute

**Note:** No automated migration runner exists yet. Migrations must be applied manually.

## Testing Strategy

### Test Hierarchy
1. **Dry-run first** (always): `--dry-run` flag skips database writes
2. **Single sheet test**: `--sheet Sheet1` to test one source
3. **Verbose mode**: `--verbose` for debug-level logs
4. **Full run**: Production execution

### Verification Checklist
- [ ] Logs show expected record counts
- [ ] No unexpected "invalid phone" warnings
- [ ] No unexpected "invalid date" warnings
- [ ] Summary table shows: Fetched, New, Inserted, Skipped
- [ ] Database record count matches expectations
- [ ] Re-running shows "0 new records" (incremental working)

## Common Issues & Solutions

### "Google Service Account file not found"
- Ensure `credentials/google_service_account.json` exists
- Check `.env` has correct path: `GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google_service_account.json`

### "Worksheet not found"
- Tab names are **case-sensitive**
- Check `.env` for correct tab name (e.g., "Bootcamp | 30_March" with exact spacing)

### "Duplicate key violates unique constraint"
- Old constraint still exists (should be replaced with new 11-field constraint)
- Run migration from `apply_migration_manually.sql`
- See `NEXT_STEPS.md` for details

### High "Skipped" count
- Expected if re-running with no new data (incremental filter working)
- Check last_ingestion_timestamp in logs
- If legitimately new data being skipped, check duplicate detection logic

### Records being incorrectly filtered out
- Check date parsing (ISO format expected)
- Verify `created_date` column in Google Sheets has valid dates
- Check phone number validation (must be 10 digits after normalization)

## Logging Conventions

### Log Levels
- **INFO**: High-level progress (sheet processing, summaries)
- **DEBUG**: Detailed operations (column normalization, API calls)
- **WARNING**: Data quality issues (invalid phones, dates)
- **ERROR**: Failures (API errors, exceptions)

### Important Log Patterns
```
"Fetched X rows from {sheet}"          - Successful data fetch
"Incremental filter: keeping X new"    - Incremental loading working
"Dropped X rows with invalid phones"   - Data quality issue
"✓ Completed {sheet}: X new, Y upserted" - Success
"Error processing {sheet}: {error}"    - Failure
```

## Future Microservices (Planned)

- **#2**: Zoom Webinar/Bootcamp Data (CSV processing)
- **#3**: CRM Sales Data Sync
- **#4**: Marketing Spend Aggregation
- **#5**: Unified Reporting Layer

When implementing these, follow the patterns established in `tofu_ingestion`:
- Orchestrator class pattern
- Independent error handling per source
- Summary statistics return
- Dry-run support
- Verbose logging option
