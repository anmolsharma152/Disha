# Disha Project Tasks & Engineering Roadmap

This document tracks completed features, active development items, and upcoming roadmap milestones for the **Disha** job intelligence engine.

---

## 1. Completed Milestones

### Phase 1: Zero-Trust Security Hardening
- [x] **SSRF Protection:** Built `is_safe_url()` in `tools/scraper_tools.py` blocking loopback, RFC 1918 private IPs, and cloud metadata (`169.254.169.254`).
- [x] **Path Traversal Guard:** Built `validate_board_slug()` enforcing `^[a-zA-Z0-9_-]+$` on ATS board inputs.
- [x] **CORS & Rate Limiting:** Enforced `ALLOWED_ORIGINS` CORS configuration and 30 req/min token bucket rate limiter in `api/server.py`.
- [x] **Prompt Injection Guard:** Wrapped untrusted JDs and resumes in `<job_description>` and `<candidate_resume>` XML tags with strict anti-jailbreak directives in `tools/career_tools.py`.
- [x] **Security Test Suite:** Created `tests/test_security.py` verifying SSRF blocking, slug regex, and tenant isolation.

### Phase 2: Core Graph & Storage Layer
- [x] **Error Recovery Edge:** Fixed `agents/scraper_agent.py` to route empty scrapes to `node_error_recovery`.
- [x] **LLM Resume Judge:** Wired `evaluate_resume_against_job` powered by Gemini 2.5 Flash into `agents/career_agent.py`.
- [x] **pgvector Storage:** Created `storage/db.py` async SQLAlchemy 2.0 ORM models (`JobOpeningModel`, `DocumentChunkModel`) with `Vector(768)` columns and native cosine distance queries (`<=>`).
- [x] **Database Initializer:** Created `storage/init_db.py` for automated table creation and vector extension enablement.

### Phase 3: Ingestion & Firecrawl Integration
- [x] **Firecrawl SDK Tools:** Created `tools/firecrawl_tools.py` with `fetch_webpage_firecrawl`, `extract_job_firecrawl`, `map_company_careers_firecrawl`, and `search_jobs_firecrawl`.
- [x] **Scraper Agent Integration:** Added `_fetch_firecrawl_search` to `agents/scraper_agent.py` for web-wide role discovery when `FIRECRAWL_API_KEY` is present.
- [x] **Firecrawl Tests:** Created `tests/test_firecrawl.py` verifying schema extraction and graceful missing-key fallbacks.

### Phase 4: Production Deployment & CI/CD
- [x] **Backend Dockerfile:** Created production `Dockerfile` with Python 3.12, system dependencies, and Playwright Chromium binaries.
- [x] **Frontend Dockerfile:** Created multi-stage `frontend/Dockerfile` utilizing Next.js `standalone` output mode.
- [x] **Production Compose:** Created `docker-compose.prod.yml` linking `db` (`ankane/pgvector`), `backend` (FastAPI), and `frontend` (Next.js).
- [x] **Environment Template:** Created `.env.example` defining all production secrets.
- [x] **Deployment Documentation:** Created comprehensive `docs/deployment.md` covering Vercel, Render, Supabase, and VPS workflows.
- [x] **Keep-Alive Workflow:** Created `.github/workflows/keep_alive.yml` with timeout guards to prevent Render sleep and Supabase pause.
- [x] **Automated CI Pipeline:** Created `.github/workflows/ci.yml` running pytest and Next.js build validation on push.

### Phase 5: Multi-Tenant Session Memory
- [x] **Client Session Tokens:** Implemented `getOrGenerateUserId()` in `frontend/hooks/useProfile.ts` generating unique `disha_user_id` tokens.
- [x] **Stream User Binding:** Passed `user_id` in `/api/chat/stream` POST payloads (`frontend/hooks/useChat.ts`).
- [x] **Memory Fail-Safe:** Added default profile memory fallback in `tools/profile.py` (`resolve_profile`) to prevent 0-skill matching on new browser tabs.

---

## 2. Active & Upcoming Roadmap

### Phase 6: Sub-15s Performance Pipeline (High Priority)
- [ ] **Parallel Scraper Engine (`asyncio.gather`):**
  - Refactor `agents/scraper_agent.py` to fetch Greenhouse, Lever, WWR RSS, YC, and Firecrawl concurrently rather than serially.
  - *Target:* Cut total scrape cycle time from 120s+ to under 15s.
- [ ] **Async Playwright Migration:**
  - Replace remaining `sync_playwright` invocations in `tools/scraper_tools.py` with `async_playwright` to eliminate event loop warnings.

### Phase 7: Claude-Style Live Agent Visualizer & Chat Feed UI (High Priority)
- [ ] **Claude-Style Live Visualizer (`AgentExecutionVisualizer.tsx`):**
  - Animated spinning wheels, hourglass icons, and real-time execution timers (`00:04s`) per pipeline step.
  - Stream fine-grained sub-step progress logs via SSE (e.g. `⏳ Searching Firecrawl for Sarvam AI...`, `⏳ Scoring 25 roles against candidate profile...`).
  - Expandable "Thinking / Activity Log" drawers for complete pipeline transparency.
- [ ] **Multi-Turn Conversational Feed (`ChatFeed.tsx`):**
  - Build scrollable message history thread preserving past user prompts, agent responses, and embedded Job Match Cards.
  - Enable conversational follow-up questions on previous results.

### Phase 8: Dynamic Resume-Derived Experience Boundaries
- [ ] **Experience Range Extraction (`tools/career_tools.py`):**
  - Extract candidate `experience_years` (e.g. 3.1 YOE) and `seniority_level` directly from uploaded resumes.
- [ ] **Adaptive Title & Seniority Filtering:**
  - Compute dynamic allowed boundary: $[\max(0, \text{exp} - 1.5),\, \text{exp} + 2.5]$ YOE.
  - Automatically filter out executive/staff roles (`Senior Staff`, `Director`, `VP`, `Chief of Staff`) for early/mid-career profiles.
  - Apply proportional experience mismatch penalties in `agents/career_agent.py`.

### Phase 9: Targeted Company Query Routing
- [ ] **Company Intent Extractor:**
  - Update supervisor agent to detect explicit company queries (e.g. *"Sarvam AI new postings"*, *"Krutrim LLM roles"*).
- [ ] **Targeted Firecrawl Dispatch:**
  - Bypass generic default board lists and dispatch targeted Firecrawl searches directly to the specified company's careers portal.

---

## 3. Verification Commands

```bash
# 1. Run full backend test suite
PYTHONPATH=. .venv/bin/pytest tests/ -v

# 2. Run security-specific tests
PYTHONPATH=. .venv/bin/pytest tests/test_security.py -v

# 3. Run Firecrawl integration tests
PYTHONPATH=. .venv/bin/pytest tests/test_firecrawl.py -v

# 4. Verify Next.js frontend production build
cd frontend && npm run build
```
