# Meteor M219 WAVES Near-Real-Time Marine Dashboard

This repository contains a dashboard for the planned R/V Meteor M219 WAVES GEOMAR Cruise.

The page works immediately with bundled sample maps. Once Copernicus Marine and CDS credentials are added to GitHub repository secrets, the scheduled workflow downloads a rolling forecast window from today through five days ahead, renders PNG snapshots into `assets/snapshots`, and writes availability metadata to `data/manifest.json`.

## Cruise Basis

- Campaign: `M219 (WAVES)`
- Platform: R/V Meteor
- Planned dates: `2026-05-30` Recife, Brazil to `2026-06-28` Emden, Germany
- Chief scientist: Peter Brandt
- Current route file: `data/route.geojson`
- Mooring markers: `data/moorings.geojson`

## Local Preview

Open `index.html` in a browser. The map tiles and Leaflet assets load from public CDNs, so an internet connection is useful for the full preview.

## Data Update Workflow

1. Create a Copernicus Marine account.
2. Create or enable a Copernicus Climate Data Store API key for ERA5 access.
3. Add these GitHub repository secrets:
   - `COPERNICUSMARINE_SERVICE_USERNAME`
   - `COPERNICUSMARINE_SERVICE_PASSWORD`
   - `CDSAPI_URL`
   - `CDSAPI_KEY`
4. Enable GitHub Pages for the repository.
5. Run the `Update Copernicus snapshots` workflow manually or wait for the daily schedule.

Dry-run the rolling forecast requests locally:

```powershell
python scripts/fetch_copernicus.py --dry-run --allow-partial
```

The products and bounding box are configured in `data/products.json`.

ERA5 winds are used for 10 m wind-vector maps plus derived wind stress and Ekman pumping maps. Wind stress uses the CDT `windstress` bulk formula with `rho_air = 1.225 kg m-3` and `Cd = 1.25e-3`; Ekman transport and pumping follow the CDT `ekman` formulation using `rho_water = 1025 kg m-3` and masking the near-equatorial band where the Coriolis term approaches zero.

## Data Layer Roadmap

The dashboard now separates layers into modeled forecasts, satellite-derived maps, freely available in-situ observations, and derived diagnostics. See `docs/data-layer-assessment.md` for implementation notes and limitations.
