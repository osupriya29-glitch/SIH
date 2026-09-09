"""
NOAA CO-OPS (Center for Operational Oceanographic Products and Services)
Tides & Currents data provider.

Endpoint, parameters, and product/datum/interval rules verified against
the official docs on 2026-09-09:
https://api.tidesandcurrents.noaa.gov/api/prod/

Single GET endpoint (`datagetter`), no API key required.
"""
from app.core.config import get_settings
from app.providers.base_provider import BaseProvider

settings = get_settings()

# Product tokens accepted by &product= (per CO-OPS docs).
WATER_LEVEL_PRODUCTS = {
    "water_level",
    "hourly_height",
    "high_low",
    "daily_mean",
    "monthly_mean",
    "one_minute_water_level",
    "predictions",
    "ofs_water_level",
}
MET_PRODUCTS = {
    "air_temperature",
    "water_temperature",
    "wind",
    "air_pressure",
    "conductivity",
    "visibility",
    "humidity",
    "salinity",
}
CURRENTS_PRODUCTS = {"currents", "currents_predictions", "currents_header"}
OTHER_PRODUCTS = {"air_gap"}
ALL_PRODUCTS = WATER_LEVEL_PRODUCTS | MET_PRODUCTS | CURRENTS_PRODUCTS | OTHER_PRODUCTS

# Datum is mandatory for all water level products except air_gap (which
# uses a fixed bridge reference and takes no datum at all).
PRODUCTS_REQUIRING_DATUM = WATER_LEVEL_PRODUCTS - set()  # every water-level product needs it

VALID_DATUMS = {
    "CRD", "IGLD", "LWD", "MHHW", "MHW", "MTL", "MSL", "MLW", "MLLW", "NAVD", "STND",
}
VALID_UNITS = {"metric", "english"}
VALID_TIME_ZONES = {"gmt", "lst", "lst_ldt"}
VALID_FORMATS = {"xml", "json", "csv"}


class InvalidCoOpsQuery(ValueError):
    """Raised when a CO-OPS query is missing required fields per the docs."""


class NOAACoOpsProvider(BaseProvider):
    provider_name = "NOAA CO-OPS"

    def __init__(self, client):
        super().__init__(client)
        self._base_url = settings.NOAA_COOPS_BASE_URL

    async def get_data(
        self,
        station: str,
        product: str,
        begin_date: str | None = None,
        end_date: str | None = None,
        date: str | None = None,
        range: int | None = None,  # noqa: A002 - matches CO-OPS param name
        datum: str | None = None,
        units: str = "metric",
        time_zone: str = "gmt",
        interval: str | None = None,
        bin: int | None = None,  # noqa: A002 - matches CO-OPS param name
        vel_type: str | None = None,
        format: str = "json",  # noqa: A002 - matches CO-OPS param name
        application: str | None = None,
    ) -> dict | list | str:
        if product not in ALL_PRODUCTS:
            raise InvalidCoOpsQuery(f"Unknown product {product!r}. Valid: {sorted(ALL_PRODUCTS)}")
        if product in PRODUCTS_REQUIRING_DATUM and product != "air_gap" and not datum:
            raise InvalidCoOpsQuery(f"datum is required for product {product!r}")
        if datum is not None and datum not in VALID_DATUMS:
            raise InvalidCoOpsQuery(f"Invalid datum {datum!r}. Valid: {sorted(VALID_DATUMS)}")
        if units not in VALID_UNITS:
            raise InvalidCoOpsQuery(f"units must be one of {sorted(VALID_UNITS)}")
        if time_zone not in VALID_TIME_ZONES:
            raise InvalidCoOpsQuery(f"time_zone must be one of {sorted(VALID_TIME_ZONES)}")
        if format not in VALID_FORMATS:
            raise InvalidCoOpsQuery(f"format must be one of {sorted(VALID_FORMATS)}")

        has_range_pair = bool((begin_date and end_date) or (begin_date and range) or (end_date and range))
        if not has_range_pair and not date and range is None:
            raise InvalidCoOpsQuery(
                "Provide one of: (begin_date & end_date), (begin_date & range), "
                "(end_date & range), date, or range."
            )

        params: dict = {
            "station": station,
            "product": product,
            "units": units,
            "time_zone": time_zone,
            "format": format,
        }
        if begin_date is not None:
            params["begin_date"] = begin_date
        if end_date is not None:
            params["end_date"] = end_date
        if date is not None:
            params["date"] = date
        if range is not None:
            params["range"] = range
        if datum is not None:
            params["datum"] = datum
        if interval is not None:
            params["interval"] = interval
        if bin is not None:
            params["bin"] = bin
        if vel_type is not None:
            params["vel_type"] = vel_type
        if application is not None:
            params["application"] = application

        return await self._get(self._base_url, params=params)
