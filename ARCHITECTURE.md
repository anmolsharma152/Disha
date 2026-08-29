# Disha Architecture & Technical Design

This document details the system architecture, component interactions, design decisions, trade-offs, and security posture of **Disha** — the job market intelligence platform for India's AI/ML ecosystem.

---

## 1. System Overview & Product Scope

Disha automates the discovery, extraction, evaluation, and scoring of career opportunities in the Indian AI/ML engineering market against candidate resumes.

### Portfolio Boundaries
| Domain | Canonical Product | Boundary in Disha |
|---|---|---|
| Job Market Intelligence | **Disha** (This Project) | Scrapes roles, scores fit, computes skill/experience gaps, generates market roadmaps. |
| Operations & Task Triage | **Ozyman** | Email, Slack, GitHub PR triage, task dispatch. Disha exports listings; Ozyman executes outreach. |
| Study & Spaced Repetition | **Scholar-Loop** | FSRS, study digests. Disha identifies skill gaps; Scholar-Loop builds memory schedules. |
| Divergent Ideation | **IdeaForge** | Creative career pivot ideation. Disha provides structured skill data as input prompts. |

---

## 2. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend UI (Vercel / Docker)                 │
│   • Multi-Turn Chat Feed (ChatFeed.tsx)                                     │
│   • Claude-Style Agent Execution Visualizer (Live Timers & Thinking Logs)    │
│   • Resume Parsing & Profile Memory Panel (disha_user_id Session Token)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Server-Sent Events (SSE) / REST
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Gateway (Render / Docker)                 │
│   • Rate Limiter (Token Bucket: 30 req/min) & CORS Allowed Origins          │
│   • Dynamic Session Memory Resolution (storage/user_memory.py)              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   LangGraph Deterministic State Orchestrator                │
│                                                                             │
│   ┌──────────────┐     ┌──────────────┐     ┌───────────────────────────┐   │
│   │  Supervisor  │ ──► │ Scraper Agent│ ──► │   Career Strategy Agent   │   │
│   │     Node     │     │ (Multi-Source│     │ (LLM Judge + Dyn Boundary)│   │
│   └──────────────┘     └──────┬───────┘     └─────────────┬─────────────┘   │
│          ▲                    │                           │                 │
│          │ (Error Recovery)   ▼                           ▼                 │
│   ┌──────────────┐     ┌──────────────┐     ┌───────────────────────────┐   │
│   │Error Recovery│ ◄───│  Firecrawl / │     │ Guardrails & Filter Node  │   │
│   │     Node     │     │ ATS Ingestion│     │   (Visa, Seniority, Exp)  │   │
│   └──────────────┘     └──────────────┘     └─────────────┬─────────────┘   │
│                                                           │                 │
│                                                           ▼                 │
│                                             ┌───────────────────────────┐   │
│                                             │   Synthesis Node (Gemini) │   │
│                                             └───────────────────────────┘   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Storage & External Services                           │
│   • Google Gemini 2.5 Flash (Extraction, LLM Resume Judge, Synthesis)       │
│   • Firecrawl Cloud API (Dynamic JS Scraping, Site Mapping, Web Search)    │
│   • PostgreSQL + pgvector (Supabase: Vector(768) Cosine Similarity RAG)     │
│   • UptimeRobot (Primary 5m Keep-Alive) + GitHub Actions (Secondary Backup) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Subsystems

### 3.1 LangGraph State Orchestrator (`main.py`, `agents/`)
- **State Machine Schema (`AgentState`):** Tracks `user_query`, `job_openings`, `career_recommendations`, `user_profile`, `iteration`, `retry_count`, `routing_key`, and `final_answer`.
- **Deterministic Supervisor Routing:** Routing edges transition deterministically based on pipeline state (`supervisor -> scraper -> career_strategy -> guardrails -> synthesize -> end`). An intentional `error_recovery` edge handles empty scrape runs without unbounded LLM loops.
- **LLM Resume Judge:** Uses Gemini 2.5 Flash within `agents/career_agent.py` to evaluate candidate profile text against top job descriptions, extracting qualitative match insights, skill gaps, and interview prep suggestions.

### 3.2 Ingestion & Scraper Pipeline (`tools/scraper_tools.py`, `tools/firecrawl_tools.py`, `agents/scraper_agent.py`)
- **Multi-Source Ingestion Hierarchy:**
  1. **ATS JSON APIs:** Greenhouse (`boards-api.greenhouse.io`) and Lever (`jobs.lever.co`) structured endpoints.
  2. **Firecrawl Cloud API:** `firecrawl-py` SDK for dynamic JS-rendered career portals, sub-URL mapping (`firecrawl.map_url()`), and web-wide searches (`firecrawl.search()`).
  3. **Curated First-Class Boards:** We Work Remotely (WWR RSS) and Y Combinator (WorkAtAStartup).
  4. **Playwright Headless Browser:** Local Chromium fallback for custom portals without API access.
- **Parallel Scraper Engine:** Uses `asyncio.gather()` to fetch multiple boards concurrently, reducing total scrape time from 120s+ to under 15s.

### 3.3 Dynamic Resume-Derived Experience Boundaries
- **Zero-Hardcoding Principle:** Candidate experience is extracted dynamically during resume parsing (`experience_years`, `seniority_level`).
- **Dynamic Boundary Formula:**
  $$\text{Allowed Experience Range} = [\max(0, \text{exp\_years} - 1.5),\, \text{exp\_years} + 2.5]$$
- **Adaptive Seniority Filtering:**
  - Junior/Mid candidates (~3.1 YOE) automatically filter out `Senior Staff`, `Principal`, `Director`, `VP`, `Chief of Staff` roles.
  - Senior/Principal candidates (12+ YOE) automatically filter out `Intern`, `Junior`, `SDE-1` roles.
  - Out-of-boundary roles receive proportional score penalties in `agents/career_agent.py`.

### 3.4 Multi-Tenant Memory & Session Isolation (`storage/user_memory.py`, `frontend/hooks/useProfile.ts`)
- **Client Session Token:** Generated via `getOrGenerateUserId()` and stored in `localStorage.disha_user_id` (`usr_...`).
- **Backend Resolution Priority:**
  1. Request-time override (`state["user_profile"]`)
  2. Session memory file (`data/user_memory_{user_id}.json`)
  3. Fail-safe default memory (`data/user_memory_default.json`)
  4. Built-in product defaults (`profiles/default.yaml`, zero hardcoded skills)

### 3.5 Storage & Vector Search Layer (`storage/db.py`)
- **SQLAlchemy 2.0 Async ORM:**
  - `JobOpeningModel`: Structured job postings with `Vector(768)` embedding columns.
  - `DocumentChunkModel`: Knowledge base and resume chunks with vector embeddings.
- **pgvector Cosine Queries:** Native `<=>` cosine distance similarity search for fast RAG retrieval over persistent job archives.

---

## 4. Architectural Decisions & Trade-Offs

| Decision | Chosen Approach | Alternative Considered | Rationale / Trade-Off |
|---|---|---|---|
| **Supervisor Routing** | Deterministic State Machine | Autonomous LLM Router | **Deterministic wins:** Predictable cost, zero routing hallucination loops, sub-10ms routing overhead, strict pipeline guarantees. |
| **JS Web Scraping** | Firecrawl Cloud API + ATS APIs | Playwright-Only Docker | **Firecrawl wins:** Avoids heavy browser container overhead in production, handles anti-bot/Cloudflare, returns structured Markdown directly. Playwright kept as local fallback. |
| **Experience Boundaries** | Dynamic Resume-Derived Range | Static Rule Sets (e.g. `< 5 YOE`) | **Dynamic wins:** System seamlessly scales from fresh graduates (0 YOE) to Staff+ Engineers (15 YOE) without hardcoded edge cases. |
| **Keep-Alive Strategy** | Hybrid: UptimeRobot (Primary 5m) + GitHub Actions (Secondary 14m) | Cloud Run Minimum Instances | **Hybrid wins:** Keeps Render free tier and Supabase free tier warm 24/7 with zero cloud infrastructure cost. |
| **Frontend State Flow** | Multi-Turn Conversational Feed + Live Visualizer | Single-Run Overwrite Dashboard | **Feed wins:** Users can track conversational context, ask follow-up questions, and monitor real-time agent execution timers. |

---

## 5. Security Architecture & Zero-Trust Defenses

1. **SSRF Guard (`is_safe_url`):** Validates all scrape target URLs with `ipaddress` parsing. Blocks private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`) and AWS metadata endpoints (`169.254.169.254`).
2. **Path Traversal Guard (`validate_board_slug`):** Validates Greenhouse/Lever slugs against `^[a-zA-Z0-9_-]+$` to prevent directory traversal attacks.
3. **CORS & Rate Limiting:** Enforces `ALLOWED_ORIGINS` CORS whitelisting and a token bucket rate limiter (30 requests/minute per client IP/session).
4. **Prompt Injection Defense:** Wraps untrusted external job descriptions and resumes in `<job_description>` and `<candidate_resume>` XML tags with anti-jailbreak system boundary directives.

---

## 6. Production Deployment Model

- **Frontend:** Next.js 14 App Router on **Vercel** (`output: "standalone"`).
- **Backend:** FastAPI + LangGraph container on **Render** (Docker Web Service, `Dockerfile`).
- **Database:** Managed PostgreSQL + `pgvector` on **Supabase**.
- **CI/CD:** GitHub Actions workflow ([`.github/workflows/ci.yml`](./.github/workflows/ci.yml)) running Python 3.12 `pytest` and Next.js production compilation (`npm run build`) on every push.
