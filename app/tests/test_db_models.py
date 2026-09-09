"""
Model/schema tests using an in-memory SQLite DB, so these run without a
live Postgres instance. The portable GUID type (app/db/types.py) is what
makes this possible while Postgres is still used natively in real deployments.
"""
import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.alert import Alert
from app.models.current_observation import CurrentObservation
from app.models.marine_analysis import MarineAnalysis, RiskLevel
from app.models.ocean_observation import OceanObservation
from app.models.tide_observation import TideObservation
from app.models.user import User, UserRole
from app.models.wave_observation import WaveObservation
from app.models.weather_observation import WeatherObservation


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_all_tables_created(db_session):
    engine = db_session.get_bind()
    table_names = set(Base.metadata.tables.keys())
    assert table_names == {
        "users",
        "weather_observations",
        "ocean_observations",
        "wave_observations",
        "current_observations",
        "tide_observations",
        "marine_analyses",
        "alerts",
    }


def test_create_user(db_session):
    user = User(email="researcher@example.com", hashed_password="hashed", role=UserRole.RESEARCHER)
    db_session.add(user)
    db_session.commit()

    fetched = db_session.query(User).filter_by(email="researcher@example.com").one()
    assert fetched.role == UserRole.RESEARCHER
    assert fetched.is_active is True
    assert fetched.id is not None


def test_create_weather_observation_allows_null_values(db_session):
    obs = WeatherObservation(
        latitude=19.07,
        longitude=72.87,
        observed_at=dt.datetime.now(dt.timezone.utc),
        source="IMD",
        status="observation",
        temperature=None,  # missing data must be nullable, never fabricated
    )
    db_session.add(obs)
    db_session.commit()

    fetched = db_session.query(WeatherObservation).one()
    assert fetched.temperature is None
    assert fetched.source == "IMD"


def test_create_ocean_wave_current_tide_observations(db_session):
    now = dt.datetime.now(dt.timezone.utc)
    db_session.add_all(
        [
            OceanObservation(latitude=1, longitude=1, observed_at=now, source="NASA Ocean Color"),
            WaveObservation(latitude=1, longitude=1, observed_at=now, source="Open-Meteo"),
            CurrentObservation(latitude=1, longitude=1, observed_at=now, source="NOAA CO-OPS"),
            TideObservation(latitude=1, longitude=1, observed_at=now, source="NOAA CO-OPS"),
        ]
    )
    db_session.commit()

    assert db_session.query(OceanObservation).count() == 1
    assert db_session.query(WaveObservation).count() == 1
    assert db_session.query(CurrentObservation).count() == 1
    assert db_session.query(TideObservation).count() == 1


def test_create_marine_analysis_and_alert(db_session):
    now = dt.datetime.now(dt.timezone.utc)
    analysis = MarineAnalysis(
        latitude=19.07,
        longitude=72.87,
        analyzed_at=now,
        summary="Rough seas expected.",
        risk_level=RiskLevel.HIGH,
        observations=["wave height 3.2m"],
        risks=["high waves"],
        recommendations=["avoid small craft advisories"],
        data_sources=["Open-Meteo", "IMD"],
        confidence=0.8,
    )
    db_session.add(analysis)
    db_session.commit()

    alert = Alert(
        latitude=19.07,
        longitude=72.87,
        issued_at=now,
        title="High wave alert",
        risk_level=RiskLevel.HIGH,
        source="Marine Risk Agent",
        marine_analysis_id=analysis.id,
    )
    db_session.add(alert)
    db_session.commit()

    fetched_alert = db_session.query(Alert).one()
    assert fetched_alert.risk_level == RiskLevel.HIGH
    assert fetched_alert.is_active is True
    assert fetched_alert.marine_analysis_id == analysis.id
