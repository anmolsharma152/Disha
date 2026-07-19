"""
Y Combinator Work at a Startup job source.

Parses the public jobs page which embeds a JSON job list in the HTML
(server-rendered props). No Algolia key required for the initial page set.
"""

from __future__ import annotations

import html as html_lib
import json
import logging
import re
import urllib.request
from typing import Any, Dict, List, Optional, Sequence

from tools.job_cache import get_cached_jobs, set_cached_jobs
from tools.job_normalizer import normalize_yc_job, validate_job_dict

logger = logging.getLogger("disha.sources.yc")

WAAS_JOBS_URL = "https://www.workatastartup.com/jobs"
WAAS_ENGINEERING_URL = "https://www.workatastartup.com/jobs/l/software-engineer"


def _fetch_html(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; DishaBot/1.0; "
                "+https://github.com/anmolsharma152/Disha)"
            ),
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _extract_jobs_json(page_html: str) -> List[Dict[str, Any]]:
    """
    Jobs are embedded as HTML-escaped JSON inside a React props blob:
    &quot;jobs&quot;:[{...}]
    """
    # Unescape common entities then find "jobs":[
    unescaped = html_lib.unescape(page_html)
    # Prefer the largest jobs array
    matches = list(re.finditer(r'"jobs"\s*:\s*\[', unescaped))
    if not matches:
        # try raw escaped form
        matches = list(re.finditer(r'&quot;jobs&quot;\s*:\s*\[', page_html))
        if matches:
            unescaped = html_lib.unescape(page_html)
            matches = list(re.finditer(r'"jobs"\s*:\s*\[', unescaped))
    if not matches:
        logger.warning("[YC] No jobs array found in page")
        return []

    # Parse from first match with a bracket counter
    start = matches[0].end() - 1  # points at '['
    depth = 0
    end = None
    for i, ch in enumerate(unescaped[start:], start=start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        logger.warning("[YC] Failed to close jobs JSON array")
        return []

    raw = unescaped[start:end]
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except json.JSONDecodeError as e:
        logger.warning("[YC] JSON parse failed: %s", e)
    return []


def fetch_yc_jobs(
    *,
    keywords: Optional[Sequence[str]] = None,
    max_results: int = 40,
    prefer_engineering: bool = True,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Fetch YC Work-at-a-Startup jobs and normalize."""
    kw = [k.lower() for k in (keywords or []) if k]
    url = WAAS_ENGINEERING_URL if prefer_engineering else WAAS_JOBS_URL
    cache_key = f"yc:{'eng' if prefer_engineering else 'all'}:kw={','.join(sorted(kw)[:8])}:n={max_results}"

    if use_cache:
        cached = get_cached_jobs(cache_key)
        if cached is not None:
            return cached[:max_results]

    logger.info("[YC] Fetching %s", url)
    try:
        page = _fetch_html(url)
    except Exception as e:
        logger.warning("[YC] page fetch failed: %s", e)
        return []

    raw_jobs = _extract_jobs_json(page)
    logger.info("[YC] Parsed %d raw jobs from page", len(raw_jobs))

    jobs: List[Dict[str, Any]] = []
    for raw in raw_jobs:
        title = (raw.get("title") or "").lower()
        role = (raw.get("roleType") or "").lower()
        company = (raw.get("companyName") or "").lower()
        blob = f"{title} {role} {company} {raw.get('location') or ''}".lower()
        if kw and not any(k in blob for k in kw):
            continue
        try:
            norm = normalize_yc_job(raw)
            validated = validate_job_dict(norm)
            if validated:
                jobs.append(validated)
        except Exception as e:
            logger.debug("[YC] normalize skip: %s", e)

    if use_cache and jobs:
        set_cached_jobs(cache_key, jobs)

    logger.info("[YC] Returning %d jobs", len(jobs[:max_results]))
    return jobs[:max_results]
