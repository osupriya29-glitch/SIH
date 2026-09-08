"""
Centralized exception handlers so every error returned by the API follows
the same JSON shape:

{
    "error": {
        "code": "HTTP_404",
        "message": "..."
    }
}

This is Phase-1 scoped: generic HTTP + validation + unhandled-exception
handling only. Domain-specific errors (provider timeouts, auth failures,
etc.) will be added in later phases as those features are built.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


def _error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app instance."""

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
