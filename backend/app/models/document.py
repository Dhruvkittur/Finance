"""
FinPilot AI — Document Model
==============================
SQLAlchemy ORM model for uploaded financial documents.
Tracks processing status, metadata, and vector embeddings.
"""

import uuid
from enum import Enum
from typing import Any, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, GUID


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"
    IMAGE = "image"
    UNKNOWN = "unknown"


class DocumentCategory(str, Enum):
    """AI-classified financial document categories."""
    ANNUAL_REPORT = "annual_report"
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    INVOICE = "invoice"
    CONTRACT = "contract"
    AUDIT_REPORT = "audit_report"
    TAX_REPORT = "tax_report"
    COMPLIANCE = "compliance"
    INVESTMENT_REPORT = "investment_report"
    BOARD_PRESENTATION = "board_presentation"
    OTHER = "other"


class Document(Base):
    """
    Represents an uploaded financial document with full processing metadata.
    """

    __tablename__ = "documents"

    # ── File Information ───────────────────────────────────────────────────────
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=True)  # SHA256

    # ── Document Metadata ──────────────────────────────────────────────────────
    doc_type: Mapped[str] = mapped_column(
        String(50), default=DocumentType.UNKNOWN, nullable=False
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100), default=DocumentCategory.OTHER, nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Extracted Content ──────────────────────────────────────────────────────
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    financial_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tables_extracted: Mapped[int] = mapped_column(Integer, default=0)
    images_extracted: Mapped[int] = mapped_column(Integer, default=0)

    # ── Processing State ───────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50), default=DocumentStatus.PENDING, nullable=False, index=True
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunks_count: Mapped[int] = mapped_column(Integer, default=0)
    embeddings_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ocr_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Vector Database Reference ──────────────────────────────────────────────
    chroma_collection_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vector_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # ── Versioning ─────────────────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("documents.id"), nullable=True
    )

    # ── Ownership ──────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    # ── Relationships ──────────────────────────────────────────────────────────
    uploaded_by: Mapped["User"] = relationship("User", back_populates="documents")  # noqa: F821
    chat_references: Mapped[List["ChatMessage"]] = relationship(  # noqa: F821
        "ChatMessage", back_populates="referenced_document"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename} status={self.status}>"

    @property
    def is_processed(self) -> bool:
        return self.status == DocumentStatus.PROCESSED

    @property
    def file_size_mb(self) -> float:
        return round(self.file_size / (1024 * 1024), 2)
