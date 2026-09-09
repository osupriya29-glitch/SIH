"""Marine hazard alerts, typically produced by the Marine Risk Agent."""
import datetime as dt
import uuid

from sqlalchemy import Boolean, DateTime, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID
from app.db.base_class import Base
from app.db.mixins import TimestampMixin
from app.models.marine_analysis import RiskLevel


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alert_location_time", "latitude", "longitude", "issued_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    issued_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="alert_risk_level"), nullable=False
    )
    source: Mapped[str | None] = mapped_column(String(128), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    resolved_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    marine_analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Alert id={self.id} risk_level={self.risk_level} active={self.is_active}>"
