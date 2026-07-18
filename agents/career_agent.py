"""
Disha - Career Strategy Agent
Scores jobs against request-time preferences (optional). No personal dossier.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Set

from schemas import AgentState
from tools.profile import (
    has_location_preferences,
    has_salary_floor,
    has_skill_preferences,
    profile_label,
    resolve_profile,
)

logger = logging.getLogger("disha.agents.career")


def normalize_location(location: str) -> str:
    return (location or "").lower().strip()


def is_location_match(
    job_location: str,
    remote_policy: str,
    profile: Mapping[str, Any],
) -> bool:
    """If no target cities configured, do not hard-filter by location."""
    if not has_location_preferences(profile):
        return True

    loc = normalize_location(job_location)
    policy = (remote_policy or "").lower()

    if policy in ("remote", "remote_friendly", "remote india"):
        return True

    for city in profile.get("target_cities") or []:
        if city and city.lower() in loc:
            return True
    return False


def is_excluded(job: Dict[str, Any], profile: Mapping[str, Any]) -> bool:
    """Optional profile keyword exclusions (title only). Guardrail handles product defaults."""
    title = (job.get("title") or "").lower()
    for excluded in profile.get("excluded_keywords") or []:
        if excluded and excluded.lower() in title:
            return True
    return False


def calculate_skill_match(
    job: Dict[str, Any],
    profile: Mapping[str, Any],
) -> tuple[float, Set[str], Set[str], str]:
    """
    Returns (match_pct, matched, missing, status).

    status: "matched" | "no_user_skills" | "no_job_skills" | "unknown"
    Without user skills we do not invent a 0% match against the job.
    """
    user_skills = {s.lower() for s in (profile.get("skills") or []) if s}

    job_tech = {s.lower() for s in (job.get("tech_stack") or []) if s}
    job_skills = {s.lower() for s in (job.get("skills_required") or []) if s}
    job_preferred = {s.lower() for s in (job.get("skills_preferred") or []) if s}
    all_job_skills = job_tech | job_skills | job_preferred

    if not user_skills and not all_job_skills:
        return 50.0, set(), set(), "unknown"
    if not user_skills:
        # Prefer jobs that at least declare a stack (slight boost via neutral band)
        return 50.0, set(), set(all_job_skills), "no_user_skills"
    if not all_job_skills:
        return 50.0, set(), set(), "no_job_skills"

    matched = user_skills & all_job_skills
    missing = all_job_skills - user_skills
    match_pct = round(len(matched) / len(all_job_skills) * 100, 1)
    return match_pct, matched, missing, "matched"


def calculate_comp_fit(
    job: Dict[str, Any],
    profile: Mapping[str, Any],
) -> tuple[str, Optional[bool]]:
    """
    Returns (fit, meets_min).
    fit: above | below | unavailable
    meets_min: True/False/None when unknown
    """
    payout_mid = job.get("payout_midpoint") or 0
    currency = (job.get("currency") or "INR").upper()

    if not payout_mid:
        return "unavailable", None

    if currency == "USD":
        payout_mid_inr = payout_mid * 83
    else:
        payout_mid_inr = payout_mid

    if not has_salary_floor(profile):
        return "unavailable", None

    floor = int(profile["min_base_salary_inr"])
    meets_min = payout_mid_inr >= floor
    return ("above" if meets_min else "below"), meets_min


def _experience_index(years: Optional[float]) -> int:
    """Map years of experience to coarse level index."""
    if years is None:
        return 2  # mid default only used when comparing unknowns carefully
    if years < 1:
        return 1  # entry
    if years < 3:
        return 2  # junior
    if years < 6:
        return 3  # mid
    if years < 10:
        return 4  # senior
    return 5  # staff+


def calculate_experience_fit(job: Dict[str, Any], profile: Mapping[str, Any]) -> str:
    exp_level = (job.get("experience_level") or "unknown").lower()
    exp_order = [
        "intern",
        "entry",
        "junior",
        "mid",
        "senior",
        "staff",
        "principal",
        "director",
        "vp",
        "c_level",
    ]
    if exp_level == "unknown" or profile.get("experience_years") is None:
        return "unknown"

    user_exp_idx = _experience_index(profile.get("experience_years"))
    job_exp_idx = exp_order.index(exp_level) if exp_level in exp_order else 2
    # Align junior-ish index onto exp_order: intern=0 entry=1 junior=2 mid=3...
    # _experience_index returns 1=entry-ish ... map to exp_order roughly
    user_on_order = min(user_exp_idx, len(exp_order) - 1)

    diff = user_on_order - job_exp_idx
    if diff >= 2:
        return "overqualified"
    if diff <= -2:
        return "stretch"
    if diff == -1:
        return "stretch"
    return "match"


def calculate_overall_score(
    match_pct: float,
    skill_status: str,
    comp_fit: str,
    remote_fit: bool,
    exp_fit: str,
    prefer_remote: bool,
    willing_to_relocate: bool,
) -> float:
    """Weighted score that stays neutral when preferences are unset."""
    if skill_status in ("no_user_skills", "no_job_skills", "unknown"):
        skill_component = 50.0
    else:
        skill_component = match_pct

    if comp_fit == "above":
        comp_component = 100.0
    elif comp_fit == "below":
        comp_component = 40.0
    else:
        comp_component = 55.0  # unavailable / no floor set

    if prefer_remote:
        remote_component = 100.0 if remote_fit else 40.0
    else:
        remote_component = 70.0

    if exp_fit == "match":
        exp_component = 100.0
    elif exp_fit == "stretch":
        exp_component = 70.0
    elif exp_fit == "overqualified":
        exp_component = 50.0
    else:
        exp_component = 60.0  # unknown

    relocate_component = 60.0 if willing_to_relocate else 40.0

    score = (
        skill_component * 0.40
        + comp_component * 0.20
        + remote_component * 0.15
        + exp_component * 0.15
        + relocate_component * 0.10
    )
    return round(score, 1)


def _format_location(job: Dict[str, Any]) -> str:
    parts = [
        p
        for p in (
            job.get("location_city"),
            job.get("location_state"),
            job.get("location_country"),
        )
        if p and str(p).lower() not in ("none", "null", "unknown")
    ]
    if parts:
        return ", ".join(str(p) for p in parts)
    raw = job.get("location_raw") or ""
    return raw if raw and str(raw).lower() != "none" else "Location not specified"


def node_career_strategy(state: AgentState) -> AgentState:
    """
    Rank job openings using optional request-time preferences.
    Without a personal skill/salary profile, ranks with neutral skill/comp bands
    and optional soft signals (remote, experience labels).
    """
    profile = resolve_profile(state)
    label = profile_label(profile)
    logger.info("[Career Strategy] Scoring jobs with %s", label)
    state["current_agent"] = "career_strategy"
    state["updated_at"] = datetime.now()
    state["user_profile"] = profile  # echo resolved prefs for downstream agents

    time.sleep(0.05)

    jobs = state.get("job_openings") or []
    if not jobs:
        logger.warning("[Career Strategy] No job openings to analyze")
        state["career_recommendations"] = []
        return state

    recommendations: List[Dict[str, Any]] = []
    prefer_remote = bool(profile.get("prefer_remote", True))
    willing = bool(profile.get("willing_to_relocate", True))

    for job in jobs:
        if is_excluded(job, profile):
            continue

        location = job.get("location_raw", "") or ""
        remote_policy = job.get("remote_policy", "") or ""
        if not is_location_match(location, remote_policy, profile):
            continue

        match_pct, matched, missing, skill_status = calculate_skill_match(job, profile)
        comp_fit, meets_min = calculate_comp_fit(job, profile)
        remote_fit = remote_policy in ("remote", "remote_friendly", "remote india")
        exp_fit = calculate_experience_fit(job, profile)
        score = calculate_overall_score(
            match_pct,
            skill_status,
            comp_fit,
            remote_fit,
            exp_fit,
            prefer_remote=prefer_remote,
            willing_to_relocate=willing,
        )

        if score >= 80:
            priority = "high"
        elif score >= 60:
            priority = "medium"
        else:
            priority = "low"

        floor = profile.get("min_base_salary_inr")
        if comp_fit == "unavailable":
            comp_reason = "Compensation not posted or no salary floor set"
        elif floor:
            comp_reason = (
                f"Compensation {comp_fit} floor "
                f"({int(floor) / 1e5:.0f} LPA)"
            )
        else:
            comp_reason = f"Compensation {comp_fit}"

        if skill_status == "no_user_skills":
            skill_reason = "No candidate skills provided — skill match neutral"
        elif skill_status == "no_job_skills":
            skill_reason = "Job listing has no structured skills — skill match neutral"
        else:
            skill_reason = (
                f"Skill overlap: {match_pct}% "
                f"({', '.join(list(matched)[:5]) or 'none'})"
            )

        rec = {
            "job_id": job.get("job_id"),
            "company": job.get("company_name"),
            "title": job.get("title"),
            "title_normalized": job.get("title_normalized"),
            "location": _format_location(job),
            "remote_policy": job.get("remote_policy"),
            "match_score": score,
            "skill_match_pct": match_pct,
            "skill_match_status": skill_status,
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing)[:8],
            "compensation": {
                "base_midpoint": job.get("payout_midpoint"),
                "total_estimate": job.get("total_comp_estimate"),
                "fit": comp_fit,
                "meets_minimum": meets_min,
                "currency": job.get("currency") or "INR",
                "display_lpa": round((job.get("payout_midpoint") or 0) / 100000, 1)
                if job.get("payout_midpoint")
                else None,
                "display_crores": round((job.get("payout_midpoint") or 0) / 10000000, 2)
                if job.get("payout_midpoint")
                else None,
            },
            "experience_fit": exp_fit,
            "remote_fit": remote_fit,
            "application_url": job.get("application_url"),
            "source_url": job.get("source_url"),
            "reasoning": (
                f"{skill_reason}. {comp_reason}. "
                f"Remote: {'yes' if remote_fit else 'no'}. "
                f"Experience: {exp_fit}."
            ),
            "priority": priority,
            "analyzed_at": datetime.now().isoformat(),
            "profile_label": label,
        }
        recommendations.append(rec)

    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    state["career_recommendations"] = recommendations

    logger.info(
        "[Career Strategy] Generated %d recommendations (%s)",
        len(recommendations),
        label,
    )
    for r in recommendations[:5]:
        logger.info(
            "  -> %s @ %s: %s (%s) [%s]",
            r["title"],
            r["company"],
            r["match_score"],
            r["priority"],
            r["location"],
        )
    return state
