"""FinPilot AI — API v1 module init"""
from app.api.v1.dashboard import (
    analytics_router as analytics,
    workflows_router as workflows,
    reports_router as reports,
    admin_router as admin,
    dashboard_router as dashboard,
)
from app.api.v1 import auth, chat, documents

__all__ = ["auth", "chat", "documents", "dashboard", "workflows", "reports", "analytics", "admin"]
