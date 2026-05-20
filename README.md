# Meteor M219 WAVES Near-Real-Time Marine Dashboard

This repository contains a near-real-time marine dashboard for the planned R/V Meteor M219 WAVES GEOMAR cruise.

The dashboard combines Copernicus Marine, Copernicus Climate (ERA5), satellite-derived products, and derived diagnostics to provide environmental context along the planned cruise route between Recife (Brazil) and Emden (Germany).

The page works immediately with bundled sample maps. Once Copernicus Marine and CDS credentials are added to GitHub repository secrets, the scheduled workflow automatically downloads updated products, renders PNG snapshots into `assets/snapshots`, and writes availability metadata to `data/manifest.json`.

---

## Cruise Basis

- Campaign: `M219 (WAVES)`
- Platform: R/V Meteor
- Planned dates: `2026-05-30` Recife, Brazil → `2026-06-28` Emden, Germany
- Chief scientist: Peter Brandt
- Current route file: `data/route.geojson`
- Mooring markers: `data/moorings.geojson`

---

## Dashboard Content

The dashboard currently includes:

### Modeled Forecast Products
- Significant wave height
- Surface currents
- Surface Conservative Temperature (TEOS-10)
- Surface Absolute Salinity (TEOS-10)

### Satellite-Derived Products
- Sea level anomaly
- Satellite sea surface salinity
- Chlorophyll-a concentration

### Atmospheric and Derived Diagnostics
- ERA5 10 m wind fields
- Wind stress magnitude and vectors
- Ekman pumping diagnostics

### Regional Focus Panels
Additional zoomed panels are generated for:
- Planned transects
- K1–K4 stations
- 0N mooring
- CVOO mooring

---

## Local Preview

Open `index.html` in a browser.

Map tiles and Leaflet dependencies are loaded from public CDNs, so an internet connection is recommended for a complete preview.

---

## Automated Data Update Workflow

### Required Accounts

1. Create a Copernicus Marine account:
   https://marine.copernicus.eu/

2. Create or enable a Copernicus Climate Data Store API key:
   https://cds.climate.copernicus.eu/

---

### Required GitHub Repository Secrets

Add the following repository secrets:

- `COPERNICUSMARINE_SERVICE_USERNAME`
- `COPERNICUSMARINE_SERVICE_PASSWORD`
- `CDSAPI_URL`
- `CDSAPI_KEY`

---

### GitHub Pages

Enable GitHub Pages for the repository.

---

### Workflow Execution

The workflow `Update Copernicus snapshots` can be:
- executed manually from GitHub Actions,
- or triggered automatically by the scheduled workflow.

By default, the workflow generates:
- 1 day backward from the selected date,
- and 5 forecast days ahead.

---

## Manual Workflow Parameters

The workflow supports optional manual inputs:

| Parameter | Description |
|---|---|
| `date` | Central date (`YYYY-MM-DD`) |
| `days_back` | Number of days before the central date |
| `days_ahead` | Number of forecast days after the central date |

If no manual inputs are provided:
- the current UTC date is used,
- with `days_back = 1`,
- and `days_ahead = 5`.

---

## Local Testing

Dry-run the workflow locally:

```powershell
python scripts/fetch_copernicus.py --dry-run --allow-partial
