"""
Project Alpha-Nexus - LangGraph Multi-Agent Orchestrator
Main entry point compiling the state graph with Supervisor pattern.
Uses modular agents from agents/ package.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from schemas import AgentState, create_initial_state

from agents import (
    node_supervisor,
    node_scraper,
    node_financial_analyst,
    node_career_strategy,
    node_learning_companion,
)

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("alpha_nexus")


# ──────────────────────────────────────────────────────────────
# Conditional Routing Logic
# ──────────────────────────────────────────────────────────────

def should_continue(state: AgentState) -> Literal[
    "scraper",
    "financial_analyst",
    "career_strategy",
    "learning_companion",
    "error_recovery",
    "synthesize",
    "end",
]:
    """
    Conditional edge function: inspects routing_key and iteration count
    to determine next node or END.
    """
    routing_key = state.get("routing_key", "end")
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 6)

    # Hard stop at max iterations
    if iteration >= max_iterations:
        logger.warning(f"[Router] Max iterations ({max_iterations}) reached -> END")
        return "end"

    # Route based on routing_key
    valid_routes = {
        "scraper": "scraper",
        "financial_analyst": "financial_analyst",
        "career_strategy": "career_strategy",
        "learning_companion": "learning_companion",
        "error_recovery": "error_recovery",
        "synthesize": "synthesize",
        "end": "end",
    }

    next_node = valid_routes.get(routing_key, "end")
    logger.debug(f"[Router] iteration={iteration}, routing_key={routing_key} -> {next_node}")
    return next_node


# ──────────────────────────────────────────────────────────────
# Synthesis Node (kept in main for aggregation)
# ──────────────────────────────────────────────────────────────

def node_synthesize(state: AgentState) -> AgentState:
    """
    Synthesis Node: Aggregates all analyses into final answer with citations.
    """
    logger.info("[Synthesize] Generating final answer...")
    state["current_agent"] = "synthesize"
    state["updated_at"] = datetime.now()

    financial = state.get("financial_analysis", {})
    career = state.get("career_recommendations", [])
    learning = state.get("learning_roadmap", {})
    metrics = state.get("company_metrics", [])
    jobs = state.get("job_openings", [])

    citations = []

    # Build answer sections
    sections = []

    # Company Overview
    if metrics:
        m = metrics[-1]
        sections.append(f"## Company Analysis: {m.get('company_name')} ({m.get('ticker')})")
        sections.append(f"- **Market Cap**: ${m.get('market_cap', 0)/1e9:.1f}B")
        sections.append(f"- **Revenue (TTM)**: ${m.get('revenue_ttm', 0)/1e6:.0f}M (YoY: {m.get('revenue_growth_yoy', 0):.1f}%)")
        sections.append(f"- **Headcount**: {m.get('headcount_current', 0)} (6m growth: {m.get('headcount_growth_6m', 0):.1f}%)")
        sections.append(f"- **Margins**: Gross {m.get('gross_margin', 0):.1f}% | Net {m.get('net_margin', 0):.1f}%")
        citations.append({"source": m.get("source_url"), "type": "financial_metrics"})

    # Financial Analysis
    if financial and "scores" in financial:
        s = financial["scores"]
        sections.append(f"\n## Investment Assessment: {financial.get('rating', 'N/A')}")
        sections.append(f"- **Composite Score**: {s.get('composite', 0)}/100")
        sections.append(f"- **Growth**: {s.get('growth', 0)}/100 | **Profitability**: {s.get('profitability', 0)}/100")
        sections.append(f"- **Valuation**: {s.get('valuation', 0)}/100 | **FCF Yield**: {s.get('fcf', 0)}/100")
        sections.append(f"- **Thesis**: {financial.get('thesis', 'N/A')}")

        if financial.get("risk_flags"):
            sections.append("- **Risk Flags**:")
            for rf in financial["risk_flags"]:
                sections.append(f"  - [{rf['severity'].upper()}] {rf['detail']}")

    # Career Recommendations
    if career and isinstance(career[0], dict) and "match_score" in career[0]:
        sections.append(f"\n## Top Career Matches ({len(career)} roles analyzed)")
        for i, c in enumerate(career[:5], 1):
            sections.append(f"\n### {i}. {c['title']} @ {c['company']} -- **{c['match_score']}/100** ({c['priority'].upper()})")
            sections.append(f"- **Location**: {c['location']} | **Remote**: {c['remote_policy']}")
            base_mid = c['compensation']['base_midpoint'] or 0
            total_est = c['compensation']['total_estimate'] or 0
            sections.append(f"- **Base**: ${base_mid:,} | **Est. Total**: ${total_est:,}")
            sections.append(f"- **Skill Match**: {c['skill_match_pct']}% ({', '.join(c['matched_skills'][:5])})")
            if c['missing_skills']:
                sections.append(f"- **Gaps**: {', '.join(c['missing_skills'][:3])}")
            sections.append(f"- **Visa**: {'Yes' if c['visa_fit'] else 'No'} | **Experience Fit**: {c['experience_fit']}")
            sections.append(f"- **Reasoning**: {c['reasoning']}")
            if c.get("application_url"):
                sections.append(f"- **Apply**: {c['application_url']}")
            citations.append({"source": c.get("source_url"), "type": "job_posting"})

    # Learning Roadmap
    if learning and "learning_phases" in learning:
        phases = learning["learning_phases"]
        sections.append(f"\n## Personalized Learning Roadmap ({len(phases)} phases, {learning.get('timeline', {}).get('total_weeks', 0)} weeks)")
        for phase in phases:
            sections.append(f"\n### {phase['title']} ({phase['estimated_weeks']} weeks)")
            sections.append(f"- **Skills to acquire**: {', '.join(phase['skills_covered'][:5])}")
            sections.append(f"- **Key papers**: {len(phase['papers'])} papers")
            for p in phase["papers"][:3]:
                sections.append(f"  - [{p['arxiv_id']}] {p['title']} ({p['year']}) -- {p['relevance']}")
            sections.append(f"- **Milestones**: {'; '.join(phase['milestones'])}")
        
        sections.append(f"\n**Next Actions**:")
        for action in learning.get("next_actions", [])[:3]:
            sections.append(f"- {action}")

    # Final confidence
    confidence_factors = []
    if financial and "scores" in financial:
        confidence_factors.append(0.8)
    if career:
        confidence_factors.append(0.7)
    if learning:
        confidence_factors.append(0.75)
    if metrics:
        confidence_factors.append(0.9)
    answer_confidence = round(sum(confidence_factors) / len(confidence_factors), 2) if confidence_factors else 0.3

    final_answer = "\n".join(sections) if sections else "Insufficient data to generate analysis."

    state["final_answer"] = final_answer
    state["answer_confidence"] = answer_confidence
    state["citations"] = citations
    state["routing_key"] = "end"

    logger.info(f"[Synthesize] Final answer generated (confidence: {answer_confidence})")
    return state


# ──────────────────────────────────────────────────────────────
# Error Recovery Node (kept in main for resilience)
# ──────────────────────────────────────────────────────────────

def node_error_recovery(state: AgentState) -> AgentState:
    """
    Error Recovery Node: Activated when a primary agent fails.
    Implements fallback pipeline: Playwright -> BeautifulSoup -> Alternative APIs -> Cached Data.
    """
    logger.warning("[Error Recovery] Attempting fallback pipeline...")
    state["current_agent"] = "error_recovery"
    state["updated_at"] = datetime.now()

    error_log = state.get("error_log", [])
    last_error = error_log[-1] if error_log else {"agent": "unknown", "error": "unknown"}

    # Determine which stage failed
    failed_agent = last_error.get("agent", "scraper")

    if failed_agent == "scraper" and not state.get("fallback_activated", {}).get("scraper"):
        # Try BeautifulSoup fallback
        logger.info("[Error Recovery] Trying BeautifulSoup + httpx fallback...")
        state["fallback_activated"]["scraper"] = True
        state["routing_key"] = "scraper"
        logger.info("[Error Recovery] Fallback activated -> routing to Scraper")

    elif failed_agent == "financial_analyst":
        logger.info("[Error Recovery] Using heuristic financial scoring...")
        state["fallback_activated"]["financial_analyst"] = True
        state["routing_key"] = "career_strategy"

    elif failed_agent == "career_strategy":
        logger.info("[Error Recovery] Using basic keyword matching...")
        state["fallback_activated"]["career_strategy"] = True
        state["routing_key"] = "learning_companion"

    elif failed_agent == "learning_companion":
        logger.info("[Error Recovery] Skipping learning -> synthesize")
        state["fallback_activated"]["learning_companion"] = True
        state["routing_key"] = "synthesize"

    else:
        logger.error("[Error Recovery] Unknown failure point -> END")
        state["routing_key"] = "end"

    return state


# ──────────────────────────────────────────────────────────────
# Graph Compilation
# ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph StateGraph with all nodes
    and conditional edges implementing the Supervisor pattern.
    """
    # Initialize graph with our AgentState schema
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("supervisor", node_supervisor)
    workflow.add_node("scraper", node_scraper)
    workflow.add_node("financial_analyst", node_financial_analyst)
    workflow.add_node("career_strategy", node_career_strategy)
    workflow.add_node("learning_companion", node_learning_companion)
    workflow.add_node("error_recovery", node_error_recovery)
    workflow.add_node("synthesize", node_synthesize)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Supervisor routes to sub-agents or synthesis/end
    workflow.add_conditional_edges(
        "supervisor",
        should_continue,
        {
            "scraper": "scraper",
            "financial_analyst": "financial_analyst",
            "career_strategy": "career_strategy",
            "learning_companion": "learning_companion",
            "error_recovery": "error_recovery",
            "synthesize": "synthesize",
            "end": END,
        },
    )

    # All sub-agents route back to supervisor
    for node_name in ["scraper", "financial_analyst", "career_strategy", "learning_companion", "error_recovery"]:
        workflow.add_edge(node_name, "supervisor")

    # Synthesize goes to supervisor for final check, then END
    workflow.add_edge("synthesize", "supervisor")

    # Compile with memory checkpointer for persistence
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)

    logger.info("LangGraph compiled successfully with MemorySaver checkpointer")
    return app


# ──────────────────────────────────────────────────────────────
# Main Execution
# ──────────────────────────────────────────────────────────────

def run_alpha_nexus(
    user_query: str,
    user_id: str = "default",
    session_id: str | None = None,
    max_iterations: int = 6,
    thread_id: str | None = None,
) -> Dict[str, Any]:
    """
    Executes the full Alpha-Nexus pipeline for a user query.

    Args:
        user_query: Natural language query from user
        user_id: User identifier for personalization
        session_id: Session identifier (auto-generated if None)
        max_iterations: Maximum supervisor iterations
        thread_id: LangGraph thread ID for checkpointing

    Returns:
        Final state dict with final_answer, citations, and all intermediate data
    """
    logger.info(f"=== Alpha-Nexus Pipeline Started ===")
    logger.info(f"Query: {user_query}")

    # Build graph
    app = build_graph()

    # Create initial state
    initial_state = create_initial_state(
        user_query=user_query,
        user_id=user_id,
        session_id=session_id,
        max_iterations=max_iterations,
    )

    # Configure checkpointing
    config = {"configurable": {"thread_id": thread_id or session_id or str(uuid.uuid4())}}

    # Execute graph
    final_state = app.invoke(initial_state, config=config)

    logger.info(f"=== Pipeline Completed ===")
    logger.info(f"Final routing: {final_state.get('routing_key')}")
    logger.info(f"Iterations: {final_state.get('iteration')}")
    logger.info(f"Confidence: {final_state.get('answer_confidence')}")

    return final_state


def stream_alpha_nexus(
    user_query: str,
    user_id: str = "default",
    session_id: str | None = None,
    max_iterations: int = 6,
    thread_id: str | None = None,
):
    """
    Streams the Alpha-Nexus pipeline execution for real-time monitoring.
    Yields state updates after each node execution.
    """
    app = build_graph()
    initial_state = create_initial_state(
        user_query=user_query,
        user_id=user_id,
        session_id=session_id,
        max_iterations=max_iterations,
    )
    config = {"configurable": {"thread_id": thread_id or session_id or str(uuid.uuid4())}}

    for chunk in app.stream(initial_state, config=config, stream_mode="values"):
        # chunk is the full state after each node
        yield chunk


# ──────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Project Alpha-Nexus - Market Intelligence & Career Optimization")
    parser.add_argument("query", nargs="?", default="Find Agentic AI and Backend roles in Bangalore on Naukri and suggest an LLMOps learning roadmap")
    parser.add_argument("--user-id", default="cli_user")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--max-iterations", type=int, default=6)
    parser.add_argument("--stream", action="store_true", help="Stream execution steps")
    parser.add_argument("--json", action="store_true", help="Output final state as JSON")

    args = parser.parse_args()

    if args.stream:
        print(f"Streaming execution for: {args.query}\n{'='*60}")
        for i, state in enumerate(stream_alpha_nexus(
            user_query=args.query,
            user_id=args.user_id,
            session_id=args.session_id,
            max_iterations=args.max_iterations,
        )):
            print(f"\n--- Step {i+1}: {state.get('current_agent', 'unknown')} ---")
            print(f"  routing_key: {state.get('routing_key')}")
            print(f"  iteration: {state.get('iteration')}")
            if state.get("final_answer"):
                print(f"  FINAL ANSWER: {state['final_answer'][:200]}...")
    else:
        result = run_alpha_nexus(
            user_query=args.query,
            user_id=args.user_id,
            session_id=args.session_id,
            max_iterations=args.max_iterations,
        )

        if args.json:
            # Convert non-serializable fields
            import copy
            serializable = copy.deepcopy(result)
            # datetime objects in lists need conversion
            def convert_dt(obj):
                if isinstance(obj, dict):
                    return {k: convert_dt(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_dt(v) for v in obj]
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                elif hasattr(obj, 'model_dump'):
                    return convert_dt(obj.model_dump())
                return obj
            serializable = convert_dt(serializable)
            print(json.dumps(serializable, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print("FINAL ANSWER")
            print(f"{'='*60}")
            print(result.get("final_answer", "No answer generated"))
            print(f"\nConfidence: {result.get('answer_confidence', 0):.0%}")
            print(f"Iterations: {result.get('iteration', 0)}")
            print(f"Citations: {len(result.get('citations', []))}")