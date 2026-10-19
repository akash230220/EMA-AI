# backend/app/main.py
"""
AI Email Operating System — FastAPI application entrypoint.

Responsibilities:
  - Create and configure the FastAPI app instance
  - Register middleware (CORS, rate limiting, error handling)
  - Wire up the v1 API router
  - Manage application lifespan (MongoDB connection on startup/shutdown,
    background scheduler for inbox sync + daily briefs)
  - Global exception handlers for consistent error response shapes

Run locally with:
    uvicorn app.main:app --reload --port 8000

Run in production (see Dockerfile) with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.mongo_client import connect_to_mongo, close_mongo_connection, ping_mongo
from app.db.indexes import ensure_indexes
from app.api.v1.router import api_router
from app.middlewares.rate_limiter import RateLimitMiddleware
from app.exceptions.custom_exceptions import AppException
from app.tasks.scheduler import start_scheduler, shutdown_scheduler

settings = get_settings()
configure_logging()
logger = logging.getLogger("ai_email_os")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages startup/shutdown lifecycle:
      - Startup: connect to MongoDB, ensure indexes exist, start the
        background scheduler (inbox sync polling, daily brief generation,
        automation rule evaluation cadence).
      - Shutdown: gracefully close the Mongo connection and stop the
        scheduler so no orphaned background tasks survive a redeploy.
    """
    logger.info("Starting AI Email OS backend (env=%s)", settings.ENVIRONMENT)

    await connect_to_mongo()
    await ensure_indexes()
    logger.info("MongoDB connected and indexes verified.")

    start_scheduler()
    logger.info("Background scheduler started.")

    yield

    logger.info("Shutting down AI Email OS backend...")
    shutdown_scheduler()
    await close_mongo_connection()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """
    Application factory. Kept separate from the module-level `app`
    instance so tests can construct isolated app instances if needed
    (e.g. with overridden settings/dependencies).
    """
    app = FastAPI(
        title="AI Email Operating System API",
        description=(
            "Production AI Email OS — Gmail sync, multi-agent AI processing "
            "(categorization, priority, sentiment, summarization, reply "
            "generation), meeting/task extraction, RAG-powered semantic "
            "search, and automation rules."
        ),
        version="1.0.0",
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # --------------------------------------------------------------------
    # Middleware (order matters — outermost registered last is applied
    # first to the request / last to the response)
    # --------------------------------------------------------------------

    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS + ["http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Content-Disposition"],  # needed for file export downloads
    )

    # --------------------------------------------------------------------
    # Routers
    # --------------------------------------------------------------------
    app.include_router(api_router, prefix="/api/v1")

    # --------------------------------------------------------------------
    # Exception handlers — ensure every error response, regardless of
    # source, has a consistent { "detail": ... } shape the frontend's
    # axiosClient.js response interceptor already expects.
    # --------------------------------------------------------------------

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning("AppException on %s %s: %s", request.method, request.url.path, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "errors": exc.errors},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Reshape Pydantic's default verbose error list into a flatter
        # field -> message map, matching what emailApi/taskApi/etc. on
        # the frontend expect in error.errors.
        field_errors = {}
        for err in exc.errors():
            field_path = ".".join(str(loc) for loc in err["loc"] if loc != "body")
            field_errors[field_path or "_"] = err["msg"]

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed.", "errors": field_errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred. Please try again.",
                "errors": None,
            },
        )

    # --------------------------------------------------------------------
    # Health check — used by Docker/Render/uptime monitors, and by the
    # frontend's IntegrationsPanel indirectly via /settings status checks
    # --------------------------------------------------------------------

    @app.get("/api/health", tags=["health"])
    async def health_check():
        mongo_ok = await ping_mongo()
        return {
            "status": "ok" if mongo_ok else "degraded",
            "environment": settings.ENVIRONMENT,
            "mongo_connected": mongo_ok,
        }

    @app.get("/", tags=["health"])
    async def root():
        return {"service": "AI Email OS API", "status": "running", "docs": "/api/docs"}

    return app


app = create_app()