"""
NOAA/NDBC (National Data Buoy Center) provider.

Verified 2026-09-09 against:
  - https://www.ndbc.noaa.gov/faq/rt_data_access.shtml (access method)
  - https://www.ndbc.noaa.gov/faq/measdes.shtml (standard meteorological
    file header/units, "MM" for missing values)

Realtime data is served as plain whitespace-delimited text files at
https://www.ndbc.noaa.gov/data/realtime2/{station}.txt — no API key.
Standard meteorological ("stdmet") header, confirmed from NOAA's own FAQ:

    #YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE
    #yr  mo dy hr mn degT  m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC  nmi   hPa    ft

Missing values are reported as "MM" and are converted to None here —
never fabricated or interpolated.
"""
import datetime as dt

from app.core.config import get_settings
from app.providers.base_provider import BaseProvider

settings = get_settings()

# Units for each standard-meteorological ("stdmet"/.txt) column, per NDBC's
# measurement-descriptions page.
STDMET_UNITS = {
    "WDIR": "degT", "WSPD": "m/s", "GST": "m/s", "WVHT": "m", "DPD": "sec",
    "APD": "sec", "MWD": "degT", "PRES": "hPa", "ATMP": "degC", "WTMP": "degC",
    "DEWP": "degC", "VIS": "nmi", "PTDY": "hPa", "TIDE": "ft",
}


class NDBCParseError(ValueError):
    """Raised when a station's realtime2 file doesn't match the expected format."""


class NOAANDBCProvider(BaseProvider):
    provider_name = "NOAA/NDBC"

    def __init__(self, client):
        super().__init__(client)
        self._base_url = settings.NOAA_NDBC_BASE_URL

    async def get_standard_meteorological(self, station: str) -> dict:
        """
        Fetches and parses {station}.txt (last ~45 days of standard
        meteorological data). Returns {"station", "unit", "observations": [...]}
        with observations newest-first, matching the source file's order.
        "MM" (missing) values become None — never guessed.
        """
        url = f"{self._base_url}/{station.lower()}.txt"
        text = await self._get_text(url)
        return self._parse_stdmet(station, text)

    def _parse_stdmet(self, station: str, text: str) -> dict:
        lines = [line for line in text.strip().splitlines() if line.strip()]
        if len(lines) < 2:
            raise NDBCParseError(f"Unexpected empty/short response for station {station!r}")

        header = lines[0].lstrip("#").split()
        # lines[1] is the units row (e.g. "yr mo dy hr mn degT m/s ...") — the
        # units come from NDBC's documented table above, not parsed from
        # this row, since its tokens aren't machine-usable unit strings.
        data_lines = lines[2:]

        observations = []
        for line in data_lines:
            values = line.split()
            if len(values) != len(header):
                continue  # skip malformed rows rather than guess field alignment
            row = dict(zip(header, values))
            try:
                timestamp = dt.datetime(
                    int(row["YY"]), int(row["MM"]), int(row["DD"]),
                    int(row["hh"]), int(row.get("mm", 0)),
                    tzinfo=dt.timezone.utc,
                )
            except (KeyError, ValueError):
                timestamp = None

            observation = {"timestamp": timestamp.isoformat() if timestamp else None}
            for key, raw_value in row.items():
                if key in ("YY", "MM", "DD", "hh", "mm"):
                    continue
                observation[key] = None if raw_value == "MM" else _try_float(raw_value)
            observations.append(observation)

        return {
            "station": station,
            "units": STDMET_UNITS,
            "observations": observations,
        }


def _try_float(value: str):
    try:
        return float(value)
    except ValueError:
        return value  # e.g. MWD/PTDY sign-prefixed or non-numeric flag codes
