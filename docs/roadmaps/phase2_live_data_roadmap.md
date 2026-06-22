# Phase 2 — Live Data & Pipeline Maturation

> **Goal:** Replace fixture/demo data with real job discovery, producing a working end-to-end pipeline: User Query → Real Job Discovery → Career Match → Final Recommendation.
>
> **Guiding principle:** Start with the easiest, highest-reliability data source first. Add complexity only after the basic pipeline is proven.
>
> **Anti-goal:** Do not build an agentic loop, LinkedIn scraper, or LLM-based routing until 5+ data sources are integrated.

---

## 1. Phase 2 Scope

### Included
- Greenhouse API integration (public JSON, no auth)
- Lever API integration (public JSON, no auth)
- Job normalizers (Greenhouse → JobOpening, Lever → JobOpening)
- Error propagation (wire `error_log` → `error_recovery`)
- Optional LLM skill enrichment from description text
- Naukri Playwright scraper (lower priority)

### Excluded (deferred to later phases or indefinitely)
- LinkedIn scraping (legal risk, maintenance burden, anti-bot complexity)
- Agentic planner loop (needs 5+ tools first)
- pgvector semantic search (no consumer yet)
- Resume evaluation integration (tool exists but no integration path)
- Cover letter generator
- Frontend (Phase 3)
- Proxy rotation (premature optimization)
- Circuit breakers (Phase 4)

---

## 2. Implementation Roadmap

### Commit 1: Add Greenhouse API Tool + Normalizer

**Purpose:** Query the public Greenhouse JSON API to fetch structured job data without Playwright or authentication.

**Files:**
- `tools/scraper_tools.py` — Add `SearchGreenhouseInput`, `GreenhouseJobResult`, `SearchGreenhouseOutput` schemas and `search_greenhouse_jobs` tool
- `agents/scraper_agent.py` or `tools/job_normalizer.py` — Add `normalize_greenhouse_job(raw) -> dict`

**Details:**
- Tool calls `GET https://boards-api.greenhouse.io/v1/boards/{board}/jobs`
- Accepts `board` (e.g., "openai", "razorpay") and optional `keywords` parameter for filtering
- Returns structured `GreenhouseJobResult` objects with: title, company, location, description, department, URL, posted date
- Normalizer maps to the 8-field minimum JobOpening contract, adds India defaults
- Tech stack and skills set to empty lists (enriched later via optional LLM step)

**Risks:**
- Low — public API with stable schema
- Some companies may not expose jobs via the API (though most do)

**Complexity:** Low (~80 lines)

---

### Commit 2: Integrate Greenhouse into Scraper Agent

**Purpose:** Replace the hardcoded OpenAI Playwright URL with a configurable list of Greenhouse boards to scrape.

**Files:**
- `agents/scraper_agent.py`

**Details:**
- Add `GREENHOUSE_BOARDS` config list: target companies using Greenhouse
- Replace current Playwright fetch + Gemini extraction with tool-based Greenhouse fetch + normalizer
- Remove BBC RSS mock CompanyMetrics generation
- Keep Gemini extraction as an optional enrichment path (for tech stack extraction from description)
- Result: state["job_openings"] contains real, structured job data

**Risks:**
- Medium — the scraper agent currently mixes RSS, Playwright, and LLM logic; must decouple without breaking existing flow

**Complexity:** Medium (~60 lines)

---

### Commit 3: Wire Error Propagation

**Purpose:** Activate the dead `error_recovery` path so tool failures don't silently degrade output quality.

**Files:**
- `agents/scraper_agent.py` — Add try/except per tool call that writes to `state["error_log"]`
- `main.py` — Ensure `should_continue` checks `error_log` before routing
- `tools/scraper_tools.py` — Return error metadata in output dict

**Details:**
- Each tool call wrapped: on failure, append `{agent, error, timestamp, attempt}` to `error_log`
- If all tools for a pipeline stage fail, set `routing_key = "error_recovery"`
- Add `MAX_RETRIES` counter per tool to prevent infinite loops
- Update synthesis to surface data-source reliability to the user

**Risks:**
- Low — additive change, doesn't modify existing working paths

**Complexity:** Low (~40 lines)

---

### Commit 4: Add Lever API Tool + Normalizer

**Purpose:** Add Lever as a second ATS source using the same pattern as Greenhouse.

**Files:**
- `tools/scraper_tools.py` — Add `SearchLeverInput`, `LeverJobResult`, `SearchLeverOutput` schemas and `search_lever_jobs` tool
- `tools/job_normalizer.py` — Add `normalize_lever_job(raw) -> dict` (shared utilities with Greenhouse normalizer)

**Details:**
- Tool calls `GET https://api.lever.co/v0/postings/{board}?mode=json`
- Accepts `board` parameter (Lever company identifier)
- Lever response includes explicit remote policy field (`categories.remote`) — map to `RemotePolicy` enum
- Shared normalizer utilities: LPA parsing, location normalization, enum mapping

**Risks:**
- Low — same pattern as Greenhouse, Lever API is also stable and public

**Complexity:** Low (~50 lines)

---

### Commit 5: Optional LLM Skill Enrichment

**Purpose:** Enrich job objects with tech stack and skills extracted from description text.

**Files:**
- `agents/scraper_agent.py` — Add enrichment step after normalization
- `tools/scraper_tools.py` — Add enrichment utility or use existing Gemini extraction

**Details:**
- After normalizer produces JobOpening dicts with empty `tech_stack` / `skills_required`:
  1. For each job with non-empty `description_raw`, call Gemini with structured output requesting tech extraction
  2. Update the job dicts with extracted technologies
  3. This is non-blocking — if enrichment fails, the base job is still valid (just missing tech stack)
  4. This enables the Career Agent's skill match scoring to produce non-zero results

**Risks:**
- Medium — adds cost ($0.10-$0.50 per scrape session) and latency (2-5s per job)
- Risk: Mitigated by making enrichment optional and non-blocking

**Complexity:** Medium (~50 lines)

---

### Commit 6: Add Naukri Playwright Scraper (if justified)

**Purpose:** Broaden coverage beyond ATS-based companies to the general Indian job market.

**Files:**
- `tools/scraper_tools.py` — Add `SearchNaukriInput`, `NaukriJobResult`, `SearchNaukriOutput` schemas and `search_naukri_jobs` tool
- `tools/job_normalizer.py` — Add `normalize_naukri_job(raw) -> dict`

**Details:**
- Playwright-based search results page scraping
- Pagination via URL parameter `?page={n}`
- LPA/CTC salary parsing (`"₹12-20 LPA"` → `payout_min=1200000, payout_max=2000000`)
- Anti-bot handling: random delays, user-agent rotation, viewport variation
- Job detail page scraping for full description (second Playwright request per job)
- Returns `NaukriJobResult` objects (typed, not raw HTML)

**Risks:**
- High — Naukri DOM changes, anti-bot measures, CAPTCHAs
- Requires Playwright runtime dependency (already in requirements.txt)
- Can block the pipeline if Naukri is slow or unavailable
- Risk mitigated by making Naukri a third-priority source (tried after Greenhouse and Lever)

**Complexity:** High (~200 lines)

---

## 3. Vertical Slice Definition

### Minimum Viable Phase 2 (Commits 1-3)

The smallest implementation that delivers real end-to-end job discovery:

```
User Query
  → Supervisor → Scraper
       → Greenhouse API (structured job data)
       → Normalizer → JobOpening objects (real, live data)
  → Career Agent (unchanged) → scored, ranked recommendations
  → Synthesis (unchanged) → final answer with live job data
```

This requires:
- Commit 1 (Greenhouse tool + normalizer)
- Commit 2 (integration into scraper agent)
- Commit 3 (error propagation — needed to handle API failures gracefully)

**What this achieves:**
- Real job data from 10-20+ Indian tech companies
- Career matching works with actual skills and compensation
- The system is demonstrably live (not demo/fixture mode)
- Error handling is functional (not dead code)

**What this postpones:**
- Additional data sources (Lever, Naukri)
- LLM enrichment (skills extracted from descriptions)
- Broad coverage (limited to Greenhouse-using companies)
- Performance optimizations (caching, parallel requests)

---

## 4. Design Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Primary data source** | Greenhouse API | Public JSON, no auth, structured data, highest reliability |
| **Secondary data source** | Lever API | Same pattern as Greenhouse, adds remote policy field |
| **Tertiary data source** | Naukri Playwright | Broader coverage, better salary data, but significantly harder |
| **Deferred indefinitely** | LinkedIn | Legal risk + scraping difficulty > value for this project |
| **Data pipeline** | Tool → RawResult → Normalizer → JobOpening | Option B from data flow review (decoupled, testable, maintainable) |
| **Tech stack extraction** | Optional LLM enrichment | Non-blocking, off by default, enabled for production |
| **Error handling** | Local per-tool + escalate to error_recovery | Fix dead error_recovery code, don't replace it |
| **Agentic loop** | Deferred (5+ tools) | Not enough tools yet to justify LLM planning |
| **Schema defaults** | Factory functions, not schema changes | Keep schema generic, India at creation time |

---

## 5. Unresolved Questions

1. **Which Indian AI/ML companies use Greenhouse vs. Lever vs. other ATS?** A discovery task is needed to build the target company → ATS type mapping before implementation begins.

2. **Should the LLM enrichment use Gemini 2.5 Flash (current model) or a cheaper model?** The current code uses gemini-2.5-flash for extraction. For batch skill enrichment, a cheaper model may suffice. Needs benchmarking.

3. **Should Naukri be done at all?** If Greenhouse + Lever cover 80% of target roles, Naukri may not be worth the effort. The decision should be made after Commits 1-4 are in production and coverage is measured.

4. **How should the tool registry be handled?** Current decorative registry (list + map, unused) should either be removed or fixed to support runtime tool selection. Needs a separate decision.

5. **Should the company board list be hardcoded or configurable?** A YAML config (`target_companies.yaml`) would make it easy to add/remove companies without code changes. This is a small design decision before Commit 1.

---

## 6. Commit Sequence

```
Commit 1:  Add Greenhouse API tool + normalizer          [Low complexity]
Commit 2:  Integrate Greenhouse into scraper agent        [Medium complexity]
Commit 3:  Wire error propagation through entire pipeline  [Low complexity]
Commit 4:  Add Lever API tool + normalizer                 [Low complexity]
Commit 5:  Add optional LLM skill enrichment               [Medium complexity]
Commit 6:  Add Naukri Playwright scraper (if justified)    [High complexity]

Total: 6 commits, ~480 lines across all files
```

---

## 7. Success Criteria

Phase 2 is successful when:

1. A query like *"Find Agentic AI and backend roles in Bangalore above 20 LPA"* returns jobs from a real, live API call (not fixtures, not Gemini-hallucinated)
2. Those jobs have correct `currency="INR"`, `location_country="IN"` for India roles
3. The Career Agent produces non-zero skill match scores (because at least some jobs have `tech_stack` populated)
4. Tool failures are reported via `error_log` and optionally trigger `error_recovery` fallback
5. The total pipeline latency for a scrape-without-LLM run is <10 seconds
