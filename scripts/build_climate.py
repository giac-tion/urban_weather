#!/usr/bin/env python3
"""Build monthly 1991-2020 climate normals from NOAA NCEI station data."""

import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
CITIES_FILE = ROOT / "data" / "cities.json"
OUTPUT_FILE = ROOT / "data" / "climate.json"
ENDPOINT = "https://www.ncei.noaa.gov/access/services/data/v1"
DATA_TYPES = {
    "MLY-TMAX-NORMAL": "high",
    "MLY-TMIN-NORMAL": "low",
    "MLY-PRCP-NORMAL": "rain",
    "MLY-SNOW-NORMAL": "snow",
}


def load_cities():
    cities = json.loads(CITIES_FILE.read_text(encoding="utf-8"))
    if not isinstance(cities, list) or not cities:
        raise ValueError(f"{CITIES_FILE} must contain a non-empty JSON array")

    names = set()
    stations = set()
    for city in cities:
        if not all(key in city for key in ("name", "lat", "station")):
            raise ValueError(f"Each city needs name, lat, and station: {city}")
        if city["name"] in names or city["station"] in stations:
            raise ValueError(f"Duplicate city name or station: {city}")
        if not -90 <= float(city["lat"]) <= 90:
            raise ValueError(f"Invalid latitude for {city['name']}: {city['lat']}")
        names.add(city["name"])
        stations.add(city["station"])
    return cities


def fetch_station(station, zero_snow_fallback=False):
    params = urlencode({
        "dataset": "normals-monthly-1991-2020",
        "stations": station,
        "dataTypes": ",".join(DATA_TYPES),
        "format": "json",
        "units": "standard",
    })
    request = Request(
        f"{ENDPOINT}?{params}",
        headers={"User-Agent": "urban-weather-climate-builder/1.0"},
    )

    for attempt in range(3):
        try:
            with urlopen(request, timeout=45) as response:
                records = json.load(response)
            break
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"NCEI returned HTTP {error.code} for {station}") from error
            time.sleep(2 ** attempt)
        except (TimeoutError, URLError) as error:
            if attempt == 2:
                raise RuntimeError(f"Could not fetch normals for {station}: {error}") from error
            time.sleep(2 ** attempt)

    if not isinstance(records, list):
        raise ValueError(f"Unexpected NCEI response for {station}: expected a JSON array")

    monthly = {key: [None] * 12 for key in DATA_TYPES.values()}
    for record in records:
        month = int(record["DATE"])
        if not 1 <= month <= 12:
            raise ValueError(f"Unexpected month {record['DATE']} for {station}")
        for data_type, field in DATA_TYPES.items():
            value = record.get(data_type)
            if value in (None, "", "-9999", "-9999.0"):
                if field == "snow" and zero_snow_fallback:
                    continue
                raise ValueError(f"Missing {data_type} for {station}, month {month}")
            monthly[field][month - 1] = float(value)

    for field, values in monthly.items():
        if field == "snow" and zero_snow_fallback and all(value is None for value in values):
            monthly[field] = [0.0] * 12
            continue
        if any(value is None for value in values):
            raise ValueError(f"NCEI returned incomplete {field} normals for {station}")
    return monthly


def main():
    cities = load_cities()
    climate = []
    for index, city in enumerate(cities):
        print(f"Fetching {city['name']} ({city['station']}) [{index + 1}/{len(cities)}]")
        zero_snow_fallback = city.get("snowFallback") == "zero"
        normals = fetch_station(city["station"], zero_snow_fallback)
        climate.append({
            "name": city["name"],
            "lat": float(city["lat"]),
            "station": city["station"],
            "snowFallback": zero_snow_fallback,
            **normals,
        })
        if index + 1 < len(cities):
            time.sleep(0.2)

    payload = {
        "dataset": "normals-monthly-1991-2020",
        "source": "NOAA NCEI",
        "cities": climate,
    }
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(climate)} cities to {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()