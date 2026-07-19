# Disha — setup

| Field | Value |
|-------|--------|
| **As of** | 2026-07-19 |
| **Stack** | Python 3.12+ · LangGraph · FastAPI · Next.js 14 · optional Postgres/pgvector |

Handoff: [STATUS.md](./STATUS.md). Architecture notes: [current_state.md](./current_state.md), `docs/architecture/`.

---

## Prerequisites

- Python 3.12+  
- Node 18+ (frontend)  
- LLM key (Gemini / provider used by agents — check env template in repo)  
- Optional: Postgres if using vector schema  

---

## Environment

Typical variables (names may vary — prefer project `.env.example`):

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` / Gemini key | Extraction, learning companion, structured job parse |
| `DATABASE_URL` | Postgres when using SQLAlchemy/pgvector path |
| Frontend API base | Point Next.js at FastAPI |

Never commit `.env` or API keys.

---

## Backend

```bash
cd ~/Projects/Disha
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# load env
uvicorn api.main:app --reload --port 8000
# If entrypoint differs, use: python main.py  or check README / api/
```

Smoke: open docs/OpenAPI or hit `/health` / `/api/v1/status`.

Playwright: install browsers if named-company scrape path is used:

```bash
playwright install
```

---

## Frontend

```bash
cd ~/Projects/Disha/frontend
npm install
npm run dev
```

---

## Docker (if used)

```bash
docker compose up   # when docker-compose.yml is the preferred path
```

---

## Tests

```bash
# from repo root with venv active
pytest tests/ -q
```

---

## Secrets hygiene

- No keys in git  
- Large scrape caches under ignored paths  
- Resume PDFs: do not commit personal PII if avoidable  

---

## Sibling setup

| Product | Path |
|---------|------|
| Ozyman | `~/Projects/Ozyman/docs/setup.md` |
| Scholar-Loop | `~/Projects/Scholar-Loop/docs/setup.md` |
| IdeaForge | `~/Projects/IdeaForge/docs/setup.md` |
