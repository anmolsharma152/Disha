# Disha Master Implementation Plan

This implementation plan integrates security audit remediations, core graph wiring, multi-user isolation & memory architecture, frontend user onboarding UI, and testing/evals/observability.

---

## Zero Hardcoding Guarantee
- **Verified Status:** `profiles/default.yaml` and `tools/profile.py` contain **zero** hardcoded user details, candidate names, or personal recommendations.
- Product defaults remain completely generic (`skills: []`, `target_cities: []`, `target_roles: []`). All personalization is strictly user-agnostic and derived dynamically at runtime from the active `user_id`'s uploaded resume and explicit query/preference context.

---

## Work Stream 1: Security Hardening

### 1. SSRF & Path Traversal Prevention
- **[MODIFY] [tools/scraper_tools.py](file:///home/anmol/Projects/Disha/tools/scraper_tools.py)**
  - Add `is_safe_url(url: str)` helper to block internal/private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`, `192.168.0.0/16`) and non-HTTP/HTTPS schemes.
  - Enforce strict slug validation regex (`^[a-zA-Z0-9_-]+$`) on `board` inputs in `search_greenhouse_jobs` and `search_lever_jobs`.

### 2. API Gateway Protection
- **[MODIFY] [api/server.py](file:///home/anmol/Projects/Disha/api/server.py)**
  - Restrict `CORSMiddleware` with configurable `ALLOWED_ORIGINS` (defaulting to `http://localhost:3000`).
  - Add endpoint rate-limiting middleware (`slowapi` or token bucket) on `/api/chat` and `/api/chat/stream`.

### 3. Prompt Injection Boundaries
- **[MODIFY] [agents/scraper_agent.py](file:///home/anmol/Projects/Disha/agents/scraper_agent.py)** & **[tools/career_tools.py](file:///home/anmol/Projects/Disha/tools/career_tools.py)**
  - Wrap raw scraped text and candidate resumes inside `<untrusted_content>` tags and reinforce system prompts to prevent embedded instruction hijacking.

---

## Work Stream 2: Core Graph & Architectural Polish

### 1. Live `pgvector` Semantic Search Connection
- **[MODIFY] [storage/db.py](file:///home/anmol/Projects/Disha/storage/db.py)** & **[agents/career_agent.py](file:///home/anmol/Projects/Disha/agents/career_agent.py)**
  - Connect existing `storage/db.py` SQLAlchemy async models (`Vector(768)` columns & `cosine_distance` `<=>` queries) directly to the live `/api/chat` path for semantic fallback search.

### 2. Wiring the LLM Resume Judge into the Graph
- **[MODIFY] [tools/career_tools.py](file:///home/anmol/Projects/Disha/tools/career_tools.py)** & **[agents/career_agent.py](file:///home/anmol/Projects/Disha/agents/career_agent.py)**
  - Wire `evaluate_resume_against_job` into `node_career_strategy` in `agents/career_agent.py` to run automatically whenever a user resume profile is loaded in `AgentState`.

### 3. Fixing Error Recovery Node Wiring
- **[MODIFY] [agents/scraper_agent.py](file:///home/anmol/Projects/Disha/agents/scraper_agent.py)** & **[main.py](file:///home/anmol/Projects/Disha/main.py)**
  - Populate `state["error_log"]` on tool failures and activate `node_error_recovery` instead of dead-ending.

### 4. Resolving Status Discrepancies & Date Stamp Drift
- **[MODIFY] [README.md](file:///home/anmol/Projects/Disha/README.md)**, **[docs/STATUS.md](file:///home/anmol/Projects/Disha/docs/STATUS.md)** & **[docs/current_state.md](file:///home/anmol/Projects/Disha/docs/current_state.md)**
  - Align component status tables across docs and update date headers to **August 2026**.

---

## Work Stream 3: Multi-User Isolation & Long-Term Memory Architecture

### 1. Strict Per-User Storage & Context Isolation (No Leakage)
- **[MODIFY] [storage/user_memory.py](file:///home/anmol/Projects/Disha/storage/user_memory.py)** & **[api/server.py](file:///home/anmol/Projects/Disha/api/server.py)**
  - Replace hardcoded fallback to `"default"` user ID with mandatory, sanitized session/user tokens (e.g. UUID v4 generated on frontend or passed via headers).
  - Isolate memory storage under `data/user_memory_{user_id}.json` (or PostgreSQL `user_profiles` table) ensuring strict tenant isolation and zero cross-user context bleeding.
  - Enforce explicit `user_id` checks on `GET /api/profile`, `POST /api/profile/resume`, and `DELETE /api/profile`.

---

## Work Stream 4: Frontend New User Onboarding & User Switcher UI

### 1. Next.js Onboarding & Resume Upload UI
- **[MODIFY] [frontend/](file:///home/anmol/Projects/Disha/frontend/)**
  - Add an **Onboarding Drawer / Modal** for first-time or new users:
    - Resume Drag-and-Drop Uploader (PDF / TXT) connecting to `POST /api/profile/resume`.
    - Profile preferences form (Target Roles, Target Cities, Min LPA Floor, Skills).
  - Add a **Session / Profile Badge** in the top navigation bar showing active user ID, loaded skill count, and an "Upload New Resume / Switch User" option.
  - Persist `disha_user_id` in browser `localStorage` and include `user_id` in every SSE chat request (`/api/chat/stream`).

---

## Work Stream 5: Testing, Evals & Observability

### 1. Automated Test Suite (`pytest`)
- **[NEW] `tests/test_security.py`**: Verify SSRF blocking, slug regex, CORS headers, and multi-user memory isolation (prevent cross-user leakage).
- **[NEW] `tests/test_api_server.py`**: Test `/api/chat`, `/api/chat/stream`, and resume upload endpoints per user ID.
- **[NEW] `tests/test_career_agent.py`**: Validate match scoring and LLM judge invocation.

### 2. LLM Evaluation Suite
- **Extraction Accuracy Eval**: Benchmark Gemini job extraction precision/recall on 10 sample JDs.
- **Scoring Consistency Eval**: Benchmark `evaluate_resume_against_job` score variance (< 5%) across multiple runs at `temperature=0.1`.

### 3. Observability & Telemetry
- Enable **LangSmith / OpenTelemetry** tracing (`LANGCHAIN_TRACING_V2=true`) to track step execution, latency, and tool inputs.
- Compute prompt/completion token usage and update `state["total_tokens"]` and `state["total_cost_usd"]` per execution.

---

## User Review & Execution

Please review the updated master plan incorporating multi-user memory isolation and the frontend onboarding UI. Let me know when you are ready to begin execution!
