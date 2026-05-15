let products = [
  {
    key: "WAVES",
    label: "Wave height and period",
    dataset: "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i",
    product: "GLOBAL_ANALYSISFORECAST_WAV_001_027",
    variables: "VHM0, VTPK, VMDR",
    institution: "Meteo-France / Copernicus Marine Service",
    cadence: "3-hourly",
    reference: "https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_WAV_001_027/services",
  },
  {
    key: "MODEL_CURRENT",
    label: "Model currents",
    dataset: "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",
    product: "GLOBAL_ANALYSISFORECAST_PHY_001_024",
    variables: "uo, vo",
    institution: "Mercator Ocean International",
    cadence: "Daily forecast",
    reference: "https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/services",
  },
  {
    key: "MODEL_TEMP",
    label: "Model temperature",
    dataset: "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
    product: "GLOBAL_ANALYSISFORECAST_PHY_001_024",
    variables: "thetao",
    institution: "Mercator Ocean International",
    cadence: "Daily forecast",
    reference: "https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/services",
  },
  {
    key: "MODEL_SAL",
    label: "Model salinity",
    dataset: "cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
    product: "GLOBAL_ANALYSISFORECAST_PHY_001_024",
    variables: "so",
    institution: "Mercator Ocean International",
    cadence: "Daily forecast",
    reference: "https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/services",
    category: "Modeled forecast",
    status: "automated",
  },
];

let snapshots = rollingForecastDates();
let availabilityStatus = {};
let manifestGeneratedAt = null;
let mooringFeatures = [];

const bundledSnapshots = [
  {
    date: "2026-05-14",
    productKey: "WAVES",
    path: "assets/snapshots/2026-05-14_WAVES.png",
  },
  {
    date: "2026-05-14",
    productKey: "SAT_SLA",
    path: "assets/snapshots/2026-05-14_SLA.png",
  },
];

const routePoints = [
  { name: "Recife, Brazil", lat: -8.0476, lon: -34.877, note: "Departure, 30 May 2026" },
  { name: "Equatorial Atlantic waypoint", lat: 0.0, lon: -23.0, note: "Editable planning waypoint" },
  { name: "Cape Verde Ocean Observatory area", lat: 17.6, lon: -24.3, note: "Regional science area" },
  { name: "Mindelo, Cabo Verde", lat: 16.886, lon: -24.9958, note: "Port call / operations hub" },
  { name: "Emden, Germany", lat: 53.367, lon: 7.207, note: "Arrival, 28 Jun 2026" },
];

function placeholderSvg(product, date) {
  const colors = {
    WAVES: ["#0b4761", "#1e91a8", "#ffe08a", "#d95f35"],
    MODEL_CURRENT: ["#153d4d", "#499a83", "#f2c14e", "#bf4e30"],
    MODEL_TEMP: ["#163c59", "#2386a8", "#f0c86a", "#bf4c35"],
    MODEL_SAL: ["#14324d", "#477b9f", "#d7e6de", "#edb458"],
    SAT_SLA: ["#193a72", "#e3eef6", "#c44536", "#5d1f1a"],
    SAT_SST: ["#0f4862", "#2d9a8e", "#f5c95c", "#c73d2f"],
    SAT_SSS: ["#123b56", "#2d7f94", "#d7e6de", "#edb458"],
    SAT_CHL: ["#14382d", "#2f8f6b", "#bedb39", "#f2d16b"],
    ERA5_WIND: ["#153d4d", "#2f8f6b", "#f2c14e", "#d95f35"],
    WIND_STRESS: ["#17212b", "#75485e", "#d95f35", "#f2c14e"],
    ARGO_PROFILES: ["#253746", "#4a7c95", "#9fc2cc", "#f6c85f"],
    ARGO_VELOCITY: ["#253746", "#33658a", "#86bbd8", "#f26419"],
    GDP_DRIFTERS: ["#153d4d", "#2f8f6b", "#f2c14e", "#d95f35"],
    EKMAN_PUMPING: ["#17212b", "#0a5f78", "#f2c14e", "#d95f35"],
    UPWELLING_INDEX: ["#14382d", "#2f8f6b", "#dce9ef", "#d95f35"],
    EDDY_DIAGNOSTICS: ["#17212b", "#3d5a80", "#98c1d9", "#ee6c4d"],
  };
  const palette = colors[product.key] || colors.WAVES;
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 900" role="img">
      <defs>
        <linearGradient id="sea" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stop-color="${palette[0]}"/>
          <stop offset="0.52" stop-color="${palette[1]}"/>
          <stop offset="0.78" stop-color="${palette[2]}"/>
          <stop offset="1" stop-color="${palette[3]}"/>
        </linearGradient>
        <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
          <path d="M80 0H0V80" fill="none" stroke="rgba(255,255,255,.18)" stroke-width="2"/>
        </pattern>
      </defs>
      <rect width="1400" height="900" fill="url(#sea)"/>
      <rect width="1400" height="900" fill="url(#grid)"/>
      <path d="M110 720 C310 620 430 510 540 438 S780 266 920 230 S1130 225 1270 160" fill="none" stroke="white" stroke-width="10" stroke-linecap="round" opacity=".88"/>
      <path d="M110 720 C310 620 430 510 540 438 S780 266 920 230 S1130 225 1270 160" fill="none" stroke="#d95f35" stroke-width="4" stroke-linecap="round"/>
      <g fill="#fff" stroke="#17212b" stroke-width="5">
        <circle cx="110" cy="720" r="16"/><circle cx="540" cy="438" r="16"/><circle cx="920" cy="230" r="16"/><circle cx="1270" cy="160" r="16"/>
      </g>
      <rect x="56" y="56" width="760" height="188" rx="14" fill="rgba(3,22,32,.56)"/>
      <text x="88" y="120" fill="white" font-family="Inter, Arial" font-size="44" font-weight="800">Map pending</text>
      <text x="88" y="172" fill="rgba(255,255,255,.88)" font-family="Inter, Arial" font-size="27">${product.label}</text>
      <text x="88" y="210" fill="rgba(255,255,255,.76)" font-family="Inter, Arial" font-size="22">${date} - waiting for the Copernicus workflow output</text>
      <text x="56" y="826" fill="rgba(255,255,255,.86)" font-family="Inter, Arial" font-size="22">${product.dataset}</text>
    </svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

async function loadProductsConfig() {
  try {
    const response = await fetch(`data/products.json?cache=${Date.now()}`);
    if (!response.ok) {
      return;
    }
    const config = await response.json();
    products = config.map((product) => ({
      key: product.key,
      label: product.label,
      dataset: product.dataset_id,
      product: product.product || product.dataset_id,
      variables: product.variables.join(", "),
      institution: product.institution || sourceLabel(product.category),
      cadence: product.workflow_enabled === false ? "On demand" : "Rolling daily",
      reference: product.product_url,
      category: product.category || "Modeled forecast",
      status: product.status || "planned",
      workflowEnabled: product.workflow_enabled !== false,
    }));
  } catch {
    // Keep the embedded forecast defaults when local preview cannot fetch JSON.
  }
}

function sourceLabel(category) {
  if (category === "Satellite-derived maps") {
    return "Copernicus Marine satellite products";
  }
  if (category === "Freely available in-situ data") {
    return "Copernicus Marine / NOAA public data";
  }
  if (category === "Derived variables") {
    return "Computed from dashboard input fields";
  }
  return "Copernicus Marine Service";
}

function rollingForecastDates() {
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  return Array.from({ length: 6 }, (_, offset) => {
    const day = new Date(today);
    day.setUTCDate(today.getUTCDate() + offset);
    return day.toISOString().slice(0, 10);
  });
}

async function loadManifest() {
  try {
    const response = await fetch(`data/manifest.json?cache=${Date.now()}`);
    if (!response.ok) {
      return;
    }
    const manifest = await response.json();
    if (Array.isArray(manifest.dates) && manifest.dates.length > 0) {
      snapshots = manifest.dates;
    }
    availabilityStatus = manifest.status || {};
    manifestGeneratedAt = manifest.generated_at || null;
  } catch {
    availabilityStatus = {};
  }
}

async function loadMoorings() {
  try {
    const response = await fetch(`data/moorings.geojson?cache=${Date.now()}`);
    if (!response.ok) {
      return;
    }
    const geojson = await response.json();
    mooringFeatures = geojson.features || [];
  } catch {
    mooringFeatures = [];
  }
}

function addBundledSnapshots() {
  bundledSnapshots.forEach((snapshot) => {
    if (!snapshots.includes(snapshot.date)) {
      snapshots.unshift(snapshot.date);
    }
    availabilityStatus[snapshot.date] = availabilityStatus[snapshot.date] || {};
    availabilityStatus[snapshot.date][snapshot.productKey] = {
      available: true,
      path: snapshot.path,
      note: "Bundled sample map",
    };
  });
  snapshots = [...new Set(snapshots)];
}

function isAvailable(date, productKey) {
  return Boolean(availabilityStatus[date]?.[productKey]?.available);
}

function availableSnapshotEntries() {
  return snapshots.flatMap((date) =>
    Object.entries(availabilityStatus[date] || {})
      .filter(([, state]) => state?.available && state?.path)
      .map(([productKey, state]) => ({ date, productKey, state })),
  );
}

function resolveSnapshot(date, product) {
  const exact = availabilityStatus[date]?.[product.key];
  if (exact?.available && exact.path) {
    return { date, productKey: product.key, state: exact, fallback: false };
  }

  const sameProduct = availableSnapshotEntries()
    .filter((entry) => entry.productKey === product.key)
    .sort((a, b) => b.date.localeCompare(a.date));
  if (sameProduct.length > 0) {
    return { ...sameProduct[0], fallback: true };
  }

  const sameCategoryKeys = new Set(
    products.filter((item) => item.category === product.category).map((item) => item.key),
  );
  const sameCategory = availableSnapshotEntries()
    .filter((entry) => sameCategoryKeys.has(entry.productKey))
    .sort((a, b) => b.date.localeCompare(a.date));
  if (sameCategory.length > 0) {
    return { ...sameCategory[0], fallback: true };
  }

  const anyAvailable = availableSnapshotEntries().sort((a, b) => b.date.localeCompare(a.date));
  if (anyAvailable.length > 0) {
    return { ...anyAvailable[0], fallback: true };
  }

  return {
    date,
    productKey: product.key,
    state: { available: false, path: `assets/snapshots/${date}_${product.key}.png` },
    fallback: false,
  };
}

function initControls() {
  const datasetSelect = document.querySelector("#dataset-select");
  const dateSelect = document.querySelector("#date-select");

  products.forEach((product) => {
    const option = document.createElement("option");
    option.value = product.key;
    option.textContent = `${product.label} - ${product.category}`;
    datasetSelect.append(option);
  });

  snapshots.forEach((date) => {
    const option = document.createElement("option");
    option.value = date;
    option.textContent = date;
    dateSelect.append(option);
  });

  datasetSelect.addEventListener("change", renderSnapshot);
  dateSelect.addEventListener("change", renderSnapshot);
}

function renderSnapshot() {
  const product = products.find((item) => item.key === document.querySelector("#dataset-select").value);
  const date = document.querySelector("#date-select").value;
  const img = document.querySelector("#snapshot-image");
  const snapshot = resolveSnapshot(date, product);
  const shownProduct = products.find((item) => item.key === snapshot.productKey) || product;
  const available = Boolean(snapshot.state.available);

  img.onerror = () => {
    img.onerror = null;
    img.src = placeholderSvg(product, date);
    img.classList.add("placeholder-map");
  };
  img.classList.toggle("placeholder-map", !available);
  img.src = snapshot.state.path;
  img.alt = `${shownProduct.label} snapshot for ${snapshot.date}`;
  const state = available ? "available map" : product.status;
  const sourceDate =
    snapshot.state.source_date && snapshot.state.source_date !== snapshot.date
      ? ` using ${snapshot.state.source_date} source data`
      : "";
  const fallbackText = snapshot.fallback
    ? ` Requested ${product.label} for ${date}; showing latest available ${shownProduct.label} from ${snapshot.date}${sourceDate}.`
    : "";
  document.querySelector("#snapshot-caption").textContent =
    `${shownProduct.label} (${shownProduct.variables}) from ${shownProduct.dataset}; ${state} for ${snapshot.date}.${fallbackText}`;
}

function renderAvailability() {
  const table = document.querySelector("#availability-table");
  table.innerHTML = "";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  ["Product", "Category", ...snapshots.map((date) => date.slice(5))].forEach((label) => {
    const th = document.createElement("th");
    th.textContent = label;
    headRow.append(th);
  });
  thead.append(headRow);
  table.append(thead);

  const tbody = document.createElement("tbody");
  products.forEach((product, productIndex) => {
    const row = document.createElement("tr");
    const name = document.createElement("td");
    name.textContent = product.key;
    row.append(name);
    const category = document.createElement("td");
    category.textContent = product.category || "";
    row.append(category);
    snapshots.forEach((date) => {
      const cell = document.createElement("td");
      const available = isAvailable(date, product.key);
      cell.textContent = available ? "X" : "pending";
      cell.className = available ? "available" : "pending";
      row.append(cell);
    });
    tbody.append(row);
  });
  table.append(tbody);
}

function renderProducts() {
  const table = document.querySelector("#products-table");
  table.innerHTML = `<thead><tr>
    <th>Layer</th><th>Category</th><th>Dataset ID</th><th>Variables</th><th>Status</th><th>Institution/source</th><th>Reference</th>
  </tr></thead>`;
  const tbody = document.createElement("tbody");
  products.forEach((product) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${product.label}</td>
      <td>${product.category}</td>
      <td><code>${product.dataset}</code></td>
      <td>${product.variables}</td>
      <td>${product.status || product.cadence}</td>
      <td>${product.institution}</td>
      <td><a href="${product.reference}">Product page</a></td>`;
    tbody.append(row);
  });
  table.append(tbody);
}

function projectPoint(lon, lat) {
  const bounds = { minLon: -43, maxLon: 12, minLat: -14, maxLat: 58 };
  const x = ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * 1000;
  const y = (1 - (lat - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * 620;
  return [x, y];
}

function pointPath(points) {
  return points
    .map((point, index) => {
      const [x, y] = projectPoint(point.lon, point.lat);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

function renderRouteOverview() {
  const routePath = pointPath(routePoints);
  const stopMarkers = routePoints
    .map((point) => {
      const [x, y] = projectPoint(point.lon, point.lat);
      return `
        <g>
          <circle cx="${x}" cy="${y}" r="7" class="route-stop" />
          <text x="${x + 11}" y="${y - 8}" class="route-label">${point.name}</text>
        </g>`;
    })
    .join("");
  const mooringMarkers = mooringFeatures
    .map((feature) => {
      const [lon, lat] = feature.geometry.coordinates;
      const [x, y] = projectPoint(lon, lat);
      const label = feature.properties.label;
      return `
        <g>
          <text x="${x}" y="${y}" class="route-star">*</text>
          <text x="${x + 13}" y="${y - 4}" class="mooring-map-label">${label}</text>
        </g>`;
    })
    .join("");

  document.querySelector("#map").innerHTML = `
    <svg class="route-overview" viewBox="0 0 1000 620" role="img" aria-label="M219 route and GEOMAR moorings">
      <defs>
        <linearGradient id="routeSea" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stop-color="#e9f4f7" />
          <stop offset="1" stop-color="#b7dbe5" />
        </linearGradient>
        <pattern id="routeGrid" width="92" height="92" patternUnits="userSpaceOnUse">
          <path d="M92 0H0V92" fill="none" stroke="rgba(10,95,120,.16)" stroke-width="1.2" />
        </pattern>
      </defs>
      <rect width="1000" height="620" fill="url(#routeSea)" />
      <rect width="1000" height="620" fill="url(#routeGrid)" />
      <path class="land" d="M0 470 C70 455 105 510 170 514 L170 620 L0 620Z" />
      <path class="land" d="M615 0 C665 42 678 115 654 185 C624 272 702 335 760 365 C842 409 855 500 805 620 L1000 620 L1000 0Z" />
      <path class="land" d="M753 0 C780 36 779 79 754 113 C718 163 725 203 760 244 C810 300 849 344 866 407 C889 493 864 559 836 620 L1000 620 L1000 0Z" />
      <text x="24" y="44" class="overview-title">M219 WAVES route overview</text>
      <text x="24" y="74" class="overview-subtitle">Recife - 23W Equator - CVOO/Mindelo - Emden, with GEOMAR moorings</text>
      <path d="${routePath}" class="route-shadow" />
      <path d="${routePath}" class="route-line" />
      ${stopMarkers}
      ${mooringMarkers}
      <g class="route-legend">
        <circle cx="0" cy="0" r="6" class="route-stop" />
        <text x="14" y="5">Cruise waypoint</text>
        <text x="0" y="31" class="route-star">*</text>
        <text x="14" y="31">GEOMAR mooring</text>
      </g>
    </svg>`;
}

function initMap() {
  renderRouteOverview();
}

async function init() {
  await loadProductsConfig();
  await loadManifest();
  addBundledSnapshots();
  await loadMoorings();
  initControls();
  renderSnapshot();
  renderAvailability();
  renderProducts();
  initMap();
  const updated = manifestGeneratedAt ? manifestGeneratedAt.slice(0, 10) : new Date().toISOString().slice(0, 10);
  document.querySelector("#last-updated").textContent = `Forecast window updated: ${updated} UTC`;
}

init();
