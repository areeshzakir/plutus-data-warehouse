# Plutus Data Warehouse

A modular data pipeline for centralizing marketing and sales funnel data from multiple sources into Supabase.

## 🎯 Project Overview

This data warehouse consolidates data from:
- Google Sheets (marketing campaigns, lead data)
- Zoom (webinar/bootcamp attendance via CSV)
- Custom CRM (sales pipeline data)
- Marketing spend data

**Current Status:** ✅ Microservice #1 Complete - TOFU Leads Ingestion

## 📁 Project Structure

```
Plutus-data-warehouse/
├── cli.py                      # Main CLI entry point
├── config.py                   # Central configuration
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (gitignored)
│
├── microservices/              # Independent microservices
│   └── tofu_ingestion/        # ✅ TOFU leads from Google Sheets
│       ├── main.py
│       └── README.md
│
├── services/                   # Shared service clients
│   ├── google_sheets.py       # Google Sheets API client
│   └── supabase_db.py         # Supabase database client
│
├── utils/                      # Utility functions
│   ├── phone_utils.py         # Phone normalization & UserID generation
│   └── logging_utils.py       # Logging configuration
│
├── supabase/                   # Database migrations
│   └── migrations/
│       └── 20250112_create_tofu_leads_table.sql
│
├── credentials/                # Service account credentials (gitignored)
├── logs/                       # Application logs (gitignored)
└── docs/                       # Project documentation
```

## 🚀 Quick Start

### 1. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

1. Place your Google Service Account JSON at `credentials/google_service_account.json`
2. Update `.env` with your Supabase credentials (already set up)
3. Share Google Sheets with the service account email

### 3. Run Your First Microservice

```bash
# Test with dry-run
python cli.py tofu-ingestion --dry-run --verbose

# Run for real
python cli.py tofu-ingestion
```

## 📊 Microservices

### ✅ #1: TOFU Leads Ingestion

**Status:** Complete and ready to use

**Purpose:** Fetch marketing leads from 3 Google Sheets and store incrementally in Supabase

**Sources:**
- Sheet1 (Main leads)
- ACCA (ACCA program leads)
- Bootcamp_30_March (Bootcamp participants)

**Features:**
- Incremental loading (only new records)
- Phone validation & UserID generation (91 + 10-digit)
- Date parsing & validation
- Automatic deduplication
- Error handling per source

**Documentation:** [microservices/tofu_ingestion/README.md](microservices/tofu_ingestion/README.md)

**Usage:**
```bash
python cli.py tofu-ingestion [--dry-run] [--verbose] [--sheet SHEET_NAME]
```

### ✅ #2: BOFU Transactions Ingestion

**Status:** Complete and aligned with the TOFU tooling.

**Purpose:** Pull ready-to-store transaction data from the Testbook CSV API and write it to Supabase exactly as received. A unique constraint on `txn_id` prevents duplicates while still attempting to insert every row each run.

**Features:**
- Reads config from `.env` (`BOFU_API_URL`, `BOFU_API_KEY`, `BOFU_SUPABASE_TABLE`).
- Keeps column order agnostic; missing columns become NULLs, unexpected ones get logged and stored inside a JSON `payload` column so nothing is lost.
- Uses the shared logging + Supabase helpers; logs live at `logs/bofu_ingestion.log`.

**Documentation:** [microservices/bofu_ingestion/README.md](microservices/bofu_ingestion/README.md)

**Usage:**
```bash
python cli.py bofu-ingestion [--dry-run] [--verbose]
```

### 🔜 Future Microservices

- **#3:** Zoom Webinar/Bootcamp Data Processing
- **#4:** CRM Sales Data Sync
- **#5:** Marketing Spend Aggregation
- **#6:** Unified Reporting Layer

## 🗄️ Database Schema

### Current Tables

#### `tofu_leads`
Marketing leads from Google Sheets with validation and computed UserID.

**Key Columns:**
- `user_id` (TEXT, UNIQUE) - Phone-based identifier (91 + 10-digit)
- `source_sheet` (TEXT) - Which Google Sheet the record came from
- `created_date` (TIMESTAMP) - Original record creation date
- `ingested_at` (TIMESTAMP) - When imported to database

See migration: `supabase/migrations/20250112_create_tofu_leads_table.sql`

## 🔧 Configuration

All configuration is centralized in:
- `.env` - Environment-specific variables (credentials, URLs)
- `config.py` - Application configuration (sheet IDs, column mappings)

**Key Environment Variables:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google_service_account.json
LOG_LEVEL=INFO
BOFU_API_URL=https://data.testbook.com/api/queries/18351/results.csv
BOFU_API_KEY=your-api-key
BOFU_SUPABASE_TABLE=bofu_transactions
```

## 📝 Logging

Logs are written to:
- Console (INFO level)
- `logs/tofu_ingestion.log` for TOFU runs (DEBUG level)
- `logs/bofu_ingestion.log` for BOFU runs (DEBUG level)

View logs:
```bash
tail -f logs/tofu_ingestion.log
```

## 🔐 Security

**Credentials are NOT committed to git:**
- `.env` contains sensitive keys
- `credentials/` contains service account JSON
- Both are in `.gitignore`

**For deployment:**
- Use environment variables or secrets management
- Never commit credentials to version control

## 📅 Scheduling

### Local (Cron)

```bash
# Edit crontab
crontab -e

# Run daily at 6 AM
0 6 * * * cd /path/to/Plutus-data-warehouse && ./venv/bin/python cli.py tofu-ingestion
```

### GitHub Actions

See `microservices/tofu_ingestion/README.md` for GitHub Actions workflow example.

## 🧪 Testing

```bash
# Dry-run (no database writes)
python cli.py tofu-ingestion --dry-run

# Verbose output for debugging
python cli.py tofu-ingestion --dry-run --verbose

# Test single sheet
python cli.py tofu-ingestion --dry-run --sheet Sheet1
```

## 📚 Documentation

- **Project Overview:** [docs/edtech_funnel_doc.md](docs/edtech_funnel_doc.md)
- **PRD:** [prd.md](prd.md)
- **TOFU Microservice:** [microservices/tofu_ingestion/README.md](microservices/tofu_ingestion/README.md)

## 🤝 Development Guidelines

### Adding a New Microservice

1. Create directory: `microservices/your_service/`
2. Implement `main.py` with a `main()` function
3. Add CLI command in `cli.py`
4. Write README with usage instructions
5. Add database migrations if needed

### Code Style

- Use type hints
- Document functions with docstrings
- Log important operations
- Handle errors gracefully
- Keep microservices independent

## 🎯 Next Steps

1. ✅ **Test TOFU ingestion** - Run with `--dry-run` first
2. ⏭️ **Add your Google Service Account JSON** to `credentials/`
3. ⏭️ **Share Google Sheets** with service account email
4. ⏭️ **Run first ingestion** - `python cli.py tofu-ingestion`
5. ⏭️ **Verify data in Supabase** - Check `tofu_leads` table
6. ⏭️ **Set up scheduling** - Cron or GitHub Actions

## 📞 Support

For issues:
1. Check logs: `logs/tofu_ingestion.log`
2. Run with `--verbose` flag
3. Review microservice README
4. Check Supabase dashboard for database issues

---

**Version:** 1.0.0 - TOFU Ingestion Microservice  
**Last Updated:** November 2025
