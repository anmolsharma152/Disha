"""
Project Alpha-Nexus - Database Layer (Async PostgreSQL + pgvector)
SQLAlchemy 2.0 async models with pgvector support for embeddings.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import ARRAY, Float
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Import our Pydantic schemas for reference
from schemas import CompanyMetrics as CompanyMetricsSchema
from schemas import JobOpening as JobOpeningSchema
from schemas import RemotePolicy, ExperienceLevel, ScraperSource

# ══════════════════════════════════════════════════════════════════
# Async Database Configuration
# ══════════════════════════════════════════════════════════════════

# Async PostgreSQL URL with pgvector support
# Default to SQLite for local dev if no DATABASE_URL set
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./alpha_nexus.db")

# Ensure async driver
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Async engine configuration
if DATABASE_URL.startswith("sqlite"):
    async_engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    async_engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ══════════════════════════════════════════════════════════════════
# Base & Mixins
# ══════════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TimestampMixin:
    """Mixin for created/updated timestamps."""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class UUIDMixin:
    """Mixin for UUID primary key."""
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )


# ══════════════════════════════════════════════════════════════════
# SQLAlchemy Models
# ══════════════════════════════════════════════════════════════════

class CompanyMetrics(Base, TimestampMixin, UUIDMixin):
    """Company financial metrics from scraped sources."""
    __tablename__ = "company_metrics"

    # Identity
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)

    # Market Data
    market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    enterprise_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pb_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ps_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Revenue & Growth
    revenue_ttm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_growth_yoy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_growth_qoq: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    operating_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Headcount
    headcount_current: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    headcount_6m_ago: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    headcount_12m_ago: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    headcount_growth_6m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    headcount_growth_12m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Cash & Debt
    cash_and_equivalents: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_debt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    free_cash_flow: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Metadata
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    scraper_source: Mapped[str] = mapped_column(String(50), nullable=False, default=ScraperSource.FINANCIAL_API.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    fiscal_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Embedded representation for vector search (pgvector)
    # 1536 dimensions for OpenAI ada-002, 3072 for text-embedding-3-large
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Computed fields stored as JSON
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_company_metrics_name_date", "company_name", "created_at"),
        Index("ix_company_metrics_ticker_date", "ticker", "created_at"),
    )

    def to_pydantic(self) -> CompanyMetricsSchema:
        """Convert to Pydantic schema."""
        data = {
            "id": self.id,
            "company_name": self.company_name,
            "ticker": self.ticker,
            "market_cap": self.market_cap,
            "enterprise_value": self.enterprise_value,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "ps_ratio": self.ps_ratio,
            "revenue_ttm": self.revenue_ttm,
            "revenue_growth_yoy": self.revenue_growth_yoy,
            "revenue_growth_qoq": self.revenue_growth_qoq,
            "gross_margin": self.gross_margin,
            "operating_margin": self.operating_margin,
            "net_margin": self.net_margin,
            "headcount_current": self.headcount_current,
            "headcount_6m_ago": self.headcount_6m_ago,
            "headcount_12m_ago": self.headcount_12m_ago,
            "headcount_growth_6m": self.headcount_growth_6m,
            "headcount_growth_12m": self.headcount_growth_12m,
            "cash_and_equivalents": self.cash_and_equivalents,
            "total_debt": self.total_debt,
            "free_cash_flow": self.free_cash_flow,
            "source_url": self.source_url,
            "source_domain": self.source_domain,
            "scraper_source": ScraperSource(self.scraper_source),
            "confidence_score": self.confidence_score,
            "fiscal_period": self.fiscal_period,
            "last_updated": self.updated_at,
            "scraped_at": self.created_at,
        }
        data.update(self.extra_data or {})
        return CompanyMetricsSchema.model_validate(data)


class JobOpening(Base, TimestampMixin, UUIDMixin):
    """Job postings from career pages and ATS systems."""
    __tablename__ = "job_openings"

    # Identity
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    title_normalized: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # Location
    location_raw: Mapped[str] = mapped_column(Text, nullable=False)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_country: Mapped[str] = mapped_column(String(2), nullable=False, default="IN")  # India default
    remote_policy: Mapped[str] = mapped_column(String(20), nullable=False, default=RemotePolicy.UNKNOWN.value)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Role Classification
    experience_level: Mapped[str] = mapped_column(String(20), nullable=False, default=ExperienceLevel.UNKNOWN.value)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="full_time")

    # Tech Stack & Skills (stored as JSON arrays)
    tech_stack: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skills_required: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skills_preferred: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    certifications: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Compensation (INR for India focus)
    payout_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payout_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    equity_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    equity_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bonus_target: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sign_on_bonus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    compensation_source: Mapped[str] = mapped_column(String(20), nullable=False, default="estimated")
    compensation_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)

    # Visa & Legal (mostly N/A for India roles, but kept for completeness)
    visa_sponsorship: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    h1b_eligible: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    security_clearance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Content
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    description_clean: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    scraper_source: Mapped[str] = mapped_column(String(50), nullable=False, default=ScraperSource.CAREER_PAGE.value)
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    application_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # Embedded representation for vector similarity search
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # Computed fields
    extra_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_job_openings_company_active", "company_name", "is_active"),
        Index("ix_job_openings_location_active", "location_city", "is_active"),
        Index("ix_job_openings_posted_date", "posted_date"),
        Index("ix_job_openings_india_remote", "location_country", "remote_policy", "is_active"),
        UniqueConstraint("job_hash", name="uq_job_hash"),
    )

    def to_pydantic(self) -> JobOpeningSchema:
        """Convert to Pydantic schema."""
        data = {
            "job_id": self.id,
            "company_name": self.company_name,
            "title": self.title,
            "title_normalized": self.title_normalized,
            "location_raw": self.location_raw,
            "location_city": self.location_city,
            "location_state": self.location_state,
            "location_country": self.location_country,
            "remote_policy": RemotePolicy(self.remote_policy),
            "timezone": self.timezone,
            "experience_level": ExperienceLevel(self.experience_level),
            "department": self.department,
            "team": self.team,
            "employment_type": self.employment_type,
            "tech_stack": self.tech_stack or [],
            "skills_required": self.skills_required or [],
            "skills_preferred": self.skills_preferred or [],
            "certifications": self.certifications or [],
            "payout_min": self.payout_min,
            "payout_max": self.payout_max,
            "equity_min": self.equity_min,
            "equity_max": self.equity_max,
            "bonus_target": self.bonus_target,
            "sign_on_bonus": self.sign_on_bonus,
            "currency": self.currency,
            "compensation_source": self.compensation_source,
            "compensation_confidence": self.compensation_confidence,
            "visa_sponsorship": self.visa_sponsorship,
            "h1b_eligible": self.h1b_eligible,
            "security_clearance": self.security_clearance,
            "description_raw": self.description_raw,
            "description_clean": self.description_clean,
            "requirements_raw": self.requirements_raw,
            "benefits_raw": self.benefits_raw,
            "source_url": self.source_url,
            "source_domain": self.source_domain,
            "scraper_source": ScraperSource(self.scraper_source),
            "posted_date": self.posted_date,
            "scraped_at": self.created_at,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
            "application_url": self.application_url,
            "job_hash": self.job_hash,
        }
        data.update(self.extra_data or {})
        return JobOpeningSchema.model_validate(data)

    @property
    def payout_midpoint(self) -> Optional[int]:
        if self.payout_min is not None and self.payout_max is not None:
            return (self.payout_min + self.payout_max) // 2
        return self.payout_min or self.payout_max


# ══════════════════════════════════════════════════════════════════
# RAG/Resume Models (for Phase 2+)
# ══════════════════════════════════════════════════════════════════

class UserProfile(Base, TimestampMixin, UUIDMixin):
    """User profile with embedded skills for RAG matching."""
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    education: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    target_roles: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    min_salary_inr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)


class Resume(Base, TimestampMixin, UUIDMixin):
    """Parsed resume data with embeddings."""
    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_sections: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    skills_extracted: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)


class DocumentChunk(Base, TimestampMixin, UUIDMixin):
    """Generic document chunks for RAG."""
    __tablename__ = "document_chunks"

    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # arxiv, blog, pdf, etc.
    source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)

    __table_args__ = (
        Index("ix_document_chunks_source", "source_type", "source_id"),
    )


# ══════════════════════════════════════════════════════════════════
# Knowledge Graph Nodes & Edges (Skills ↔ Roles ↔ Companies)
# ══════════════════════════════════════════════════════════════════

class SkillNode(Base, TimestampMixin, UUIDMixin):
    """Canonical skill taxonomy node."""
    __tablename__ = "kg_skills"
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # language, framework, concept, tool
    aliases: Mapped[list] = mapped_column(JSON, default=list)  # ["py", "python3"]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)
    frequency: Mapped[int] = mapped_column(Integer, default=0)  # how many jobs require this


class RoleNode(Base, TimestampMixin, UUIDMixin):
    """Normalized role titles (ML Engineer, LLM Engineer, etc.)."""
    __tablename__ = "kg_roles"
    title: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    canonical_title: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    seniority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # junior, mid, senior, staff, principal
    function: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ml, backend, data, research
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avg_base_lpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # INR LPA benchmark
    market_demand_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100


class CompanyNode(Base, TimestampMixin, UUIDMixin):
    """Employer entities with sector/tags."""
    __tablename__ = "kg_companies"
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # fintech, ecommerce, saas, ai
    stage: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # startup, growth, public, enterprise
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tech_stack_summary: Mapped[list] = mapped_column(JSON, default=list)
    hiring_velocity: Mapped[float] = mapped_column(Float, default=0.0)  # jobs/month


# ══════════════════════════════════════════════════════════════════
# Knowledge Graph Edges (explicit relationships with weights)
# ══════════════════════════════════════════════════════════════════

class RoleSkillEdge(Base, TimestampMixin, UUIDMixin):
    """Role ↔ Skill with requirement type and weight."""
    __tablename__ = "kg_role_skills"
    role_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("kg_roles.id"), nullable=False, index=True)
    skill_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("kg_skills.id"), nullable=False, index=True)
    requirement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # required, preferred, nice_to_have
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # importance 0-1
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)  # how many job postings confirm this

    __table_args__ = (UniqueConstraint("role_id", "skill_id", "requirement_type", name="uq_role_skill_type"),)


class CompanyRoleEdge(Base, TimestampMixin, UUIDMixin):
    """Company ↔ Role (hiring relationship)."""
    __tablename__ = "kg_company_roles"
    company_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("kg_companies.id"), nullable=False, index=True)
    role_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("kg_roles.id"), nullable=False, index=True)
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_base_lpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("company_id", "role_id", name="uq_company_role"),)


class CompanySkillEdge(Base, TimestampMixin, UUIDMixin):
    """Company ↔ Skill (tech stack evidence)."""
    __tablename__ = "kg_company_skills"
    company_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("kg_companies.id"), nullable=False, index=True)
    skill_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("kg_skills.id"), nullable=False, index=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    __table_args__ = (UniqueConstraint("company_id", "skill_id", name="uq_company_skill"),)


# ══════════════════════════════════════════════════════════════════
# Repository Classes (Async)
# ══════════════════════════════════════════════════════════════════

class CompanyMetricsRepository:
    """Async repository for CompanyMetrics CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, metrics: CompanyMetricsSchema) -> CompanyMetrics:
        """Insert or update company metrics based on ticker+source_url."""
        existing = None
        if metrics.ticker:
            result = await self.session.execute(
                select(CompanyMetrics).where(
                    CompanyMetrics.ticker == metrics.ticker,
                    CompanyMetrics.source_url == metrics.source_url,
                )
            )
            existing = result.scalar_one_or_none()
        if not existing and metrics.company_name:
            result = await self.session.execute(
                select(CompanyMetrics).where(
                    CompanyMetrics.company_name == metrics.company_name,
                    CompanyMetrics.source_url == metrics.source_url,
                )
            )
            existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            for key, value in metrics.model_dump().items():
                if hasattr(existing, key) and key not in ("id", "created_at"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Insert new
            db_metrics = CompanyMetrics(
                id=metrics.company_id,
                company_name=metrics.company_name,
                ticker=metrics.ticker,
                market_cap=metrics.market_cap,
                enterprise_value=metrics.enterprise_value,
                pe_ratio=metrics.pe_ratio,
                pb_ratio=metrics.pb_ratio,
                ps_ratio=metrics.ps_ratio,
                revenue_ttm=metrics.revenue_ttm,
                revenue_growth_yoy=metrics.revenue_growth_yoy,
                revenue_growth_qoq=metrics.revenue_growth_qoq,
                gross_margin=metrics.gross_margin,
                operating_margin=metrics.operating_margin,
                net_margin=metrics.net_margin,
                headcount_current=metrics.headcount_current,
                headcount_6m_ago=metrics.headcount_6m_ago,
                headcount_12m_ago=metrics.headcount_12m_ago,
                headcount_growth_6m=metrics.headcount_growth_6m,
                headcount_growth_12m=metrics.headcount_growth_12m,
                cash_and_equivalents=metrics.cash_and_equivalents,
                total_debt=metrics.total_debt,
                free_cash_flow=metrics.free_cash_flow,
                source_url=metrics.source_url,
                source_domain=metrics.source_domain,
                scraper_source=metrics.scraper_source.value,
                confidence_score=metrics.confidence_score,
                fiscal_period=metrics.fiscal_period,
                extra_data={},
            )
            self.session.add(db_metrics)
            await self.session.commit()
            await self.session.refresh(db_metrics)
            return db_metrics

    async def get_latest_by_ticker(self, ticker: str) -> Optional[CompanyMetrics]:
        result = await self.session.execute(
            select(CompanyMetrics)
            .where(CompanyMetrics.ticker == ticker)
            .order_by(CompanyMetrics.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_all_recent(self, days: int = 30) -> List[CompanyMetrics]:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(CompanyMetrics)
            .where(CompanyMetrics.created_at >= cutoff)
            .order_by(CompanyMetrics.created_at.desc())
        )
        return list(result.scalars().all())

    async def vector_search(self, query_embedding: List[float], limit: int = 10) -> List[CompanyMetrics]:
        """Semantic search using cosine similarity on embedding arrays."""
        # For PostgreSQL with pgvector, use cosine_distance
        # For SQLite/array, we'll do Python-side filtering for now
        result = await self.session.execute(
            select(CompanyMetrics)
            .where(CompanyMetrics.embedding.is_not(None))
            .limit(limit * 5)  # Get more candidates for Python-side sorting
        )
        candidates = list(result.scalars().all())
        
        # Python-side cosine similarity (for SQLite dev)
        if candidates:
            import numpy as np
            query_vec = np.array(query_embedding)
            scored = []
            for c in candidates:
                if c.embedding:
                    cand_vec = np.array(c.embedding)
                    # Cosine similarity
                    sim = np.dot(query_vec, cand_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(cand_vec))
                    scored.append((sim, c))
            scored.sort(key=lambda x: -x[0])
            return [c for _, c in scored[:limit]]
        return []


class JobOpeningRepository:
    """Async repository for JobOpening CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, job: JobOpeningSchema) -> JobOpening:
        """Insert or update job based on job_hash or source_url."""
        existing = None
        if job.job_hash:
            result = await self.session.execute(
                select(JobOpening).where(JobOpening.job_hash == job.job_hash)
            )
            existing = result.scalar_one_or_none()
        if not existing:
            result = await self.session.execute(
                select(JobOpening).where(JobOpening.source_url == job.source_url)
            )
            existing = result.scalar_one_or_none()

        if existing:
            # Update
            for key, value in job.model_dump().items():
                if hasattr(existing, key) and key not in ("id", "created_at"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Insert
            db_job = JobOpening(
                id=job.job_id,
                company_name=job.company_name,
                title=job.title,
                title_normalized=job.title_normalized,
                location_raw=job.location_raw,
                location_city=job.location_city,
                location_state=job.location_state,
                location_country=job.location_country,
                remote_policy=job.remote_policy.value,
                timezone=job.timezone,
                experience_level=job.experience_level.value,
                department=job.department,
                team=job.team,
                employment_type=job.employment_type,
                tech_stack=job.tech_stack,
                skills_required=job.skills_required,
                skills_preferred=job.skills_preferred,
                certifications=job.certifications,
                payout_min=job.payout_min,
                payout_max=job.payout_max,
                equity_min=job.equity_min,
                equity_max=job.equity_max,
                bonus_target=job.bonus_target,
                sign_on_bonus=job.sign_on_bonus,
                currency=job.currency,
                compensation_source=job.compensation_source,
                compensation_confidence=job.compensation_confidence,
                visa_sponsorship=job.visa_sponsorship,
                h1b_eligible=job.h1b_eligible,
                security_clearance=job.security_clearance,
                description_raw=job.description_raw,
                description_clean=job.description_clean,
                requirements_raw=job.requirements_raw,
                benefits_raw=job.benefits_raw,
                source_url=job.source_url,
                source_domain=job.source_domain,
                scraper_source=job.scraper_source.value,
                posted_date=job.posted_date,
                expires_at=job.expires_at,
                is_active=job.is_active,
                application_url=job.application_url,
                job_hash=job.job_hash,
                extra_data={},
            )
            self.session.add(db_job)
            await self.session.commit()
            await self.session.refresh(db_job)
            return db_job

    async def get_active_by_company(self, company_name: str) -> List[JobOpening]:
        result = await self.session.execute(
            select(JobOpening)
            .where(
                JobOpening.company_name == company_name,
                JobOpening.is_active == True,
            )
            .order_by(JobOpening.posted_date.desc())
        )
        return result.scalars().all()

    async def get_recent(self, days: int = 30, limit: int = 100) -> List[JobOpening]:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(JobOpening)
            .where(
                JobOpening.posted_date >= cutoff,
                JobOpening.is_active == True,
            )
            .order_by(JobOpening.posted_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_india_remote_jobs(self, limit: int = 50) -> List[JobOpening]:
        """Get jobs relevant to India targeting (remote or India locations)."""
        result = await self.session.execute(
            select(JobOpening)
            .where(
                JobOpening.is_active == True,
                JobOpening.location_country == "IN",
            )
            .order_by(JobOpening.posted_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def vector_search(self, query_embedding: List[float], limit: int = 10) -> List[JobOpening]:
        """Semantic search using cosine similarity on embedding arrays."""
        result = await self.session.execute(
            select(JobOpening)
            .where(
                JobOpening.embedding.is_not(None),
                JobOpening.is_active == True,
            )
            .limit(limit * 5)
        )
        candidates = list(result.scalars().all())
        
        if candidates:
            import numpy as np
            query_vec = np.array(query_embedding)
            scored = []
            for c in candidates:
                if c.embedding:
                    cand_vec = np.array(c.embedding)
                    sim = np.dot(query_vec, cand_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(cand_vec))
                    scored.append((sim, c))
            scored.sort(key=lambda x: -x[0])
            return [c for _, c in scored[:limit]]
        return []


class DocumentChunkRepository:
    """Async repository for DocumentChunk (RAG)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        existing = await self.session.execute(
            select(DocumentChunk).where(
                DocumentChunk.source_type == chunk.source_type,
                DocumentChunk.source_id == chunk.source_id,
                DocumentChunk.chunk_index == chunk.chunk_index,
            )
        )
        existing = existing.scalar_one_or_none()

        if existing:
            for key, value in chunk.__dict__.items():
                if not key.startswith("_") and key not in ("id", "created_at"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            self.session.add(chunk)
            await self.session.commit()
            await self.session.refresh(chunk)
            return chunk

    async def vector_search(
        self,
        query_embedding: List[float],
        source_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[DocumentChunk]:
        """Semantic search across document chunks using cosine similarity."""
        query = (
            select(DocumentChunk)
            .where(DocumentChunk.embedding.is_not(None))
            .limit(limit * 5)
        )
        if source_types:
            query = query.where(DocumentChunk.source_type.in_(source_types))
        result = await self.session.execute(query)
        candidates = list(result.scalars().all())
        
        if candidates:
            import numpy as np
            query_vec = np.array(query_embedding)
            scored = []
            for c in candidates:
                if c.embedding:
                    cand_vec = np.array(c.embedding)
                    sim = np.dot(query_vec, cand_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(cand_vec))
                    scored.append((sim, c))
            scored.sort(key=lambda x: -x[0])
            return [c for _, c in scored[:limit]]
        return []


# ══════════════════════════════════════════════════════════════════
# Database Utilities (Async)
# ══════════════════════════════════════════════════════════════════

async def init_db() -> None:
    """Initialize database tables (includes pgvector extension)."""
    # For PostgreSQL, ensure pgvector extension exists
    if not DATABASE_URL.startswith("sqlite"):
        async with async_engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """Drop all tables (use with caution!)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_company_repo() -> CompanyMetricsRepository:
    """Get a company metrics repository with a new session."""
    session = AsyncSessionLocal()
    return CompanyMetricsRepository(session)


async def get_job_repo() -> JobOpeningRepository:
    """Get a job opening repository with a new session."""
    session = AsyncSessionLocal()
    return JobOpeningRepository(session)


async def get_doc_repo() -> DocumentChunkRepository:
    """Get a document chunk repository with a new session."""
    session = AsyncSessionLocal()
    return DocumentChunkRepository(session)


# ══════════════════════════════════════════════════════════════════
# Test / Demo
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio
    from sqlalchemy import text

    async def test_db():
        print("=" * 60)
        print("Initializing Async Database")
        print("=" * 60)

        await init_db()
        print(f"Database: {DATABASE_URL}")
        print("Tables created:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

        # Test write/read
        async with get_db_session() as session:
            company_repo = CompanyMetricsRepository(session)
            job_repo = JobOpeningRepository(session)

            # Create test company metrics
            from schemas import CompanyMetrics as CM
            test_metrics = CM(
                company_name="Test Corp India",
                ticker="TEST",
                market_cap=1_000_000_000,
                revenue_ttm=100_000_000,
                revenue_growth_yoy=25.0,
                headcount_current=500,
                headcount_6m_ago=400,
                source_url="https://example.com/test",
                source_domain="example.com",
            )
            await company_repo.upsert(test_metrics)
            print("\n✓ Company metrics inserted")

            # Read back
            retrieved = await company_repo.get_latest_by_ticker("TEST")
            print(f"✓ Retrieved: {retrieved.company_name} ({retrieved.ticker}) - ${retrieved.market_cap/1e9:.1f}B")

            # Create test job
            from schemas import JobOpening as JO
            from schemas import RemotePolicy, ExperienceLevel
            test_job = JO(
                company_name="Test Corp India",
                title="Senior ML Engineer - Agentic AI",
                location_raw="Bangalore, Karnataka (Hybrid)",
                location_city="Bangalore",
                location_state="Karnataka",
                location_country="IN",
                remote_policy=RemotePolicy.HYBRID,
                experience_level=ExperienceLevel.SENIOR,
                tech_stack=["Python", "PyTorch", "LangGraph", "Kubernetes"],
                payout_min=4_500_000,
                payout_max=6_500_000,
                currency="INR",
                description_raw="We are hiring for agentic AI...",
                source_url="https://example.com/jobs/1",
                source_domain="example.com",
                job_hash="abc123",
            )
            await job_repo.upsert(test_job)
            print("✓ Job opening inserted")

            jobs = await job_repo.get_active_by_company("Test Corp India")
            print(f"✓ Retrieved {len(jobs)} active jobs for Test Corp India")

        print("\n" + "=" * 60)
        print("Async Database test passed!")
        print("=" * 60)

    asyncio.run(test_db())