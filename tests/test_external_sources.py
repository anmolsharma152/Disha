"""Tests for WWR / YC sources (live network when available)."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from tools.board_selection import select_scrape_plan
from tools.job_cache import dedupe_jobs, get_cached_jobs, set_cached_jobs
from tools.job_normalizer import normalize_wwr_job, normalize_yc_job, validate_job_dict


class TestExternalSources(unittest.TestCase):
    def test_plan_enables_wwr_and_yc_for_career_query(self) -> None:
        plan = select_scrape_plan("Find Agentic AI backend roles remote")
        self.assertTrue(plan.fetch_wwr)
        self.assertTrue(plan.fetch_yc)
        self.assertIn("programming", plan.wwr_categories)

    def test_plan_company_match_skips_external_by_default(self) -> None:
        plan = select_scrape_plan("Software engineer roles at PhonePe")
        # Company-specific path returns early without external flags
        self.assertFalse(plan.fetch_wwr)
        self.assertFalse(plan.fetch_yc)

    def test_normalize_wwr(self) -> None:
        raw = {
            "company": "Acme",
            "title": "Senior Backend Engineer",
            "link": "https://weworkremotely.com/remote-jobs/acme-senior-backend",
            "description": "Build APIs with Python FastAPI Docker Kubernetes PostgreSQL",
            "headquarters": "Remote",
            "region": "Anywhere in the World",
            "category": "programming",
            "tags": ["Full-Stack Programming"],
            "skills": [],
        }
        norm = normalize_wwr_job(raw)
        validated = validate_job_dict(norm)
        self.assertIsNotNone(validated)
        assert validated is not None
        self.assertEqual(validated["company_name"], "Acme")
        self.assertEqual(validated["scraper_source"], "we_work_remotely")
        self.assertEqual(validated["remote_policy"], "remote")
        self.assertTrue(validated["skills_required"])

    def test_normalize_yc(self) -> None:
        raw = {
            "id": 12345,
            "title": "Founding Engineer",
            "jobType": "Fulltime",
            "location": "San Francisco, CA, US / Remote",
            "roleType": "Full stack",
            "salary": "$150K - $220K",
            "companyName": "ExampleAI",
            "companySlug": "example-ai",
            "companyBatch": "W26",
            "companyOneLiner": "AI agents for ops",
            "applyUrl": "https://www.workatastartup.com/jobs/12345",
        }
        norm = normalize_yc_job(raw)
        validated = validate_job_dict(norm)
        self.assertIsNotNone(validated)
        assert validated is not None
        self.assertEqual(validated["company_name"], "ExampleAI")
        self.assertEqual(validated["scraper_source"], "yc_jobs")
        self.assertEqual(validated["payout_min"], 150000)
        self.assertEqual(validated["payout_max"], 220000)

    def test_dedupe_jobs(self) -> None:
        jobs = [
            {"title": "Eng", "company_name": "A", "source_url": "https://x.com/1"},
            {"title": "Eng", "company_name": "A", "source_url": "https://x.com/1?ref=1"},
            {"title": "Other", "company_name": "B", "source_url": "https://x.com/2"},
        ]
        out = dedupe_jobs(jobs)
        self.assertEqual(len(out), 2)

    def test_job_cache_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DISHA_DATA_DIR": tmp}):
                set_cached_jobs("test_key", [{"title": "A"}])
                hit = get_cached_jobs("test_key", ttl_seconds=3600)
                self.assertIsNotNone(hit)
                self.assertEqual(hit[0]["title"], "A")


@unittest.skipIf(os.environ.get("DISHA_SKIP_NETWORK") == "1", "network skipped")
class TestExternalSourcesLive(unittest.TestCase):
    def test_fetch_wwr_live(self) -> None:
        from tools.sources.wwr import fetch_wwr_jobs

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DISHA_DATA_DIR": tmp}):
                jobs = fetch_wwr_jobs(
                    categories=["programming"],
                    max_results=5,
                    use_cache=False,
                )
        self.assertGreater(len(jobs), 0)
        self.assertEqual(jobs[0].get("scraper_source"), "we_work_remotely")

    def test_fetch_yc_live(self) -> None:
        from tools.sources.yc_jobs import fetch_yc_jobs

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"DISHA_DATA_DIR": tmp}):
                jobs = fetch_yc_jobs(max_results=5, use_cache=False)
        self.assertGreater(len(jobs), 0)
        self.assertEqual(jobs[0].get("scraper_source"), "yc_jobs")


if __name__ == "__main__":
    unittest.main()
