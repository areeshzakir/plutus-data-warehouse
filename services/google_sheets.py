"""
Google Sheets API client for fetching data
"""
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from typing import Optional
import logging

from config import GOOGLE_SERVICE_ACCOUNT_FILE

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Client for interacting with Google Sheets API"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    def __init__(self):
        """Initialize Google Sheets client with service account authentication"""
        try:
            credentials = Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=self.SCOPES
            )
            self.client = gspread.authorize(credentials)
            logger.info("Google Sheets client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def fetch_sheet_data(
        self, 
        sheet_id: str, 
        tab_name: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch data from a specific Google Sheet tab.
        
        Args:
            sheet_id: Google Sheets spreadsheet ID
            tab_name: Name of the worksheet/tab
            
        Returns:
            DataFrame with sheet data, or None if error occurs
        """
        try:
            logger.info(f"Fetching data from sheet {sheet_id}, tab '{tab_name}'")
            
            # Open spreadsheet
            spreadsheet = self.client.open_by_key(sheet_id)
            logger.debug(f"Opened spreadsheet: {spreadsheet.title}")
            
            # Get worksheet
            try:
                worksheet = spreadsheet.worksheet(tab_name)
            except gspread.exceptions.WorksheetNotFound:
                logger.error(f"Worksheet '{tab_name}' not found in spreadsheet")
                return None
            
            # Fetch all records
            records = worksheet.get_all_records()
            
            if not records:
                logger.warning(f"No data found in worksheet '{tab_name}'")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            logger.info(
                f"Fetched {len(df)} rows from '{tab_name}' "
                f"with columns: {list(df.columns)}"
            )
            
            return df
            
        except gspread.exceptions.APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching sheet data: {e}", exc_info=True)
            return None
