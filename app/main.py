"""
Ocean Agentic AI — FastAPI application entrypoint.

Implemented so far (Phases 1-7):
- App instance + config
- Basic logging
- GET /health
- Swagger (/docs) + ReDoc (/redoc)
- Global JSON error handling
- PostgreSQL + SQLAlchemy models (app/db, app/models)
- JWT auth: register / login / me (app/api/routes/auth.py)
- IMD provider + routes (app/providers/imd_provider.py, app/api/routes/imd.py)
- Open-Meteo Marine provider + routes (app/providers/open_meteo_provider.py, app/api/routes/open_meteo.py)
- NASA Ocean Color provider + routes — file search is real; point-value
  extraction is intentionally NOT implemented (returns 501, see
  app/providers/nasa_ocean_color_provider.py)
- NOAA CO-OPS, NOAA/NDBC, and NWS providers + routes (app/providers/noaa_*.py, app/api/routes/noaa.py)
- TidesAtlas provider + routes — additional tides/weather/waves source,
  requires TIDESATLAS_API_KEY (app/providers/tidesatlas_provider.py, app/api/routes/tidesatlas.py)

Do not add other external providers or AI agents here yet — those come in
later phases per the project's phased build plan.
"""
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.routes import (
    auth,
    health,
    imd,
    marine,
    nasa_ocean_color,
    noaa,
    open_meteo,
    tidesatlas,
)
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting %s v%s in '%s' mode",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    # Single shared client for all providers — reused across requests so
    # connections are pooled instead of reopened per call.
    app.state.http_client = httpx.AsyncClient(timeout=settings.IMD_REQUEST_TIMEOUT_SECONDS)
    try:
        yield
    finally:
        await app.state.http_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(imd.router)
    app.include_router(open_meteo.router)
    app.include_router(nasa_ocean_color.router)
    app.include_router(noaa.router)
    app.include_router(tidesatlas.router)
    app.include_router(marine.router)

    return app


app = create_app()
