"""
Project Alpha-Nexus - Supervisor Agent
Orchestrates the multi-agent workflow with cyclic state management.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Literal

from schemas import AgentState

logger = logging.getLogger("alpha_nexus.agents.supervisor")


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

    elif state.get("routing_key") == "scraper" and (has_metrics or has_jobs):
        # Scraper returned data -> analyze
        if any(kw in query for kw in ["invest", "stock", "financial", "risk", "valuation", "market"]):
            state["routing_key"] = "financial_analyst"
            logger.info("[Supervisor] Data collected -> delegating to Financial Analyst")
        elif any(kw in query for kw in ["job", "career", "salary", "hiring", "role", "apply", "skill", "learn", "roadmap", "paper", "research"]):
            # Check if learning roadmap is requested - if so, do career first then learning
            if any(kw in query for kw in ["learn", "roadmap", "paper", "research", "study"]):
                state["routing_key"] = "career_strategy"
                logger.info("[Supervisor] Data collected -> delegating to Career Strategy (then Learning)")
            else:
                state["routing_key"] = "career_strategy"
                logger.info("[Supervisor] Data collected -> delegating to Career Strategy")
        else:
            # Default: career strategy first
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

    elif state.get("routing_key") == "error_recovery":
        # Error recovery attempted, try alternative or end
        if state.get("fallback_activated", {}).get("scraper"):
            state["routing_key"] = "end"
            logger.warning("[Supervisor] Fallback exhausted -> END")
        else:
            state["routing_key"] = "scraper"
            logger.info("[Supervisor] Error recovery -> retrying Scraper with fallback")
        return state

    else:
        # Default fallback
        state["routing_key"] = "scraper"
        logger.info("[Supervisor] Default -> Scraper")
        return state