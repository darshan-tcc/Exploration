"""Async SQLAlchemy session and engine management."""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from factory_backend.core.config import settings

from sqlalchemy.pool import NullPool

# Engine using NullPool for async safety across multiple asyncio tasks/tests
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining async database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
