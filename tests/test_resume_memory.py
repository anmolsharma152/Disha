"""Tests for resume extraction and single-user memory."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.resume_parser import extract_profile_from_resume_text, extract_text_from_upload
from tools.profile import resolve_profile, profile_label
from schemas import create_initial_state


SAMPLE_RESUME = """
Alex Kumar
Bangalore, India | alex@example.com

SUMMARY
Backend and ML engineer with 4 years of experience building APIs and LLM systems.

EXPERIENCE
Software Engineer, Acme Corp (2021-2025)
- Built FastAPI microservices on Kubernetes and AWS
- Shipped RAG pipelines with LangChain, LangGraph, and Pinecone
- Fine-tuned models with PyTorch and MLflow

SKILLS
Python, TypeScript, PostgreSQL, Redis, Docker, Terraform, GCP, vLLM

EDUCATION
B.Tech Computer Science
"""


class TestResumeMemory(unittest.TestCase):
    def test_heuristic_extracts_skills_and_city(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            # Force heuristic by removing keys for this call path
            env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY")}
            with patch.dict(os.environ, env, clear=True):
                profile, method = extract_profile_from_resume_text(SAMPLE_RESUME)
        self.assertEqual(method, "heuristic")
        skills_l = {s.lower() for s in profile["skills"]}
        self.assertTrue(skills_l & {"python", "fastapi", "kubernetes", "pytorch", "langchain"})
        cities = {c.lower() for c in profile["target_cities"]}
        self.assertTrue(cities & {"bangalore"})
        self.assertIsNotNone(profile.get("experience_years"))

    def test_txt_upload_extract(self) -> None:
        text = extract_text_from_upload("resume.txt", SAMPLE_RESUME.encode("utf-8"))
        self.assertIn("Alex Kumar", text)

    def test_memory_roundtrip(self) -> None:
        from storage import user_memory as um

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DISHA_DATA_DIR": tmp}):
                um.clear_memory("testuser")
                profile, method = extract_profile_from_resume_text(SAMPLE_RESUME)
                mem = um.upsert_profile_from_resume(
                    profile=profile,
                    filename="resume.txt",
                    text_preview=SAMPLE_RESUME[:100],
                    char_count=len(SAMPLE_RESUME),
                    user_id="testuser",
                    extraction_method=method,
                )
                self.assertEqual(mem["source"], "resume_upload")
                loaded = um.get_profile("testuser")
                self.assertGreater(len(loaded.get("skills") or []), 3)
                view = um.memory_public_view("testuser")
                self.assertTrue(view["has_profile"])
                um.clear_memory("testuser")
                self.assertFalse(um.memory_public_view("testuser")["has_profile"])

    def test_resolve_profile_uses_memory(self) -> None:
        from storage import user_memory as um

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DISHA_DATA_DIR": tmp}):
                um.upsert_profile_from_resume(
                    profile={
                        "display_name": "Alex Kumar",
                        "skills": ["Python", "Kubernetes"],
                        "target_roles": ["Backend Engineer"],
                        "target_cities": ["bangalore"],
                        "experience_years": 4,
                        "prefer_remote": True,
                        "willing_to_relocate": True,
                    },
                    filename="r.txt",
                    text_preview="x",
                    char_count=10,
                    user_id="default",
                    extraction_method="heuristic",
                )
                p = resolve_profile({"user_id": "default"}, user_id="default")
                self.assertIn("Python", p["skills"])
                label = profile_label(p).lower()
                self.assertTrue(
                    "alex" in label or "memory" in label or "skills" in label,
                    label,
                )
                state = create_initial_state("roles at PhonePe", user_id="default")
                self.assertIn("Python", state["user_profile"]["skills"])


if __name__ == "__main__":
    unittest.main()
