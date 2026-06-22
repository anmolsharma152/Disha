# ADR-002: Agentic Loop Evaluation

**Status:** Deferred (accept when ≥5 data sources exist)
**Author:** Architecture Review
**Area:** Orchestration, Scraper Architecture
**Supersedes:** N/A

---

## Context

Disha uses a deterministic LangGraph supervisor pattern where the execution path is predetermined by keyword matching and iteration count. This provides:

- Predictable execution (same query → same path every time)
- Observable state (every graph stream shows exact node transitions)
- Cheap operation (no LLM calls for routing decisions)

But it also means the scraper agent cannot adapt to changing conditions:

- If a platform returns 0 results, the scraper cannot try an alternative
- If a platform returns many results, the scraper cannot decide to stop early
- If the user's query matches multiple domains, the scraper cannot explore all of them

This ADR evaluates whether a bounded agentic loop would improve the system.

---

## Decision Drivers

1. **Maintain determinism for scoring** — Career, financial, guardrail, and synthesis should remain deterministic
2. **Add flexibility to data acquisition** — The scraper should adapt to real-world conditions
3. **Preserve observability** — LangGraph streaming must continue to show meaningful state
4. **Avoid premature complexity** — An agentic loop is overhead; it must be justified by tool count
5. **Bound worst-case latency** — Agentic loops can loop indefinitely; must have hard limits

---

## Workflow Evaluation

### Workflows Where Deterministic Is Sufficient

| Workflow | Reason |
|----------|--------|
| **Career matching** | Weighted formula on static inputs. Adding LLM would be non-reproducible. |
| **Financial analysis** | Pure computation on `company_metrics[]`. No decisions to make. |
| **Guardrail filtering** | Rule-based with no ambiguity. No decisions to make. |
| **Synthesis** | Templated aggregation. No decisions to make. |
| **Supervisor routing** | Query-intent mapping is stable. LLM routing would add cost without benefit. |

### Workflows That Could Benefit from Agentic Behavior

| Workflow | Current | Agentic Potential |
|----------|---------|-------------------|
| **Job scraping** | Hardcoded URL, single pass, no error recovery | Dynamic platform selection, query refinement, depth control, fallback |
| **Company research** | Single-company analysis only | Multi-company parallel research, source discovery |
| **Learning roadmap** | Single Gemini call | Iterative refinement (but current approach works well) |

### Workflows Where Tool Exists but Is Not Integrated

| Workflow | Tool | Status |
|----------|------|--------|
| **Resume evaluation** | `evaluate_resume_against_job` | Never called by any agent. Tool integration is prerequisite to agentic behavior. |

---

## Threshold Analysis

### How many tools before a planner is justified?

| Tool Count | Recommended Architecture | Rationale |
|-----------|--------------------------|-----------|
| 0-2 tools | Direct calls | No decisions to make |
| 3-4 tools | Deterministic fallback chain | `if/elif` simpler than LLM planning |
| 5-6 tools | Conditional dispatch (query-based) | `if "naukri" in query → Naukri; elif "startup" → Wellfound` |
| 7+ tools | LLM planner | Decision space large enough for LLM reasoning |

### Platform-specific evaluation

| Platforms Available | Architecture | Planner Justified? |
|--------------------|-------------|-------------------|
| Greenhouse only | Direct call | No decisions to make |
| Greenhouse + Lever | `try/except` chain | Simple enough for deterministic code |
| Greenhouse + Lever + Naukri | 3-branch `if`/`elif`/`else` | Deterministic code still better |
| + Wellfound | 4 branches | Deterministic still fine |
| + Ashby, + Indeed, + Company portals | 7+ branches | Planner starts to make sense |

**Verdict:** An agentic planner is not justified until ≥5 distinct data sources exist. With the Phase 2 plan (Greenhouse + Lever → Naukri), we will have 3 sources — comfortably within deterministic territory.

---

## Hybrid Architecture Template

When an agentic loop is eventually justified, it should follow this template:

```
Supervisor (unchanged)
  → Scraper Node (bounded agentic sub-loop)
       │
       ├── Planner (LLM): "What should I scrape next?"
       │     Input: user_query, results_so_far[], platforms_remaining[]
       │     Output: {tool: str, params: dict}
       │
       ├── Executor (deterministic): Call tool, collect results
       │
       ├── Evaluator (deterministic): enough_results()?
       │     ├── Yes → commit results to state, exit loop
       │     └── No → back to Planner (max 5 iterations)
       │
       └── On max iterations → commit what we have, log warning
  → Career (unchanged, deterministic)
  → Financial (unchanged, deterministic)
  → Guardrail (unchanged, deterministic)
  → Synthesize (unchanged, deterministic)
```

### Key constraints for the bounded loop:

1. **Isolated state** — The loop's internal state (plan, results, retries) lives in a sub-dict of AgentState, not in graph-level shared fields
2. **Bounded iterations** — Hard cap of 5 planner iterations per scraper execution
3. **Graph-level observability preserved** — The loop runs inside a single `node_scraper` call. LangGraph sees one transition: `supervisor → scraper → supervisor`
4. **Determinism preserved for downstream** — Career, financial, guardrail, and synthesis see the same data regardless of loop internals
5. **Loop internals are logged** — `state["scraper_plan_log"]` captures planner decisions for debugging

---

## Conclusion

### Commission Decision

**Do not implement an agentic loop in Phase 2.**

Rationale:
- Phase 2 adds 2-3 tools (Greenhouse, Lever, optionally Naukri) — below the 5-tool threshold
- A deterministic fallback chain (`try Greenhouse → try Lever → try Naukri`) is simpler, cheaper, and more reliable
- The agentic loop would add latency (LLM calls), cost, and non-determinism without proportional benefit
- Fixing the existing error propagation (which is dead code) is a prerequisite to any adaptive behavior

### Deferred Decision

**Re-evaluate when both conditions are met:**
1. ≥5 distinct data sources are integrated into the scraper
2. Error recovery is functional and has been tested with real failures

At that point, implement a bounded agentic loop *only inside the scraper node*, leaving all other graph nodes deterministic.

---

## References

- `main.py:222` — Error recovery node (dead code, must be fixed before agentic loop)
- `agents/scraper_agent.py:283` — Scraper agent (would host the agentic loop)
- ADR-001 — Live job ingestion strategy (defines platform ordering)
