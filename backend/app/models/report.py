"""
FinPilot AI — Report, AuditLog, AgentRun Models
==================================================
"""

import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, GUID


class ReportType(str, Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    RISK_REPORT = "risk_report"
    COMPLIANCE_REPORT = "compliance_report"
    INVESTMENT_REPORT = "investment_report"
    FORECAST_REPORT = "forecast_report"
    FRAUD_REPORT = "fraud_report"
    AUDIT_REPORT = "audit_report"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    WORD = "word"
    POWERPOINT = "powerpoint"
    HTML = "html"


class Report(Base):
    """AI-generated financial report with export capabilities."""

    __tablename__ = "reports"

    # ── Report Info ────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Content ────────────────────────────────────────────────────────────────
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    charts_data: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # ── Source ────────────────────────────────────────────────────────────────
    source_documents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("chat_sessions.id"), nullable=True
    )

    # ── Export ────────────────────────────────────────────────────────────────
    exported_formats: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    export_paths: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── AI Metadata ────────────────────────────────────────────────────────────
    agents_used: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Ownership ──────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    created_by: Mapped["User"] = relationship("User", back_populates="reports")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Report id={self.id} type={self.report_type} title={self.title}>"


class AuditLog(Base):
    """Immutable audit log for all user actions (compliance requirement)."""

    __tablename__ = "audit_logs"

    # ── Action ────────────────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Request Context ────────────────────────────────────────────────────────
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    request_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ── Result ────────────────────────────────────────────────────────────────
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ── Actor ─────────────────────────────────────────────────────────────────
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True, index=True
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} user_id={self.user_id}>"


class AgentRun(Base):
    """Records metadata for each individual agent execution in the LangGraph pipeline."""

    __tablename__ = "agent_runs"

    # ── Agent Info ─────────────────────────────────────────────────────────────
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # ── Execution ─────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)

    # ── Association ────────────────────────────────────────────────────────────
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("chat_sessions.id"), nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} agent={self.agent_name} status={self.status}>"
