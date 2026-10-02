"""Environment-driven configuration. Nothing here is hardcoded for production use."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://localhost:5432/morocco_observatory"
    )
    # The registry is read from the existing Next.js app, never hand-copied.
    # See app/api/registry/route.ts — it re-exports the existing HCP_INDICATORS array.
    registry_url: str = os.getenv("REGISTRY_URL", "http://localhost:3000/api/registry")
    registry_cache_path: str = os.getenv(
        "REGISTRY_CACHE_PATH", "tests/fixtures/registry_cache.json"
    )
    hcp_timeout_seconds: int = int(os.getenv("HCP_TIMEOUT_SECONDS", "20"))
    hcp_max_retries: int = int(os.getenv("HCP_MAX_RETRIES", "3"))


settings = Settings()
