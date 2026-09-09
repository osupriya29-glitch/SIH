"""Ocean current observation/forecast records (NOAA CO-OPS, NDBC)."""
import uuid

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID
from app.db.base_class import Base
from app.db.mixins import ObservationMixin


class CurrentObservation(ObservationMixin, Base):
    __tablename__ = "current_observations"
    __table_args__ = (
        Index("ix_current_obs_location_time", "latitude", "longitude", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    speed: Mapped[float | None] = mapped_column(nullable=True)
    speed_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    direction: Mapped[float | None] = mapped_column(nullable=True)  # degrees

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CurrentObservation id={self.id} source={self.source} at={self.observed_at}>"
