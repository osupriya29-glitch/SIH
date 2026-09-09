"""
Import this module (not app.db.base_class directly) wherever all models need
to be registered on Base.metadata — primarily Alembic's env.py.

Every new model must be imported here or Alembic autogenerate will not see it.
"""
from app.db.base_class import Base  # noqa: F401

from app.models.user import User  # noqa: F401
from app.models.weather_observation import WeatherObservation  # noqa: F401
from app.models.ocean_observation import OceanObservation  # noqa: F401
from app.models.wave_observation import WaveObservation  # noqa: F401
from app.models.current_observation import CurrentObservation  # noqa: F401
from app.models.tide_observation import TideObservation  # noqa: F401
from app.models.marine_analysis import MarineAnalysis  # noqa: F401
from app.models.alert import Alert  # noqa: F401
