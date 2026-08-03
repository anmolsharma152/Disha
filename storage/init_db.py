"""
Disha - Database Initialization Script
Ensures pgvector extension and ORM tables are created in PostgreSQL.
"""

import asyncio
import logging
import os
import sys

from sqlalchemy import text

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from storage.db import Base, DATABASE_URL, get_async_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("disha.storage.init_db")


async def init_db():
    """Initialize database tables and pgvector extension."""
    db_url = os.environ.get("DATABASE_URL", DATABASE_URL)
    logger.info("Initializing database at %s...", db_url.split("@")[-1] if "@" in db_url else db_url)

    engine = await get_async_engine(db_url)

    try:
        async with engine.begin() as conn:
            # Enable pgvector extension if using PostgreSQL
            if "postgresql" in db_url:
                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    logger.info("[DB] Enabled 'vector' extension.")
                except Exception as e:
                    logger.warning("[DB] Could not enable 'vector' extension: %s", e)

            # Create all ORM tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("[DB] All database tables created successfully.")

    except Exception as e:
        logger.error("[DB] Database initialization failed: %s", e)
        raise e
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
