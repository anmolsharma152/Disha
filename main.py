"""
Project Alpha-Nexus - LangGraph Multi-Agent Orchestrator
Main entry point compiling the state graph with Supervisor pattern.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from schemas import (
    AgentState,
    CompanyMetrics,
    JobOpening,
    RemotePolicy,
    ExperienceLevel,
    ScraperSource,
    create_initial_state,
    validate_company_metrics,
    validate_job_opening,
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
# Mock Node Implementations (replace with real agents later)
# ──────────────────────────────────────────────────────────────

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
        elif any(kw in query for kw in ["job", "career", "salary", "hiring", "role", "apply", "skill"]):
            state["routing_key"] = "career_strategy"
            logger.info("[Supervisor] Data collected -> delegating to Career Strategy")
        else:
            # Default: do both analyses (financial first)
            state["routing_key"] = "financial_analyst"
            logger.info("[Supervisor] Data collected -> delegating to Financial Analyst (default)")
        return state

    elif state.get("routing_key") == "financial_analyst" and has_financial and not has_career:
        # Financial done, need career
        if any(kw in query for kw in ["job", "career", "salary", "hiring", "role", "apply"]):
            state["routing_key"] = "career_strategy"
            logger.info("[Supervisor] Financial done -> delegating to Career Strategy")
        else:
            state["routing_key"] = "synthesize"
            logger.info("[Supervisor] Financial done -> synthesizing")
        return state

    elif state.get("routing_key") == "career_strategy" and has_career:
        # Career done -> synthesize
        state["routing_key"] = "synthesize"
        logger.info("[Supervisor] Career done -> synthesizing")
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


def node_scraper(state: AgentState) -> AgentState:
    """
    Scraper Agent: Dynamically invokes scraping tools based on target domains.
    MOCK: Returns simulated company metrics and job openings.
    """
    logger.info("[Scraper] Starting scrape simulation...")
    state["current_agent"] = "scraper"
    state["updated_at"] = datetime.now()

    # Simulate scraping delay
    import time
    time.sleep(0.1)

    # Mock company metrics
    mock_metrics = CompanyMetrics(
        company_name="Nexus Technologies",
        ticker="NEXUS",
        market_cap=2_500_000_000,
        enterprise_value=2_300_000_000,
        pe_ratio=28.5,
        revenue_ttm=180_000_000,
        revenue_growth_yoy=42.3,
        revenue_growth_qoq=12.1,
        gross_margin=72.5,
        operating_margin=18.2,
        net_margin=11.8,
        headcount_current=420,
        headcount_6m_ago=350,
        headcount_12m_ago=280,
        cash_and_equivalents=85_000_000,
        total_debt=12_000_000,
        free_cash_flow=22_000_000,
        source_url="https://finance.yahoo.com/quote/NEXUS",
        source_domain="finance.yahoo.com",
        scraper_source=ScraperSource.FINANCIAL_API,
        confidence_score=0.92,
        fiscal_period="2024-Q3",
    )

    # Mock job openings
    mock_jobs = [
        JobOpening(
            company_name="Nexus Technologies",
            title="Senior Machine Learning Engineer",
            location_raw="San Francisco, CA (Hybrid 3/2)",
            location_city="San Francisco",
            location_state="CA",
            location_country="US",
            remote_policy=RemotePolicy.HYBRID,
            experience_level=ExperienceLevel.SENIOR,
            department="AI Research",
            tech_stack=["Python", "PyTorch", "TensorFlow", "Kubernetes", "AWS", "MLflow"],
            skills_required=["Deep Learning", "LLM Fine-tuning", "Distributed Training", "MLOps"],
            skills_preferred=["CUDA", "Triton", "Ray", "WandB"],
            payout_min=180_000,
            payout_max=260_000,
            equity_min=50_000,
            equity_max=120_000,
            bonus_target=30_000,
            compensation_source="levels_fyi",
            compensation_confidence=0.85,
            visa_sponsorship=True,
            h1b_eligible=True,
            description_raw="Join our AI Research team building next-gen foundation models...",
            source_url="https://nexustech.com/careers/senior-ml-engineer",
            source_domain="nexustech.com",
            scraper_source=ScraperSource.ATS_GREENHOUSE,
            posted_date=datetime(2024, 11, 15),
            is_active=True,
            application_url="https://nexustech.com/apply/12345",
        ),
        JobOpening(
            company_name="Nexus Technologies",
            title="Staff Backend Engineer - ML Infrastructure",
            location_raw="Remote (US)",
            location_city="Remote",
            location_state="US",
            location_country="US",
            remote_policy=RemotePolicy.REMOTE,
            experience_level=ExperienceLevel.STAFF,
            department="Platform Engineering",
            tech_stack=["Go", "Rust", "Kubernetes", "gRPC", "Prometheus", "ClickHouse"],
            skills_required=["High-throughput Systems", "GPU Cluster Management", "Compiler Internals"],
            skills_preferred=["CUDA", "Triton Inference Server", "KubeRay", "vLLM"],
            payout_min=220_000,
            payout_max=320_000,
            equity_min=80_000,
            equity_max=200_000,
            bonus_target=50_000,
            compensation_source="levels_fyi",
            compensation_confidence=0.88,
            visa_sponsorship=True,
            h1b_eligible=True,
            description_raw="Build the infrastructure that powers our 10,000+ GPU training clusters...",
            source_url="https://nexustech.com/careers/staff-backend-ml-infra",
            source_domain="nexustech.com",
            scraper_source=ScraperSource.ATS_GREENHOUSE,
            posted_date=datetime(2024, 11, 10),
            is_active=True,
            application_url="https://nexustech.com/apply/12346",
        ),
    ]

    # Append to state (extend, don't replace)
    existing_metrics = state.get("company_metrics", [])
    existing_jobs = state.get("job_openings", [])

    # Avoid duplicates by company_name/ticker or job_id
    existing_tickers = {m.get("ticker") for m in existing_metrics if m.get("ticker")}
    if mock_metrics.ticker not in existing_tickers:
        state["company_metrics"] = existing_metrics + [mock_metrics.model_dump(mode="json")]

    existing_job_ids = {j.get("job_id") for j in existing_jobs if j.get("job_id")}
    new_job_dicts = [j.model_dump(mode="json") for j in mock_jobs if j.job_id not in existing_job_ids]
    state["job_openings"] = existing_jobs + new_job_dicts

    # Mock raw scraped page
    state["raw_scraped_pages"].append({
        "url": "https://nexustech.com/careers",
        "html": "<html>...mock html...</html>",
        "markdown": "# Nexus Technologies Careers\n\n## Open Roles\n...",
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "scraper": "playwright",
            "status": 200,
        },
    })

    logger.info(f"[Scraper] Added 1 company, {len(new_job_dicts)} new jobs")
    return state


def node_financial_analyst(state: AgentState) -> AgentState:
    """
    Financial Analyst Agent: Consumes raw metrics and stock trends
    to calculate investment scores and risk flags.
    MOCK: Returns simulated analysis.
    """
    logger.info("[Financial Analyst] Analyzing company metrics...")
    state["current_agent"] = "financial_analyst"
    state["updated_at"] = datetime.now()

    import time
    time.sleep(0.1)

    metrics = state.get("company_metrics", [])
    if not metrics:
        logger.warning("[Financial Analyst] No metrics to analyze")
        state["financial_analysis"] = {"error": "No company metrics available"}
        return state

    # Take the most recent metrics
    latest = metrics[-1]

    # Mock analysis computation
    revenue_growth = latest.get("revenue_growth_yoy", 0)
    headcount_growth = latest.get("headcount_growth_6m", 0)
    pe_ratio = latest.get("pe_ratio", 0) or 1
    gross_margin = latest.get("gross_margin", 0)
    net_margin = latest.get("net_margin", 0)
    fcf = latest.get("free_cash_flow", 0)
    market_cap = latest.get("market_cap", 1)

    # Simple scoring (0-100)
    growth_score = min(100, max(0, (revenue_growth * 1.5) + (headcount_growth * 1.2)))
    profitability_score = min(100, max(0, (gross_margin * 0.6) + (net_margin * 1.5) + 20))
    valuation_score = min(100, max(0, 100 - (pe_ratio * 1.5))) if pe_ratio > 0 else 50
    fcf_score = min(100, max(0, (fcf / market_cap * 100) * 50 + 50)) if market_cap > 0 else 50

    composite = round((growth_score * 0.35 + profitability_score * 0.25 + valuation_score * 0.2 + fcf_score * 0.2), 1)

    # Risk flags
    risk_flags = []
    if pe_ratio > 40:
        risk_flags.append({"type": "high_valuation", "severity": "medium", "detail": f"P/E ratio {pe_ratio:.1f} above sector median"})
    if revenue_growth < 10:
        risk_flags.append({"type": "slowing_growth", "severity": "high", "detail": f"YoY revenue growth only {revenue_growth:.1f}%"})
    if net_margin < 5:
        risk_flags.append({"type": "low_profitability", "severity": "medium", "detail": f"Net margin {net_margin:.1f}%"})
    if fcf < 0:
        risk_flags.append({"type": "negative_fcf", "severity": "high", "detail": "Negative free cash flow"})

    # Investment thesis
    if composite >= 75:
        thesis = "STRONG BUY: High growth, solid margins, reasonable valuation"
        rating = "Strong Buy"
    elif composite >= 60:
        thesis = "BUY: Good fundamentals with manageable risks"
        rating = "Buy"
    elif composite >= 45:
        thesis = "HOLD: Mixed signals, monitor for improvement"
        rating = "Hold"
    else:
        thesis = "AVOID: Significant fundamental concerns"
        rating = "Avoid"

    state["financial_analysis"] = {
        "company": latest.get("company_name"),
        "ticker": latest.get("ticker"),
        "scores": {
            "growth": round(growth_score, 1),
            "profitability": round(profitability_score, 1),
            "valuation": round(valuation_score, 1),
            "fcf": round(fcf_score, 1),
            "composite": composite,
        },
        "rating": rating,
        "thesis": thesis,
        "risk_flags": risk_flags,
        "key_metrics": {
            "revenue_growth_yoy": revenue_growth,
            "headcount_growth_6m": headcount_growth,
            "pe_ratio": pe_ratio,
            "gross_margin": gross_margin,
            "net_margin": net_margin,
            "fcf_yield": round(fcf / market_cap * 100, 2) if market_cap > 0 else None,
        },
        "analyzed_at": datetime.now().isoformat(),
    }

    logger.info(f"[Financial Analyst] Composite score: {composite} -> {rating}")
    return state


def node_career_strategy(state: AgentState) -> AgentState:
    """
    Career Strategy Agent: Matches user profiles/skills against scraped roles
    to recommend high-yield job applications.
    MOCK: Returns simulated recommendations.
    """
    logger.info("[Career Strategy] Matching roles against user profile...")
    state["current_agent"] = "career_strategy"
    state["updated_at"] = datetime.now()

    import time
    time.sleep(0.1)

    jobs = state.get("job_openings", [])
    if not jobs:
        logger.warning("[Career Strategy] No job openings to analyze")
        state["career_recommendations"] = [{"error": "No job openings available"}]
        return state

    # Mock user profile (in reality, this comes from user input / session)
    user_profile = {
        "skills": ["Python", "PyTorch", "Kubernetes", "AWS", "MLOps", "Distributed Systems"],
        "experience_years": 6,
        "target_roles": ["ML Engineer", "ML Infrastructure", "Backend Engineer"],
        "min_base_salary": 180_000,
        "prefer_remote": True,
        "visa_required": True,
    }

    recommendations = []

    for job in jobs:
        # Skill match scoring
        job_tech = set(s.lower() for s in job.get("tech_stack", []))
        job_skills = set(s.lower() for s in job.get("skills_required", []))
        user_skills = set(s.lower() for s in user_profile["skills"])

        all_job_skills = job_tech | job_skills
        matched = user_skills & all_job_skills
        missing = all_job_skills - user_skills
        match_pct = round(len(matched) / len(all_job_skills) * 100, 1) if all_job_skills else 0

        # Compensation fit
        payout_mid = job.get("payout_midpoint") or 0
        comp_fit = "above" if payout_mid >= user_profile["min_base_salary"] else "below"

        # Remote fit
        remote_fit = job.get("remote_policy") in ("remote", "remote_friendly") and user_profile["prefer_remote"]

        # Visa fit
        visa_fit = job.get("visa_sponsorship") == True and user_profile["visa_required"]

        # Experience fit
        exp_level = job.get("experience_level", "unknown")
        exp_order = ["intern", "entry", "junior", "mid", "senior", "staff", "principal", "director", "vp", "c_level"]
        user_exp_idx = min(user_profile["experience_years"] // 2, len(exp_order) - 1)
        job_exp_idx = exp_order.index(exp_level) if exp_level in exp_order else 2
        exp_fit = "match" if abs(user_exp_idx - job_exp_idx) <= 1 else ("overqualified" if user_exp_idx > job_exp_idx else "stretch")

        # Overall score
        score = (
            match_pct * 0.4 +
            (100 if comp_fit == "above" else 50) * 0.25 +
            (100 if remote_fit else 30) * 0.15 +
            (100 if visa_fit else 0) * 0.1 +
            (100 if exp_fit == "match" else (70 if exp_fit == "stretch" else 40)) * 0.1
        )

        rec = {
            "job_id": job.get("job_id"),
            "company": job.get("company_name"),
            "title": job.get("title"),
            "title_normalized": job.get("title_normalized"),
            "location": f"{job.get('location_city', '')}, {job.get('location_state', '')}".strip(", "),
            "remote_policy": job.get("remote_policy"),
            "match_score": round(score, 1),
            "skill_match_pct": match_pct,
            "matched_skills": sorted(list(matched)),
            "missing_skills": sorted(list(missing))[:5],
            "compensation": {
                "base_midpoint": payout_mid,
                "total_estimate": job.get("total_comp_estimate"),
                "fit": comp_fit,
            },
            "experience_fit": exp_fit,
            "remote_fit": remote_fit,
            "visa_fit": visa_fit,
            "application_url": job.get("application_url"),
            "source_url": job.get("source_url"),
            "reasoning": f"Strong skill overlap ({match_pct}%), {comp_fit} target salary, "
                         f"{'remote-friendly' if remote_fit else 'onsite/hybrid'}, "
                         f"{'visa sponsorship available' if visa_fit else 'no visa support'}.",
            "priority": "high" if score >= 75 else ("medium" if score >= 55 else "low"),
            "analyzed_at": datetime.now().isoformat(),
        }
        recommendations.append(rec)

    # Sort by score descending
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    state["career_recommendations"] = recommendations

    logger.info(f"[Career Strategy] Generated {len(recommendations)} recommendations")
    for r in recommendations[:3]:
        logger.info(f"  -> {r['title']} @ {r['company']}: {r['match_score']} ({r['priority']})")

    return state


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

        # Mock fallback data
        fallback_metrics = CompanyMetrics(
            company_name="Nexus Technologies (fallback)",
            ticker="NEXUS",
            market_cap=2_400_000_000,
            revenue_ttm=175_000_000,
            revenue_growth_yoy=38.0,
            headcount_current=400,
            headcount_6m_ago=330,
            source_url="https://api.alternative-data.com/v1/companies/NEXUS",
            source_domain="api.alternative-data.com",
            scraper_source=ScraperSource.FINANCIAL_API,
            confidence_score=0.65,
            fiscal_period="2024-Q3",
        )

        existing = state.get("company_metrics", [])
        existing_tickers = {m.get("ticker") for m in existing if m.get("ticker")}
        if fallback_metrics.ticker not in existing_tickers:
            state["company_metrics"] = existing + [fallback_metrics.model_dump(mode="json")]

        state["routing_key"] = "financial_analyst"
        logger.info("[Error Recovery] Fallback data injected -> routing to Financial Analyst")

    elif failed_agent == "financial_analyst":
        # Simple heuristic fallback
        logger.info("[Error Recovery] Using heuristic financial scoring...")
        state["fallback_activated"]["financial_analyst"] = True
        state["routing_key"] = "career_strategy"

    elif failed_agent == "career_strategy":
        logger.info("[Error Recovery] Using basic keyword matching...")
        state["fallback_activated"]["career_strategy"] = True
        state["routing_key"] = "synthesize"

    else:
        logger.error("[Error Recovery] Unknown failure point -> END")
        state["routing_key"] = "end"

    return state


def node_synthesize(state: AgentState) -> AgentState:
    """
    Synthesis Node: Aggregates all analyses into final answer with citations.
    """
    logger.info("[Synthesize] Generating final answer...")
    state["current_agent"] = "synthesize"
    state["updated_at"] = datetime.now()

    financial = state.get("financial_analysis", {})
    career = state.get("career_recommendations", [])
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

    # Final confidence
    confidence_factors = []
    if financial and "scores" in financial:
        confidence_factors.append(0.8)
    if career:
        confidence_factors.append(0.7)
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
# Conditional Routing Logic
# ──────────────────────────────────────────────────────────────

def should_continue(state: AgentState) -> Literal[
    "scraper",
    "financial_analyst",
    "career_strategy",
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
        "error_recovery": "error_recovery",
        "synthesize": "synthesize",
        "end": "end",
    }

    next_node = valid_routes.get(routing_key, "end")
    logger.debug(f"[Router] iteration={iteration}, routing_key={routing_key} -> {next_node}")
    return next_node


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
            "error_recovery": "error_recovery",
            "synthesize": "synthesize",
            "end": END,
        },
    )

    # All sub-agents route back to supervisor
    for node_name in ["scraper", "financial_analyst", "career_strategy", "error_recovery"]:
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
    parser.add_argument("query", nargs="?", default="Find me high-paying ML roles at growing AI companies with strong fundamentals")
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