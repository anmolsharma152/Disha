"""Unit tests for error recovery routing (no network)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from schemas import create_initial_state
from main import node_error_recovery, should_continue
from agents.supervisor_agent import node_supervisor
from tools.board_selection import select_scrape_plan


class TestErrorRecovery(unittest.TestCase):
    def test_fallback_plan_broader_than_default(self) -> None:
        normal = select_scrape_plan("Agentic AI roles in Bangalore", fallback=False)
        wide = select_scrape_plan("Agentic AI roles in Bangalore", fallback=True)
        self.assertIn("fallback_career", wide.reasons)
        self.assertGreaterEqual(len(wide.greenhouse), len(normal.greenhouse))
        self.assertEqual(wide.title_keywords, [])

    def test_error_recovery_activates_scraper_fallback(self) -> None:
        state = create_initial_state("Find ML roles", session_id="t1")
        state["error_log"] = [{
            "agent": "scraper",
            "tool": "scrape_plan",
            "error": "No jobs",
            "severity": "error",
        }]
        state["routing_key"] = "error_recovery"
        out = node_error_recovery(state)
        self.assertTrue(out["fallback_activated"].get("scraper"))
        self.assertEqual(out["routing_key"], "scraper")
        self.assertEqual(out["error_log"], [])
        self.assertEqual(should_continue(out), "scraper")

    def test_error_recovery_second_scraper_failure_goes_synthesize(self) -> None:
        state = create_initial_state("Find ML roles", session_id="t2")
        state["fallback_activated"] = {"scraper": True}
        state["error_log"] = [{
            "agent": "scraper",
            "error": "still empty",
            "severity": "error",
        }]
        out = node_error_recovery(state)
        self.assertEqual(out["routing_key"], "synthesize")
        self.assertEqual(should_continue(out), "synthesize")

    def test_supervisor_routes_empty_scrape_to_recovery(self) -> None:
        state = create_initial_state("Find ML roles", session_id="t3")
        state["iteration"] = 1  # will become 2 inside supervisor
        state["routing_key"] = "scraper"
        state["job_openings"] = []
        state["company_metrics"] = []
        out = node_supervisor(state)
        self.assertEqual(out["routing_key"], "error_recovery")

    def test_supervisor_does_not_recover_when_jobs_present(self) -> None:
        state = create_initial_state("Find ML roles", session_id="t4")
        state["iteration"] = 1
        state["routing_key"] = "scraper"
        state["job_openings"] = [{"title": "ML Engineer", "company_name": "X"}]
        state["error_log"] = [{
            "agent": "scraper",
            "tool": "playwright",
            "error": "timeout",
            "severity": "error",
        }]
        out = node_supervisor(state)
        self.assertEqual(out["routing_key"], "career_strategy")

    def test_supervisor_continues_after_fallback_empty(self) -> None:
        state = create_initial_state("Find ML roles", session_id="t5")
        state["iteration"] = 2
        state["routing_key"] = "scraper"
        state["job_openings"] = []
        state["fallback_activated"] = {"scraper": True}
        out = node_supervisor(state)
        self.assertEqual(out["routing_key"], "career_strategy")

    def test_scraper_records_error_on_empty(self) -> None:
        from agents.scraper_agent import node_scraper

        state = create_initial_state(
            "roles at nonexistentcoxyz",
            session_id="t6",
        )
        # Force an empty plan by mocking select + fetch paths
        with patch("agents.scraper_agent.select_scrape_plan") as mock_plan, \
             patch("agents.scraper_agent._fetch_greenhouse", return_value=[]), \
             patch("agents.scraper_agent._fetch_lever", return_value=[]), \
             patch("agents.scraper_agent._extract_jobs_with_gemini", return_value=[]):
            from tools.board_selection import ScrapePlan
            mock_plan.return_value = ScrapePlan(
                greenhouse=[],
                lever=[],
                reasons=["test_empty"],
            )
            out = node_scraper(state)
        self.assertEqual(out["job_openings"], [])
        self.assertTrue(
            any(e.get("severity") == "error" for e in out.get("error_log", []))
        )


if __name__ == "__main__":
    unittest.main()
