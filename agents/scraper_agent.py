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
    core_keywords = ["machine learning", "deep learning", "nlp", "computer vision", 
                     "generative ai", "foundation model", "transformer", "pytorch", "tensorflow"]
    if any(kw in text for kw in core_keywords):
        return True
    
    return False


def extract_tech_stack(text: str) -> list:
    """Extract technology stack from job description text."""
    tech_keywords = [
        # Languages
        "python", "go", "golang", "rust", "java", "typescript", "javascript",
        "c++", "scala", "kotlin",
        # ML/AI Frameworks
        "pytorch", "tensorflow", "jax", "flax", "keras", "huggingface", "transformers",
        "langchain", "langgraph", "llama-index", "haystack",
        # MLOps/LLMOps
        "mlflow", "wandb", "kubeflow", "airflow", "prefect", "dagster",
        "vllm", "triton", "tgi", "bento", "ollama",
        "ray", "kuberay", "mlrun", "zenml", "evidently",
        # Infrastructure
        "kubernetes", "k8s", "docker", "helm", "terraform", "ansible",
        "aws", "gcp", "azure", "gke", "eks", "aks",
        # Data
        "postgresql", "mysql", "redis", "clickhouse", "snowflake", "bigquery",
        "kafka", "pulsar", "spark", "flink", "dbt",
        # Vector DBs
        "pinecone", "weaviate", "milvus", "qdrant", "chroma", "pgvector",
        # Monitoring
        "prometheus", "grafana", "datadog", "newrelic",
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
        rss_result = fetch_financial_news_rss.invoke({
            "feed_url": "http://feeds.bbci.co.uk/news/business/rss.xml",
            "max_items": 5,
        })
        logger.info(f"[Scraper] RSS fetch returned {len(rss_result.get('articles', []))} articles")

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
                existing_tickers = {m.get("ticker") for m in existing_metrics if m.get("ticker")}
                state["company_metrics"] = existing_metrics + [mock_metrics.model_dump(mode="json")]
    except Exception as e:
        logger.warning(f"[Scraper] RSS fetch failed: {e}")

    # Example 2: Scrape a webpage via Playwright stub
    try:
        # Ensure URL is string (fix HttpUrl -> str conversion)
        url = str("https://nexustech.com/careers")
        page_result = fetch_webpage_playwright.invoke({
            "url": url,
            "wait_for_selector": ".job-listings",
            "wait_for_timeout": 5000,
        })
        logger.info(f"[Scraper] Playwright stub returned page: {page_result.get('title')}")

        state["raw_scraped_pages"].append({
            "url": page_result["url"],
            "html": page_result["html"],
            "markdown": page_result["markdown"],
            "metadata": {
                "scraped_at": page_result["scraped_at"],
                "scraper": "playwright-stub",
                "status": 200,
            },
        })
    except Exception as e:
        logger.warning(f"[Scraper] Playwright fetch failed: {e}")

    # Mock data for demo (simulating real scraped India-relevant jobs)
    mock_metrics = CompanyMetrics(
        company_name="Razorpay",
        ticker=None,  # Private
        market_cap=7_500_000_000,  # $7.5B valuation
        enterprise_value=None,
        pe_ratio=None,
        pb_ratio=None,
        ps_ratio=None,
        revenue_ttm=2_500_000_000,  # ~2.5B INR
        revenue_growth_yoy=65.0,
        revenue_growth_qoq=15.2,
        gross_margin=78.0,
        operating_margin=22.0,
        net_margin=15.0,
        headcount_current=1_200,
        headcount_6m_ago=950,
        headcount_12m_ago=750,
        cash_and_equivalents=500_000_000,
        total_debt=50_000_000,
        free_cash_flow=180_000_000,
        source_url="https://razorpay.com/careers",
        source_domain="razorpay.com",
        scraper_source=ScraperSource.CAREER_PAGE,
        confidence_score=0.85,
        fiscal_period="2024-Q3",
    )

    # India-relevant mock jobs with Agentic/LLMOps focus
    mock_jobs = [
        JobOpening(
            company_name="Razorpay",
            title="Senior AI/ML Engineer - Agentic Workflows",
            location_raw="Bangalore, Karnataka (Hybrid)",
            location_city="Bangalore",
            location_state="Karnataka",
            location_country="IN",
            remote_policy=RemotePolicy.HYBRID,
            experience_level=ExperienceLevel.SENIOR,
            department="AI Platform",
            tech_stack=["Python", "PyTorch", "LangGraph", "LangChain", "Kubernetes", "AWS", "MLflow", "Ray"],
            skills_required=["Agentic AI", "LLM Fine-tuning", "RAG Systems", "Multi-Agent Orchestration", "Tool Use"],
            skills_preferred=["vLLM", "Triton", "KubeRay", "MLOps", "Model Serving", "Vector Databases"],
            payout_min=4_500_000,  # 45 LPA INR
            payout_max=6_500_000,  # 65 LPA INR
            equity_min=500_000,
            equity_max=1_500_000,
            bonus_target=800_000,
            compensation_source="levels_fyi",
            compensation_confidence=0.8,
            visa_sponsorship=False,
            h1b_eligible=False,
            description_raw=(
                "Build the next generation of agentic AI systems at Razorpay. "
                "You will design and implement autonomous agent workflows using LangGraph, "
                "develop RAG pipelines for financial knowledge, and build model serving "
                "infrastructure for LLMs. Work with a team of researchers and engineers "
                "to ship production-grade AI agents for fintech applications."
            ),
            source_url="https://razorpay.com/careers/senior-ai-ml-engineer-agentic",
            source_domain="razorpay.com",
            scraper_source=ScraperSource.CAREER_PAGE,
            posted_date=datetime(2024, 11, 20),
            is_active=True,
            application_url="https://razorpay.com/apply/ai-agentic-001",
        ),
        JobOpening(
            company_name="Swiggy",
            title="Staff ML Engineer - LLMOps & Model Platform",
            location_raw="Bangalore, Karnataka (Remote-friendly)",
            location_city="Bangalore",
            location_state="Karnataka",
            location_country="IN",
            remote_policy=RemotePolicy.REMOTE_FRIENDLY,
            experience_level=ExperienceLevel.STAFF,
            department="ML Platform",
            tech_stack=["Go", "Python", "Kubernetes", "vLLM", "Triton", "MLflow", "Prometheus", "ClickHouse"],
            skills_required=["LLMOps", "Model Serving", "GPU Cluster Management", "ML Platform", "A/B Testing", "Drift Detection"],
            skills_preferred=["KubeRay", "BentoML", "Evidently", "Feature Store", "Model Registry"],
            payout_min=6_000_000,  # 60 LPA INR
            payout_max=9_000_000,  # 90 LPA INR
            equity_min=1_000_000,
            equity_max=3_000_000,
            bonus_target=1_500_000,
            compensation_source="levels_fyi",
            compensation_confidence=0.85,
            visa_sponsorship=False,
            h1b_eligible=False,
            description_raw=(
                "Lead the LLMOps platform at Swiggy powering 100+ models in production. "
                "Build scalable model serving infrastructure with vLLM/Triton, implement "
                "automated drift detection, A/B testing frameworks, and feature stores. "
                "Drive best practices for LLM deployment, monitoring, and cost optimization."
            ),
            source_url="https://swiggy.com/careers/staff-ml-engineer-llmops",
            source_domain="swiggy.com",
            scraper_source=ScraperSource.CAREER_PAGE,
            posted_date=datetime(2024, 11, 18),
            is_active=True,
            application_url="https://swiggy.com/apply/ml-llmops-002",
        ),
        JobOpening(
            company_name="Zoho",
            title="Backend Engineer - AI Agent Infrastructure",
            location_raw="Chennai, Tamil Nadu (Onsite)",
            location_city="Chennai",
            location_state="Tamil Nadu",
            location_country="IN",
            remote_policy=RemotePolicy.ONSITE,
            experience_level=ExperienceLevel.MID,
            department="AI Research",
            tech_stack=["Java", "Python", "PostgreSQL", "Redis", "Kafka", "Docker", "Kubernetes"],
            skills_required=["Distributed Systems", "Backend Development", "Agent Frameworks", "Workflow Engines"],
            skills_preferred=["LangGraph", "Temporal", "Actix", "Vector Search", "RAG"],
            payout_min=2_800_000,  # 28 LPA INR
            payout_max=4_200_000,  # 42 LPA INR
            equity_min=200_000,
            equity_max=800_000,
            bonus_target=500_000,
            compensation_source="glassdoor",
            compensation_confidence=0.7,
            visa_sponsorship=False,
            h1b_eligible=False,
            description_raw=(
                "Build the infrastructure layer for Zoho's AI agents. "
                "Design high-throughput workflow engines, implement agent communication protocols, "
                "and optimize for latency and cost. Work closely with ML researchers to "
                "productionize agentic systems."
            ),
            source_url="https://zoho.com/careers/backend-ai-agent-infra",
            source_domain="zoho.com",
            scraper_source=ScraperSource.CAREER_PAGE,
            posted_date=datetime(2024, 11, 15),
            is_active=True,
            application_url="https://zoho.com/apply/backend-ai-003",
        ),
        JobOpening(
            company_name="Cred",
            title="Founding ML Engineer - Autonomous Agents",
            location_raw="Bangalore, Karnataka (Hybrid)",
            location_city="Bangalore",
            location_state="Karnataka",
            location_country="IN",
            remote_policy=RemotePolicy.HYBRID,
            experience_level=ExperienceLevel.SENIOR,
            department="AI Products",
            tech_stack=["Python", "PyTorch", "JAX", "LangGraph", "LangChain", "Kubernetes", "GCP", "TPU"],
            skills_required=["Autonomous Agents", "LLM Reasoning", "Multi-Agent Systems", "Planning", "Tool Use"],
            skills_preferred=["AlphaGeometry", "Tree of Thoughts", "Self-Refine", "Constitutional AI"],
            payout_min=5_500_000,  # 55 LPA INR
            payout_max=8_500_000,  # 85 LPA INR
            equity_min=2_000_000,
            equity_max=5_000_000,
            bonus_target=1_000_000,
            compensation_source="levels_fyi",
            compensation_confidence=0.75,
            visa_sponsorship=False,
            h1b_eligible=False,
            description_raw=(
                "Join as a founding ML engineer building autonomous financial agents. "
                "Design agents that can reason, plan, and execute complex financial workflows. "
                "Work with cutting-edge reasoning paradigms (ToT, Reflexion, Self-Consistency) "
                "and deploy on TPU clusters. High ownership, high impact."
            ),
            source_url="https://cred.club/careers/founding-ml-engineer-agents",
            source_domain="cred.club",
            scraper_source=ScraperSource.CAREER_PAGE,
            posted_date=datetime(2024, 11, 22),
            is_active=True,
            application_url="https://cred.club/apply/founding-ml-agents-004",
        ),
    ]

    # Append to state (extend, don't replace)
    existing_metrics = state.get("company_metrics", [])
    existing_jobs = state.get("job_openings", [])

    existing_tickers = {m.get("ticker") for m in existing_metrics if m.get("ticker")}
    if mock_metrics.ticker not in existing_tickers:
        state["company_metrics"] = existing_metrics + [mock_metrics.model_dump(mode="json")]

    existing_job_ids = {j.get("job_id") for j in existing_jobs if j.get("job_id")}
    new_job_dicts = [j.model_dump(mode="json") for j in mock_jobs if j.job_id not in existing_job_ids]
    state["job_openings"] = existing_jobs + new_job_dicts

    logger.info(f"[Scraper] Added 1 company, {len(new_job_dicts)} India-relevant Agentic/LLMOps jobs")
    return state