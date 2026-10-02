"""Raw HTTP fetch for one HCP indicator. This module never parses the
response — it only fetches, hashes, and reports what happened, so the
raw_objects row is always honest about exactly what came back over the wire.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import requests

from data_pipeline.config.settings import settings


@dataclass
class RawFetchResult:
    url: str
    http_status: int
    retrieved_at: datetime
    checksum: str
    raw_payload: Optional[Any]
    error: Optional[str] = None


def _checksum(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def fetch_raw(api_url: str) -> RawFetchResult:
    last_error = None
    for attempt in range(1, settings.hcp_max_retries + 1):
        try:
            response = requests.get(api_url, timeout=settings.hcp_timeout_seconds)
            retrieved_at = datetime.now(timezone.utc)
            checksum = _checksum(response.content)
            try:
                payload = response.json()
            except ValueError:
                payload = None
            return RawFetchResult(
                url=api_url,
                http_status=response.status_code,
                retrieved_at=retrieved_at,
                checksum=checksum,
                raw_payload=payload,
            )
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt < settings.hcp_max_retries:
                time.sleep(1.5 * attempt)
    return RawFetchResult(
        url=api_url,
        http_status=0,
        retrieved_at=datetime.now(timezone.utc),
        checksum="",
        raw_payload=None,
        error=last_error or "unknown fetch error",
    )
