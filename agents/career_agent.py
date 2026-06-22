"""
Project Alpha-Nexus - Career Strategy Agent
Hyper-personalized job matching for Anmol Sharma (IIT Mandi, Data Science & AI).
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Set
import os
import yaml

from schemas import (
    AgentState,
    JobOpening,
    RemotePolicy,
    ExperienceLevel,
)

logger = logging.getLogger("alpha_nexus.agents.career")


# ══════════════════════════════════════════════════════════════════
# Personal Profile - Anmol Sharma
# ══════════════════════════════════════════════════════════════════

def load_user_profile():
    profile_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_profile.yaml")
    with open(profile_path, "r") as f:
        return yaml.safe_load(f)

USER_PROFILE = load_user_profile()


def normalize_location(location: str) -> str:
    """Normalize location string for comparison."""
    return location.lower().strip()


def is_location_match(job_location: str, remote_policy: str) -> bool:
    """Check if job location matches user preferences."""
    loc = normalize_location(job_location)
    policy = remote_policy.lower() if remote_policy else ""
    
    # Remote-friendly roles are always a match
    if policy in ("remote", "remote_friendly", "remote india"):
        return True
    
    # Check target cities
    for city in USER_PROFILE["target_cities"]:
        if city in loc:
            return True
    
    return False


def is_excluded(job: Dict[str, Any]) -> bool:
    """Check if job should be excluded based on hard filters (title only)."""
    title = (job.get("title") or "").lower()
    
    for excluded in USER_PROFILE["excluded_keywords"]:
        if excluded in title:
            return True
    
    return False


def calculate_skill_match(job: Dict[str, Any]) -> tuple[float, Set[str], Set[str]]:
    """Calculate skill match percentage and identify gaps."""
    user_skills = set(s.lower() for s in USER_PROFILE["skills"])
    
    job_tech = set(s.lower() for s in job.get("tech_stack", []))
    job_skills = set(s.lower() for s in job.get("skills_required", []))
    job_preferred = set(s.lower() for s in job.get("skills_preferred", []))
    
    all_job_skills = job_tech | job_skills | job_preferred
    if not all_job_skills:
        return 0.0, set(), set()
    
    matched = user_skills & all_job_skills
    missing = all_job_skills - user_skills
    
    match_pct = round(len(matched) / len(all_job_skills) * 100, 1)
    return match_pct, matched, missing


def calculate_comp_fit(job: Dict[str, Any]) -> tuple[str, bool]:
    """Calculate compensation fit — India-first (INR, LPA, Crores)."""
    payout_mid = job.get("payout_midpoint") or 0
    currency = job.get("currency", "INR").upper()
    
    # India-first: assume INR unless explicitly marked otherwise
    # Indian CTC typically 5L-3Cr range. USD roles would be marked currency="USD"
    if currency == "USD":
        payout_mid_inr = payout_mid * 83  # explicit USD conversion
    else:
        payout_mid_inr = payout_mid  # already INR
    
    meets_min = payout_mid_inr >= USER_PROFILE["min_base_salary_inr"]
    fit = "above" if meets_min else "below"
    return fit, meets_min


def calculate_experience_fit(job: Dict[str, Any]) -> str:
    """Calculate experience level fit."""
    exp_level = job.get("experience_level", "unknown").lower()
    exp_order = ["intern", "entry", "junior", "mid", "senior", "staff", "principal", "director", "vp", "c_level"]
    
    # User has ~2 years (internships + projects) -> entry/junior
    user_exp_idx = 2  # junior
    job_exp_idx = exp_order.index(exp_level) if exp_level in exp_order else 2
    
    diff = user_exp_idx - job_exp_idx
    if diff >= 2:
        return "overqualified"
    elif diff <= -2:
        return "stretch"
    elif diff == -1:
        return "stretch"
    elif diff == 1:
        return "match"
    else:
        return "match"


def calculate_overall_score(
    match_pct: float,
    comp_fit: str,
    remote_fit: bool,
    visa_fit: bool,
    exp_fit: str,
) -> float:
    """Calculate weighted overall score."""
    score = (
        match_pct * 0.35 +
        (100 if comp_fit == "above" else 40) * 0.20 +
        (100 if remote_fit else 30) * 0.15 +
        (100 if visa_fit else 0) * 0.10 +
        (100 if exp_fit == "match" else (70 if exp_fit == "stretch" else 40)) * 0.10 +
        (20 if USER_PROFILE["willing_to_relocate"] else 0) * 0.10
    )
    return round(score, 1)


def node_career_strategy(state: AgentState) -> AgentState:
    """
    Career Strategy Agent: Matches user profile against scraped roles
    to recommend high-yield job applications.
    Hyper-personalized for Anmol Sharma (IIT Mandi, Data Science & AI).
    """
    logger.info("[Career Strategy] Matching roles against Anmol Sharma's profile (IIT Mandi)...")
    state["current_agent"] = "career_strategy"
    state["updated_at"] = datetime.now()

    time.sleep(0.1)

    jobs = state.get("job_openings", [])
    if not jobs:
        logger.warning("[Career Strategy] No job openings to analyze")
        state["career_recommendations"] = [{"error": "No job openings available"}]
        return state

    recommendations = []

    for job in jobs:
        # Hard exclusions (Rust, C++, HFT)
        if is_excluded(job):
            logger.debug(f"[Career] Excluded: {job.get('title')} @ {job.get('company_name')}")
            continue

        # Location filter
        location = job.get("location_raw", "")
        remote_policy = job.get("remote_policy", "")
        if not is_location_match(location, remote_policy):
            logger.debug(f"[Career] Location mismatch: {job.get('title')} @ {job.get('company_name')} ({location})")
            continue

        # Skill match
        match_pct, matched, missing = calculate_skill_match(job)
        
        # Compensation fit
        comp_fit, meets_min = calculate_comp_fit(job)
        
        # Remote fit
        remote_fit = remote_policy in ("remote", "remote_friendly", "remote india")
        
        # Visa fit (Indian citizen, no visa needed)
        visa_fit = True  # Always true for India roles
        
        # Experience fit
        exp_fit = calculate_experience_fit(job)
        
        # Overall score
        score = calculate_overall_score(match_pct, comp_fit, remote_fit, visa_fit, exp_fit)
        
        # Priority
        if score >= 80:
            priority = "high"
        elif score >= 60:
            priority = "medium"
        else:
            priority = "low"
        
        # Build recommendation
        rec = {
            "job_id": job.get("job_id"),
            "company": job.get("company_name"),
            "title": job.get("title"),
            "title_normalized": job.get("title_normalized"),
            "location": f"{job.get('location_city', '')}, {job.get('location_state', '')}".strip(", "),
            "remote_policy": job.get("remote_policy"),
            "match_score": score,
            "skill_match_pct": match_pct,
            "matched_skills": sorted(list(matched)),
            "missing_skills": sorted(list(missing))[:8],
            "compensation": {
                "base_midpoint": job.get("payout_midpoint"),
                "total_estimate": job.get("total_comp_estimate"),
                "fit": comp_fit,
                "meets_minimum": meets_min,
                "currency": "INR",
                "display_lpa": round((job.get("payout_midpoint") or 0) / 100000, 1),
                "display_crores": round((job.get("payout_midpoint") or 0) / 10000000, 2),
            },
            "experience_fit": exp_fit,
            "remote_fit": remote_fit,
            "visa_fit": visa_fit,
            "application_url": job.get("application_url"),
            "source_url": job.get("source_url"),
            "reasoning": (
                f"Skill overlap: {match_pct}% ({', '.join(list(matched)[:5])}). "
                f"Compensation {comp_fit} minimum ({USER_PROFILE['min_base_salary_inr']/1e5:.0f} LPA). "
                f"Location: {'✓ Match' if remote_fit else 'Relocate: ' + location}. "
                f"Experience: {exp_fit}. "
                f"Gaps: {', '.join(list(missing)[:3])}."
            ),
            "priority": priority,
            "analyzed_at": datetime.now().isoformat(),
        }
        recommendations.append(rec)

    # Sort by score descending
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    state["career_recommendations"] = recommendations

    logger.info(f"[Career Strategy] Generated {len(recommendations)} personalized recommendations")
    for r in recommendations[:5]:
        logger.info(f"  -> {r['title']} @ {r['company']}: {r['match_score']} ({r['priority']}) [{r['location']}]")

    return state