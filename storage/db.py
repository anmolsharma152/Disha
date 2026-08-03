"""
Disha - Database Storage & pgvector Integration
Async SQLAlchemy 2.0 models, repository methods, and pgvector cosine search.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

logger = logging.getLogger("disha.storage.db")

# Default database URL: PostgreSQL with asyncpg or fallback to SQLite async
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/disha_db"
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class JobOpeningModel(Base):
    """Postgres table for persistent job openings with vector embeddings."""
    __tablename__ = "job_openings"

    job_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    title_normalized: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    location_raw: Mapped[str] = mapped_column(String(300), nullable=False)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="IN")
    remote_policy: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    experience_level: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    employment_type: Mapped[str] = mapped_column(String(50), nullable=False, default="full_time")

    tech_stack: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skills_required: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skills_preferred: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    payout_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payout_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")

    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(200), nullable=False)
    scraper_source: Mapped[str] = mapped_column(String(50), nullable=False, default="career_page")

    # Vector embedding column (768 dimensions for Gemini embeddings)
    if HAS_PGVECTOR:
        embedding = mapped_column(Vector(768), nullable=True)
    else:
        embedding = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class DocumentChunkModel(Base):
    """Postgres table for document chunks and vector search."""
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    if HAS_PGVECTOR:
        embedding = mapped_column(Vector(768), nullable=True)
    else:
        embedding = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class VectorRepository:
    """Async repository for semantic search using pgvector."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def vector_search_jobs(
        self,
        query_embedding: List[float],
        limit: int = 10,
    ) -> List[JobOpeningModel]:
        """Perform native pgvector cosine distance search for jobs."""
        if not HAS_PGVECTOR or not query_embedding:
            logger.warning("[pgvector] pgvector not installed or query embedding empty")
            return []

        try:
            stmt = (
                select(JobOpeningModel)
                .where(JobOpeningModel.embedding.is_not(None))
                .order_by(JobOpeningModel.embedding.cosine_distance(query_embedding))
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("[pgvector] Vector search failed: %s", e)
            return []

    async def save_job(self, job_dict: Dict[str, Any], embedding: Optional[List[float]] = None) -> JobOpeningModel:
        """Persist job opening with embedding."""
        obj = JobOpeningModel(
            company_name=job_dict.get("company_name", "Unknown"),
            title=job_dict.get("title", "Untitled"),
            title_normalized=job_dict.get("title_normalized"),
            location_raw=job_dict.get("location_raw", "India"),
            location_city=job_dict.get("location_city"),
            location_state=job_dict.get("location_state"),
            location_country=job_dict.get("location_country", "IN"),
            remote_policy=str(job_dict.get("remote_policy", "unknown")),
            experience_level=str(job_dict.get("experience_level", "unknown")),
            tech_stack=job_dict.get("tech_stack", []),
            skills_required=job_dict.get("skills_required", []),
            skills_preferred=job_dict.get("skills_preferred", []),
            payout_min=job_dict.get("payout_min"),
            payout_max=job_dict.get("payout_max"),
            currency=job_dict.get("currency", "INR"),
            description_raw=job_dict.get("description_raw", ""),
            source_url=job_dict.get("source_url", ""),
            source_domain=job_dict.get("source_domain", ""),
            scraper_source=str(job_dict.get("scraper_source", "career_page")),
            embedding=embedding,
        )
        self.session.add(obj)
        await self.session.commit()
        return obj


async def get_async_engine(db_url: str = DATABASE_URL) -> AsyncEngine:
    """Create async SQLAlchemy engine."""
    return create_async_engine(db_url, echo=False)
