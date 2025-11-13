#!/usr/bin/env bash
# Run TOFU ingestion once; suitable for cron/launchd
# Logs to logs/scheduler.log

set -euo pipefail

PROJECT_DIR="/Users/classplus/My Projects/Plutus-data-warehouse"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/scheduler.log"

mkdir -p "$LOG_DIR"

# Export env from .env (if present)
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$PROJECT_DIR/.env"
  set +a
fi

# Ensure Google credentials path is available if defined in config
export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-$PROJECT_DIR/credentials/google_service_account.json}"

cd "$PROJECT_DIR"

echo "[$(date -Is)] START tofu-ingestion" >> "$LOG_FILE"
"$PROJECT_DIR/venv/bin/python" cli.py tofu-ingestion >> "$LOG_FILE" 2>&1 || echo "[$(date -Is)] ERROR during run" >> "$LOG_FILE"
echo "[$(date -Is)] END tofu-ingestion" >> "$LOG_FILE"
