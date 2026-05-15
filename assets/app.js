const MANIFEST_URL = "data/manifest.json";
const PRODUCTS_URL = "data/products.json";

const ROUTE = [
  [-34.877, -8.0476],
  [-23.0, 0.0],
  [-24.3, 17.6],
  [-24.9958, 16.886],
  [7.207, 53.367],
];

let manifest = null;
let products = [];
let selectedProductKey = null;
let selectedDate = null;

let zoomState = {
  scale: 1,
  x: 0,
  y: 0,
  dragging: false,
  startX: 0,
  startY: 0,
  originX: 0,
  originY: 0,
};

const datasetSelect = document.getElementById("dataset-select");
const dateSelect = document.getElementById("date-select");
const snapshotImage = document.getElementById("snapshot-image");
const snapshotCaption = document.getElementById("snapshot-caption");
const availabilityTable = document.getElementById("availability-table");
const productsTable = document.getElementById("products-table");
const lastUpdated = document.getElementById("last-updated");

async function loadJson(url) {
  const response = await fetch(`${url}?v=${Date.now()}`);
  if (!response.ok) throw new Error(`Could not load ${url}`);
  return response.json();
}

function sortedDates() {
  return [...(manifest?.dates || [])].sort((a, b) => new Date(a) - new Date(b));
}

function productByKey(productKey) {
  return products.find((p) => p.key === productKey);
}

function statusFor(date, productKey) {
  return manifest?.status?.[date]?.[productKey] || null;
}

function isAvailable(date, productKey) {
  return Boolean(statusFor(date, productKey)?.available);
}

function sourceDateLabel(date, productKey) {
  const status = statusFor(date, productKey);
  if (!status?.source_date || status.source_date === date) return "";
  return ` using ${status.source_date}`;
}

function setLastUpdated() {
  if (!manifest?.generated_at) {
    lastUpdated.textContent = "Forecast window updated: pending first data run";
    return;
  }

  const generated = new Date(manifest.generated_at);
  lastUpdated.textContent = `Forecast window updated: ${generated
    .toISOString()
    .replace("T", " ")
    .slice(0, 16)} UTC`;
}

function populateSelectors() {
  datasetSelect.innerHTML = "";
  dateSelect.innerHTML = "";

  const dates = sortedDates();
  const productList = products.filter((p) => p.workflow_enabled !== false);

  for (const product of productList) {
    const option = document.createElement("option");
    option.value = product.key;
    option.textContent = product.label || product.key;
    datasetSelect.appendChild(option);
  }

  for (const date of dates) {
    const option = document.createElement("option");
    option.value = date;
    option.textContent = date;
    dateSelect.appendChild(option);
  }

  selectedProductKey =
    productList.find((p) => dates.some((d) => isAvailable(d, p.key)))?.key ||
    productList[0]?.key ||
    null;

  selectedDate =
    dates.find((d) => selectedProductKey && isAvailable(d, selectedProductKey)) ||
    dates[dates.length - 1] ||
    null;

  if (selectedProductKey) datasetSelect.value = selectedProductKey;
  if (selectedDate) dateSelect.value = selectedDate;
}

function updateSnapshot() {
  if (!selectedProductKey || !selectedDate) return;

  const status = statusFor(selectedDate, selectedProductKey);
  const product = productByKey(selectedProductKey);
  const label = product?.label || selectedProductKey;

  resetZoom();

  if (status?.available && status.path) {
    snapshotImage.src = `${status.path}?v=${manifest.generated_at || Date.now()}`;
    snapshotImage.alt = `${label} for ${selectedDate}`;
    snapshotCaption.textContent = `${label} | shown for ${selectedDate}${sourceDateLabel(
      selectedDate,
      selectedProductKey
    )}`;
  } else {
    snapshotImage.removeAttribute("src");
    snapshotImage.alt = "No snapshot available";
    snapshotCaption.textContent = `${label} | no snapshot available for ${selectedDate}`;
  }

  highlightAvailabilitySelection();
}

function renderAvailabilityTable() {
  const dates = sortedDates();

  let html = "<thead><tr><th>Product</th>";

  for (const date of dates) {
    html += `<th>${date}</th>`;
  }

  html += "</tr></thead><tbody>";

  for (const product of products) {
    const planned = product.workflow_enabled === false;

    html += `<tr data-product="${product.key}" class="${planned ? "planned-row" : ""}">`;
    html += `<th>${product.label || product.key}<small>${product.key}</small></th>`;

    for (const date of dates) {
      const status = statusFor(date, product.key);

      if (planned) {
        html += `<td><span class="status planned">planned</span></td>`;
      } else if (status?.available) {
        const source =
          status.source_date && status.source_date !== date
            ? `Source date: ${status.source_date}`
            : "Available";

        html += `<td title="${source}">
          <button class="status available" data-product="${product.key}" data-date="${date}">✓</button>
        </td>`;
      } else if (status?.error) {
        html += `<td title="${escapeHtml(status.error)}"><span class="status failed">×</span></td>`;
      } else {
        html += `<td><span class="status missing">—</span></td>`;
      }
    }

    html += "</tr>";
  }

  html += "</tbody>";
  availabilityTable.innerHTML = html;

  availabilityTable.querySelectorAll("button.status.available").forEach((button) => {
    button.addEventListener("click", () => {
      selectedProductKey = button.dataset.product;
      selectedDate = button.dataset.date;

      datasetSelect.value = selectedProductKey;
      dateSelect.value = selectedDate;

      updateSnapshot();
    });
  });

  highlightAvailabilitySelection();
}

function highlightAvailabilitySelection() {
  availabilityTable.querySelectorAll("td, th").forEach((cell) => {
    cell.classList.remove("selected-cell", "selected-row");
  });

  availabilityTable
    .querySelectorAll(`tr[data-product="${selectedProductKey}"] th`)
    .forEach((cell) => {
      cell.classList.add("selected-row");
    });

  availabilityTable
    .querySelectorAll(`button[data-product="${selectedProductKey}"][data-date="${selectedDate}"]`)
    .forEach((button) => {
      button.closest("td")?.classList.add("selected-cell");
    });
}

function renderProductsTable() {
  let html = `
    <thead>
      <tr>
        <th>Product</th>
        <th>Category</th>
        <th>Status</th>
        <th>Dataset ID</th>
        <th>Variables</th>
        <th>Source</th>
      </tr>
    </thead>
    <tbody>
  `;

  for (const product of products) {
    const statusText = product.workflow_enabled === false ? "planned" : product.status || "automated";

    const productUrl = product.product_url
      ? `<a href="${product.product_url}" target="_blank" rel="noopener">Official page</a>`
      : "";

    html += `
      <tr>
        <td><strong>${product.label || product.key}</strong><small>${product.key}</small></td>
        <td>${product.category || "Not specified"}</td>
        <td>${statusText}</td>
        <td><code>${product.dataset_id || "derived"}</code></td>
        <td>${(product.variables || []).map((v) => `<code>${v}</code>`).join(" ")}</td>
        <td>${productUrl}</td>
      </tr>
    `;
  }

  html += "</tbody>";
  productsTable.innerHTML = html;
}

function renderRouteMap() {
  const map = document.getElementById("map");
  if (!map) return;

  const width = 900;
  const height = 700;
  const padding = 55;

  const lons = ROUTE.map((p) => p[0]);
  const lats = ROUTE.map((p) => p[1]);

  const lonMin = Math.min(...lons) - 6;
  const lonMax = Math.max(...lons) + 6;
  const latMin = Math.min(...lats) - 8;
  const latMax = Math.max(...lats) + 6;

  const project = ([lon, lat]) => {
    const x = padding + ((lon - lonMin) / (lonMax - lonMin)) * (width - 2 * padding);
    const y = height - padding - ((lat - latMin) / (latMax - latMin)) * (height - 2 * padding);
    return [x, y];
  };

  const points = ROUTE.map(project);
  const path = points.map((p) => p.join(",")).join(" ");

  map.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Planned M219 cruise route">
      <defs>
        <linearGradient id="seaGradient" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#dceff6"/>
          <stop offset="100%" stop-color="#8bb8cf"/>
        </linearGradient>
      </defs>

      <rect width="${width}" height="${height}" rx="22" fill="url(#seaGradient)"/>

      ${gridLines(width, height, padding)}

      <polyline points="${path}" fill="none" stroke="white" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" opacity="0.7"/>
      <polyline points="${path}" fill="none" stroke="#d95f35" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="12 10"/>

      ${points
        .map(
          ([x, y], i) => `
            <circle cx="${x}" cy="${y}" r="8" fill="white" stroke="#17212b" stroke-width="2"/>
            <text x="${x + 11}" y="${y - 9}" font-size="18" font-weight="700" fill="#17212b">${i + 1}</text>
          `
        )
        .join("")}

      <text x="${padding}" y="${height - 24}" font-size="18" fill="#17212b">
        Planned route: Recife → Equatorial Atlantic → Cape Verde/CVOO → Kiel
      </text>
    </svg>
  `;
}

function gridLines(width, height, padding) {
  let lines = "";

  for (let i = 1; i <= 5; i++) {
    const x = padding + i * ((width - 2 * padding) / 6);
    lines += `<line x1="${x}" y1="${padding}" x2="${x}" y2="${
      height - padding
    }" stroke="white" stroke-width="1" opacity="0.35"/>`;
  }

  for (let i = 1; i <= 4; i++) {
    const y = padding + i * ((height - 2 * padding) / 5);
    lines += `<line x1="${padding}" y1="${y}" x2="${
      width - padding
    }" y2="${y}" stroke="white" stroke-width="1" opacity="0.35"/>`;
  }

  return lines;
}

function resetZoom() {
  zoomState.scale = 1;
  zoomState.x = 0;
  zoomState.y = 0;
  zoomState.dragging = false;
  applyZoom();
}

function applyZoom() {
  snapshotImage.style.transform = `translate(${zoomState.x}px, ${zoomState.y}px) scale(${zoomState.scale})`;
}

function zoomAtCenter(factor) {
  zoomState.scale = Math.max(1, Math.min(zoomState.scale * factor, 6));

  if (zoomState.scale === 1) {
    zoomState.x = 0;
    zoomState.y = 0;
  }

  applyZoom();
}

function setupZoomControls() {
  const stage = document.querySelector(".zoom-stage");
  if (!stage) return;

  document.querySelectorAll("[data-zoom-target='snapshot']").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.zoomAction;

      if (action === "in") zoomAtCenter(1.25);
      if (action === "out") zoomAtCenter(1 / 1.25);
      if (action === "reset") resetZoom();
    });
  });

  stage.addEventListener("pointerdown", (event) => {
    if (zoomState.scale <= 1) return;

    zoomState.dragging = true;
    zoomState.startX = event.clientX;
    zoomState.startY = event.clientY;
    zoomState.originX = zoomState.x;
    zoomState.originY = zoomState.y;

    stage.classList.add("dragging");
    stage.setPointerCapture(event.pointerId);
  });

  stage.addEventListener("pointermove", (event) => {
    if (!zoomState.dragging) return;

    zoomState.x = zoomState.originX + (event.clientX - zoomState.startX);
    zoomState.y = zoomState.originY + (event.clientY - zoomState.startY);

    applyZoom();
  });

  stage.addEventListener("pointerup", (event) => {
    zoomState.dragging = false;
    stage.classList.remove("dragging");

    try {
      stage.releasePointerCapture(event.pointerId);
    } catch (_) {}
  });

  stage.addEventListener("pointercancel", () => {
    zoomState.dragging = false;
    stage.classList.remove("dragging");
  });

  stage.addEventListener("pointerleave", () => {
    zoomState.dragging = false;
    stage.classList.remove("dragging");
  });

  stage.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
      zoomAtCenter(factor);
    },
    { passive: false }
  );
}

function setupEvents() {
  datasetSelect.addEventListener("change", () => {
    selectedProductKey = datasetSelect.value;

    const dates = sortedDates();
    selectedDate =
      dates.find((d) => isAvailable(d, selectedProductKey)) ||
      selectedDate ||
      dates[dates.length - 1];

    dateSelect.value = selectedDate;
    updateSnapshot();
  });

  dateSelect.addEventListener("change", () => {
    selectedDate = dateSelect.value;
    updateSnapshot();
  });
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function init() {
  try {
    [manifest, products] = await Promise.all([loadJson(MANIFEST_URL), loadJson(PRODUCTS_URL)]);

    setLastUpdated();
    populateSelectors();
    renderAvailabilityTable();
    renderProductsTable();
    renderRouteMap();
    setupZoomControls();
    setupEvents();
    updateSnapshot();
  } catch (error) {
    console.error(error);
    snapshotCaption.textContent = `Dashboard data could not be loaded: ${error.message}`;
  }
}

init();
