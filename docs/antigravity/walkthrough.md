# Production Deployment & Firecrawl Execution Walkthrough

We have completed the deployment setup phase and integrated **Firecrawl** cloud scraping and site extraction into Disha.

---

## 1. Firecrawl Cloud Scraper & Web Search Integration

### Tools Module (`tools/firecrawl_tools.py`)
- **[tools/firecrawl_tools.py](file:///home/anmol/Projects/Disha/tools/firecrawl_tools.py)**: Added `firecrawl-py` SDK integration with SSRF URL protection.
- Tools implemented:
  - `fetch_webpage_firecrawl`: Converts JS-rendered career pages to Markdown.
  - `map_company_careers_firecrawl`: Uses `firecrawl.map_url()` to discover active job URLs under `/careers`.
  - `search_jobs_firecrawl`: Executes web-wide search across job boards (`firecrawl.search()`).

### Scraper Agent Pipeline (`agents/scraper_agent.py`)
- Integrated `_fetch_firecrawl_search` into `node_scraper`. Automatically conducts web-wide role searches when `FIRECRAWL_API_KEY` is present.

### Dependencies & Tests (`tests/test_firecrawl.py`)
- Added `firecrawl-py` to `requirements.txt` and `FIRECRAWL_API_KEY` to `.env.example`.
- Created unit tests verifying URL validation and graceful fallback when uninitialized.

---

## 2. Production Deployment Stack

- **Backend Dockerfile (`Dockerfile`)**: Python 3.12 + Playwright Chromium.
- **Frontend Dockerfile (`frontend/Dockerfile`)**: Multi-stage Next.js 14 standalone build.
- **Production Compose (`docker-compose.prod.yml`)**: PostgreSQL + `pgvector` + FastAPI + Next.js.
- **Deployment Guide (`docs/deployment.md`)**: Deployment workflows for Render/Railway/Vercel/Supabase and VPS Docker Compose.

---

## 3. Verification

- **Firecrawl Test Suite:** `PYTHONPATH=. .venv/bin/pytest tests/test_firecrawl.py` passed (2/2).
- **Full Test Suite:** Ran all 45+ unit & integration tests (`pytest`) — 100% passed.
- **Production Build:** Next.js build (`npm run build`) passed with `output: "standalone"`.
