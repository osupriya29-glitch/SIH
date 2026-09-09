"""
NASA Ocean Color (OB.DAAC) provider.

IMPORTANT — this provider is only PARTIALLY implemented, on purpose:

1. `search_files()` is REAL and fully wired up. It wraps OB.DAAC's
   documented file_search API (HTTP POST, verified 2026-09-09 against
   https://oceandata.sci.gsfc.nasa.gov/file_search/file_search_help),
   which finds satellite data FILES matching a sensor/product/date range
   (e.g. "Aqua-MODIS L3 mapped chlorophyll for 2026-09-01"). No login is
   required for this search.

2. `get_point_value()` is NOT implemented. It raises
   OceanColorExtractionPending rather than returning fabricated data.
   Reason: file_search only returns FILE LISTINGS — actual chlorophyll-a /
   SST values at a specific lat/lon require downloading the matched
   NetCDF granule (which needs an Earthdata Login "appkey":
   https://oceandata.sci.gsfc.nasa.gov/appkey/) and reading the nearest
   pixel with a geospatial library (e.g. xarray/netCDF4/h5py — none of
   which are in this project's dependencies yet). That is a materially
   larger integration than the other Phase-4/5 providers, and per the
   project's rule on unverifiable/unbuilt integrations, this is marked
   pending rather than faked.

Do not add fabricated point-value logic here. When this is built for
real, it belongs in its own method backed by an actual file download +
netCDF read, gated on NASA_OCEAN_COLOR_APPKEY being configured.
"""
from app.core.config import get_settings
from app.providers.base_provider import BaseProvider

settings = get_settings()

# Sensor ID <-> name mapping, copied verbatim from OB.DAAC's file_search
# docs (subset most relevant to ocean/marine work; OB.DAAC's full list
# also includes many non-ocean-color sensors like PRISM, CALIOP, etc).
SENSOR_IDS = {
    0: "GLOBAL",
    6: "SeaWiFS",
    7: "Aqua-MODIS",
    8: "Terra-MODIS",
    9: "OCTS",
    11: "CZCS",
    14: "SNPP-VIIRS",
    19: "MERIS",
    21: "OCM2",
    25: "HICO",
    27: "GOCI",
    29: "S3A-OLCI",
    33: "NOAA20-VIIRS",
    36: "S3B-OLCI",
    41: "PACE-SPEXONE",
    42: "PACE-OCI",
    43: "NOAA21-VIIRS",
    48: "PACE-HARP2",
    58: "NOAA22-VIIRS",
}

# Data class / level tokens accepted by &dtype=
DATA_CLASSES = {"L0", "L1", "L2", "L3b", "L3m", "MET", "misc"}


class InvalidOceanColorQuery(ValueError):
    """Raised when a file_search call is missing required fields."""


class OceanColorExtractionPending(NotImplementedError):
    """
    Raised by get_point_value() — point-value extraction from NASA Ocean
    Color granules is not implemented yet (see module docstring).
    """

    def __init__(self):
        super().__init__(
            "Point-value extraction (e.g. chlorophyll-a at a coordinate) from NASA "
            "Ocean Color is not implemented. It requires downloading the matched "
            "NetCDF granule (Earthdata Login appkey) and reading the nearest pixel, "
            "which is not built yet. Use /files (search_files) to find candidate "
            "granules in the meantime."
        )


class NASAOceanColorProvider(BaseProvider):
    provider_name = "NASA Ocean Color"

    def __init__(self, client):
        super().__init__(client)
        self._search_url = settings.NASA_OCEAN_COLOR_FILE_SEARCH_URL

    async def search_files(
        self,
        sensor_id: int | None = None,
        sensor: str | None = None,
        dtype: str | None = None,
        dtid: int | None = None,
        sdate: str | None = None,
        edate: str | None = None,
        backdays: int | None = None,
        datetype: int | None = None,
        suite_id: str | None = None,
        prod_id: str | None = None,
        resolution_id: str | None = None,
        period: str | None = None,
        search: str | None = None,
        addurl: bool = True,
        results_as_file: bool = True,
        format: str = "json",
    ) -> dict | list | str:
        """
        POST /file_search — finds files matching the given criteria.
        Returns a file listing (JSON/text/HTML depending on `format`), NOT
        geophysical values. Raises InvalidOceanColorQuery if required
        fields per OB.DAAC's docs are missing.
        """
        if sensor_id is None and sensor is None:
            raise InvalidOceanColorQuery("One of sensor_id or sensor is required.")
        if dtype is not None and dtype not in DATA_CLASSES:
            raise InvalidOceanColorQuery(f"dtype must be one of {sorted(DATA_CLASSES)}, got {dtype!r}")
        has_date_range = sdate is not None and edate is not None
        if not has_date_range and backdays is None:
            raise InvalidOceanColorQuery(
                "Provide either (sdate and edate) or backdays to bound the search."
            )

        data: dict = {
            "results_as_file": "1" if results_as_file else "0",
            "addurl": "1" if addurl else "0",
            "format": format,
        }
        if sensor_id is not None:
            data["sensor_id"] = sensor_id
        if sensor is not None:
            data["sensor"] = sensor
        if dtype is not None:
            data["dtype"] = dtype
        if dtid is not None:
            data["dtid"] = dtid
        if sdate is not None:
            data["sdate"] = sdate
        if edate is not None:
            data["edate"] = edate
        if backdays is not None:
            data["backdays"] = backdays
        if datetype is not None:
            data["datetype"] = datetype
        if suite_id is not None:
            data["suite_id"] = suite_id
        if prod_id is not None:
            data["prod_id"] = prod_id
        if resolution_id is not None:
            data["resolution_id"] = resolution_id
        if period is not None:
            data["period"] = period
        if search is not None:
            data["search"] = search
        if settings.NASA_OCEAN_COLOR_APPKEY:
            data["appkey"] = settings.NASA_OCEAN_COLOR_APPKEY

        return await self._post_form(self._search_url, data=data)

    async def get_point_value(self, latitude: float, longitude: float, product: str, date: str):
        """Not implemented — see OceanColorExtractionPending."""
        raise OceanColorExtractionPending()
