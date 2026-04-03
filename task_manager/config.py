"""Configuration for the task_manager package — loads environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_env_path, override=False)


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default)


# Database
# Production: AlloyDB via Cloud SQL Python Connector
# Local dev: SQLite fallback
DATABASE_URL: str = _optional(
    "DATABASE_URL", "sqlite+aiosqlite:///./task_manager.db"
)

# AlloyDB instance URI (used by Cloud SQL connector in production)
ALLOYDB_INSTANCE_URI: str = _optional(
    "ALLOYDB_INSTANCE_URI",
    "projects/ivf-agent/locations/us-central1/clusters/ivf-care-cluster/instances/ivf-care-cluster-primary",
)

ALLOYDB_DB: str = _optional("ALLOYDB_DB", "task_manager")
ALLOYDB_USER: str = _optional("ALLOYDB_USER", "postgres")
ALLOYDB_PASSWORD: str = _optional("ALLOYDB_PASSWORD", "")

# Security
SECRET_KEY: str = _optional("SECRET_KEY", "change-me-in-production")

# Google Cloud
GOOGLE_CLOUD_PROJECT: str = _optional("GOOGLE_CLOUD_PROJECT", "ivf-agent")
GOOGLE_CLOUD_REGION: str = _optional("GOOGLE_CLOUD_REGION", "us-central1")

# Agent model
AGENT_MODEL: str = _optional("AGENT_MODEL", "gemini-2.5-flash")
