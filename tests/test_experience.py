"""Tests for deterministic experience years from resume date ranges."""

from __future__ import annotations

import unittest
from datetime import date

from tools.experience import compute_experience_years, extract_professional_spans


RESUME = """
Anmol Sharma
AI Engineer
PROFESSIONAL EXPERIENCE
Independent Research & Development, AI Systems Engineer        06/2024 – Present
Self-Directed / Open Source
• Built agents
Teleperformance, Technical Support Executive 07/2023 – 04/2024 | Jaipur, India
• Support
EDUCATION
Indian Institute of Technology (IIT), Mandi05/2025 – 06/2026
Bachelor of Computer Applications (BCA), Jaipur National University 06/2019 – 05/2022
"""


class TestExperience(unittest.TestCase):
    def test_sums_professional_not_education(self) -> None:
        today = date(2026, 4, 1)
        spans = extract_professional_spans(RESUME, today=today)
        self.assertGreaterEqual(len(spans), 2)
        years = compute_experience_years(RESUME, today=today)
        self.assertIsNotNone(years)
        assert years is not None
        # ~ 07/2023-04/2024 (10m) + 06/2024-04/2026 (23m) = 33m ≈ 2.8y
        self.assertGreaterEqual(years, 2.0)
        self.assertLessEqual(years, 3.5)
        self.assertNotAlmostEqual(years, 0.9, delta=0.15)

    def test_empty_text(self) -> None:
        self.assertIsNone(compute_experience_years(""))


if __name__ == "__main__":
    unittest.main()
