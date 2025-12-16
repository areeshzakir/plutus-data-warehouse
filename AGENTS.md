# Repository Guidelines

## Project Structure & Module Organization
Top-level `cli.py` dispatches ingestion workflows, reading sheet IDs and secrets from `config.py` and `.env`. Microservices live under `microservices/`, each with its own `main.py` and README; mirror existing pipelines such as `microservices/tofu_ingestion`, `microservices/zoom_ingestion`, `microservices/mofu_ingestion`, and `microservices/bofu_ingestion` when adding new ones. Shared integrations sit in `services/` (`google_sheets.py`, `supabase_db.py`, `transaction_api.py`) while reusable helpers remain in `utils/` (`phone_utils.py`, `logging_utils.py`). Database migrations belong in `supabase/migrations/`, and any docs or playbooks should go into `docs/` to keep operational context versioned.

## Build, Test, and Development Commands
Use the repo-level virtual environment and CLI commands below for all local work:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python cli.py tofu-ingestion --dry-run --verbose
python cli.py tofu-ingestion --sheet ACCA
python cli.py tofu-ingestion
python cli.py zoom-ingestion --dry-run --verbose
python cli.py mofu-ingestion --dry-run --verbose
python cli.py bofu-ingestion --dry-run --verbose
```

Dry-run mode performs validation without touching Supabase; drop `--dry-run` to ingest for real. Run `python microservices/*/main.py --dry-run` only when debugging a specific module in isolation.

## Coding Style & Naming Conventions
Target Python 3.10+, use 4-space indentation, and keep modules and filenames in `snake_case`. Add type hints and short docstrings that describe inputs, outputs, and side effects. Wire up loggers through `utils.logging_utils` instead of `print`. Name new microservices with matching directory and CLI slug (`microservices/zoom_sync` + `zoom-sync`), and keep configuration centralized in `config.py` rather than hard-coding sheet IDs or database URLs.

## Testing Guidelines
Formal unit tests are pending, so rely on controlled executions plus Supabase checks. Always start with `python cli.py tofu-ingestion --dry-run --verbose` (or the equivalent `zoom-ingestion`, `mofu-ingestion`, `bofu-ingestion`) and confirm the summary reflects only new rows. Tail the relevant log (`logs/tofu_ingestion.log`, `logs/zoom_ingestion.log`, etc.) for traceback-level detail, and verify the target tables (`tofu_leads`, `zoom_webinar_attendance`, `mofu_lead_assignments`, `bofu_transactions`) inside Supabase after each write. Use sheet/API-specific runs (e.g., `--sheet Bootcamp_30_March`) to isolate data issues.

## Commit & Pull Request Guidelines
History uses short, imperative messages (`Delete README.md`, `Initial commit...`), so keep subjects ≤72 characters and add optional wrapped body text explaining the motivation. Each pull request should include: a concise change summary, linked issue or task ID, recent command output (dry-run or live ingestion), notes on any schema or config edits with pointers to `supabase/migrations/...`, and screenshots or log excerpts when they clarify the impact.

## Security & Configuration Tips
Never commit `.env`, Supabase keys, or Google credentials; everything under `credentials/` and `logs/` stays gitignored. Store the service account JSON securely and reference it via `GOOGLE_SERVICE_ACCOUNT_FILE`. Review migrations for accidental PII exposure before pushing, and scrub downloaded CSVs before attaching them to issues.
