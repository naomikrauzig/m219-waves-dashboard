"""Download and plot Copernicus Marine quick-look subsets for M219 WAVES."""

from __future__ import annotations

import argparse
import json
import os
import sys
import cartopy.crs as ccrs
import cartopy.feature as cfeature
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
SEAWATER_DENSITY = 1025.0

SURFACE_ONLY_PRODUCTS = {"MODEL_CURRENT", "MODEL_TEMP", "MODEL_SAL"}

REGIONAL_PRODUCTS = {
    "WAVES",
    "MODEL_CURRENT",
    "MODEL_TEMP",
    "MODEL_SAL",
    "SAT_SLA",
    "SAT_SSS",
    "SAT_CHL",
    "ERA5_WIND",
    "WIND_STRESS",
    "EKMAN_PUMPING",
}

REGIONAL_EXTENT = {
    "xlim": (-45, -15),
    "ylim": (-25, 25),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    parser.add_argument("--days-ahead", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--force-plots", action="store_true")
    return parser.parse_args()


def target_start_day(value: str | None) -> date:
    if value:
        return datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.now(timezone.utc).date()


def target_days(value: str | None, days_ahead: int) -> list[date]:
    center_day = target_start_day(value)

    return [
        center_day + timedelta(days=offset)
        for offset in range(-5, days_ahead + 1)
    ]


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
        "variable": product.get(
            "cds_variables",
            ["10m_u_component_of_wind", "10m_v_component_of_wind"],
        ),
        "year": [f"{source_day.year:04d}"],
        "month": [f"{source_day.month:02d}"],
        "day": [f"{source_day.day:02d}"],
        "time": ["00:00", "06:00", "12:00", "18:00"],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": [max_lat, min_lon, min_lat, max_lon],
    }

    print(
        json.dumps(
            {
                "product": product["key"],
                "source": "cds",
                "request": request,
            },
            indent=2,
        ),
        flush=True,
    )

    if dry_run:
        return None

    import cdsapi

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    url = os.environ.get("CDSAPI_URL")
    key = os.environ.get("CDSAPI_KEY")
    client_kwargs = {"url": url, "key": key} if url and key else {}

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

    if product["key"] in SURFACE_ONLY_PRODUCTS:
        request["minimum_depth"] = 0
        request["maximum_depth"] = 2

    print(
        json.dumps(
            {
                "product": product["key"],
                "request": request,
            },
            indent=2,
        ),
        flush=True,
    )

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
    output_file = DOWNLOAD_DIR / f"{source_day.isoformat()}_{product['key']}.nc"

    if output_file.exists() and output_file.stat().st_size > 0:
        print(f"Using cached raw file: {output_file}", flush=True)
        return output_file

    if product.get("source") == "cds_era5":
        return download_era5_subset(product, source_day, dry_run)

    return download_copernicus_subset(product, source_day, dry_run)


def choose_variable(dataset: Any, preferred: list[str]) -> str:
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


def robust_limits(values: Any, lower: float = 2, upper: float = 98) -> tuple[float, float]:
    import numpy as np

    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]

    if arr.size == 0:
        return 0.0, 1.0

    vmin, vmax = np.nanpercentile(arr, [lower, upper])

    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
        vmin, vmax = float(np.nanmin(arr)), float(np.nanmax(arr))

    if vmin == vmax:
        vmax = vmin + 1.0

    return float(vmin), float(vmax)


def symmetric_limits(values: Any, percentile: float = 98) -> tuple[float, float]:
    import numpy as np

    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]

    if arr.size == 0:
        return -1.0, 1.0

    limit = np.nanpercentile(np.abs(arr), percentile)

    if not np.isfinite(limit) or limit == 0:
        limit = max(abs(float(np.nanmin(arr))), abs(float(np.nanmax(arr))), 1.0)

    return -float(limit), float(limit)


def contour_levels(values: Any, n: int = 8, symmetric: bool = False) -> list[float]:
    import numpy as np

    if symmetric:
        vmin, vmax = symmetric_limits(values, 98)
    else:
        vmin, vmax = robust_limits(values, 5, 95)

    levels = np.linspace(vmin, vmax, n)
    return [float(v) for v in levels if np.isfinite(v)]


def get_cmocean_cmap(name: str):
    import cmocean

    return getattr(cmocean.cm, name)


def lon_lat_from_da(da: Any) -> tuple[Any, Any, str, str]:
    lon_name = coordinate_name(da, ("longitude", "lon"))
    lat_name = coordinate_name(da, ("latitude", "lat"))

    return da[lon_name], da[lat_name], lon_name, lat_name


def lat_lon_grids(lon: Any, lat: Any) -> tuple[Any, Any]:
    import numpy as np

    lon_values = lon.values if hasattr(lon, "values") else lon
    lat_values = lat.values if hasattr(lat, "values") else lat

    if getattr(lon_values, "ndim", 1) == 1 and getattr(lat_values, "ndim", 1) == 1:
        return np.meshgrid(lon_values, lat_values)

    return lon_values, lat_values


def teos10_absolute_salinity(sp_da: Any) -> Any:
    import gsw
    import xarray as xr

    lon, lat, _, _ = lon_lat_from_da(sp_da)
    lon2d, lat2d = lat_lon_grids(lon, lat)

    p = 0.0
    sa = gsw.SA_from_SP(sp_da.values, p, lon2d, lat2d)

    return xr.DataArray(
        sa,
        coords=sp_da.coords,
        dims=sp_da.dims,
        attrs={
            "long_name": "Absolute Salinity",
            "units": "g kg-1",
            "standard_name": "sea_water_absolute_salinity",
        },
    )


def teos10_conservative_temperature(thetao_da: Any, sp_da: Any) -> Any:
    import gsw
    import xarray as xr

    lon, lat, _, _ = lon_lat_from_da(thetao_da)
    lon2d, lat2d = lat_lon_grids(lon, lat)

    p = 0.0
    sa = gsw.SA_from_SP(sp_da.values, p, lon2d, lat2d)

    standard_name = str(thetao_da.attrs.get("standard_name", "")).lower()
    long_name = str(thetao_da.attrs.get("long_name", "")).lower()

    if "conservative" in standard_name or "conservative" in long_name:
        ct = thetao_da.values
    else:
        ct = gsw.CT_from_pt(sa, thetao_da.values)

    return xr.DataArray(
        ct,
        coords=thetao_da.coords,
        dims=thetao_da.dims,
        attrs={
            "long_name": "Conservative Temperature",
            "units": "degree_C",
            "standard_name": "sea_water_conservative_temperature",
        },
    )


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

    cd = (0.75 + 0.067 * speed) * 1e-3
    cd = np.clip(cd, 0.8e-3, 2.5e-3)

    tau = AIR_DENSITY * cd * speed**2

    taux = np.where(speed > 0, tau * u10 / speed, 0.0)
    tauy = np.where(speed > 0, tau * v10 / speed, 0.0)

    return taux, tauy, tau


def grid_spacing_m(lon2d: Any, lat2d: Any) -> tuple[Any, Any]:
    import numpy as np

    dx = EARTH_RADIUS_M * np.cos(np.deg2rad(lat2d)) * np.gradient(np.deg2rad(lon2d), axis=1)
    dy = EARTH_RADIUS_M * np.gradient(np.deg2rad(lat2d), axis=0)

    return dx, dy


def ekman_fields(lon: Any, lat: Any, u10: Any, v10: Any) -> tuple[Any, Any, Any, Any, Any]:
    import numpy as np

    lon2d, lat2d = lat_lon_grids(lon, lat)
    taux, tauy, _tau = windstress_components(u10, v10)

    f = 2 * OMEGA * np.sin(np.deg2rad(lat2d))
    f = np.where(np.abs(lat2d) < 2.0, np.nan, f)

    ue = tauy / (SEAWATER_DENSITY * f)
    ve = -taux / (SEAWATER_DENSITY * f)

    dx, dy = grid_spacing_m(lon2d, lat2d)
    due_dx = np.gradient(ue, axis=1) / dx
    dve_dy = np.gradient(ve, axis=0) / dy

    w_e = -(due_dx + dve_dy)

    return ue, ve, w_e, taux, tauy


def rolling_mean_2d(values: Any, size: int = 3) -> Any:
    import numpy as np
    from scipy.ndimage import uniform_filter

    arr = np.asarray(values, dtype=float)
    finite = np.isfinite(arr)

    filled = np.where(finite, arr, 0.0)
    weights = uniform_filter(finite.astype(float), size=size, mode="nearest")
    smoothed = uniform_filter(filled, size=size, mode="nearest")

    with np.errstate(invalid="ignore", divide="ignore"):
        result = smoothed / weights

    result[weights == 0] = np.nan

    return result


def add_route_and_moorings(ax: Any, extent: dict | None = None) -> None:
    xlim = extent["xlim"] if extent else None
    ylim = extent["ylim"] if extent else None

    def inside(lon: float, lat: float) -> bool:
        if xlim is None or ylim is None:
            return True
        return xlim[0] <= lon <= xlim[1] and ylim[0] <= lat <= ylim[1]

    ports = [
        (-34.877, -8.0476, "Recife"),
        (-24.9958, 16.886, "Mindelo"),
        (7.207, 53.367, "Emden"),
    ]

    for lon, lat, label in ports:
        if not inside(lon, lat):
            continue

        ax.scatter(
            lon,
            lat,
            s=80,
            marker="o",
            color="white",
            edgecolor="#17212b",
            linewidth=1.4,
            zorder=8,
            transform=ccrs.PlateCarree(),
        )

        ax.text(
            lon + 0.35,
            lat + 0.35,
            label,
            fontsize=10,
            fontweight="bold",
            color="#17212b",
            zorder=9,
            transform=ccrs.PlateCarree(),
            bbox=dict(
                facecolor="white",
                edgecolor="none",
                alpha=0.82,
                boxstyle="round,pad=0.22",
            ),
        )

    planned_points = [
        (-33.8, -9.8, "K1"),
        (-33.2, -9.6, "K2"),
        (-32.6, -9.4, "K3"),
        (-32.0, -9.2, "K4"),
        (-23.1650166667, -0.05705, "0N"),
        (-24.3309166667, 17.5412833333, "CVOO"),
    ]

    for lon, lat, label in planned_points:
        if not inside(lon, lat):
            continue

        ax.scatter(
            lon,
            lat,
            marker="p",
            s=220,
            color="#b30000",
            edgecolor="white",
            linewidth=2.0,
            zorder=10,
            transform=ccrs.PlateCarree(),
        )

        ax.text(
            lon + 0.35,
            lat + 0.35,
            label,
            fontsize=11,
            fontweight="bold",
            color="#111827",
            zorder=11,
            transform=ccrs.PlateCarree(),
            bbox=dict(
                facecolor="white",
                edgecolor="none",
                alpha=0.88,
                boxstyle="round,pad=0.24",
            ),
        )


def add_metadata(ax: Any, product: dict, source_day: date) -> None:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    dataset_id = product.get("dataset_id", "derived")

    ax.text(
        0.995,
        0.01,
        f"{dataset_id}\nSource: {source_day.isoformat()} | Generated: {generated}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        color="#17212b",
        bbox=dict(
            facecolor="white",
            alpha=0.65,
            edgecolor="none",
            boxstyle="round,pad=0.25",
        ),
        zorder=20,
    )


def snapshot_title(product: dict, target_day: date, source_day: date) -> str:
    title = f"{product['label']} | {target_day.isoformat()}"

    if source_day != target_day:
        title = f"{title} (source {source_day.isoformat()})"

    return title

    if product["key"] == "EKMAN_PUMPING":
        title = (
            f"M219 WAVES | Ekman pumping from ERA5 winds "
            f"(3×3 spatial rolling mean; past data only) | "
            f"shown for {target_day.isoformat()}"
        )

        if source_day != target_day:
            title = f"{title} using {source_day.isoformat()} data"

        return title

    title = f"M219 WAVES | {product['label']} | shown for {target_day.isoformat()}"

    if source_day != target_day:
        title = f"{title} using {source_day.isoformat()} data"

    return title


def save_figure(fig: Any, target_day: date, product: dict, suffix: str = "") -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    output = SNAPSHOT_DIR / f"{target_day.isoformat()}_{product['key']}{suffix}.png"

    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight", dpi=120)

    print(f"Saved snapshot: {output}", flush=True)


def plot_scalar_map(
    ax: Any,
    fig: Any,
    lon: Any,
    lat: Any,
    values: Any,
    cmap: Any,
    label: str,
    signed: bool = False,
    contours: bool = True,
    log_norm: bool = False,
    physical_levels: list[float] | None = None,
) -> None:
    import numpy as np
    from matplotlib.colors import LogNorm, TwoSlopeNorm

    if log_norm:
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr) & (arr > 0)]

        vmin = max(float(np.nanpercentile(arr, 2)), 0.01) if arr.size else 0.01
        vmax = float(np.nanpercentile(arr, 98)) if arr.size else 5.0
        vmax = max(vmax, vmin * 1.5)

        mesh = ax.pcolormesh(
            lon,
            lat,
            values,
            shading="auto",
            cmap=cmap,
            norm=LogNorm(vmin=vmin, vmax=vmax),
            transform=ccrs.PlateCarree(),
        )

        levels = np.geomspace(vmin, vmax, 7)

    elif signed:
        vmin, vmax = symmetric_limits(values, 98)
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0.0, vmax=vmax)

        mesh = ax.pcolormesh(
            lon,
            lat,
            values,
            shading="auto",
            cmap=cmap,
            norm=norm,
            transform=ccrs.PlateCarree(),
        )

        levels = physical_levels if physical_levels is not None else contour_levels(
            values,
            n=9,
            symmetric=True,
        )

    else:
        vmin, vmax = robust_limits(values, 2, 98)

        mesh = ax.pcolormesh(
            lon,
            lat,
            values,
            shading="auto",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            transform=ccrs.PlateCarree(),
        )

        levels = physical_levels if physical_levels is not None else contour_levels(
            values,
            n=8,
            symmetric=False,
        )

    fig.colorbar(mesh, ax=ax, pad=0.012, shrink=0.86, label=label)

    if contours and len(levels) >= 3:
        try:
            ax.contour(
                lon,
                lat,
                values,
                levels=levels,
                colors="#17212b",
                linewidths=0.45,
                alpha=0.45,
                transform=ccrs.PlateCarree(),
            )
        except Exception:
            pass


def format_axes(
    ax: Any,
    product: dict,
    target_day: date,
    source_day: date,
    extent: dict | None = None,
) -> None:
    if extent is not None:
        ax.set_xlim(*extent["xlim"])
        ax.set_ylim(*extent["ylim"])

    ax.set_title(
        snapshot_title(product, target_day, source_day),
        loc="left",
        weight="bold",
        fontsize=12,
        pad=6,
    )

    gridlines = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=0.55,
        color="white",
        alpha=0.55,
        linestyle="-",
    )
    gridlines.top_labels = False
    gridlines.right_labels = False
    gridlines.xlabel_style = {"size": 8, "color": "#17212b"}
    gridlines.ylabel_style = {"size": 8, "color": "#17212b"}

    add_route_and_moorings(ax, extent=extent)
    add_metadata(ax, product, source_day)


def plot_wind_snapshot(
    product: dict,
    dataset: Any,
    target_day: date,
    source_day: date,
    suffix: str = "",
    extent: dict | None = None,
) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    u10, v10, lon_name, lat_name = wind_components(dataset)
    speed = np.hypot(u10, v10)

    lon = u10[lon_name]
    lat = u10[lat_name]
    lon2d, lat2d = lat_lon_grids(lon, lat)

    step_y = max(1, speed.shape[0] // 30)
    step_x = max(1, speed.shape[1] // 40)

    fig = plt.figure(figsize=(14, 9), dpi=120)

    ax = plt.axes(projection=ccrs.PlateCarree())

    ax.add_feature(
        cfeature.LAND,
        facecolor="#f4efe6",
        edgecolor="0.35",
        linewidth=0.4,
        zorder=3,
    )

    ax.add_feature(
        cfeature.COASTLINE,
        linewidth=0.5,
        edgecolor="0.25",
        zorder=4,
    )

    plot_scalar_map(
        ax,
        fig,
        lon,
        lat,
        speed,
        get_cmocean_cmap("speed"),
        "10 m wind speed (m s$^{-1}$)",
        contours=True,
    )

    ax.quiver(
        lon2d[::step_y, ::step_x],
        lat2d[::step_y, ::step_x],
        u10.values[::step_y, ::step_x],
        v10.values[::step_y, ::step_x],
        color="#17212b",
        alpha=0.72,
        scale=450,
        transform=ccrs.PlateCarree(),
    )

    format_axes(ax, product, target_day, source_day, extent=extent)

    save_figure(fig, target_day, product, suffix=suffix)

    plt.close(fig)


def plot_derived_snapshot(
    product: dict,
    nc_path: Path,
    target_day: date,
    source_day: date,
    suffix: str = "",
    extent: dict | None = None,
) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    import xarray as xr
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    with xr.open_dataset(nc_path) as ds:
        u10, v10, lon_name, lat_name = wind_components(ds)

        lon = u10[lon_name]
        lat = u10[lat_name]
        lon2d, lat2d = lat_lon_grids(lon, lat)

        _ue, _ve, w_e, taux, tauy = ekman_fields(lon, lat, u10.values, v10.values)

        fig = plt.figure(figsize=(14, 9), dpi=120)
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(
            cfeature.LAND,
            facecolor="#f4efe6",
            edgecolor="0.35",
            linewidth=0.4,
            zorder=3,
        )

        ax.add_feature(
            cfeature.COASTLINE,
            linewidth=0.5,
            edgecolor="0.25",
            zorder=4,
        )

        if product["key"] == "WIND_STRESS":
            tau = np.hypot(taux, tauy)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                tau,
                get_cmocean_cmap("speed"),
                "Wind stress magnitude (N m$^{-2}$)",
                contours=True,
            )

            step_y = max(1, tau.shape[0] // 30)
            step_x = max(1, tau.shape[1] // 40)
            ax.quiver(
                lon2d[::step_y, ::step_x],
                lat2d[::step_y, ::step_x],
                taux[::step_y, ::step_x],
                tauy[::step_y, ::step_x],
                color="#17212b",
                alpha=0.75,
                scale=8,
                transform=ccrs.PlateCarree(),
            )

        else:
            plot_values = rolling_mean_2d(w_e, size=3) * 1e7

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                plot_values,
                get_cmocean_cmap("balance"),
                "Ekman pumping velocity, 3×3 spatial rolling mean from ERA5 past data only (10$^{-7}$ m s$^{-1}$)",
                signed=True,
                contours=True,
            )

            ax.contour(
                lon,
                lat,
                plot_values,
                levels=[0],
                colors="black",
                linewidths=0.9,
                alpha=0.75,
                transform=ccrs.PlateCarree(),
            )

        format_axes(ax, product, target_day, source_day, extent=extent)
        save_figure(fig, target_day, product, suffix=suffix)

        plt.close(fig)


def plot_snapshot(
    product: dict,
    nc_path: Path,
    target_day: date,
    source_day: date,
    salinity_path: Path | None = None,
    suffix: str = "",
    extent: dict | None = None,
) -> None:
    import matplotlib.pyplot as plt
    import numpy as np
    import xarray as xr
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    with xr.open_dataset(nc_path) as ds:

        if product.get("source") == "cds_era5":
            plot_wind_snapshot(
                product,
                ds,
                target_day,
                source_day,
                suffix=suffix,
                extent=extent,
            )
            return

        fig = plt.figure(figsize=(14, 9), dpi=120)

        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.add_feature(
            cfeature.LAND,
            facecolor="#f4efe6",
            edgecolor="0.35",
            linewidth=0.4,
            zorder=3,
        )

        ax.add_feature(
            cfeature.COASTLINE,
            linewidth=0.5,
            edgecolor="0.25",
            zorder=4,
        )

        if product["key"] == "MODEL_CURRENT":

            u_name = choose_variable(ds, ["uo"])
            v_name = choose_variable(ds, ["vo"])

            u = as_2d(ds, u_name)
            v = as_2d(ds, v_name)

            speed = np.hypot(u, v)

            lon, lat, _, _ = lon_lat_from_da(u)
            lon2d, lat2d = lat_lon_grids(lon, lat)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                speed,
                get_cmocean_cmap("speed"),
                "Surface current speed (m s$^{-1}$)",
                contours=True,
            )

            step_y = max(1, speed.shape[0] // 30)
            step_x = max(1, speed.shape[1] // 40)

            ax.quiver(
                lon2d[::step_y, ::step_x],
                lat2d[::step_y, ::step_x],
                u.values[::step_y, ::step_x],
                v.values[::step_y, ::step_x],
                color="#17212b",
                alpha=0.7,
                scale=12,
                transform=ccrs.PlateCarree(),
            )
            
        elif product["key"] == "MODEL_SAL":
            sp_name = choose_variable(ds, ["so"])
            sp = as_2d(ds, sp_name)
            sa = teos10_absolute_salinity(sp)

            lon, lat, _, _ = lon_lat_from_da(sa)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                sa,
                get_cmocean_cmap("haline"),
                "Absolute Salinity, SA (g kg$^{-1}$)",
                contours=True,
            )

        elif product["key"] == "MODEL_TEMP":
            theta_name = choose_variable(ds, ["thetao"])
            thetao = as_2d(ds, theta_name)

            if salinity_path is None:
                raise RuntimeError(
                    "MODEL_TEMP requires MODEL_SAL file for TEOS-10 Conservative Temperature."
                )

            with xr.open_dataset(salinity_path) as sal_ds:
                sp_name = choose_variable(sal_ds, ["so"])
                sp = as_2d(sal_ds, sp_name)
                ct = teos10_conservative_temperature(thetao, sp)

            lon, lat, _, _ = lon_lat_from_da(ct)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                ct,
                get_cmocean_cmap("thermal"),
                "Conservative Temperature, CT ($^\\circ$C)",
                contours=True,
            )

        elif product["key"] == "SAT_SLA":
            var_name = choose_variable(ds, ["sla", "adt"])
            da = as_2d(ds, var_name)

            lon, lat, _, _ = lon_lat_from_da(da)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                da,
                get_cmocean_cmap("balance"),
                f"{var_name} (m)",
                signed=True,
                contours=True,
                physical_levels=[x / 100 for x in range(-100, 105, 10)],
            )

        elif product["key"] == "SAT_CHL":
            var_name = choose_variable(ds, ["CHL", "chl"])
            da = as_2d(ds, var_name)

            lon, lat, _, _ = lon_lat_from_da(da)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                da,
                get_cmocean_cmap("algae"),
                "Chlorophyll-a (mg m$^{-3}$, log scale)",
                contours=False,
                log_norm=True,
            )

        elif product["key"] == "SAT_SSS":
            sp_name = choose_variable(ds, ["sos", "sss"])
            sp = as_2d(ds, sp_name)
            sa = teos10_absolute_salinity(sp)

            lon, lat, _, _ = lon_lat_from_da(sa)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                sa,
                get_cmocean_cmap("haline"),
                "Absolute Salinity, SA (g kg$^{-1}$)",
                contours=True,
            )

        elif product["key"] == "WAVES":
            var_name = choose_variable(ds, ["VHM0", "vhm0"])
            da = as_2d(ds, var_name)

            lon, lat, _, _ = lon_lat_from_da(da)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                da,
                get_cmocean_cmap("ice"),
                "Significant wave height, Hs (m)",
                contours=True,
            )

        else:
            var_name = choose_variable(ds, product["variables"])
            da = as_2d(ds, var_name)

            lon, lat, _, _ = lon_lat_from_da(da)

            plot_scalar_map(
                ax,
                fig,
                lon,
                lat,
                da,
                get_cmocean_cmap("tempo"),
                f"{var_name}",
                contours=True,
            )

        format_axes(ax, product, target_day, source_day, extent=extent)
        save_figure(fig, target_day, product, suffix=suffix)

        plt.close(fig)


def write_manifest(days: list[date], products: list[dict], status: dict[str, dict[str, dict]]) -> None:
    new_dates = [day.isoformat() for day in days]

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "forecast_start": new_dates[0] if new_dates else None,
        "forecast_end": new_dates[-1] if new_dates else None,
        "dates": new_dates,
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

    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)

    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote manifest: {MANIFEST_FILE}", flush=True)
    print(f"Manifest forecast window: {manifest['forecast_start']} to {manifest['forecast_end']}", flush=True)
    print(f"Manifest generated_at: {manifest['generated_at']}", flush=True)

def process_product(
    product: dict,
    products: list[dict],
    target_day: date,
    source_day: date,
    dry_run: bool,
    raw_cache: dict[tuple[str, str], Path],
    force_plots: bool = False,
) -> Path | None:

    full_snapshot = SNAPSHOT_DIR / f"{target_day.isoformat()}_{product['key']}.png"
    regional_snapshot = SNAPSHOT_DIR / f"{target_day.isoformat()}_{product['key']}_REGIONAL.png"

    needs_regional = product["key"] in REGIONAL_PRODUCTS

    if not force_plots and full_snapshot.exists() and full_snapshot.stat().st_size > 0:
        if not needs_regional or (
            regional_snapshot.exists() and regional_snapshot.stat().st_size > 0
        ):
            print(f"Using cached snapshot: {full_snapshot}", flush=True)
            return full_snapshot

    if product.get("source") == "derived":

        if dry_run:
            return None

        source_key = product["derives_from"]
        cache_key = (source_day.isoformat(), source_key)

        source_path = raw_cache.get(cache_key)

        if source_path is None:
            expected_path = DOWNLOAD_DIR / f"{source_day.isoformat()}_{source_key}.nc"

            source_path = (
                expected_path
                if expected_path.exists() and expected_path.stat().st_size > 0
                else None
            )

        if source_path is None:
            source_product = product_by_key(products, source_key)
            source_path = download_subset(source_product, source_day, dry_run)

            if source_path is not None:
                raw_cache[cache_key] = source_path

        if source_path is None:
            return None

        if force_plots or not full_snapshot.exists() or full_snapshot.stat().st_size == 0:
            plot_derived_snapshot(
                product,
                source_path,
                target_day,
                source_day,
            )

        if needs_regional and (
            force_plots or
            not regional_snapshot.exists() or regional_snapshot.stat().st_size == 0
        ):
            plot_derived_snapshot(
                product,
                source_path,
                target_day,
                source_day,
                suffix="_REGIONAL",
                extent=REGIONAL_EXTENT,
            )

        return source_path

    nc_path = download_subset(product, source_day, dry_run)

    if nc_path is not None:
        raw_cache[(source_day.isoformat(), product["key"])] = nc_path

        salinity_path = None

        if product["key"] == "MODEL_TEMP":
            sal_product = product_by_key(products, "MODEL_SAL")
            salinity_path = download_subset(sal_product, source_day, dry_run)

            if salinity_path is not None:
                raw_cache[(source_day.isoformat(), "MODEL_SAL")] = salinity_path

        if force_plots or not full_snapshot.exists() or full_snapshot.stat().st_size == 0:
            plot_snapshot(
                product,
                nc_path,
                target_day,
                source_day,
                salinity_path=salinity_path,
            )

        if needs_regional and (
            force_plots or
            not regional_snapshot.exists() or regional_snapshot.stat().st_size == 0
        ):
            plot_snapshot(
                product,
                nc_path,
                target_day,
                source_day,
                salinity_path=salinity_path,
                suffix="_REGIONAL",
                extent=REGIONAL_EXTENT,
            )

    return nc_path


def main() -> None:
    args = parse_args()

    days = target_days(args.date, args.days_ahead)

    print(f"Workflow input date: {args.date}", flush=True)
    print(f"days_ahead: {args.days_ahead}", flush=True)
    print(f"Target days: {[d.isoformat() for d in days]}", flush=True)

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
                        nc_path = process_product(
                            product,
                            products,
                            day,
                            source_day,
                            args.dry_run,
                            raw_cache,
                            force_plots=args.force_plots,
                        )

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
                        error_text = str(exc)
                        product_errors.append(f"{source_day.isoformat()}: {error_text}")

                        if "Please check that the dataset exists" in error_text:
                            raise RuntimeError("; ".join(product_errors))

                else:
                    raise RuntimeError("; ".join(product_errors))

            except Exception as exc:
                message = f"{day_key} {product_key}: {exc}"
                status[day_key][product_key] = {"available": False, "error": str(exc)}
                failures.append(message)

                print(f"ERROR {message}", file=sys.stderr, flush=True)

                if not args.allow_partial:
                    raise

    if not args.dry_run:
        write_manifest(days, products, status)

    if failures:
        print("Completed with product failures:", file=sys.stderr, flush=True)

        for failure in failures:
            print(f"- {failure}", file=sys.stderr, flush=True)

    if not args.dry_run and made_snapshots == 0:
        raise SystemExit("No snapshots were generated. Check credentials, dataset IDs, and requested date.")


if __name__ == "__main__":
    main()
