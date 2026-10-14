# City Climate and col Comparison

A static dashboard comparing 1991-2020 monthly climate normals for the cities in `data/cities.json`. The page loads `data/climate.json`; it does not make browser requests to NOAA or Open-Meteo. A second tab embeds SmartAsset's col calculator for manual city-pair comparisons; selected weather cities are listed there for reference.

## Update the climate data

Run the generator locally with Python 3 and an internet connection:

```sh
python scripts/build_climate.py
```

The GitHub Actions workflow can also be started from **Actions → Update climate normals → Run workflow**. It fetches the current NCEI normals and commits `data/climate.json` when the data changes. No API token or repository secret is required.

Monthly average relative humidity is calculated from Open-Meteo ERA5-Land daily mean humidity for 1991-2020. Temperature, rainfall, and snowfall continue to use NOAA NCEI station normals.

To add a city, add its display name, latitude, and NOAA station ID to `data/cities.json`, then run the generator. If the station has no published snowfall normals and the city should chart as zero snowfall, set `"snowFallback": "zero"`; the generated data and dashboard identify this fallback.

## Preview and publish

Serve the repository root locally so the browser can fetch the JSON file:

```sh
python -m http.server
```

Open `http://localhost:8000`. For GitHub Pages, select the `main` branch and root folder under **Settings → Pages**.

The col tab uses SmartAsset's embedded calculator, which requires manual entry of a current city, destination, household income, and household size. If embedding is unavailable, the tab links to the calculator directly.

Run this to start local host:
python -m http.server 8000