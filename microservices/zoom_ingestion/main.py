"""Zoom Webinar attendance ingestion pipeline"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from zoneinfo import ZoneInfo
import logging

import pandas as pd

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import (  # noqa: E402
    LOG_LEVEL,
    ZOOM_DB_COLUMN_MAP,
    ZOOM_EXPECTED_COLUMNS,
    ZOOM_LOG_FILE,
    ZOOM_SHEET_ID,
    ZOOM_SHEET_TAB,
    ZOOM_SUPABASE_TABLE,
)
from services.google_sheets import GoogleSheetsClient  # noqa: E402
from services.supabase_db import SupabaseClient  # noqa: E402
from utils.logging_utils import setup_logger  # noqa: E402
from utils.phone_utils import normalize_phone, generate_user_id  # noqa: E402


logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


BOOLEAN_TRUE = {"yes", "true", "1", "y"}
BOOLEAN_FALSE = {"no", "false", "0", "n"}


def normalize_space(text: str) -> str:
    text = str(text or "").strip()
    return " ".join(text.split())


def proper_case(text: str) -> str:
    if not text:
        return text
    return " ".join(word.capitalize() for word in normalize_space(text).split(" "))


def normalize_bool(value: str) -> Tuple[bool, str]:
    token = (value or "").strip().lower()
    if token in BOOLEAN_TRUE:
        return True, "Yes"
    if token in BOOLEAN_FALSE:
        return False, "No"
    return False, ""


def parse_datetime(value: str) -> Optional[pd.Timestamp]:
    if not value or not str(value).strip():
        return None
    dt = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(dt):
        return None
    if dt.tzinfo is None:
        dt = dt.tz_localize(IST)
    else:
        dt = dt.tz_convert(IST)
    return dt


def first_non_blank(values: List[str]) -> str:
    for item in values:
        if isinstance(item, str) and item.strip():
            return item
    return ""


class ZoomIngestionOrchestrator:
    """Fetch, clean, dedupe, and load Zoom webinar attendance"""

    def __init__(self):
        logger.info("Initializing Zoom Ingestion Orchestrator")
        self.sheets_client = GoogleSheetsClient()
        self.db_client = SupabaseClient(table_name=ZOOM_SUPABASE_TABLE)
        self.source_sheet_name = ZOOM_SHEET_TAB

    def run(self, dry_run: bool = False) -> Dict:
        summary = {
            "fetched": 0,
            "invalid_contact": 0,
            "invalid_dates": 0,
            "deduped": 0,
            "inserted": 0,
            "skipped": 0,
            "error": None,
        }

        try:
            df_raw = self.sheets_client.fetch_sheet_data(ZOOM_SHEET_ID, ZOOM_SHEET_TAB)
            summary["fetched"] = len(df_raw) if df_raw is not None else 0

            if df_raw is None or df_raw.empty:
                logger.warning("No Zoom data fetched")
                return summary

            df_clean, invalid_contact, invalid_dates = self._clean_dataframe(df_raw)
            summary["invalid_contact"] = invalid_contact
            summary["invalid_dates"] = invalid_dates

            if df_clean.empty:
                logger.warning("No valid rows after cleaning")
                return summary

            df_dedup = self._dedupe(df_clean)
            summary["deduped"] = len(df_dedup)

            df_filtered = self._apply_incremental_filter(df_dedup)
            if df_filtered.empty:
                logger.info("No new Zoom records to insert after incremental filter")
                return summary

            df_ready = self._prepare_for_upsert(df_filtered)

            if dry_run:
                logger.info("[DRY RUN] Would insert %s Zoom records", len(df_ready))
                logger.debug("Sample Zoom record: %s", df_ready.iloc[0].to_dict())
                summary["inserted"] = len(df_ready)
            else:
                result = self.db_client.insert_records(df_ready)
                summary["inserted"] = result.get("succeeded", 0)
                summary["skipped"] = result.get("skipped", 0)

            logger.info(
                "✓ Zoom ingestion complete: %s fetched, %s inserted, %s skipped",
                summary["fetched"],
                summary["inserted"],
                summary["skipped"],
            )

        except Exception as exc:  # pragma: no cover
            summary["error"] = str(exc)
            logger.error("Zoom ingestion failed: %s", exc, exc_info=True)

        return summary

    def _clean_dataframe(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
        df = df_raw.copy()
        df.columns = df.columns.str.strip()

        payload_records = df.to_dict("records")
        payload_series = pd.Series(payload_records, index=df.index)

        # Rename to snake_case
        columns_to_rename = {k: v for k, v in ZOOM_DB_COLUMN_MAP.items() if k in df.columns}
        df = df.rename(columns=columns_to_rename)

        # Keep only expected columns
        keep_cols = [col for col in ZOOM_EXPECTED_COLUMNS if col in df.columns]
        df = df[keep_cols]
        # Align payload length after column filtering
        payload_records = df.to_dict("records")

        # Normalize text fields
        for col in [
            "category",
            "attended",
            "user_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "registration_time",
            "approval_status",
            "join_time",
            "leave_time",
            "is_guest",
            "country_region_name",
            "source",
        ]:
            if col in df.columns:
                df[col] = df[col].astype(str).map(normalize_space)

        df["user_name"] = df.get("user_name", "").map(proper_case)
        df["first_name"] = df.get("first_name", "").map(proper_case)
        df["last_name"] = df.get("last_name", "").map(proper_case)
        df["country_region_name"] = df.get("country_region_name", "").map(proper_case)
        df["email"] = df.get("email", "").str.lower()

        # Clean phone and build user_id
        df["phone"] = df.get("phone", "").map(normalize_phone)
        df["user_id"] = df["phone"].map(lambda p: generate_user_id(p) if p else None)

        # Boolean normalization
        attended_bool, attended_str = zip(*(normalize_bool(v) for v in df.get("attended", "")))
        df["attended_bool"] = attended_bool
        df["attended"] = attended_str

        guest_bool, guest_str = zip(*(normalize_bool(v) for v in df.get("is_guest", "")))
        df["is_guest_bool"] = guest_bool
        df["is_guest"] = guest_str

        # Time parsing
        df["join_dt"] = df.get("join_time", "").replace({"--": ""}).map(parse_datetime)
        df["leave_dt"] = df.get("leave_time", "").replace({"--": ""}).map(parse_datetime)
        df["registration_dt"] = df.get("registration_time", "").replace({"--": ""}).map(parse_datetime)

        invalid_dates = int(df["join_dt"].isna().sum() + df["leave_dt"].isna().sum() + df["registration_dt"].isna().sum())

        # Webinar date to date-only (IST)
        webinar_dates = pd.to_datetime(df.get("webinar_date", ""), dayfirst=True, errors="coerce")
        df["webinar_date_dt"] = webinar_dates.dt.tz_localize(IST, nonexistent="NaT", ambiguous="NaT")
        df["webinar_date_date"] = df["webinar_date_dt"].dt.date

        # Time in session minutes
        df["time_in_session_minutes"] = pd.to_numeric(
            df.get("time_in_session_minutes", 0).replace({"": 0, "--": 0}),
            errors="coerce",
        ).fillna(0).astype(int)

        # Drop rows with no usable contact (no phone and no email) or missing webinar_date
        contact_mask = df["phone"].astype(bool) | df.get("email", "").astype(bool)
        date_mask = df["webinar_date_date"].notna()
        invalid_contact = int((~contact_mask | ~date_mask).sum())
        df = df[contact_mask & date_mask].copy()

        # Attach payload aligned to filtered index
        df["payload"] = payload_series.loc[df.index].tolist()
        df["source_sheet"] = self.source_sheet_name

        return df, invalid_contact, invalid_dates

    def _dedupe(self, df: pd.DataFrame) -> pd.DataFrame:
        grouped_rows: List[Dict[str, object]] = []

        # Create grouping key: (webinar_date_date, primary_identifier)
        df["dedupe_key"] = df.apply(
            lambda row: (row["webinar_date_date"], row["phone"] if row["phone"] else row.get("email", "")),
            axis=1,
        )

        for (_, _), group in df.groupby("dedupe_key", sort=False):
            grouped_rows.append(self._aggregate_group(group))

        return pd.DataFrame(grouped_rows)

    def _aggregate_group(self, group: pd.DataFrame) -> Dict[str, object]:
        group_sorted = group.sort_values(by="join_dt", ascending=True)
        result: Dict[str, object] = {}

        result["webinar_date"] = group_sorted.iloc[0]["webinar_date_date"].isoformat()
        result["source_sheet"] = group_sorted.iloc[0]["source_sheet"]

        # Sum time in session
        result["time_in_session_minutes"] = int(group_sorted["time_in_session_minutes"].sum())

        # Join/leave
        join_candidates = group_sorted["join_dt"].dropna()
        leave_candidates = group_sorted["leave_dt"].dropna()
        result["join_time"] = (
            join_candidates.min().astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%d %H:%M:%S%z")
            if not join_candidates.empty
            else None
        )
        result["leave_time"] = (
            leave_candidates.max().astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%d %H:%M:%S%z")
            if not leave_candidates.empty
            else None
        )

        result["attended"] = "Yes" if group_sorted["attended_bool"].any() else "No"

        if group_sorted["is_guest_bool"].any():
            result["is_guest"] = "Yes"
        elif (group_sorted["is_guest"].eq("No")).all():
            result["is_guest"] = "No"
        else:
            result["is_guest"] = ""

        for column in [
            "user_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "registration_time",
            "approval_status",
            "country_region_name",
            "source",
            "category",
        ]:
            result[column] = first_non_blank(group_sorted[column].tolist()) if column in group_sorted.columns else ""

        # If registration_dt parsed, use earliest formatted UTC
        reg_dt_candidates = group_sorted["registration_dt"].dropna()
        result["registration_time"] = (
            reg_dt_candidates.min().astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%d %H:%M:%S%z")
            if not reg_dt_candidates.empty
            else None
        )

        result["user_id"] = generate_user_id(result["phone"]) if result.get("phone") else None

        # Keep mon if present
        result["mon"] = first_non_blank(group_sorted.get("mon", pd.Series([], dtype=str)).astype(str).tolist()) if "mon" in group_sorted else None

        # Keep payload from first row (original data)
        result["payload"] = group_sorted.iloc[0].get("payload")

        return result

    def _apply_incremental_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        last_ts = self.db_client.get_last_ingestion_timestamp(
            source_value=self.source_sheet_name,
            date_column="webinar_date",
            source_column="source_sheet",
        )

        if last_ts:
            before = len(df)
            df["webinar_date_dt"] = pd.to_datetime(df["webinar_date"], utc=True)
            df = df[df["webinar_date_dt"] > last_ts]
            filtered_out = before - len(df)
            logger.info("Incremental filter: keeping %s, filtered out %s", len(df), filtered_out)

        return df

    def _prepare_for_upsert(self, df: pd.DataFrame) -> pd.DataFrame:
        df_ready = df.copy()
        # webinar_date already ISO date string; join/leave/registration already formatted strings or None
        df_ready = df_ready.where(pd.notna(df_ready), None)
        return df_ready


def main(dry_run: bool = False, verbose: bool = False) -> int:
    """Entry point for CLI"""
    log_level = "DEBUG" if verbose else LOG_LEVEL
    setup_logger("root", ZOOM_LOG_FILE, log_level)

    orchestrator = ZoomIngestionOrchestrator()
    summary = orchestrator.run(dry_run=dry_run)

    exit_code = 1 if summary.get("error") else 0
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="Zoom Webinar Attendance Ingestion")
    parser.add_argument("--dry-run", action="store_true", help="Skip database writes")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run, verbose=args.verbose))
