"""HTTP client for fetching bottom-of-funnel transaction data"""
from __future__ import annotations

import io
import logging
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs

import pandas as pd
import requests


logger = logging.getLogger(__name__)


class TransactionAPIClient:
    """Client that fetches CSV data from the BOFU API endpoint"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 60):
        if not base_url:
            raise ValueError("BOFU_API_URL must be provided in the environment")
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def _build_url(self) -> str:
        """Inject api_key query param if provided and missing"""
        if not self.api_key:
            return self.base_url

        parsed = urlparse(self.base_url)
        query = parse_qs(parsed.query)
        if "api_key" in query:
            # assume caller embedded the key already; don't override
            return self.base_url

        query["api_key"] = [self.api_key]
        encoded = urlencode(query, doseq=True)
        rebuilt = parsed._replace(query=encoded)
        return urlunparse(rebuilt)

    def fetch_transactions(self) -> pd.DataFrame:
        """Download the CSV and return a DataFrame (never drops rows)"""
        url = self._build_url()
        logger.info("Fetching BOFU transactions from %s", url)

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Failed to fetch BOFU transactions: %s", exc)
            raise

        if not response.text.strip():
            logger.warning("BOFU API returned an empty response")
            return pd.DataFrame()

        df = pd.read_csv(io.StringIO(response.text))
        logger.info("Fetched %s BOFU rows", len(df))
        return df
