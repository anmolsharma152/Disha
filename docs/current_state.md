# Disha — Current State

> **Automated Market Intelligence & Career Optimization Platform for India's AI/ML job landscape.**
>
> Last updated: 2026-06-22

---

## 1. Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| LangGraph orchestration | ✅ Working | 8-node StateGraph with cyclic Supervisor routing, iteration guard, MemorySaver checkpointing |
| Supervisor routing | ✅ Working | Keyword-based intent routing, max-6 iteration guard, deterministic `should_continue()` |
| Guardrail node | ✅ Working | Domain/tech/visa exclusion filtering pre-synthesis |
| Synthesis node | ✅ Working | Templated aggregation of financial, career, learning sections with citations |
| Financial analyst | ✅ Working | India-first private-market scoring: ARR growth, burn multiple, runway, ESOP |
| Career matching | ✅ Working | Weighted scoring: skill match %, comp fit, location fit, experience fit |
| Learning companion | ✅ Working | Gemini-driven gap analysis, phased roadmap, ArXiv paper recommendations |
| FastAPI + SSE gateway | ✅ Working | `/api/chat`, `/api/chat/stream`, `/health`, `/api/v1/status` |
| RSS scraping tool | ✅ Working | `feedparser`-based `fetch_financial_news_rss` |
| Playwright page scraper tool | ✅ Working | `fetch_webpage_playwright` — sync Playwright, markdown conversion |
| PostgreSQL + pgvector scaffold | ✅ Working | Async SQLAlchemy 2.0 models, `Vector(768)` columns, native `cosine_distance` |
| Resume evaluation tool | ✅ Working | Gemini structured output tool exists but is never called by any agent |
| LLM job extraction | ✅ Working | `node_scraper` uses Gemini `with_structured_output(JobExtraction)` — primary data path |
| Error recovery node | ❌ Dead code | Logic exists but never activates — no agent writes to `error_log` or routes to `error_recovery` |
| Live Playwright scraping | ✅ Working | Real browser rendering of `boards.greenhouse.io/openai` |
| Greenhouse API ingestion | 🔧 Phase 2 | Structured JSON via `boards-api.greenhouse.io` — next priority |
| pgvector semantic search | ❌ Never invoked | Schema with `Vector(768)` + `cosine_distance` exists but never called at runtime |
| `ADVANCED_PAPERS` / `LEARNING_RESOURCES` | ❌ Dead code | Static data in `learning_agent.py` — only LLM path is used |
| `extract_skills_from_text` / `extract_ats_keywords` | ❌ Dead code | Stubs in `career_tools.py` that return empty results |
| `BeautifulSoupScrapeInput` | ❌ Dead code | Schema defined but tool commented out of registry |

---

## 2. What the System Does Today

Given a query like *"Find Agentic AI and backend roles in Bangalore above 20 LPA"*:

1. **Supervisor** routes to **Scraper Agent**
2. **Scraper Agent** fetches BBC News RSS (irrelevant), scrapes OpenAI's Greenhouse page with Playwright, feeds markdown to Gemini for job extraction, applies India-relevance and Agentic/LLMOps keyword filters
3. **Supervisor** routes to **Career Strategy Agent**
4. **Career Agent** scores each job dict against the user profile (IIT Mandi, Data Science & AI, curated skill set, 20LPA minimum) using deterministic weighted formulas
5. **Supervisor** routes to **Learning Companion** (if query mentions learning/roadmap)
6. **Learning Companion** calls Gemini to generate a phased learning roadmap for skill gaps
7. **Guardrail** strips excluded domains (HFT, embedded, firmware, Rust, C++)
8. **Synthesize** builds the final answer with sections for company analysis, career matches, and learning plan

**The pipeline executes end-to-end, but the data quality is poor.** The scraper fetches a single US-based company's career page (OpenAI) and a UK news RSS feed. The Gemini extraction may produce viable `JobOpening` objects, but they represent a small, non-representative sample of the Indian AI/ML job market. Per ADR-001, this will be replaced by structured API ingestion from Greenhouse and Lever, eliminating the Playwright+Gemini extraction path for these sources.

---

## 3. Current Architecture Pattern

```
User Query
  → Supervisor (deterministic keyword routing)
    → Scraper (hardcoded tool calls, inline LLM extraction)
    → Career (deterministic scoring)
    → Financial (deterministic scoring)
    → Learning (single LLM call)
  → Guardrail (rule-based filter)
  → Synthesize (templated aggregation)
  → Supervisor → END
```

**Key characteristics:**
- Fully deterministic routing (no LLM in the routing path)
- Sequential agent execution (no parallelism)
- 8 graph nodes, max 6 iterations
- Single-pass scraping per pipeline run
- Error handling is present in the graph (`error_recovery` node) but disconnected from the agents

---

## 4. Known Issues

1. **Error recovery is dead code.** No agent writes exceptions to `state["error_log"]` or sets `routing_key = "error_recovery"`. All tool exceptions are caught and logged as warnings, then ignored.

2. **Tool registry is decorative.** `SCRAPER_TOOLS` list and `TOOL_MAP` exist but the scraper agent calls tools by name directly. The registry provides no value today.

3. **Scraper agent has mixed responsibilities.** `node_scraper` handles: RSS news, Playwright page scraping, Gemini extraction, mock CompanyMetrics generation, keyword filtering. Adding more tools to this function would compound complexity.

4. **LLM extraction is the primary job data path.** The system depends on Gemini to extract jobs from HTML markdown. This is non-deterministic, slow (~5s per page), and costly.

5. **JobOpening defaults are US-centric.** `currency="USD"`, `location_country="US"`. India-scraped jobs must explicitly override these, or compensation calculations produce wrong results.

6. **Greenhouse API is scraped with Playwright.** The code targets `boards.greenhouse.io/openai` with a full browser renderer when a public JSON API (`boards-api.greenhouse.io/v1/boards/openai/jobs`) returns structured data. ADR-001 accepts switching to the JSON API as Phase 2 priority 1.

---

## 5. Resolved Decisions

| Question | Decision | ADR |
|----------|----------|-----|
| JobOpening defaults | Keep schema generic (USD/US). Factory functions set India defaults at creation time. | ADR-001 |
| Job data source priority | Greenhouse API (1st) → Lever API (2nd) → Naukri (3rd) → LinkedIn (deferred) | ADR-001 |
| Agentic loop in scraper | Deferred until ≥5 data sources exist. Error recovery must be functional first. | ADR-002 |
| Supervisor routing | Keep deterministic. No LLM in routing path. | ADR-002 |
| Gemini job extraction | Demoted from primary path to optional enrichment. Structured APIs provide base data. | ADR-001 |

## 6. Remaining Open Questions

- Should the tool registry be removed, fixed (runtime tool selection), or left as-is?
- Should `error_recovery` be fixed at the graph level or replaced with local error handling in each agent?
