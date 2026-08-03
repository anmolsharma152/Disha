# Disha Firecrawl Integration Plan

This plan details the integration of **Firecrawl** (`firecrawl-py` Python SDK / API) into Disha's job ingestion layer as a first-class scraper and extraction backend for complex, JS-rendered career portals (Workday, Instahyre, Wellfound, BeBee, custom `/careers` pages).

---

## 1. Objective & Architecture

### Why Firecrawl in Disha?
- **JS Rendering Without Browser Overhead:** Eliminates heavy Playwright container maintenance for JS-rendered career portals.
- **Native JSON Schema Extraction:** Extracts structured `JobOpening` Pydantic objects directly in a single API call using Firecrawl's LLM extraction engine.
- **Site Mapping & Discovery:** Maps company `/careers` sub-URLs (`firecrawl.map_url()`) to discover active engineering job postings automatically.
- **Multi-Source Job Search:** Executes multi-board search queries across career pages using `firecrawl.search()`.

### Scraper Priority Hierarchy

```text
Query → Scraper Agent
       ├─ 1. Greenhouse JSON API (boards-api.greenhouse.io)
       ├─ 2. Lever Board Scraper (jobs.lever.co)
       ├─ 3. Firecrawl API (firecrawl.search / scrape / extract) ◄─ [NEW PRIMARY]
       └─ 4. Playwright Headless Browser (local fallback if no API key)
```

---

## 2. Proposed Changes & New Modules

### Component 1: Dependency & Environment Configuration
#### **[MODIFY] [requirements.txt](file:///home/anmol/Projects/Disha/requirements.txt)**
- Add `firecrawl-py>=1.0.0`.

#### **[MODIFY] [.env.example](file:///home/anmol/Projects/Disha/.env.example)**
- Add `FIRECRAWL_API_KEY=your_firecrawl_api_key_here`.

---

### Component 2: Dedicated Firecrawl Tools Module
#### **[NEW] [tools/firecrawl_tools.py](file:///home/anmol/Projects/Disha/tools/firecrawl_tools.py)**
Implement standard LangChain-compatible tools wrapping the `firecrawl-py` SDK:

1. **`fetch_webpage_firecrawl`**:
   - Calls `firecrawl.scrape_url(url, params={'formats': ['markdown']})`.
   - Returns clean, script-stripped Markdown content for any JS-heavy page.
   - Includes SSRF safety validation (`is_safe_url`).

2. **`extract_job_firecrawl`**:
   - Calls `firecrawl.scrape_url(url, params={'formats': ['extract'], 'extract': {'schema': JobSchema}})` using `JobOpening` schema.
   - Directly returns parsed `JobOpening` dict without requiring secondary LLM calls.

3. **`map_company_careers_firecrawl`**:
   - Calls `firecrawl.map_url(url, params={'search': 'engineer|developer|ml|ai'})`.
   - Returns list of specific job posting URLs under a company's career section.

4. **`search_jobs_firecrawl`**:
   - Calls `firecrawl.search(query, params={'limit': 10})`.
   - Performs web-wide role discovery across job sites.

---

### Component 3: Integration into Scraper Agent
#### **[MODIFY] [agents/scraper_agent.py](file:///home/anmol/Projects/Disha/agents/scraper_agent.py)**
- Check for `FIRECRAWL_API_KEY` in environment.
- When scraping non-ATS company URLs or running multi-source search:
  - Prefer `extract_job_firecrawl` / `fetch_webpage_firecrawl`.
  - Fall back to Playwright only if `FIRECRAWL_API_KEY` is not configured.

---

### Component 4: Testing & Verification
#### **[NEW] [tests/test_firecrawl.py](file:///home/anmol/Projects/Disha/tests/test_firecrawl.py)**
- **Unit Tests:** Mocked tests verifying schema extraction, URL mapping, and error handling.
- **Integration Test:** Live scraping test when `FIRECRAWL_API_KEY` is set in environment.

---

## 3. Verification & Execution Plan

1. Install `firecrawl-py` package:
   ```bash
   pip install firecrawl-py
   ```
2. Create `tools/firecrawl_tools.py` and register tools.
3. Update `agents/scraper_agent.py` to route custom URL scrapes through Firecrawl.
4. Run test suite:
   ```bash
   PYTHONPATH=. .venv/bin/pytest tests/test_firecrawl.py
   ```

---

## User Review Required

Please review this plan. Once approved, I will begin implementing the `firecrawl-py` integration!
