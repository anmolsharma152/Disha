# AGENTS.md

Guidance for coding agents working in **Disha**.

## Product scope

Disha is **job market intelligence** for India’s AI/ML landscape: scrape/ingest roles, score against profile, company/financial context, learning gaps.

**Out of scope:**

| Domain | Product |
|--------|---------|
| Gmail / GitHub / tasks / kicks | Ozyman |
| FSRS / study digests | Scholar-Loop |
| Creative idea diverge–evaluate OS | IdeaForge |

Portfolio: [docs/portfolio-product-boundaries.md](./docs/portfolio-product-boundaries.md).  
Resume: [docs/STATUS.md](./docs/STATUS.md).

## Important paths

| Area | Path |
|------|------|
| Graph / agents | `agents/` |
| Tools (scrape, etc.) | `tools/` |
| FastAPI | `api/` |
| Frontend | `frontend/` |
| Schemas | `schemas.py` |
| Docs / ADRs | `docs/` |

## Engineering norms

- Prefer structured job APIs over brittle Playwright+LLM extraction when both exist.  
- Deterministic supervisor routing is intentional — don’t add LLM routing without an ADR.  
- Keep India-first defaults on compensation/location for scraped India roles.  
- Atomic commits; never commit secrets, `venv/`, or personal resume data unless user asks.  
- Soft-fail scrapes with clear empty states; don’t invent job listings.
