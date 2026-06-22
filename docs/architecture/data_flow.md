# Disha Data Flow

---

## 1. End-to-End Pipeline

### 1.1 Query Processing Sequence

```
User Query
  │
  ▼
┌─────────────────────┐
│  SUPERVISOR (iter 1)│──→ routing_key = "scraper"
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│  SCRAPER             │  Reads: user_query
│                      │  Writes: job_openings[], company_metrics[], raw_scraped_pages[]
│  1. RSS feed fetch   │
│  2. Playwright page  │
│  3. Gemini extract   │
│  4. Keyword filter   │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│  SUPERVISOR (iter 2)│──→ routing_key depends on query intent
│  Check: has_jobs?   │      "invest" → financial_analyst
│  Detect: keywords   │      "job/career" → career_strategy
└─────────────────────┘      default → career_strategy
  │
  ├──→ financial_analyst ───→ supervisor ───→ ...
  │     Reads: company_metrics[]
  │     Writes: financial_analysis{}
  │
  └──→ career_strategy ───→ supervisor ───→ ...
        Reads: job_openings[]
        Writes: career_recommendations[]
         │
         └──→ (if "learn/roadmap" in query)
               └──→ learning_companion
                     Reads: career_recommendations[]
                     Writes: learning_roadmap{}

... (supervisor routes to synthesize)

  │
  ▼
┌─────────────────────┐
│  GUARDRAIL           │  Reads: job_openings[], company_metrics[]
│                      │  Writes: (filtered in-place), guardrail_stats{}
│  Strips: HFT, Rust,  │
│  C++, firmware,      │
│  visa-required       │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│  SYNTHESIZE          │  Reads: all analysis fields
│                      │  Writes: final_answer, answer_confidence, citations[]
│  Build sections:     │
│  - Company Overview  │
│  - Financial Scores  │
│  - Career Matches    │
│  - Learning Roadmap  │
└─────────────────────┘
  │
  ▼
┌─────────────────────┐
│  SUPERVISOR (final) │──→ routing_key = "end" → END
└─────────────────────┘
```

---

## 2. Data Contracts Per Node

### 2.1 Supervisor → Scraper

| Field | Value set by | Notes |
|-------|-------------|-------|
| `user_query` | Initial state | Used to determine what to scrape |
| `routing_key` | Supervisor | Set to `"scraper"` |
| `iteration` | Supervisor | Incremented |

### 2.2 Scraper → Supervisor

| Field | Type | Populated by | Notes |
|-------|------|-------------|-------|
| `job_openings` | `List[Dict]` | `node_scraper` | `JobOpening.model_dump(mode="json")` — may be empty |
| `company_metrics` | `List[Dict]` | `node_scraper` | `CompanyMetrics.model_dump(mode="json")` — may be empty |
| `raw_scraped_pages` | `List[Dict]` | `node_scraper` | `{url, html, markdown, metadata}` |

### 2.3 Scraper → Career Agent

| Field | Required by Career | Can be empty? | Source |
|-------|-------------------|---------------|--------|
| `title` | Display + skill matching | No | Job posting title |
| `company_name` | Display | No | Company name |
| `location_raw` | Location match | No | Raw location string |
| `remote_policy` | Remote fit score | Yes — default UNKNOWN | Enum value |
| `experience_level` | Experience fit | Yes — default UNKNOWN | Enum value |
| `tech_stack` | Skill match % | Yes — score = 0 | List of strings |
| `skills_required` | Skill match % | Yes — score = 0 | List of strings |
| `skills_preferred` | Skill match % | Yes — score = 0 | List of strings |
| `payout_min/payout_max` | Comp fit | Yes — uses midpoint | Integer in currency units |
| `currency` | Comp fit | Yes — default "USD" in schema; normalizer sets "INR" for India | ISO 4217 code |
| `description_raw` | Excluded-domain filter | No — needed for filtering | Full HTML or text |
| `source_url` | Citations | No | Absolute URL |
| `application_url` | Apply link | Yes | URL or null |

### 2.4 Career Agent → Supervisor

| Field | Type | Notes |
|-------|------|-------|
| `career_recommendations` | `List[Dict]` | Ranked by `match_score` descending |
| Each recommendation: | | |
| `match_score` | float (0-100) | Weighted composite |
| `skill_match_pct` | float (0-100) | Jaccard similarity on skill sets |
| `matched_skills` | `List[str]` | Skills overlapping with user profile |
| `missing_skills` | `List[str]` | Job skills not in user profile |
| `compensation.fit` | str ("above"/"below") | Base ≥ min_base_salary_inr? |
| `experience_fit` | str ("match"/"stretch"/"overqualified") | Level comparison |
| `priority` | str ("high"/"medium"/"low") | score ≥ 80, ≥ 60, else low |

### 2.5 Supervisor → Financial Analyst

| Field | Type | Notes |
|-------|------|-------|
| `company_metrics` | `List[Dict]` | At least one entry needed for analysis |

### 2.6 Financial Analyst → Supervisor

| Field | Type | Notes |
|-------|------|-------|
| `financial_analysis.scores.composite` | float (0-100) | Weighted: growth 35%, efficiency 25%, runway 20%, ESOP 20% |
| `financial_analysis.rating` | str | "Strong Accumulate" / "Accumulate" / "Hold" / "Avoid" |
| `financial_analysis.risk_flags` | `List[Dict]` | Each: `{type, severity, detail}` |

### 2.7 Career Agent → Learning Companion

| Field | Type | Notes |
|-------|------|-------|
| `career_recommendations[].missing_skills` | `List[str]` | Aggregated across all jobs |
| `user_profile.yaml` | YAML file | Loaded by learning agent directly |

### 2.8 Learning Companion → Supervisor

| Field | Type | Notes |
|-------|------|-------|
| `learning_roadmap.learning_phases` | `List[Dict]` | Phased curriculum with papers, milestones |
| `learning_roadmap.paper_recommendations` | `List[Dict]` | ArXiv papers with relevance scores |
| `learning_roadmap.gap_analysis` | `Dict` | Skill → frequency mapping |

### 2.9 Guardrail → Synthesize

| Field | Type | Notes |
|-------|------|-------|
| `job_openings` | `List[Dict]` | Filtered (excluded domains/tech/visa removed) |
| `company_metrics` | `List[Dict]` | Filtered (excluded domains removed) |
| `guardrail_stats` | `Dict` | `{jobs_dropped: int, companies_dropped: int}` |

### 2.10 Synthesize → Supervisor

| Field | Type | Notes |
|-------|------|-------|
| `final_answer` | `Optional[str]` | Markdown-formatted answer |
| `answer_confidence` | float (0-1) | Average of per-section confidence |
| `citations` | `List[Dict]` | `{source, type}` for attribution |
| `routing_key` | Literal["end"] | Set to "end" |

---

## 3. State Field Lifecycle

| Field | Created by | Modified by | Consumed by | Deleted by |
|-------|-----------|-------------|-------------|------------|
| `user_query` | `create_initial_state` | — | Supervisor, Synthesis | — |
| `routing_key` | `create_initial_state` | Supervisor, Guardrail | `should_continue` | — |
| `iteration` | `create_initial_state` | Supervisor | `should_continue` | — |
| `job_openings` | Scraper | Guardrail (filter) | Career, Synthesis | — |
| `company_metrics` | Scraper | Guardrail (filter) | Financial, Synthesis | — |
| `career_recommendations` | Career | — | Learning, Synthesis | — |
| `financial_analysis` | Financial | — | Synthesis | — |
| `learning_roadmap` | Learning | — | Synthesis | — |
| `error_log` | Any agent | Error Recovery | Error Recovery | — |
| `final_answer` | Synthesis | — | API response | — |

---

## 4. Current Data Flow Deficiencies

1. **Error_recovery is isolated.** The node exists in the graph but no agent routes to it. Stale errors are never cleaned up, and the node can fire on errors from previous runs.

2. **Scraper ignores the user query.** The same URL (OpenAI Greenhouse) is scraped regardless of what the user asks. `user_query` is available in state but unused by `node_scraper`.

3. **No deduplication across iterations.** If the supervisor routes back to the scraper (which it doesn't currently, but the error_recovery path allows it), the same jobs could be appended again.

4. **Financial analysis is single-company.** It takes `metrics[-1]` (the last entry), ignoring all other company data. If the scraper produces metrics for multiple companies, only the last one is scored.

5. **Token/cost tracking is stubbed.** `state["total_tokens"]` and `state["total_cost_usd"]` are initialized to 0 and never updated by any agent.
