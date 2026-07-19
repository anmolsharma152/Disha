# Disha — status handoff

| Field | Value |
|-------|--------|
| **As of** | 2026-07-19 |
| **Branch** | `master` (default) |
| **Product** | Market intelligence for India’s AI/ML jobs — find, score, compare, recommend |
| **Not this product** | Ozyman (ops) · Scholar-Loop (FSRS) · IdeaForge (creative synthesis) |

Longer audit: [current_state.md](./current_state.md) (may lag; prefer this file for resume).  
Portfolio: [portfolio-product-boundaries.md](./portfolio-product-boundaries.md).  
Setup: [setup.md](./setup.md). Agents: [../AGENTS.md](../AGENTS.md).

---

## What ships today

| Component | Status | Notes |
|-----------|--------|-------|
| LangGraph supervisor | ✅ | Deterministic keyword routing, max-6 iteration guard |
| Scraper path | ✅ | Greenhouse + Lever tools; WWR + YC RSS; Playwright+Gemini for named companies |
| Career scoring | ✅ | Skill %, LPA fit, location, experience |
| Financial analyst | ✅ | India-first private-market style scores |
| Learning companion | ✅ | Gemini gap analysis + phased roadmap |
| FastAPI + SSE | ✅ | `/api/chat`, `/api/chat/stream` |
| Next.js chat UI | ✅ | SSE chat, job cards, recommendations |
| pgvector schema | 🔧 | Models exist; not on live chat path |
| Resume evaluation tool | 🔧 | Gemini tool exists; not wired into graph |

---

## Architecture snapshot

```text
Query → Supervisor → Scraper / Career / Financial / Learning
                   → Guardrail → Synthesize → answer + jobs/recs
```

- Backend: FastAPI · LangGraph · Python 3.12+  
- Frontend: Next.js 14  
- DB scaffold: Postgres + pgvector (optional for live path)

---

## Known gaps (prioritized)

### P0 / product quality
- [ ] Prefer structured board APIs over Playwright+Gemini as primary path (see ADRs)
- [ ] Ensure India-default currency/location on job objects
- [ ] Wire error_recovery when scrapes fail (avoid silent empty runs)

### P1
- [ ] Connect pgvector semantic search on the live path if needed for “similar roles”
- [ ] Wire resume evaluation into graph when user attaches profile/resume
- [ ] Remove or clearly document dead stubs (`extract_skills_from_text`, static LEARNING_RESOURCES, etc.)

### Explicit non-goals
- Mail/GitHub operator → **Ozyman**  
- FSRS emails → **Scholar-Loop**  
- Creative diverge–evaluate idea OS → **IdeaForge**

---

## Local dev checklist

```bash
cd ~/Projects/Disha
# Python API
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# set GEMINI / LLM keys per .env.example if present
uvicorn api.main:app --reload   # verify path in repo if different

# Frontend (if using)
cd frontend && npm install && npm run dev
```

Confirm health: FastAPI `/health` or `/api/v1/status` when running.

---

## Resume protocol

1. Read this file + portfolio boundaries.  
2. Skim `docs/current_state.md` and recent `docs/decisions/` / ADRs.  
3. `git status` / `git log -5` on `master`.  
4. Touch only job-market scope.  
5. Atomic commits; no secrets / `venv` / large caches.
