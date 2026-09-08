"""Pydantic schemas for the health check endpoint."""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str = Field(default="ok", description="Overall service status.")
    app_name: str = Field(description="Name of the application.")
    version: str = Field(description="Application version.")
    environment: str = Field(description="Current runtime environment.")
