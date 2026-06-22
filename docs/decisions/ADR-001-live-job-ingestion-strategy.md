# ADR-001: Live Job Ingestion Strategy

**Status:** Accepted (2026-06-22)
**Author:** Architecture Review
**Area:** Scraping, Data Ingestion, Job Pipeline
**Supersedes:** N/A

---

## Context

Disha currently runs in "demo mode" with poor-quality live data:

1. The scraper fetches BBC News RSS and OpenAI's Greenhouse page via Playwright
2. It uses Gemini to extract `JobOpening` objects from scraped markdown
3. The extracted jobs represent a single, non-Indian company (OpenAI)
4. The system has no dedicated job search tools for Indian platforms

Before Phase 2 can deliver real end-to-end job discovery, a live data ingestion strategy must be established.

---

## Decision Drivers

1. **Need real Indian AI/ML job data** — The system's value proposition is India-specific career matching
2. **Avoid fragile architectures** — The scraper should not depend on anti-bot evasion, login flows, or session management
3. **Maintain determinism** — The ingestion pipeline should produce reproducible results
4. **Minimize LLM API costs** — Current Gemini extraction is slow and expensive for large-scale ingestion
5. **Enable incremental rollout** — Support adding data sources one at a time without rewiring the agent

---

## Considered Options

### Option A: Playwright-based platform scraping

Scrape Naukri and LinkedIn using Playwright with anti-bot measures.

**Pros:**
- Broad coverage of Indian job market
- No API rate limits

**Cons:**
- Fragile — DOM changes break scrapers regularly
- Requires anti-bot evasion (proxies, login, CAPTCHAs)
- High maintenance burden
- Legal risk (LinkedIn vs. HiQ Labs)
- Slow — full browser per page

### Option B: Public ATS API integration

Use the public JSON APIs provided by Greenhouse and Lever ATS systems.

**Pros:**
- No authentication required
- Structured data returned (no LLM extraction needed)
- Extremely reliable — HTTP GET against stable endpoints
- Low maintenance — API schema changes rarely
- Fast — single HTTP request per board
- Legal — operating within intended API usage

**Cons:**
- Only covers companies using Greenhouse or Lever
- Limited to ~10-15 major Indian tech companies initially
- Missing Naukri/LinkedIn breadth

### Option C: Option B + Naukri Playwright (layered)

Start with Option B (Greenhouse + Lever), add Naukri Playwright in a second layer.

**Pros:**
- Best of both worlds: reliable structured data + broad coverage
- Can use Greenhouse/Lever data to drive the demo while Naukri is developed
- Naukri is a fallback when Greenhouse/Lever don't have a target company

**Cons:**
- More work overall (two implementations)
- Risk that Naukri effort is wasted if Greenhouse/Lever cover sufficient roles

### Option D: LLM-only extraction (current approach)

Keep the existing pattern: scrape any HTML, feed to Gemini for extraction.

**Pros:**
- No per-platform code
- Flexible — works with any webpage

**Cons:**
- Non-deterministic — same page produces different results
- High cost — 1 Gemini call per page
- High latency — 3-10s per extraction
- Unreliable — LLM may hallucinate fields or miss jobs

---

## Decision

**Accept Option C: Greenhouse/Lever API first, Naukri Playwright second.**

### Rationale

1. **Greenhouse and Lever cover the highest-value jobs.** The target market (AI/ML engineer, Bangalore, 20LPA+) is concentrated at companies that use modern ATS systems (Greenhouse, Lever, Ashby). These are the same companies whose jobs are most relevant for Disha's career matching.

2. **The codebase already references Greenhouse.** OpenAI's Greenhouse board is hardcoded in `node_scraper`. Replacing the Playwright call with a JSON API call is a ~10-line change that improves reliability from ~60% to ~99.9%.

3. **Greenhouse/Lever provide structured data with 80% of required fields.** Title, company, location, description, department, and URL are available as direct fields. Only tech stack and skills require LLM extraction (optional, can do offline).

4. **Naukri is a valuable but costly addition.** It provides broader coverage and better salary data. But it requires Playwright, anti-bot handling, and LPA parsing. It should be added only after the Greenhouse/Lever pipeline is stable.

5. **LinkedIn is deferred indefinitely.** The legal risk, scraping difficulty, and maintenance burden exceed the value for Phase 2. LinkedIn provides excellent data but is not worth the operational overhead for this project's scope.

---

## Consequences

### Positive

- Immediate access to structured job data from 50+ Indian tech companies using Greenhouse/Lever
- No anti-bot infrastructure needed for initial Phase 2
- Deterministic, testable, low-latency data pipeline
- LLM costs shift from extraction to optional enrichment
- Easy to add new companies (one line: add board name to config list)

### Negative

- Initial coverage is limited to companies that use Greenhouse or Lever
- Must discover which target companies use these ATS systems
- Naukri development is postponed — broader coverage comes later

### Mitigations

- Build a configurable company list mapping each target company to its board URL and ATS type
- Make the normalizer pluggable (`normalize_greenhouse`, `normalize_lever`, later `normalize_naukri`)
- Schedule Naukri as a follow-up commit, not a Phase 2 blocker

---

## Implementation Summary

| Source | Priority | Approach | Complexity | Lines |
|--------|----------|----------|------------|-------|
| Greenhouse API | **1st** | HTTP GET `boards-api.greenhouse.io/v1/boards/{board}/jobs` | Low (~60 lines tool + normalizer) | Low |
| Lever API | **2nd** | HTTP GET `api.lever.co/v0/postings/{board}?mode=json` | Low (~50 lines tool + normalizer) | Low |
| Naukri Playwright | **3rd** | Playwright search results + job detail pages | High (~200 lines) | High |
| LinkedIn | **Deferred** | Not implemented | Very High | Indefinite |

---

## References

- `agents/scraper_agent.py` — Current scraper agent (will be modified to dispatch to API-based tools)
- `tools/scraper_tools.py` — Tool registry (new tools added here)
- `schemas.py:150` — JobOpening model (minimum viable contract defined in job_opening_contract.md)
