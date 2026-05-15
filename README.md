# Meteor M219 WAVES Near-Real-Time Marine Dashboard

This repository contains a dashboard for the planned R/V Meteor M219 WAVES GEOMAR Cruise.

The page works immediately with generated placeholders. Once Copernicus Marine credentials are added to GitHub repository secrets, the scheduled workflow downloads a rolling forecast window from today through five days ahead, renders PNG snapshots into `assets/snapshots`, and writes availability metadata to `data/manifest.json`.

## Cruise Basis

- Campaign: `M219 (WAVES)`
- Platform: R/V Meteor
- Planned dates: `2026-05-30` Recife, Brazil to `2026-06-28` Emden, Germany
- Chief scientist: Peter Brandt
- Current route file: `data/route.geojson`
- Mooring markers: `data/moorings.geojson`

## Local Preview

Open `index.html` in a browser. The map tiles and Leaflet assets load from public CDNs, so an internet connection is useful for the full preview.

## Copernicus Marine Update Workflow

1. Create a Copernicus Marine account.
2. Add these GitHub repository secrets:
   - `COPERNICUSMARINE_SERVICE_USERNAME`
   - `COPERNICUSMARINE_SERVICE_PASSWORD`
3. Enable GitHub Pages for the repository.
4. Run the `Update Copernicus snapshots` workflow manually or wait for the daily schedule.

Dry-run the rolling forecast requests locally:

```powershell
python scripts/fetch_copernicus.py --dry-run --allow-partial
```

The products and bounding box are configured in `data/products.json`.

## Data Layer Roadmap

The dashboard now separates layers into modeled forecasts, satellite-derived maps, freely available in-situ observations, and derived diagnostics. See `docs/data-layer-assessment.md` for implementation notes and limitations.
