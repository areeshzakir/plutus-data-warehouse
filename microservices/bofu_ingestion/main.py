"""BOFU Transactions ingestion pipeline"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict
import math
import numbers
import numpy as np
from decimal import Decimal

import logging
import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import (  # noqa: E402
    BOFU_API_KEY,
    BOFU_API_URL,
    BOFU_DB_COLUMN_MAP,
    BOFU_EXPECTED_COLUMNS,
    BOFU_LOG_FILE,
    BOFU_SUPABASE_TABLE,
    LOG_LEVEL,
)
from services.transaction_api import TransactionAPIClient  # noqa: E402
from services.supabase_db import SupabaseClient  # noqa: E402
from utils.logging_utils import setup_logger  # noqa: E402


logger = logging.getLogger(__name__)


class BOFUIngestionOrchestrator:
    """Fetches BOFU transactions and writes them to Supabase"""

    def __init__(self):
        logger.info("Initializing BOFU Ingestion Orchestrator")
        self.api_client = TransactionAPIClient(BOFU_API_URL, BOFU_API_KEY)
        self.db_client = SupabaseClient(table_name=BOFU_SUPABASE_TABLE)

    def run(self, dry_run: bool = False) -> Dict:
        summary = {
            "fetched": 0,
            "inserted": 0,
            "skipped": 0,
            "error": None,
        }

        try:
            df_raw = self.api_client.fetch_transactions()
            summary["fetched"] = len(df_raw)

            if df_raw.empty:
                logger.warning("No BOFU rows returned by API")
                return summary

            df_prepared = self._prepare_dataframe(df_raw)

            if dry_run:
                logger.info("[DRY RUN] Would insert %s BOFU rows", len(df_prepared))
                logger.debug("Sample BOFU record: %s", df_prepared.iloc[0].to_dict())
                summary["inserted"] = len(df_prepared)
            else:
                result = self.db_client.insert_records(df_prepared)
                summary["inserted"] = result.get("succeeded", 0)
                summary["skipped"] = result.get("skipped", 0)

            logger.info(
                "✓ BOFU ingestion complete: %s fetched, %s inserted, %s skipped",
                summary["fetched"],
                summary["inserted"],
                summary["skipped"],
            )

        except Exception as exc:  # pragma: no cover - safety net
            summary["error"] = str(exc)
            logger.error("BOFU ingestion failed: %s", exc, exc_info=True)

        return summary

    def _prepare_dataframe(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """Rename columns to DB schema and add payload column"""
        df = df_raw.copy()
        df.columns = df.columns.str.strip()

        incoming_cols = set(df.columns)
        expected_cols = set(BOFU_DB_COLUMN_MAP.keys())

        missing = sorted(expected_cols - incoming_cols)
        unexpected = sorted(incoming_cols - expected_cols)

        if missing:
            logger.warning(
                "BOFU response missing columns: %s. Filling them with NULLs.",
                ", ".join(missing),
            )
            for col in missing:
                df[col] = None

        if unexpected:
            logger.warning(
                "BOFU response returned new columns: %s. Storing them only in payload.",
                ", ".join(unexpected),
            )

        payload_records = [self._sanitize_payload(rec) for rec in df.to_dict("records")]

        ordered_cols = [col for col in BOFU_DB_COLUMN_MAP.keys() if col in df.columns]
        df = df[ordered_cols]
        df = df.rename(columns=BOFU_DB_COLUMN_MAP)
        df["payload"] = payload_records

        # Ensure all expected DB columns exist even if missing upstream
        for column in BOFU_EXPECTED_COLUMNS:
            if column not in df.columns:
                df[column] = None

        df = df[BOFU_EXPECTED_COLUMNS + ["payload"]]
        df = df.astype(object).where(pd.notna(df), None)
        return df

    @staticmethod
    def _sanitize_payload(record: Dict[str, object]) -> Dict[str, object]:
        clean: Dict[str, object] = {}
        for key, value in record.items():
            if isinstance(value, numbers.Real):
                if isinstance(value, np.floating):
                    value = float(value)
                if isinstance(value, Decimal):
                    value = float(value)
                if pd.isna(value):
                    clean[key] = None
                elif math.isinf(value):
                    clean[key] = 0
                else:
                    clean[key] = value
            elif hasattr(value, "isoformat"):
                clean[key] = value.isoformat()
            else:
                clean[key] = value
        return clean


def main(dry_run: bool = False, verbose: bool = False) -> int:
    """Entry point for CLI"""
    log_level = "DEBUG" if verbose else LOG_LEVEL
    setup_logger("root", BOFU_LOG_FILE, log_level)

    orchestrator = BOFUIngestionOrchestrator()
    summary = orchestrator.run(dry_run=dry_run)

    exit_code = 1 if summary.get("error") else 0
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="BOFU Transactions Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Skip database writes")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run, verbose=args.verbose))
