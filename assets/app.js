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
  {
    date: "2026-05-14",
    productKey: "SAT_SST",
    path: "assets/snapshots/2026-05-14_SST_L4.png",
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
    SAT_CHL: ["#14382d", "#2f8f6b", "#bedb39", "#f2d16b"],
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
  const expectedPath =
    availabilityStatus[date]?.[product.key]?.path || `assets/snapshots/${date}_${product.key}.png`;
  const available = isAvailable(date, product.key);

  img.onerror = () => {
    img.onerror = null;
    img.src = placeholderSvg(product, date);
    img.classList.add("placeholder-map");
  };
  img.classList.toggle("placeholder-map", !available);
  img.src = expectedPath;
  img.alt = `${product.label} snapshot for ${date}`;
  const state = available ? "available map" : product.status;
  document.querySelector("#snapshot-caption").textContent =
    `${product.label} (${product.variables}) from ${product.dataset}; ${state} for ${date}.`;
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

function initMap() {
  const map = L.map("map", { scrollWheelZoom: false });
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 12,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const latLngs = routePoints.map((point) => [point.lat, point.lon]);
  L.polyline(latLngs, { color: "#d95f35", weight: 4, opacity: 0.95 }).addTo(map);
  routePoints.forEach((point) => {
    L.circleMarker([point.lat, point.lon], {
      radius: 7,
      color: "#17212b",
      weight: 2,
      fillColor: "#fff",
      fillOpacity: 1,
    })
      .addTo(map)
      .bindPopup(`<strong>${point.name}</strong><br>${point.note}`);
  });
  mooringFeatures.forEach((feature) => {
    const [lon, lat] = feature.geometry.coordinates;
    const props = feature.properties;
    const icon = L.divIcon({
      className: "mooring-marker",
      html: `<span class="mooring-star">*</span><span class="mooring-label">${props.label}</span>`,
      iconSize: [120, 24],
      iconAnchor: [10, 12],
    });
    L.marker([lat, lon], { icon })
      .addTo(map)
      .bindPopup(
        `<strong>${props.label}</strong><br>${props.region}<br>Water depth: ${props.water_depth_m} m`,
      );
  });
  map.fitBounds(latLngs, { padding: [28, 28] });
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
