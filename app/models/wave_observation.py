"""Wave observation/forecast records (Open-Meteo, NOAA/NDBC, TidesAtlas)."""
import uuid

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID
from app.db.base_class import Base
from app.db.mixins import ObservationMixin


class WaveObservation(ObservationMixin, Base):
    __tablename__ = "wave_observations"
    __table_args__ = (
        Index("ix_wave_obs_location_time", "latitude", "longitude", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    height: Mapped[float | None] = mapped_column(nullable=True)
    height_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    direction: Mapped[float | None] = mapped_column(nullable=True)  # degrees
    period: Mapped[float | None] = mapped_column(nullable=True)  # seconds

    swell_height: Mapped[float | None] = mapped_column(nullable=True)
    swell_height_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WaveObservation id={self.id} source={self.source} at={self.observed_at}>"
