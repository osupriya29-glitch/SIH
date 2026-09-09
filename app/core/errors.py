"""
Centralized exception handlers so every error returned by the API follows
the same JSON shape:

{
    "error": {
        "code": "HTTP_404",
        "message": "..."
    }
}

This includes a handler for ProviderError (external data-provider
failures, Phase 4+) in addition to generic HTTP/validation/unhandled
exceptions.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.providers.base_provider import ProviderError, ProviderNotConfigured
from app.providers.nasa_ocean_color_provider import (
    InvalidOceanColorQuery,
    OceanColorExtractionPending,
)
from app.providers.noaa_coops_provider import InvalidCoOpsQuery
from app.providers.noaa_ndbc_provider import NDBCParseError
from app.providers.open_meteo_provider import InvalidMarineVariable
from app.providers.tidesatlas_provider import InvalidTidesAtlasQuery

logger = get_logger(__name__)


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app instance."""

    @app.exception_handler(InvalidTidesAtlasQuery)
    async def invalid_tidesatlas_query_handler(request: Request, exc: InvalidTidesAtlasQuery):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(code="INVALID_TIDESATLAS_QUERY", message=str(exc)),
        )

    @app.exception_handler(ProviderNotConfigured)
    async def provider_not_configured_handler(request: Request, exc: ProviderNotConfigured):
        provider_token = exc.provider.upper().replace(" ", "_").replace("-", "_")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body(code=f"PROVIDER_NOT_CONFIGURED_{provider_token}", message=exc.detail),
        )

    @app.exception_handler(InvalidCoOpsQuery)
    async def invalid_coops_query_handler(request: Request, exc: InvalidCoOpsQuery):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(code="INVALID_COOPS_QUERY", message=str(exc)),
        )

    @app.exception_handler(NDBCParseError)
    async def ndbc_parse_error_handler(request: Request, exc: NDBCParseError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=_error_body(code="NDBC_PARSE_ERROR", message=str(exc)),
        )

    @app.exception_handler(InvalidOceanColorQuery)
    async def invalid_ocean_color_query_handler(request: Request, exc: InvalidOceanColorQuery):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(code="INVALID_OCEAN_COLOR_QUERY", message=str(exc)),
        )

    @app.exception_handler(OceanColorExtractionPending)
    async def ocean_color_extraction_pending_handler(request: Request, exc: OceanColorExtractionPending):
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content=_error_body(code="NOT_IMPLEMENTED_PENDING", message=str(exc)),
        )

    @app.exception_handler(InvalidMarineVariable)
    async def invalid_marine_variable_handler(request: Request, exc: InvalidMarineVariable):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(code="INVALID_MARINE_VARIABLE", message=str(exc)),
        )

    @app.exception_handler(ProviderError)
    async def provider_error_handler(request: Request, exc: ProviderError):
        status_code = status.HTTP_504_GATEWAY_TIMEOUT if exc.is_timeout else status.HTTP_502_BAD_GATEWAY
        logger.warning("Provider error from %s: %s", exc.provider, exc.detail)
        provider_token = exc.provider.upper().replace(" ", "_").replace("-", "_")
        return JSONResponse(
            status_code=status_code,
            content=_error_body(
                code=f"PROVIDER_ERROR_{provider_token}",
                message=f"{exc.provider} is currently unavailable: {exc.detail}",
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code=f"HTTP_{exc.status_code}", message=str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(code="VALIDATION_ERROR", message=str(exc.errors())),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Never leak stack traces / internals to the client.
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred."),
        )
