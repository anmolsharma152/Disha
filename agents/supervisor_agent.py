"""
Disha - Supervisor Agent
Orchestrates the multi-agent workflow with cyclic state management.
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Literal

from schemas import AgentState

logger = logging.getLogger("disha.agents.supervisor")

# ══════════════════════════════════════════════════════════════════
# Guardrail: Hard exclusions (HFT, Rust, C++, Visa-sponsorship metrics)
# ══════════════════════════════════════════════════════════════════

EXCLUDED_DOMAINS = {
    "hft", "high-frequency trading", "high frequency trading", 
    "quant trading", "market making", "latency trading",
    "proprietary trading", "prop trading"
}

EXCLUDED_TECH = {
    "rust", "c++", "cpp", "verilog", "vhdl", "fpga", 
    "kernel", "embedded", "firmware", "device driver",
    "rtos", "real-time", "microcontroller"
}

EXCLUDED_VISA_METRICS = {
    "h1b", "h-1b", "visa sponsorship", "visa sponsor",
    "work authorization", "green card", "permanent residency",
    "us citizen", "us citizenship", "citizenship required",
    "security clearance", "secret clearance", "top secret"
}

def guardrail_filter_jobs(jobs: list[Dict[str, Any]]) -> tuple[list[Dict[str, Any]], int]:
    """Filter out jobs matching excluded domains, tech, or visa requirements."""
    filtered = []
    dropped = 0
    
    for job in jobs:
        full_text = f"{job.get('title','')} {job.get('description_raw','')} {' '.join(job.get('tech_stack',[]))} {' '.join(job.get('skills_required',[]))} {' '.join(job.get('skills_preferred',[]))}".lower()
        title = (job.get("title") or "").lower()
        
        # Domain exclusion (match against full text — domain is inherently about the company/role)
        if any(excl in full_text for excl in EXCLUDED_DOMAINS):
            logger.info(f"[Guardrail] Dropped job (domain): {job.get('title')} @ {job.get('company_name')}")
            dropped += 1
            continue
        
        # Tech exclusion (match against title only — descriptions frequently mention excluded tech in passing)
        if any(excl in title for excl in EXCLUDED_TECH):
            logger.info(f"[Guardrail] Dropped job (tech): {job.get('title')} @ {job.get('company_name')}")
            dropped += 1
            continue
        
        # Visa sponsorship exclusion (for India roles, visa not needed)
        if any(excl in full_text for excl in EXCLUDED_VISA_METRICS):
            logger.info(f"[Guardrail] Dropped job (visa): {job.get('title')} @ {job.get('company_name')}")
            dropped += 1
            continue
        
        filtered.append(job)
    
    return filtered, dropped


def guardrail_filter_companies(metrics: list[Dict[str, Any]]) -> tuple[list[Dict[str, Any]], int]:
    """Filter out companies in excluded domains."""
    filtered = []
    dropped = 0
    
    for m in metrics:
        name = m.get("company_name", "").lower()
        desc = m.get("extra_data", {}).get("description", "").lower()
        
        if any(excl in name for excl in EXCLUDED_DOMAINS) or any(excl in desc for excl in EXCLUDED_DOMAINS):
            logger.info(f"[Guardrail] Dropped company (domain): {name}")
            dropped += 1
            continue
        
        filtered.append(m)
    
    return filtered, dropped


def node_guardrail_pre_synthesis(state: AgentState) -> AgentState:
    """
    Guardrail Node: Runs immediately before synthesis.
    Strips excluded jobs/companies to save token costs and enforce constraints.
    """
    logger.info("[Guardrail] Pre-synthesis filtering...")
    state["current_agent"] = "guardrail"
    state["updated_at"] = datetime.now()
    
    # Filter job_openings
    jobs = state.get("job_openings", [])
    if jobs:
        filtered_jobs, dropped = guardrail_filter_jobs(jobs)
        if dropped:
            logger.info(f"[Guardrail] Filtered {dropped} excluded jobs before synthesis")
            state["job_openings"] = filtered_jobs
            guardrail_stats = state.get("guardrail_stats", {})
            guardrail_stats["jobs_dropped"] = dropped
            state["guardrail_stats"] = guardrail_stats
    
    # Filter company_metrics
    metrics = state.get("company_metrics", [])
    if metrics:
        filtered_metrics, dropped = guardrail_filter_companies(metrics)
        if dropped:
            logger.info(f"[Guardrail] Filtered {dropped} excluded companies before synthesis")
            state["company_metrics"] = filtered_metrics
            guardrail_stats = state.get("guardrail_stats", {})
            guardrail_stats["companies_dropped"] = dropped
            state["guardrail_stats"] = guardrail_stats
    
    # Always route to synthesize after guardrail
    state["routing_key"] = "synthesize"
    return state


def node_supervisor(state: AgentState) -> AgentState:
    """
    Supervisor Agent: Analyzes user intent, delegates to sub-agents,
    aggregates results, and determines when objective is met.
    """
    logger.info(f"[Supervisor] Iteration {state['iteration']}/{state['max_iterations']} | routing_key={state.get('routing_key')}")

    # Increment iteration counter
    state["iteration"] = state.get("iteration", 0) + 1
    state["updated_at"] = datetime.now()
    state["current_agent"] = "supervisor"

    # Record delegation
    if state.get("routing_key") and state["routing_key"] != "scraper":
        state["delegation_history"].append({
            "from": "supervisor",
            "to": state["routing_key"],
            "iteration": state["iteration"],
            "timestamp": datetime.now().isoformat(),
        })

    # Hard stop at max iterations
    if state["iteration"] > state.get("max_iterations", 6):
        logger.warning(f"[Supervisor] Max iterations ({state['max_iterations']}) reached -> forcing END")
        state["routing_key"] = "end"
        return state

    # If already at end, stay at end
    if state.get("routing_key") == "end":
        logger.info("[Supervisor] Already at END -> staying at END")
        return state

    # Extract what we have so far
    has_metrics = bool(state.get("company_metrics"))
    has_jobs = bool(state.get("job_openings"))
    has_financial = bool(state.get("financial_analysis"))
    has_career = bool(state.get("career_recommendations"))
    has_learning = bool(state.get("learning_roadmap"))

    # Routing logic based on what's been collected
    query = state.get("user_query", "").lower()

    if state["iteration"] == 1:
        # First pass: always scrape first
        state["routing_key"] = "scraper"
        logger.info("[Supervisor] First iteration -> delegating to Scraper")
        return state

    elif state.get("routing_key") == "scraper":
        fallback_scraper = bool(state.get("fallback_activated", {}).get("scraper"))
        scrape_failed = not has_metrics and not has_jobs

        # Empty scrape → error_recovery once; after fallback, continue with partial/empty
        if scrape_failed and not fallback_scraper:
            state["routing_key"] = "error_recovery"
            logger.warning(
                "[Supervisor] Scraper returned no data -> Error Recovery"
            )
            return state

        if scrape_failed and fallback_scraper:
            # Give career/financial a chance to produce a graceful empty answer
            logger.warning(
                "[Supervisor] Scraper empty after fallback — continuing pipeline"
            )

        # Scraper returned data (or empty after fallback) -> analyze by intent
        if any(kw in query for kw in ["invest", "stock", "financial", "risk", "valuation", "market"]):
            state["routing_key"] = "financial_analyst"
            logger.info("[Supervisor] Data collected -> delegating to Financial Analyst")
        elif any(kw in query for kw in ["job", "career", "salary", "hiring", "role", "apply", "skill", "learn", "roadmap", "paper", "research"]):
            state["routing_key"] = "career_strategy"
            logger.info("[Supervisor] Data collected -> delegating to Career Strategy")
        else:
            state["routing_key"] = "career_strategy"
            logger.info("[Supervisor] Data collected -> delegating to Career Strategy (default)")
        return state

    elif state.get("routing_key") == "financial_analyst" and has_financial and not has_career:
        # Financial done, need career
        if any(kw in query for kw in ["job", "career", "salary", "hiring", "role", "apply", "learn", "roadmap"]):
            if any(kw in query for kw in ["learn", "roadmap", "paper", "research"]):
                state["routing_key"] = "learning_companion"
                logger.info("[Supervisor] Financial done -> delegating to Learning Companion")
            else:
                state["routing_key"] = "career_strategy"
                logger.info("[Supervisor] Financial done -> delegating to Career Strategy")
        else:
            state["routing_key"] = "synthesize"
            logger.info("[Supervisor] Financial done -> synthesizing")
        return state

    elif state.get("routing_key") == "career_strategy" and has_career:
        # Career done -> check if learning needed
        if any(kw in query for kw in ["learn", "roadmap", "paper", "research", "study"]):
            state["routing_key"] = "learning_companion"
            logger.info("[Supervisor] Career done -> delegating to Learning Companion")
        else:
            state["routing_key"] = "synthesize"
            logger.info("[Supervisor] Career done -> synthesizing")
        return state

    elif state.get("routing_key") == "learning_companion" and has_learning:
        # Learning done -> synthesize
        state["routing_key"] = "synthesize"
        logger.info("[Supervisor] Learning done -> synthesizing")
        return state

    elif state.get("routing_key") == "synthesize":
        # Already synthesized -> end
        state["routing_key"] = "end"
        logger.info("[Supervisor] Synthesis complete -> END")
        return state

    else:
        # Default fallback
        state["routing_key"] = "scraper"
        logger.info("[Supervisor] Default -> Scraper")
        return state