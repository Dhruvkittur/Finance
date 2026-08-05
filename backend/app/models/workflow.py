"""
FinPilot AI — Workflow Model
==============================
SQLAlchemy ORM model for React Flow visual workflow pipelines.
"""

import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, GUID


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class WorkflowRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Workflow(Base):
    """Visual workflow definition created in the React Flow builder."""

    __tablename__ = "workflows"

    # ── Workflow Definition ────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=WorkflowStatus.DRAFT, nullable=False
    )

    # ── React Flow Graph ───────────────────────────────────────────────────────
    nodes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    edges: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    viewport: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Trigger Configuration ──────────────────────────────────────────────────
    trigger_type: Mapped[str] = mapped_column(
        String(50), default="manual"  # manual | schedule | event | webhook
    )
    trigger_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Execution Stats ────────────────────────────────────────────────────────
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)

    # ── Ownership ──────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    # ── Relationships ──────────────────────────────────────────────────────────
    created_by: Mapped["User"] = relationship("User", back_populates="workflows")  # noqa: F821


class WorkflowRun(Base):
    """Records an execution instance of a workflow."""

    __tablename__ = "workflow_runs"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("workflows.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=WorkflowRunStatus.QUEUED, nullable=False
    )
    trigger_source: Mapped[str] = mapped_column(String(100), default="manual")
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    node_executions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
