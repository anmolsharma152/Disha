# Disha Master Integrated Implementation & Architecture Plan

This master document consolidates all planned and active work streams for Disha — combining security, core graph logic, multi-tenant isolation, production deployment, Firecrawl cloud scraping, experience-level guardrails, zero-hardcoding audits, and Claude-style live agent visualization.

---

## 1. Unified Architectural Work Streams

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DISHA ARCHITECTURE & UX PIPELINE                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                  1. Multi-Tenant Session & Zero-Trust Security
                  ├─ Strict session UUID (disha_user_id) per browser
                  ├─ SSRF (is_safe_url) & Path Traversal Guard
                  └─ Prompt Injection (<untrusted_content> XML)
                                       │
                                       ▼
                  2. Dynamic Scraper & Firecrawl Ingestion Layer
                  ├─ ATS JSON APIs (Greenhouse & Lever)
                  ├─ Firecrawl Cloud API (search, map_url, scrape)
                  ├─ Targeted Company Query Extraction (e.g. Sarvam AI)
                  └─ Parallel Fetching via asyncio.gather() (< 15s)
                                       │
                                       ▼
                  3. Experience Seniority Guardrails & Matching
                  ├─ Parse candidate experience_years (e.g. 3.1 yrs)
                  ├─ Filter out Senior Staff, Principal, Director, VP
                  └─ LLM Resume Judge (evaluate_resume_against_job)
                                       │
                                       ▼
                  4. Claude-Style Agent Visualizer & Chat Feed UI
                  ├─ Spinning wheels / timers / hourglasses per agent step
                  ├─ Real-time sub-step status stream (SSE logs)
                  ├─ Expandable "Thinking / Progress Log" drawers
                  └─ Multi-Turn Conversational Chat Feed (ChatFeed.tsx)
                                       │
                                       ▼
                  5. Production Deployment & Hybrid Keep-Alive
                  ├─ Dockerized FastAPI + Next.js 14 Standalone
                  ├─ Supabase (pgvector) + Render (Docker Web Service)
                  └─ UptimeRobot (Primary 5m) + GitHub Actions (Secondary)
```

---

## Stream 1: Claude-Style Agent Visualization & Multi-Turn Chat Feed (Frontend UX)

### Objectives:
- **Live Activity Drawers & Timers:** Replace static *"Planning new steps..."* text with animated spinners, timers (`00:04s`), and live status summaries showing exactly what the agent is doing at any point (similar to Claude / ChatGPT thinking drops).
- **Multi-Turn Chat Feed (`ChatFeed.tsx`):** Transform single-run dashboard into a true conversational thread where past user prompts, agent text responses, and job artifacts remain visible in a scrollable message history feed.

### Key Components:
- **[NEW] [frontend/components/chat/AgentExecutionVisualizer.tsx](file:///home/anmol/Projects/Disha/frontend/components/chat/AgentExecutionVisualizer.tsx):**
  - Displays pipeline stages: `Supervisor → Scraper → Career Strategy → Guardrails → Synthesize`.
  - Shows spinning wheels / hourglass icons and real-time timers for active agents.
  - Expandable drawer containing live sub-step logs:
    - `⏳ [Scraper] Searching Firecrawl for 'Sarvam AI new postings'... (00:03s)`
    - `⏳ [Scraper] Ingesting 28 jobs from Y Combinator WorkAtAStartup... (00:06s)`
    - `⏳ [Career Strategy] Evaluating candidate profile (~3.1 yrs exp) against 25 openings... (00:09s)`
- **[NEW] [frontend/components/chat/ChatFeed.tsx](file:///home/anmol/Projects/Disha/frontend/components/chat/ChatFeed.tsx):**
  - Renders user prompt bubbles and assistant message turns chronologically.
  - Embeds interactive artifact panels (Top Matches Grid, Summary, All Openings) inside assistant response blocks.

---

## Stream 2: Experience Seniority Guardrails & Title Matching

### Objectives:
- Eliminate irrelevant senior-level listings (*"Senior Staff Software Engineer"*, *"Director"*, *"Chief of Staff"*) for candidates with junior/mid-level experience.

### Key Rules:
- **Candidate Experience Extraction:** Automatically derive `experience_years` from uploaded resume or profile (e.g. 3.1 years).
- **Seniority Exclusion Filter:**
  - If `candidate.experience_years < 5.0`: Automatically exclude titles containing `Senior Staff`, `Staff Engineer`, `Principal`, `Director`, `Vice President`, `VP`, `Head of`, `Chief of Staff`, `Lead (10+ yrs)`.
  - Target matching roles: `AI Engineer`, `Machine Learning Engineer`, `Software Development Engineer II (SDE-2)`, `Associate AI Engineer`, `Applied AI Specialist`.
- **Career Agent Score Penalty:** Apply heavy penalty in `agents/career_agent.py` for jobs requiring experience > 2 years above the candidate's current profile.

---

## Stream 3: Zero Hardcoding & Complete Context Audit

### Objectives:
- Re-audit the entire codebase to guarantee **100% dynamic, user-agnostic execution**. Zero hardcoded preferences, zero hardcoded company assumptions.

### Audit Checklist:
- **`profiles/default.yaml`**: Standardize on empty fallback defaults (`skills: []`, `target_cities: []`).
- **`tools/profile.py`**: Enforce preference resolution priority: `state["user_profile"]` (request) → `user_memory_{user_id}.json` (user session) → `profiles/default.yaml` (empty product defaults).
- **Tenant Isolation:** Ensure `user_id` is consistently passed from Next.js client (`disha_user_id`) to all backend endpoints (`/api/profile`, `/api/profile/resume`, `/api/chat/stream`).

---

## Stream 4: Targeted Company Query Extraction & Firecrawl Ingestion

### Objectives:
- Resolve queries targeting specific companies (*"Sarvam AI new postings"*, *"PhonePe job openings"*) dynamically instead of scraping generic hardcoded board lists.

### Implementation:
- **Company Intent Extractor:** Update `agents/supervisor_agent.py` and `agents/scraper_agent.py` to extract company names from queries.
- **Firecrawl Targeted Ingestion:** For specific company queries, bypass generic boards and execute `firecrawl.search("Sarvam AI jobs India")` or `firecrawl.map_url("https://www.sarvam.ai/careers")`.
- **Parallel Scraper Execution:** Refactor `agents/scraper_agent.py` to run board scrapers concurrently via `asyncio.gather()`, cutting scrape times from 120s+ to under 15s.

---

## Stream 5: Production Deployment & Hybrid Keep-Alive Architecture

### Objectives:
- Maintain 24/7 production deployment using managed PaaS services and robust uptime monitoring.

### Architecture:
- **Frontend:** Next.js 14 App deployed on **Vercel** (`output: "standalone"`).
- **Backend API:** FastAPI + LangGraph containerized on **Render** (Docker Web Service with Playwright Chromium).
- **Database:** Managed PostgreSQL + `pgvector` on **Supabase** (`storage/db.py` ORM with 768d cosine distance queries).
- **Hybrid Keep-Alive Strategy:**
  - **Primary:** **UptimeRobot** 5-minute HTTP monitor hitting `https://disha-api.onrender.com/health` (keeps Render warm & alerts on downtime).
  - **Secondary:** **GitHub Actions Workflow** ([`.github/workflows/keep_alive.yml`](file:///home/anmol/Projects/Disha/.github/workflows/keep_alive.yml)) executing `curl` crons every 14 minutes.

---

## Stream 6: Security Hardening & Zero-Trust Defense

### Completed Defenses:
- **SSRF Protection:** `is_safe_url()` blocking private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`).
- **Path Traversal Guard:** `validate_board_slug()` enforcing regex `^[a-zA-Z0-9_-]+$`.
- **CORS & Rate Limiting:** `ALLOWED_ORIGINS` CORS restrictions and token bucket rate limiter (`check_rate_limit()`).
- **Prompt Injection Defense:** `<job_description>` and `<candidate_resume>` XML tag framing in `tools/career_tools.py`.

---

## 2. Verification & Testing Plan

1. **Seniority Guardrail Verification:** Run query with 3.1 yrs experience profile and verify `Senior Staff`, `Director`, and `Chief of Staff` roles are filtered out.
2. **Claude-Style Visualizer Verification:** Test timers, spinners, and expandable thinking drawers during live chat streams.
3. **Multi-Turn Chat Feed Verification:** Verify previous conversation turns remain visible in the UI history.
4. **Targeted Scrape Verification:** Query *"Sarvam AI new postings"* and verify Firecrawl fetches Sarvam AI job listings.
5. **Full Test Suite:**
   ```bash
   PYTHONPATH=. .venv/bin/pytest tests/
   ```

---

## User Review Required

Please review this master integrated plan covering all 6 architectural streams. Once approved, implementation will proceed systematically across backend guardrails and frontend visualization!
