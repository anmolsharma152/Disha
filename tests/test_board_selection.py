"""Unit tests for query-aware board selection (no network)."""

from __future__ import annotations

import unittest

from tools.board_selection import (
    extract_mentioned_companies,
    extract_title_keywords,
    is_financial_query,
    job_matches_india_preference,
    job_matches_keywords,
    select_scrape_plan,
    GREENHOUSE_CATALOG,
)


class TestBoardSelection(unittest.TestCase):
    def test_company_match_phonepe(self) -> None:
        plan = select_scrape_plan("Show me engineering roles at PhonePe")
        boards = [b for _, b in plan.greenhouse]
        self.assertEqual(boards, ["phonepe"])
        self.assertIn("company_match", plan.reasons)

    def test_company_match_anthropic(self) -> None:
        plan = select_scrape_plan("Any ML jobs at Anthropic?")
        self.assertEqual([b for _, b in plan.greenhouse], ["anthropic"])
        self.assertTrue(any("ml" in k or "machine learning" in k for k in plan.title_keywords) or plan.title_keywords)

    def test_default_career_plan(self) -> None:
        plan = select_scrape_plan(
            "Find Agentic AI and backend roles in Bangalore above 20 LPA"
        )
        self.assertGreater(len(plan.greenhouse), 0)
        self.assertIn("default_career", plan.reasons)
        self.assertTrue(plan.prefer_india_locations)
        # Should include topic filters
        self.assertTrue(
            any("agentic" in k or "backend" in k for k in plan.title_keywords),
            plan.title_keywords,
        )

    def test_financial_query_skips_rss(self) -> None:
        plan = select_scrape_plan("Should I invest in Indian AI companies?")
        self.assertTrue(is_financial_query("Should I invest in Indian AI companies?"))

    def test_openai_resolved_via_greenhouse(self) -> None:
        plan = select_scrape_plan("OpenAI research roles")
        self.assertIn("openai", [b for _, b in plan.greenhouse])

    def test_extract_title_keywords_agentic(self) -> None:
        kws = extract_title_keywords("Agentic AI LLMOps engineer in Pune")
        self.assertTrue(any("agentic" in k for k in kws))
        self.assertTrue(any("llmops" in k or "mlops" in k for k in kws))

    def test_job_keyword_or_match(self) -> None:
        job = {"title": "Senior Backend Engineer", "description_raw": "Python services"}
        self.assertTrue(job_matches_keywords(job, ["backend", "agentic"]))
        self.assertFalse(job_matches_keywords(job, ["agentic", "langgraph"]))
        self.assertTrue(job_matches_keywords(job, []))

    def test_india_preference_drops_sf_only(self) -> None:
        us_job = {"title": "ML Engineer", "location_raw": "San Francisco, CA, United States"}
        in_job = {"title": "ML Engineer", "location_raw": "Bangalore, India"}
        self.assertFalse(job_matches_india_preference(us_job, True))
        self.assertTrue(job_matches_india_preference(in_job, True))
        self.assertTrue(job_matches_india_preference(us_job, False))

    def test_mentioned_companies_sorted_by_alias_length(self) -> None:
        hits = extract_mentioned_companies("jobs at scale ai", GREENHOUSE_CATALOG)
        self.assertTrue(hits)
        self.assertEqual(hits[0].board, "scaleai")

    def test_default_plan_caps_boards(self) -> None:
        plan = select_scrape_plan("ML engineer jobs", max_greenhouse=4, max_lever=2)
        self.assertLessEqual(len(plan.greenhouse), 4)
        self.assertLessEqual(len(plan.lever), 2)


if __name__ == "__main__":
    unittest.main()
