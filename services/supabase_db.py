"""
Supabase database client for TOFU leads
"""
from datetime import datetime
from typing import Optional, Dict, List, Union
import logging
import pandas as pd
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Client for interacting with Supabase database"""
    
    def __init__(self):
        """Initialize Supabase client"""
        try:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def get_last_ingestion_timestamp(self, source_sheet: str) -> Optional[datetime]:
        """
        Get the most recent created_date for a specific source sheet.
        
        Args:
            source_sheet: Name of the source sheet
            
        Returns:
            Most recent datetime, or None if no records exist
        """
        try:
            logger.debug(f"Fetching last ingestion timestamp for source: {source_sheet}")
            
            response = (
                self.client.table(SUPABASE_TABLE)
                .select("created_date")
                .eq("source_sheet", source_sheet)
                .order("created_date", desc=True)
                .limit(1)
                .execute()
            )
            
            if response.data and len(response.data) > 0:
                # Parse the timestamp string to datetime
                timestamp_str = response.data[0].get("created_date")
                if timestamp_str:
                    timestamp = pd.to_datetime(timestamp_str, utc=True)
                    logger.info(f"Last ingestion timestamp for '{source_sheet}': {timestamp}")
                    return timestamp.to_pydatetime()
            
            logger.info(f"No existing records found for source: {source_sheet}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching last ingestion timestamp: {e}", exc_info=True)
            return None
    
    def insert_records(
        self, 
        records: Union[List[Dict], pd.DataFrame],
        batch_size: int = 5000
    ) -> Dict[str, int]:
        """
        Insert records into the database, skipping exact duplicates.
        Uses upsert with ignoreDuplicates to handle the unique constraint on all fields.
        
        Duplicate = ALL fields identical (name, email, phone, city, question_1, 
        utm_source, utm_medium, utm_camp, created_date, ad_name, source_sheet)
        
        Args:
            records: List of dicts or DataFrame to insert
            batch_size: Number of records to process in each batch
            
        Returns:
            Dict with counts: {
                'attempted': total records,
                'succeeded': successfully inserted,
                'skipped': duplicates skipped
            }
        """
        # Convert DataFrame to list of dicts if needed
        if isinstance(records, pd.DataFrame):
            records = records.to_dict('records')
        
        if not records:
            logger.warning("No records to insert")
            return {'attempted': 0, 'succeeded': 0, 'skipped': 0}
        
        total = len(records)
        succeeded = 0
        skipped = 0
        
        logger.info(f"Starting insert of {total} records in batches of {batch_size}")
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            try:
                logger.debug(f"Inserting batch {batch_num}/{total_batches} ({len(batch)} records)")
                
                # Try to insert entire batch
                response = (
                    self.client.table(SUPABASE_TABLE)
                    .insert(batch)
                    .execute()
                )
                
                if response.data:
                    batch_success = len(response.data)
                    succeeded += batch_success
                    logger.debug(f"Batch {batch_num}: {batch_success} inserted")
                else:
                    succeeded += len(batch)
                    logger.debug(f"Batch {batch_num} completed")
                    
            except Exception as e:
                # Check if it's a duplicate key error (code 23505)
                error_str = str(e)
                if '23505' in error_str or 'duplicate key' in error_str.lower():
                    # Batch has duplicates - try smaller sub-batches
                    logger.debug(f"Batch {batch_num} has duplicates, using sub-batches...")
                    batch_succeeded = 0
                    batch_skipped = 0
                    
                    # Try sub-batches of 100 records
                    sub_batch_size = 100
                    for sub_i in range(0, len(batch), sub_batch_size):
                        sub_batch = batch[sub_i:sub_i + sub_batch_size]
                        try:
                            sub_response = (
                                self.client.table(SUPABASE_TABLE)
                                .insert(sub_batch)
                                .execute()
                            )
                            if sub_response.data:
                                batch_succeeded += len(sub_response.data)
                        except Exception as sub_error:
                            # Sub-batch still has duplicates - try one by one
                            for record in sub_batch:
                                try:
                                    single_response = (
                                        self.client.table(SUPABASE_TABLE)
                                        .insert([record])
                                        .execute()
                                    )
                                    if single_response.data:
                                        batch_succeeded += 1
                                except:
                                    batch_skipped += 1
                    
                    succeeded += batch_succeeded
                    skipped += batch_skipped
                    logger.debug(
                        f"Batch {batch_num}: {batch_succeeded} inserted, "
                        f"{batch_skipped} skipped (duplicates)"
                    )
                else:
                    # Unexpected error
                    logger.error(
                        f"Batch {batch_num} unexpected error: {e}",
                        exc_info=True
                    )
                    skipped += len(batch)
        
        result = {
            'attempted': total,
            'succeeded': succeeded,
            'skipped': skipped
        }
        
        logger.info(
            f"Insert complete: {succeeded}/{total} inserted, {skipped} skipped (duplicates)"
        )
        
        return result
