"""Tests for generic / request-time profile resolution and career scoring."""

from __future__ import annotations

import unittest

from tools.profile import (
    has_salary_floor,
    has_skill_preferences,
    load_default_profile,
    merge_preferences,
    profile_label,
    resolve_profile,
)
from agents.career_agent import (
    calculate_comp_fit,
    calculate_skill_match,
    is_location_match,
    node_career_strategy,
)
from schemas import create_initial_state


class TestProfile(unittest.TestCase):
    def test_default_is_not_personal(self) -> None:
        p = load_default_profile()
        name = (p.get("display_name") or p.get("name") or "").lower()
        self.assertNotIn("anmol", name)
        self.assertNotIn("iit", name)
        self.assertFalse(has_skill_preferences(p))
        self.assertFalse(has_salary_floor(p))
        self.assertIn("default preferences", profile_label(p))

    def test_resolve_merges_request_override(self) -> None:
        state = {
            "user_profile": {
                "skills": ["Python", "Kubernetes"],
                "min_base_salary_inr": 2500000,
                "target_cities": ["bangalore"],
            }
        }
        p = resolve_profile(state)
        self.assertEqual(p["skills"], ["Python", "Kubernetes"])
        self.assertEqual(p["min_base_salary_inr"], 2500000)
        self.assertTrue(has_skill_preferences(p))
        self.assertTrue(has_salary_floor(p))

    def test_comp_unavailable_without_floor_or_pay(self) -> None:
        fit, meets = calculate_comp_fit(
            {"payout_midpoint": None, "currency": "INR"},
            {"min_base_salary_inr": None},
        )
        self.assertEqual(fit, "unavailable")
        self.assertIsNone(meets)

        fit2, meets2 = calculate_comp_fit(
            {"payout_midpoint": 3000000, "currency": "INR"},
            {"min_base_salary_inr": None},
        )
        self.assertEqual(fit2, "unavailable")
        self.assertIsNone(meets2)

    def test_location_open_when_no_cities(self) -> None:
        self.assertTrue(
            is_location_match("San Francisco, CA", "onsite", {"target_cities": []})
        )
        self.assertFalse(
            is_location_match(
                "San Francisco, CA",
                "onsite",
                {"target_cities": ["bangalore"]},
            )
        )

    def test_create_initial_state_has_generic_profile(self) -> None:
        import os
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DISHA_DATA_DIR": tmp}):
                state = create_initial_state("test query", session_id="p1", user_id="empty")
                p = state["user_profile"]
                self.assertEqual(p.get("skills") or [], [])

    def test_skill_match_neutral_without_user_skills(self) -> None:
        job = {
            "tech_stack": ["python", "kubernetes"],
            "skills_required": ["go"],
            "skills_preferred": [],
        }
        pct, matched, missing, status = calculate_skill_match(job, {"skills": []})
        self.assertEqual(status, "no_user_skills")
        self.assertEqual(pct, 0.0)

    def test_skill_match_with_user_skills(self) -> None:
        job = {
            "tech_stack": ["python", "kubernetes"],
            "skills_required": ["go"],
            "skills_preferred": [],
            "title": "Backend Engineer",
            "description_raw": "",
        }
        pct, matched, missing, status = calculate_skill_match(
            job, {"skills": ["Python", "Go"]}
        )
        self.assertEqual(status, "matched")
        self.assertGreater(pct, 40.0)
        self.assertIn("python", matched)

    def test_career_node_with_default_profile(self) -> None:
        import os
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DISHA_DATA_DIR": tmp}):
                state = create_initial_state("roles", session_id="p2", user_id="empty2")
        state["job_openings"] = [
            {
                "job_id": "1",
                "company_name": "Acme",
                "title": "Backend Engineer",
                "location_raw": "Bangalore",
                "location_city": "Bangalore",
                "location_state": None,
                "remote_policy": "hybrid",
                "tech_stack": [],
                "skills_required": [],
                "skills_preferred": [],
                "experience_level": "mid",
                "payout_midpoint": None,
                "currency": "INR",
            }
        ]
        out = node_career_strategy(state)
        recs = out["career_recommendations"]
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["location"], "Bangalore")
        self.assertNotIn("None", recs[0]["location"])
        self.assertEqual(recs[0]["compensation"]["fit"], "unavailable")
        self.assertGreaterEqual(recs[0]["match_score"], 20)

    def test_merge_preferences_clears_with_empty_list(self) -> None:
        base = merge_preferences({}, {"skills": ["Python"]})
        self.assertEqual(base["skills"], ["Python"])
        cleared = merge_preferences(base, {"skills": []})
        self.assertEqual(cleared["skills"], [])


if __name__ == "__main__":
    unittest.main()
