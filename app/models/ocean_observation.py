"""Ocean/biology observation records (NASA Ocean Color, etc.)."""
import uuid

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID
from app.db.base_class import Base
from app.db.mixins import ObservationMixin


class OceanObservation(ObservationMixin, Base):
    __tablename__ = "ocean_observations"
    __table_args__ = (
        Index("ix_ocean_obs_location_time", "latitude", "longitude", "observed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )

    sea_surface_temperature: Mapped[float | None] = mapped_column(nullable=True)
    sst_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    chlorophyll_a: Mapped[float | None] = mapped_column(nullable=True)
    chlorophyll_a_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    salinity: Mapped[float | None] = mapped_column(nullable=True)
    salinity_unit: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # e.g. NASA product/dataset name, preserved for traceability.
    product: Mapped[str | None] = mapped_column(String(128), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OceanObservation id={self.id} source={self.source} at={self.observed_at}>"
