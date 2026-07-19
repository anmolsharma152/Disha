# Phase 3 — Data Quality & Pipeline Honesty

> **Goal:** Fix the gaps that survived Phase 2 — garbage descriptions, silent drops, unused profile fields, dead code — so the pipeline produces *correct* scores, not just *any* scores.
>
> **Guiding principle:** Every data quality fix should make the output more honest. If we can't extract skills, say so. If we dropped a role, explain why. If BBC RSS is junk, don't pretend it's company analysis.
>
> **Anti-goal:** Do not add new data sources, LLM enrichment, or features during this phase. Only fix what exists.

---

## P0 — Wrong Outputs

### Fix 1: Unescape HTML entities before stripping tags

**Problem:** `strip_html()` at `tools/job_normalizer.py:169` never calls `html.unescape()`. Greenhouse API returns `content` as HTML-entity-encoded HTML (`&lt;div&gt;`). The resulting `description_raw` contains literal entity text, making it garbage for any downstream consumer (skill extraction, Gemini enrichment, or UI display).

**Fix:**
```python
import html

def strip_html(html_content: str) -> str:
    html_content = html.unescape(html_content)  # <-- add this line
    clean = re.sub(r"<[^>]+>", " ", html_content)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean
```

**Files:** `tools/job_normalizer.py:169-173`

**Verification:** Greenhouse job descriptions should contain readable text like "We are looking for..." instead of `&lt;div&gt;We are looking for...&lt;/div&gt;`

**Complexity:** 1 line

---

### Fix 2: Gate BBC RSS behind financial intent only

**Problem:** `_fetch_rss_metrics()` at `agents/scraper_agent.py:348` fires on *every* scrape (hardcoded BBC Business RSS URL). This creates `CompanyMetrics("BBC Business")` objects with all nulls for ARR, headcount, cash, etc. The financial analyst always reads `metrics[-1]` (the last article) and scores all-zero data.

**Fix:**
```python
if plan.fetch_rss:
    _fetch_rss_metrics(state)
```
Change to only fire when the query has financial intent (already gated in `board_selection.py:393-395` for the financial-only path, but `plan.fetch_rss` defaults to `False` and is set `True` in `select_scrape_plan()` for financial queries). Verify that `plan.fetch_rss` is never set `True` for career queries.

Alternatively, if the BBC RSS path is genuinely useless (it always produces null CompanyMetrics), remove it entirely and rely on the financial agent returning a graceful empty response when `metrics` is empty.

**Files:** `agents/scraper_agent.py:539-540`, `tools/board_selection.py:393-406`

**Verification:** Career queries should produce 0 `company_metrics` entries. Financial queries for named companies should produce real/non-null metrics only.

**Complexity:** Low (condition change or removal)

---

### Fix 3: Log location-dropped jobs so user sees them

**Problem:** `is_location_match()` at `agents/career_agent.py:38-56` silently drops jobs that don't match target cities. A perfect-fit Applied AI Scientist role in San Francisco is discarded with no trace. The user has no idea it existed.

**Fix:** Add a `logger.info()` call inside the hard-drop path at line 402-403:
```python
if loc_score_pre < 20:
    logger.info("[Career] Dropped job (location): %s @ %s — %s",
                job.get("title"), job.get("company_name"), job.get("location_raw"))
    dropped += 1
    continue
```

Optionally accumulate dropped-with-reason into a new `state["dropped_jobs"]` list so synthesis can surface counts.

**Files:** `agents/career_agent.py:400-404`

**Verification:** Logs should show why each role was dropped. Synthesis can optionally say "3 roles excluded (2 by location, 1 by domain)."

**Complexity:** 3 lines

---

### Fix 4: Wire `experience_years` into experience-fit calculation

**Problem:** `user_profile["experience_years"]` is set by the resume parser (date-range algorithm in `tools/experience.py`) but `calculate_experience_fit()` at `agents/career_agent.py:266` uses it in a fallback path. When `experience_level` is "unknown" (common — most ATS jobs don't specify seniority), the function falls through to title heuristics and returns "unknown" instead of using the candidate's actual years.

**Fix:** In the `exp_level == "unknown"` branch (line 273), explicitly read `profile.get("experience_years")` and apply a direct mapping:
```python
if exp_level == "unknown":
    years = profile.get("experience_years")
    if years is not None:
        if years < 1: return "entry"
        if years < 3: return "junior"
        if years < 6: return "mid"
        if years < 10: return "senior"
        return "staff"
    # fall back to existing title heuristics...
```

**Files:** `agents/career_agent.py:266-295`

**Verification:** Users with `experience_years: 5` in their profile should get "match" for "mid" roles, not "unknown" for every job without an explicit seniority label.

**Complexity:** ~8 lines

---

## P1 — Dead Code & Unused Fields

### Fix 5: Remove clearly dead code

**Problem:** Multiple artifacts are never used but clutter the codebase:

| Artifact | File | Lines | Status |
|---|---|---|---|
| `storage/db.py` | Full async pgvector scaffold | 885 | Never imported anywhere |
| `extract_skills_from_text()` stub | `tools/career_tools.py:57-59` | 3 | Returns `{}`, real version in `skill_lexicon.py` |
| `extract_ats_keywords()` stub | `tools/career_tools.py:61-63` | 3 | Returns `[]` |
| Tool registries (`SCRAPER_TOOLS`, `TOOL_MAP`, `CAREER_TOOLS`) | `tools/scraper_tools.py`, `tools/career_tools.py` | ~20 | Agents call tools by name directly |
| `total_tokens` / `total_cost_usd` tracking | `schemas.py:360-361` | 2 | Initialized to 0, never incremented |
| `retrieved_chunks`, `knowledge_gaps`, `circuit_breakers` | `schemas.py:349-350,344` | 3 | State fields, never populated |

**Fix:** Remove each. The DB scaffold is 885 lines of code with no live consumer — if pgvector is needed later, it can be restored from git history. The stubs and registries are noise.

**Files:** `storage/db.py`, `tools/career_tools.py:57-63`, `tools/career_tools.py:154-168`, `tools/scraper_tools.py` (registries), `schemas.py` (unused fields)

**Complexity:** Medium (many files, but each change is a deletion)

**Risk:** Low — all code is provably dead (confirmed by grep for imports/callers).

---

### Fix 6: Use `target_roles` in title relevance scoring

**Problem:** `user_profile["target_roles"]` is extracted from resumes (e.g., `["ML Engineer", "Backend Engineer"]`) but `calculate_title_relevance()` at `agents/career_agent.py:146` only matches against query tokens. The target roles from the profile provide more accurate signal.

**Fix:** Already partially implemented — `calculate_title_relevance()` at line 167-178 reads `profile.get("target_roles")` and computes a `best_role` score. This code **exists but may not fire** if the profile resolution path doesn't carry `target_roles` through. Verify that `resolve_profile()` includes `target_roles` from resume memory.

**Files:** `agents/career_agent.py:167-178` (verify it works), `tools/profile.py:125-165` (verify `target_roles` flows through)

**Verification:** If the resume says "Backend Engineer" and a job is titled "Backend Engineer", the title relevance should score it highly even if the query only says "find jobs".

**Complexity:** Verification + potential 1-line fix

---

### Fix 7: Add test runner

**Problem:** 6 test files exist in `tests/` but no `pytest` in `requirements.txt` and no CI configuration. Tests are untestable without manual setup.

**Fix:**
```txt
# tests
pytest
```
Add to `requirements.txt`. Optionally add `tests/` to a `pyproject.toml` `[tool.pytest.ini_options]` section.

**Files:** `requirements.txt`

**Complexity:** 1 line

---

## Commit Sequence

```
Fix 1:  Unescape HTML entities in strip_html()           [1 line, P0]
Fix 2:  Gate BBC RSS behind financial intent             [Low, P0]
Fix 3:  Log location-dropped jobs                        [3 lines, P0]
Fix 4:  Wire experience_years into experience-fit        [~8 lines, P0]
-----
Fix 5:  Remove dead code (db.py, stubs, registries, etc) [Medium, P1]
Fix 6:  Verify target_roles flows through to scoring     [Verification, P1]
Fix 7:  Add pytest to requirements.txt                   [1 line, P1]
```

Total: ~100 lines changed across ~10 files. All fixes are in the backend core pipeline — no frontend changes.

---

## Success Criteria

1. Greenhouse job descriptions contain readable text (no `&lt;` / `&gt;` entities)
2. Career-only queries produce 0 `company_metrics` entries (no junk BBC data)
3. Logs show why each job was dropped (location, domain, or skills)
4. Users with `experience_years` in their profile get non-"unknown" experience fits
5. `storage/db.py` is deleted or clearly documented as dead
6. `target_roles` from resume actually influence title relevance
7. `pytest tests/` runs the 6 existing test files

---

## What This Does NOT Fix

These are intentionally deferred (beyond P0/P1 scope or blocked by unresolved decisions):

| Issue | Reason Deferred |
|---|---|
| Skill match returns 0% when lexicon misses terms | Requires active skill enrichment (LLM or heuristic), which is a new feature |
| `evaluate_resume_against_job` tool never called | Requires integrating into graph routing — new feature, not a bug fix |
| error_recovery node never activates | Requires agents to write to error_log — Fix 3 (logging) is a prerequisite |
| BBC RSS data is still garbage for financial queries | The RSS path produces null metrics regardless; replacing it needs a real financial data source |
| `user_query` not used by scraper to filter sources | Board selection already uses query (Fix 2 covers the one hardcoded source — BBC) |
| pgvector semantically empty | No consumer exists for vector search yet |
