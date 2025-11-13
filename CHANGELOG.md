# Changelog - TOFU Leads Ingestion

## [2025-01-12] - Deduplication Logic Update

### Changed
- **Deduplication behavior**: Now allows multiple records per `user_id`
- **Database schema**: Replaced single-column UNIQUE constraint with composite constraint
- **Drop logic**: Changed from "keep first per UserID" to "keep all unique combinations"

### Why This Change?
To track user journey across multiple marketing touchpoints:
- Same user from different campaigns = separate records ✅
- Same user at different times = separate records ✅
- Exact duplicate (all fields identical) = blocked ❌

### Before vs After

#### Before (Old Logic)
```
Constraint: UNIQUE(user_id)
Deduplication: Drop all duplicates by user_id, keep most recent

Example:
- UserID 919876543210, Campaign A, 2025-01-10 → INSERTED
- UserID 919876543210, Campaign B, 2025-01-15 → DROPPED ❌
Result: Only 1 record per user
```

#### After (New Logic)
```
Constraint: UNIQUE(user_id, created_date, utm_source, utm_medium, utm_camp, source_sheet)
Deduplication: Drop only exact duplicates (all fields identical)

Example:
- UserID 919876543210, Campaign A, 2025-01-10 → INSERTED
- UserID 919876543210, Campaign B, 2025-01-15 → INSERTED ✅
Result: Multiple records per user tracking their journey
```

### Files Changed
1. `microservices/tofu_ingestion/main.py` (lines 119-128)
   - Removed: `drop_duplicates(subset=['user_id'])`
   - Added: `drop_duplicates()` (all columns)

2. `services/supabase_db.py` (lines 64-149)
   - Updated upsert to use `ignore_duplicates=True`
   - Added tracking for duplicate count

3. `supabase/migrations/20250112_allow_duplicate_userids.sql`
   - Dropped: UNIQUE constraint on `user_id`
   - Added: Composite UNIQUE constraint

4. `docs/DEDUPLICATION_LOGIC.md` (new)
   - Comprehensive documentation of deduplication rules

### Drop Reasons Explained

**Previous run (168,835 fetched → 145,400 inserted):**
1. ❌ Invalid dates: 0 rows (Sheet1 has clean dates)
2. ❌ Invalid phones: 2 rows
3. ❌ **Duplicate user_ids: 23,433 rows** ← This was the old logic
   - Same user appeared multiple times with different campaigns
   - Old logic kept only the most recent record per user

**Now with new logic:**
1. ❌ Invalid dates: Same as before
2. ❌ Invalid phones: Same as before  
3. ✅ **Duplicate user_ids: ALLOWED** (unless exact duplicate)
4. ❌ Exact duplicates: Only blocks if ALL fields match

### Migration Status
- ✅ Database schema updated
- ✅ Code updated
- ⚠️ **Existing data remains as-is** (225,666 records with old deduplication)
- 💡 To re-ingest with new logic: Clear table and run fresh ingestion

### Impact
- **More records will be inserted** (tracking user journey)
- **Better marketing attribution** (see which campaigns users engaged with)
- **No data loss** for re-engagements

### Next Steps
1. ✅ Schema migration applied
2. ✅ Code updated
3. ⏳ Test with new data (incremental runs will use new logic)
4. Optional: Clear existing data and re-run for historical correction

### Testing
```bash
# Dry run to test (no DB writes)
./venv/bin/python cli.py tofu-ingestion --dry-run

# Run actual ingestion with new logic
./venv/bin/python cli.py tofu-ingestion

# Check for users with multiple records
psql -c "SELECT user_id, COUNT(*) FROM tofu_leads GROUP BY user_id HAVING COUNT(*) > 1 LIMIT 10;"
```

---

## [2025-01-12] - Initial Release

### Added
- TOFU Leads Ingestion microservice
- Google Sheets integration (3 sheets)
- Supabase database storage
- Incremental loading by `created_date`
- Phone number normalization to UserID
- CLI interface with dry-run mode
- Comprehensive logging
