#!/usr/bin/env python3
"""
Diagnostic script to examine date parsing issues in ACCA sheet
"""
import pandas as pd
from services.google_sheets import GoogleSheetsClient
from config import TOFU_SHEETS

def diagnose_acca_dates():
    """Examine the ACCA sheet dates to understand why so many are invalid"""
    
    # Find ACCA sheet config
    acca_config = next((s for s in TOFU_SHEETS if s['name'] == 'ACCA'), None)
    if not acca_config:
        print("❌ ACCA sheet not found in config")
        return
    
    print("🔍 Fetching ACCA sheet data...")
    gs_client = GoogleSheetsClient()
    df = gs_client.fetch_sheet_data(
        sheet_id=acca_config['id'],
        tab_name=acca_config['tab']
    )
    
    print(f"✓ Fetched {len(df)} rows")
    print(f"\n📋 Columns: {list(df.columns)}")
    
    # Normalize column names
    df.columns = df.columns.str.strip()
    
    # Find the created_date column
    date_col = 'created date'
    if date_col not in df.columns:
        print(f"❌ '{date_col}' column not found!")
        return
    
    print(f"\n📅 Analyzing '{date_col}' column...")
    print(f"Total rows: {len(df)}")
    print(f"Non-null values: {df[date_col].notna().sum()}")
    print(f"Null values: {df[date_col].isna().sum()}")
    
    # Show sample of raw date values
    print(f"\n📊 Sample raw date values (first 20 non-null):")
    sample_dates = df[df[date_col].notna()][date_col].head(20)
    for idx, date_val in enumerate(sample_dates, 1):
        print(f"  {idx:2d}. {repr(date_val)} (type: {type(date_val).__name__})")
    
    # Show value counts for date patterns
    print(f"\n📈 Date value distribution (top 10):")
    value_counts = df[date_col].value_counts().head(10)
    for val, count in value_counts.items():
        print(f"  {repr(val):40s} : {count:6d} occurrences")
    
    # Try parsing with pandas
    print(f"\n🔧 Testing pandas date parsing...")
    df_test = df.copy()
    df_test['parsed_date'] = pd.to_datetime(
        df_test[date_col],
        dayfirst=True,
        errors='coerce',
        utc=True
    )
    
    valid_dates = df_test['parsed_date'].notna().sum()
    invalid_dates = df_test['parsed_date'].isna().sum()
    
    print(f"  Valid dates parsed: {valid_dates}")
    print(f"  Invalid dates (NaT): {invalid_dates}")
    print(f"  Invalid percentage: {invalid_dates/len(df)*100:.1f}%")
    
    # Show examples of dates that failed to parse
    print(f"\n❌ Sample dates that FAILED to parse (first 20):")
    failed_df = df_test[df_test['parsed_date'].isna() & df_test[date_col].notna()]
    if not failed_df.empty:
        for idx, (_, row) in enumerate(failed_df.head(20).iterrows(), 1):
            print(f"  {idx:2d}. {repr(row[date_col])}")
    else:
        print("  (All non-null dates parsed successfully)")
    
    # Show examples of dates that successfully parsed
    print(f"\n✅ Sample dates that SUCCEEDED to parse (first 10):")
    success_df = df_test[df_test['parsed_date'].notna()]
    if not success_df.empty:
        for idx, (_, row) in enumerate(success_df.head(10).iterrows(), 1):
            print(f"  {idx:2d}. Raw: {repr(row[date_col]):40s} → Parsed: {row['parsed_date']}")
    
    # Check for empty strings or whitespace
    print(f"\n🔍 Checking for empty/whitespace-only values...")
    empty_count = (df[date_col].astype(str).str.strip() == '').sum()
    print(f"  Empty or whitespace-only: {empty_count}")
    
    # Check data types
    print(f"\n📦 Data type analysis:")
    dtype_counts = df[date_col].apply(lambda x: type(x).__name__).value_counts()
    for dtype, count in dtype_counts.items():
        print(f"  {dtype}: {count} rows")
    
    print("\n✅ Diagnosis complete!")
    print("\n💡 Recommendations:")
    print("  1. Check if dates are actually empty strings")
    print("  2. Check if dates use an unexpected format")
    print("  3. Check if column contains mixed data types")
    print("  4. Consider cleaning the Google Sheet source data")

if __name__ == "__main__":
    diagnose_acca_dates()
