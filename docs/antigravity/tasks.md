# Disha Implementation Task List

## Completed Infrastructure & Core Features
- [x] SSRF Protection & URL Validation (`is_safe_url`) in `tools/scraper_tools.py`
- [x] Path Traversal Regex Validation (`validate_board_slug`) in `tools/scraper_tools.py`
- [x] Restrict CORS `ALLOWED_ORIGINS` in `api/server.py`
- [x] Rate Limiting Middleware (`check_rate_limit`) on `/api/chat` endpoints in `api/server.py`
- [x] Prompt Injection Framing (<untrusted_content> XML tags) in `tools/career_tools.py`
- [x] Wire Error Recovery Node routing (`state["routing_key"] = "error_recovery"`) in `agents/scraper_agent.py`
- [x] Wire LLM Resume Judge (`evaluate_resume_against_job`) into `agents/career_agent.py`
- [x] Security & Multi-User Isolation Test Suite (`tests/test_security.py`)
- [x] Create `storage/db.py` with SQLAlchemy 2.0 models & `Vector(768)` `cosine_distance` RAG query methods
- [x] Multi-User Isolation: Generate client session UUID (`disha_user_id`) in `frontend/hooks/useProfile.ts`
- [x] Synchronize initial `userId` state in `useProfile.ts` with `getOrGenerateUserId` to prevent memory desync
- [x] Next.js 14 Production Build Verification (`npm run build` passed)
- [x] Backend Production Dockerfile (`Dockerfile`) with Playwright Chromium support
- [x] Database Initialization Script (`storage/init_db.py`)
- [x] Frontend Standalone Production Dockerfile (`frontend/Dockerfile`)
- [x] Production Docker Compose configuration (`docker-compose.prod.yml`)
- [x] Production Environment Variable Template (`.env.example`)
- [x] Production Deployment Guide (`docs/deployment.md`)
- [x] Firecrawl Cloud Scraper Integration (`tools/firecrawl_tools.py`)
- [x] Firecrawl Web Search Integration in `agents/scraper_agent.py`
- [x] Firecrawl Test Suite (`tests/test_firecrawl.py`)
- [x] GitHub Actions Keep-Alive Workflow (`.github/workflows/keep_alive.yml`)

---

## Crucial Issues & Feature Roadmap (Logged for Next Sprint)

- [ ] **1. Frontend Agent Execution Visualization & Live Sub-Step Progress:**
  - Build real-time agent workflow visualizer in Next.js UI (`Supervisor → Scraper → Career Strategy → Synthesize`).
  - Stream fine-grained sub-step progress logs via SSE (e.g. *"Scraping Greenhouse (PhonePe)..."*, *"Firecrawl web search..."*, *"Evaluating resume against 25 roles..."*) instead of static *"Planning new steps..."*.
  - Show interactive agent state badges, active scraper sources, and step timings.

- [ ] **2. Targeted Company Query Routing (e.g., "Sarvam AI new postings"):**
  - Update `agents/scraper_agent.py` and `agents/supervisor_agent.py` to extract company intent from queries.
  - Dynamically trigger Firecrawl search/scrape for specified companies (e.g. Sarvam AI, Krutrim, PhysicsWallah) instead of relying solely on hardcoded ATS board lists.

- [ ] **3. Scraper Parallelization & Speed Optimization:**
  - Refactor `agents/scraper_agent.py` to execute Greenhouse, Lever, WWR, and YC scrapes in parallel via `asyncio.gather()`.
  - Target scrape time reduction from 120s+ to under 15s.

- [ ] **4. Async Playwright Migration:**
  - Convert remaining `sync_playwright()` usages in `tools/scraper_tools.py` to `async_playwright()` to eliminate event loop warnings in FastAPI.
