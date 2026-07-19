"""
Disha - Scraper Agent
Query-aware job acquisition via Greenhouse/Lever, optional Playwright + Gemini.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel

from schemas import (
    AgentState,
    CompanyMetrics,
    JobOpening,
    ScraperSource,
)

from tools.scraper_tools import (
    fetch_financial_news_rss,
    fetch_webpage_playwright,
    search_greenhouse_jobs,
    search_lever_jobs,
)
from tools.job_normalizer import (
    normalize_greenhouse_job,
    normalize_lever_job,
    validate_job_dict,
)
from tools.board_selection import (
    ScrapePlan,
    job_matches_india_preference,
    job_matches_keywords,
    select_scrape_plan,
)
from tools.profile import resolve_profile
from tools.job_cache import dedupe_jobs
from tools.sources import fetch_wwr_jobs, fetch_yc_jobs

logger = logging.getLogger("disha.agents.scraper")


# ══════════════════════════════════════════════════════════════════
# India / domain helpers (shared filters)
# ══════════════════════════════════════════════════════════════════

INDIAN_JOB_PLATFORMS = [
    "naukri.com",
    "linkedin.com/in/jobs",
    "instahyre.com",
    "cutshort.io",
    "wellfound.com",
    "foundit.in",
]

INDIAN_TARGET_CITIES = [
    "bangalore",
    "bengaluru",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "pune",
    "hyderabad",
    "chennai",
    "mumbai",
    "kolkata",
]

AGENTIC_KEYWORDS = [
    "agentic",
    "langgraph",
    "langchain",
    "llm",
    "rag",
    "multi-agent",
    "autonomous agent",
    "tool use",
    "function calling",
    "mcp",
    "model context protocol",
    "workflow automation",
    "agent orchestration",
]

LLMOPS_KEYWORDS = [
    "llmops",
    "mlops",
    "model serving",
    "vllm",
    "tgi",
    "triton",
    "bento",
    "mlflow",
    "wandb",
    "kubeflow",
    "airflow",
    "prefect",
    "dagster",
    "model monitoring",
    "drift detection",
    "feature store",
    "model registry",
]

EXCLUDED_KEYWORDS = ["hft", "rust", "c++", "firmware", "embedded", "c/c++"]


def filter_jobs(jobs: list[Dict]) -> list[Dict]:
    """Prune unwanted roles before they hit the graph."""
    filtered = []
    for job in jobs:
        title = (job.get("title") or "").lower()
        if not any(kw in title for kw in EXCLUDED_KEYWORDS):
            filtered.append(job)
    return filtered


def is_india_relevant(location: str, source_domain: str) -> bool:
    """Check if a job is relevant to India targeting."""
    location_lower = location.lower()
    domain_lower = source_domain.lower()

    if any(platform in domain_lower for platform in INDIAN_JOB_PLATFORMS):
        return True
    if any(city in location_lower for city in INDIAN_TARGET_CITIES):
        return True
    if "remote" in location_lower and "india" in location_lower:
        return True
    return False


def is_agentic_relevant(title: str, description: str, tech_stack: list) -> bool:
    """Check if job is relevant to Agentic AI/ML/LLMOps roles."""
    text = f"{title} {description} {' '.join(tech_stack)}".lower()
    if any(kw in text for kw in AGENTIC_KEYWORDS):
        return True
    if any(kw in text for kw in LLMOPS_KEYWORDS):
        return True
    core_keywords = [
        "machine learning",
        "deep learning",
        "nlp",
        "computer vision",
        "generative ai",
        "foundation model",
        "transformer",
        "pytorch",
        "tensorflow",
    ]
    return any(kw in text for kw in core_keywords)


def extract_tech_stack(text: str) -> list:
    """Extract technology stack from job description text."""
    tech_keywords = [
        "python", "go", "golang", "rust", "java", "typescript", "javascript",
        "c++", "scala", "kotlin", "pytorch", "tensorflow", "jax", "flax",
        "keras", "huggingface", "transformers", "langchain", "langgraph",
        "llama-index", "haystack", "mlflow", "wandb", "kubeflow", "airflow",
        "prefect", "dagster", "vllm", "triton", "tgi", "bento", "ollama",
        "ray", "kuberay", "kubernetes", "k8s", "docker", "helm", "terraform",
        "aws", "gcp", "azure", "postgresql", "redis", "clickhouse", "kafka",
        "spark", "pinecone", "weaviate", "milvus", "qdrant", "chroma", "pgvector",
    ]
    text_lower = text.lower()
    found = []
    for kw in tech_keywords:
        if kw in text_lower and kw not in found:
            found.append(kw)
    return found


def _append_error(state: AgentState, tool: str, error: Exception, severity: str = "warning") -> None:
    log = state.setdefault("error_log", [])
    log.append({
        "agent": "scraper",
        "tool": tool,
        "error": str(error),
        "timestamp": datetime.now().isoformat(),
        "severity": severity,
    })


_ENGINEERING_TITLE_HINTS = (
    "engineer",
    "developer",
    "software",
    "sde",
    "swe",
    "scientist",
    "machine learning",
    "data ",
    "ml ",
    "ai ",
    "platform",
    "backend",
    "fullstack",
    "full stack",
    "devops",
    "sre",
    "research",
)


def _is_engineering_ish(job: Dict[str, Any]) -> bool:
    title = (job.get("title") or "").lower()
    return any(h in title for h in _ENGINEERING_TITLE_HINTS)


def _apply_query_filters(
    jobs: List[Dict[str, Any]],
    plan: ScrapePlan,
) -> List[Dict[str, Any]]:
    """
    Apply topic keywords + soft India preference with progressive fallback.

    1) keyword ∩ india preference
    2) keyword-only (if any keyword hits)
    3) engineering-ish ∩ india
    4) engineering-ish global
    5) all jobs (still subject to exclusion filter later)
    """
    if not jobs:
        return []

    def india_ok(job: Dict[str, Any]) -> bool:
        return job_matches_india_preference(job, plan.prefer_india_locations)

    kw = plan.title_keywords
    strict = [
        j for j in jobs
        if job_matches_keywords(j, kw) and india_ok(j)
    ]
    if strict:
        return strict

    if kw:
        kw_only = [j for j in jobs if job_matches_keywords(j, kw)]
        if kw_only:
            india_subset = [j for j in kw_only if india_ok(j)]
            logger.info(
                "[Scraper] Strict topic+india empty; using keyword matches "
                "(%d, india_subset=%d)",
                len(kw_only),
                len(india_subset),
            )
            return india_subset or kw_only

    eng_india = [j for j in jobs if _is_engineering_ish(j) and india_ok(j)]
    if eng_india:
        logger.info(
            "[Scraper] No topic hits; falling back to %d India engineering-ish roles",
            len(eng_india),
        )
        return eng_india

    eng = [j for j in jobs if _is_engineering_ish(j)]
    if eng:
        logger.info(
            "[Scraper] No India engineering hits; falling back to %d engineering-ish roles",
            len(eng),
        )
        return eng

    logger.info(
        "[Scraper] Filters matched nothing useful; keeping all %d jobs",
        len(jobs),
    )
    return list(jobs)



def _fetch_greenhouse(plan: ScrapePlan) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []
    # Single strongest keyword for API-side title prefilter (optional)
    api_kw = plan.title_keywords[0] if len(plan.title_keywords) == 1 else None

    logger.info(
        "[Scraper] Greenhouse boards=%s keywords=%s",
        [b for _, b in plan.greenhouse],
        plan.title_keywords,
    )
    for company_name, board in plan.greenhouse:
        try:
            payload: Dict[str, Any] = {
                "board": board,
                "max_results": plan.max_results_per_board,
            }
            if api_kw:
                payload["keywords"] = api_kw
            gh_result = search_greenhouse_jobs.invoke(payload)
            if gh_result.get("error"):
                logger.warning(
                    "[Scraper] Greenhouse board '%s' failed: %s",
                    board,
                    gh_result["error"],
                )
                continue
            for raw_job in gh_result.get("jobs", []):
                norm = normalize_greenhouse_job(raw_job)
                norm["company_name"] = company_name
                validated = validate_job_dict(norm)
                if validated:
                    jobs.append(validated)
                    logger.info("  -> [Greenhouse] %s @ %s", validated["title"], company_name)
        except Exception as e:
            logger.warning("[Scraper] Greenhouse board '%s' exception: %s", board, e)
    return jobs


def _fetch_lever(plan: ScrapePlan) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []
    api_kw = plan.title_keywords[0] if len(plan.title_keywords) == 1 else None

    logger.info("[Scraper] Lever boards=%s", [b for _, b in plan.lever])
    for company_name, board in plan.lever:
        try:
            payload: Dict[str, Any] = {
                "board": board,
                "max_results": min(plan.max_results_per_board, 10),
            }
            if api_kw:
                payload["keywords"] = api_kw
            lv_result = search_lever_jobs.invoke(payload)
            if lv_result.get("error"):
                logger.warning(
                    "[Scraper] Lever board '%s' failed: %s",
                    board,
                    lv_result["error"],
                )
                continue
            for raw_job in lv_result.get("jobs", []):
                norm = normalize_lever_job(raw_job)
                norm["company_name"] = company_name
                validated = validate_job_dict(norm)
                if validated:
                    jobs.append(validated)
                    logger.info("  -> [Lever] %s @ %s", validated["title"], company_name)
        except Exception as e:
            logger.warning("[Scraper] Lever board '%s' exception: %s", board, e)
    return jobs


def _fetch_rss_metrics(state: AgentState) -> None:
    try:
        rss_result = fetch_financial_news_rss.invoke(
            {
                "feed_url": "http://feeds.bbci.co.uk/news/business/rss.xml",
                "max_items": 5,
            }
        )
        logger.info(
            "[Scraper] RSS fetch returned %s articles",
            len(rss_result.get("articles", [])),
        )
        if rss_result.get("articles"):
            for article in rss_result["articles"][:2]:
                mock_metrics = CompanyMetrics(
                    company_name="BBC Business",
                    ticker=None,
                    market_cap=None,
                    revenue_ttm=None,
                    revenue_growth_yoy=None,
                    headcount_current=None,
                    headcount_6m_ago=None,
                    source_url=article["link"],
                    source_domain=article["source_domain"],
                    scraper_source=ScraperSource.RSS_FEED,
                    confidence_score=0.7,
                    fiscal_period=None,
                )
                existing_metrics = state.get("company_metrics", [])
                state["company_metrics"] = existing_metrics + [
                    mock_metrics.model_dump(mode="json")
                ]
    except Exception as e:
        logger.warning("[Scraper] RSS fetch failed: %s", e)
        _append_error(state, "fetch_financial_news_rss", e, severity="warning")


def _fetch_playwright_pages(state: AgentState, urls: List[str]) -> None:
    for url in urls:
        try:
            logger.info("[Scraper] Playwright fetching: %s", url)
            page_result = fetch_webpage_playwright.invoke(
                {
                    "url": url,
                    "wait_for_timeout": 5000,
                }
            )
            state.setdefault("raw_scraped_pages", []).append(
                {
                    "url": page_result["url"],
                    "html": page_result.get("html", ""),
                    "markdown": page_result.get("markdown", ""),
                    "metadata": {
                        "scraped_at": page_result.get("scraped_at"),
                        "scraper": "playwright",
                        "status": 200,
                    },
                }
            )
        except Exception as e:
            logger.warning("[Scraper] Playwright fetch failed for %s: %s", url, e)
            # Non-fatal if ATS boards still produce jobs; empty scrape is what triggers recovery
            _append_error(state, "fetch_webpage_playwright", e, severity="warning")


def _extract_jobs_with_gemini(state: AgentState) -> List[Dict[str, Any]]:
    scraped_pages = state.get("raw_scraped_pages", [])
    pages_with_content = [p for p in scraped_pages if len(p.get("markdown", "")) > 50]
    has_gemini_key = bool(
        os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    )
    if not pages_with_content or not has_gemini_key:
        if not pages_with_content:
            logger.info("[Scraper] No Playwright pages with content — skip Gemini")
        if not has_gemini_key:
            logger.info("[Scraper] No Gemini API key — skip LLM extraction")
        return []

    extracted: List[Dict[str, Any]] = []
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        class JobExtraction(BaseModel):
            jobs: list[JobOpening]

        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
        structured_llm = llm.with_structured_output(JobExtraction)

        for page in pages_with_content:
            md_text = page.get("markdown", "")
            url = page.get("url", "")
            try:
                logger.info("[Scraper] Extracting jobs via LLM from %s...", url)
                prompt = f"""
Extract all job openings from the following career page markdown.
The source URL is {url}.
If compensation or specific skills are missing, leave them empty or null.
Only extract actual job listings. Limit to the top 5 jobs found.

Markdown Content:
{md_text[:25000]}
"""
                result = structured_llm.invoke(prompt)
                if result and result.jobs:
                    for job in result.jobs:
                        job.source_url = url
                        extracted.append(job.model_dump(mode="json"))
                        logger.info(
                            "  -> Extracted: %s at %s", job.title, job.company_name
                        )
            except Exception as e:
                logger.error("[Scraper] LLM extraction failed for %s: %s", url, e)
    except Exception as e:
        logger.warning("[Scraper] Gemini initialization failed (non-fatal): %s", e)
    return extracted


# ══════════════════════════════════════════════════════════════════
# Main node
# ══════════════════════════════════════════════════════════════════


def node_scraper(state: AgentState) -> AgentState:
    """
    Scraper Agent: selects ATS boards from the user query, fetches jobs,
    optionally pulls RSS (financial) or Playwright pages (named companies).

    When ``fallback_activated["scraper"]`` is set (error_recovery), uses a
    broader scrape plan with relaxed filters.
    """
    query = state.get("user_query") or ""
    fallback = bool(state.get("fallback_activated", {}).get("scraper"))
    profile = resolve_profile(state)
    state["user_profile"] = profile  # ensure memory is visible downstream

    plan = select_scrape_plan(query, fallback=fallback)

    # Ground with target roles only (NOT every skill — that matches sales JDs too)
    if not fallback:
        role_terms: List[str] = []
        for role in (profile.get("target_roles") or [])[:5]:
            r = str(role).lower().strip()
            if r and r not in role_terms:
                role_terms.append(r)
                # Also add meaningful tokens: "ai engineer" -> engineer, ai
                for tok in r.replace("/", " ").split():
                    if len(tok) > 2 and tok not in role_terms and tok not in {
                        "and", "the", "for", "with"
                    }:
                        role_terms.append(tok)
        if role_terms:
            existing = {k.lower() for k in plan.title_keywords}
            for g in role_terms:
                if g not in existing:
                    plan.title_keywords.append(g)
            plan.reasons.append("grounded_target_roles")
        cities = [c.lower() for c in (profile.get("target_cities") or []) if c]
        if cities and any(
            c in {
                "bangalore", "bengaluru", "delhi", "pune", "hyderabad",
                "mumbai", "jaipur", "india", "remote",
            }
            for c in cities
        ):
            plan.prefer_india_locations = True

    logger.info(
        "[Scraper] plan reasons=%s gh=%d lever=%d rss=%s playwright=%d "
        "keywords=%s fallback=%s profile=%s",
        plan.reasons,
        len(plan.greenhouse),
        len(plan.lever),
        plan.fetch_rss,
        len(plan.playwright_urls),
        plan.title_keywords[:12],
        fallback,
        profile.get("display_name") or f"{len(profile.get('skills') or [])} skills",
    )

    state["current_agent"] = "scraper"
    state["updated_at"] = datetime.now()
    state.setdefault("error_log", [])
    state.setdefault("raw_scraped_pages", [])
    state.setdefault("company_metrics", [])
    state.setdefault("job_openings", [])
    state.setdefault("fallback_activated", {})
    state.setdefault("retry_count", {})

    # Count attempts for observability
    state["retry_count"]["scraper"] = state["retry_count"].get("scraper", 0) + 1

    if plan.fetch_rss:
        _fetch_rss_metrics(state)

    if plan.playwright_urls:
        _fetch_playwright_pages(state, plan.playwright_urls)

    new_job_dicts: List[Dict[str, Any]] = []
    new_job_dicts.extend(_fetch_greenhouse(plan))
    new_job_dicts.extend(_fetch_lever(plan))
    new_job_dicts.extend(_extract_jobs_with_gemini(state))

    # External first-class boards (WWR, YC) — cached
    ext_kw = list(plan.title_keywords[:6]) if plan.title_keywords else None
    if plan.fetch_wwr:
        try:
            wwr = fetch_wwr_jobs(
                categories=plan.wwr_categories or ["programming", "devops"],
                keywords=ext_kw,
                max_results=plan.external_max_results,
                use_cache=True,
            )
            new_job_dicts.extend(wwr)
            logger.info("[Scraper] WWR contributed %d jobs", len(wwr))
        except Exception as e:
            logger.warning("[Scraper] WWR fetch failed: %s", e)
            _append_error(state, "fetch_wwr", e, severity="warning")

    if plan.fetch_yc:
        try:
            yc = fetch_yc_jobs(
                keywords=ext_kw,
                max_results=plan.external_max_results,
                prefer_engineering=True,
                use_cache=True,
            )
            new_job_dicts.extend(yc)
            logger.info("[Scraper] YC contributed %d jobs", len(yc))
        except Exception as e:
            logger.warning("[Scraper] YC fetch failed: %s", e)
            _append_error(state, "fetch_yc", e, severity="warning")

    filtered = _apply_query_filters(new_job_dicts, plan)
    filtered = filter_jobs(filtered)
    filtered = dedupe_jobs(filtered)

    existing = state.get("job_openings", [])
    state["job_openings"] = existing + filtered

    def _count(src: str) -> int:
        return sum(1 for j in filtered if j.get("scraper_source") == src)

    gh_count = _count("ats_greenhouse")
    lv_count = _count("ats_lever")
    wwr_count = _count("we_work_remotely")
    yc_count = _count("yc_jobs")
    other = len(filtered) - gh_count - lv_count - wwr_count - yc_count
    logger.info(
        "[Scraper] Added %d jobs (GH=%d Lever=%d WWR=%d YC=%d other=%d) plan=%s",
        len(filtered),
        gh_count,
        lv_count,
        wwr_count,
        yc_count,
        other,
        plan.reasons,
    )

    # Signal recovery only when this pass produced nothing useful
    has_jobs = bool(state.get("job_openings"))
    has_metrics = bool(state.get("company_metrics"))
    if not has_jobs and not has_metrics:
        state["error_log"].append({
            "agent": "scraper",
            "tool": "scrape_plan",
            "error": (
                f"No jobs or metrics after scrape "
                f"(plan={plan.reasons}, fallback={fallback})"
            ),
            "timestamp": datetime.now().isoformat(),
            "severity": "error",
            "attempt": state["retry_count"].get("scraper", 1),
        })
        logger.warning("[Scraper] Empty result — recorded error for recovery routing")

    return state
