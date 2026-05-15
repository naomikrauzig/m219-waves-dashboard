"""Download and plot Copernicus Marine quick-look subsets for M219 WAVES.

The script is designed for GitHub Actions. It uses repository secrets for
Copernicus Marine credentials and writes PNG snapshots consumed by index.html.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_FILE = ROOT / "data" / "products.json"
MANIFEST_FILE = ROOT / "data" / "manifest.json"
MOORINGS_FILE = ROOT / "data" / "moorings.geojson"
SNAPSHOT_DIR = ROOT / "assets" / "snapshots"
DOWNLOAD_DIR = ROOT / "data" / "raw"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Start date as YYYY-MM-DD, defaults to today UTC.")
    parser.add_argument("--days-ahead", type=int, default=5, help="Number of forecast days after the start date.")
    parser.add_argument("--dry-run", action="store_true", help="Print requests without downloading.")
    parser.add_argument("--allow-partial", action="store_true", help="Continue if one product cannot be downloaded.")
    return parser.parse_args()


def target_start_day(value: str | None) -> date:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.now(timezone.utc).date()


def target_days(value: str | None, days_ahead: int) -> list[date]:
    start = target_start_day(value)
    return [start + timedelta(days=offset) for offset in range(days_ahead + 1)]


def candidate_days(product: dict, target_day: date) -> list[date]:
    if product.get("date_strategy") != "latest_available":
        return [target_day]

    today = datetime.now(timezone.utc).date()
    start = min(target_day, today)
    max_backfill_days = int(product.get("max_backfill_days", 10))
    return [start - timedelta(days=offset) for offset in range(max_backfill_days + 1)]


def load_products() -> list[dict]:
    products = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    return [product for product in products if product.get("workflow_enabled", True)]


def load_moorings() -> list[dict]:
    if not MOORINGS_FILE.exists():
        return []
    geojson = json.loads(MOORINGS_FILE.read_text(encoding="utf-8"))
    return geojson.get("features", [])


def download_subset(product: dict, source_day: date, dry_run: bool) -> Path | None:
    start = f"{source_day.isoformat()}T00:00:00"
    end = f"{source_day.isoformat()}T23:59:59"
    min_lon, min_lat, max_lon, max_lat = product["bbox"]
    output_file = DOWNLOAD_DIR / f"{source_day.isoformat()}_{product['key']}.nc"

    request = {
        "dataset_id": product["dataset_id"],
        "variables": product["variables"],
        "minimum_longitude": min_lon,
        "maximum_longitude": max_lon,
        "minimum_latitude": min_lat,
        "maximum_latitude": max_lat,
        "start_datetime": start,
        "end_datetime": end,
        "output_directory": str(DOWNLOAD_DIR),
        "output_filename": output_file.name,
        "overwrite": True,
    }
    print(json.dumps({"product": product["key"], "request": request}, indent=2))
    if dry_run:
        return None

    import copernicusmarine

    username = os.environ.get("COPERNICUSMARINE_SERVICE_USERNAME")
    password = os.environ.get("COPERNICUSMARINE_SERVICE_PASSWORD")
    if not username or not password:
        raise RuntimeError(
            "Missing GitHub Actions secrets: COPERNICUSMARINE_SERVICE_USERNAME "
            "and COPERNICUSMARINE_SERVICE_PASSWORD must be set."
        )

    request["username"] = username
    request["password"] = password

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    copernicusmarine.subset(**request)
    return output_file


def choose_variable(dataset, preferred: list[str]) -> str:
    available = {name.lower(): name for name in dataset.data_vars}
    for name in preferred:
        if name in dataset.data_vars:
            return name
        if name.lower() in available:
            return available[name.lower()]
    data_vars = list(dataset.data_vars)
    if not data_vars:
        raise ValueError("No plottable variables found in downloaded dataset.")
    return data_vars[0]


def plot_snapshot(product: dict, nc_path: Path, target_day: date, source_day: date) -> None:
    import matplotlib.pyplot as plt
    import xarray as xr

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(nc_path)
    var_name = choose_variable(ds, product["variables"])
    da = ds[var_name]

    spatial_dims = {"latitude", "lat", "longitude", "lon"}
    while da.ndim > 2:
        dim = next((name for name in da.dims if name not in spatial_dims), da.dims[0])
        da = da.isel({dim: 0})

    lon_name = "longitude" if "longitude" in da.coords else "lon"
    lat_name = "latitude" if "latitude" in da.coords else "lat"

    fig, ax = plt.subplots(figsize=(14, 9), dpi=140)
    mesh = ax.pcolormesh(da[lon_name], da[lat_name], da, shading="auto", cmap="viridis")
    fig.colorbar(mesh, ax=ax, pad=0.012, label=f"{var_name}")
    ax.plot([-34.877, -23.0, -24.3, -24.9958, 7.207], [-8.0476, 0.0, 17.6, 16.886, 53.367], color="white", lw=3)
    ax.plot([-34.877, -23.0, -24.3, -24.9958, 7.207], [-8.0476, 0.0, 17.6, 16.886, 53.367], color="#d95f35", lw=1.4)
    ax.scatter([-34.877, -23.0, -24.3, -24.9958, 7.207], [-8.0476, 0.0, 17.6, 16.886, 53.367], s=26, color="white", edgecolor="#17212b", zorder=3)
    for mooring in load_moorings():
        lon, lat = mooring["geometry"]["coordinates"]
        label = mooring["properties"]["label"]
        ax.scatter(lon, lat, marker="*", s=150, color="#f2c14e", edgecolor="#17212b", linewidth=0.8, zorder=4)
        ax.text(lon + 0.18, lat + 0.18, label, fontsize=8, weight="bold", color="#17212b", zorder=5)
    title = f"M219 WAVES | {product['label']} | shown for {target_day.isoformat()}"
    if source_day != target_day:
        title = f"{title} using {source_day.isoformat()} data"
    ax.set_title(title, loc="left", weight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(color="white", alpha=0.28)
    fig.tight_layout()
    fig.savefig(SNAPSHOT_DIR / f"{target_day.isoformat()}_{product['key']}.png")
    plt.close(fig)


def write_manifest(days: list[date], products: list[dict], status: dict[str, dict[str, dict]]) -> None:
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "forecast_start": days[0].isoformat(),
        "forecast_end": days[-1].isoformat(),
        "dates": [day.isoformat() for day in days],
        "products": [
            {
                "key": product["key"],
                "label": product["label"],
                "category": product.get("category", "Modeled forecast"),
                "status": product.get("status", "automated"),
                "dataset_id": product["dataset_id"],
                "variables": product["variables"],
            }
            for product in products
        ],
        "status": status,
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    days = target_days(args.date, args.days_ahead)
    products = load_products()
    made_snapshots = 0
    failures: list[str] = []
    status: dict[str, dict[str, dict]] = {day.isoformat(): {} for day in days}

    for day in days:
        day_key = day.isoformat()
        for product in products:
            product_key = product["key"]
            product_errors: list[str] = []
            try:
                for source_day in candidate_days(product, day):
                    try:
                        nc_path = download_subset(product, source_day, args.dry_run)
                        if nc_path is not None:
                            plot_snapshot(product, nc_path, day, source_day)
                            made_snapshots += 1
                            status[day_key][product_key] = {
                                "available": True,
                                "path": f"assets/snapshots/{day_key}_{product_key}.png",
                                "source_date": source_day.isoformat(),
                            }
                            break
                        status[day_key][product_key] = {"available": False, "dry_run": True}
                        break
                    except Exception as exc:
                        product_errors.append(f"{source_day.isoformat()}: {exc}")
                else:
                    raise RuntimeError("; ".join(product_errors))
            except Exception as exc:
                message = f"{day_key} {product_key}: {exc}"
                status[day_key][product_key] = {"available": False, "error": str(exc)}
                failures.append(message)
                print(f"ERROR {message}", file=sys.stderr)
                if not args.allow_partial:
                    raise

    if not args.dry_run:
        write_manifest(days, products, status)

    if failures:
        print("Completed with product failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

    if not args.dry_run and made_snapshots == 0:
        raise SystemExit("No snapshots were generated. Check credentials, dataset IDs, and requested date.")


if __name__ == "__main__":
    main()
