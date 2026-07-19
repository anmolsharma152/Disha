# Phase 2 Core Intelligence Implementation

This plan outlines the steps to complete the final major features of Phase 2 for the Disha project. This will transition the architecture from using stubs and keyword-matching to full-fledged LLM-driven execution and vector search.

## User Review Required
> [!IMPORTANT]
> This requires adding Docker to your workflow. I will create a `docker-compose.yml` to spin up a PostgreSQL instance with the `pgvector` extension locally. 
> Ensure you have Docker installed on your machine.

> [!WARNING]
> Live scraping with Playwright can be brittle due to bot protection on sites like LinkedIn and Naukri. We will focus the initial implementation on standard company career pages (e.g., Swiggy, Cred, Razorpay) which are typically less heavily shielded.

## Proposed Changes

---

### Playwright Scraper & LLM Extraction
Currently, `fetch_webpage_playwright` in `scraper_tools.py` returns a hardcoded stub.

#### [MODIFY] [requirements.txt](file:///home/anmol/Projects/Disha/requirements.txt)
- Add `playwright`, `beautifulsoup4`, and `markdownify`.

#### [MODIFY] [tools/scraper_tools.py](file:///home/anmol/Projects/Disha/tools/scraper_tools.py)
- Implement actual headless browser navigation using Playwright.
- Wait for the DOM to load, extract HTML, and convert it to clean Markdown.

#### [MODIFY] [agents/scraper_agent.py](file:///home/anmol/Projects/Disha/agents/scraper_agent.py)
- Use Gemini 2.5 Flash's structured output capabilities (`with_structured_output`) to parse the scraped Markdown directly into the `JobOpening` Pydantic schema, eliminating regex/brittle parsing.

---

### LLM-Based Resume Evaluator
Currently, `evaluate_resume_against_job` in `career_tools.py` uses simple string `.count()` keyword matching to evaluate skills.

#### [MODIFY] [requirements.txt](file:///home/anmol/Projects/Disha/requirements.txt)
- Add `PyPDF2` for local resume ingestion.

#### [MODIFY] [tools/career_tools.py](file:///home/anmol/Projects/Disha/tools/career_tools.py)
- Replace `extract_skills_from_text` and `evaluate_resume_against_job` stubs.
- Instantiate a Gemini 2.5 Flash LLM Chain.
- Pass the resume text and job description to the LLM, instructing it to act as an "LLM Judge" and output the `EvaluateResumeOutput` JSON schema natively.

---

### Vector Database Activation (pgvector)
Currently, `storage/db.py` falls back to SQLite and performs Python-side `numpy` dot-product operations for semantic search.

#### [NEW] [docker-compose.yml](file:///home/anmol/Projects/Disha/docker-compose.yml)
- Create a Docker Compose file defining a `pgvector` container (using the `ankane/pgvector` image) exposed on port 5432.

#### [MODIFY] [storage/db.py](file:///home/anmol/Projects/Disha/storage/db.py)
- Change default `DATABASE_URL` to point to the local `postgresql+asyncpg://` container.
- Integrate `GoogleGenerativeAIEmbeddings` to generate 768-dimensional embeddings for jobs and documents.
- Refactor the `vector_search` methods to use native SQLAlchemy `cosine_distance` (`<=>`) operators within PostgreSQL.

## Verification Plan

### Automated Tests
- Run `python tools/scraper_tools.py` to verify Playwright successfully fetches and renders a live dynamic webpage.
- Run `python tools/career_tools.py` to verify the Gemini 2.5 Flash judge successfully scores a sample resume.
- Run `docker compose up -d` followed by a database migration script to ensure `pgvector` initializes successfully.

### Manual Verification
- Execute `python main.py` with an end-to-end query using the newly ingested Playwright jobs and Vector DB embeddings. Verify output in the terminal.
