"""
FinPilot AI — Chat Models
===========================
SQLAlchemy ORM models for chat sessions and messages
with agent metadata, citations, and streaming support.
"""

import uuid
from enum import Enum
from typing import Any, List, Optional

from sqlalchemy import (
    Boolean, Float, ForeignKey, Integer, JSON, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, GUID


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"
    TOOL = "tool"


class ChatSession(Base):
    """
    Represents a conversation session between a user and the AI agents.
    Contains full conversation history and session-level metadata.
    """

    __tablename__ = "chat_sessions"

    # ── Session Info ───────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(500), default="New Conversation")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Ownership ──────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False, index=True
    )

    # ── Session Statistics ─────────────────────────────────────────────────────
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    avg_response_time_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Context ────────────────────────────────────────────────────────────────
    active_documents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    session_context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")  # noqa: F821
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session",
        cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id} messages={self.message_count}>"


class ChatMessage(Base):
    """
    Individual message in a chat session.
    Stores the full agent reasoning chain, citations, and confidence scores.
    """

    __tablename__ = "chat_messages"

    # ── Message Content ────────────────────────────────────────────────────────
    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), default="markdown")

    # ── AI Metadata ────────────────────────────────────────────────────────────
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    response_time_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Agent Intelligence ─────────────────────────────────────────────────────
    agents_used: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    agent_timeline: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    reasoning_steps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tools_used: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hallucination_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Citations ──────────────────────────────────────────────────────────────
    citations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    source_documents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # ── Visualizations ─────────────────────────────────────────────────────────
    charts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tables: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # ── Referenced Document ────────────────────────────────────────────────────
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("documents.id"), nullable=True
    )

    # ── Feedback ───────────────────────────────────────────────────────────────
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    referenced_document: Mapped[Optional["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="chat_references"
    )

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} role={self.role} session_id={self.session_id}>"
