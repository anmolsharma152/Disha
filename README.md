# Disha 

### Description

Disha is a modular, agent-driven Personal Intelligence system designed to automate market intelligence and career strategy. Built for the India-centric tech landscape, it orchestrates specialized agents—Scraper, Financial, Career, Learning, and Reviewer—to convert noisy data into actionable, high-signal insights for AI/ML professionals.

### Key Pillars

- **Agentic Orchestration:** Supervisor-Specialist pattern with cyclic feedback loops.
- **India-Localized Intelligence:** Specialized extraction for Naukri, LinkedIn India, and tier-1 domestic company portals.
- **Production-Ready:** Async FastAPI backend, structured vector storage (pgvector), and decoupled UI.
- **Hyper-Personalized:** Embedded profile matching for IIT Mandi/Data Science specializations.

# Project Disha

> **Automated Market Intelligence & Career Optimization Platform** — _Disha_

A production-grade, multi-agent system built on **LangGraph** that autonomously scrapes corporate career pages and financial data, performs investment analysis, and matches opportunities against hyper-personalized user profiles — all orchestrated through a Supervisor pattern with cyclic state management. **Built for Anmol Sharma (IIT Mandi, Data Science & AI).**

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SUPERVISOR AGENT                                 │
│  Intent Analysis • Dynamic Delegation • Aggregation • Termination Guard    │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ routing_key (scraper | financial_analyst | career_strategy | learning_companion | synthesize | end)
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐         ┌───────────────┐         ┌──────────────────┐
│  SCRAPER      │         │  FINANCIAL    │         │  CAREER          │
│  AGENT        │         │  ANALYST      │         │  STRATEGY        │
│               │         │               │         │                  │
│ • Playwright  │         │ • Valuation   │         │ • Skill Match    │
│ • Beautiful-  │         │   (P/E,       │         │ • Comp Fit       │
│   Soup        │         │   EV/Rev)     │         │ • India Filter   │
│ • RSS Feeds   │         │ • Growth      │         │ • Remote/        │
│ • India       │         │ • Profit-     │         │   Visa Policy    │
│   Platforms   │         │   ability     │         │ • Priority       │
│   (Naukri,    │         │ • FCF Yield   │         │   Ranking        │
│   LinkedIn)   │         │ • Risk Flags  │         │                  │
└───────┬───────┘         └───────┬───────┘         └────────┬─────────┘
        │                         │                          │
        │                         │                          ▼
        │                         │                 ┌──────────────────┐
        │                         │                 │  LEARNING        │
        │                         │                 │  COMPANION       │
        │                         │                 │                  │
        │                         │                 │ • Gap Analysis   │
        │                         │                 │ • ArXiv Papers   │
        │                         │                 │ • Phase Roadmap  │
        │                         │                 │ • LLMOps/MLOps   │
        │                         │                 │ • Neuro-Symbolic │
        └─────────────────────────┼─────────────────┴────────┬─────────┘
                                  ▼                          ▼
                        ┌─────────────────────────────────────────────┐
                        │              SYNTHESIZE NODE                │
                        │  Final Answer • Citations • Confidence     │
                        └────────────────────┬────────────────────────┘
                                             ▼
                                  ┌────────────────────┐
                                  │        END         │
                                  └────────────────────┘
```

### Core Components

| Component              | Technology                              | Responsibility                                                                                                         |
| ---------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Supervisor**         | LangGraph + Pydantic                    | Orchestrates multi-agent workflow, manages cyclic state, enforces iteration limits (max 6)                             |
| **Scraper Agent**      | Playwright, BeautifulSoup, `feedparser` | Dynamic JS rendering, static parsing, RSS feeds, **India-focused platforms** (Naukri, LinkedIn India, company portals) |
| **Financial Analyst**  | Custom scoring engine                   | Valuation, growth, profitability, FCF yield, risk flags, investment thesis                                             |
| **Career Strategy**    | Skill-gap analysis, comp matching       | Tech stack extraction, **INR salary benchmarking**, India city/remote filtering, priority ranking                      |
| **Learning Companion** | Gap analysis + curated KB               | **Advanced ArXiv papers**, LLMOps/MLOps paradigms, neuro-symbolic AI, **skips intro syntax**                           |
| **Knowledge Base**     | PostgreSQL + `pgvector` (async)         | Vector search over jobs/resumes/papers, structured metrics, LangGraph checkpoints                                      |
| **API Gateway**        | FastAPI + SSE                           | Async `/api/v1/chat` & `/api/v1/chat/stream` endpoints                                                                 |
| **Frontend**           | Next.js 14 + Tailwind + Shadcn/UI       | Real-time chat, job dashboard, learning roadmap, analytics                                                             |

### State Management

- **`AgentState` (TypedDict)**: Complete conversation + data + routing + resilience state
- **Pydantic v2 Schemas**: `CompanyMetrics`, `JobOpening` with strict validation, computed properties
- **Checkpointing**: `MemorySaver` (dev) → `PostgresSaver` (prod) for persistence
- **Async SQLAlchemy 2.0**: Full async PostgreSQL with `pgvector` scaffolding for embeddings

---

## Roadmap (Updated 4-Phase Pipeline)

### Phase 1: Modular Multi-Agent Framework & Async Postgres + pgvector Pipeline ✅ **COMPLETE**

- [x] **Modular Agent Architecture** — `agents/` package with independent `scraper_agent`, `financial_agent`, `career_agent`, `supervisor_agent`, `learning_agent`
- [x] **FastAPI Async Gateway** — `api/server.py` with `/api/v1/chat` (sync) and `/api/v1/chat/stream` (SSE)
- [x] **Async PostgreSQL + pgvector Scaffold** — `storage/db.py` with SQLAlchemy 2.0 async, `CompanyMetrics`, `JobOpening`, `UserProfile`, `Resume`, `DocumentChunk` models with `ARRAY(Float)` embeddings (pgvector-ready)
- [x] **India Job Localization** — Hardcoded Naukri/LinkedIn India/Company portals, Bangalore/Delhi NCR/Pune/Hyderabad/Remote-India filters
- [x] **Pydantic Bug Fix** — `HttpUrl` → `str` conversion in Playwright stub
- [x] **Frontend Scaffold** — `frontend/README.md` with Next.js 14 + Shadcn/UI architecture

### Phase 2: Hyper-Personalized Career Matcher & Advanced Research Learning Agent

- [ ] **Resume Evaluation Tool** — Activate `tools/career_tools.evaluate_resume_against_job` with LLM-based extraction (replace keyword stub)
- [ ] **Cover Letter Generator** — Tailored letters per application using job description + user profile + company research
- [ ] **Interview Prep Agent** — Company-specific question generation from filings, news, tech stack, financial health
- [ ] **Learning Agent LLM Integration** — Replace curated paper list with dynamic ArXiv API + semantic search over `DocumentChunk`
- [ ] **Skill Gap → Course Mapping** — Map missing skills to specific courses (DeepLearning.AI, Hugging Face, vendor certs)
- [ ] **Portfolio Project Generator** — Suggest GitHub projects to demonstrate missing skills

### Phase 3: Enterprise Decoupled Interfaces (FastAPI Async Gateway + Next.js Serverless UI)

- [ ] **Next.js Frontend Implementation** — Build `frontend/app/` with chat, jobs, learning, analytics, settings pages
- [ ] **Real-time SSE Chat UI** — Live agent status indicators, expandable citations, confidence visualization
- [ ] **Job Dashboard** — Filterable cards, skill gap bars, compensation breakdown, one-click apply
- [ ] **Learning Roadmap UI** — Phase cards, paper viewer, progress tracking, milestone checklists
- [ ] **Authentication** — NextAuth.js with GitHub/Google, user profile persistence
- [ ] **Deployment** — Vercel (frontend) + Railway/Fly.io (FastAPI) + Neon/Managed PG (database)

### Phase 4: Production Integrations (MCP Servers, PDF Parsing, Email Pipelines)

- [ ] **Model Context Protocol (MCP) Servers** — LinkedIn, Glassdoor, SEC EDGAR, Yahoo Finance, Naukri, Wellfound APIs
- [ ] **PDF Parsing Pipeline** — `marker-pdf` / `pymupdf` for 10-K, 10-Q, earnings transcripts, resume PDFs
- [ ] **Automated Email Digests** — Scheduled daily market scans, weekly career match refresh, high-priority alerts via SendGrid/SES
- [ ] **Selector Config YAML** — Per-domain CSS/XPath selectors with versioning & layout-change detection
- [ ] **Circuit Breakers** — Per-domain failure tracking, exponential backoff, fallback chains (Playwright → BS4 → RSS → Cache)
- [ ] **Observability** — LangSmith tracing, structured logging, cost/token tracking, Sentry error monitoring
- [ ] **Multi-tenancy** — User isolation, team workspaces, role-based access

---

## Quick Start

```bash
# Clone and setup
cd /home/anmol/Projects/Disha

# Activate virtual environment
source venv/bin/activate

# Install production dependencies
pip install fastapi uvicorn sqlalchemy asyncpg pgvector numpy

# Verify compilation & run personalized query
python -m py_compile main.py agents/*.py tools/*.py storage/*.py api/*.py
python main.py "Find Agentic AI and Backend roles in Bangalore on Naukri and suggest an LLMOps learning roadmap"

# Or stream execution
python main.py "Should I invest in Indian AI companies?" --stream

# JSON output for API testing
python main.py "Analyze Razorpay financial health" --json

# Run FastAPI server (in separate terminal)
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

---

## Project Structure

```
Disha/
├── main.py                      # LangGraph compilation, CLI entry point
├── schemas.py                   # Pydantic v2 models (CompanyMetrics, JobOpening, AgentState)
├── fetch_rss.py                 # Legacy RSS scraper (reference)
├── .gitignore
├── README.md
├── agents/                      # Modular agent implementations
│   ├── __init__.py
│   ├── scraper_agent.py         # India-focused scraping with real tools
│   ├── financial_agent.py       # Valuation & risk analysis
│   ├── career_agent.py          # Hyper-personalized matching (IIT Mandi profile)
│   ├── supervisor_agent.py      # Cyclic routing with iteration guard
│   └── learning_agent.py        # ArXiv papers, phase roadmap, gap analysis
├── api/
│   ├── __init__.py
│   └── server.py                # FastAPI + SSE endpoints
├── frontend/
│   └── README.md                # Next.js 14 + Shadcn/UI architecture
├── storage/
│   ├── __init__.py
│   └── db.py                    # Async SQLAlchemy + pgvector scaffold
├── tools/
│   ├── __init__.py
│   ├── scraper_tools.py         # RSS + Playwright stub (HttpUrl fix)
│   └── career_tools.py          # Resume evaluation tool (stub)
└── venv/                        # (ignored)
```

---

## Personalization: Anmol Sharma (IIT Mandi)

This system is **hyper-personalized** to your exact background:

| Aspect               | Configuration                                                                |
| -------------------- | ---------------------------------------------------------------------------- |
| **Identity**         | Anmol Sharma, IIT Mandi B.Tech (Data Science & AI Minor), Jaipur             |
| **Target Roles**     | AI/ML Engineer, Backend Developer, Data Scientist, Quant/Data, LLMOps        |
| **Target Locations** | Bangalore, Delhi NCR, Pune, Hyderabad, Remote India                          |
| **Platforms**        | Naukri, LinkedIn India, Instahyre, Cutshort, Wellfound, Company portals      |
| **Core Stack**       | Agentic workflows, LangGraph, Multi-Agent Systems, RAG, LLMOps               |
| **EXCLUDED**         | Rust, C++, High-Frequency Trading (HFT), Embedded, Kernel, Firmware          |
| **Salary Floor**     | ₹20 LPA base (configurable)                                                  |
| **Learning Focus**   | Advanced ArXiv papers, LLMOps infra, Neuro-symbolic AI, Backend architecture |

---

## License

Proprietary — **Project Disha** internal use only.

