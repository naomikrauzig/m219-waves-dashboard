# Meteor M219 WAVES Near-Real-Time Marine Dashboard

This repository contains a GitHub Pages-ready static dashboard modeled after the MSM142 near-real-time satellite snapshot page, adapted for the planned RV Meteor M219 WAVES cruise corridor from Recife to the Equator, Cape Verde / Mindelo, and Emden.

The page works immediately with generated placeholders. Once Copernicus Marine credentials are added to GitHub repository secrets, the scheduled workflow can download subsets and render PNG snapshots into `assets/snapshots`.

## Cruise Basis

- Campaign: `M219 (WAVES)`
- Platform: RV Meteor
- Planned dates: `2026-05-30` Recife, Brazil to `2026-06-28` Emden, Germany
- Chief scientist listed by PANGAEA: Peter Brandt
- Current route file: `data/route.geojson`

## Local Preview

Open `index.html` in a browser. The map tiles and Leaflet assets load from public CDNs, so an internet connection is useful for the full preview.

## Copernicus Marine Update Workflow

1. Create a Copernicus Marine account.
2. Add these GitHub repository secrets:
   - `COPERNICUSMARINE_SERVICE_USERNAME`
   - `COPERNICUSMARINE_SERVICE_PASSWORD`
3. Enable GitHub Pages for the repository.
4. Run the `Update Copernicus snapshots` workflow manually or wait for the daily schedule.

Dry-run the requests locally:

```powershell
python scripts/fetch_copernicus.py --date 2026-05-30 --dry-run
```

The products and bounding box are configured in `data/products.json`.
