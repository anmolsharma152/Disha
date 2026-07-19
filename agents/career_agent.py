"""
Disha - Career Strategy Agent

Ranks jobs like a job board: title/role relevance first, then skills,
location, and experience — and drops obvious non-tech noise for tech seekers.
"""

from __future__ import annotations

import logging
import re
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
from tools.skill_lexicon import (
    extract_skills_from_text,
    is_likely_non_tech_title,
    is_likely_tech_title,
    title_tokens,
)

logger = logging.getLogger("disha.agents.career")


def normalize_location(location: str) -> str:
    return (location or "").lower().strip()


def is_location_match(
    job_location: str,
    remote_policy: str,
    profile: Mapping[str, Any],
) -> bool:
    if not has_location_preferences(profile):
        return True
    loc = normalize_location(job_location)
    policy = (remote_policy or "").lower()
    if policy in ("remote", "remote_friendly", "remote india"):
        return True
    for city in profile.get("target_cities") or []:
        if city and city.lower() in loc:
            return True
    # India-wide profile cities shouldn't kill remote-global if "remote" listed
    if any(c.lower() == "remote" for c in (profile.get("target_cities") or [])):
        if "remote" in loc:
            return True
    return False


def is_excluded(job: Dict[str, Any], profile: Mapping[str, Any], query: str) -> bool:
    title = (job.get("title") or "").lower()
    q = (query or "").lower()

    for excluded in profile.get("excluded_keywords") or []:
        if excluded and excluded.lower() in title:
            return True

    # Drop non-tech noise unless the user explicitly searches for it
    sales_intent = any(
        w in q for w in ("sales", "account executive", "recruiter", "marketing", "hr ")
    )
    if not sales_intent and is_likely_non_tech_title(title):
        return True

    # If seeker has tech target roles / skills, require tech-ish titles
    tech_seeker = bool(profile.get("skills")) or any(
        any(
            k in str(r).lower()
            for k in ("engineer", "developer", "ml", "ai", "data", "software", "sde")
        )
        for r in (profile.get("target_roles") or [])
    )
    if tech_seeker and not sales_intent and not is_likely_tech_title(title):
        # Allow if strong skill overlap later — but default drop pure non-tech
        return True

    return False


def _job_skill_set(job: Dict[str, Any]) -> Set[str]:
    skills: Set[str] = set()
    for key in ("tech_stack", "skills_required", "skills_preferred"):
        for s in job.get(key) or []:
            if s:
                skills.add(str(s).lower())
    # Fallback: mine description if still empty
    if not skills:
        blob = f"{job.get('title') or ''}\n{job.get('description_raw') or ''}"
        for s in extract_skills_from_text(blob, limit=30):
            skills.add(s.lower())
            # also write back for UI
        if skills:
            labels = extract_skills_from_text(blob, limit=30)
            job["tech_stack"] = labels
            job["skills_required"] = labels
    return skills


def calculate_skill_match(
    job: Dict[str, Any],
    profile: Mapping[str, Any],
) -> tuple[float, Set[str], Set[str], str]:
    user_skills = {s.lower() for s in (profile.get("skills") or []) if s}
    all_job_skills = _job_skill_set(job)

    if not user_skills and not all_job_skills:
        return 0.0, set(), set(), "unknown"
    if not user_skills:
        return 0.0, set(), set(all_job_skills), "no_user_skills"
    if not all_job_skills:
        # Still try title token overlap with user skills
        title = (job.get("title") or "").lower()
        matched = {s for s in user_skills if s in title or any(t in s for t in title.split())}
        if matched:
            return 25.0, matched, set(), "title_only"
        return 0.0, set(), set(), "no_job_skills"

    matched = user_skills & all_job_skills
    # Partial: user skill contained in job skill string or vice versa
    if not matched:
        for us in user_skills:
            for js in all_job_skills:
                if us in js or js in us:
                    matched.add(us)
    missing = all_job_skills - matched
    # Score relative to user skills coverage of job (job board style)
    # + how many of user's top skills appear
    if not all_job_skills:
        match_pct = 0.0
    else:
        coverage = len(matched) / max(len(all_job_skills), 1)
        user_hit = len(matched) / max(len(user_skills), 1)
        match_pct = round(100.0 * (0.65 * coverage + 0.35 * min(user_hit * 3, 1.0)), 1)
    return match_pct, matched, missing, "matched" if matched else "no_overlap"


def calculate_title_relevance(
    job: Dict[str, Any],
    profile: Mapping[str, Any],
    query: str,
) -> float:
    """0-100: how well title matches query + target roles (what Naukri does well)."""
    title = (job.get("title") or "").lower()
    if not title:
        return 0.0

    score = 0.0
    q_tokens = title_tokens(query)
    t_tokens = title_tokens(title)

    if q_tokens and t_tokens:
        overlap = q_tokens & t_tokens
        score += 55.0 * (len(overlap) / max(len(q_tokens), 1))
        # Bonus for multi-token hits
        if len(overlap) >= 2:
            score += 10.0

    # Target role phrases
    roles = [str(r).lower() for r in (profile.get("target_roles") or []) if r]
    best_role = 0.0
    for role in roles:
        r_toks = title_tokens(role)
        if not r_toks:
            continue
        ov = r_toks & t_tokens
        best_role = max(best_role, 40.0 * (len(ov) / max(len(r_toks), 1)))
        if role in title:
            best_role = max(best_role, 45.0)
    score += best_role

    # Generic tech title floor
    if is_likely_tech_title(title):
        score += 8.0
    if is_likely_non_tech_title(title):
        score -= 40.0

    return max(0.0, min(100.0, round(score, 1)))


def calculate_location_score(
    job: Dict[str, Any],
    profile: Mapping[str, Any],
) -> float:
    loc = normalize_location(
        f"{job.get('location_raw') or ''} {job.get('location_city') or ''} "
        f"{job.get('location_country') or ''}"
    )
    policy = (job.get("remote_policy") or "").lower()
    cities = [c.lower() for c in (profile.get("target_cities") or []) if c]

    if not cities:
        # Mild preference for India / remote when no prefs
        if job.get("location_country") in ("IN", "India") or "india" in loc:
            return 70.0
        if policy in ("remote", "remote_friendly"):
            return 65.0
        return 50.0

    if any(c in loc for c in cities):
        return 100.0
    if policy in ("remote", "remote_friendly") and (
        "remote" in cities or profile.get("prefer_remote")
    ):
        return 85.0
    if job.get("location_country") in ("IN", "India") or "india" in loc:
        if any(
            c in {"bangalore", "bengaluru", "delhi", "pune", "hyderabad", "mumbai", "jaipur", "india"}
            for c in cities
        ):
            return 75.0
    # Harsh penalty for US/EU-only when user is India-based
    us_eu = any(
        x in loc
        for x in (
            "united states", " usa", "san francisco", "new york", "seattle",
            "london", "denmark", "sweden", "netherlands", "germany",
        )
    )
    if us_eu and any(
        c in {"jaipur", "bangalore", "bengaluru", "delhi", "pune", "india", "hyderabad", "mumbai"}
        for c in cities
    ):
        return 15.0
    return 35.0


def calculate_comp_fit(
    job: Dict[str, Any],
    profile: Mapping[str, Any],
) -> tuple[str, Optional[bool]]:
    payout_mid = job.get("payout_midpoint") or 0
    currency = (job.get("currency") or "INR").upper()
    if not payout_mid:
        return "unavailable", None
    payout_mid_inr = payout_mid * 83 if currency == "USD" else payout_mid
    if not has_salary_floor(profile):
        return "unavailable", None
    floor = int(profile["min_base_salary_inr"])
    meets = payout_mid_inr >= floor
    return ("above" if meets else "below"), meets


def _experience_index(years: Optional[float]) -> int:
    if years is None:
        return 2
    if years < 1:
        return 1
    if years < 3:
        return 2
    if years < 6:
        return 3
    if years < 10:
        return 4
    return 5


def calculate_experience_fit(job: Dict[str, Any], profile: Mapping[str, Any]) -> str:
    exp_level = (job.get("experience_level") or "unknown").lower()
    exp_order = [
        "intern", "entry", "junior", "mid", "senior", "staff",
        "principal", "director", "vp", "c_level",
    ]
    years = profile.get("experience_years")
    if exp_level == "unknown" or years is None:
        # Infer from title keywords vs years
        title = (job.get("title") or "").lower()
        if years is not None:
            if years < 2 and any(w in title for w in ("staff", "principal", "director", "head of", "senior manager")):
                return "stretch"
            if years < 3 and "senior" in title and "junior" not in title:
                return "stretch"
            if years >= 1 and any(w in title for w in ("intern",)):
                return "overqualified"
        return "unknown"

    user_exp_idx = _experience_index(float(years))
    job_exp_idx = exp_order.index(exp_level) if exp_level in exp_order else 2
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
    title_score: float,
    skill_pct: float,
    skill_status: str,
    location_score: float,
    exp_fit: str,
    comp_fit: str,
) -> float:
    """
    Job-board style weights:
      title/role  40%
      skills      35%
      location    15%
      experience  10%
    Comp is informational only unless floor is set (small nudge).
    """
    if skill_status in ("no_user_skills", "unknown"):
        skill_component = 20.0
    elif skill_status in ("no_job_skills", "title_only"):
        skill_component = max(skill_pct, 15.0)
    elif skill_status == "no_overlap":
        skill_component = 5.0
    else:
        skill_component = skill_pct

    if exp_fit == "match":
        exp_component = 100.0
    elif exp_fit == "stretch":
        exp_component = 55.0
    elif exp_fit == "overqualified":
        exp_component = 40.0
    else:
        exp_component = 60.0

    score = (
        title_score * 0.40
        + skill_component * 0.35
        + location_score * 0.15
        + exp_component * 0.10
    )
    if comp_fit == "below":
        score -= 5.0
    elif comp_fit == "above":
        score += 3.0

    # Hard floor: weak title match cannot rank high even with random skill hits
    if title_score < 20:
        score = min(score, 45.0)

    return round(max(0.0, min(100.0, score)), 1)


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
    profile = resolve_profile(state)
    label = profile_label(profile)
    query = state.get("user_query") or ""
    logger.info("[Career Strategy] Ranking with %s", label)
    state["current_agent"] = "career_strategy"
    state["updated_at"] = datetime.now()
    state["user_profile"] = profile

    time.sleep(0.02)

    jobs = state.get("job_openings") or []
    if not jobs:
        logger.warning("[Career Strategy] No job openings to analyze")
        state["career_recommendations"] = []
        return state

    recommendations: List[Dict[str, Any]] = []
    dropped = 0

    for job in jobs:
        if is_excluded(job, profile, query):
            dropped += 1
            continue
        if not is_location_match(
            job.get("location_raw", "") or "",
            job.get("remote_policy", "") or "",
            profile,
        ):
            # Soft: keep but will score low on location — only hard-drop if cities set and remote not ok
            if has_location_preferences(profile) and (job.get("remote_policy") or "") not in (
                "remote",
                "remote_friendly",
            ):
                # still allow India remote-ish; if truly mismatched, skip
                loc_score_pre = calculate_location_score(job, profile)
                if loc_score_pre < 20:
                    dropped += 1
                    continue

        title_score = calculate_title_relevance(job, profile, query)
        skill_pct, matched, missing, skill_status = calculate_skill_match(job, profile)
        loc_score = calculate_location_score(job, profile)
        exp_fit = calculate_experience_fit(job, profile)
        comp_fit, meets_min = calculate_comp_fit(job, profile)
        score = calculate_overall_score(
            title_score, skill_pct, skill_status, loc_score, exp_fit, comp_fit
        )

        # Drop junk that still slipped through with terrible dual scores
        # Keep clear tech titles even when the query is vague / no skills yet
        if title_score < 12 and skill_pct < 15 and not is_likely_tech_title(
            job.get("title") or ""
        ):
            dropped += 1
            continue

        if score >= 75:
            priority = "high"
        elif score >= 55:
            priority = "medium"
        else:
            priority = "low"

        remote_policy = job.get("remote_policy") or "unknown"
        remote_fit = remote_policy in ("remote", "remote_friendly", "remote india")

        rec = {
            "job_id": job.get("job_id"),
            "company": job.get("company_name"),
            "title": job.get("title"),
            "title_normalized": job.get("title_normalized"),
            "location": _format_location(job),
            "remote_policy": remote_policy,
            "match_score": score,
            "title_relevance": title_score,
            "skill_match_pct": skill_pct,
            "skill_match_status": skill_status,
            "location_score": loc_score,
            "matched_skills": sorted(matched)[:12],
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
                f"Title fit {title_score:.0f}/100. "
                f"Skills {skill_pct:.0f}% ({', '.join(list(matched)[:4]) or 'few overlaps'}). "
                f"Location score {loc_score:.0f}. Experience: {exp_fit}."
            ),
            "priority": priority,
            "analyzed_at": datetime.now().isoformat(),
            "profile_label": label,
        }
        recommendations.append(rec)

    recommendations.sort(
        key=lambda x: (x["match_score"], x.get("title_relevance", 0)),
        reverse=True,
    )
    # Keep top N for UI clarity
    recommendations = recommendations[:25]
    state["career_recommendations"] = recommendations

    logger.info(
        "[Career Strategy] %d recommendations (%d dropped) via %s",
        len(recommendations),
        dropped,
        label,
    )
    for r in recommendations[:5]:
        logger.info(
            "  -> [%s] %s @ %s score=%s title=%s skills=%s",
            r["priority"],
            r["title"],
            r["company"],
            r["match_score"],
            r.get("title_relevance"),
            r["skill_match_pct"],
        )
    return state
