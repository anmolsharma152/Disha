# Disha 🧭

> **Automated Market Intelligence & Career Optimization Platform for India's AI/ML job landscape.**

A production-grade, multi-agent system built on **LangGraph** that scrapes corporate career pages and financial data, performs investment analysis, and matches opportunities against a hyper-personalized user profile — orchestrated through a Supervisor pattern with cyclic state management.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/built%20with-LangGraph-orange)](https://github.com/langchain-ai/langgraph)
[![PostgreSQL](https://img.shields.io/badge/database-postgres%2Bpgvector-green)](https://github.com/pgvector/pgvector)
[![FastAPI](https://img.shields.io/badge/api-FastAPI-teal)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## What It Does

Disha answers questions like:

- *"Find Agentic AI and backend roles in Bangalore above 20 LPA"*
- *"Should I apply to Razorpay or Swiggy given my current skill set?"*
- *"What LLMOps skills am I missing for Staff ML Engineer roles?"*
- *"Suggest an ArXiv-backed learning roadmap for my skill gaps"*

It responds with structured recommendations — scored, ranked, with compensation fit, skill overlap, and explicit reasoning — not generic LLM output.

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Supervisor orchestration | ✅ Working | Cyclic routing, iteration guard, guardrails |
| Career scoring engine | ✅ Working | Skill match %, LPA benchmarking, experience fit |
| Financial analyst | ✅ Working | Burn multiple, ESOP, runway scoring (India-first) |
| Learning companion | ✅ Working | Gap analysis, ArXiv roadmap, phase-based curriculum |
| FastAPI + SSE gateway | ✅ Working | `/api/chat` sync + `/api/chat/stream` SSE |
| RSS feed ingestion | ✅ Working | Live feeds via `feedparser` |
| Live job scraping | 🔧 Phase 2 | Playwright scaffold ready; Naukri/LinkedIn targeting next |
| pgvector search | 🔧 Phase 2 | Schema and models complete; semantic search pending |
| Next.js frontend | 🔧 Phase 3 | Architecture documented; implementation pending |

**Demo mode:** Run with fixture data (curated Indian AI/ML roles at Swiggy, Razorpay, CRED) to see the full pipeline end-to-end without scraping dependencies.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SUPERVISOR AGENT                               │
│   Intent Analysis • Dynamic Delegation • Aggregation • Iteration Guard │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
         ┌─────────────────────┼──────────────────────┐
         ▼                     ▼                      ▼
┌──────────────┐      ┌────────────────┐    ┌─────────────────┐
│  SCRAPER     │      │  FINANCIAL     │    │  CAREER         │
│  AGENT       │      │  ANALYST       │    │  STRATEGY       │
│              │      │                │    │                 │
│ • Playwright │      │ • ARR Growth   │    │ • Skill Match   │
│ • BS4        │      │ • Burn Multiple│    │ • LPA Bench.    │
│ • RSS Feeds  │      │ • Runway       │    │ • India Filter  │
│ • Naukri     │      │ • ESOP Score   │    │ • Priority Rank │
│ • LinkedIn   │      │ • Risk Flags   │    │                 │
└──────┬───────┘      └────────┬───────┘    └────────┬────────┘
       │                       │                     │
       │                       │                     ▼
       │                       │            ┌─────────────────┐
       │                       │            │  LEARNING       │
       │                       │            │  COMPANION      │
       │                       │            │                 │
       │                       │            │ • Gap Analysis  │
       │                       │            │ • ArXiv Papers  │
       │                       │            │ • Phase Roadmap │
       │                       │            │ • LLMOps/MLOps  │
       └───────────────────────┼────────────┴────────┬────────┘
                               ▼                     ▼
                    ┌──────────────────────────────────────┐
                    │           GUARDRAIL NODE             │
                    │  Domain Filter • Visa Strip • Dedup  │
                    └─────────────────┬────────────────────┘
                                      ▼
                    ┌──────────────────────────────────────┐
                    │          SYNTHESIZE NODE             │
                    │  Final Answer • Citations • Score    │
                    └─────────────────────────────────────┘
```

Agents are routed **sequentially** by the Supervisor based on query intent — not in parallel. A career query routes: `scraper → career_strategy → [learning_companion] → guardrail → synthesize`. A financial query routes: `scraper → financial_analyst → guardrail → synthesize`.

---

## Core Components

| Component | Technology | Responsibility |
|-----------|-----------|---------------|
| **Supervisor** | LangGraph + Pydantic | Cyclic orchestration, intent routing, max-6 iteration guard |
| **Scraper Agent** | Playwright, BeautifulSoup, `feedparser` | JS rendering, static parsing, RSS, India platforms |
| **Financial Analyst** | Custom scoring engine | ARR growth, burn multiple, ESOP transparency, runway — India private-market metrics |
| **Career Strategy** | Skill-gap + comp matching | Stack extraction, INR/LPA benchmarking, city/remote filter, priority ranking |
| **Learning Companion** | Gap analysis + curated KB | ArXiv papers, LLMOps paradigms, phase-based roadmap |
| **Guardrail Node** | Rule-based filter | Strips excluded domains (HFT, firmware), deduplicates before synthesis |
| **Knowledge Base** | PostgreSQL + pgvector (async) | Vector search over jobs/resumes/papers, LangGraph checkpoints |
| **API Gateway** | FastAPI + SSE | `/api/chat` sync, `/api/chat/stream` SSE, `/health`, `/api/v1/status` |
| **Frontend** | Next.js 14 + Tailwind + Shadcn/UI | Chat UI, job dashboard, learning roadmap (Phase 3) |

---

## Quick Start

```bash
git clone https://github.com/anmolsharma152/Disha.git
cd Disha

python -m venv venv
source venv/bin/activate

pip install fastapi uvicorn sqlalchemy asyncpg pgvector numpy feedparser langchain-core pydantic

# Run a query directly
python main.py "Find Agentic AI and backend roles in Bangalore"

# Stream output
python main.py "Should I invest in Indian AI companies?" --stream

# JSON output
python main.py "Analyze Razorpay financial health" --json

# Start the API server
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

Then hit the API:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Find Agentic AI roles in Bangalore above 20 LPA"}'
```

API docs available at `http://localhost:8000/docs`.

---

## Example Output

```
### 1. Senior AI/ML Engineer — Agentic Workflows @ Razorpay — 67.4/100 (MEDIUM)
- Location: Bangalore | Remote: Hybrid
- Base: ₹55 LPA | Est. Total: ₹73 LPA
- Skill Match: 68.4% (LangGraph, LangChain, Kubernetes, MLflow, vLLM)
- Gaps: multi-agent orchestration, model serving, drift detection
- Experience Fit: stretch
- Apply: razorpay.com/careers
```

---

## Project Structure

```
Disha/
├── main.py                  # LangGraph compilation, CLI entry point
├── schemas.py               # Pydantic v2 models: CompanyMetrics, JobOpening, AgentState
├── README.md
├── agents/
│   ├── scraper_agent.py     # India-focused scraping pipeline
│   ├── financial_agent.py   # Private-market valuation (burn multiple, ESOP, runway)
│   ├── career_agent.py      # Skill-gap scoring, LPA benchmarking
│   ├── supervisor_agent.py  # Cyclic routing + guardrail pre-synthesis
│   └── learning_agent.py    # ArXiv gap analysis, phase roadmap
├── api/
│   └── server.py            # FastAPI + SSE endpoints
├── storage/
│   └── db.py                # Async SQLAlchemy 2.0 + pgvector scaffold
├── tools/
│   ├── scraper_tools.py     # RSS (live) + Playwright (stub, Phase 2)
│   └── career_tools.py      # Resume evaluation tool (stub, Phase 2)
└── frontend/
    └── README.md            # Next.js 14 architecture spec (Phase 3)
```

---

## Configuration

Disha's profile matching is fully configurable via `agents/career_agent.py` and `agents/learning_agent.py`. The default profile targets India-based AI/ML engineering roles:

| Parameter | Default |
|-----------|---------|
| Target roles | AI/ML Engineer, LLM Engineer, LLMOps Engineer, ML Platform Engineer |
| Target cities | Bangalore, Delhi NCR, Pune, Hyderabad, Remote India |
| Salary floor | ₹20 LPA base |
| Excluded domains | HFT, embedded, firmware, kernel |
| Learning focus | LLMOps infra, agentic systems, ArXiv-level ML research |

---

## Roadmap

### Phase 1 — Modular Framework & Async Postgres Scaffold ✅

- [x] Supervisor-Specialist multi-agent architecture (LangGraph)
- [x] FastAPI gateway with SSE streaming
- [x] Async PostgreSQL + pgvector schema (SQLAlchemy 2.0)
- [x] India job localization — INR/LPA benchmarking, city filters
- [x] Financial scoring engine — burn multiple, ESOP, runway (India private-market)
- [x] Career scoring engine — skill overlap, comp fit, experience fit
- [x] Guardrail node — domain/tech exclusions pre-synthesis
- [x] Demo mode with curated fixture data

### Phase 2 — Live Data & LLM Integration 🔧

- [ ] Live Playwright scraping — Naukri, LinkedIn India, company portals
- [ ] LLM-based resume evaluation (replace keyword stub)
- [ ] Dynamic ArXiv API integration in Learning Companion
- [ ] pgvector semantic search activation
- [ ] Cover letter generator

### Phase 3 — Frontend & Deployment 🔧

- [ ] Next.js 14 chat UI with SSE streaming
- [ ] Job dashboard — filterable cards, skill gap bars, one-click apply
- [ ] Learning roadmap UI — phase cards, paper viewer, progress tracking
- [ ] Deployment — Vercel + Railway + Neon Postgres

### Phase 4 — Production Integrations 🔧

- [ ] MCP servers — LinkedIn, Glassdoor, Yahoo Finance, Wellfound
- [ ] PDF parsing — earnings transcripts, resume analysis
- [ ] Automated email digests — daily market scans, weekly match refresh
- [ ] LangSmith tracing, cost/token observability
- [ ] Circuit breakers — per-domain failure tracking, fallback chains

---

## License

MIT
