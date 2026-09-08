"""
Ocean Agentic AI — FastAPI application entrypoint.

Phase 1 scope only:
- App instance + config
- Basic logging
- GET /health
- Swagger (/docs) + ReDoc (/redoc)
- Global JSON error handling

Do not add DB, auth, external providers, or AI agents here yet —
those come in later phases per the project's phased build plan.
"""
from fastapi import FastAPI

from app.api.routes import health
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)

    app.include_router(health.router)

    @app.on_event("startup")
    async def on_startup() -> None:
        logger.info(
            "Starting %s v%s in '%s' mode",
            settings.APP_NAME,
            settings.APP_VERSION,
            settings.ENVIRONMENT,
        )

    return app


app = create_app()
