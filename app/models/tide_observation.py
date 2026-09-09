"""Tide observation/prediction records (NOAA CO-OPS, TidesAtlas)."""
import uuid

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID
from app.db.base_class import Base
from app.db.mixins import ObservationMixin


class TideObservation(ObservationMixin, Base):
    __tablename__ = "tide_observations"
    __table_args__ = (
        Index("ix_tide_obs_location_time", "latitude", "longitude", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    water_level: Mapped[float | None] = mapped_column(nullable=True)
    water_level_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # e.g. "high" / "low" / a predicted level value — kept as free text since
    # NOAA CO-OPS and TidesAtlas may express predictions differently.
    prediction: Mapped[str | None] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TideObservation id={self.id} source={self.source} at={self.observed_at}>"
