"""MOFU Lead Assignments ingestion pipeline"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict
import logging
from zoneinfo import ZoneInfo

import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import (  # noqa: E402
    LOG_LEVEL,
    MOFU_API_URL,
    MOFU_DB_COLUMN_MAP,
    MOFU_EXPECTED_COLUMNS,
    MOFU_LOG_FILE,
    MOFU_SUPABASE_TABLE,
)
from services.mofu_api import MOFUAPIClient  # noqa: E402
from services.supabase_db import SupabaseClient  # noqa: E402
from utils.logging_utils import setup_logger  # noqa: E402


logger = logging.getLogger(__name__)


IST = ZoneInfo("Asia/Kolkata")


class MOFUIngestionOrchestrator:
    """Fetches MOFU lead assignments and writes them to Supabase"""

    def __init__(self):
        logger.info("Initializing MOFU Ingestion Orchestrator")
        self.api_client = MOFUAPIClient(MOFU_API_URL)
        self.db_client = SupabaseClient(table_name=MOFU_SUPABASE_TABLE)

    def run(self, dry_run: bool = False) -> Dict:
        summary = {
            "fetched": 0,
            "invalid_date": 0,
            "inserted": 0,
            "skipped": 0,
            "missing_columns": [],
            "unexpected_columns": [],
            "error": None,
        }

        try:
            df_raw = self.api_client.fetch_assignments()
            summary["fetched"] = len(df_raw)

            if df_raw.empty:
                logger.warning("No MOFU rows returned by API")
                return summary

            df_prepared, invalid_dates, missing, unexpected = self._prepare_dataframe(df_raw)
            summary["invalid_date"] = invalid_dates
            summary["missing_columns"] = missing
            summary["unexpected_columns"] = unexpected

            if df_prepared.empty:
                logger.warning("No valid MOFU records after date parsing")
                return summary

            # Incremental filter based on assign_on and sources
            df_filtered = self._apply_incremental_filter(df_prepared)
            if df_filtered.empty:
                logger.info("No new MOFU records to insert after incremental filter")
                return summary

            # Drop exact duplicates in-memory (ignore payload so dicts don't break hashing)
            before_dedup = len(df_filtered)
            dedupe_cols = [col for col in df_filtered.columns if col != "payload"]
            df_filtered = df_filtered.drop_duplicates(subset=dedupe_cols, keep="first")
            duplicates_removed = before_dedup - len(df_filtered)
            if duplicates_removed > 0:
                logger.info("Removed %s exact in-memory duplicates", duplicates_removed)

            df_clean = self._prepare_for_upsert(df_filtered)

            if dry_run:
                logger.info("[DRY RUN] Would insert %s MOFU records", len(df_clean))
                logger.debug("Sample MOFU record: %s", df_clean.iloc[0].to_dict())
                summary["inserted"] = len(df_clean)
            else:
                result = self.db_client.insert_records(df_clean)
                summary["inserted"] = result.get("succeeded", 0)
                summary["skipped"] = result.get("skipped", 0)

            logger.info(
                "✓ MOFU ingestion complete: %s fetched, %s inserted, %s skipped",
                summary["fetched"],
                summary["inserted"],
                summary["skipped"],
            )

        except Exception as exc:  # pragma: no cover - safety net
            summary["error"] = str(exc)
            logger.error("MOFU ingestion failed: %s", exc, exc_info=True)

        return summary

    def _prepare_dataframe(self, df_raw: pd.DataFrame):
        """Handle schema drift, rename columns, parse dates"""
        df = df_raw.copy()
        df.columns = df.columns.str.strip()

        payload_records = df.to_dict("records")

        incoming_cols = set(df.columns)
        expected_cols_raw = set(MOFU_DB_COLUMN_MAP.keys())

        missing = sorted(expected_cols_raw - incoming_cols)
        unexpected = sorted(incoming_cols - expected_cols_raw)

        if missing:
            logger.warning(
                "MOFU response missing columns: %s. Filling them with NULLs.",
                ", ".join(missing),
            )
            for col in missing:
                df[col] = None

        if unexpected:
            logger.warning(
                "MOFU response returned new columns: %s. Storing them only in payload.",
                ", ".join(unexpected),
            )

        ordered_cols = [col for col in MOFU_DB_COLUMN_MAP.keys() if col in df.columns]
        df = df[ordered_cols]
        df = df.rename(columns=MOFU_DB_COLUMN_MAP)

        for column in MOFU_EXPECTED_COLUMNS:
            if column not in df.columns:
                df[column] = None

        df = df[MOFU_EXPECTED_COLUMNS]
        df["payload"] = payload_records

        df_parsed, invalid_dates = self._parse_assign_on(df)
        return df_parsed, invalid_dates, missing, unexpected

    def _parse_assign_on(self, df: pd.DataFrame):
        if "assign_on" not in df.columns:
            logger.error("assign_on column not found")
            return pd.DataFrame(), len(df)

        parsed = pd.to_datetime(df["assign_on"], errors="coerce")
        try:
            parsed = parsed.dt.tz_localize(IST, ambiguous="NaT", nonexistent="NaT")
        except TypeError:
            # If already timezone-aware, just convert
            parsed = parsed.dt.tz_convert(IST)

        invalid_mask = parsed.isna()
        invalid_count = invalid_mask.sum()
        if invalid_count > 0:
            logger.warning("Dropping %s rows with invalid assignOn timestamps", invalid_count)

        parsed_utc = parsed.dt.tz_convert("UTC")
        df_valid = df[~invalid_mask].copy()
        df_valid["assign_on"] = parsed_utc[~invalid_mask]

        return df_valid, invalid_count

    def _apply_incremental_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only records newer than the last ingested assign_on per source."""
        if df.empty:
            return df

        # Group by source to reduce repeated lookups
        filtered_frames = []
        for source_value, group in df.groupby("sources"):
            last_ts = self.db_client.get_last_ingestion_timestamp(
                source_value=source_value,
                date_column="assign_on",
                source_column="sources",
            )

            if last_ts:
                before = len(group)
                group = group[group["assign_on"] > last_ts]
                filtered_out = before - len(group)
                logger.info(
                    "Incremental filter for %s: keeping %s, filtered out %s",
                    source_value,
                    len(group),
                    filtered_out,
                )

            filtered_frames.append(group)

        if not filtered_frames:
            return pd.DataFrame(columns=df.columns)

        return pd.concat(filtered_frames, ignore_index=True)

    def _prepare_for_upsert(self, df: pd.DataFrame) -> pd.DataFrame:
        df_ready = df.copy()
        if "assign_on" in df_ready.columns:
            df_ready["assign_on"] = df_ready["assign_on"].dt.strftime("%Y-%m-%d %H:%M:%S%z")

        df_ready = df_ready.where(pd.notna(df_ready), None)
        return df_ready


def main(dry_run: bool = False, verbose: bool = False) -> int:
    """Entry point for CLI"""
    log_level = "DEBUG" if verbose else LOG_LEVEL
    setup_logger("root", MOFU_LOG_FILE, log_level)

    orchestrator = MOFUIngestionOrchestrator()
    summary = orchestrator.run(dry_run=dry_run)

    exit_code = 1 if summary.get("error") else 0
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="MOFU Lead Assignments Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Skip database writes")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run, verbose=args.verbose))
