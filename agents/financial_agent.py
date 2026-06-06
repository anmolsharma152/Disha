"""
Project Alpha-Nexus - Financial Analyst Agent (India-First)
Private-market valuation for Indian startups (Swiggy, Razorpay, Cred, etc.).
Metrics: ARR, Revenue Growth, Burn Multiple, ESOP %, Runway — NOT P/E, Market Cap.
"""

from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import Any, Dict

from schemas import AgentState, CompanyMetrics, ScraperSource

logger = logging.getLogger("alpha_nexus.agents.financial")

# India-first: private company benchmarks (2024-25)
INDIAN_BENCHMARKS = {
    "fintech": {"arr_growth_good": 80, "burn_multiple_good": 1.5, "runway_months_min": 18},
    "saas":    {"arr_growth_good": 100, "burn_multiple_good": 1.2, "runway_months_min": 24},
    "ecommerce": {"arr_growth_good": 60, "burn_multiple_good": 2.0, "runway_months_min": 12},
    "ai_infra":  {"arr_growth_good": 150, "burn_multiple_good": 2.5, "runway_months_min": 18},
    "general":   {"arr_growth_good": 50, "burn_multiple_good": 2.0, "runway_months_min": 18},
}

def infer_sector(company_name: str) -> str:
    name = company_name.lower()
    if any(x in name for x in ["razorpay", "paytm", "phonepe", "zerodha", "groww", "cred", "pine labs", "pine", "bharatpe"]):
        return "fintech"
    if any(x in name for x in ["swiggy", "zomato", "blinkit", "zepto", "bigbasket", "dunzo"]):
        return "ecommerce"
    if any(x in name for x in ["freshworks", "zoho", "chargebee", "postman", "hasura", "browserstack"]):
        return "saas"
    if any(x in name for x in ["krutrim", "sarvam", "gnani", "fluid ai", "haptik", "nvidia", "openai"]):
        return "ai_infra"
    return "general"

def node_financial_analyst(state: AgentState) -> AgentState:
    """
    India-First Financial Analyst: scores private Indian companies on
    ARR growth, burn efficiency, runway, ESOP transparency — not P/E ratios.
    """
    logger.info("[Financial Analyst] Analyzing company metrics (India-first)...")
    state["current_agent"] = "financial_analyst"
    state["updated_at"] = datetime.now()
    time.sleep(0.1)

    metrics = state.get("company_metrics", [])
    if not metrics:
        logger.warning("[Financial Analyst] No metrics to analyze")
        state["financial_analysis"] = {"error": "No company metrics available"}
        return state

    latest = metrics[-1]
    company = latest.get("company_name", "Unknown")
    sector = infer_sector(company)
    benchmarks = INDIAN_BENCHMARKS.get(sector, INDIAN_BENCHMARKS["general"])

    # Extract India-relevant metrics (fallback to 0 if missing)
    arr = latest.get("revenue_ttm", 0) or 0
    arr_growth = latest.get("revenue_growth_yoy", 0) or 0
    headcount = latest.get("headcount_current", 0) or 0
    headcount_growth = latest.get("headcount_growth_6m", 0) or 0
    cash = latest.get("cash_and_equivalents", 0) or 0
    burn_rate = latest.get("free_cash_flow", 0) or 0  # negative = burn
    monthly_burn = abs(burn_rate) / 12 if burn_rate < 0 else 0
    runway_months = cash / monthly_burn if monthly_burn > 0 else 999

    # Burn Multiple = Net Burn / Net New ARR (lower is better)
    net_new_arr = arr * (arr_growth / 100)
    burn_multiple = monthly_burn * 12 / net_new_arr if net_new_arr > 0 else 999

    # ESOP transparency (from extra_data or estimated)
    esop_pool_pct = latest.get("extra_data", {}).get("esop_pool_percent", 0)
    esop_granted_pct = latest.get("extra_data", {}).get("esop_granted_percent", 0)

    # ── Scoring (0-100 each) ──────────────────────────────────────────────
    growth_score = min(100, max(0, (arr_growth / benchmarks["arr_growth_good"]) * 100))
    
    efficiency_score = min(100, max(0, 
        (benchmarks["burn_multiple_good"] / max(burn_multiple, 0.1)) * 100
    )) if burn_multiple > 0 else 50

    runway_score = min(100, max(0, (runway_months / benchmarks["runway_months_min"]) * 100))

    esop_score = 0
    if esop_pool_pct > 0:
        esop_score = min(100, (esop_pool_pct / 15) * 100)  # 15% pool = excellent
    elif esop_granted_pct > 0:
        esop_score = min(100, (esop_granted_pct / 3) * 100)  # 3% granted = good

    # Composite: growth 35%, efficiency 25%, runway 20%, esop 20%
    composite = round(
        growth_score * 0.35 + efficiency_score * 0.25 + runway_score * 0.20 + esop_score * 0.20, 1
    )

    # ── Risk Flags (India-specific) ───────────────────────────────────────
    risk_flags = []
    if arr_growth < benchmarks["arr_growth_good"] * 0.5:
        risk_flags.append({"type": "slow_arr_growth", "severity": "high", 
            "detail": f"ARR growth {arr_growth:.0f}% << sector benchmark {benchmarks['arr_growth_good']}%"})
    if burn_multiple > benchmarks["burn_multiple_good"] * 2:
        risk_flags.append({"type": "high_burn_multiple", "severity": "high",
            "detail": f"Burn multiple {burn_multiple:.1f}x >> good threshold {benchmarks['burn_multiple_good']}x"})
    if runway_months < benchmarks["runway_months_min"]:
        risk_flags.append({"type": "short_runway", "severity": "critical",
            "detail": f"Runway {runway_months:.0f} months < minimum {benchmarks['runway_months_min']}"})
    if esop_pool_pct == 0 and esop_granted_pct == 0:
        risk_flags.append({"type": "no_esop_transparency", "severity": "medium",
            "detail": "No ESOP pool/grant data disclosed — negotiate transparency"})

    # ── Verdict (India venture language) ──────────────────────────────────
    if composite >= 80:
        verdict = "HIGH CONVICTION"
        rating = "Strong Accumulate"
    elif composite >= 65:
        verdict = "POSITIVE"
        rating = "Accumulate"
    elif composite >= 50:
        verdict = "MONITOR"
        rating = "Hold / Monitor"
    else:
        verdict = "CAUTION"
        rating = "Avoid"

    state["financial_analysis"] = {
        "company": company,
        "sector": sector,
        "scores": {
            "arr_growth": round(growth_score, 1),
            "capital_efficiency": round(efficiency_score, 1),
            "runway": round(runway_score, 1),
            "esop_transparency": round(esop_score, 1),
            "composite": composite,
        },
        "rating": rating,
        "verdict": verdict,
        "key_metrics_inr": {
            "arr_cr": round(arr / 1e7, 1),           # Crores
            "arr_growth_yoy_pct": round(arr_growth, 1),
            "headcount": headcount,
            "headcount_growth_6m_pct": round(headcount_growth, 1),
            "cash_cr": round(cash / 1e7, 1),
            "monthly_burn_cr": round(monthly_burn / 1e7, 2),
            "runway_months": round(runway_months, 1),
            "burn_multiple": round(burn_multiple, 2),
            "esop_pool_pct": esop_pool_pct,
            "esop_granted_pct": esop_granted_pct,
        },
        "risk_flags": risk_flags,
        "benchmarks_used": benchmarks,
        "analyzed_at": datetime.now().isoformat(),
    }

    logger.info(f"[Financial Analyst] {company} -> {rating} (composite: {composite})")
    return state