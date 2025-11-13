# Next Steps - Exact Duplicate Detection Implementation

## ✅ Completed

1. **Updated database client** (`services/supabase_db.py`)
   - Changed from `insert()` to `upsert()` with `ignore_duplicates=True`
   - Returns `{attempted, succeeded, skipped}` instead of `{attempted, succeeded, failed}`
   - Gracefully handles exact duplicates without errors

2. **Updated orchestrator** (`microservices/tofu_ingestion/main.py`)
   - Tracks "skipped" instead of "failed" records
   - Updated logging to show "Inserted" and "Skipped" counts
   - Removed misleading "Failed" count

3. **Created migration file** (`supabase/migrations/20250113_remove_unique_constraint.sql`)
   - Drops old constraints (`tofu_leads_unique_record`, `tofu_leads_user_id_key`)
   - Creates new unique index on ALL 11 fields
   - Uses `COALESCE` to handle NULL values consistently

4. **Created documentation**
   - `docs/EXACT_DUPLICATE_DETECTION.md` - Full explanation of duplicate logic
   - `apply_migration_manually.sql` - Ready-to-run SQL for Supabase dashboard

## ⏳ Action Required

### Step 1: Apply Database Migration

**Option A: Via Supabase Dashboard (Recommended)**

1. Go to: https://supabase.com/dashboard/project/rwrfabtpzyzjbfwyogcm/editor
2. Copy and paste the contents of `apply_migration_manually.sql`
3. Click "Run"
4. Verify the index was created (last SELECT statement in the file)

**Expected output:**
```
indexname: idx_tofu_leads_all_fields_unique
indexdef: CREATE UNIQUE INDEX idx_tofu_leads_all_fields_unique ON public.tofu_leads...
```

### Step 2: Clear Existing Data (Optional)

If you want to start fresh with all records:

```bash
# Run this SQL in Supabase dashboard
DELETE FROM public.tofu_leads;
```

If you want to keep existing data, skip this step. The new constraint will be applied to all future inserts.

### Step 3: Run Full Ingestion

```bash
cd "/Users/classplus/My Projects/Plutus-data-warehouse"
./venv/bin/python cli.py tofu-ingestion
```

**Expected results:**
- Sheet1: ~146,860 inserted, ~22,678 skipped (exact duplicates)
- ACCA: ~116,574 inserted, ~132 skipped
- Bootcamp: ~14,703 inserted

**Total:** ~278,137 unique records inserted

### Step 4: Test Re-running (Verify Duplicate Protection)

Run the script again immediately:

```bash
./venv/bin/python cli.py tofu-ingestion
```

**Expected results:**
- Fetched: 0 new records (incremental date filter)
- OR if date filter passes: All records skipped as duplicates

This proves the system is safe to run multiple times!

## 🔍 How to Verify

### Check database count:
```bash
./venv/bin/python << EOF
from services.supabase_db import SupabaseClient
db = SupabaseClient()
result = db.client.table('tofu_leads').select('id', count='exact').execute()
print(f"Total records: {result.count:,}")
EOF
```

### Check logs:
```bash
tail -50 logs/tofu_ingestion.log
```

Look for:
- "Inserted: X" (new records added)
- "Skipped: Y" (duplicates automatically handled)
- NO "Failed: Z" entries (unless there's a real error)

## 📝 Key Changes Summary

| Before | After |
|--------|-------|
| Composite constraint on 6 fields | Unique index on ALL 11 fields |
| Failed to insert 22k records | Gracefully skips exact duplicates |
| Misleading "Failed" count | Clear "Skipped" count |
| Risk of duplicates on re-run | Safe to run multiple times |

## 🎯 Definition of Duplicate

A record is a duplicate if ALL these fields match:
1. name
2. email  
3. phone_number
4. city
5. question_1
6. utm_source
7. utm_medium
8. utm_camp
9. **created_date**
10. ad_name
11. source_sheet

**Different date = Different record ✅**
**Different campaign = Different record ✅**
**Exact same everything = Duplicate ❌**

## 🆘 Troubleshooting

### If you see "duplicate key violates unique constraint":
- The old constraint still exists
- Re-run the migration SQL to drop it
- Check: `SELECT conname FROM pg_constraint WHERE conrelid = 'public.tofu_leads'::regclass AND contype = 'u';`

### If all records are being skipped:
- Check the `created_date` filter is working
- Look at `last_ingestion_timestamp` in logs
- Try: `--sheet Sheet1` to process one sheet at a time

### If you see errors about on_conflict:
- Supabase client might need updating
- Alternative: use try/except to catch unique constraint errors

## 📊 Expected Final Stats

After full ingestion:
- Total Google Sheet rows: ~319,431
- Invalid data removed: ~187 (phone/date issues)
- Exact duplicates: ~41,107
- **Final database records: ~278,137** ✅
