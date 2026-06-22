"""
Project Alpha-Nexus - Scraper Agent
Real-world data acquisition using RSS feeds and Playwright for dynamic content.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict

from langchain_core.tools import tool
from pydantic import BaseModel, Field, HttpUrl

from schemas import (
    AgentState,
    CompanyMetrics,
    JobOpening,
    RemotePolicy,
    ExperienceLevel,
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

logger = logging.getLogger("alpha_nexus.agents.scraper")


# ══════════════════════════════════════════════════════════════════
# India-Specific Configuration
# ══════════════════════════════════════════════════════════════════

INDIAN_JOB_PLATFORMS = [
    "naukri.com",
    "linkedin.com/in/jobs",
    "instahyre.com",
    "cutshort.io",
    "wellfound.com",  # AngelList India
    "foundit.in",  # formerly Monster India
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

# Greenhouse boards to query (company_name → board_name mapping)
# TODO: validate which companies use Greenhouse vs Lever vs other ATS
GREENHOUSE_BOARDS: Dict[str, str] = {
    "Razorpay": "razorpay",
    "Swiggy": "swiggy",
    "CRED": "cred",
    "Zomato": "zomato",
    "Freshworks": "freshworks",
    "Postman": "postman",
}

INDIAN_COMPANY_PORTALS = [
    "tcs.com/careers",
    "infosys.com/careers",
    "wipro.com/careers",
    "hcltech.com/careers",
    "techmahindra.com/careers",
    "zoho.com/careers",
    "freshworks.com/careers",
    "razorpay.com/careers",
    "swiggy.com/careers",
    "zomato.com/careers",
    "paytm.com/careers",
    "phonepe.com/careers",
    "dunzo.com/careers",
    "cred.club/careers",
    "meesho.com/careers",
    "sharechat.com/careers",
    "kreditbee.in/careers",
    "slice.com/careers",
]

# Agentic/AI specific keywords for filtering
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
    "a/b testing",
    "feature store",
    "model registry",
]


# ══════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════

EXCLUDED_KEYWORDS = ["hft", "rust", "c++", "firmware", "embedded", "c/c++"]


def filter_jobs(jobs: list[Dict]) -> list[Dict]:
    """Prune unwanted roles before they hit the Graph to save tokens."""
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

    # Check platform
    if any(platform in domain_lower for platform in INDIAN_JOB_PLATFORMS):
        return True

    # Check location
    if any(city in location_lower for city in INDIAN_TARGET_CITIES):
        return True

    # Check remote India
    if "remote" in location_lower and "india" in location_lower:
        return True

    return False


def is_agentic_relevant(title: str, description: str, tech_stack: list) -> bool:
    """Check if job is relevant to Agentic AI/ML/LLMOps roles."""
    text = f"{title} {description} {' '.join(tech_stack)}".lower()

    # Check for Agentic keywords
    if any(kw in text for kw in AGENTIC_KEYWORDS):
        return True

    # Check for LLMOps keywords
    if any(kw in text for kw in LLMOPS_KEYWORDS):
        return True

    # Check for core ML/AI terms
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
    if any(kw in text for kw in core_keywords):
        return True

    return False


def extract_tech_stack(text: str) -> list:
    """Extract technology stack from job description text."""
    tech_keywords = [
        # Languages
        "python",
        "go",
        "golang",
        "rust",
        "java",
        "typescript",
        "javascript",
        "c++",
        "scala",
        "kotlin",
        # ML/AI Frameworks
        "pytorch",
        "tensorflow",
        "jax",
        "flax",
        "keras",
        "huggingface",
        "transformers",
        "langchain",
        "langgraph",
        "llama-index",
        "haystack",
        # MLOps/LLMOps
        "mlflow",
        "wandb",
        "kubeflow",
        "airflow",
        "prefect",
        "dagster",
        "vllm",
        "triton",
        "tgi",
        "bento",
        "ollama",
        "ray",
        "kuberay",
        "mlrun",
        "zenml",
        "evidently",
        # Infrastructure
        "kubernetes",
        "k8s",
        "docker",
        "helm",
        "terraform",
        "ansible",
        "aws",
        "gcp",
        "azure",
        "gke",
        "eks",
        "aks",
        # Data
        "postgresql",
        "mysql",
        "redis",
        "clickhouse",
        "snowflake",
        "bigquery",
        "kafka",
        "pulsar",
        "spark",
        "flink",
        "dbt",
        # Vector DBs
        "pinecone",
        "weaviate",
        "milvus",
        "qdrant",
        "chroma",
        "pgvector",
        # Monitoring
        "prometheus",
        "grafana",
        "datadog",
        "newrelic",
    ]

    text_lower = text.lower()
    found = []
    for kw in tech_keywords:
        if kw in text_lower and kw not in found:
            found.append(kw)

    return found


# ══════════════════════════════════════════════════════════════════
# Main Node Function
# ══════════════════════════════════════════════════════════════════


def node_scraper(state: AgentState) -> AgentState:
    """
    Scraper Agent: Dynamically invokes scraping tools based on target domains.
    Uses real tools: fetch_financial_news_rss for RSS feeds, fetch_webpage_playwright for webpages.
    Filters for India-relevant Agentic AI/LLMOps/ML roles.
    """
    logger.info("[Scraper] Starting scrape with real tools (India-focused)...")
    state["current_agent"] = "scraper"
    state["updated_at"] = datetime.now()

    # Simulate scraping delay
    time.sleep(0.1)

    # Example 1: Fetch financial/business news via RSS
    try:
        rss_result = fetch_financial_news_rss.invoke(
            {
                "feed_url": "http://feeds.bbci.co.uk/news/business/rss.xml",
                "max_items": 5,
            }
        )
        logger.info(
            f"[Scraper] RSS fetch returned {len(rss_result.get('articles', []))} articles"
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
                existing_tickers = {
                    m.get("ticker") for m in existing_metrics if m.get("ticker")
                }
                state["company_metrics"] = existing_metrics + [
                    mock_metrics.model_dump(mode="json")
                ]
    except Exception as e:
        logger.warning(f"[Scraper] RSS fetch failed: {e}")
        state["error_log"].append({
            "agent": "scraper",
            "tool": "fetch_financial_news_rss",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "severity": "warning",
        })

    # Scrape a real webpage via Playwright
    try:
        url = "https://boards.greenhouse.io/openai"
        logger.info(f"[Scraper] Playwright fetching live URL: {url}")
        page_result = fetch_webpage_playwright.invoke(
            {
                "url": url,
                "wait_for_timeout": 5000,
            }
        )
        logger.info(
            f"[Scraper] Playwright returned page: {page_result.get('title')}"
        )

        state["raw_scraped_pages"].append(
            {
                "url": page_result["url"],
                "html": page_result["html"],
                "markdown": page_result["markdown"],
                "metadata": {
                    "scraped_at": page_result["scraped_at"],
                    "scraper": "playwright-stub",
                    "status": 200,
                },
            }
        )
    except Exception as e:
        logger.warning(f"[Scraper] Playwright fetch failed: {e}")
        state["error_log"].append({
            "agent": "scraper",
            "tool": "fetch_webpage_playwright",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "severity": "error",
        })

    # 2. Fetch jobs from Greenhouse API (structured data, preferred path)
    new_job_dicts: List[Dict[str, Any]] = []
    logger.info(f"[Scraper] Querying {len(GREENHOUSE_BOARDS)} Greenhouse boards...")
    for company_name, board in GREENHOUSE_BOARDS.items():
        try:
            gh_result = search_greenhouse_jobs.invoke({
                "board": board,
                "max_results": 20,
            })
            if gh_result.get("error"):
                logger.warning(f"[Scraper] Greenhouse board '{board}' failed: {gh_result['error']}")
                continue
            for raw_job in gh_result.get("jobs", []):
                norm = normalize_greenhouse_job(raw_job)
                norm["company_name"] = company_name
                validated = validate_job_dict(norm)
                if validated:
                    new_job_dicts.append(validated)
                    logger.info(f"  -> [Greenhouse] {validated['title']} @ {company_name}")
        except Exception as e:
            logger.warning(f"[Scraper] Greenhouse board '{board}' exception: {e}")

    # 3. Fetch jobs from Lever boards (Playwright + BS4, no Gemini cost)
    LEVER_BOARDS: Dict[str, str] = {
        "Groww": "groww",
        "Dunzo": "dunzo",
        "Unacademy": "unacademy",
        "UpGrad": "upgrad",
    }
    logger.info(f"[Scraper] Querying {len(LEVER_BOARDS)} Lever boards...")
    for company_name, board in LEVER_BOARDS.items():
        try:
            lv_result = search_lever_jobs.invoke({
                "board": board,
                "max_results": 10,
            })
            if lv_result.get("error"):
                logger.warning(f"[Scraper] Lever board '{board}' failed: {lv_result['error']}")
                continue
            for raw_job in lv_result.get("jobs", []):
                norm = normalize_lever_job(raw_job)
                norm["company_name"] = company_name
                validated = validate_job_dict(norm)
                if validated:
                    new_job_dicts.append(validated)
                    logger.info(f"  -> [Lever] {validated['title']} @ {company_name}")
        except Exception as e:
            logger.warning(f"[Scraper] Lever board '{board}' exception: {e}")

    # 4. Extract Jobs from Playwright scraped pages using Gemini 2.5 Flash
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    class JobExtraction(BaseModel):
        jobs: list[JobOpening]

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    structured_llm = llm.with_structured_output(JobExtraction)

    existing_metrics = state.get("company_metrics", [])
    existing_jobs = state.get("job_openings", [])

    existing_tickers = {m.get("ticker") for m in existing_metrics if m.get("ticker")}
    if "RZPY" not in existing_tickers: # mock metrics logic kept for downstream agents
        pass

    for page in state.get("raw_scraped_pages", []):
        md_text = page.get("markdown", "")
        url = page.get("url", "")
        
        if len(md_text) > 50:
            try:
                logger.info(f"[Scraper] Extracting jobs via LLM from {url}...")
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
                        new_job_dicts.append(job.model_dump(mode="json"))
                        logger.info(f"  -> Extracted: {job.title} at {job.company_name}")
                        
            except Exception as e:
                logger.error(f"[Scraper] LLM Extraction failed for {url}: {e}")

    existing_job_ids = {j.get("job_id") for j in existing_jobs if j.get("job_id")}
    # Deduplicate based on generated ID (or job_hash if it existed)

    # Apply early-stopping guardrails
    filtered_jobs = filter_jobs(new_job_dicts)
    state["job_openings"] = existing_jobs + filtered_jobs

    gh_count = sum(1 for j in new_job_dicts if j.get("scraper_source") == "ats_greenhouse")
    lv_count = sum(1 for j in new_job_dicts if j.get("scraper_source") == "ats_lever")
    pw_count = len(new_job_dicts) - gh_count - lv_count
    logger.info(
        f"[Scraper] Added {len(filtered_jobs)} jobs ({gh_count} Greenhouse, {lv_count} Lever, {pw_count} Gemini/Playwright) after guardrails"
    )
    return state
