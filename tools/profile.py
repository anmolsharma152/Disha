"""
Disha - User preference / profile resolution.

Profiles are optional request-time inputs. Defaults are generic product
settings (not a single person's resume). Empty skills/cities/salary mean
"no hard preference" rather than a fake zero match.
"""

from __future__ import annotations

import copy
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

import yaml

logger = logging.getLogger("disha.tools.profile")

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PATH = _ROOT / "profiles" / "default.yaml"

_PROFILE_CACHE: Optional[Dict[str, Any]] = None


def _empty_profile() -> Dict[str, Any]:
    return {
        "display_name": None,
        "name": None,  # alias accepted from older callers
        "skills": [],
        "target_cities": [],
        "target_roles": [],
        "experience_years": None,
        "min_base_salary_inr": None,
        "prefer_remote": True,
        "willing_to_relocate": True,
        "excluded_keywords": [],
        "excluded_domains": [],
    }


def _coerce_profile(raw: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    base = _empty_profile()
    if not raw:
        return base
    data = dict(raw)
    # Normalize name aliases
    if data.get("display_name") is None and data.get("name"):
        data["display_name"] = data.get("name")
    for key, default in base.items():
        if key not in data or data[key] is None:
            if key in ("skills", "target_cities", "target_roles", "excluded_keywords", "excluded_domains"):
                data[key] = list(default) if isinstance(default, list) else default
            elif key not in data:
                data[key] = default
    # Ensure list fields are lists
    for list_key in (
        "skills",
        "target_cities",
        "target_roles",
        "excluded_keywords",
        "excluded_domains",
    ):
        val = data.get(list_key)
        if val is None:
            data[list_key] = []
        elif not isinstance(val, list):
            data[list_key] = [val]
    return data


def load_default_profile(path: Optional[str] = None) -> Dict[str, Any]:
    """Load product default preferences from YAML (cached)."""
    global _PROFILE_CACHE
    if path is None and _PROFILE_CACHE is not None:
        return copy.deepcopy(_PROFILE_CACHE)

    env_path = os.environ.get("DISHA_PROFILE_PATH")
    candidates: List[Path] = []
    if path:
        candidates.append(Path(path))
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(_DEFAULT_PATH)

    loaded: Dict[str, Any] = _empty_profile()
    for p in candidates:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
                loaded = _coerce_profile(raw)
                logger.debug("[Profile] Loaded defaults from %s", p)
                break
            except Exception as e:
                logger.warning("[Profile] Failed to load %s: %s", p, e)
    else:
        logger.info("[Profile] Using built-in empty defaults")

    if path is None:
        _PROFILE_CACHE = copy.deepcopy(loaded)
    return copy.deepcopy(loaded)


def merge_preferences(
    base: Mapping[str, Any],
    override: Optional[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Shallow-merge override onto base; lists/scalars from override win when set."""
    out = _coerce_profile(base)
    if not override:
        return out
    for key, value in override.items():
        if value is None:
            continue
        if isinstance(value, list) and len(value) == 0 and key in out:
            # Explicit empty list clears the preference
            out[key] = []
            continue
        out[key] = value
    return _coerce_profile(out)


def resolve_profile(state: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """
    Resolve effective profile for this run.

    Priority: state["user_profile"] (request override) > defaults.
    """
    defaults = load_default_profile()
    if not state:
        return defaults
    override = state.get("user_profile") if isinstance(state, Mapping) else None
    if not override:
        return defaults
    return merge_preferences(defaults, override)


def profile_label(profile: Mapping[str, Any]) -> str:
    """Human-readable label for logs (never requires a real name)."""
    name = profile.get("display_name") or profile.get("name")
    if name:
        return str(name)
    n_skills = len(profile.get("skills") or [])
    if n_skills:
        return f"custom preferences ({n_skills} skills)"
    return "default preferences (no personal profile)"


def has_skill_preferences(profile: Mapping[str, Any]) -> bool:
    return bool(profile.get("skills"))


def has_location_preferences(profile: Mapping[str, Any]) -> bool:
    return bool(profile.get("target_cities"))


def has_salary_floor(profile: Mapping[str, Any]) -> bool:
    v = profile.get("min_base_salary_inr")
    return v is not None and int(v) > 0
