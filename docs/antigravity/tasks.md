# Disha Product & Engineering Task List

## Stream 1: Core Foundation & Multi-Tenant Security (Completed)
- [x] SSRF Protection & URL Validation (`is_safe_url`) in `tools/scraper_tools.py`
- [x] Path Traversal Regex Validation (`validate_board_slug`) in `tools/scraper_tools.py`
- [x] Restrict CORS `ALLOWED_ORIGINS` in `api/server.py`
- [x] Rate Limiting Middleware (`check_rate_limit`) on `/api/chat` endpoints in `api/server.py`
- [x] Prompt Injection Framing (<untrusted_content> XML tags) in `tools/career_tools.py`
- [x] Security & Multi-User Isolation Test Suite (`tests/test_security.py`)
- [x] Multi-User Isolation: Generate client session UUID (`disha_user_id`) in `frontend/hooks/useProfile.ts`
- [x] Synchronize initial `userId` state in `useProfile.ts` with `getOrGenerateUserId` to prevent memory desync

## Stream 2: Graph Architecture, LLM Resume Judge & Storage (Completed)
- [x] Wire Error Recovery Node routing (`state["routing_key"] = "error_recovery"`) in `agents/scraper_agent.py`
- [x] Wire LLM Resume Judge (`evaluate_resume_against_job`) into `agents/career_agent.py`
- [x] Create `storage/db.py` with SQLAlchemy 2.0 models & `Vector(768)` `cosine_distance` RAG query methods

## Stream 3: Ingestion & Deployment (Completed)
- [x] Firecrawl Cloud Scraper Integration (`tools/firecrawl_tools.py`)
- [x] Firecrawl Web Search Integration in `agents/scraper_agent.py`
- [x] Backend Production Dockerfile (`Dockerfile`) & Next.js Production Dockerfile (`frontend/Dockerfile`)
- [x] Production Docker Compose (`docker-compose.prod.yml`) & Environment Template (`.env.example`)
- [x] Production Deployment Guide (`docs/deployment.md`)
- [x] GitHub Actions Keep-Alive Workflow (`.github/workflows/keep_alive.yml`)

---

## Active Product & UX Work Streams (PM & UI/UX Director Blueprint)

- [ ] **Stream 4: Flexible Onboarding & Intent-Based Dual Routing:**
  - Support instant chat for new users without requiring upfront resume upload.
  - Route conversational queries (*"What skills do I need for Sarvam AI?"*) to instant synthesis (< 3s).
  - Route job discovery queries (*"Find AI roles at PhonePe"*) to parallel scraper pipeline (< 12s).

- [ ] **Stream 5: Sub-15s Performance Pipeline & Parallel Scrapers:**
  - Refactor `agents/scraper_agent.py` to fetch Greenhouse, Lever, WWR, and YC concurrently via `asyncio.gather()`.
  - Target total scrape time reduction from 120s+ to under 12s.

- [ ] **Stream 6: Claude-Style Live Agent Visualizer & Timers (Frontend UX):**
  - Build `AgentExecutionVisualizer.tsx` with animated spinning wheels, hourglasses, and live timers (`00:04s`).
  - Stream progress logs via SSE (`"Scraping PhonePe..."`, `"Evaluating 25 roles..."`).
  - Add expandable "Thinking & Tool Log" drawers for complete transparency.

- [ ] **Stream 7: Multi-Turn Conversational Chat Feed (Frontend UX):**
  - Build `ChatFeed.tsx` in Next.js UI to preserve multi-turn message history threads.
  - Render user prompt bubbles, assistant text responses, and attached job artifacts in a scrollable chat stream.

- [ ] **Stream 8: Dynamic Resume-Derived Experience Boundaries (Zero Hardcoding):**
  - Extract candidate experience years & seniority level dynamically from resume.
  - Compute dynamic experience boundary `[exp_years - 1.5, exp_years + 2.5]`.
  - Filter out Senior Staff/Director roles for junior candidates; filter out Intern roles for senior candidates.

- [ ] **Stream 9: Targeted Company Query Extraction (e.g. "Sarvam AI new postings"):**
  - Extract company intent from user queries in `agents/supervisor_agent.py`.
  - Trigger targeted Firecrawl search/scrape for specified companies instead of hardcoded default board lists.
