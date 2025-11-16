# BOFU Transactions Ingestion Microservice

## Purpose
Fetches ready-to-store transaction data (bottom of the funnel) from the Testbook CSV API and saves it in Supabase without filtering or dropping any rows.

## Configuration
Add the following variables to your `.env` file:

```
BOFU_API_URL=https://data.testbook.com/api/queries/18351/results.csv
BOFU_API_KEY=Wg8bUe8ijZ1g3OijQGtPVDFRXYaGcYFChODQ65kg
BOFU_SUPABASE_TABLE=bofu_transactions
BOFU_LOG_FILE=logs/bofu_ingestion.log
```

> Keep the actual API key in `.env`; never commit it.

## How It Works
1. `services.transaction_api.TransactionAPIClient` downloads the CSV.
2. Every column returned by the API is kept. Known columns are mapped to snake_case table columns; unexpected columns are stored inside a `payload` JSON column so nothing is lost.
3. The pipeline does **not** drop or deduplicate rows. Instead, the Supabase table has a unique constraint on `txn_id`, so reruns safely skip already stored transactions.
4. Results are inserted through the shared `SupabaseClient` using the `bofu_transactions` table.

## Commands
```bash
# Dry run (no database writes)
python cli.py bofu-ingestion --dry-run --verbose

# Real ingestion
python cli.py bofu-ingestion
```

Logs stream to console and `logs/bofu_ingestion.log` for auditing.

## Schema Drift Handling
- Missing columns from the API are logged and stored as NULL for that run.
- New columns trigger a warning and are still captured inside the `payload` JSON column until the table/schema is updated.
- Column order changes have no impact because columns are matched by name.

## Scheduling
Use the same cron/GitHub Actions pattern as the TOFU service; just swap the CLI command to `bofu-ingestion`.
