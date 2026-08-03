# Disha Production Deployment Guide

This guide covers deploying Disha using **Option A** (Vercel + PaaS Backend + Supabase), **Option B** (Single VPS Docker Compose), and **Option C** (GCP Cloud Run + Cloud SQL).

---

## Prerequisites

- **Google Gemini API Key:** Required for LLM extraction, learning roadmaps, and resume matching.
- **Docker & Docker Compose** (for containerized deployments).
- **PostgreSQL Database with `pgvector` extension** (e.g. Supabase, Neon.tech, AWS RDS, or containerized `ankane/pgvector`).

---

## Option A: Managed PaaS Deployment (Recommended for Speed)

### 1. Database (Supabase / Neon.tech)
1. Create a PostgreSQL project on Supabase or Neon.
2. Run SQL in the SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Copy your async connection string:
   `postgresql+asyncpg://postgres:[YOUR-PASSWORD]@[YOUR-HOST]:5432/postgres`

### 2. Backend API (Render / Railway / AWS App Runner)
1. Link your GitHub repository to Render / Railway.
2. Select **Docker** environment type (points to root `Dockerfile`).
3. Set Environment Variables:
   - `GEMINI_API_KEY`: `your_gemini_key`
   - `DATABASE_URL`: `postgresql+asyncpg://...`
   - `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app`
4. Deploy! Health check endpoint: `https://your-backend.onrender.com/health`

### 3. Frontend UI (Vercel)
1. Import repository on [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com`
4. Click **Deploy**.

---

## Option B: Self-Hosted VPS Deployment (Single Docker Compose)

Deploy the entire stack (Postgres + pgvector, FastAPI, Next.js UI) on a Linux VPS (DigitalOcean, Hetzner, AWS EC2):

1. Clone repository to server:
   ```bash
   git clone https://github.com/anmolsharma152/Disha.git
   cd Disha
   ```

2. Copy `.env.example` to `.env` and add your secrets:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. Launch production stack:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

4. Verify status:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   curl http://localhost:8000/health
   ```
   Open `http://YOUR-SERVER-IP:3000` in your browser!

---

## Option C: Google Cloud Platform (Cloud Run + Cloud SQL)

1. Enable Cloud Run & Cloud SQL on GCP.
2. Build & push Docker image to Artifact Registry:
   ```bash
   gcloud builds submit --tag gcr.io/[PROJECT-ID]/disha-backend:latest .
   ```
3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy disha-backend \
     --image gcr.io/[PROJECT-ID]/disha-backend:latest \
     --platform managed \
     --set-env-vars GEMINI_API_KEY="...",ALLOWED_ORIGINS="..."
   ```

---

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API Key | Required |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://...` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |
| `DISHA_DATA_DIR` | User memory storage path | `/app/data` |
| `NEXT_PUBLIC_API_URL` | Frontend API endpoint URL | `http://localhost:8000` |
