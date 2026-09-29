# SIH 2026 — Ocean / Marine Agentic AI Platform

Comprehensive backend for marine intelligence combining oceanographic, meteorological, buoy, tidal, and satellite observations into a unified data service with autonomous agent architecture readiness.

## Project Structure
```
FINAL SIH/
├── alembic/              # Database migration scripts (PostgreSQL/Supabase)
├── alembic.ini           # Alembic configuration
├── app/
│   ├── api/
│   │   ├── routes/       # API endpoints (marine, auth, imd, open-meteo, noaa, tidesatlas, nasa)
│   │   └── deps.py       # FastAPI dependencies (auth, providers, services)
│   ├── core/             # Configuration, error handlers, security, logging
│   ├── db/               # SQLAlchemy session, base models, mixins
│   ├── models/           # DB entities (Weather, Wave, Ocean, Tide, Current, Alert, Analysis, User)
│   ├── providers/        # External API providers (IMD, Open-Meteo, NOAA CO-OPS/NDBC/NWS, TidesAtlas, NASA)
│   ├── schemas/          # Pydantic v2 schemas (unified marine data, auth, health)
│   ├── services/         # Business logic (marine aggregation service, user service)
│   ├── tests/            # Automated test suite (53 tests passing across Phases 1-9)
│   └── main.py           # FastAPI entrypoint & router configuration
├── .env                  # Environment variables & provider API keys
├── .env.example          # Environment template
├── pytest.ini            # Pytest configuration
└── requirements.txt      # Python dependencies
```


### 3. Running Automated Tests
```powershell
.\.venv\Scripts\python.exe -m pytest
```
All 53 unit and integration tests will execute against SQLite in-memory with zero external network dependencies.
