"""
TOFU Leads Ingestion - Main Orchestrator

Fetches marketing leads from Google Sheets and stores them incrementally in Supabase.
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import TOFU_SHEETS, DB_COLUMN_MAP
from services.google_sheets import GoogleSheetsClient
from services.supabase_db import SupabaseClient
from utils.phone_utils import generate_user_id
from utils.logging_utils import setup_logger

logger = logging.getLogger(__name__)


class TOFUIngestionOrchestrator:
    """Orchestrates the TOFU leads ingestion process"""
    
    def __init__(self):
        """Initialize clients"""
        logger.info("Initializing TOFU Ingestion Orchestrator")
        self.sheets_client = GoogleSheetsClient()
        self.db_client = SupabaseClient()
    
    def process_sheet(
        self,
        sheet_config: Dict,
        dry_run: bool = False
    ) -> Dict:
        """
        Process a single Google Sheet.
        
        Args:
            sheet_config: Dict with keys: id, tab, name
            dry_run: If True, skip database writes
            
        Returns:
            Summary dict with processing stats
        """
        sheet_name = sheet_config['name']
        sheet_id = sheet_config['id']
        tab_name = sheet_config['tab']
        
        logger.info(f"Processing sheet: {sheet_name} (tab: {tab_name})")
        
        summary = {
            'sheet': sheet_name,
            'fetched': 0,
            'invalid_phone': 0,
            'invalid_date': 0,
            'new_records': 0,
            'upserted': 0,
            'skipped': 0,
            'error': None
        }
        
        try:
            # 1. Get last ingestion timestamp
            last_timestamp = self.db_client.get_last_ingestion_timestamp(sheet_name)
            
            # 2. Fetch data from Google Sheets
            df_raw = self.sheets_client.fetch_sheet_data(sheet_id, tab_name)
            
            if df_raw is None or df_raw.empty:
                logger.warning(f"No data fetched from {sheet_name}")
                return summary
            
            summary['fetched'] = len(df_raw)
            logger.info(f"Fetched {len(df_raw)} rows from {sheet_name}")
            
            # 3. Normalize column names and rename to DB columns
            df = self._normalize_columns(df_raw)
            
            # 4. Parse and validate created_date
            df, invalid_dates = self._parse_dates(df)
            summary['invalid_date'] = invalid_dates
            
            if df.empty:
                logger.warning(f"No valid records after date parsing for {sheet_name}")
                return summary
            
            # 5. Generate user_id from phone number
            df, invalid_phones = self._generate_user_ids(df)
            summary['invalid_phone'] = invalid_phones
            
            if df.empty:
                logger.warning(f"No valid records after phone validation for {sheet_name}")
                return summary
            
            # 6. Add source_sheet column
            df['source_sheet'] = sheet_name
            
            # 7. Apply incremental filter
            if last_timestamp:
                before_filter = len(df)
                df = df[df['created_date'] > last_timestamp]
                filtered_out = before_filter - len(df)
                logger.info(
                    f"Incremental filter: keeping {len(df)} new records "
                    f"(filtered out {filtered_out} existing)"
                )
            
            summary['new_records'] = len(df)
            
            if df.empty:
                logger.info(f"No new records to process for {sheet_name}")
                return summary
            
            # 8. Remove in-memory exact duplicates before sending to DB
            # This reduces unnecessary API calls for duplicates in the same batch
            before_dedup = len(df)
            df = df.drop_duplicates(keep='first')
            duplicates_removed = before_dedup - len(df)
            
            if duplicates_removed > 0:
                logger.info(
                    f"Removed {duplicates_removed} exact in-memory duplicates, "
                    f"{len(df)} records to insert"
                )
            
            # 9. Prepare for upsert
            df_clean = self._prepare_for_upsert(df)
            
            # 10. Insert or dry-run
            if dry_run:
                logger.info(f"[DRY RUN] Would insert {len(df_clean)} records")
                logger.debug(f"Sample record: {df_clean.iloc[0].to_dict()}")
                summary['upserted'] = len(df_clean)
            else:
                result = self.db_client.insert_records(df_clean)
                summary['upserted'] = result['succeeded']
                summary['skipped'] = result.get('skipped', 0)
            
            logger.info(
                f"✓ Completed {sheet_name}: {summary['new_records']} new, "
                f"{summary['upserted']} inserted, {summary['skipped']} skipped"
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing {sheet_name}: {error_msg}", exc_info=True)
            summary['error'] = error_msg
        
        return summary
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize and rename columns to match database schema"""
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Rename columns using DB_COLUMN_MAP
        columns_to_rename = {}
        for sheet_col, db_col in DB_COLUMN_MAP.items():
            if sheet_col in df.columns:
                columns_to_rename[sheet_col] = db_col
        
        df = df.rename(columns=columns_to_rename)
        
        # Keep only columns that are in the database
        db_columns = list(DB_COLUMN_MAP.values())
        existing_db_cols = [col for col in db_columns if col in df.columns]
        df = df[existing_db_cols]
        
        logger.debug(f"Normalized columns: {list(df.columns)}")
        return df
    
    def _parse_dates(self, df: pd.DataFrame) -> tuple:
        """Parse created_date column and filter invalid dates"""
        if 'created_date' not in df.columns:
            logger.error("created_date column not found")
            return pd.DataFrame(), len(df)
        
        # Filter out empty strings first
        empty_mask = df['created_date'].astype(str).str.strip() == ''
        empty_count = empty_mask.sum()
        if empty_count > 0:
            logger.warning(f"Dropping {empty_count} rows with empty dates")
        
        # Parse dates without dayfirst to properly handle ISO 8601 format
        # This works for both ISO 8601 (YYYY-MM-DD) and other common formats
        df['created_date'] = pd.to_datetime(
            df['created_date'],
            errors='coerce',
            utc=True
        )
        
        # Count and remove rows with invalid/unparseable dates (excluding empties)
        invalid_mask = df['created_date'].isna()
        invalid_count = invalid_mask.sum()
        
        if invalid_count > empty_count:
            unparseable = invalid_count - empty_count
            logger.warning(
                f"Dropping {unparseable} additional rows with unparseable dates"
            )
        
        df_valid = df[~invalid_mask].copy()
        
        # Filter out future-dated records (more than 1 day ahead)
        # This prevents CHECK constraint violations that would skip entire batches
        from datetime import datetime, timezone, timedelta
        max_allowed_date = datetime.now(timezone.utc) + timedelta(days=1)
        future_mask = df_valid['created_date'] > max_allowed_date
        future_count = future_mask.sum()
        
        if future_count > 0:
            logger.warning(
                f"Dropping {future_count} rows with future dates (beyond {max_allowed_date.date()})"
            )
            df_valid = df_valid[~future_mask].copy()
        
        return df_valid, invalid_count + future_count
    
    def _generate_user_ids(self, df: pd.DataFrame) -> tuple:
        """Generate user_id from phone_number"""
        if 'phone_number' not in df.columns:
            logger.error("phone_number column not found")
            return pd.DataFrame(), len(df)
        
        # Generate user_id for each row
        df['user_id'] = df['phone_number'].apply(generate_user_id)
        
        # Count and remove rows with invalid user_ids
        invalid_mask = df['user_id'].isna()
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            logger.warning(f"Dropping {invalid_count} rows with invalid phone numbers")
        
        df_valid = df[~invalid_mask].copy()
        return df_valid, invalid_count
    
    def _prepare_for_upsert(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for database upsert"""
        # Convert timestamp to ISO format string
        if 'created_date' in df.columns:
            df['created_date'] = df['created_date'].dt.strftime('%Y-%m-%d %H:%M:%S%z')
        
        # Fill NaN with None for proper NULL handling
        df = df.where(pd.notna(df), None)
        
        return df
    
    def run(
        self,
        dry_run: bool = False,
        sheet_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Run the ingestion process for all configured sheets.
        
        Args:
            dry_run: If True, skip database writes
            sheet_filter: If provided, only process this specific sheet
            
        Returns:
            List of summary dicts, one per sheet
        """
        logger.info("="*60)
        logger.info("Starting TOFU Leads Ingestion")
        if dry_run:
            logger.info("** DRY RUN MODE - No database writes **")
        logger.info("="*60)
        
        # Filter sheets if specified
        sheets_to_process = TOFU_SHEETS
        if sheet_filter:
            sheets_to_process = [
                s for s in TOFU_SHEETS 
                if s['name'] == sheet_filter or s['tab'] == sheet_filter
            ]
            if not sheets_to_process:
                logger.error(f"No sheet found matching filter: {sheet_filter}")
                return []
        
        logger.info(f"Processing {len(sheets_to_process)} sheet(s)")
        
        # Process each sheet
        summaries = []
        for sheet_config in sheets_to_process:
            summary = self.process_sheet(sheet_config, dry_run)
            summaries.append(summary)
        
        # Print overall summary
        self._print_summary(summaries)
        
        return summaries
    
    def _print_summary(self, summaries: List[Dict]):
        """Print summary table"""
        logger.info("="*60)
        logger.info("INGESTION SUMMARY")
        logger.info("="*60)
        
        total_fetched = 0
        total_new = 0
        total_upserted = 0
        total_skipped = 0
        errors = []
        
        for s in summaries:
            status = "✓" if not s['error'] else "✗"
            logger.info(
                f"{status} {s['sheet']:20} | "
                f"Fetched: {s['fetched']:6} | "
                f"New: {s['new_records']:6} | "
                f"Inserted: {s['upserted']:6} | "
                f"Skipped: {s['skipped']:5}"
            )
            
            if s['error']:
                errors.append(f"{s['sheet']}: {s['error']}")
            
            total_fetched += s['fetched']
            total_new += s['new_records']
            total_upserted += s['upserted']
            total_skipped += s['skipped']
        
        logger.info("-"*60)
        logger.info(
            f"TOTAL{' '*16} | "
            f"Fetched: {total_fetched:6} | "
            f"New: {total_new:6} | "
            f"Inserted: {total_upserted:6} | "
            f"Skipped: {total_skipped:5}"
        )
        logger.info("="*60)
        
        if errors:
            logger.error("ERRORS:")
            for error in errors:
                logger.error(f"  - {error}")


def main(dry_run: bool = False, verbose: bool = False, sheet: Optional[str] = None):
    """
    Main entry point for TOFU ingestion.
    
    Args:
        dry_run: Skip database writes
        verbose: Enable debug logging
        sheet: Process only this specific sheet
        
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Setup logging
    from config import LOG_FILE, LOG_LEVEL
    log_level = "DEBUG" if verbose else LOG_LEVEL
    setup_logger("root", LOG_FILE, log_level)
    
    # Run orchestrator
    orchestrator = TOFUIngestionOrchestrator()
    summaries = orchestrator.run(dry_run=dry_run, sheet_filter=sheet)
    
    # Determine exit code
    has_errors = any(s['error'] is not None for s in summaries)
    exit_code = 1 if has_errors else 0
    
    return exit_code


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TOFU Leads Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Skip database writes")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--sheet", type=str, help="Process only this sheet")
    
    args = parser.parse_args()
    exit_code = main(dry_run=args.dry_run, verbose=args.verbose, sheet=args.sheet)
    sys.exit(exit_code)
