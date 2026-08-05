"""
FinPilot AI — Security Module
==============================
Handles:
- Password hashing (bcrypt)
- JWT token creation and verification
- Role-based access control (RBAC)
- OAuth2 utilities
- API key management
- Input sanitization for prompt injection protection
"""

import re
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Union

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password Hashing ──────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


# ── Role Definitions ──────────────────────────────────────────────────────────

class UserRole(str, Enum):
    """
    Role hierarchy for RBAC.
    Higher roles inherit permissions from lower roles.
    """
    VIEWER = "viewer"         # Read-only access to dashboards and reports
    ANALYST = "analyst"       # Can chat, upload documents, run analyses
    MANAGER = "manager"       # Can manage workflows, export reports
    ADMIN = "admin"           # Full access including user management
    SUPERADMIN = "superadmin" # System-level access, model configuration


ROLE_HIERARCHY = {
    UserRole.VIEWER: 0,
    UserRole.ANALYST: 1,
    UserRole.MANAGER: 2,
    UserRole.ADMIN: 3,
    UserRole.SUPERADMIN: 4,
}


def has_minimum_role(user_role: str, required_role: UserRole) -> bool:
    """Check if a user's role meets the minimum requirement."""
    user_level = ROLE_HIERARCHY.get(UserRole(user_role), -1)
    required_level = ROLE_HIERARCHY.get(required_role, 999)
    return user_level >= required_level


# ── JWT Token Management ──────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    subject: Union[str, int],
    role: str = UserRole.ANALYST,
    extra_claims: Optional[dict] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: User ID or email as the token subject
        role: User's role for RBAC
        extra_claims: Additional claims to embed in the token

    Returns:
        Signed JWT string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(subject),
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "type": "access",
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: Union[str, int]) -> str:
    """
    Create a long-lived JWT refresh token.

    Args:
        subject: User ID as the token subject

    Returns:
        Signed JWT refresh token string
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "type": "refresh",
        "jti": generate_secure_token(16),  # JWT ID for revocation
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT string

    Returns:
        Decoded payload dict

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI Dependencies ───────────────────────────────────────────────────────

async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> dict:
    """
    FastAPI dependency to extract and validate the current user from JWT.
    Used in protected routes via Depends().
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


async def get_current_user_id(
    payload: dict = Depends(get_current_user_payload),
) -> str:
    """Extract user ID from the token payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return user_id


def require_role(minimum_role: UserRole):
    """
    FastAPI dependency factory for role-based authorization.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])
        async def admin_endpoint(): ...
    """
    async def role_checker(
        payload: dict = Depends(get_current_user_payload),
    ) -> dict:
        user_role = payload.get("role", UserRole.VIEWER)
        if not has_minimum_role(user_role, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {minimum_role.value}",
            )
        return payload
    return role_checker


# ── Prompt Injection Protection ───────────────────────────────────────────────

# Patterns commonly used in prompt injection attacks
PROMPT_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all instructions",
    r"forget your instructions",
    r"you are now",
    r"act as if you are",
    r"system prompt",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"###\s*instruction",
    r"jailbreak",
    r"DAN mode",
    r"developer mode",
]

COMPILED_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS
]


def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.

    Args:
        text: Raw user input
        max_length: Maximum allowed input length

    Returns:
        Sanitized input string

    Raises:
        ValueError: If injection attempt is detected
    """
    if not text or not isinstance(text, str):
        return ""

    # Truncate to max length
    text = text[:max_length]

    # Check for injection patterns
    for pattern in COMPILED_INJECTION_PATTERNS:
        if pattern.search(text):
            raise ValueError(
                "Input contains potentially unsafe content. "
                "Please rephrase your question."
            )

    # Remove null bytes and control characters (except newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    return text.strip()


# ── PII Detection ─────────────────────────────────────────────────────────────

PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
}


def detect_pii(text: str) -> dict[str, list[str]]:
    """
    Detect PII in text content.

    Returns:
        Dict mapping PII type to list of found values (redacted)
    """
    found_pii: dict[str, list[str]] = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            found_pii[pii_type] = [f"[REDACTED_{pii_type.upper()}]" for _ in matches]
    return found_pii


def redact_pii(text: str) -> str:
    """Replace PII in text with redaction markers."""
    for pii_type, pattern in PII_PATTERNS.items():
        text = pattern.sub(f"[REDACTED_{pii_type.upper()}]", text)
    return text
