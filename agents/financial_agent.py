"""
Project Alpha-Nexus - Financial Analyst Agent
Investment analysis, risk scoring, and thesis generation.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict

from schemas import (
    AgentState,
    CompanyMetrics,
    ScraperSource,
)

logger = logging.getLogger("alpha_nexus.agents.financial")


def node_financial_analyst(state: AgentState) -> AgentState:
    """
    Financial Analyst Agent: Consumes raw metrics and stock trends
    to calculate investment scores and risk flags.
    """
    logger.info("[Financial Analyst] Analyzing company metrics...")
    state["current_agent"] = "financial_analyst"
    state["updated_at"] = datetime.now()

    time.sleep(0.1)

    metrics = state.get("company_metrics", [])
    if not metrics:
        logger.warning("[Financial Analyst] No metrics to analyze")
        state["financial_analysis"] = {"error": "No company metrics available"}
        return state

    # Take the most recent metrics
    latest = metrics[-1]

    # Extract key metrics
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

    # India-specific considerations
    company_name = latest.get("company_name", "").lower()
    is_indian = any(ind in company_name for ind in ["razorpay", "swiggy", "zoho", "cred", "paytm", "phonepe", "zerodha", "groww"])
    if is_indian:
        risk_flags.append({"type": "emerging_market", "severity": "info", "detail": "Indian private market - limited liquidity, regulatory considerations"})

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