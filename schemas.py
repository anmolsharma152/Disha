"""
Project Alpha-Nexus - Core Data Schemas
Pydantic v2 models for validated data exchange across the pipeline.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import TypedDict


# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────

class RemotePolicy(str, Enum):
    """Remote work policy classification."""
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    REMOTE_FRIENDLY = "remote_friendly"
    UNKNOWN = "unknown"


class ExperienceLevel(str, Enum):
    """Standardized experience levels."""
    INTERN = "intern"
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    DIRECTOR = "director"
    VP = "vp"
    C_LEVEL = "c_level"
    UNKNOWN = "unknown"


class ScraperSource(str, Enum):
    """Origin of scraped data."""
    CAREER_PAGE = "career_page"
    ATS_GREENHOUSE = "ats_greenhouse"
    ATS_LEVER = "ats_lever"
    ATS_WORKDAY = "ats_workday"
    ATS_ASHBY = "ats_ashby"
    ATS_BAMBOO = "ats_bamboo"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    INDEED = "indeed"
    RSS_FEED = "rss_feed"
    SEC_FILING = "sec_filing"
    FINANCIAL_API = "financial_api"
    MANUAL = "manual"


# ──────────────────────────────────────────────────────────────
# Core Domain Models
# ──────────────────────────────────────────────────────────────

class CompanyMetrics(BaseModel):
    """
    Validated financial & operational metrics for a target company.
    All monetary values in USD unless otherwise noted.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
        extra="forbid",
    )

    # Identity
    company_name: str = Field(..., min_length=1, max_length=200)
    ticker: Optional[str] = Field(None, pattern=r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")
    company_id: UUID = Field(default_factory=uuid4)

    # Market Data
    market_cap: Optional[float] = Field(None, ge=0, description="Market capitalization in USD")
    enterprise_value: Optional[float] = Field(None, ge=0, description="Enterprise value in USD")
    pe_ratio: Optional[float] = Field(None, ge=0, description="Price-to-earnings ratio")
    pb_ratio: Optional[float] = Field(None, ge=0, description="Price-to-book ratio")
    ps_ratio: Optional[float] = Field(None, ge=0, description="Price-to-sales ratio")

    # Revenue & Growth
    revenue_ttm: Optional[float] = Field(None, ge=0, description="Trailing twelve months revenue in USD")
    revenue_growth_yoy: Optional[float] = Field(None, description="Year-over-year revenue growth (%)")
    revenue_growth_qoq: Optional[float] = Field(None, description="Quarter-over-quarter revenue growth (%)")
    gross_margin: Optional[float] = Field(None, ge=0, le=100, description="Gross margin (%)")
    operating_margin: Optional[float] = Field(None, ge=-100, le=100, description="Operating margin (%)")
    net_margin: Optional[float] = Field(None, ge=-100, le=100, description="Net profit margin (%)")

    # Headcount & Workforce
    headcount_current: Optional[int] = Field(None, ge=0)
    headcount_6m_ago: Optional[int] = Field(None, ge=0)
    headcount_12m_ago: Optional[int] = Field(None, ge=0)
    headcount_growth_6m: Optional[float] = Field(None, description="6-month headcount growth (%)")
    headcount_growth_12m: Optional[float] = Field(None, description="12-month headcount growth (%)")

    # Cash & Debt
    cash_and_equivalents: Optional[float] = Field(None, ge=0, description="Cash & equivalents in USD")
    total_debt: Optional[float] = Field(None, ge=0, description="Total debt in USD")
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow in USD")

    # Metadata
    source_url: str = Field(..., description="Primary source URL for this data")
    source_domain: str = Field(..., description="Domain of source (e.g., finance.yahoo.com)")
    scraper_source: ScraperSource = Field(ScraperSource.FINANCIAL_API)
    confidence_score: float = Field(0.5, ge=0.0, le=1.0, description="Data confidence 0-1")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    fiscal_period: Optional[str] = Field(None, description="e.g., '2024-Q3', '2024-FY'")

    @field_validator("headcount_growth_6m", "headcount_growth_12m", mode="before")
    @classmethod
    def compute_headcount_growth(cls, v: Optional[float], info) -> Optional[float]:
        """Auto-compute growth if current and historical headcounts present."""
        if v is not None:
            return v
        data = info.data
        current = data.get("headcount_current")
        past_6m = data.get("headcount_6m_ago")
        past_12m = data.get("headcount_12m_ago")
        field_name = info.field_name
        if field_name == "headcount_growth_6m" and current and past_6m and past_6m > 0:
            return round(((current - past_6m) / past_6m) * 100, 2)
        if field_name == "headcount_growth_12m" and current and past_12m and past_12m > 0:
            return round(((current - past_12m) / past_12m) * 100, 2)
        return None

    def model_post_init(self, __context: Any) -> None:
        """Ensure derived growth fields are computed."""
        if self.headcount_growth_6m is None and self.headcount_current and self.headcount_6m_ago:
            if self.headcount_6m_ago > 0:
                self.headcount_growth_6m = round(
                    ((self.headcount_current - self.headcount_6m_ago) / self.headcount_6m_ago) * 100, 2
                )
        if self.headcount_growth_12m is None and self.headcount_current and self.headcount_12m_ago:
            if self.headcount_12m_ago > 0:
                self.headcount_growth_12m = round(
                    ((self.headcount_current - self.headcount_12m_ago) / self.headcount_12m_ago) * 100, 2
                )


class JobOpening(BaseModel):
    """
    Validated job posting with extracted tech stack and compensation intelligence.
    """
    model_config = ConfigDict(
        validate_assignment=True,
        ser_json_timedelta="iso8601",
        extra="forbid",
    )

    # Identity
    job_id: UUID = Field(default_factory=uuid4)
    company_name: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=300)
    title_normalized: Optional[str] = Field(None, max_length=300)

    # Location & Policy
    location_raw: str = Field(..., description="Original location string from posting")
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = Field("US", max_length=2)
    remote_policy: RemotePolicy = RemotePolicy.UNKNOWN
    timezone: Optional[str] = None

    # Role Classification
    experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN
    department: Optional[str] = None
    team: Optional[str] = None
    employment_type: str = Field("full_time", pattern="^(full_time|part_time|contract|internship|temp)$")

    # Tech Stack & Skills (extracted via NER/regex/LLM)
    tech_stack: List[str] = Field(default_factory=list, description="Canonicalized technology names")
    skills_required: List[str] = Field(default_factory=list)
    skills_preferred: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    # Compensation
    payout_min: Optional[int] = Field(None, ge=0, description="Annual base minimum in USD")
    payout_max: Optional[int] = Field(None, ge=0, description="Annual base maximum in USD")
    equity_min: Optional[int] = Field(None, ge=0, description="Annual equity grant minimum in USD")
    equity_max: Optional[int] = Field(None, ge=0, description="Annual equity grant maximum in USD")
    bonus_target: Optional[int] = Field(None, ge=0, description="Annual bonus target in USD")
    sign_on_bonus: Optional[int] = Field(None, ge=0, description="Sign-on bonus in USD")
    currency: str = Field("USD", pattern="^[A-Z]{3}$")
    compensation_source: Literal["posted", "estimated", "glassdoor", "levels_fyi", "h1b"] = "estimated"
    compensation_confidence: float = Field(0.3, ge=0.0, le=1.0)

    # Visa & Legal
    visa_sponsorship: Optional[bool] = None
    h1b_eligible: Optional[bool] = None
    security_clearance: Optional[str] = None

    # Content
    description_raw: str = Field(..., description="Full raw job description text")
    description_clean: Optional[str] = None
    requirements_raw: Optional[str] = None
    benefits_raw: Optional[str] = None

    # Metadata
    source_url: str = Field(..., description="Direct URL to job posting")
    source_domain: str = Field(..., description="Domain of source")
    scraper_source: ScraperSource = ScraperSource.CAREER_PAGE
    posted_date: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    application_url: Optional[str] = None
    job_hash: Optional[str] = Field(None, description="Content hash for deduplication")

    @field_validator("payout_max", mode="after")
    @classmethod
    def validate_payout_range(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure max >= min if both present."""
        if v is not None and info.data.get("payout_min") is not None:
            if v < info.data["payout_min"]:
                raise ValueError("payout_max must be >= payout_min")
        return v

    @field_validator("tech_stack", "skills_required", "skills_preferred", mode="before")
    @classmethod
    def deduplicate_skills(cls, v: List[str]) -> List[str]:
        """Case-insensitive deduplication preserving order."""
        seen = set()
        result = []
        for item in v or []:
            key = item.lower().strip()
            if key and key not in seen:
                seen.add(key)
                result.append(item.strip())
        return result

    def model_post_init(self, __context: Any) -> None:
        """Auto-normalize title if not provided."""
        if not self.title_normalized:
            self.title_normalized = self._normalize_title(self.title)

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Map vendor-specific titles to canonical roles."""
        replacements = {
            r"\bsr\.\b": "senior",
            r"\bjr\.\b": "junior",
            r"\bsoftware engineer\b": "Software Engineer",
            r"\bbackend\b": "Backend",
            r"\bfrontend\b": "Frontend",
            r"\bfullstack\b": "Full Stack",
            r"\bdevops\b": "DevOps",
            r"\bsre\b": "SRE",
            r"\bml\b": "Machine Learning",
            r"\bai\b": "AI",
            r"\bdata scientist\b": "Data Scientist",
            r"\bdata engineer\b": "Data Engineer",
        }
        import re
        normalized = title.strip()
        for pattern, repl in replacements.items():
            normalized = re.sub(pattern, repl, normalized, flags=re.IGNORECASE)
        return normalized

    @property
    def payout_midpoint(self) -> Optional[int]:
        """Midpoint of posted range."""
        if self.payout_min is not None and self.payout_max is not None:
            return (self.payout_min + self.payout_max) // 2
        return self.payout_min or self.payout_max

    @property
    def total_comp_estimate(self) -> Optional[int]:
        """Rough total comp estimate (base + equity + bonus)."""
        base = self.payout_midpoint or 0
        equity = ((self.equity_min or 0) + (self.equity_max or 0)) // 2 if self.equity_min or self.equity_max else 0
        bonus = self.bonus_target or 0
        return base + equity + bonus if any([base, equity, bonus]) else None

    def model_dump(self, *args, **kwargs):
        """Ensure computed properties are included in serialization."""
        data = super().model_dump(*args, **kwargs)
        data["payout_midpoint"] = self.payout_midpoint
        data["total_comp_estimate"] = self.total_comp_estimate
        return data


# ──────────────────────────────────────────────────────────────
# LangGraph Agent State
# ──────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    """
    Complete state schema for the LangGraph multi-agent orchestrator.
    All fields optional to allow incremental construction.
    """

    # ─── Conversation & Intent ───
    messages: List[Any]  # List[BaseMessage] - avoided import for decoupling
    user_query: str
    user_id: Optional[str]
    session_id: str

    # ─── Routing & Control ───
    routing_key: Literal[
        "scraper",
        "financial_analyst",
        "career_strategy",
        "learning_companion",
        "synthesize",
        "error_recovery",
        "end",
    ]
    iteration: int
    max_iterations: int
    current_agent: Optional[str]
    delegation_history: List[Dict[str, Any]]

    # ─── Extracted Data (append-only) ───
    company_metrics: List[Dict[str, Any]]  # CompanyMetrics model_dump()
    job_openings: List[Dict[str, Any]]     # JobOpening model_dump()
    raw_scraped_pages: List[Dict[str, Any]]  # {url, html, markdown, metadata}

    # ─── Analysis Outputs ───
    financial_analysis: Dict[str, Any]  # Per-company scores, risk flags, ratios
    career_recommendations: List[Dict[str, Any]]  # Ranked job matches with reasoning
    learning_roadmap: Dict[str, Any]  # Personalized learning path with papers, courses
    market_intelligence: Dict[str, Any]  # Sector trends, salary benchmarks

    # ─── Resilience & Error Handling ───
    error_log: List[Dict[str, Any]]  # {agent, error, timestamp, attempt}
    retry_count: Dict[str, int]  # {agent_name: attempts}
    circuit_breakers: Dict[str, bool]  # {domain: is_open}
    fallback_activated: Dict[str, bool]  # {pipeline_stage: used_fallback}
    guardrail_stats: Dict[str, int]  # {jobs_dropped, companies_dropped}

    # ─── RAG & Knowledge ───
    retrieved_chunks: List[Dict[str, Any]]  # Vector search results
    knowledge_gaps: List[str]  # Identified missing info for next iteration

    # ─── Final Output ───
    final_answer: Optional[str]
    answer_confidence: float
    citations: List[Dict[str, Any]]  # Source attribution

    # ─── Metadata ───
    started_at: datetime
    updated_at: datetime
    total_tokens: int
    total_cost_usd: float


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def create_initial_state(
    user_query: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    max_iterations: int = 6,
) -> AgentState:
    """Factory for a clean initial agent state."""
    import uuid
    now = datetime.utcnow()
    return AgentState(
        messages=[],
        user_query=user_query,
        user_id=user_id,
        session_id=session_id or str(uuid.uuid4()),
        routing_key="scraper",
        iteration=0,
        max_iterations=max_iterations,
        current_agent=None,
        delegation_history=[],
        company_metrics=[],
        job_openings=[],
        raw_scraped_pages=[],
        financial_analysis={},
        career_recommendations=[],
        market_intelligence={},
        error_log=[],
        retry_count={},
        circuit_breakers={},
        fallback_activated={},
        retrieved_chunks=[],
        knowledge_gaps=[],
        final_answer=None,
        answer_confidence=0.0,
        citations=[],
        started_at=now,
        updated_at=now,
        total_tokens=0,
        total_cost_usd=0.0,
    )


def validate_company_metrics(data: Dict[str, Any]) -> CompanyMetrics:
    """Validate and coerce dict to CompanyMetrics."""
    return CompanyMetrics.model_validate(data)


def validate_job_opening(data: Dict[str, Any]) -> JobOpening:
    """Validate and coerce dict to JobOpening."""
    return JobOpening.model_validate(data)


# ──────────────────────────────────────────────────────────────
# Type Aliases for Common Patterns
# ──────────────────────────────────────────────────────────────

CompanyMetricsList = List[CompanyMetrics]
JobOpeningList = List[JobOpening]
ScrapedPageDict = Dict[str, Any]
ErrorEntry = Dict[str, Any]
CitationDict = Dict[str, Any]

__all__ = [
    # Enums
    "RemotePolicy",
    "ExperienceLevel",
    "ScraperSource",
    # Models
    "CompanyMetrics",
    "JobOpening",
    # State
    "AgentState",
    # Helpers
    "create_initial_state",
    "validate_company_metrics",
    "validate_job_opening",
    # Type aliases
    "CompanyMetricsList",
    "JobOpeningList",
    "ScrapedPageDict",
    "ErrorEntry",
    "CitationDict",
]