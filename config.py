"""Configuration module — loads environment variables via python-dotenv."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level up from ivf_advisor/)
_env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_env_path, override=False)


def _require(name: str) -> str:
    """Return the value of a required environment variable, raising if absent."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set. "
            f"Copy .env.example to .env and fill in the values."
        )
    return value


def _optional(name: str, default: str = "") -> str:
    """Return the value of an optional environment variable."""
    return os.getenv(name, default)


# ---------------------------------------------------------------------------
# Required configuration
# ---------------------------------------------------------------------------

GOOGLE_API_KEY: str = _optional("GOOGLE_API_KEY")  # Not needed when using ADC on GCP
GOOGLE_CLOUD_PROJECT: str = _optional("GOOGLE_CLOUD_PROJECT")
VERTEX_SEARCH_DATASTORE_ID: str = _optional("VERTEX_SEARCH_DATASTORE_ID")

# ---------------------------------------------------------------------------
# Optional configuration (with sensible defaults)
# ---------------------------------------------------------------------------

GOOGLE_CLOUD_REGION: str = _optional("GOOGLE_CLOUD_REGION", "us-central1")
REDIS_URL: str = _optional("REDIS_URL", "redis://localhost:6379/0")

# ---------------------------------------------------------------------------
# Agent constants
# ---------------------------------------------------------------------------

AGENT_NAME: str = "ivf_treatment_advisor"
AGENT_MODEL: str = "gemini-1.5-pro"

# Latency SLA thresholds (seconds) — Requirement 13
LATENCY_SLA_NO_TOOL: int = 10
LATENCY_SLA_WITH_TOOL: int = 20
