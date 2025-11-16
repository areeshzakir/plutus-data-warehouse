# MOFU Lead Assignments Ingestion Microservice

## Purpose
Fetches middle-of-funnel lead assignment data from the MOFU API (CSV) and saves it to Supabase without dropping rows. It only keeps records newer than the last ingested `assign_on` per source, while still reprocessing the most recent day to avoid gaps.

## Configuration
Add the following to your `.env`:

```
MOFU_API_URL=<api-endpoint-that-returns-csv>
MOFU_SUPABASE_TABLE=mofu_lead_assignments
MOFU_LOG_FILE=logs/mofu_ingestion.log
```

## How It Works
1. `services.mofu_api.MOFUAPIClient` downloads the CSV (no auth needed).
2. Columns are mapped to snake_case; missing columns are logged and filled as NULLs.
3. Unexpected columns are logged and still captured inside a `payload` JSON column so nothing is lost.
4. `assign_on` is parsed as IST and stored in UTC. Rows with invalid timestamps are dropped with a warning.
5. Incremental loading keeps only rows where `assign_on` is newer than the last ingested value for that `sources` group (with a 1-day rollback safety net from the shared Supabase client).
6. Inserts use the shared `SupabaseClient` with a unique constraint on `(sources, assign_on, lead_mobile)` to prevent duplicates on reruns.

## Commands
```bash
# Dry run (no database writes)
python cli.py mofu-ingestion --dry-run --verbose

# Real ingestion
python cli.py mofu-ingestion
```

Logs stream to console and `logs/mofu_ingestion.log`.

## Schema Drift Handling
- Missing expected columns → warning + NULL fill
- New/extra columns → warning + captured in `payload`
- Column order changes → ignored; columns matched by name

## Table Schema
Created by `supabase/migrations/20251116_create_mofu_lead_assignments_table.sql` with a unique constraint on `(sources, assign_on, lead_mobile)`.
