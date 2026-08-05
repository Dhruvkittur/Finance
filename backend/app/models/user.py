"""
FinPilot AI — User Model
==========================
SQLAlchemy ORM model for users with RBAC and OAuth support.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID
from app.core.security import UserRole


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """
    Core user model with authentication, roles, and profile data.
    Supports both password-based login and OAuth (Google).
    """

    __tablename__ = "users"

    # ── Identity ───────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Authentication ─────────────────────────────────────────────────────────
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # ── OAuth ──────────────────────────────────────────────────────────────────
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── RBAC ──────────────────────────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        String(50), default=UserRole.ANALYST, nullable=False
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Status ─────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50), default=UserStatus.ACTIVE, nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    login_count: Mapped[int] = mapped_column(default=0)

    # ── Preferences ────────────────────────────────────────────────────────────
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    language: Mapped[str] = mapped_column(String(10), default="en")
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    documents: Mapped[List["Document"]] = relationship(  # noqa: F821
        "Document", back_populates="uploaded_by", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(  # noqa: F821
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )
    workflows: Mapped[List["Workflow"]] = relationship(  # noqa: F821
        "Workflow", back_populates="created_by", cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(  # noqa: F821
        "Report", back_populates="created_by", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SUPERADMIN)
