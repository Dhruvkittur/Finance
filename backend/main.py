"""
FinPilot AI — FastAPI Application Entry Point
==============================================
Production-ready enterprise application with:
- Async FastAPI with lifespan context manager
- WebSocket support for real-time streaming
- JWT authentication middleware
- CORS configuration
- Rate limiting
- Request/response logging
- Health check endpoints
- OpenAPI documentation
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.dashboard import (
    dashboard_router,
    analytics_router,
    workflows_router,
    reports_router,
    admin_router,
)
from app.core.config import settings
from app.core.database import create_db_tables, engine
from app.core.redis_client import redis_client
from app.core.logging_config import configure_logging
# from app.services.vector_service import VectorService

# Configure structured logging
configure_logging()
logger = logging.getLogger(__name__)


# ─── Lifespan Context Manager ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    Runs startup logic before yielding and cleanup on shutdown.
    """
    logger.info("Starting FinPilot AI backend...")
    
    # Initialize Database
    logger.info("Initializing Database...")
    await create_db_tables()
    logger.info("Database tables initialized")

    # Connect to Redis
    # await redis_client.connect()
    logger.info("Redis bypassed for local dev")

    # Initialize ChromaDB collections
    # vector_service = VectorService()
    # await vector_service.initialize_collections()
    logger.info("ChromaDB bypassed for local dev")

    # Seed demo data if DEMO_MODE is enabled
    if settings.DEMO_MODE:
        from app.utils.demo_seeder import seed_demo_data
        await seed_demo_data()
        logger.info("Demo data seeded")

    logger.info(f"FinPilot AI v{settings.APP_VERSION} is ready!")

    yield  # Application runs here

    # Cleanup on shutdown
    logger.info("Shutting down FinPilot AI...")
    # await redis_client.disconnect()
    await engine.dispose()
    logger.info("Shutdown complete")


# ─── FastAPI App Factory ───────────────────────────────────────────────────────

def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="""
## FinPilot AI — Enterprise Multi-Agent Financial Intelligence Platform

**Autonomous AI Workforce for Modern Finance**

### Features
- 🤖 17 Autonomous AI Agents powered by LangGraph
- 📄 Intelligent Document Processing (PDF, DOCX, Excel, Images)
- 🔍 Semantic & Hybrid Search with ChromaDB
- 📊 Real-time Financial Analytics Dashboard
- 🔒 Enterprise Security (JWT, RBAC, Audit Logs)
- ⚡ Streaming Responses via WebSocket
- 🎯 Multi-model AI (Gemini 2.5 Flash, Groq, OpenRouter)

### Authentication
All endpoints (except `/health` and `/auth`) require a valid JWT Bearer token.
        """,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if settings.APP_DEBUG else None,
        redoc_url="/api/redoc" if settings.APP_DEBUG else None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
        },
    )

    # ── Middleware Stack ───────────────────────────────────────────────────────

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # Gzip compression for large responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── Request Logging & Tracing ──────────────────────────────────────────────

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """Log all incoming requests with timing and correlation ID."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()

        # Add request ID to logs
        logger.info(
            f"→ {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        response: Response = await call_next(request)

        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        logger.info(
            f"← {request.method} {request.url.path} {response.status_code} {process_time:.2f}ms",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": process_time,
            },
        )

        return response

    # ── Global Exception Handler ───────────────────────────────────────────────

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "request_id": getattr(request.state, "request_id", "unknown"),
                "message": str(exc) if settings.APP_DEBUG else "An unexpected error occurred",
            },
        )

    # ── API Routers ────────────────────────────────────────────────────────────

    api_prefix = "/api/v1"

    app.include_router(auth_router,       prefix=api_prefix, tags=["Authentication"])
    app.include_router(chat_router,       prefix=api_prefix, tags=["Chat & Agents"])
    app.include_router(documents_router,  prefix=api_prefix, tags=["Document Intelligence"])
    app.include_router(dashboard_router,  prefix=api_prefix, tags=["Dashboard"])
    app.include_router(workflows_router,  prefix=api_prefix, tags=["Workflow Builder"])
    app.include_router(reports_router,    prefix=api_prefix, tags=["Reports"])
    app.include_router(analytics_router,  prefix=api_prefix, tags=["Analytics"])
    app.include_router(admin_router,      prefix=api_prefix, tags=["Admin"])

    # ── Health Checks ──────────────────────────────────────────────────────────

    @app.get(
        "/health",
        tags=["Health"],
        summary="Application health check",
        response_description="Returns service health status",
    )
    async def health_check():
        """
        Lightweight health check for load balancer probes.
        Returns overall status and individual service statuses.
        """
        checks = {}

        # Redis health
        try:
            await redis_client.ping()
            checks["redis"] = "healthy"
        except Exception:
            checks["redis"] = "unhealthy"

        # Database health
        try:
            async with engine.begin() as conn:
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            checks["database"] = "healthy"
        except Exception:
            checks["database"] = "unhealthy"

        overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"

        return {
            "status": overall,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "services": checks,
        }

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Kubernetes readiness probe."""
        return {"status": "ok", "message": "FinPilot AI is running!"}

    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Kubernetes liveness probe."""
        return {"status": "alive"}

    # ── Static Files (uploaded documents served from backend) ─────────────────
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    return app


# ─── Application Instance ─────────────────────────────────────────────────────

app = create_application()


# ─── Development Server Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.APP_DEBUG else 4,
    )
