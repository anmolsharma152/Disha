# Disha 🧭

> **Market intelligence and career optimization for India's AI/ML job landscape.**

Disha is a multi-agent system that finds roles, scores them against a personal profile, analyzes companies, and can propose learning roadmaps — not generic chat, but structured matches with compensation fit, skill overlap, and explicit reasoning.

**Portfolio:** Disha owns *job market fit* only. Not ops (Ozyman), not FSRS (Scholar-Loop), not creative synthesis (IdeaForge). See [docs/portfolio-product-boundaries.md](./docs/portfolio-product-boundaries.md).

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/built%20with-LangGraph-orange)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/api-FastAPI-teal)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/frontend-Next.js%2014-black)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/database-postgres%2Bpgvector-green)](https://github.com/pgvector/pgvector)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## What it does

Ask things like:

- *"Find Agentic AI and backend roles in Bangalore above 20 LPA"*
- *"Should I apply to Razorpay or Swiggy given my skill set?"*
- *"What LLMOps skills am I missing for Staff ML Engineer roles?"*
- *"Suggest an ArXiv-backed learning roadmap for my skill gaps"*

Typical flow:

```
Query → Supervisor (keyword routing)
      → Scraper (Greenhouse / Lever / Playwright + optional Gemini)
      → Career · Financial · Learning specialists
      → Guardrail → Synthesize → answer + structured jobs/recommendations
```

---

## Current status

| Component | Status | Notes |
|-----------|--------|-------|
| Supervisor orchestration | ✅ Working | Cyclic routing, max-6 iteration guard, guardrails |
| Career scoring | ✅ Working | Skill match %, LPA fit, location, experience |
| Financial analyst | ✅ Working | India-first private-market style scores |
| Learning companion | ✅ Working | Gemini gap analysis + phased roadmap |
| FastAPI + SSE | ✅ Working | `/api/chat`, `/api/chat/stream` with jobs + recs |
| Greenhouse + Lever tools | ✅ Working | Structured boards + normalizers |
| Query-aware board selection | ✅ Working | Company/topic/India filters choose boards; skip junk RSS on career queries |
| We Work Remotely + YC jobs | ✅ Working | RSS + Work-at-a-Startup page; 12h file cache + dedupe |
| Playwright + Gemini extract | ✅ Working | Only for named companies without a public board |
| Next.js chat UI | ✅ Working | SSE chat, job cards, recommendations, dark mode |
| pgvector schema | 🔧 Scaffold | Models + repos exist; not on the live chat path |
| Error recovery node | ✅ Working | Empty scrape → broader fallback plan; then continue / synthesize |
| Resume evaluation tool | 🔧 Partial | Gemini tool exists; not wired into the graph |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SUPERVISOR AGENT                               │
│   Intent analysis · Deterministic routing · Iteration guard             │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
         ┌─────────────────────┼──────────────────────┐
         ▼                     ▼                      ▼
┌──────────────┐      ┌────────────────┐    ┌─────────────────┐
│  SCRAPER     │      │  FINANCIAL     │    │  CAREER         │
│              │      │  ANALYST       │    │  STRATEGY       │
│ • Greenhouse │      │ • Growth       │    │ • Skill match   │
│ • Lever      │      │ • Burn / runway│    │ • LPA fit       │
│ • Playwright │      │ • ESOP / risk  │    │ • India filter  │
│ • Gemini ext │      │                │    │ • Ranked recs   │
└──────┬───────┘      └────────┬───────┘    └────────┬────────┘
       │                       │                     ▼
       │                       │            ┌─────────────────┐
       │                       │            │  LEARNING       │
       │                       │            │  COMPANION      │
       │                       │            │ • Gaps / ArXiv  │
       │                       │            │ • Phase roadmap │
       └───────────────────────┼────────────┴────────┬────────┘
                               ▼                     ▼
                    ┌──────────────────────────────────────┐
                    │  GUARDRAIL → SYNTHESIZE              │
                    │  Domain filter · Final answer        │
                    └──────────────────────────────────────┘
```

Routing is **deterministic** (no LLM in the control plane). Specialists run **sequentially** and return to the supervisor.

| Layer | Stack |
|-------|--------|
| Orchestration | LangGraph, Pydantic v2 |
| LLM | Google Gemini (extraction, learning companion, resume tool) |
| Ingestion | Greenhouse/Lever APIs, Playwright, RSS |
| API | FastAPI, Server-Sent Events |
| UI | Next.js 14, TypeScript, Tailwind, Shadcn/UI |
| Storage | SQLAlchemy 2.0 async + pgvector (scaffold) |
| Config | `profiles/default.yaml`, optional request `preferences`, `.env` |

---

## Quick start

### Backend

```bash
git clone https://github.com/anmolsharma152/Disha.git
cd Disha

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Optional: Postgres + pgvector
docker compose up -d

# .env
echo 'GEMINI_API_KEY="your_api_key_here"' >> .env

# CLI
python main.py "Find Agentic AI and backend roles in Bangalore"
python main.py "Should I invest in Indian AI companies?" --stream
python main.py "Analyze Razorpay financial health" --json

# API
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Find Agentic AI roles in Bangalore above 20 LPA"}'
```

Interactive docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
# optional: export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:3000`. The UI streams agent status, job cards, career recommendations, and the final markdown answer from `/api/chat/stream`.

---

## Example output

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

## Project structure

```
Disha/
├── main.py                  # LangGraph compile, CLI, synthesize / error_recovery
├── schemas.py               # JobOpening, CompanyMetrics, AgentState, …
├── profiles/
│   └── default.yaml         # Generic prefs (empty = no hard personal filters)
├── agents/
│   ├── supervisor_agent.py  # Routing + pre-synthesis guardrail
│   ├── scraper_agent.py     # ATS + Playwright + optional Gemini extraction
│   ├── career_agent.py      # Deterministic match scoring
│   ├── financial_agent.py   # Company / investment style scores
│   └── learning_agent.py    # Gemini learning roadmap
├── tools/
│   ├── scraper_tools.py     # RSS, Playwright, Greenhouse, Lever
│   ├── board_selection.py   # Query → ATS boards + keyword plan
│   ├── job_normalizer.py    # ATS / WWR / YC payloads → JobOpening
│   ├── job_cache.py         # File cache + dedupe for job fetches
│   ├── sources/             # WWR (RSS), YC Work-at-a-Startup, …
│   └── career_tools.py      # Resume evaluation (Gemini)
├── api/
│   └── server.py            # FastAPI + SSE
├── storage/
│   └── db.py                # Async SQLAlchemy + pgvector models/repos
├── frontend/                # Next.js chat UI (SSE, jobs, recommendations)
├── docs/                    # Architecture, ADRs, roadmaps
└── docker-compose.yml       # pgvector Postgres
```

---

## Configuration

### Preferences & resume memory

Disha does **not** hardcode a personal dossier. Profile fields fill from:

1. **Resume upload** (UI or `POST /api/profile/resume`) → stored as single-user memory under `data/`  
2. **Request `preferences`** — optional per-query overrides  
3. **`profiles/default.yaml`** — empty product defaults when no memory  

| Preference | Empty means |
|------------|-------------|
| `skills` | Skill match is neutral (not fake 0%) |
| `target_cities` | No hard location drop |
| `min_base_salary_inr` | Comp fit = unavailable (not auto “below”) |
| `experience_years` | Experience fit = unknown |

After you upload a resume, chat/search uses that memory automatically (user id `default` for v1).

```bash
# Upload resume
curl -X POST "http://localhost:8000/api/profile/resume?user_id=default" \
  -F "file=@/path/to/resume.pdf"

# Inspect memory
curl "http://localhost:8000/api/profile?user_id=default"
```

Environment:

```bash
GEMINI_API_KEY="your_api_key_here"
# optional: DISHA_DATA_DIR=/path/to/data   # where user_memory_*.json is stored
# optional frontend
NEXT_PUBLIC_API_URL="http://localhost:8000"
```

---

## Roadmap

### Done

- [x] Supervisor–specialist LangGraph graph with guardrails
- [x] FastAPI gateway + SSE (including structured jobs/recommendations)
- [x] Career + financial scoring engines (India-aware)
- [x] Greenhouse + Lever ingestion + job normalizers
- [x] Query-aware board selection (company match, topic keywords, India soft filter)
- [x] Playwright scraping + optional Gemini job extraction
- [x] Gemini learning companion
- [x] Next.js chat UI (streaming status, job list, recommendation cards)
- [x] Async Postgres + pgvector schema scaffold

### Next

- [ ] Expand live India ATS board coverage as more public boards are validated
- [ ] Wire `error_log` → `error_recovery` for real fallbacks
- [ ] Persist jobs / use pgvector on the live path when needed
- [ ] Richer job dashboard + learning roadmap UI
- [ ] Deployment (e.g. Vercel + API host + managed Postgres)
- [ ] Observability (tracing, cost), circuit breakers, cover letters

---

## License

MIT
