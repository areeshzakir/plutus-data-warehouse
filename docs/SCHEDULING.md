# Scheduling the TOFU Ingestion

This service can be scheduled in two ways. Pick ONE:

Option A) Local schedule on your Mac via cron
Option B) GitHub Actions (runs in the cloud)

Option A: macOS cron
1. Make the runner executable:
   chmod +x "/Users/classplus/My Projects/Plutus-data-warehouse/scripts/run_tofu_ingestion.sh"

2. Add a daily cron at 3:00 AM local time:
   crontab -e
   # then add this line:
   0 3 * * * /bin/bash "/Users/classplus/My Projects/Plutus-data-warehouse/scripts/run_tofu_ingestion.sh" >> "/Users/classplus/My Projects/Plutus-data-warehouse/logs/scheduler.log" 2>&1

3. Verify logs:
   tail -f "/Users/classplus/My Projects/Plutus-data-warehouse/logs/scheduler.log"

Notes:
- The script sources .env so SUPABASE_URL/KEY and other vars are available
- Google creds default to credentials/google_service_account.json

Option B: GitHub Actions (recommended if you want it off your laptop)
1. Add repo secrets:
   - SUPABASE_URL
   - SUPABASE_KEY (service role preferred)
   - GOOGLE_SERVICE_ACCOUNT_JSON (paste full JSON)

2. The workflow below runs daily at 03:00 UTC. It writes the JSON to credentials/google_service_account.json and runs the ingestion.

3. Enable workflows in your repo settings.

