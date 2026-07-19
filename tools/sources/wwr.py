"""
We Work Remotely job source via public RSS feeds.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import feedparser

from tools.job_cache import get_cached_jobs, set_cached_jobs
from tools.job_normalizer import normalize_wwr_job, validate_job_dict

logger = logging.getLogger("disha.sources.wwr")

WWR_CATEGORIES = {
    "programming": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "devops": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "all": "https://weworkremotely.com/remote-jobs.rss",
}

DEFAULT_CATEGORIES = ("programming", "devops")


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def _parse_company_title(raw_title: str) -> tuple[str, str]:
    """WWR titles are usually 'Company: Role'."""
    t = (raw_title or "").strip()
    if ":" in t:
        company, role = t.split(":", 1)
        return company.strip(), role.strip()
    return "Unknown", t


def _entry_to_raw(entry: Any, category: str) -> Dict[str, Any]:
    raw_title = entry.get("title") or ""
    company, title = _parse_company_title(raw_title)
    summary_html = entry.get("summary") or entry.get("description") or ""
    description = _strip_html(summary_html)
    # Headquarters line often present
    hq = None
    m = re.search(r"Headquarters:\s*([^<\n]+)", summary_html, re.I)
    if m:
        hq = _strip_html(m.group(1))

    tags = []
    for tag in entry.get("tags") or []:
        if isinstance(tag, dict) and tag.get("term"):
            tags.append(tag["term"])
        elif isinstance(tag, str):
            tags.append(tag)

    skills_field = entry.get("skills")
    skills: List[str] = []
    if isinstance(skills_field, str) and skills_field.strip():
        # Often noisy SEO; keep short tokens only
        parts = re.split(r",| and ", skills_field)
        skills = [p.strip() for p in parts if 2 < len(p.strip()) < 40][:15]

    region = entry.get("region") or entry.get("country") or "Remote"
    link = entry.get("link") or entry.get("id") or ""

    return {
        "company": company,
        "title": title,
        "link": link,
        "description": description,
        "headquarters": hq,
        "region": region,
        "category": category,
        "tags": tags,
        "skills": skills,
        "published": entry.get("published"),
        "job_type": entry.get("type"),
    }


def fetch_wwr_jobs(
    *,
    categories: Optional[Sequence[str]] = None,
    keywords: Optional[Sequence[str]] = None,
    max_results: int = 40,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """
    Fetch and normalize jobs from WWR RSS categories.

    keywords: optional client-side filter (OR match against title+description).
    """
    cats = list(categories or DEFAULT_CATEGORIES)
    kw = [k.lower() for k in (keywords or []) if k]
    cache_key = f"wwr:{','.join(cats)}:kw={','.join(sorted(kw)[:8])}:n={max_results}"

    if use_cache:
        cached = get_cached_jobs(cache_key)
        if cached is not None:
            return cached[:max_results]

    raw_entries: List[Dict[str, Any]] = []
    for cat in cats:
        url = WWR_CATEGORIES.get(cat) or WWR_CATEGORIES["programming"]
        logger.info("[WWR] Fetching RSS category=%s", cat)
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries or []:
                raw_entries.append(_entry_to_raw(entry, cat))
        except Exception as e:
            logger.warning("[WWR] category %s failed: %s", cat, e)

    jobs: List[Dict[str, Any]] = []
    for raw in raw_entries:
        blob = f"{raw.get('title','')} {raw.get('description','')}".lower()
        if kw and not any(k in blob for k in kw):
            continue
        try:
            norm = normalize_wwr_job(raw)
            validated = validate_job_dict(norm)
            if validated:
                jobs.append(validated)
        except Exception as e:
            logger.debug("[WWR] normalize skip: %s", e)

    if use_cache and jobs:
        set_cached_jobs(cache_key, jobs)

    logger.info("[WWR] Returning %d jobs (from %d raw)", len(jobs[:max_results]), len(raw_entries))
    return jobs[:max_results]
