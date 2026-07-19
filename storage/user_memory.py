"""
Single-user memory store (file-backed JSON).

v1: one active user ("default"). Resume-derived preferences live here
and feed profile resolution without hardcoding a personal dossier in code.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("disha.storage.user_memory")

_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DIR = _ROOT / "data"
_LOCK = threading.Lock()

DEFAULT_USER_ID = "default"


def _memory_path(user_id: str = DEFAULT_USER_ID) -> Path:
    base = Path(os.environ.get("DISHA_DATA_DIR", str(_DEFAULT_DIR)))
    base.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (user_id or DEFAULT_USER_ID))
    return base / f"user_memory_{safe}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_memory(user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    return {
        "user_id": user_id or DEFAULT_USER_ID,
        "profile": {},
        "resume": None,
        "source": None,
        "updated_at": None,
        "created_at": None,
    }


def load_memory(user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    path = _memory_path(user_id)
    if not path.is_file():
        return empty_memory(user_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return empty_memory(user_id)
        data.setdefault("user_id", user_id)
        data.setdefault("profile", {})
        data.setdefault("resume", None)
        return data
    except Exception as e:
        logger.warning("[Memory] Failed to load %s: %s", path, e)
        return empty_memory(user_id)


def save_memory(memory: Dict[str, Any], user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    path = _memory_path(user_id)
    payload = dict(memory)
    payload["user_id"] = user_id or DEFAULT_USER_ID
    payload["updated_at"] = _now_iso()
    if not payload.get("created_at"):
        payload["created_at"] = payload["updated_at"]
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
    logger.info("[Memory] Saved profile for user=%s path=%s", user_id, path)
    return payload


def clear_memory(user_id: str = DEFAULT_USER_ID) -> bool:
    path = _memory_path(user_id)
    with _LOCK:
        if path.is_file():
            path.unlink()
            logger.info("[Memory] Cleared user=%s", user_id)
            return True
    return False


def get_profile(user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    mem = load_memory(user_id)
    profile = mem.get("profile") or {}
    return profile if isinstance(profile, dict) else {}


def upsert_profile_from_resume(
    *,
    profile: Dict[str, Any],
    filename: str,
    text_preview: str,
    char_count: int,
    user_id: str = DEFAULT_USER_ID,
    extraction_method: str = "llm",
) -> Dict[str, Any]:
    mem = load_memory(user_id)
    if not mem.get("created_at"):
        mem["created_at"] = _now_iso()
    mem["profile"] = profile
    mem["source"] = "resume_upload"
    mem["resume"] = {
        "filename": filename,
        "uploaded_at": _now_iso(),
        "char_count": char_count,
        "text_preview": (text_preview or "")[:500],
        "extraction_method": extraction_method,
    }
    return save_memory(mem, user_id=user_id)


def memory_public_view(user_id: str = DEFAULT_USER_ID) -> Dict[str, Any]:
    """Safe payload for API/UI (no full resume text)."""
    mem = load_memory(user_id)
    profile = mem.get("profile") or {}
    resume = mem.get("resume") or None
    skills = profile.get("skills") or []
    return {
        "user_id": mem.get("user_id", user_id),
        "has_profile": bool(skills or profile.get("display_name") or profile.get("target_roles")),
        "profile": profile,
        "resume": {
            "filename": resume.get("filename"),
            "uploaded_at": resume.get("uploaded_at"),
            "char_count": resume.get("char_count"),
            "extraction_method": resume.get("extraction_method"),
            "text_preview": resume.get("text_preview"),
        }
        if resume
        else None,
        "source": mem.get("source"),
        "updated_at": mem.get("updated_at"),
        "created_at": mem.get("created_at"),
        "skill_count": len(skills) if isinstance(skills, list) else 0,
    }
