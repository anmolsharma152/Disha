# Disha Production Deployment Implementation Plan

This plan details the steps to containerize, configure, and deploy the Disha backend API, frontend UI, and Postgres+pgvector database to production.

---

## 1. Target Architecture & Environment

```text
                                ┌─────────────────────────┐
                                │   Next.js 14 Frontend   │
                                │    (Vercel / Docker)    │
                                └────────────┬────────────┘
                                             │ HTTP/SSE
                                             ▼
                                ┌─────────────────────────┐
                                │   FastAPI Backend API   │
                                │   (Docker / Cloud Run)  │
                                └──────┬────────────┬─────┘
                                       │            │
                         Google Gemini │            │ SQLAlchemy + pgvector
                              API      ▼            ▼
                                ┌───────────┐  ┌──────────────────┐
                                │ Gemini 2.5│  │ Managed Postgres │
                                │   Flash   │  │   + pgvector     │
                                └───────────┘  └──────────────────┘
```

- **Backend Gateway:** FastAPI + LangGraph orchestrator containerized with Playwright headless Chromium.
- **Frontend:** Next.js 14 app deployed on Vercel or standalone Docker container.
- **Database:** PostgreSQL instance with `pgvector` extension enabled (Supabase / Neon.tech / Render Postgres / Docker).

---

## 2. Proposed Changes & New Artifacts

### Component 1: Backend Containerization
#### **[NEW] [Dockerfile](file:///home/anmol/Projects/Disha/Dockerfile)**
- Base image: `mcr.microsoft.com/playwright/python:v1.44.0-jammy` or `python:3.12-slim` with system Playwright Chromium dependencies installed.
- Install Python requirements (`pip install -r requirements.txt`).
- Expose port `8000`.
- Entrypoint: `uvicorn api.server:app --host 0.0.0.0 --port 8000`.

### Component 2: Database Initialization Script
#### **[NEW] [storage/init_db.py](file:///home/anmol/Projects/Disha/storage/init_db.py)**
- Async database initialization script creating `job_openings` and `document_chunks` tables with `Vector(768)` columns if missing.

### Component 3: Frontend Production Docker & Build Config
#### **[NEW] [frontend/Dockerfile](file:///home/anmol/Projects/Disha/frontend/Dockerfile)**
- Multi-stage Next.js production build (`node:20-alpine`).
- Production environment variable handling for `NEXT_PUBLIC_API_URL`.

### Component 4: Environment & Production Docker Compose
#### **[NEW] [.env.example](file:///home/anmol/Projects/Disha/.env.example)**
- Template for production secrets (`GEMINI_API_KEY`, `ALLOWED_ORIGINS`, `DATABASE_URL`, `DISHA_DATA_DIR`).
#### **[NEW] [docker-compose.prod.yml](file:///home/anmol/Projects/Disha/docker-compose.prod.yml)**
- Production multi-container compose file orchestrating `db` (pgvector), `backend` (FastAPI), and `frontend` (Next.js).

### Component 5: Deployment Documentation
#### **[NEW] [docs/deployment.md](file:///home/anmol/Projects/Disha/docs/deployment.md)**
- Comprehensive deployment guide covering:
  - Option A: Free/PaaS Deployment (Render/Railway + Vercel + Supabase)
  - Option B: Self-Hosted Docker Compose (`docker compose -f docker-compose.prod.yml up -d`)
  - Option C: GCP Cloud Run + Cloud SQL.

---

## 3. Verification Plan

### Automated Verification
1. Test Docker image build locally:
   ```bash
   docker build -t disha-backend:latest .
   ```
2. Test full multi-container stack locally:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```
3. Run backend health check against containerized server:
   ```bash
   curl http://localhost:8000/health
   ```
4. Run full test suite inside backend container:
   ```bash
   docker run --rm disha-backend:latest pytest tests/
   ```

---

## User Review Required

> [!IMPORTANT]
> **Deployment Destination Preference**: Which deployment strategy do you prefer for initial launch?
> 1. **Option A (Recommended for Quick Start):** Vercel (Frontend) + Render/Railway (Backend) + Supabase (pgvector DB).
> 2. **Option B (Self-Hosted Single VPS):** Single Docker Compose setup on a VPS (DigitalOcean / Hetzner / AWS EC2).
> 3. **Option C (Cloud Run / GCP):** Google Cloud Run + Cloud SQL.

Please let me know your preferred deployment target so I can tailor the configuration files accordingly!
