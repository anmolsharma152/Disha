# Disha Comprehensive Master Implementation & Architectural Plan

This document serves as the authoritative, all-inclusive master technical design and implementation blueprint for **Disha**. It preserves all technical implementation details across security, graph routing, pgvector storage, multi-tenant isolation, deployment, Firecrawl scraping, product management vision, Claude-style UI/UX visualization, and dynamic resume-derived experience boundaries.

---

## Table of Contents
1. [Target Product Vision & UX Architecture](#1-target-product-vision--ux-architecture)
2. [Work Stream 1: Security Hardening & Zero-Trust Verification](#stream-1-security-hardening--zero-trust-verification)
3. [Work Stream 2: Core Graph, LLM Resume Judge & pgvector RAG](#stream-2-core-graph-llm-resume-judge--pgvector-rag)
4. [Work Stream 3: Multi-User Isolation & Tenant Memory Binding](#stream-3-multi-user-isolation--tenant-memory-binding)
5. [Work Stream 4: Firecrawl Cloud Ingestion & Site Mapping](#stream-4-firecrawl-cloud-ingestion--site-mapping)
6. [Work Stream 5: Production Deployment & Hybrid Keep-Alive Architecture](#stream-5-production-deployment--hybrid-keep-alive-architecture)
7. [Work Stream 6: Claude-Style Agent Execution Visualizer & Multi-Turn Chat UI](#stream-6-claude-style-agent-execution-visualizer--multi-turn-chat-ui)
8. [Work Stream 7: Dynamic Resume-Derived Experience Boundaries (Zero Hardcoding)](#stream-7-dynamic-resume-derived-experience-boundaries-zero-hardcoding)
9. [Work Stream 8: Sub-15s Performance Pipeline & Parallel Scrapers](#stream-8-sub-15s-performance-pipeline--parallel-scrapers)
10. [Comprehensive Verification & Test Plan](#10-comprehensive-verification--test-plan)

---

## 1. Target Product Vision & UX Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISHA - CONVERSATIONAL CAREER & MARKET OS                │
└─────────────────────────────────────────────────────────────────────────────┘
  │
  ├─ 1. Zero Cold-Start & Flexible Onboarding
  │   ├─ Instant Chat Mode (works without resume upload upfront)
  │   └─ Drag & Drop Resume Upload (instantly grounds memory & experience boundary)
  │
  ├─ 2. Intent-Based Dual Routing
  │   ├─ Conversational Query Intent → Instant Synthesis / Web Search (< 3s)
  │   └─ Job Discovery Intent → Parallel Scraper + Firecrawl + Career Match (< 12s)
  │
  ├─ 3. Sub-15s Performance Pipeline
  │   ├─ Concurrently fetch scrapers via asyncio.gather()
  │   └─ 6-hour Tiered Cache for instant repeat searches (< 1s)
  │
  ├─ 4. Claude-Style Agent Execution Visualizer & Chat Feed
  │   ├─ Animated spinners, timers (00:04s), and sub-step status streams
  │   ├─ Expandable "Thinking / Progress Log" drawers
  │   └─ Persistent Multi-Turn Conversation Thread (ChatFeed.tsx)
  │
  └─ 5. Production Infrastructure & Security
      ├─ Dockerized FastAPI + Next.js 14 Standalone (Vercel + Render + Supabase)
      ├─ UptimeRobot (Primary 5m) + GitHub Actions keep_alive.yml (Secondary 14m)
      └─ Zero-Trust Security (SSRF guards, path validation, prompt injection tags)
```

---

## Stream 1: Security Hardening & Zero-Trust Verification

### 1. SSRF Protection & URL Validation
- **Module:** [`tools/scraper_tools.py`](file:///home/anmol/Projects/Disha/tools/scraper_tools.py)
- **Implementation:** Added `is_safe_url(url)` validator using Python's `ipaddress` library.
- **Rule:** Blocks non-HTTP/HTTPS schemes and restricts access to private/internal IP ranges (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254` AWS metadata, `192.168.0.0/16`). Pydantic input models (`FetchRSSInput`, `PlaywrightScrapeInput`, `FirecrawlScrapeInput`) validate URLs before network dispatch.

### 2. Path Traversal & Board Slug Guard
- **Module:** [`tools/scraper_tools.py`](file:///home/anmol/Projects/Disha/tools/scraper_tools.py)
- **Implementation:** Added `validate_board_slug(slug)` enforcing regex `^[a-zA-Z0-9_-]+$`. Prevents directory traversal attacks in Greenhouse and Lever slug inputs.

### 3. Restricted CORS & Token Bucket Rate Limiting
- **Module:** [`api/server.py`](file:///home/anmol/Projects/Disha/api/server.py)
- **Implementation:** Restricted CORS `allow_origins` to `ALLOWED_ORIGINS` env var (defaulting to `http://localhost:3000`). Added `check_rate_limit(client_id)` token bucket middleware capping chat endpoints at 30 requests/minute per client.

### 4. Anti-Jailbreak Prompt Injection Tags
- **Module:** [`tools/career_tools.py`](file:///home/anmol/Projects/Disha/tools/career_tools.py)
- **Implementation:** Wrapped untrusted raw job descriptions and candidate resumes inside `<job_description>` and `<candidate_resume>` XML tags with explicit anti-jailbreak system boundary instructions.

---

## Stream 2: Core Graph, LLM Resume Judge & pgvector RAG

### 1. Error Recovery Node Edge
- **Module:** [`agents/scraper_agent.py`](file:///home/anmol/Projects/Disha/agents/scraper_agent.py) & [`main.py`](file:///home/anmol/Projects/Disha/main.py)
- **Implementation:** Updated empty scrape run handlers to set `state["routing_key"] = "error_recovery"`, triggering `node_error_recovery` in the LangGraph state machine.

### 2. LLM Resume Judge Integration
- **Module:** [`agents/career_agent.py`](file:///home/anmol/Projects/Disha/agents/career_agent.py)
- **Implementation:** Wired `evaluate_resume_against_job` into `node_career_strategy`. Automatically evaluates top matching roles against candidate resume text using Gemini 2.5 Flash.

### 3. PostgreSQL + pgvector ORM & RAG Storage
- **Module:** [`storage/db.py`](file:///home/anmol/Projects/Disha/storage/db.py)
- **Implementation:** Built async SQLAlchemy 2.0 ORM models (`JobOpeningModel`, `DocumentChunkModel`) with `Vector(768)` embedding columns and native `cosine_distance` (`<=>`) vector similarity queries.

---

## Stream 3: Multi-User Isolation & Tenant Memory Binding

### 1. Client Session UUID Token
- **Module:** [`frontend/hooks/useProfile.ts`](file:///home/anmol/Projects/Disha/frontend/hooks/useProfile.ts)
- **Implementation:** Added `getOrGenerateUserId()` generating unique client session tokens stored in `localStorage.disha_user_id` (`usr_...`). Synchronized initial state to avoid cold-start memory desync.

### 2. Request Body User Binding
- **Module:** [`frontend/hooks/useChat.ts`](file:///home/anmol/Projects/Disha/frontend/hooks/useChat.ts)
- **Implementation:** Passed `user_id` in every SSE POST request body to `/api/chat/stream`, ensuring zero cross-tenant memory leakage.

---

## Stream 4: Firecrawl Cloud Ingestion & Site Mapping

### 1. Firecrawl SDK Tool Wrapper
- **Module:** [`tools/firecrawl_tools.py`](file:///home/anmol/Projects/Disha/tools/firecrawl_tools.py)
- **Implementation:** Built LangChain-compatible tools wrapping `firecrawl-py`:
  - `fetch_webpage_firecrawl`: Scraping JS-rendered career pages into clean Markdown.
  - `extract_job_firecrawl`: Direct JSON Schema extraction of `JobOpening` dicts.
  - `map_company_careers_firecrawl`: Mapping company `/careers/*` sub-URLs via `firecrawl.map_url()`.
  - `search_jobs_firecrawl`: Multi-source web search via `firecrawl.search()`.

### 2. Scraper Agent Web Search Integration
- **Module:** [`agents/scraper_agent.py`](file:///home/anmol/Projects/Disha/agents/scraper_agent.py)
- **Implementation:** Added `_fetch_firecrawl_search` to `node_scraper` for automatic web-wide job discovery when `FIRECRAWL_API_KEY` is present.

---

## Stream 5: Production Deployment & Hybrid Keep-Alive Architecture

### 1. Production Artifacts
- **Backend `Dockerfile`:** Python 3.12 + system dependencies + Playwright Chromium.
- **Frontend `Dockerfile`:** Multi-stage Next.js 14 production build (`output: "standalone"`).
- **`docker-compose.prod.yml`:** Multi-container orchestration (`db` pgvector, `backend`, `frontend`).
- **`.env.example`:** Production configuration schema.
- **`docs/deployment.md`:** Comprehensive deployment guide for Vercel, Render, Supabase, and single VPS Docker Compose.

### 2. Hybrid Keep-Alive Strategy
- **Primary:** **UptimeRobot** 5-minute HTTP monitor targeting `https://disha-api.onrender.com/health` (prevents Render 15-min sleep & alerts on downtime).
- **Secondary Backup:** **GitHub Actions Workflow** ([`.github/workflows/keep_alive.yml`](file:///home/anmol/Projects/Disha/.github/workflows/keep_alive.yml)) executing `curl` crons every 14 minutes against Render and Supabase.

---

## Stream 6: Claude-Style Agent Execution Visualizer & Multi-Turn Chat UI

### 1. Live Activity Cards & Sub-Step SSE Streaming
- **Module:** [`api/server.py`](file:///home/anmol/Projects/Disha/api/server.py) & [`frontend/components/chat/AgentExecutionVisualizer.tsx`](file:///home/anmol/Projects/Disha/frontend/components/chat/AgentExecutionVisualizer.tsx)
- **Implementation:**
  - Update SSE event generator to stream sub-step progress logs (e.g. `{"type": "substep", "agent": "scraper", "message": "Searching Firecrawl for Sarvam AI...", "timestamp": "00:04s"}`).
  - Render pipeline stage indicators (`Supervisor → Scraper → Career Strategy → Guardrails → Synthesize`).
  - Add animated spinning wheels, hourglass icons, real-time timers, and expandable "Thinking & Tool Activity" drawers.

### 2. Multi-Turn Conversational Chat Feed
- **Module:** [`frontend/components/chat/ChatFeed.tsx`](file:///home/anmol/Projects/Disha/frontend/components/chat/ChatFeed.tsx)
- **Implementation:** Replace single-run sidebar output with a scrollable chat thread rendering user prompt bubbles, assistant text responses, and embedded Job Cards chronologically.

---

## Stream 7: Dynamic Resume-Derived Experience Boundaries (Zero Hardcoding)

### 1. Dynamic Resume Extraction
- **Module:** [`tools/career_tools.py`](file:///home/anmol/Projects/Disha/tools/career_tools.py)
- **Implementation:** LLM resume extraction derives `experience_years` (e.g. 3.1 yrs) and candidate `seniority_level` (`entry`, `mid`, `senior`, `principal`).

### 2. Adaptive Experience Boundary Computation
- **Module:** [`agents/career_agent.py`](file:///home/anmol/Projects/Disha/agents/career_agent.py)
- **Implementation:** Compute experience range `[exp_years - 1.5, exp_years + 2.5]` dynamically from candidate profile:
  - For a 3.1-year experience profile: Allowed range `1.6` to `5.6` years. Automatically filter out `Senior Staff`, `Principal`, `Director`, `VP`, `Chief of Staff`.
  - For a 14-year experience profile: Allowed range `12.5` to `16.5+` years. Automatically filter out `Intern`, `SDE-1`, `Junior Developer`.
- Apply score penalty for job openings requiring experience outside the computed candidate boundary.

---

## Stream 8: Sub-15s Performance Pipeline & Parallel Scrapers

### 1. Parallel Scraper Engine (`asyncio.gather`)
- **Module:** [`agents/scraper_agent.py`](file:///home/anmol/Projects/Disha/agents/scraper_agent.py)
- **Implementation:** Refactor serial scraper loop to execute Greenhouse, Lever, WWR RSS, YC, and Firecrawl searches concurrently using `asyncio.gather()`. Reduce total scrape execution time from 120s+ to under 12s.

### 2. Response Caching
- **Module:** [`tools/job_cache.py`](file:///home/anmol/Projects/Disha/tools/job_cache.py)
- **Implementation:** 6-hour disk/memory cache for raw job board listings to serve instant repeat queries in < 1s.

---

## 10. Comprehensive Verification & Test Plan

1. **Security Suite:** `PYTHONPATH=. .venv/bin/pytest tests/test_security.py` (SSRF, board slug, multi-user isolation).
2. **Firecrawl Suite:** `PYTHONPATH=. .venv/bin/pytest tests/test_firecrawl.py`.
3. **Seniority Guardrails Test:** Verify candidate with 3.1 yrs experience profile filters out Senior Staff and Director roles.
4. **Sub-15s Speed Test:** Benchmark parallel scraper timing under 12s.
5. **Claude Visualizer & Chat Feed Test:** Verify Next.js build (`npm run build`) and test multi-turn chat feed with live timers.
