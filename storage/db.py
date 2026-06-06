"""
Project Alpha-Nexus - Database Layer
SQLAlchemy models and connection for persistent storage.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional
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
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

# Import our Pydantic schemas for reference
from schemas import CompanyMetrics as CompanyMetricsSchema
from schemas import JobOpening as JobOpeningSchema
from schemas import RemotePolicy, ExperienceLevel, ScraperSource


# ══════════════════════════════════════════════════════════════════
# Database Configuration
# ══════════════════════════════════════════════════════════════════

# Use SQLite for dev, PostgreSQL via env var for prod
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alpha_nexus.db")

# Engine configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
        PG_UUID(as_uuid=True) if not DATABASE_URL.startswith("sqlite") else Text,
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

    # Computed fields stored as JSON for flexibility
    extra_data: Mapped[dict] = mapped_column(
        SQLiteJSON if DATABASE_URL.startswith("sqlite") else JSON,
        nullable=False,
        default=dict,
    )

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
        # Merge extra_data
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
    location_country: Mapped[str] = mapped_column(String(2), nullable=False, default="US")
    remote_policy: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RemotePolicy.UNKNOWN.value
    )
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Role Classification
    experience_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ExperienceLevel.UNKNOWN.value
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="full_time")

    # Tech Stack & Skills (stored as JSON arrays)
    tech_stack: Mapped[list] = mapped_column(
        SQLiteJSON if DATABASE_URL.startswith("sqlite") else JSON,
        nullable=False,
        default=list,
    )
    skills_required: Mapped[list] = mapped_column(
        SQLiteJSON if DATABASE_URL.startswith("sqlite") else JSON,
        nullable=False,
        default=list,
    )
    skills_preferred: Mapped[list] = mapped_column(
        SQLiteJSON if DATABASE_URL.startswith("sqlite") else JSON,
        nullable=False,
        default=list,
    )
    certifications: Mapped[list] = mapped_column(
        SQLiteJSON if DATABASE_URL.startswith("sqlite") else JSON,
        nullable=False,
        default=list,
    )

    # Compensation
    payout_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payout_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    equity_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    equity_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bonus_target: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sign_on_bonus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    compensation_source: Mapped[str] = mapped_column(String(20), nullable=False, default="estimated")
    compensation_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)

    # Visa & Legal
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

    # Computed fields
    extra_data: Mapped[dict] = mapped_column(
        SQLiteJSON if DATABASE_URL.startswith("sqlite") else JSON,
        nullable=False,
        default=dict,
    )

    __table_args__ = (
        Index("ix_job_openings_company_active", "company_name", "is_active"),
        Index("ix_job_openings_location_active", "location_city", "is_active"),
        Index("ix_job_openings_posted_date", "posted_date"),
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
# Repository Classes
# ══════════════════════════════════════════════════════════════════

class CompanyMetricsRepository:
    """Repository for CompanyMetrics CRUD operations."""

    def __init__(self, session):
        self.session = session

    def upsert(self, metrics: CompanyMetricsSchema) -> CompanyMetrics:
        """Insert or update company metrics based on ticker+source_url."""
        existing = None
        if metrics.ticker:
            existing = self.session.query(CompanyMetrics).filter(
                CompanyMetrics.ticker == metrics.ticker,
                CompanyMetrics.source_url == metrics.source_url,
            ).first()
        if not existing and metrics.company_name:
            existing = self.session.query(CompanyMetrics).filter(
                CompanyMetrics.company_name == metrics.company_name,
                CompanyMetrics.source_url == metrics.source_url,
            ).first()

        if existing:
            # Update existing
            for key, value in metrics.model_dump().items():
                if hasattr(existing, key) and key not in ("id", "created_at"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.session.commit()
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
            self.session.commit()
            self.session.refresh(db_metrics)
            return db_metrics

    def get_latest_by_ticker(self, ticker: str) -> Optional[CompanyMetrics]:
        return self.session.query(CompanyMetrics).filter(
            CompanyMetrics.ticker == ticker
        ).order_by(CompanyMetrics.created_at.desc()).first()

    def get_all_recent(self, days: int = 30) -> list[CompanyMetrics]:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.session.query(CompanyMetrics).filter(
            CompanyMetrics.created_at >= cutoff
        ).order_by(CompanyMetrics.created_at.desc()).all()


class JobOpeningRepository:
    """Repository for JobOpening CRUD operations."""

    def __init__(self, session):
        self.session = session

    def upsert(self, job: JobOpeningSchema) -> JobOpening:
        """Insert or update job based on job_hash or source_url."""
        existing = None
        if job.job_hash:
            existing = self.session.query(JobOpening).filter(
                JobOpening.job_hash == job.job_hash
            ).first()
        if not existing:
            existing = self.session.query(JobOpening).filter(
                JobOpening.source_url == job.source_url
            ).first()

        if existing:
            # Update
            for key, value in job.model_dump().items():
                if hasattr(existing, key) and key not in ("id", "created_at"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.session.commit()
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
            self.session.commit()
            self.session.refresh(db_job)
            return db_job

    def get_active_by_company(self, company_name: str) -> list[JobOpening]:
        return self.session.query(JobOpening).filter(
            JobOpening.company_name == company_name,
            JobOpening.is_active == True,
        ).order_by(JobOpening.posted_date.desc()).all()

    def get_recent(self, days: int = 30, limit: int = 100) -> list[JobOpening]:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.session.query(JobOpening).filter(
            JobOpening.posted_date >= cutoff,
            JobOpening.is_active == True,
        ).order_by(JobOpening.posted_date.desc()).limit(limit).all()


# ══════════════════════════════════════════════════════════════════
# Database Utilities
# ══════════════════════════════════════════════════════════════════

def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all tables (use with caution!)."""
    Base.metadata.drop_all(bind=engine)


@contextmanager
def get_db_session() -> Generator:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_company_repo() -> CompanyMetricsRepository:
    """Get a company metrics repository with a new session."""
    session = SessionLocal()
    return CompanyMetricsRepository(session)


def get_job_repo() -> JobOpeningRepository:
    """Get a job opening repository with a new session."""
    session = SessionLocal()
    return JobOpeningRepository(session)


# ══════════════════════════════════════════════════════════════════
# Test / Demo
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Initializing Database")
    print("=" * 60)

    init_db()
    print(f"Database: {DATABASE_URL}")
    print("Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

    # Test write/read
    with get_db_session() as session:
        company_repo = CompanyMetricsRepository(session)
        job_repo = JobOpeningRepository(session)

        # Create test company metrics
        from schemas import CompanyMetrics as CM
        test_metrics = CM(
            company_name="Test Corp",
            ticker="TEST",
            market_cap=1_000_000_000,
            revenue_ttm=100_000_000,
            revenue_growth_yoy=25.0,
            headcount_current=500,
            headcount_6m_ago=400,
            source_url="https://example.com/test",
            source_domain="example.com",
        )
        company_repo.upsert(test_metrics)
        print("\n✓ Company metrics inserted")

        # Read back
        retrieved = company_repo.get_latest_by_ticker("TEST")
        print(f"✓ Retrieved: {retrieved.company_name} ({retrieved.ticker}) - ${retrieved.market_cap/1e9:.1f}B")

        # Create test job
        from schemas import JobOpening as JO
        from schemas import RemotePolicy, ExperienceLevel
        test_job = JO(
            company_name="Test Corp",
            title="Senior Software Engineer",
            location_raw="San Francisco, CA",
            location_city="San Francisco",
            location_state="CA",
            remote_policy=RemotePolicy.HYBRID,
            experience_level=ExperienceLevel.SENIOR,
            tech_stack=["Python", "PostgreSQL", "AWS"],
            payout_min=160000,
            payout_max=220000,
            description_raw="We are hiring...",
            source_url="https://example.com/jobs/1",
            source_domain="example.com",
            job_hash="abc123",
        )
        job_repo.upsert(test_job)
        print("✓ Job opening inserted")

        jobs = job_repo.get_active_by_company("Test Corp")
        print(f"✓ Retrieved {len(jobs)} active jobs for Test Corp")

    print("\n" + "=" * 60)
    print("Database test passed!")
    print("=" * 60)