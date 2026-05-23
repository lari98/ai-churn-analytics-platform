"""
FastAPI Application Entry Point
AI Customer Churn & Behavioral Analytics Platform
Production-ready with GDPR compliance, RBAC, and Azure integration.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from api.core.config import get_settings
from api.core.database import close_db, init_db
from api.middleware.audit_log import AuditLogMiddleware
from api.middleware.pii_masking import PIIMaskingMiddleware
from api.routers import anomaly, churn, gdpr, insights, retention, segmentation

logger = logging.getLogger(__name__)
settings = get_settings()


# ─── Application Lifecycle ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event handlers."""
    # Startup
    logger.info("Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    await init_db()
    logger.info("Database initialised")
    yield
    # Shutdown
    await close_db()
    logger.info("Application shutdown complete")


# ─── Application Factory ──────────────────────────────────────────────────────

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Enterprise AI Customer Churn & Behavioral Analytics Platform. "
            "GDPR/DSGVO compliant. DACH Telecom & Banking."
        ),
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
        contact={
            "name": "Platform Team",
            "email": "platform@churn-analytics.example.com",
        },
        license_info={"name": "Proprietary"},
    )

    # ─── Security Middleware ──────────────────────────────────────────────────
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.churn-analytics.azure.com", "localhost", "127.0.0.1"],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "X-API-Version"],
        expose_headers=["X-Correlation-ID", "X-Audit-Event-ID", "X-Request-ID"],
        max_age=600,
    )

    # ─── Custom Middleware (order matters: applied in reverse) ────────────────
    app.add_middleware(PIIMaskingMiddleware)   # Applied last (outermost)
    app.add_middleware(AuditLogMiddleware)     # Applied second

    # ─── Routers ─────────────────────────────────────────────────────────────
    api_prefix = settings.API_V1_PREFIX

    app.include_router(churn.router, prefix=f"{api_prefix}/churn", tags=["Churn Prediction"])
    app.include_router(segmentation.router, prefix=f"{api_prefix}/segmentation", tags=["Segmentation"])
    app.include_router(anomaly.router, prefix=f"{api_prefix}/anomaly", tags=["Anomaly Detection"])
    app.include_router(retention.router, prefix=f"{api_prefix}/retention", tags=["Retention"])
    app.include_router(insights.router, prefix=f"{api_prefix}/insights", tags=["GenAI Insights"])
    app.include_router(gdpr.router, prefix=f"{api_prefix}/gdpr", tags=["GDPR Compliance"])

    # ─── Prometheus Metrics ───────────────────────────────────────────────────
    Instrumentator(
        should_group_status_codes=True,
        should_respect_env_var=True,
        env_var_name="ENABLE_METRICS",
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # ─── Health & Readiness Endpoints ────────────────────────────────────────
    @app.get("/health", include_in_schema=False)
    async def health_check():
        """Liveness probe — returns 200 if app is running."""
        return {"status": "healthy", "version": settings.APP_VERSION}

    @app.get("/ready", include_in_schema=False)
    async def readiness_check():
        """Readiness probe — checks DB + dependencies."""
        from api.core.database import check_database_health
        db_status = await check_database_health()
        all_healthy = db_status["status"] == "healthy"
        return JSONResponse(
            status_code=200 if all_healthy else 503,
            content={
                "status": "ready" if all_healthy else "not_ready",
                "checks": {"database": db_status},
            },
        )

    # ─── Global Exception Handlers ────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
        logger.error(
            "Unhandled exception [%s] on %s %s: %s",
            correlation_id, request.method, request.url.path, exc,
            exc_info=True,
        )
        # Never expose internal error details in production
        detail = str(exc) if settings.ENVIRONMENT == "development" else "Internal server error"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": detail,
                "correlation_id": correlation_id,
            },
        )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Attach a request ID to every request."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(round((time.monotonic() - start) * 1000, 2))
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return app


# ─── App Instance ────────────────────────────────────────────────────────────

app = create_application()
