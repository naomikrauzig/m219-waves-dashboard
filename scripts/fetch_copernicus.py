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
SNAPSHOT_DIR = ROOT / "assets" / "snapshots"
DOWNLOAD_DIR = ROOT / "data" / "raw"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Snapshot date as YYYY-MM-DD, defaults to yesterday UTC.")
    parser.add_argument("--dry-run", action="store_true", help="Print requests without downloading.")
    parser.add_argument("--allow-partial", action="store_true", help="Continue if one product cannot be downloaded.")
    return parser.parse_args()


def target_day(value: str | None) -> date:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return (datetime.now(timezone.utc) - timedelta(days=1)).date()


def load_products() -> list[dict]:
    return json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))


def download_subset(product: dict, day: date, dry_run: bool) -> Path | None:
    start = f"{day.isoformat()}T00:00:00"
    end = f"{day.isoformat()}T23:59:59"
    min_lon, min_lat, max_lon, max_lat = product["bbox"]
    output_file = DOWNLOAD_DIR / f"{day.isoformat()}_{product['key']}.nc"

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
    for name in preferred:
        if name in dataset:
            return name
    data_vars = list(dataset.data_vars)
    if not data_vars:
        raise ValueError("No plottable variables found in downloaded dataset.")
    return data_vars[0]


def plot_snapshot(product: dict, nc_path: Path, day: date) -> None:
    import matplotlib.pyplot as plt
    import xarray as xr

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(nc_path)
    var_name = choose_variable(ds, product["variables"])
    da = ds[var_name]

    while da.ndim > 2:
        dim = da.dims[0]
        da = da.isel({dim: 0})

    lon_name = "longitude" if "longitude" in da.coords else "lon"
    lat_name = "latitude" if "latitude" in da.coords else "lat"

    fig, ax = plt.subplots(figsize=(14, 9), dpi=140)
    mesh = ax.pcolormesh(da[lon_name], da[lat_name], da, shading="auto", cmap="viridis")
    fig.colorbar(mesh, ax=ax, pad=0.012, label=f"{var_name}")
    ax.plot([-34.877, -23.0, -24.3, -24.9958, 7.207], [-8.0476, 0.0, 17.6, 16.886, 53.367], color="white", lw=3)
    ax.plot([-34.877, -23.0, -24.3, -24.9958, 7.207], [-8.0476, 0.0, 17.6, 16.886, 53.367], color="#d95f35", lw=1.4)
    ax.scatter([-34.877, -23.0, -24.3, -24.9958, 7.207], [-8.0476, 0.0, 17.6, 16.886, 53.367], s=26, color="white", edgecolor="#17212b", zorder=3)
    ax.set_title(f"M219 WAVES | {product['label']} | {day.isoformat()}", loc="left", weight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(color="white", alpha=0.28)
    fig.tight_layout()
    fig.savefig(SNAPSHOT_DIR / f"{day.isoformat()}_{product['key']}.png")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    day = target_day(args.date)
    made_snapshots = 0
    failures: list[str] = []

    for product in load_products():
        try:
            nc_path = download_subset(product, day, args.dry_run)
            if nc_path is not None:
                plot_snapshot(product, nc_path, day)
                made_snapshots += 1
        except Exception as exc:
            message = f"{product['key']}: {exc}"
            failures.append(message)
            print(f"ERROR {message}", file=sys.stderr)
            if not args.allow_partial:
                raise

    if failures:
        print("Completed with product failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

    if not args.dry_run and made_snapshots == 0:
        raise SystemExit("No snapshots were generated. Check credentials, dataset IDs, and requested date.")


if __name__ == "__main__":
    main()
