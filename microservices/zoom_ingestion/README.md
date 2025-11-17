# Zoom Webinar Attendance Ingestion Microservice

## Purpose
Pulls Zoom webinar attendance data from Google Sheets, cleans and deduplicates it by `(Webinar Date, Phone)` (fallback to email if phone is missing), aggregates session time, and stores the result in Supabase.

## Configuration
Add to `.env` (defaults are set for the shared sheet/tab):

```
ZOOM_SHEET_ID=1_5weku38mXGFrGZgHa0yGo8VDxn6XMXkXbThLpp8FhY
ZOOM_SHEET_TAB=Zoom Data - July/Jun
ZOOM_SUPABASE_TABLE=zoom_webinar_attendance
ZOOM_LOG_FILE=logs/zoom_ingestion.log
```

Supabase credentials come from the existing `SUPABASE_URL` and `SUPABASE_KEY`.

## How It Works
1. Fetches the sheet via the shared GoogleSheetsClient.
2. Normalizes text (trim, proper-case names, lowercase email), cleans phone to 10 digits, builds `user_id` as `91` + phone.
3. Parses times as IST and stores them in UTC; coerces `Time in Session (minutes)` to integers.
4. Drops rows with neither phone nor email, or missing webinar date.
5. Deduplicates by `(Webinar Date, Phone)`; if phone is absent, deduplicates by `(Webinar Date, Email)`. Within each group, it:
   - Sums minutes in session
   - Uses earliest Join Time, latest Leave Time
   - Sets Attended = Yes if any row is Yes
   - Picks first non-blank values for names/email/approval/status/source/category
6. Keeps the original row as `payload` for troubleshooting and schema drift.
7. Incremental loads use `Webinar Date` as the cutoff (with a 1-day rollback safety net from the shared Supabase client); DB uniqueness guards duplicates.

## Commands
```bash
# Dry run (no database writes)
python cli.py zoom-ingestion --dry-run --verbose

# Real ingestion
python cli.py zoom-ingestion
```

## Table Schema
Created by `supabase/migrations/20251117_create_zoom_webinar_attendance_table.sql` with a uniqueness on `(source_sheet, webinar_date, COALESCE(phone,''), COALESCE(email,''))`.
