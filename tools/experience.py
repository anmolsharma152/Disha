"""
Deterministic professional experience years from resume text date ranges.

Does not use an LLM. Parses MM/YYYY–MM/YYYY / Present style spans and
sums non-overlapping professional months, excluding education lines.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

_MONTH = r"(?:0?[1-9]|1[0-2])"
_YEAR = r"(?:19|20)\d{2}"
# 06/2024 – Present | 07/2023 – 04/2024 | 06/2024-Present | 2021 – 2024
_RANGE_RE = re.compile(
    rf"(?P<a_m>{_MONTH})[/\-.](?P<a_y>{_YEAR})\s*[–—\-to]+\s*"
    rf"(?:(?P<b_m>{_MONTH})[/\-.](?P<b_y>{_YEAR})|(?P<present>Present|present|Current|current|Now|now))",
    re.I,
)
_YEAR_ONLY_RE = re.compile(
    rf"(?P<a_y>{_YEAR})\s*[–—\-to]+\s*(?:(?P<b_y>{_YEAR})|(?P<present>Present|present|Current|current))",
    re.I,
)

_EDU_MARKERS = (
    "bachelor",
    "master",
    "b.tech",
    "btech",
    "m.tech",
    "bca",
    "mca",
    "university",
    "institute of technology",
    "iit ",
    "education",
    "minor in",
    "cgpa",
    "school",
    "college",
    "degree",
)

_PRO_MARKERS = (
    "experience",
    "engineer",
    "developer",
    "intern",
    "research",
    "independent",
    "self-directed",
    "open source",
    "support",
    "executive",
    "consultant",
    "founder",
    "freelance",
)


@dataclass(frozen=True)
class DateSpan:
    start: date
    end: date
    source_line: str


def _month_end(y: int, m: int) -> date:
    if m == 12:
        return date(y, 12, 31)
    # last day approx via next month - 1 day
    return date(y, m + 1, 1).fromordinal(date(y, m + 1, 1).toordinal() - 1)


def _parse_spans_from_line(line: str, today: date) -> List[DateSpan]:
    spans: List[DateSpan] = []
    for m in _RANGE_RE.finditer(line):
        a_m, a_y = int(m.group("a_m")), int(m.group("a_y"))
        start = date(a_y, a_m, 1)
        if m.group("present"):
            end = today
        else:
            b_m, b_y = int(m.group("b_m")), int(m.group("b_y"))
            end = _month_end(b_y, b_m)
        if end >= start:
            spans.append(DateSpan(start=start, end=end, source_line=line.strip()[:160]))
    if spans:
        return spans
    for m in _YEAR_ONLY_RE.finditer(line):
        a_y = int(m.group("a_y"))
        start = date(a_y, 1, 1)
        if m.group("present"):
            end = today
        else:
            b_y = int(m.group("b_y"))
            end = date(b_y, 12, 31)
        if end >= start:
            spans.append(DateSpan(start=start, end=end, source_line=line.strip()[:160]))
    return spans


def _is_education_line(line: str) -> bool:
    low = line.lower()
    return any(k in low for k in _EDU_MARKERS)


def _is_professional_context(line: str, prev_lines: List[str]) -> bool:
    ctx = " ".join(prev_lines[-2:] + [line]).lower()
    if _is_education_line(line) or _is_education_line(ctx):
        return False
    if any(k in ctx for k in _PRO_MARKERS):
        return True
    # Date ranges under PROFESSIONAL EXPERIENCE header
    return "experience" in " ".join(prev_lines[-8:]).lower()


def extract_professional_spans(
    text: str,
    today: Optional[date] = None,
) -> List[DateSpan]:
    """
    Walk resume lines with a simple section state machine so summary lines
    mentioning IIT/education do not poison the first work date range.
    """
    today = today or date.today()
    lines = (text or "").splitlines()
    spans: List[DateSpan] = []
    section = "unknown"  # unknown | experience | education | other

    for line in lines:
        low = line.lower().strip()
        if not low:
            continue
        # Section headers
        if re.search(r"professional\s+experience|work\s+experience|employment\s+history", low):
            section = "experience"
            continue
        if re.search(r"^education\b|academic\s+background", low) or low == "education":
            section = "education"
            continue
        if re.search(r"^(skills|projects|certifications|awards)\b", low):
            section = "other"
            continue

        line_spans = _parse_spans_from_line(line, today)
        if not line_spans:
            continue

        if section == "education" or _is_education_line(line):
            continue
        if section == "experience":
            spans.extend(line_spans)
            continue
        # Unknown section: allow only if line looks professional and not education
        if _is_professional_context(line, []) and not _is_education_line(line):
            spans.extend(line_spans)
    return spans


def merge_spans(spans: List[DateSpan]) -> List[Tuple[date, date]]:
    if not spans:
        return []
    ordered = sorted(((s.start, s.end) for s in spans), key=lambda x: x[0])
    merged: List[List[date]] = [[ordered[0][0], ordered[0][1]]]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:
            if end > last[1]:
                last[1] = end
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged]


def months_between(start: date, end: date) -> int:
    if end < start:
        return 0
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


def compute_experience_years(
    text: str,
    today: Optional[date] = None,
) -> Optional[float]:
    """
    Return years of professional experience (1 decimal), or None if no spans found.
    """
    today = today or date.today()
    spans = extract_professional_spans(text, today=today)
    if not spans:
        return None
    merged = merge_spans(spans)
    total_months = sum(months_between(a, b) for a, b in merged)
    if total_months <= 0:
        return None
    years = round(total_months / 12.0, 1)
    # Cap absurd parses
    if years > 50:
        return None
    return years


def apply_deterministic_experience(profile: dict, resume_text: str) -> dict:
    """Overwrite profile experience_years when date ranges parse successfully."""
    years = compute_experience_years(resume_text)
    out = dict(profile)
    if years is not None:
        out["experience_years"] = years
        out["experience_years_source"] = "date_ranges"
    elif out.get("experience_years") is not None:
        out["experience_years_source"] = "llm_or_heuristic"
    return out
