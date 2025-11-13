# TOFU Leads Deduplication Logic

## Overview
The TOFU leads ingestion pipeline now supports **multiple records per user** while preventing exact duplicate entries.

---

## Why Records Are Dropped

When comparing "Fetched" vs "Inserted" counts, records are dropped for these reasons:

### 1. **Empty Dates**
- **What**: Rows where `created_date` is an empty string or null
- **Example**: 126 rows dropped from ACCA sheet (0.1% of fetched)
- **Fix**: Ensure all rows have a valid `created date` value in Google Sheets
- **Note**: Previously, 63,648 rows were incorrectly dropped due to date parser misconfiguration (now fixed)

### 2. **Invalid Phone Numbers**
- **What**: Phone numbers that can't be normalized to 10 digits
- **Example**: 2 rows from Sheet1, 58 from Bootcamp_30_March
- **Fix**: Ensure phone numbers have at least 10 digits

### 3. **Exact Duplicates** (New behavior)
- **What**: Rows where ALL fields are identical (same user_id, date, campaign, source)
- **Behavior**: First occurrence kept, duplicates removed
- **Note**: Same user_id with different campaigns/dates = **kept as separate records**

### 4. **Incremental Loading** (On subsequent runs)
- **What**: Records with `created_date <= last_ingestion_timestamp`
- **Behavior**: Filtered out to avoid re-processing old data
- **Note**: This is expected behavior, not an error

---

## New Deduplication Rules

### ✅ **ALLOWED: Same User, Different Context**
A user (UserID) can appear multiple times if they came from:
- Different campaigns (utm_source, utm_medium, utm_camp)
- Different dates (created_date)
- Different sheets (source_sheet)

**Example:**
```
UserID: 919876543210
Record 1: Campaign A, 2025-01-10, Sheet1  ✅ INSERTED
Record 2: Campaign B, 2025-01-15, Sheet1  ✅ INSERTED (same user, different campaign/date)
Record 3: Campaign A, 2025-01-10, ACCA    ✅ INSERTED (same user, different source)
```

### ❌ **BLOCKED: Exact Duplicates**
Only blocks when **ALL** these fields are identical:
- user_id
- created_date
- utm_source
- utm_medium
- utm_camp
- source_sheet

**Example:**
```
UserID: 919876543210
Record 1: Campaign A, 2025-01-10, Sheet1  ✅ INSERTED
Record 2: Campaign A, 2025-01-10, Sheet1  ❌ BLOCKED (exact duplicate)
```

---

## Database Schema

### Unique Constraint
```sql
UNIQUE (user_id, created_date, utm_source, utm_medium, utm_camp, source_sheet)
```

This composite constraint ensures:
1. Same user can have multiple records
2. Each unique (user + campaign + date + source) combination appears only once

---

## Implementation Details

### Code Changes
1. **Deduplication** (`microservices/tofu_ingestion/main.py:119-128`)
   - Old: `df.drop_duplicates(subset=['user_id'])`
   - New: `df.drop_duplicates()` (all columns)

2. **Upsert Logic** (`services/supabase_db.py:64-149`)
   - Changed to use `ignore_duplicates=True`
   - Tracks: succeeded, failed, duplicates

3. **Database Migration** (`supabase/migrations/20250112_allow_duplicate_userids.sql`)
   - Removed: UNIQUE constraint on `user_id` alone
   - Added: Composite UNIQUE constraint

---

## Example Scenarios

### Scenario 1: User Re-engages with Different Campaign
```
Input:
Row 1: UserID=919876543210, Date=2025-01-10, Campaign=Google_Ad_A
Row 2: UserID=919876543210, Date=2025-01-15, Campaign=Facebook_Ad_B

Result: Both inserted ✅
Reason: Different campaign and date
```

### Scenario 2: Duplicate Form Submission
```
Input:
Row 1: UserID=919876543210, Date=2025-01-10, Campaign=Google_Ad_A
Row 2: UserID=919876543210, Date=2025-01-10, Campaign=Google_Ad_A

Result: Only Row 1 inserted, Row 2 skipped ❌
Reason: Exact duplicate
```

### Scenario 3: Same User Across Multiple Sheets
```
Input:
Sheet1, Row 1: UserID=919876543210, Date=2025-01-10, Campaign=Google_Ad_A
ACCA, Row 1:   UserID=919876543210, Date=2025-01-10, Campaign=Google_Ad_A

Result: Both inserted ✅
Reason: Different source_sheet (Sheet1 vs ACCA)
```

---

## Monitoring

### Check Dropped Records
```bash
# View invalid dates count
grep "Dropping.*invalid dates" logs/tofu_ingestion.log

# View invalid phones count
grep "Dropping.*invalid phone" logs/tofu_ingestion.log

# View exact duplicates count
grep "exact duplicates removed" logs/tofu_ingestion.log
```

### Query Database for User with Multiple Records
```sql
SELECT user_id, COUNT(*) as record_count, 
       array_agg(DISTINCT utm_source) as campaigns,
       array_agg(DISTINCT source_sheet) as sources
FROM tofu_leads
GROUP BY user_id
HAVING COUNT(*) > 1
ORDER BY record_count DESC
LIMIT 10;
```

---

## FAQs

**Q: Why do I see "168,833 fetched, 145,400 inserted" on first run?**
A: 23,433 rows had duplicate UserIDs with identical campaign/date/source. Only the first occurrence was kept.

**Q: Will this track user journey across campaigns?**
A: Yes! Same user appearing in different campaigns/dates will create separate records.

**Q: What if I want to truly deduplicate by UserID?**
A: Query the database:
```sql
SELECT DISTINCT ON (user_id) *
FROM tofu_leads
ORDER BY user_id, created_date DESC;
```

**Q: How do I clean invalid dates in Google Sheets?**
A: Ensure `created date` column uses format: `YYYY-MM-DD HH:MM:SS` or `DD/MM/YYYY HH:MM:SS`
