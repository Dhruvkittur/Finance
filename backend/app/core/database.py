"""
FinPilot AI — Async Database Engine
=====================================
SQLAlchemy async engine configuration with:
- Connection pooling
- Async session factory
- Base declarative model
- Table creation utility
"""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.core.config import settings

class GUID(TypeDecorator):
    """Platform-independent GUID type (PostgreSQL UUID or SQLite CHAR(36))."""
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value
            else:
                return uuid.UUID(str(value))

# ── Async Engine ──────────────────────────────────────────────────────────────

engine = create_async_engine(
    "sqlite+aiosqlite:///./finpilot.db",
    connect_args={"check_same_thread": False},
    echo=settings.DATABASE_ECHO,
)

# ── Session Factory ───────────────────────────────────────────────────────────

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ── Base Declarative Model ────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    Provides common fields: id, created_at, updated_at.
    """

    # Common primary key using GUID
    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# ── Dependency Injection ──────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Table Creation ────────────────────────────────────────────────────────────

async def create_db_tables() -> None:
    """
    Create all database tables defined in ORM models.
    Called during application startup (lifespan).
    In production, use Alembic migrations instead.
    """
    # Import all models to ensure they are registered with Base
    from app.models import (  # noqa: F401
        user,
        document,
        chat,
        workflow,
        report,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
