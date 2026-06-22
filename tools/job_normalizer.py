"""
Disha - Job Normalizers
Transforms raw API responses into canonical JobOpening-compatible dicts.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from schemas import (
    ExperienceLevel,
    JobOpening,
    RemotePolicy,
    ScraperSource,
)

logger = logging.getLogger("disha.tools.normalizer")


# ──────────────────────────────────────────────────────────────
# India Defaults
# ──────────────────────────────────────────────────────────────

INDIA_COUNTRY = "IN"
INDIA_CURRENCY = "INR"
GREENHOUSE_DOMAIN = "boards.greenhouse.io"


# ──────────────────────────────────────────────────────────────
# Helper: Location Parsing
# ──────────────────────────────────────────────────────────────

_KNOWN_CITIES = {
    "bangalore", "bengaluru", "delhi", "gurgaon", "gurugram",
    "noida", "pune", "hyderabad", "chennai", "mumbai", "kolkata",
    "ahmedabad", "jaipur", "kochi", "coimbatore", "indore",
}

_KNOWN_STATES = {
    "karnataka", "delhi", "haryana", "uttar pradesh", "maharashtra",
    "telangana", "tamil nadu", "west bengal", "gujarat", "rajasthan",
    "kerala", "madhya pradesh",
}

_KNOWN_COUNTRIES = {
    "india", "united states", "united kingdom", "canada",
    "australia", "germany", "singapore", "uae", "italy",
    "ireland", "france", "netherlands", "spain", "japan",
    "china", "south korea", "brazil", "mexico",
}

_COUNTRY_ABBREVIATIONS = {
    "us": "united states",
    "usa": "united states",
    "uk": "united kingdom",
    "uae": "united arab emirates",
}

_COUNTRY_TO_ISO = {
    "india": "IN",
    "united states": "US",
    "united kingdom": "GB",
    "canada": "CA",
    "australia": "AU",
    "germany": "DE",
    "singapore": "SG",
    "uae": "AE",
    "united arab emirates": "AE",
    "italy": "IT",
    "ireland": "IE",
    "france": "FR",
    "netherlands": "NL",
    "spain": "ES",
    "japan": "JP",
    "china": "CN",
    "south korea": "KR",
    "brazil": "BR",
    "mexico": "MX",
}


def _resolve_country(location_raw: str, parsed_name: Optional[str]) -> Optional[str]:
    """Resolve country to ISO 3166-1 alpha-2 code."""
    text_lower = location_raw.lower()
    # Check parsed name first
    if parsed_name:
        iso = _COUNTRY_TO_ISO.get(parsed_name.lower())
        if iso:
            return iso
    # Fallback: search location text for full country names
    for name, iso in _COUNTRY_TO_ISO.items():
        if name in text_lower:
            return iso
    # Fallback: search location text for abbreviations (word-boundary matched)
    for abbr, full in _COUNTRY_ABBREVIATIONS.items():
        iso = _COUNTRY_TO_ISO.get(full)
        if iso and re.search(rf"\b{re.escape(abbr)}\b", text_lower):
            return iso
    return None


def parse_location(location_name: Optional[str]) -> Dict[str, Optional[str]]:
    """Parse a location string like 'Bangalore, India' into components."""
    result: Dict[str, Optional[str]] = {
        "city": None,
        "state": None,
        "country": None,
    }
    if not location_name:
        return result

    parts = [p.strip() for p in location_name.split(",")]
    lower_parts = [p.lower() for p in parts]

    for i, lp in enumerate(lower_parts):
        resolved = _COUNTRY_ABBREVIATIONS.get(lp, lp)
        if resolved in _KNOWN_COUNTRIES:
            result["country"] = parts[i]
        elif lp in _KNOWN_STATES:
            result["state"] = parts[i]
        elif lp in _KNOWN_CITIES:
            result["city"] = parts[i]

    return result


# ──────────────────────────────────────────────────────────────
# Helper: Seniority → ExperienceLevel
# ──────────────────────────────────────────────────────────────

_SENIORITY_MAP: List[tuple[re.Pattern, ExperienceLevel]] = [
    (re.compile(r"\bprincipal\b", re.I), ExperienceLevel.PRINCIPAL),
    (re.compile(r"\bstaff\b", re.I), ExperienceLevel.STAFF),
    (re.compile(r"\bsenior\b|\bsr\.?\b|\blead\b", re.I), ExperienceLevel.SENIOR),
    (re.compile(r"\bmid[\s-]?level\b", re.I), ExperienceLevel.MID),
    (re.compile(r"\bjunior\b|\bjr\.?\b", re.I), ExperienceLevel.JUNIOR),
    (re.compile(r"\bintern\b", re.I), ExperienceLevel.INTERN),
]


def infer_experience_level(title: str) -> ExperienceLevel:
    """Infer experience level from job title patterns."""
    for pattern, level in _SENIORITY_MAP:
        if pattern.search(title):
            return level
    return ExperienceLevel.UNKNOWN


# ──────────────────────────────────────────────────────────────
# Helper: Remote Policy Inference
# ──────────────────────────────────────────────────────────────

def infer_remote_policy(location_name: Optional[str], title: str) -> RemotePolicy:
    """Infer remote policy from location and title."""
    text = f"{location_name or ''} {title}".lower()
    if re.search(r"\bremote\b", text):
        return RemotePolicy.REMOTE
    if re.search(r"\bhybrid\b", text):
        return RemotePolicy.HYBRID
    return RemotePolicy.UNKNOWN


# ──────────────────────────────────────────────────────────────
# Helper: Strip HTML Tags
# ──────────────────────────────────────────────────────────────

def strip_html(html: str) -> str:
    """Strip HTML tags, keeping text content."""
    clean = re.sub(r"<[^>]+>", " ", html)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


# ──────────────────────────────────────────────────────────────
# Greenhouse Normalizer
# ──────────────────────────────────────────────────────────────


def normalize_greenhouse_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a RawGreenhouseJob dict into a JobOpening-compatible dict.

    Sets India defaults (currency INR, country IN). Location is parsed
    from Greenhouse's structured location field. Tech stack and skills
    are left empty — they require LLM enrichment from the description.
    """
    title = raw.get("title", "").strip()
    location_raw = ""
    if raw.get("location") and isinstance(raw["location"], dict):
        location_raw = raw["location"].get("name", "")
    elif raw.get("offices"):
        offices = raw["offices"]
        if offices and isinstance(offices[0], dict):
            location_raw = offices[0].get("location", {}).get("name", "")

    location_components = parse_location(location_raw)
    description_html = raw.get("content", "")
    description_text = strip_html(description_html)

    department = ""
    if raw.get("departments"):
        dept = raw["departments"][0]
        if isinstance(dept, dict):
            department = dept.get("name", "")

    absolute_url = raw.get("absolute_url", "") or ""
    experience = infer_experience_level(title)
    remote = infer_remote_policy(location_raw, title)

    country_code = _resolve_country(location_raw, location_components.get("country"))

    job_dict: Dict[str, Any] = {
        "company_name": "",  # overwritten by caller with actual company name
        "title": title,
        "location_raw": location_raw,
        "location_city": location_components.get("city"),
        "location_state": location_components.get("state"),
        "location_country": country_code,
        "remote_policy": remote.value,
        "experience_level": experience.value,
        "department": department or None,
        "tech_stack": [],
        "skills_required": [],
        "skills_preferred": [],
        "payout_min": None,
        "payout_max": None,
        "currency": INDIA_CURRENCY if country_code == INDIA_COUNTRY else "USD",
        "compensation_source": "estimated",
        "compensation_confidence": 0.3,
        "description_raw": description_text if description_text else title,
        "source_url": absolute_url,
        "source_domain": GREENHOUSE_DOMAIN,
        "scraper_source": ScraperSource.ATS_GREENHOUSE.value,
        "posted_date": None,
        "is_active": True,
        "application_url": absolute_url or None,
    }

    return job_dict


# ──────────────────────────────────────────────────────────────
# Lever Normalizer
# ──────────────────────────────────────────────────────────────


LEVER_DOMAIN = "jobs.lever.co"


def normalize_lever_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a RawLeverJob dict into a JobOpening-compatible dict.

    Lever listing pages include title, location, department, and URL but
    not the full description. Description enrichment requires fetching
    each job's detail page.
    """
    title = raw.get("title", "").strip()
    location_raw = raw.get("location", "") or ""
    department = raw.get("department", "") or ""
    absolute_url = raw.get("absolute_url", "") or ""

    location_components = parse_location(location_raw)
    experience = infer_experience_level(title)
    remote = infer_remote_policy(location_raw, title)
    country_code = _resolve_country(location_raw, location_components.get("country"))

    job_dict: Dict[str, Any] = {
        "company_name": "",
        "title": title,
        "location_raw": location_raw,
        "location_city": location_components.get("city"),
        "location_state": location_components.get("state"),
        "location_country": country_code,
        "remote_policy": remote.value,
        "experience_level": experience.value,
        "department": department or None,
        "tech_stack": [],
        "skills_required": [],
        "skills_preferred": [],
        "payout_min": None,
        "payout_max": None,
        "currency": INDIA_CURRENCY if country_code == INDIA_COUNTRY else "USD",
        "compensation_source": "estimated",
        "compensation_confidence": 0.2,
        "description_raw": title,
        "source_url": absolute_url,
        "source_domain": LEVER_DOMAIN,
        "scraper_source": ScraperSource.ATS_LEVER.value,
        "posted_date": None,
        "is_active": True,
        "application_url": absolute_url or None,
    }

    return job_dict


# ──────────────────────────────────────────────────────────────
# Validation Helper
# ──────────────────────────────────────────────────────────────


def validate_job_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a normalizer output dict against the JobOpening schema.
    Returns the serialized dict on success, logs and returns None on failure."""
    try:
        job = JobOpening.model_validate(data)
        return job.model_dump(mode="json")
    except Exception as e:
        logger.error(f"JobOpening validation failed: {e}")
        logger.debug(f"Failed data: {data}")
        return None
