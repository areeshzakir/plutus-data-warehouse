# Date Parsing Issue - ACCA Sheet (FIXED)

## Issue Discovered
**63,648 rows (54.6%)** were being dropped from ACCA sheet as "invalid dates"

## Root Cause Analysis

### Problem 1: Empty String Dates
- **126 rows** had empty string values (`''`) in the `created date` column
- These legitimately cannot be parsed

### Problem 2: Wrong Date Parser Configuration
The dates in ACCA sheet use **ISO 8601 format**: `2025-08-03T17:05:56.113Z`

**Original Code** (WRONG):
```python
df['created_date'] = pd.to_datetime(
    df['created_date'],
    dayfirst=True,  # ❌ WRONG for ISO 8601!
    errors='coerce',
    utc=True
)
```

**The Problem**:
- ISO 8601 format: `2025-08-03` = August 3, 2025 (YYYY-**MM**-DD)
- `dayfirst=True` forces: `2025-08-03` = interpreted as **day-first**
- Pandas sees "day 08, month 03" which is valid → **March 8, 2025** (WRONG!)
- BUT for dates like `2025-08-13` → "day 08, month 13" → **INVALID** (no month 13) → NaT

This caused **63,522 valid dates to be rejected** because:
- Dates with day > 12 (like `2025-08-13`) were unparseable with `dayfirst=True`
- Dates with day ≤ 12 were **misparsed** (month/day swapped)

## The Fix

**New Code** (CORRECT):
```python
# Filter out empty strings first
empty_mask = df['created_date'].astype(str).str.strip() == ''
empty_count = empty_mask.sum()
if empty_count > 0:
    logger.warning(f"Dropping {empty_count} rows with empty dates")

# Parse dates without dayfirst to properly handle ISO 8601 format
df['created_date'] = pd.to_datetime(
    df['created_date'],
    errors='coerce',
    utc=True  # No dayfirst=True
)
```

**Why This Works**:
- Pandas automatically detects ISO 8601 format when `dayfirst` is not specified
- ISO 8601 dates parse correctly: `2025-08-13T01:44:30.076Z` → August 13, 2025 ✅
- Empty strings are explicitly tracked and reported separately

## Results

### Before Fix
- **Total rows**: 116,667
- **Dropped as invalid**: 63,648 (54.6%)
- **Actually empty**: 126 (0.1%)
- **Wrongly rejected**: 63,522 (54.5%) ❌

### After Fix
- **Total rows**: 116,667
- **Dropped as empty**: 126 (0.1%)
- **Dropped as invalid**: 0 (0%)
- **Successfully parsed**: 116,541 (99.9%) ✅

## Impact on Other Sheets

### Sheet1 (168K rows)
- Uses ISO 8601 format: `2025-11-12T18:30:00.000Z`
- ✅ Also benefited from fix (no dates being misparsed)

### Bootcamp_30_March (33K rows)
- Uses ISO 8601 format: `2025-01-10T12:00:00.000Z`
- ✅ Also benefited from fix

## Date Format Support

The updated parser now correctly handles:
1. ✅ **ISO 8601**: `2025-08-13T17:05:56.113Z`
2. ✅ **ISO 8601 (no timezone)**: `2025-08-13T17:05:56`
3. ✅ **Standard date**: `2025-08-13`
4. ✅ **US format**: `08/13/2025` (month/day/year)
5. ⚠️ **European format**: `13/08/2025` (day/month/year) - Use with caution

**Note**: If your Google Sheets ever use DD/MM/YYYY format (European), you'll need to add format detection logic.

## Verification

Run diagnostic to check date parsing:
```bash
./venv/bin/python diagnose_dates.py
```

Expected output for ACCA:
```
Valid dates parsed: 116541
Invalid dates (NaT): 126
Invalid percentage: 0.1%
```

## Lessons Learned

1. **Always verify date formats** before choosing parser settings
2. **`dayfirst=True` should only be used for DD/MM/YYYY formats** (e.g., European dates)
3. **ISO 8601 dates should NEVER use `dayfirst=True`** - they're always YYYY-MM-DD
4. **Empty strings should be filtered separately** from unparseable dates for better diagnostics

## Related Files
- `microservices/tofu_ingestion/main.py` (lines 176-207)
- `diagnose_dates.py` (diagnostic tool)
- `docs/DEDUPLICATION_LOGIC.md` (updated with correct drop reasons)
