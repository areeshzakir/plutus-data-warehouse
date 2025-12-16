#!/usr/bin/env python3
"""Map question_1 field from tofu_leads table to CSV records by phone number."""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.supabase_db import SupabaseClient


def main():
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    input_file = "/Users/classplus/Downloads/Areesh - Data Cleanup for WebIngestion - Sheet14.csv"
    output_file = f"/Users/classplus/Downloads/Areesh - Data Cleanup for WebIngestion - Sheet14_with_question1_{timestamp}.csv"
    
    # Read CSV
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} records from CSV")
    
    # Get unique phone numbers (user_ids)
    phone_numbers = df['Phone'].astype(str).tolist()
    
    # Connect to database
    db = SupabaseClient()
    
    # Fetch question_1 for all phone numbers
    # Query in batches to avoid hitting limits
    batch_size = 100
    question_map = {}
    
    for i in range(0, len(phone_numbers), batch_size):
        batch = phone_numbers[i:i + batch_size]
        result = db.client.table('tofu_leads').select('user_id, question_1').in_('user_id', batch).execute()
        
        for row in result.data:
            question_map[row['user_id']] = row['question_1']
        
        print(f"Processed {min(i + batch_size, len(phone_numbers))}/{len(phone_numbers)} phone numbers")
    
    # Map question_1 to dataframe
    df['question_1'] = df['Phone'].astype(str).map(question_map)
    
    # Stats
    matched = df['question_1'].notna().sum()
    print(f"\nMatched {matched}/{len(df)} records ({matched/len(df)*100:.1f}%)")
    
    # Save output
    df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
