"""Persist long-running analysis jobs to disk.

Uvicorn's --reload and multi-worker setups clear in-memory state; polling would
otherwise get 404 for a valid job_id."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# backend/.analysis_jobs/{uuid}.json
_JOBS_DIR = Path(__file__).resolve().parents[2] / ".analysis_jobs"

_SAFE_JOB_ID = re.compile(r"^[0-9a-fA-F-]{36}$")


def _job_path(job_id: str) -> Path:
    if not _SAFE_JOB_ID.match(job_id):
        raise ValueError("invalid job_id")
    return _JOBS_DIR / f"{job_id}.json"


def save_job(job_id: str, payload: dict[str, Any]) -> None:
    """Write job state. *payload* must be JSON-serialisable."""
    path = _job_path(job_id)
    _JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_job(job_id: str) -> dict[str, Any] | None:
    """Return job dict or None if missing / invalid id."""
    try:
        path = _job_path(job_id)
    except ValueError:
        return None
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("could not read job %s: %s", job_id, exc)
        return None
