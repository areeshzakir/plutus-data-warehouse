"""
Central configuration for Plutus Data Warehouse
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
BASE_DIR = Path(__file__).parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
LOGS_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "tofu_leads"

# Google Service Account
GOOGLE_SERVICE_ACCOUNT_FILE = BASE_DIR / os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", 
    "credentials/google_service_account.json"
)

# Google Sheets Configuration - TOFU Leads
TOFU_SHEETS = [
    {
        "id": os.getenv("SHEET_1_ID"),
        "tab": os.getenv("SHEET_1_TAB"),
        "name": os.getenv("SHEET_1_NAME", "Sheet1"),
    },
    {
        "id": os.getenv("SHEET_2_ID"),
        "tab": os.getenv("SHEET_2_TAB"),
        "name": os.getenv("SHEET_2_NAME", "ACCA"),
    },
    {
        "id": os.getenv("SHEET_3_ID"),
        "tab": os.getenv("SHEET_3_TAB"),
        "name": os.getenv("SHEET_3_NAME", "Bootcamp_30_March"),
    },
]

# Column mappings
TOFU_COLUMNS = [
    "Name",
    "Email", 
    "Phone number",
    "City",
    "Question 1",
    "utmSource",
    "utmMedium",
    "utmCamp",
    "created date",
    "ad name",
]

# Database column mapping (Google Sheets -> Supabase)
DB_COLUMN_MAP = {
    "Name": "name",
    "Full name": "name",  # Alternative column name
    "Email": "email",
    "Phone number": "phone_number",
    "City": "city",
    "Question 1": "question_1",
    "utmSource": "utm_source",
    "utmMedium": "utm_medium",
    "utmCamp": "utm_camp",
    "created date": "created_date",
    "ad name": "ad_name",
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/tofu_ingestion.log")

# Validation
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

if not GOOGLE_SERVICE_ACCOUNT_FILE.exists():
    raise ValueError(
        f"Google Service Account file not found at {GOOGLE_SERVICE_ACCOUNT_FILE}. "
        f"Please place your service account JSON file in the credentials directory."
    )
