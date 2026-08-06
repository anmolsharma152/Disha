# Disha Master Implementation Task List

## Stream 1: Security & Multi-User Memory Isolation (Completed)
- [x] SSRF Protection & URL Validation (`is_safe_url`) in `tools/scraper_tools.py`
- [x] Path Traversal Regex Validation (`validate_board_slug`) in `tools/scraper_tools.py`
- [x] Restrict CORS `ALLOWED_ORIGINS` in `api/server.py`
- [x] Rate Limiting Middleware (`check_rate_limit`) on `/api/chat` endpoints in `api/server.py`
- [x] Prompt Injection Framing (<untrusted_content> XML tags) in `tools/career_tools.py`
- [x] Security & Multi-User Isolation Test Suite (`tests/test_security.py`)
- [x] Multi-User Isolation: Generate client session UUID (`disha_user_id`) in `frontend/hooks/useProfile.ts`
- [x] Synchronize initial `userId` state in `useProfile.ts` with `getOrGenerateUserId` to prevent memory desync

## Stream 2: Core Graph, LLM Resume Judge & pgvector (Completed)
- [x] Wire Error Recovery Node routing (`state["routing_key"] = "error_recovery"`) in `agents/scraper_agent.py`
- [x] Wire LLM Resume Judge (`evaluate_resume_against_job`) into `agents/career_agent.py`
- [x] Create `storage/db.py` with SQLAlchemy 2.0 models & `Vector(768)` `cosine_distance` RAG query methods

## Stream 3: Cloud Ingestion & Firecrawl Integration (Completed)
- [x] Firecrawl Cloud Scraper Integration (`tools/firecrawl_tools.py`)
- [x] Firecrawl Web Search Integration in `agents/scraper_agent.py`
- [x] Firecrawl Test Suite (`tests/test_firecrawl.py`)

## Stream 4: Production Deployment & Keep-Alive (Completed)
- [x] Backend Production Dockerfile (`Dockerfile`) with Playwright Chromium support
- [x] Database Initialization Script (`storage/init_db.py`)
- [x] Frontend Standalone Production Dockerfile (`frontend/Dockerfile`)
- [x] Production Docker Compose configuration (`docker-compose.prod.yml`)
- [x] Production Environment Variable Template (`.env.example`)
- [x] Production Deployment Guide (`docs/deployment.md`)
- [x] GitHub Actions Keep-Alive Workflow (`.github/workflows/keep_alive.yml`)

---

## Active & Upcoming Implementation Work Streams

- [ ] **Stream 5: Dynamic Resume-Derived Experience Boundaries (Zero Hardcoding):**
  - Parse candidate's experience years (e.g. 3.1 yrs) & seniority level from ingested resume (`tools/career_tools.py`).
  - Compute dynamic experience boundary (`[exp_years - 1.5, exp_years + 2.5]` yrs).
  - Dynamically filter and penalize roles outside candidate's ingested boundary in `agents/career_agent.py`.

- [ ] **Stream 6: Claude-Style Agent Visualization & Timers (Frontend UX):**
  - Build `AgentExecutionVisualizer.tsx` with animated spinning wheels, timers (`00:05s`), and hourglasses.
  - Stream fine-grained sub-step progress logs via SSE (`"Scraping PhonePe..."`, `"Evaluating 25 roles..."`).
  - Add expandable "Thinking & Tool Log" drawers for full transparency.

- [ ] **Stream 7: Multi-Turn Conversational Chat Feed (Frontend UX):**
  - Build `ChatFeed.tsx` in Next.js UI to preserve multi-turn message history threads.
  - Render user prompt bubbles, assistant text responses, and attached job artifacts in a scrollable chat stream.

- [ ] **Stream 8: Targeted Company Query Extraction (e.g. "Sarvam AI new postings"):**
  - Extract company intent from user queries (*Sarvam AI, Krutrim, PhysicsWallah*) in `agents/supervisor_agent.py`.
  - Trigger targeted Firecrawl search/scrape for specified companies instead of hardcoded default board lists.

- [ ] **Stream 9: Scraper Parallelization & Speed Optimization:**
  - Refactor `agents/scraper_agent.py` to execute board scrapes concurrently via `asyncio.gather()`, cutting scrape times from 120s+ to < 15s.

- [ ] **Stream 10: Complete Codebase Zero-Hardcoding Audit:**
  - Re-audit all tools, prompts, default profiles, and parameters to ensure 100% dynamic user-driven execution with zero hardcoded assumptions.
