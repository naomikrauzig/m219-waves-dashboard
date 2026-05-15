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
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_FILE = ROOT / "data" / "products.json"
MANIFEST_FILE = ROOT / "data" / "manifest.json"
MOORINGS_FILE = ROOT / "data" / "moorings.geojson"
SNAPSHOT_DIR = ROOT / "assets" / "snapshots"
DOWNLOAD_DIR = ROOT / "data" / "raw"
EARTH_RADIUS_M = 6_371_000.0
OMEGA = 7.2921159e-5
AIR_DENSITY = 1.225
DRAG_COEFFICIENT = 1.25e-3
SEAWATER_DENSITY = 1025.0


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

    default_backfill = 3 if product.get("key") == "SAT_SLA" else 5
    max_backfill_days = int(product.get("max_backfill_days", default_backfill))

    return [start - timedelta(days=offset) for offset in range(max_backfill_days + 1)]


def load_products() -> list[dict]:
    products = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
    return [product for product in products if product.get("workflow_enabled", True)]


def product_by_key(products: list[dict], key: str) -> dict:
    for product in products:
        if product["key"] == key:
            return product
    raise KeyError(f"Product {key!r} is not configured.")


def load_moorings() -> list[dict]:
    if not MOORINGS_FILE.exists():
        return []
    geojson = json.loads(MOORINGS_FILE.read_text(encoding="utf-8"))
    return geojson.get("features", [])


def download_era5_subset(product: dict, source_day: date, dry_run: bool) -> Path | None:
    min_lon, min_lat, max_lon, max_lat = product["bbox"]
    output_file = DOWNLOAD_DIR / f"{source_day.isoformat()}_{product['key']}.nc"
    request = {
        "product_type": ["reanalysis"],
        "variable": product.get("cds_variables", ["10m_u_component_of_wind", "10m_v_component_of_wind"]),
        "year": [f"{source_day.year:04d}"],
        "month": [f"{source_day.month:02d}"],
        "day": [f"{source_day.day:02d}"],
        "time": ["00:00", "06:00", "12:00", "18:00"],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": [max_lat, min_lon, min_lat, max_lon],
    }
    print(json.dumps({"product": product["key"], "source": "cds", "request": request}, indent=2))
    if dry_run:
        return None

    import cdsapi

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    url = os.environ.get("CDSAPI_URL")
    key = os.environ.get("CDSAPI_KEY")
    client_kwargs = {}
    if url and key:
        client_kwargs = {"url": url, "key": key}
    client = cdsapi.Client(**client_kwargs)
    client.retrieve(product["dataset_id"], request).download(str(output_file))
    return output_file


def download_copernicus_subset(product: dict, source_day: date, dry_run: bool) -> Path | None:
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


def download_subset(product: dict, source_day: date, dry_run: bool) -> Path | None:
    if product.get("source") == "cds_era5":
        return download_era5_subset(product, source_day, dry_run)
    return download_copernicus_subset(product, source_day, dry_run)


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


def coordinate_name(dataset: Any, candidates: tuple[str, ...]) -> str:
    for name in candidates:
        if name in dataset.coords:
            return name
        if name in dataset.dims:
            return name
    raise KeyError(f"None of these coordinates were found: {candidates}")


def as_2d(dataset: Any, var_name: str) -> Any:
    da = dataset[var_name]
    spatial_dims = {"latitude", "lat", "longitude", "lon"}
    while da.ndim > 2:
        dim = next((name for name in da.dims if name not in spatial_dims), da.dims[0])
        da = da.isel({dim: 0})
    return da


def wind_components(dataset: Any) -> tuple[Any, Any, str, str]:
    u_name = choose_variable(dataset, ["u10", "10u", "u_component_of_wind_10m"])
    v_name = choose_variable(dataset, ["v10", "10v", "v_component_of_wind_10m"])
    u10 = as_2d(dataset, u_name)
    v10 = as_2d(dataset, v_name)
    lon_name = coordinate_name(u10, ("longitude", "lon"))
    lat_name = coordinate_name(u10, ("latitude", "lat"))
    return u10, v10, lon_name, lat_name


def windstress_components(u10: Any, v10: Any) -> tuple[Any, Any, Any]:
    import numpy as np

    speed = np.hypot(u10, v10)
    tau = AIR_DENSITY * DRAG_COEFFICIENT * speed**2
    taux = np.where(speed > 0, tau * u10 / speed, 0.0)
    tauy = np.where(speed > 0, tau * v10 / speed, 0.0)
    return taux, tauy, tau


def lat_lon_grids(lon: Any, lat: Any) -> tuple[Any, Any]:
    import numpy as np

    lon_values = lon.values if hasattr(lon, "values") else lon
    lat_values = lat.values if hasattr(lat, "values") else lat
    if getattr(lon_values, "ndim", 1) == 1 and getattr(lat_values, "ndim", 1) == 1:
        return np.meshgrid(lon_values, lat_values)
    return lon_values, lat_values


def grid_spacing_m(lon2d: Any, lat2d: Any) -> tuple[Any, Any]:
    import numpy as np

    dx = EARTH_RADIUS_M * np.cos(np.deg2rad(lat2d)) * np.gradient(np.deg2rad(lon2d), axis=1)
    dy = EARTH_RADIUS_M * np.gradient(np.deg2rad(lat2d), axis=0)
    return dx, dy


def ekman_fields(lon: Any, lat: Any, u10: Any, v10: Any) -> tuple[Any, Any, Any, Any, Any]:
    import numpy as np

    lon2d, lat2d = lat_lon_grids(lon, lat)
    taux, tauy, tau = windstress_components(u10, v10)
    f = 2 * OMEGA * np.sin(np.deg2rad(lat2d))
    f = np.where(np.abs(lat2d) < 2.0, np.nan, f)
    ue = tauy / (SEAWATER_DENSITY * f)
    ve = -taux / (SEAWATER_DENSITY * f)
    dx, dy = grid_spacing_m(lon2d, lat2d)
    due_dx = np.gradient(ue, axis=1) / dx
    dve_dy = np.gradient(ve, axis=0) / dy
    w_e = due_dx + dve_dy
    return ue, ve, w_e, taux, tauy


def add_route_and_moorings(ax: Any) -> None:
    ax.plot(
        [-34.877, -23.0, -24.3, -24.9958, 7.207],
        [-8.0476, 0.0, 17.6, 16.886, 53.367],
        color="white",
        lw=3,
        linestyle="--",
        alpha=0.55,
    )
    ax.plot(
        [-34.877, -23.0, -24.3, -24.9958, 7.207],
        [-8.0476, 0.0, 17.6, 16.886, 53.367],
        color="#d95f35",
        lw=1.4,
        linestyle="--",
        alpha=0.58,
    )
    ax.scatter([-34.877, -23.0, -24.3, -24.9958, 7.207], [-8.0476, 0.0, 17.6, 16.886, 53.367], s=26, color="white", edgecolor="#17212b", zorder=3)
    for mooring in load_moorings():
        lon, lat = mooring["geometry"]["coordinates"]
        label = mooring["properties"]["label"]
        ax.scatter(lon, lat, marker="p", s=110, color="#c62828", edgecolor="white", linewidth=0.9, zorder=4)
        ax.text(lon + 0.18, lat + 0.18, label, fontsize=8, weight="bold", color="#17212b", zorder=5)


def snapshot_title(product: dict, target_day: date, source_day: date) -> str:
    title = f"M219 WAVES | {product['label']} | shown for {target_day.isoformat()}"
    if source_day != target_day:
        title = f"{title} using {source_day.isoformat()} data"
    return title


def plot_wind_snapshot(product: dict, dataset: Any, target_day: date, source_day: date) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    u10, v10, lon_name, lat_name = wind_components(dataset)
    speed = np.hypot(u10, v10)
    lon = u10[lon_name]
    lat = u10[lat_name]
    lon2d, lat2d = lat_lon_grids(lon, lat)
    step_y = max(1, speed.shape[0] // 22)
    step_x = max(1, speed.shape[1] // 28)

    fig, ax = plt.subplots(figsize=(14, 9), dpi=140)
    mesh = ax.pcolormesh(lon, lat, speed, shading="auto", cmap="viridis")
    fig.colorbar(mesh, ax=ax, pad=0.012, label="10 m wind speed (m/s)")
    ax.quiver(lon2d[::step_y, ::step_x], lat2d[::step_y, ::step_x], u10.values[::step_y, ::step_x], v10.values[::step_y, ::step_x], color="#17212b", alpha=0.7, scale=450)
    add_route_and_moorings(ax)
    ax.set_title(snapshot_title(product, target_day, source_day), loc="left", weight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(color="white", alpha=0.28)
    fig.tight_layout()
    fig.savefig(SNAPSHOT_DIR / f"{target_day.isoformat()}_{product['key']}.png")
    plt.close(fig)


def plot_derived_snapshot(product: dict, nc_path: Path, target_day: date, source_day: date) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    import xarray as xr

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(nc_path)
    u10, v10, lon_name, lat_name = wind_components(ds)
    lon = u10[lon_name]
    lat = u10[lat_name]
    lon2d, lat2d = lat_lon_grids(lon, lat)
    ue, ve, w_e, taux, tauy = ekman_fields(lon, lat, u10.values, v10.values)

    fig, ax = plt.subplots(figsize=(14, 9), dpi=140)
    if product["key"] == "WIND_STRESS":
        tau = np.hypot(taux, tauy)
        mesh = ax.pcolormesh(lon, lat, tau, shading="auto", cmap="magma")
        fig.colorbar(mesh, ax=ax, pad=0.012, label="Wind stress magnitude (N m-2)")
        step_y = max(1, tau.shape[0] // 22)
        step_x = max(1, tau.shape[1] // 28)
        ax.quiver(lon2d[::step_y, ::step_x], lat2d[::step_y, ::step_x], taux[::step_y, ::step_x], tauy[::step_y, ::step_x], color="#17212b", alpha=0.72, scale=8)
    else:
        plot_values = w_e * 1e7
        limit = np.nanpercentile(np.abs(plot_values), 97)
        if not np.isfinite(limit) or limit == 0:
            limit = 20
        mesh = ax.pcolormesh(lon, lat, plot_values, shading="auto", cmap="RdBu_r", vmin=-limit, vmax=limit)
        fig.colorbar(mesh, ax=ax, pad=0.012, label="Ekman pumping velocity (1e-7 m s-1)")
        ax.contour(lon, lat, plot_values, levels=[0], colors="#17212b", linewidths=0.8, alpha=0.55)
    add_route_and_moorings(ax)
    ax.set_title(snapshot_title(product, target_day, source_day), loc="left", weight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(color="white", alpha=0.28)
    fig.tight_layout()
    fig.savefig(SNAPSHOT_DIR / f"{target_day.isoformat()}_{product['key']}.png")
    plt.close(fig)


def plot_snapshot(product: dict, nc_path: Path, target_day: date, source_day: date) -> None:
    import matplotlib.pyplot as plt
    import xarray as xr

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ds = xr.open_dataset(nc_path)
    if product.get("source") == "cds_era5":
        plot_wind_snapshot(product, ds, target_day, source_day)
        return

    var_name = choose_variable(ds, product["variables"])
    da = as_2d(ds, var_name)

    lon_name = "longitude" if "longitude" in da.coords else "lon"
    lat_name = "latitude" if "latitude" in da.coords else "lat"

    fig, ax = plt.subplots(figsize=(14, 9), dpi=140)
    mesh = ax.pcolormesh(da[lon_name], da[lat_name], da, shading="auto", cmap="viridis")
    fig.colorbar(mesh, ax=ax, pad=0.012, label=f"{var_name}")
    add_route_and_moorings(ax)
    ax.set_title(snapshot_title(product, target_day, source_day), loc="left", weight="bold")
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


def process_product(
    product: dict,
    products: list[dict],
    target_day: date,
    source_day: date,
    dry_run: bool,
    raw_cache: dict[tuple[str, str], Path],
) -> Path | None:
    if product.get("source") == "derived":
        if dry_run:
            return None
        source_key = product["derives_from"]
        cache_key = (source_day.isoformat(), source_key)
        source_path = raw_cache.get(cache_key)
        if source_path is None:
            expected_path = DOWNLOAD_DIR / f"{source_day.isoformat()}_{source_key}.nc"
            source_path = expected_path if expected_path.exists() else None
        if source_path is None:
            source_product = product_by_key(products, source_key)
            source_path = download_subset(source_product, source_day, dry_run)
            if source_path is not None:
                raw_cache[cache_key] = source_path
        if source_path is None:
            return None
        plot_derived_snapshot(product, source_path, target_day, source_day)
        return source_path

    nc_path = download_subset(product, source_day, dry_run)
    if nc_path is not None:
        raw_cache[(source_day.isoformat(), product["key"])] = nc_path
        plot_snapshot(product, nc_path, target_day, source_day)
    return nc_path


def main() -> None:
    args = parse_args()
    days = target_days(args.date, args.days_ahead)
    products = load_products()
    made_snapshots = 0
    failures: list[str] = []
    status: dict[str, dict[str, dict]] = {day.isoformat(): {} for day in days}
    raw_cache: dict[tuple[str, str], Path] = {}

    for day in days:
        day_key = day.isoformat()
        for product in products:
            product_key = product["key"]
            product_errors: list[str] = []
            try:
                for source_day in candidate_days(product, day):
                    try:
                        nc_path = process_product(product, products, day, source_day, args.dry_run, raw_cache)
                        if nc_path is not None:
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
