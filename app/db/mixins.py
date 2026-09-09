"""Reusable SQLAlchemy mixins shared across models."""
import datetime as dt

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """created_at / updated_at columns, managed by the database."""

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ObservationMixin(TimestampMixin):
    """
    Common fields shared by every marine/weather/ocean/wave/current/tide
    observation table, mirroring the normalized data model's requirement to
    always preserve source, timestamp, parameter, unit and location.
    """

    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    observed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(nullable=False, index=True)
    # "observation" (measured) vs "forecast" (predicted) — set explicitly by
    # the provider layer, never guessed.
    status: Mapped[str] = mapped_column(nullable=False, default="observation")
