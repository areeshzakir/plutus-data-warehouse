#!/usr/bin/env python3
"""
Analyze the gap between fetched rows and inserted rows
"""

# Expected from Google Sheets
sheets_data = {
    'Sheet1': {
        'fetched': 168864,
        'inserted_db': 139873,
    },
    'ACCA': {
        'fetched': 116673,
        'inserted_db': 46729,
    },
    'Bootcamp_30_March': {
        'fetched': 219674,  # User's number
        'inserted_db': 32974,
    }
}

print("=" * 70)
print("INGESTION GAP ANALYSIS")
print("=" * 70)

total_fetched = 0
total_inserted = 0

for sheet_name, data in sheets_data.items():
    fetched = data['fetched']
    inserted = data['inserted_db']
    gap = fetched - inserted
    gap_pct = (gap / fetched * 100) if fetched > 0 else 0
    
    print(f"\n{sheet_name}:")
    print(f"  Fetched from Google Sheets: {fetched:7,}")
    print(f"  Inserted into Database:     {inserted:7,}")
    print(f"  Gap:                        {gap:7,} ({gap_pct:.1f}%)")
    
    total_fetched += fetched
    total_inserted += inserted

print("\n" + "-" * 70)
print(f"TOTAL:")
print(f"  Fetched from Google Sheets: {total_fetched:7,}")
print(f"  Inserted into Database:     {total_inserted:7,}")
print(f"  Gap:                        {total_fetched - total_inserted:7,} ({(total_fetched - total_inserted) / total_fetched * 100:.1f}%)")
print("=" * 70)

print("\n📋 POSSIBLE REASONS FOR THE GAP:\n")
print("1. Invalid phone numbers (can't normalize to 10 digits)")
print("2. Empty dates (created_date is empty string)")
print("3. Duplicate UserIDs (OLD LOGIC - kept only 1 per UserID)")
print("4. Exact duplicate rows (NEW LOGIC - all fields identical)")
print("5. Database constraint violations on initial insert")
print("\n⚠️  The main issue is likely #3 - the FIRST ingestion used")
print("   the OLD deduplication logic that kept only 1 record per UserID")
print("   (we've since updated the logic but haven't re-ingested)")

# Calculate expected drops based on original ingestion
print("\n" + "=" * 70)
print("BREAKDOWN FROM ORIGINAL INGESTION LOG:")
print("=" * 70)

original_ingestion = {
    'Sheet1': {
        'fetched': 168835,
        'new_records': 168833,  # After date/phone validation
        'upserted': 145400,     # After deduplication by user_id
    },
    'ACCA': {
        'fetched': 116645,
        'new_records': 52997,   # After invalid dates (63,648 dropped!)
        'upserted': 47292,      # After deduplication by user_id
    },
    'Bootcamp_30_March': {
        'fetched': 33814,
        'new_records': 33756,   # After phone validation (58 invalid)
        'upserted': 32974,      # After deduplication by user_id
    }
}

print("\nSheet1:")
print(f"  Fetched:        168,835")
print(f"  Invalid phone:        2 (dropped)")
print(f"  Valid:          168,833")
print(f"  Dedup (UserID): 23,433 (dropped - OLD LOGIC)")
print(f"  Inserted:       145,400")

print("\nACCA:")
print(f"  Fetched:        116,645")
print(f"  Empty dates:        126 (dropped)")
print(f"  Invalid dates:  63,648 (dropped - BUG, now fixed!)")
print(f"  Valid:           52,871")
print(f"  Dedup (UserID):   5,579 (dropped - OLD LOGIC)")
print(f"  Inserted:        47,292")

print("\nBootcamp_30_March:")
print(f"  Fetched:         33,814")
print(f"  Invalid phone:       58 (dropped)")
print(f"  Valid:           33,756")
print(f"  Dedup (UserID):     782 (dropped - OLD LOGIC)")
print(f"  Inserted:        32,974")

print("\n" + "=" * 70)
print("TOTAL ORIGINAL INGESTION:")
print(f"  Fetched:         319,294")
print(f"  Invalid data:     63,834 (dates + phones)")
print(f"  Dedup (UserID):   29,794 (OLD LOGIC)")
print(f"  Inserted:        225,666")
print("=" * 70)

print("\n💡 TO GET FULL DATA:")
print("   1. Clear the database table")
print("   2. Re-run ingestion with NEW logic (already updated)")
print("   3. Should insert ~485,000+ records (less exact duplicates)")
print("\n   Command: ./venv/bin/python cli.py tofu-ingestion")
