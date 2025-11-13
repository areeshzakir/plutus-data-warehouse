# Exact Duplicate Detection

## Overview
The TOFU Leads Ingestion system prevents exact duplicate records using a database-level unique constraint on ALL fields that define a unique lead.

## What is a Duplicate?

A record is considered a **duplicate** if and only if **ALL** of the following fields are identical:

1. `name` (Full name)
2. `email`
3. `phone_number`
4. `city`
5. `question_1`
6. `utm_source`
7. `utm_medium`
8. `utm_camp`
9. `created_date`
10. `ad_name`
11. `source_sheet`

## Examples

### ✅ Allowed (NOT duplicates)

#### Same user, different date:
```
Roniya Khatun | roniyak476@gmail.com | 917585887329 | ... | 2025-11-04T16:12:53.844Z | ...
Roniya Khatun | roniyak476@gmail.com | 917585887329 | ... | 2025-11-05T16:12:53.844Z | ...
```
**Reason:** Different `created_date` → Different records ✓

#### Same user, different campaign:
```
Roniya Khatun | roniyak476@gmail.com | 917585887329 | ... | Plutus_ACCA_CCC | ...
Roniya Khatun | roniyak476@gmail.com | 917585887329 | ... | Plutus_CCC_Website | ...
```
**Reason:** Different `utm_camp` → Different records ✓

#### Same user, different source sheet:
```
... | source_sheet: Sheet1
... | source_sheet: ACCA
```
**Reason:** Different `source_sheet` → Different records ✓

### ❌ Blocked (Duplicates)

#### Exact same record:
```
Roniya Khatun | roniyak476@gmail.com | 917585887329 | 11th/12th | fb | cpc | Plutus_ACCA_CCC_Website | 2025-11-04T16:12:53.844Z | Video-CCC | Sheet1
Roniya Khatun | roniyak476@gmail.com | 917585887329 | 11th/12th | fb | cpc | Plutus_ACCA_CCC_Website | 2025-11-04T16:12:53.844Z | Video-CCC | Sheet1
```
**Reason:** ALL fields identical → Duplicate ✗

## Technical Implementation

### Database Constraint
A unique index on all fields prevents duplicates at the database level:

```sql
CREATE UNIQUE INDEX idx_tofu_leads_all_fields_unique 
ON public.tofu_leads(
    COALESCE(name, ''),
    COALESCE(email, ''),
    COALESCE(phone_number, ''),
    COALESCE(city, ''),
    COALESCE(question_1, ''),
    COALESCE(utm_source, ''),
    COALESCE(utm_medium, ''),
    COALESCE(utm_camp, ''),
    created_date,
    COALESCE(ad_name, ''),
    COALESCE(source_sheet, '')
);
```

**Note:** `COALESCE(field, '')` treats NULL values as empty strings, so two NULL values are considered equal.

### Application Logic
The Python code uses `upsert` with `ignore_duplicates=True`:

```python
response = (
    self.client.table(SUPABASE_TABLE)
    .upsert(batch, on_conflict='*', ignore_duplicates=True)
    .execute()
)
```

When a duplicate is detected:
- The database silently skips it (no error thrown)
- The record is **not** inserted
- It's counted as "skipped" in the logs

## Running the Script Multiple Times

**Safe to run repeatedly!** ✅

If you run the ingestion script multiple times:
1. First run: All new records inserted
2. Second run: 
   - Records with `created_date > last_run` are fetched
   - Exact duplicates are automatically skipped
   - Only truly new records are inserted

**No risk of duplicate data**, even if:
- The script crashes mid-run
- Google Sheets contain duplicate rows
- You manually re-run the script
- Multiple processes run simultaneously

## Logging Output

```
✓ Sheet1               | Fetched: 169574 | New: 169538 | Inserted: 146860 | Skipped: 22678
```

**Interpretation:**
- **Fetched:** Total rows from Google Sheet
- **New:** After filtering by date and removing invalid data
- **Inserted:** Successfully inserted into database
- **Skipped:** Exact duplicates (already in database)

## Migration Applied

File: `supabase/migrations/20250113_remove_unique_constraint.sql`

To apply manually, run `apply_migration_manually.sql` in Supabase dashboard.
