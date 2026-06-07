const MANIFEST_URL = "data/manifest.json";
const PRODUCTS_URL = "data/products.json";

const PANEL_DEFAULTS = [
  "WAVES",
  "MODEL_CURRENT",
  "SAT_SLA",
  "WIND_STRESS",
  "EKMAN_PUMPING",
  "SAT_CHL",
  "MODEL_SAL",
  "MODEL_TEMP",
  "MODEL_CURRENT",
  "SAT_SLA"
];

let manifest = null;
let products = [];
let panelStates = [];

const availabilityTable = document.getElementById("availability-table");
const productsTable = document.getElementById("products-table");
const lastUpdated = document.getElementById("last-updated");

async function loadJson(url) {
  const response = await fetch(`${url}?v=${Date.now()}`);

  if (!response.ok) {
    throw new Error(`Could not load ${url}`);
  }

  return response.json();
}

function sortedDates() {
  return [...(manifest?.dates || [])].sort((a, b) => new Date(a) - new Date(b));
}

function productByKey(productKey) {
  return products.find((product) => product.key === productKey);
}

function statusFor(date, productKey) {
  return manifest?.status?.[date]?.[productKey] || null;
}

function isAvailable(date, productKey) {
  return Boolean(statusFor(date, productKey)?.available);
}

function sourceDateLabel(date, productKey) {
  const status = statusFor(date, productKey);

  if (!status?.source_date || status.source_date === date) {
    return "";
  }

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

function initialisePanelStates() {
  const dates = sortedDates();
  const latestDate = dates[dates.length - 1];
  const enabledProducts = products.filter((product) => product.workflow_enabled !== false);

  panelStates = [...document.querySelectorAll(".map-panel")].map((panel, index) => {
    const preferredKey = PANEL_DEFAULTS[index];

    const productKey =
      enabledProducts.find((product) => product.key === preferredKey)?.key ||
      enabledProducts[index]?.key ||
      enabledProducts[0]?.key ||
      "";

    const date =
      [...dates].reverse().find((day) => isAvailable(day, productKey)) ||
      latestDate ||
      "";

    return {
      panel,
      productKey,
      date,
      zoom: {
        scale: 1,
        x: 0,
        y: 0,
        dragging: false,
        startX: 0,
        startY: 0,
        originX: 0,
        originY: 0
      }
    };
  });
}

function populatePanelSelectors() {
  const dates = sortedDates();
  const enabledProducts = products.filter((product) => product.workflow_enabled !== false);

  panelStates.forEach((state) => {
    const datasetSelect = state.panel.querySelector(".panel-dataset-select");
    const dateSelect = state.panel.querySelector(".panel-date-select");

    datasetSelect.innerHTML = "";
    dateSelect.innerHTML = "";

    enabledProducts.forEach((product) => {
      const option = document.createElement("option");

      option.value = product.key;
      option.textContent = product.label || product.key;

      datasetSelect.appendChild(option);
    });

    dates.forEach((date) => {
      const option = document.createElement("option");

      option.value = date;
      option.textContent = date;

      dateSelect.appendChild(option);
    });

    datasetSelect.value = state.productKey;
    dateSelect.value = state.date;

    datasetSelect.addEventListener("change", () => {
      state.productKey = datasetSelect.value;

      const bestDate =
        [...dates].reverse().find((date) => isAvailable(date, state.productKey)) ||
        state.date ||
        dates[dates.length - 1] ||
        "";

      state.date = bestDate;
      dateSelect.value = bestDate;

      updatePanel(state);
    });

    dateSelect.addEventListener("change", () => {
      state.date = dateSelect.value;
      updatePanel(state);
    });
  });
}

function panelSnapshotPath(state, status) {
  const panelIndex = Number(state.panel.dataset.panel);

  const normalPath = status.path;
  const regionalPath = `assets/snapshots/${state.date}_${state.productKey}_REGIONAL.png`;
  const zoomPath =
  `assets/snapshots/${state.date}_${state.productKey}_ZOOM.png`;

const equatorialPath =
  `assets/snapshots/${state.date}_${state.productKey}_EQUATORIAL.png`;

if (panelIndex === 8) {
  return {
    primary: zoomPath,
    fallback: normalPath
  };
}

if (panelIndex === 9) {
  return {
    primary: equatorialPath,
    fallback: zoomPath
  };
}

  if (panelIndex >= 6) {
    return {
      primary: regionalPath,
      fallback: normalPath
    };
  }

  return {
    primary: normalPath,
    fallback: null
  };
}

function updatePanel(state) {
  const image = state.panel.querySelector(".panel-image");
  const caption = state.panel.querySelector(".panel-caption");

  const status = statusFor(state.date, state.productKey);
  const product = productByKey(state.productKey);

  const label = product?.label || state.productKey || "Dataset";

  resetPanelZoom(state);

  if (status?.available && status.path) {
    const version = manifest.generated_at || Date.now();
    const paths = panelSnapshotPath(state, status);

    image.onerror = null;
    image.src = `${paths.primary}?v=${version}`;

    if (paths.fallback) {
      image.onerror = () => {
        image.onerror = null;
        image.src = `${paths.fallback}?v=${version}`;
      };
    }

    image.alt = `${label} for ${state.date}`;

    caption.textContent = `${label} | shown for ${state.date}${sourceDateLabel(
      state.date,
      state.productKey
    )}`;
  } else {
    image.removeAttribute("src");
    image.alt = "No snapshot available";

    caption.textContent = `${label} | no snapshot available for ${
      state.date || "selected date"
    }`;
  }
}

function updateAllPanels() {
  panelStates.forEach(updatePanel);
}

function resetPanelZoom(state) {
  state.zoom.scale = 1;
  state.zoom.x = 0;
  state.zoom.y = 0;
  state.zoom.dragging = false;

  const stage = state.panel.querySelector(".zoom-stage");

  stage?.classList.remove("is-zoomed", "dragging");

  applyPanelZoom(state);
}

function applyPanelZoom(state) {
  const image = state.panel.querySelector(".panel-image");

  image.style.transform = `translate(${state.zoom.x}px, ${state.zoom.y}px) scale(${state.zoom.scale})`;
}

function zoomPanelAtCenter(state, factor) {
  state.zoom.scale = Math.max(1, Math.min(state.zoom.scale * factor, 8));

  if (state.zoom.scale === 1) {
    state.zoom.x = 0;
    state.zoom.y = 0;
  }

  applyPanelZoom(state);
}

function setupPanelZoom() {
  panelStates.forEach((state) => {
    const stage = state.panel.querySelector(".zoom-stage");

    state.panel.querySelectorAll("[data-panel-zoom]").forEach((button) => {
      button.addEventListener("click", () => {
        const action = button.dataset.panelZoom;

        if (action === "in") {
          zoomPanelAtCenter(state, 1.35);
        }

        if (action === "out") {
          zoomPanelAtCenter(state, 1 / 1.35);
        }

        if (action === "reset") {
          resetPanelZoom(state);
        }

        stage.classList.toggle("is-zoomed", state.zoom.scale > 1);
      });
    });

    stage.addEventListener("pointerdown", (event) => {
      if (state.zoom.scale <= 1) {
        return;
      }

      state.zoom.dragging = true;
      state.zoom.startX = event.clientX;
      state.zoom.startY = event.clientY;
      state.zoom.originX = state.zoom.x;
      state.zoom.originY = state.zoom.y;

      stage.classList.add("dragging");
      stage.setPointerCapture(event.pointerId);
    });

    stage.addEventListener("pointermove", (event) => {
      if (!state.zoom.dragging) {
        return;
      }

      state.zoom.x = state.zoom.originX + (event.clientX - state.zoom.startX);
      state.zoom.y = state.zoom.originY + (event.clientY - state.zoom.startY);

      applyPanelZoom(state);
    });

    stage.addEventListener("pointerup", (event) => {
      state.zoom.dragging = false;
      stage.classList.remove("dragging");

      try {
        stage.releasePointerCapture(event.pointerId);
      } catch (_) {}
    });

    stage.addEventListener("pointercancel", () => {
      state.zoom.dragging = false;
      stage.classList.remove("dragging");
    });
  });
}

function renderAvailabilityTable() {
  if (!availabilityTable) {
    return;
  }

  const dates = sortedDates();

  let html = "<thead><tr><th>Product</th>";

  dates.forEach((date) => {
    html += `<th>${date}</th>`;
  });

  html += "</tr></thead><tbody>";

  products.forEach((product) => {
    const planned = product.workflow_enabled === false;

    html += `<tr data-product="${product.key}" class="${planned ? "planned-row" : ""}">`;
    html += `<th>${product.label || product.key}<small>${product.key}</small></th>`;

    dates.forEach((date) => {
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
        html += `<td title="${escapeHtml(status.error)}">
          <span class="status failed">×</span>
        </td>`;
      } else {
        html += `<td><span class="status missing">—</span></td>`;
      }
    });

    html += "</tr>";
  });

  html += "</tbody>";

  availabilityTable.innerHTML = html;

  availabilityTable.querySelectorAll("button.status.available").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = panelStates[0];

      panel.productKey = button.dataset.product;
      panel.date = button.dataset.date;

      const datasetSelect = panel.panel.querySelector(".panel-dataset-select");
      const dateSelect = panel.panel.querySelector(".panel-date-select");

      datasetSelect.value = panel.productKey;
      dateSelect.value = panel.date;

      updatePanel(panel);
    });
  });
}

function renderProductsTable() {
  if (!productsTable) {
    return;
  }

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

  products.forEach((product) => {
    const statusText =
      product.workflow_enabled === false ? "planned" : product.status || "automated";

    const productUrl = product.product_url
      ? `<a href="${product.product_url}" target="_blank" rel="noopener">Official page</a>`
      : "";

    html += `
      <tr>
        <td>
          <strong>${product.label || product.key}</strong>
          <small>${product.key}</small>
        </td>
        <td>${product.category || "Not specified"}</td>
        <td>${statusText}</td>
        <td><code>${product.dataset_id || "derived"}</code></td>
        <td>${(product.variables || []).map((variable) => `<code>${variable}</code>`).join(" ")}</td>
        <td>${productUrl}</td>
      </tr>
    `;
  });

  html += "</tbody>";

  productsTable.innerHTML = html;
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
    [manifest, products] = await Promise.all([
      loadJson(MANIFEST_URL),
      loadJson(PRODUCTS_URL)
    ]);

    setLastUpdated();
    initialisePanelStates();
    populatePanelSelectors();
    setupPanelZoom();
    updateAllPanels();
    renderAvailabilityTable();
    renderProductsTable();
  } catch (error) {
    console.error(error);

    document.querySelectorAll(".panel-caption").forEach((caption) => {
      caption.textContent = `Dashboard data could not be loaded: ${error.message}`;
    });
  }
}

init();
