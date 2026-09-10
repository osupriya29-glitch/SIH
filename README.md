# SIH
I’ll trace the current database models and the API code that reads or writes them, then map the linked tables and attributes into a clear schema. I’ll start with the two database implementations and the main backend entrypoints.

Read 

Read 

Read 

Read 

The active backend currently persists only marine forecasts: `main.py` inserts into a single `marine_data` table, while weather data is returned but not stored. I’m checking the remaining project files for any existing schema or chatbot entities so the table list reflects the whole system rather than just one endpoint.

Searched for files matching `**/*.py`, 9 matches

Searched for regex `CREATE TABLE|INSERT INTO|SELECT |FROM |models|database|marine_data|weather` (`**/*.py`), 32 results

Read 

Read 

Read 

Based on the current backend, the database should contain these linked tables:

### 1. `locations`

| Attribute | Type | Key |
|---|---|---|
| `location_id` | `SERIAL` | Primary key |
| `location_name` | `VARCHAR(150)` | |
| `latitude` | `DECIMAL(9,6)` | |
| `longitude` | `DECIMAL(9,6)` | |
| `created_at` | `TIMESTAMPTZ` | |

### 2. `marine_data`

This is the table currently used by `/marine/save`.

| Attribute | Type | Key |
|---|---|---|
| `marine_data_id` | `SERIAL` | Primary key |
| `location_id` | `INTEGER` | Foreign key → `locations.location_id` |
| `timestamp` | `TIMESTAMPTZ` | |
| `wave_height` | `DECIMAL(6,2)` | |
| `wave_direction` | `DECIMAL(6,2)` | |
| `wave_period` | `DECIMAL(6,2)` | |
| `wind_wave_height` | `DECIMAL(6,2)` | |
| `created_at` | `TIMESTAMPTZ` | |

Relationship:

```text
locations 1 ───────────< marine_data
```

The existing code currently inserts `location`, `latitude`, and `longitude` directly into `marine_data`. With normalization, those should come from the `locations` table through `location_id`.

### 3. `weather_data`

The `/weather` endpoint currently retrieves weather data but does not save it.

| Attribute | Type | Key |
|---|---|---|
| `weather_data_id` | `SERIAL` | Primary key |
| `location_id` | `INTEGER` | Foreign key → `locations.location_id` |
| `timestamp` | `TIMESTAMPTZ` | |
| `temperature_2m` | `DECIMAL(6,2)` | |
| `wind_speed_10m` | `DECIMAL(6,2)` | |
| `wind_direction_10m` | `DECIMAL(6,2)` | |
| `precipitation` | `DECIMAL(6,2)` | |
| `created_at` | `TIMESTAMPTZ` | |

Relationship:

```text
locations 1 ───────────< weather_data
```

### Overall structure

```text
locations
   ├── marine_data
   └── weather_data
```

The minimum table required by the current code is `marine_data`. For a cleaner database design, use `locations`, `marine_data`, and `weather_data`.
