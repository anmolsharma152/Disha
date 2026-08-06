# Disha Master Integrated Implementation & Architecture Plan

This master document consolidates all planned and active work streams for Disha — combining security, core graph logic, multi-tenant isolation, production deployment, Firecrawl cloud scraping, dynamic resume-derived experience boundaries, zero-hardcoding audits, and Claude-style live agent visualization.

---

## 1. Unified Architectural Work Streams

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DISHA MASTER INTEGRATED PIPELINE                      │
└─────────────────────────────────────────────────────────────────────────────┘
  │
  ├─ 1. Multi-Tenant Session & Zero-Trust Security
  │   ├─ Strict session UUID (disha_user_id) per browser
  │   ├─ SSRF (is_safe_url) & Path Traversal Guard
  │   └─ Prompt Injection (<untrusted_content> XML)
  │
  ├─ 2. Dynamic Resume-Derived Experience Boundaries (ZERO HARDCODING)
  │   ├─ Ingest candidate experience_years & seniority_level dynamically from resume
  │   ├─ Compute dynamic experience boundary: (e.g. [exp - 1.5, exp + 2.5] yrs)
  │   └─ Adaptively filter/penalize titles out of candidate's ingested boundary
  │
  ├─ 3. Dynamic Scraper & Firecrawl Ingestion Layer
  │   ├─ ATS JSON APIs (Greenhouse & Lever)
  │   ├─ Firecrawl Cloud API (search, map_url, scrape)
  │   ├─ Targeted Company Query Extraction (e.g. Sarvam AI)
  │   └─ Parallel Fetching via asyncio.gather() (< 15s)
  │
  ├─ 4. Claude-Style Agent Visualizer & Multi-Turn Chat Feed (Frontend UX)
  │   ├─ Spinning wheels / timers / hourglasses (00:04s) per step
  │   ├─ Real-time sub-step status stream (SSE logs)
  │   ├─ Expandable "Thinking / Progress Log" drawers
  │   └─ Multi-Turn Conversational Chat Feed (ChatFeed.tsx)
  │
  └─ 5. Production Deployment & Hybrid Keep-Alive Architecture
      ├─ Dockerized FastAPI + Next.js 14 Standalone (Vercel + Render + Supabase)
      └─ UptimeRobot (Primary 5m) + GitHub Actions keep_alive.yml (Secondary)
```

---

## Stream 1: Dynamic Resume-Derived Experience Boundaries (Zero Hardcoding)

### Objectives:
- Eliminate hardcoded experience thresholds. Experience boundaries are **computed dynamically from the candidate's ingested resume**.

### Dynamic Ingestion & Boundary Logic:
1. **Resume Ingestion (`tools/career_tools.py`):**
   * During LLM resume extraction, extract:
     * `experience_years`: Total professional years (e.g. 3.1 yrs, 1.0 yrs, or 12.0 yrs).
     * `seniority_level`: Derived candidate level (`entry`, `mid`, `senior`, `principal`).
2. **Dynamic Boundary Computation:**
   * Compute dynamic experience range: `[exp_years - 1.5, exp_years + 2.5]` years.
   * If a candidate with 3.1 years experience uploads their resume:
     * Allowed Range: `1.6` to `5.6` years.
     * Dynamic Title Exclusions: Senior Staff, Principal, Director, VP, Chief of Staff (automatically filtered out).
   * If a candidate with 14 years experience uploads their resume:
     * Allowed Range: `12.5` to `16.5+` years.
     * Dynamic Title Exclusions: Intern, SDE-1, Junior Developer (automatically filtered out).
3. **Career Agent Penalty (`agents/career_agent.py`):**
   * Dynamically penalize job openings whose experience requirements fall outside the candidate's ingested boundary.

---

## Stream 2: Claude-Style Agent Visualization & Multi-Turn Chat Feed (Frontend UX)

### Objectives:
- **Live Activity Drawers & Timers:** Replace static *"Planning new steps..."* text with animated spinners, timers (`00:04s`), and live status summaries showing exactly what the agent is doing at any point (similar to Claude / ChatGPT thinking drops).
- **Multi-Turn Chat Feed (`ChatFeed.tsx`):** Transform single-run dashboard into a true conversational thread where past user prompts, agent text responses, and job artifacts remain visible in a scrollable message history feed.

### Key Components:
- **[NEW] [frontend/components/chat/AgentExecutionVisualizer.tsx](file:///home/anmol/Projects/Disha/frontend/components/chat/AgentExecutionVisualizer.tsx):**
  - Displays pipeline stages: `Supervisor → Scraper → Career Strategy → Guardrails → Synthesize`.
  - Shows spinning wheels / hourglass icons and real-time timers for active agents.
  - Expandable drawer containing live sub-step logs:
    - `⏳ [Scraper] Searching Firecrawl for 'Sarvam AI new postings'... (00:03s)`
    - `⏳ [Career Strategy] Computing candidate experience boundary (3.1 yrs)... (00:06s)`
    - `⏳ [Career Strategy] Evaluating candidate profile against 25 openings... (00:09s)`
- **[NEW] [frontend/components/chat/ChatFeed.tsx](file:///home/anmol/Projects/Disha/frontend/components/chat/ChatFeed.tsx):**
  - Renders user prompt bubbles and assistant message turns chronologically.
  - Embeds interactive artifact panels (Top Matches Grid, Summary, All Openings) inside assistant response blocks.

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

1. **Dynamic Seniority Guardrail Verification:** Test candidate with 3.1 yrs vs 12 yrs and verify experience boundaries adapt dynamically to ingested resume.
2. **Claude-Style Visualizer Verification:** Test timers, spinners, and expandable thinking drawers during live chat streams.
3. **Multi-Turn Chat Feed Verification:** Verify previous conversation turns remain visible in the UI history.
4. **Targeted Scrape Verification:** Query *"Sarvam AI new postings"* and verify Firecrawl fetches Sarvam AI job listings.
5. **Full Test Suite:**
   ```bash
   PYTHONPATH=. .venv/bin/pytest tests/
   ```

---

## User Review Required

Please review this updated master plan. Experience boundaries are now fully dynamic and derived directly from ingested candidate resumes!
