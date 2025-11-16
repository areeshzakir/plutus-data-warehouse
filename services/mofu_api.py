"""HTTP client for fetching middle-of-funnel lead assignment data"""
from __future__ import annotations

import io
import logging
from typing import Optional

import pandas as pd
import requests


logger = logging.getLogger(__name__)


class MOFUAPIClient:
    """Client that fetches CSV data from the MOFU API endpoint"""

    def __init__(self, base_url: str, timeout: int = 60):
        if not base_url:
            raise ValueError("MOFU_API_URL must be provided in the environment")
        self.base_url = base_url
        self.timeout = timeout

    def fetch_assignments(self) -> pd.DataFrame:
        """Download the CSV and return a DataFrame (never drops rows)"""
        logger.info("Fetching MOFU assignments from %s", self.base_url)

        try:
            response = requests.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch MOFU assignments: %s", exc)
            raise

        if not response.text.strip():
            logger.warning("MOFU API returned an empty response")
            return pd.DataFrame()

        df = pd.read_csv(io.StringIO(response.text))
        logger.info("Fetched %s MOFU rows", len(df))
        return df
