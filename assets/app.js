const products = [
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
    key: "WIND",
    label: "Surface wind and stress",
    dataset: "cmems_obs-wind_glo_phy_nrt_l4_0.125deg_PT1H",
    product: "WIND_GLO_PHY_L4_NRT_012_004",
    variables: "eastward_wind, northward_wind, wind_speed",
    institution: "KNMI / Copernicus Marine Service",
    cadence: "Hourly",
    reference: "https://data.marine.copernicus.eu/products",
  },
  {
    key: "SLA",
    label: "Sea level anomaly",
    dataset: "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
    product: "SEALEVEL_GLO_PHY_L4_NRT_008_046",
    variables: "sla, adt, ugos, vgos",
    institution: "CLS, CNES / Copernicus Marine Service",
    cadence: "Daily",
    reference: "https://data.marine.copernicus.eu/products",
  },
  {
    key: "SST_L4",
    label: "Sea surface temperature",
    dataset: "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
    product: "SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001",
    variables: "analysed_sst",
    institution: "UK Met Office",
    cadence: "Daily",
    reference: "https://data.marine.copernicus.eu/products",
  },
  {
    key: "CHL",
    label: "Chlorophyll-a",
    dataset: "cmems_obs-oc_glo_bgc-plankton_nrt_l3-multi-4km_P1D",
    product: "OCEANCOLOUR_GLO_BGC_L3_NRT_009_101",
    variables: "CHL",
    institution: "ACRI / GlobColour",
    cadence: "Daily",
    reference: "https://data.marine.copernicus.eu/products",
  },
  {
    key: "MODEL_TEMP",
    label: "Model temperature",
    dataset: "cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m",
    product: "GLOBAL_ANALYSISFORECAST_PHY_001_024",
    variables: "thetao",
    institution: "Mercator Ocean International",
    cadence: "Daily",
    reference: "https://data.marine.copernicus.eu/products",
  },
  {
    key: "MODEL_SAL",
    label: "Model salinity",
    dataset: "cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
    product: "GLOBAL_ANALYSISFORECAST_PHY_001_024",
    variables: "so",
    institution: "Mercator Ocean International",
    cadence: "Daily",
    reference: "https://data.marine.copernicus.eu/products",
  },
];

const snapshots = [
  "2026-05-30",
  "2026-05-31",
  "2026-06-01",
  "2026-06-02",
  "2026-06-03",
  "2026-06-04",
  "2026-06-05",
  "2026-06-06",
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
    WIND: ["#153d4d", "#499a83", "#f2c14e", "#bf4e30"],
    SLA: ["#193a72", "#e3eef6", "#c44536", "#5d1f1a"],
    SST_L4: ["#0f4862", "#2d9a8e", "#f5c95c", "#c73d2f"],
    CHL: ["#14382d", "#2f8f6b", "#bedb39", "#f2d16b"],
    MODEL_TEMP: ["#163c59", "#2386a8", "#f0c86a", "#bf4c35"],
    MODEL_SAL: ["#14324d", "#477b9f", "#d7e6de", "#edb458"],
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
      <path d="M110 720 C310 620 430 510 540 438 S780 266 920 230 S1130 225 1270 160" fill="none" stroke="white" stroke-width="10" stroke-linecap="round" opacity=".92"/>
      <path d="M110 720 C310 620 430 510 540 438 S780 266 920 230 S1130 225 1270 160" fill="none" stroke="#d95f35" stroke-width="4" stroke-linecap="round"/>
      <g fill="#fff" stroke="#17212b" stroke-width="5">
        <circle cx="110" cy="720" r="16"/><circle cx="540" cy="438" r="16"/><circle cx="920" cy="230" r="16"/><circle cx="1270" cy="160" r="16"/>
      </g>
      <text x="56" y="76" fill="white" font-family="Inter, Arial" font-size="42" font-weight="800">${product.label}</text>
      <text x="56" y="126" fill="rgba(255,255,255,.86)" font-family="Inter, Arial" font-size="26">${date} - placeholder until Copernicus run is published</text>
      <text x="56" y="826" fill="rgba(255,255,255,.86)" font-family="Inter, Arial" font-size="24">${product.dataset}</text>
    </svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function initControls() {
  const datasetSelect = document.querySelector("#dataset-select");
  const dateSelect = document.querySelector("#date-select");

  products.forEach((product) => {
    const option = document.createElement("option");
    option.value = product.key;
    option.textContent = product.label;
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
  const expectedPath = `assets/snapshots/${date}_${product.key}.png`;

  img.onerror = () => {
    img.onerror = null;
    img.src = placeholderSvg(product, date);
  };
  img.src = expectedPath;
  img.alt = `${product.label} snapshot for ${date}`;
  document.querySelector("#snapshot-caption").textContent =
    `${product.label} (${product.variables}) from ${product.dataset}.`;
}

function renderAvailability() {
  const table = document.querySelector("#availability-table");
  table.innerHTML = "";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  ["Product", ...snapshots.map((date) => date.slice(5))].forEach((label) => {
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
    snapshots.forEach((_, index) => {
      const cell = document.createElement("td");
      const available = index <= Math.max(1, 7 - productIndex);
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
    <th>Layer</th><th>Dataset ID</th><th>Variables</th><th>Cadence</th><th>Institution</th><th>Reference</th>
  </tr></thead>`;
  const tbody = document.createElement("tbody");
  products.forEach((product) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${product.label}</td>
      <td><code>${product.dataset}</code></td>
      <td>${product.variables}</td>
      <td>${product.cadence}</td>
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
  map.fitBounds(latLngs, { padding: [28, 28] });
}

function init() {
  initControls();
  renderSnapshot();
  renderAvailability();
  renderProducts();
  initMap();
  document.querySelector("#last-updated").textContent = `Last updated: ${new Date().toISOString().slice(0, 10)} UTC`;
}

init();
