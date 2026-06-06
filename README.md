# Project Alpha-Nexus

> **Automated Market Intelligence & Career Optimization Platform**

A production-grade, multi-agent system built on **LangGraph** that autonomously scrapes corporate career pages and financial data, performs investment analysis, and matches opportunities against user profiles — all orchestrated through a Supervisor pattern with cyclic state management.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        SUPERVISOR                               │
│  Intent Analysis • Delegation • Aggregation • Termination      │
└───────────────────────┬─────────────────────────────────────────┘
                        │ routing_key
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌──────────┐   ┌─────────────┐ ┌──────────────┐
   │ SCRAPER  │   │  FINANCIAL  │ │  CAREER      │
   │ AGENT    │   │  ANALYST    │ │  STRATEGY    │
   │          │   │             │ │              │
   │ • Play-  │   │ • Valuation │ │ • Skill      │
   │   wright │   │ • Risk      │ │   Match      │
   │ • BS4    │   │   Flags     │ │ • Comp Fit   │
   │ • RSS    │   │ • Scores    │ │ • Visa/Remote│
   └────┬─────┘   └──────┬──────┘ └──────┬───────┘
        │                │                │
        └────────────────┴────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   SYNTHESIZE    │
               │  Final Answer   │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │      END        │
               └─────────────────┘
```

### Core Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Supervisor** | LangGraph + Pydantic | Orchestrates multi-agent workflow, manages cyclic state, enforces iteration limits |
| **Scraper Agent** | Playwright, BeautifulSoup, `feedparser` | Dynamic JS rendering, static parsing, RSS feeds, selector resilience with fallbacks |
| **Financial Analyst** | Custom scoring engine | Valuation (P/E, EV/Rev), growth, profitability, FCF yield, risk flags, investment thesis |
| **Career Strategy** | Skill-gap analysis, comp matching | Tech stack extraction, salary benchmarking, visa/remote filtering, application prioritization |
| **Knowledge Base** | PostgreSQL + `pgvector` | Vector search over job descriptions & filings, structured metrics, LangGraph checkpoints |

### State Management

- **`AgentState` (TypedDict)**: Complete conversation + data + routing + resilience state
- **Pydantic v2 Schemas**: `CompanyMetrics`, `JobOpening` with strict validation
- **Checkpointing**: `MemorySaver` (dev) → `PostgresSaver` (prod) for persistence

---

## Roadmap

### Phase 1: Tool Integration & Data Pipeline
- [ ] **MCP Tool Framework** — Model Context Protocol servers for external APIs (LinkedIn, Glassdoor, SEC EDGAR, Yahoo Finance)
- [ ] **PDF Parsing Pipeline** — `marker-pdf` / `pymupdf` for 10-K, 10-Q, earnings transcripts
- [ ] **RSS/Feed Aggregation** — Multi-source financial news & job board feeds with dedup

### Phase 2: Career Intelligence
- [ ] **Resume Evaluation Agent** — Parse user resume, extract skills, match against job requirements, suggest gaps
- [ ] **Cover Letter Generator** — Tailored letters per application using job description + user profile
- [ ] **Interview Prep Agent** — Company-specific question generation from filings, news, tech stack

### Phase 3: Notifications & Automation
- [ ] **Email Capabilities** — Scheduled digests, new job alerts, earnings summaries via SendGrid/SES
- [ ] **Cron/Scheduled Runs** — Daily market scans, weekly career match refresh
- [ ] **Slack/Discord Integration** — Real-time notifications for high-priority matches

### Phase 4: Production Hardening
- [ ] **PostgreSQL + pgvector** — Persistent vector store with metadata filtering
- [ ] **Selector Config YAML** — Per-domain CSS/XPath selectors with versioning & auto-detection
- [ ] **Circuit Breakers** — Per-domain failure tracking, exponential backoff, fallback chains
- [ ] **Observability** — LangSmith tracing, structured logging, cost/token tracking

---

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd alpha_nexus
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # (to be created)

# Run a query
python main.py "Find me high-paying ML roles at growing AI companies"

# Stream execution
python main.py "Should I invest in NEXUS?" --stream

# JSON output
python main.py "Analyze NEXUS financial health" --json
```

---

## Project Structure

```
alpha_nexus/
├── main.py              # LangGraph compilation, CLI entry point
├── schemas.py           # Pydantic v2 models (CompanyMetrics, JobOpening, AgentState)
├── fetch_rss.py         # RSS feed scraper (to be integrated as @tool)
├── .gitignore
├── README.md
└── venv/                # (ignored)
```

---

## License

Proprietary — Project Alpha-Nexus internal use only.