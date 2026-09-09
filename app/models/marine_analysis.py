"""Stored AI marine analysis results (risk, recommendations, etc.)."""
import datetime as dt
import enum
import uuid

from sqlalchemy import JSON, DateTime, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID
from app.db.base_class import Base
from app.db.mixins import TimestampMixin


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MarineAnalysis(TimestampMixin, Base):
    __tablename__ = "marine_analyses"
    __table_args__ = (
        Index("ix_marine_analysis_location_time", "latitude", "longitude", "analyzed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    analyzed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[RiskLevel | None] = mapped_column(
        Enum(RiskLevel, name="risk_level"), nullable=True
    )

    # Free-form structured lists — kept as JSON since their shape is agent-
    # defined (observations/risks/recommendations text produced per request).
    observations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    data_sources: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # AI/system confidence indicator only — NOT a scientific probability.
    confidence: Mapped[float | None] = mapped_column(nullable=True)

    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MarineAnalysis id={self.id} risk_level={self.risk_level} at={self.analyzed_at}>"
