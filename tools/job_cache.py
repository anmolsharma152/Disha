"""
Simple file-backed job fetch cache.

Stores normalized JobOpening dicts by cache key with TTL so re-queries
do not hammer WWR/YC/Greenhouse every time.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("disha.tools.job_cache")

_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TTL_SECONDS = int(os.environ.get("DISHA_JOB_CACHE_TTL", str(12 * 3600)))


def _cache_dir() -> Path:
    base = Path(os.environ.get("DISHA_DATA_DIR", str(_ROOT / "data")))
    d = base / "job_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _key_path(cache_key: str) -> Path:
    h = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:40]
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in cache_key)[:60]
    return _cache_dir() / f"{safe}_{h}.json"


def get_cached_jobs(cache_key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Optional[List[Dict[str, Any]]]:
    path = _key_path(cache_key)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ts = float(payload.get("cached_at", 0))
        if time.time() - ts > ttl_seconds:
            return None
        jobs = payload.get("jobs")
        if isinstance(jobs, list):
            logger.info("[Cache] HIT %s (%d jobs)", cache_key, len(jobs))
            return jobs
    except Exception as e:
        logger.warning("[Cache] read failed %s: %s", cache_key, e)
    return None


def set_cached_jobs(cache_key: str, jobs: List[Dict[str, Any]]) -> None:
    path = _key_path(cache_key)
    try:
        path.write_text(
            json.dumps(
                {"cached_at": time.time(), "cache_key": cache_key, "jobs": jobs},
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )
        logger.info("[Cache] STORE %s (%d jobs)", cache_key, len(jobs))
    except Exception as e:
        logger.warning("[Cache] write failed %s: %s", cache_key, e)


def job_dedupe_key(job: Dict[str, Any]) -> str:
    title = (job.get("title") or "").strip().lower()
    company = (job.get("company_name") or "").strip().lower()
    url = (job.get("source_url") or job.get("application_url") or "").strip().lower()
    if url:
        # strip query params for stability
        url = url.split("?")[0]
        return f"url:{url}"
    return f"tc:{company}|{title}"


def dedupe_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for j in jobs:
        k = job_dedupe_key(j)
        if k in seen:
            continue
        seen.add(k)
        out.append(j)
    return out
