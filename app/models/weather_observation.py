"""Weather observation/forecast records (IMD, NOAA, etc.)."""
import uuid

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID
from app.db.base_class import Base
from app.db.mixins import ObservationMixin


class WeatherObservation(ObservationMixin, Base):
    __tablename__ = "weather_observations"
    __table_args__ = (
        Index("ix_weather_obs_location_time", "latitude", "longitude", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    temperature: Mapped[float | None] = mapped_column(nullable=True)
    temperature_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    wind_speed: Mapped[float | None] = mapped_column(nullable=True)
    wind_speed_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    wind_direction: Mapped[float | None] = mapped_column(nullable=True)  # degrees

    precipitation: Mapped[float | None] = mapped_column(nullable=True)
    precipitation_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    pressure: Mapped[float | None] = mapped_column(nullable=True)
    pressure_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WeatherObservation id={self.id} source={self.source} at={self.observed_at}>"
