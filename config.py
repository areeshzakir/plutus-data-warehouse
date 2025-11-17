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

# Bottom of Funnel (BOFU) API Configuration
BOFU_API_URL = os.getenv("BOFU_API_URL")
BOFU_API_KEY = os.getenv("BOFU_API_KEY")
BOFU_SUPABASE_TABLE = os.getenv("BOFU_SUPABASE_TABLE", "bofu_transactions")

# Middle of Funnel (MOFU) API Configuration
MOFU_API_URL = os.getenv("MOFU_API_URL")
MOFU_SUPABASE_TABLE = os.getenv("MOFU_SUPABASE_TABLE", "mofu_lead_assignments")

# Zoom Webinar Data (Google Sheets)
ZOOM_SHEET_ID = os.getenv(
    "ZOOM_SHEET_ID",
    "1_5weku38mXGFrGZgHa0yGo8VDxn6XMXkXbThLpp8FhY",
)
ZOOM_SHEET_TAB = os.getenv("ZOOM_SHEET_TAB", "Zoom Data - July/Jun")
ZOOM_SUPABASE_TABLE = os.getenv("ZOOM_SUPABASE_TABLE", "zoom_webinar_attendance")


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

# Bottom of Funnel (BOFU) Transaction Columns
BOFU_DB_COLUMN_MAP = {
    "_id": "mongo_id",
    "status": "status",
    "txn_id": "txn_id",
    "sid": "sid",
    "emiId": "emi_id",
    "pId": "pid",
    "paymentGateway": "payment_gateway",
    "target": "target",
    "targetSuperGroup": "target_super_group",
    "courseName": "course_name",
    "source": "source",
    "tokenAmount": "token_amount",
    "WithOut_Token_paidAmount": "without_token_paid_amount",
    "createdOn": "created_on",
    "pType": "p_type",
    "eBookRev": "ebook_rev",
    "bookRev": "book_rev",
    "paymentType": "payment_type",
    "DP": "dp",
    "Total_emis": "total_emis",
    "lastEmiDate": "last_emi_date",
    "total_emis_due": "total_emis_due",
    "Total_Timely_EMIs_paid": "total_timely_emis_paid",
    "paidAmount": "paid_amount",
    "corePartner": "core_partner",
    "StudentEmail": "student_email",
    "StudentContact": "student_contact",
    "StudentSignupDate": "student_signup_date",
    "StudentName": "student_name",
    "TotalAmount": "total_amount",
    "product": "product",
    "mandateStatus": "mandate_status",
    "EBook_Net_Amount": "ebook_net_amount",
    "Book_Net_Amount": "book_net_amount",
    "Product_Net_Amount": "product_net_amount",
    "netAmount": "net_amount",
    "employeeName": "employee_name",
    "employeeTeam": "employee_team",
    "Total_emi": "total_emi",
    "Paid_Emi_Count": "paid_emi_count",
    "Unpaid_Emi_Count": "unpaid_emi_count",
    "Paid_Emi_Amount": "paid_emi_amount",
    "Unpaid_Amount": "unpaid_amount",
    "Last_Paid_Date": "last_paid_date",
    "netAmountAfterPDD": "net_amount_after_pdd",
}
BOFU_EXPECTED_COLUMNS = list(BOFU_DB_COLUMN_MAP.values())

# Middle of Funnel (MOFU) Lead Assignment Columns
MOFU_DB_COLUMN_MAP = {
    "sources": "sources",
    "assignOn": "assign_on",
    "leadMobile": "lead_mobile",
    "employee": "employee",
}
MOFU_EXPECTED_COLUMNS = list(MOFU_DB_COLUMN_MAP.values())

# Zoom Webinar Columns
ZOOM_DB_COLUMN_MAP = {
    "Mon": "mon",
    "Webinar Date": "webinar_date",
    "Category": "category",
    "Attended": "attended",
    "User Name (Original Name)": "user_name",
    "First Name": "first_name",
    "Last Name": "last_name",
    "Email": "email",
    "Phone": "phone",
    "Registration Time": "registration_time",
    "Approval Status": "approval_status",
    "Join Time": "join_time",
    "Leave Time": "leave_time",
    "Time in Session (minutes)": "time_in_session_minutes",
    "Is Guest": "is_guest",
    "Country/Region Name": "country_region_name",
    "Source": "source",
}
ZOOM_EXPECTED_COLUMNS = list(ZOOM_DB_COLUMN_MAP.values())

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/tofu_ingestion.log")
BOFU_LOG_FILE = BASE_DIR / os.getenv("BOFU_LOG_FILE", "logs/bofu_ingestion.log")
MOFU_LOG_FILE = BASE_DIR / os.getenv("MOFU_LOG_FILE", "logs/mofu_ingestion.log")
ZOOM_LOG_FILE = BASE_DIR / os.getenv("ZOOM_LOG_FILE", "logs/zoom_ingestion.log")

# Validation
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

if not GOOGLE_SERVICE_ACCOUNT_FILE.exists():
    raise ValueError(
        f"Google Service Account file not found at {GOOGLE_SERVICE_ACCOUNT_FILE}. "
        f"Please place your service account JSON file in the credentials directory."
    )
