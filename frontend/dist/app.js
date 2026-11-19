/**
 * EVolve - Front-End Application Engine
 * Pure Vanilla TypeScript/JavaScript for maximum speed, offline reliability, and zero build tool friction.
 */

const API_BASE = "/api";

// Global Application State
const state = {
  activePage: "overview",
  profiles: [],
  activeProfile: null,
  dataSourceLabel: "Synthetic Demo Data",
  charging: {
    sessions: [],
    selectedSessionId: null,
    readings: [],
    analysisResult: null,
    timeEstimateResult: null
  },
  range: {
    result: null,
    tripsRegression: null
  },
  trip: {
    result: null
  },
  health: {
    measurements: [],
    result: null
  },
  methodsLab: {
    category: "integration", // 'integration', 'interpolation', 'root_finding', 'regression'
    result: null
  },
  history: []
};

// API Client Helper
async function apiCall(endpoint, method = "GET", body = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" }
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const res = await fetch(`${API_BASE}${endpoint}`, options);
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || "API request failed");
  }
  return res.json();
}

// Show temporary notification
function showNotification(message, type = "info") {
  const container = document.getElementById("notification-container");
  if (!container) return;
  const div = document.createElement("div");
  div.className = `banner banner-${type}`;
  div.style.marginBottom = "8px";
  div.style.boxShadow = "0 2px 8px rgba(0,0,0,0.1)";
  div.innerHTML = `<span>${type === 'danger' ? '⚠️' : 'ℹ️'} ${message}</span>`;
  container.appendChild(div);
  setTimeout(() => {
    div.remove();
  }, 4000);
}

// Router Navigation
function navigateTo(pageId) {
  state.activePage = pageId;
  document.querySelectorAll(".nav-link").forEach(el => {
    el.classList.toggle("active", el.dataset.page === pageId);
  });
  renderCurrentPage();
}

// --- Initial Data Load ---
async function initializeApp() {
  try {
    const profs = await apiCall("/profiles");
    state.profiles = profs;
    if (profs.length > 0) {
      state.activeProfile = profs[0];
      updateHeaderProfile();
    }
    // Load charging sessions
    const sessions = await apiCall("/charging/sessions");
    state.charging.sessions = sessions;
    if (sessions.length > 0) {
      state.charging.selectedSessionId = sessions[0].id;
      state.charging.readings = sessions[0].readings || [];
    }
    // Load capacity measurements
    const capList = await apiCall("/health/measurements");
    state.health.measurements = capList;

    renderCurrentPage();
  } catch (err) {
    console.error("Initialization error:", err);
    showNotification("Failed to load initial data. Is FastAPI backend running?", "danger");
  }
}

function updateHeaderProfile() {
  const el = document.getElementById("header-profile-name");
  if (el && state.activeProfile) {
    el.innerText = `${state.activeProfile.name} (${state.activeProfile.usable_capacity_kwh} kWh)`;
  }
  const badgeEl = document.getElementById("header-data-source");
  if (badgeEl) {
    badgeEl.innerText = state.dataSourceLabel;
  }
}

// --- SVG Charting Utility ---
function generateSVGLineChart(dataPoints, xKey, yKey, title, xLabel, yLabel, options = {}) {
  if (!dataPoints || dataPoints.length === 0) {
    return `<div style="text-align:center; padding: 40px; color:#94a3b8;">No data available for chart</div>`;
  }

  const width = options.width || 560;
  const height = options.height || 240;
  const pad = { top: 30, right: 30, bottom: 40, left: 55 };

  const xs = dataPoints.map(d => Number(d[xKey]));
  const ys = dataPoints.map(d => Number(d[yKey]));

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs) || (minX + 1);
  const minY = Math.min(0, Math.min(...ys));
  const maxY = Math.max(...ys) * 1.1 || 10;

  const scaleX = x => pad.left + ((x - minX) / (maxX - minX)) * (width - pad.left - pad.right);
  const scaleY = y => height - pad.bottom - ((y - minY) / (maxY - minY)) * (height - pad.top - pad.bottom);

  // Path coordinates
  const pathD = dataPoints.map((d, i) => {
    const px = scaleX(Number(d[xKey]));
    const py = scaleY(Number(d[yKey]));
    return `${i === 0 ? 'M' : 'L'} ${px.toFixed(1)} ${py.toFixed(1)}`;
  }).join(" ");

  // Points circles
  const circles = dataPoints.map(d => {
    const px = scaleX(Number(d[xKey]));
    const py = scaleY(Number(d[yKey]));
    const isEst = d.is_estimated;
    return `<circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="${isEst ? 5 : 4}" 
              fill="${isEst ? '#d97706' : (options.color || '#2563eb')}" 
              stroke="#ffffff" stroke-width="2">
              <title>${xLabel}: ${d[xKey]}, ${yLabel}: ${d[yKey]}${isEst ? ' (Estimated)' : ''}</title>
            </circle>`;
  }).join("");

  return `
    <div style="font-weight:600; font-size:0.85rem; color:#334155; margin-bottom:4px;">${title}</div>
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}">
      <!-- Grid lines -->
      <line x1="${pad.left}" y1="${scaleY(minY)}" x2="${width - pad.right}" y2="${scaleY(minY)}" stroke="#cbd5e1" stroke-width="1"/>
      <line x1="${pad.left}" y1="${scaleY(maxY * 0.5)}" x2="${width - pad.right}" y2="${scaleY(maxY * 0.5)}" stroke="#f1f5f9" stroke-dasharray="4"/>
      <line x1="${pad.left}" y1="${pad.top}" x2="${width - pad.right}" y2="${pad.top}" stroke="#f1f5f9" stroke-dasharray="4"/>
      <line x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${height - pad.bottom}" stroke="#cbd5e1" stroke-width="1"/>
      
      <!-- Axis Labels -->
      <text x="${pad.left}" y="${pad.top - 10}" font-size="10" fill="#64748b" text-anchor="middle">${yLabel}</text>
      <text x="${width - pad.right}" y="${height - 10}" font-size="10" fill="#64748b" text-anchor="end">${xLabel}</text>
      
      <!-- Values on axis -->
      <text x="${pad.left - 6}" y="${scaleY(minY) + 3}" font-size="10" fill="#94a3b8" text-anchor="end">${minY.toFixed(0)}</text>
      <text x="${pad.left - 6}" y="${scaleY(maxY * 0.5) + 3}" font-size="10" fill="#94a3b8" text-anchor="end">${(maxY * 0.5).toFixed(0)}</text>
      <text x="${pad.left - 6}" y="${scaleY(maxY) + 3}" font-size="10" fill="#94a3b8" text-anchor="end">${maxY.toFixed(0)}</text>
      
      <!-- Area fill -->
      <path d="${pathD} L ${scaleX(maxX)} ${scaleY(minY)} L ${scaleX(minX)} ${scaleY(minY)} Z" fill="${options.color || '#2563eb'}" fill-opacity="0.08"/>
      
      <!-- Main Line -->
      <path d="${pathD}" fill="none" stroke="${options.color || '#2563eb'}" stroke-width="2.5" stroke-linejoin="round"/>
      
      <!-- Circles -->
      ${circles}
    </svg>
  `;
}

// --- Page Renderers ---

function renderCurrentPage() {
  const container = document.getElementById("main-content");
  if (!container) return;

  switch (state.activePage) {
    case "overview":
      renderOverview(container);
      break;
    case "charging":
      renderChargingAnalysis(container);
      break;
    case "range":
      renderRangePrediction(container);
      break;
    case "trips":
      renderTripSimulator(container);
      break;
    case "health":
      renderBatteryHealth(container);
      break;
    case "methods":
      renderMethodsLab(container);
      break;
    case "data":
      renderDataHistory(container);
      break;
    case "about":
      renderAboutProject(container);
      break;
    default:
      renderOverview(container);
  }
}

// 1. OVERVIEW PAGE
function renderOverview(container) {
  const prof = state.activeProfile || { name: "Demo Vehicle", usable_capacity_kwh: 60.0, current_soc: 50.0 };
  const availEnergy = (prof.usable_capacity_kwh * (prof.current_soc / 100.0)).toFixed(1);

  container.innerHTML = `
    <div class="banner banner-info">
      <div>
        <strong>Computational Analytics System Active</strong>: Working on 
        <span class="badge badge-demo">${state.dataSourceLabel}</span>. 
        All numerical integration, interpolation, regression, and root-finding operations run transparently with mathematical step-by-step logs.
      </div>
    </div>

    <div class="grid-4">
      <div class="metric-box">
        <div class="metric-label">Active Vehicle</div>
        <div class="metric-value" style="font-size:1.15rem; font-weight:600; margin-top:8px;">${prof.name}</div>
        <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">Nominal: ${prof.nominal_capacity_kwh || 64} kWh</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Usable Capacity (Cu)</div>
        <div class="metric-value">${prof.usable_capacity_kwh}<span class="metric-unit">kWh</span></div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Current Battery SoC</div>
        <div class="metric-value">${prof.current_soc}<span class="metric-unit">%</span></div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Available Battery Energy</div>
        <div class="metric-value">${availEnergy}<span class="metric-unit">kWh</span></div>
      </div>
    </div>

    <div class="grid-2" style="margin-top:20px;">
      <div class="card">
        <div class="card-title">
          <span>Active Analytical Modules</span>
          <span class="badge badge-profile">v1.0.0</span>
        </div>
        <div class="card-subtitle">Select a dedicated workspace from the sidebar or click below:</div>
        <div style="display:flex; flex-direction:column; gap:10px;">
          <a class="btn btn-secondary" onclick="navigateTo('charging')" style="justify-content:flex-start;">
            ⚡ <strong>Charging Analysis</strong>: Trapezoidal & Simpson 1/3 energy integration, sensor interpolation
          </a>
          <a class="btn btn-secondary" onclick="navigateTo('range')" style="justify-content:flex-start;">
            🛣️ <strong>Range Prediction</strong>: Least squares linear regression on trip consumption
          </a>
          <a class="btn btn-secondary" onclick="navigateTo('trips')" style="justify-content:flex-start;">
            🧭 <strong>Trip Simulator</strong>: Feasibility verification & Bisection/Newton root-finding
          </a>
          <a class="btn btn-secondary" onclick="navigateTo('health')" style="justify-content:flex-start;">
            🔋 <strong>Battery Health (SOH)</strong>: Degradation tracking, capacity loss calculation
          </a>
          <a class="btn btn-secondary" onclick="navigateTo('methods')" style="justify-content:flex-start;">
            🔬 <strong>Methods Lab</strong>: Academic derivations, algorithm comparison & error metrics
          </a>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Vehicle Profile Configuration</div>
        <div class="card-subtitle">Edit current vehicle specifications used across all mathematical engines:</div>
        <form id="profile-edit-form" onsubmit="handleSaveProfile(event)">
          <div class="form-group">
            <label class="form-label">Profile / Vehicle Name</label>
            <input type="text" id="prof-name" class="form-control" value="${prof.name}" required />
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Nominal Capacity (kWh)</label>
              <input type="number" step="0.1" id="prof-nom" class="form-control" value="${prof.nominal_capacity_kwh || 64.0}" required />
            </div>
            <div class="form-group">
              <label class="form-label">Usable Capacity Cu (kWh)</label>
              <input type="number" step="0.1" id="prof-use" class="form-control" value="${prof.usable_capacity_kwh}" required />
            </div>
          </div>
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">Current Battery SoC (%)</label>
              <input type="number" min="0" max="100" step="0.5" id="prof-soc" class="form-control" value="${prof.current_soc}" required />
            </div>
            <div class="form-group">
              <label class="form-label">Original Capacity (kWh)</label>
              <input type="number" step="0.1" id="prof-orig" class="form-control" value="${prof.original_usable_capacity_kwh || prof.usable_capacity_kwh}" required />
            </div>
          </div>
          <button type="submit" class="btn btn-primary" style="margin-top:8px;">Save Profile Changes</button>
        </form>
      </div>
    </div>
  `;
}

async function handleSaveProfile(e) {
  e.preventDefault();
  if (!state.activeProfile) return;
  const updated = {
    name: document.getElementById("prof-name").value,
    nominal_capacity_kwh: parseFloat(document.getElementById("prof-nom").value),
    usable_capacity_kwh: parseFloat(document.getElementById("prof-use").value),
    current_soc: parseFloat(document.getElementById("prof-soc").value),
    original_usable_capacity_kwh: parseFloat(document.getElementById("prof-orig").value)
  };

  try {
    const res = await apiCall(`/profiles/${state.activeProfile.id}`, "PUT", updated);
    state.activeProfile = res;
    updateHeaderProfile();
    showNotification("Vehicle profile updated successfully!", "success");
    renderOverview(document.getElementById("main-content"));
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

// 2. CHARGING ANALYSIS PAGE
function renderChargingAnalysis(container) {
  const sessions = state.charging.sessions || [];
  const currSessionId = state.charging.selectedSessionId;
  const readings = state.charging.readings || [];

  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
      <div>
        <h2 style="font-size:1.15rem; font-weight:700;">Charging Session Analysis</h2>
        <p style="font-size:0.82rem; color:#64748b;">Numerical integration of charging power, sensor interpolation & target time estimation.</p>
      </div>
      <div style="display:flex; gap:10px;">
        <select class="form-control" style="width:280px;" onchange="handleSelectChargingSession(this.value)">
          ${sessions.map(s => `<option value="${s.id}" ${s.id == currSessionId ? 'selected' : ''}>${s.session_name}</option>`).join("")}
        </select>
        <button class="btn btn-secondary" onclick="handleInterpolateMissing()">Fill Missing (Interpolation)</button>
        <button class="btn btn-primary" onclick="handleRunChargingAnalysis()">Run Integration</button>
      </div>
    </div>

    <div class="grid-2">
      <!-- Readings Table Card -->
      <div class="card">
        <div class="card-title">
          <span>Charging Readings Telemetry</span>
          <span style="font-size:0.75rem; font-weight:400; color:#64748b;">${readings.length} records</span>
        </div>
        <div class="table-responsive" style="max-height: 280px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Elapsed (min)</th>
                <th>Battery SoC (%)</th>
                <th>Power (kW)</th>
                <th>Meter (kWh)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${readings.map(r => `
                <tr>
                  <td>${r.elapsed_minutes}</td>
                  <td>${r.soc_percent !== null && r.soc_percent !== undefined ? r.soc_percent.toFixed(1) + '%' : '<span style="color:#d97706; font-weight:600;">[MISSING]</span>'}</td>
                  <td>${r.power_kw !== null && r.power_kw !== undefined ? r.power_kw.toFixed(1) + ' kW' : '<span style="color:#94a3b8;">--</span>'}</td>
                  <td>${r.cumulative_energy_kwh !== null && r.cumulative_energy_kwh !== undefined ? r.cumulative_energy_kwh.toFixed(2) : '--'}</td>
                  <td>${r.is_estimated ? '<span class="tag-estimated">ESTIMATED</span>' : '<span style="color:#64748b; font-size:0.75rem;">MEASURED</span>'}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        <div style="margin-top:12px; font-size:0.78rem; color:#64748b;">
          💡 Missing sensor values can be populated using Linear or Newton Divided-Difference interpolation.
        </div>
      </div>

      <!-- Charts Card -->
      <div class="card">
        <div class="card-title">Charging Curves (Power & SoC vs Time)</div>
        <div id="charging-chart-container">
          ${readings.filter(r => r.soc_percent !== null).length >= 2 
            ? generateSVGLineChart(readings.filter(r => r.soc_percent !== null), "elapsed_minutes", "soc_percent", "State of Charge (%) vs Time (min)", "Time (min)", "SoC (%)", { color: "#2563eb" })
            : `<div style="text-align:center; padding:50px; color:#94a3b8;">Click 'Run Integration' or select a session to view charging curve</div>`
          }
        </div>
      </div>
    </div>

    <!-- Numerical Integration Output -->
    <div id="charging-analysis-results">
      ${state.charging.analysisResult ? renderChargingResultsView(state.charging.analysisResult) : ''}
    </div>

    <!-- Charging Time Estimation Card -->
    <div class="card" style="margin-top:20px;">
      <div class="card-title">Charging Time Estimation (Target SoC)</div>
      <div class="card-subtitle">Compares simplified constant-power baseline with variable-power taper curve numerical integration:</div>
      <div class="grid-3">
        <div class="form-group">
          <label class="form-label">Current Battery SoC (%)</label>
          <input type="number" id="time-current-soc" class="form-control" value="${state.activeProfile ? state.activeProfile.current_soc : 20}" />
        </div>
        <div class="form-group">
          <label class="form-label">Target Battery SoC (%)</label>
          <input type="number" id="time-target-soc" class="form-control" value="80" />
        </div>
        <div class="form-group">
          <label class="form-label">Charger Rating / Constant Power (kW)</label>
          <input type="number" id="time-power-kw" class="form-control" value="11" />
        </div>
      </div>
      <button class="btn btn-secondary" onclick="handleEstimateChargingTime()">Calculate Estimated Time</button>
      <div id="charging-time-result-area" style="margin-top:14px;">
        ${state.charging.timeEstimateResult ? renderChargingTimeResultView(state.charging.timeEstimateResult) : ''}
      </div>
    </div>
  `;
}

function handleSelectChargingSession(sessId) {
  state.charging.selectedSessionId = Number(sessId);
  const found = state.charging.sessions.find(s => s.id == sessId);
  if (found) {
    state.charging.readings = found.readings || [];
    state.charging.analysisResult = null;
    renderChargingAnalysis(document.getElementById("main-content"));
  }
}

async function handleInterpolateMissing() {
  const readings = state.charging.readings;
  if (!readings || readings.length < 2) {
    showNotification("At least 2 readings required to interpolate.", "danger");
    return;
  }
  try {
    const res = await apiCall("/charging/interpolate", "POST", {
      readings: readings,
      method: "linear",
      max_gap_minutes: 30.0
    });
    state.charging.readings = res.readings;
    showNotification(`Interpolation complete: Filled ${res.estimated_count} missing reading(s).`, "success");
    renderChargingAnalysis(document.getElementById("main-content"));
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

async function handleRunChargingAnalysis() {
  const readings = state.charging.readings;
  if (!readings || readings.length < 2) {
    showNotification("At least 2 readings required for numerical integration.", "danger");
    return;
  }
  try {
    const lastReading = readings[readings.length - 1];
    const meterVal = lastReading && lastReading.cumulative_energy_kwh ? lastReading.cumulative_energy_kwh : null;
    const url = meterVal ? `/charging/analyze?method=trapezoidal&meter_reading_kwh=${meterVal}` : `/charging/analyze?method=trapezoidal`;
    const res = await apiCall(url, "POST", readings);
    state.charging.analysisResult = res;
    renderChargingAnalysis(document.getElementById("main-content"));
    showNotification("Charging numerical integration executed successfully!", "success");
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

async function handleEstimateChargingTime() {
  const currSoc = parseFloat(document.getElementById("time-current-soc").value);
  const targetSoc = parseFloat(document.getElementById("time-target-soc").value);
  const pKw = parseFloat(document.getElementById("time-power-kw").value);
  const cu = state.activeProfile ? state.activeProfile.usable_capacity_kwh : 60.0;

  // Build observed taper curve from current session if available
  const pairs = [];
  for (const r of state.charging.readings) {
    if (r.soc_percent !== null && r.power_kw !== null) {
      pairs.push([r.soc_percent, r.power_kw]);
    }
  }

  try {
    const res = await apiCall("/charging/time-estimate", "POST", {
      usable_capacity_kwh: cu,
      current_soc: currSoc,
      target_soc: targetSoc,
      constant_power_kw: pKw,
      observed_soc_power_pairs: pairs.length >= 2 ? pairs : null
    });
    state.charging.timeEstimateResult = res;
    const area = document.getElementById("charging-time-result-area");
    if (area) {
      area.innerHTML = renderChargingTimeResultView(res);
    }
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

function renderChargingResultsView(res) {
  const eng = res.energy_calculation || {};
  const comp = res.integration_comparison || {};
  const meterErr = res.meter_comparison;

  return `
    <div class="card">
      <div class="card-title">
        <span>Numerical Integration Findings & Energy Calculation</span>
        <span class="badge badge-demo">${eng.method || 'Trapezoidal Rule'}</span>
      </div>
      
      <div class="grid-4">
        <div class="metric-box">
          <div class="metric-label">Delivered Energy</div>
          <div class="metric-value">${eng.total_energy_kwh ? eng.total_energy_kwh.toFixed(3) : '--'}<span class="metric-unit">kWh</span></div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Duration</div>
          <div class="metric-value">${eng.total_time_minutes ? eng.total_time_minutes.toFixed(0) : '--'}<span class="metric-unit">min</span></div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Average Charging Power</div>
          <div class="metric-value">${eng.average_power_kw ? eng.average_power_kw.toFixed(1) : '--'}<span class="metric-unit">kW</span></div>
        </div>
        <div class="metric-box">
          <div class="metric-label">SoC Charging Rate</div>
          <div class="metric-value">${res.average_soc_rate_per_hour ? res.average_soc_rate_per_hour.toFixed(1) : '--'}<span class="metric-unit">%/hr</span></div>
        </div>
      </div>

      ${meterErr ? `
        <div class="banner banner-info" style="margin-top:14px;">
          <div>
            <strong>Physical Meter Comparison:</strong> Charger meter recorded <strong>${meterErr.actual.toFixed(2)} kWh</strong> vs 
            integrated numerical energy <strong>${meterErr.predicted.toFixed(2)} kWh</strong>. 
            Absolute Error: <strong>${meterErr.absolute_error.toFixed(4)} kWh</strong> (${meterErr.percentage_error_display}).
          </div>
        </div>
      ` : ''}

      ${comp.simpson_eligible ? `
        <div class="banner banner-success" style="margin-top:10px;">
          <div>
            <strong>Method Comparison Available:</strong> Dataset is uniformly spaced. 
            Trapezoidal: <strong>${comp.trapezoidal.total_energy_kwh.toFixed(4)} kWh</strong> | 
            Simpson's 1/3: <strong>${comp.simpsons.total_energy_kwh.toFixed(4)} kWh</strong> 
            (Diff: ${comp.absolute_difference_kwh.toFixed(6)} kWh / ${comp.percentage_difference.toFixed(4)}%).
          </div>
        </div>
      ` : `
        <div class="banner banner-warning" style="margin-top:10px;">
          <div>
            <strong>Simpson's 1/3 Rule Status:</strong> Ineligible on this dataset (${comp.simpson_ineligibility_reason || 'non-uniform intervals'}). 
            Trapezoidal Rule applied safely as the general integration method.
          </div>
        </div>
      `}

      <!-- Worked Steps Preview -->
      <div class="steps-container">
        <div style="font-weight:600; font-size:0.82rem; margin-bottom:8px; color:#475569;">MATHEMATICAL DERIVATION & INTERVAL STRIPS:</div>
        <div class="formula-block">${eng.formula || 'E = sum( (P_i + P_{i+1})/2 * Delta t )'}</div>
        ${(eng.steps || []).map(s => `<div class="step-row">${s}</div>`).join("")}
      </div>
    </div>
  `;
}

function renderChargingTimeResultView(res) {
  const cEst = res.constant_power_estimate;
  const vEst = res.variable_power_estimate;

  return `
    <div class="grid-2">
      ${cEst ? `
        <div class="metric-box">
          <div class="metric-label">Constant-Power Baseline</div>
          <div class="metric-value" style="color:#2563eb;">${cEst.formatted_time}</div>
          <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">${cEst.energy_needed_kwh} kWh needed at constant ${cEst.assumed_power_kw} kW</div>
          <div style="font-size:0.72rem; color:#94a3b8; margin-top:4px;">${cEst.assumptions_warning}</div>
        </div>
      ` : ''}

      ${vEst ? `
        <div class="metric-box">
          <div class="metric-label">Variable Taper Integration</div>
          <div class="metric-value" style="color:#059669;">${vEst.formatted_time}</div>
          <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">${vEst.explanation}</div>
          <div style="font-size:0.72rem; color:#059669; margin-top:4px; font-weight:600;">Includes battery taper above 80% SoC</div>
        </div>
      ` : `
        <div class="metric-box">
          <div class="metric-label">Variable Power Taper Model</div>
          <div style="font-size:0.82rem; color:#64748b; margin-top:8px;">Load a variable-power session (e.g. DC Fast Charge) to evaluate variable curve numerical integration.</div>
        </div>
      `}
    </div>
  `;
}

// 3. RANGE PREDICTION PAGE
function renderRangePrediction(container) {
  const prof = state.activeProfile || { usable_capacity_kwh: 60.0, current_soc: 50.0 };

  container.innerHTML = `
    <div style="margin-bottom:16px;">
      <h2 style="font-size:1.15rem; font-weight:700;">Driving Consumption & Range Prediction</h2>
      <p style="font-size:0.82rem; color:#64748b;">Computes remaining driving distance using usable energy and historical least-squares linear regression.</p>
    </div>

    <div class="grid-2">
      <!-- Controls Card -->
      <div class="card">
        <div class="card-title">Prediction Parameters</div>
        <div class="form-group">
          <label class="form-label">Usable Battery Capacity (kWh)</label>
          <input type="number" id="range-cu" class="form-control" value="${prof.usable_capacity_kwh}" />
        </div>
        <div class="form-group">
          <label class="form-label">Current Battery SoC (%)</label>
          <input type="number" id="range-soc" class="form-control" value="${prof.current_soc}" />
        </div>
        <div class="form-group">
          <label class="form-label">Direct Consumption Rate (kWh/km) [Optional]</label>
          <input type="number" step="0.001" id="range-rate" class="form-control" value="0.185" />
          <span style="font-size:0.72rem; color:#64748b;">0.185 kWh/km corresponds to 18.5 kWh/100 km</span>
        </div>
        <div class="form-group" style="margin-top:12px;">
          <label style="display:flex; align-items:center; gap:8px; font-size:0.85rem; cursor:pointer;">
            <input type="checkbox" id="range-use-regression" checked />
            <strong>Use Historical Trip Data Linear Regression</strong>
          </label>
          <p style="font-size:0.75rem; color:#64748b; margin-left:22px;">Derives marginal consumption slope b from logged trip observations.</p>
        </div>
        <button class="btn btn-primary" onclick="handlePredictRange()" style="margin-top:10px;">Calculate Range Prediction</button>
      </div>

      <!-- Scenarios Display -->
      <div class="card" id="range-scenarios-card">
        <div class="card-title">Operational Range Scenarios</div>
        <div class="card-subtitle">Accounts for real-world environmental and speed variances:</div>
        <div id="range-scenarios-output">
          <div style="text-align:center; padding:40px; color:#94a3b8;">Click 'Calculate Range Prediction' to generate scenarios.</div>
        </div>
      </div>
    </div>

    <!-- Regression Model Details -->
    <div id="range-regression-details"></div>
  `;
}

async function handlePredictRange() {
  const cu = parseFloat(document.getElementById("range-cu").value);
  const soc = parseFloat(document.getElementById("range-soc").value);
  const rate = parseFloat(document.getElementById("range-rate").value);
  const useReg = document.getElementById("range-use-regression").checked;

  let tripDists = [];
  let tripEnergies = [];

  if (useReg) {
    try {
      const trips = await apiCall("/trips");
      tripDists = trips.map(t => Number(t.distance_km));
      tripEnergies = trips.map(t => Number(t.energy_consumed_kwh));
    } catch (e) {
      console.warn("Could not fetch trips for regression:", e);
    }
  }

  try {
    const res = await apiCall("/range/predict", "POST", {
      usable_capacity_kwh: cu,
      current_soc_percent: soc,
      consumption_kwh_per_km: rate,
      use_trips_regression: useReg && tripDists.length >= 2,
      trip_distances_km: tripDists.length >= 2 ? tripDists : null,
      trip_energies_kwh: tripEnergies.length >= 2 ? tripEnergies : null
    });

    state.range.result = res;
    renderRangeResults(res);
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

function renderRangeResults(res) {
  const rp = res.range_prediction;
  const sc = rp.scenarios;
  const reg = res.regression_model;

  const scenEl = document.getElementById("range-scenarios-output");
  if (scenEl) {
    scenEl.innerHTML = `
      <div style="margin-bottom:14px; font-size:0.85rem;">
        Available Energy: <strong>${rp.available_energy_kwh} kWh</strong> | Effective Rate: <strong>${rp.consumption_kwh_per_100km} kWh/100km</strong>
      </div>
      <div class="grid-3">
        <div class="metric-box" style="border-left: 4px solid #ef4444;">
          <div class="metric-label">Conservative</div>
          <div class="metric-value">${sc.conservative.range_km}<span class="metric-unit">km</span></div>
          <div style="font-size:0.72rem; color:#64748b; margin-top:4px;">Highway / Winter (+15%)</div>
        </div>
        <div class="metric-box" style="border-left: 4px solid #2563eb;">
          <div class="metric-label">Expected (Nominal)</div>
          <div class="metric-value">${sc.expected.range_km}<span class="metric-unit">km</span></div>
          <div style="font-size:0.72rem; color:#64748b; margin-top:4px;">Mixed Driving Rate</div>
        </div>
        <div class="metric-box" style="border-left: 4px solid #059669;">
          <div class="metric-label">Optimistic</div>
          <div class="metric-value">${sc.optimistic.range_km}<span class="metric-unit">km</span></div>
          <div style="font-size:0.72rem; color:#64748b; margin-top:4px;">City Eco-Driving (-15%)</div>
        </div>
      </div>
      <div class="steps-container" style="margin-top:14px;">
        <div style="font-weight:600; font-size:0.8rem; margin-bottom:6px;">CALCULATION STEPS:</div>
        ${rp.steps.map(s => `<div class="step-row">${s}</div>`).join("")}
      </div>
    `;
  }

  const regEl = document.getElementById("range-regression-details");
  if (regEl && reg) {
    regEl.innerHTML = `
      <div class="card" style="margin-top:20px;">
        <div class="card-title">
          <span>Least Squares Linear Regression Model (Distance vs Energy)</span>
          <span class="badge badge-demo">R² = ${reg.r_squared}</span>
        </div>
        <div class="grid-4">
          <div class="metric-box">
            <div class="metric-label">Fitted Slope (b)</div>
            <div class="metric-value">${reg.slope_kwh_per_km}<span class="metric-unit">kWh/km</span></div>
            <div style="font-size:0.72rem; color:#64748b;">${reg.slope_kwh_per_100km} kWh/100km</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Intercept (a)</div>
            <div class="metric-value">${reg.intercept_kwh}<span class="metric-unit">kWh</span></div>
            <div style="font-size:0.72rem; color:#64748b;">Baseline auxiliary load</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Mean Absolute Error</div>
            <div class="metric-value">${reg.mae_kwh}<span class="metric-unit">kWh</span></div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Root Mean Sq Error</div>
            <div class="metric-value">${reg.rmse_kwh}<span class="metric-unit">kWh</span></div>
          </div>
        </div>
        <div class="formula-block">${reg.equation}</div>
      </div>
    `;
  }
}

// 4. TRIP SIMULATOR PAGE
function renderTripSimulator(container) {
  const prof = state.activeProfile || { usable_capacity_kwh: 60.0, current_soc: 80.0 };

  container.innerHTML = `
    <div style="margin-bottom:16px;">
      <h2 style="font-size:1.15rem; font-weight:700;">Journey Feasibility Simulator</h2>
      <p style="font-size:0.82rem; color:#64748b;">Distance-and-consumption feasibility engine with Bisection and Newton-Raphson root-finding verification.</p>
    </div>

    <div class="grid-2">
      <!-- Input Card -->
      <div class="card">
        <div class="card-title">Journey Specifications</div>
        <div class="form-group">
          <label class="form-label">Journey Distance (km)</label>
          <input type="number" id="trip-distance" class="form-control" value="180" />
        </div>
        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">Starting SoC (%)</label>
            <input type="number" id="trip-start-soc" class="form-control" value="${prof.current_soc || 80.0}" />
          </div>
          <div class="form-group">
            <label class="form-label">Arrival Reserve Target (%)</label>
            <input type="number" id="trip-reserve-soc" class="form-control" value="10.0" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Expected Consumption (kWh/km)</label>
          <input type="number" step="0.001" id="trip-rate" class="form-control" value="0.185" />
        </div>
        <button class="btn btn-primary" onclick="handleSimulateTrip()" style="margin-top:10px;">Simulate Journey</button>
      </div>

      <!-- Feasibility Result Card -->
      <div class="card" id="trip-feasibility-card">
        <div class="card-title">Feasibility Assessment</div>
        <div id="trip-result-area">
          <div style="text-align:center; padding:50px; color:#94a3b8;">Click 'Simulate Journey' to compute arrival charge and reserve adequacy.</div>
        </div>
      </div>
    </div>

    <!-- Root Finding Demo Card -->
    <div id="trip-root-finding-area"></div>
  `;
}

async function handleSimulateTrip() {
  const dist = parseFloat(document.getElementById("trip-distance").value);
  const startSoc = parseFloat(document.getElementById("trip-start-soc").value);
  const reserve = parseFloat(document.getElementById("trip-reserve-soc").value);
  const rate = parseFloat(document.getElementById("trip-rate").value);
  const cu = state.activeProfile ? state.activeProfile.usable_capacity_kwh : 60.0;

  try {
    const res = await apiCall("/trips/analyze", "POST", {
      usable_capacity_kwh: cu,
      starting_soc_percent: startSoc,
      journey_distance_km: dist,
      consumption_rate_kwh_per_km: rate,
      desired_reserve_percent: reserve
    });

    state.trip.result = res;
    renderTripResults(res);
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

function renderTripResults(res) {
  const area = document.getElementById("trip-result-area");
  if (!area) return;

  const isFeas = res.is_feasible;
  const statusBannerClass = isFeas ? "banner-success" : (res.arrival_soc_percent < 0 ? "banner-warning" : "banner-info");

  area.innerHTML = `
    <div class="banner ${statusBannerClass}">
      <div>
        <strong>${isFeas ? '✅ TRIP FEASIBLE' : '⚠️ FEASIBILITY WARNING'}:</strong> ${res.message}
      </div>
    </div>

    <div class="grid-3" style="margin-top:14px;">
      <div class="metric-box">
        <div class="metric-label">Energy Required</div>
        <div class="metric-value">${res.energy_required_kwh}<span class="metric-unit">kWh</span></div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Charge Consumed</div>
        <div class="metric-value">${res.soc_consumed_percent}<span class="metric-unit">%</span></div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Arrival SoC</div>
        <div class="metric-value" style="color:${isFeas ? '#059669' : '#e11d48'};">${res.arrival_soc_percent}<span class="metric-unit">%</span></div>
      </div>
    </div>

    <div style="margin-top:14px; font-size:0.84rem; color:#475569;">
      Minimum starting battery charge required to preserve ${res.desired_reserve_percent}% arrival reserve: 
      <strong>${res.min_starting_soc_percent}%</strong>.
    </div>
  `;

  // Root finding demo
  const rfArea = document.getElementById("trip-root-finding-area");
  if (rfArea && res.root_finding_demo) {
    const demo = res.root_finding_demo;
    const bisect = demo.bisection;
    const newton = demo.newton_raphson;

    rfArea.innerHTML = `
      <div class="card" style="margin-top:20px;">
        <div class="card-title">
          <span>Numerical Root-Finding Demonstration: Solving for Minimum Starting SoC</span>
          <span class="badge badge-demo">Methods Lab Engine</span>
        </div>
        <div class="card-subtitle">${demo.academic_explanation}</div>
        
        <div class="grid-2">
          <div>
            <div style="font-weight:600; font-size:0.85rem; color:#2563eb; margin-bottom:6px;">Bisection Method (${bisect.iterations_count} iterations)</div>
            <div class="metric-box">
              <div class="metric-label">Calculated Root</div>
              <div class="metric-value">${bisect.root}%<span class="metric-unit">SoC</span></div>
              <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">Tolerance: ${bisect.tolerance} | Residual f(S): ${bisect.f_root}</div>
            </div>
          </div>
          <div>
            <div style="font-weight:600; font-size:0.85rem; color:#059669; margin-bottom:6px;">Newton-Raphson Method (${newton.iterations_count} iterations)</div>
            <div class="metric-box">
              <div class="metric-label">Calculated Root</div>
              <div class="metric-value">${newton.root}%<span class="metric-unit">SoC</span></div>
              <div style="font-size:0.75rem; color:#64748b; margin-top:4px;">Tolerance: ${newton.tolerance} | Residual f(S): ${newton.f_root}</div>
            </div>
          </div>
        </div>

        <div class="steps-container" style="margin-top:14px;">
          <div style="font-weight:600; font-size:0.8rem; margin-bottom:6px;">BISECTION ITERATION TRACE:</div>
          ${bisect.history.slice(0, 6).map(h => `
            <div class="step-row">Iter ${h.iteration}: [${h.a}, ${h.b}] -> Midpoint m = ${h.midpoint_m} (f(m) = ${h.f_m})</div>
          `).join("")}
          ${bisect.history.length > 6 ? `<div class="step-row">... (${bisect.history.length - 6} more iterations converged to root)</div>` : ''}
        </div>
      </div>
    `;
  }
}

// 5. BATTERY HEALTH (SOH) PAGE
function renderBatteryHealth(container) {
  const prof = state.activeProfile || { original_usable_capacity_kwh: 60.0, usable_capacity_kwh: 54.9 };
  const measurements = state.health.measurements || [];

  container.innerHTML = `
    <div style="margin-bottom:16px;">
      <h2 style="font-size:1.15rem; font-weight:700;">Battery Capacity & State of Health (SOH)</h2>
      <p style="font-size:0.82rem; color:#64748b;">Evaluates capacity degradation, capacity loss (kWh & %), and annualized degradation trends.</p>
    </div>

    <div class="grid-2">
      <!-- Input Card -->
      <div class="card">
        <div class="card-title">Capacity Measurements</div>
        <div class="form-group">
          <label class="form-label">Original Usable Capacity When New (kWh)</label>
          <input type="number" id="soh-orig-cu" class="form-control" value="${prof.original_usable_capacity_kwh || 60.0}" />
        </div>
        <div class="form-group">
          <label class="form-label">Current Measured Usable Capacity (kWh)</label>
          <input type="number" step="0.1" id="soh-curr-cu" class="form-control" value="${prof.usable_capacity_kwh}" />
        </div>
        <button class="btn btn-primary" onclick="handleAnalyzeHealth()" style="margin-top:10px;">Calculate Battery Health</button>
      </div>

      <!-- SOH Result Output -->
      <div class="card" id="soh-results-card">
        <div class="card-title">State of Health Diagnosis</div>
        <div id="soh-result-area">
          <div style="text-align:center; padding:40px; color:#94a3b8;">Click 'Calculate Battery Health' to run SOH engine.</div>
        </div>
      </div>
    </div>

    <!-- Degradation Trend Chart Card -->
    <div class="card" style="margin-top:20px;">
      <div class="card-title">Historical Capacity Degradation Trend</div>
      <div class="card-subtitle">Measured usable capacity over time:</div>
      <div id="soh-trend-chart">
        ${measurements.length >= 2 
          ? generateSVGLineChart(measurements.map((m, i) => ({ index: i + 1, usable_capacity_kwh: m.usable_capacity_kwh, date: m.measurement_date })), "index", "usable_capacity_kwh", "Usable Battery Capacity (kWh) Over Successive Inspections", "Inspection #", "Capacity (kWh)", { color: "#0d9488" })
          : `<div style="text-align:center; padding:40px; color:#94a3b8;">No historical measurements loaded.</div>`
        }
      </div>
    </div>
  `;
}

async function handleAnalyzeHealth() {
  const orig = parseFloat(document.getElementById("soh-orig-cu").value);
  const curr = parseFloat(document.getElementById("soh-curr-cu").value);

  const hist = (state.health.measurements || []).map(m => ({
    date: m.measurement_date,
    capacity_kwh: m.usable_capacity_kwh,
    notes: m.measurement_notes
  }));

  try {
    const res = await apiCall("/health/analyze", "POST", {
      original_usable_capacity_kwh: orig,
      current_usable_capacity_kwh: curr,
      historical_measurements: hist.length >= 2 ? hist : null
    });

    state.health.result = res;
    renderHealthResults(res);
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

function renderHealthResults(res) {
  const area = document.getElementById("soh-result-area");
  if (!area) return;

  area.innerHTML = `
    <div class="grid-3">
      <div class="metric-box">
        <div class="metric-label">Estimated SOH</div>
        <div class="metric-value" style="color:#059669;">${res.soh_percent}<span class="metric-unit">%</span></div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Capacity Loss</div>
        <div class="metric-value">${res.capacity_loss_kwh}<span class="metric-unit">kWh</span></div>
        <div style="font-size:0.72rem; color:#64748b;">${res.capacity_loss_percent}% loss</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Health Status</div>
        <div class="metric-value" style="font-size:1.15rem; font-weight:700; color:#2563eb; margin-top:8px;">${res.health_status}</div>
      </div>
    </div>

    ${res.annual_degradation_rate_percent !== null ? `
      <div class="banner banner-info" style="margin-top:14px;">
        <div>Annual Degradation Rate: <strong>${res.annual_degradation_rate_percent}% per year</strong> based on dated inspection records.</div>
      </div>
    ` : ''}

    <div class="steps-container" style="margin-top:14px;">
      <div style="font-weight:600; font-size:0.8rem; margin-bottom:6px;">FORMULA & DERIVATION:</div>
      ${res.steps.map(s => `<div class="step-row">${s}</div>`).join("")}
    </div>
  `;
}

// 6. METHODS LAB PAGE (ACADEMIC CENTERPIECE)
function renderMethodsLab(container) {
  const cat = state.methodsLab.category;

  container.innerHTML = `
    <div style="margin-bottom:16px;">
      <h2 style="font-size:1.15rem; font-weight:700;">Numerical Methods Laboratory </h2>
      <p style="font-size:0.82rem; color:#64748b;">Interactive mathematical playground demonstrating worked step-by-step algorithms, comparisons, and error metrics.</p>
    </div>

    <div class="tabs">
      <button class="tab-btn ${cat === 'integration' ? 'active' : ''}" onclick="handleSwitchLabTab('integration')">Integration (Trapezoidal vs Simpson 1/3)</button>
      <button class="tab-btn ${cat === 'interpolation' ? 'active' : ''}" onclick="handleSwitchLabTab('interpolation')">Interpolation (Linear vs Newton Polynomial)</button>
      <button class="tab-btn ${cat === 'root_finding' ? 'active' : ''}" onclick="handleSwitchLabTab('root_finding')">Root-Finding (Bisection vs Newton-Raphson)</button>
      <button class="tab-btn ${cat === 'regression' ? 'active' : ''}" onclick="handleSwitchLabTab('regression')">Linear Regression & Error Metrics</button>
    </div>

    <div id="methods-lab-content">
      ${renderLabContent(cat)}
    </div>
  `;
}

function handleSwitchLabTab(cat) {
  state.methodsLab.category = cat;
  state.methodsLab.result = null;
  renderMethodsLab(document.getElementById("main-content"));
}

function renderLabContent(cat) {
  if (cat === "integration") {
    return `
      <div class="card">
        <div class="card-title">Numerical Integration Comparison</div>
        <div class="card-subtitle">Test Trapezoidal Rule and Simpson's 1/3 Rule on uniform vs non-uniform power observations:</div>
        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">Time Points in Minutes (Comma Separated)</label>
            <input type="text" id="lab-int-t" class="form-control" value="0, 15, 30, 45, 60" />
            <span style="font-size:0.72rem; color:#64748b;">Requires uniform spacing and even intervals for Simpson 1/3</span>
          </div>
          <div class="form-group">
            <label class="form-label">Power in kW (Comma Separated)</label>
            <input type="text" id="lab-int-p" class="form-control" value="10.0, 12.5, 14.0, 11.5, 9.0" />
          </div>
        </div>
        <button class="btn btn-primary" onclick="handleRunLabIntegration()">Run Comparison & Step-by-Step Derivation</button>
        <div id="lab-int-output" style="margin-top:16px;"></div>
      </div>
    `;
  } else if (cat === "interpolation") {
    return `
      <div class="card">
        <div class="card-title">Polynomial Interpolation Comparison</div>
        <div class="card-subtitle">Compare Linear piecewise interpolation with Newton's Divided-Difference global polynomial:</div>
        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">Known Coordinates (x, y pairs separated by semicolon)</label>
            <input type="text" id="lab-inter-pts" class="form-control" value="10, 20; 25, 35; 40, 52; 60, 70" />
          </div>
          <div class="form-group">
            <label class="form-label">Target x Value to Estimate</label>
            <input type="number" step="0.1" id="lab-inter-target" class="form-control" value="30" />
          </div>
        </div>
        <button class="btn btn-primary" onclick="handleRunLabInterpolation()">Interpolate & View Divided Difference Table</button>
        <div id="lab-inter-output" style="margin-top:16px;"></div>
      </div>
    `;
  } else if (cat === "root_finding") {
    return `
      <div class="card">
        <div class="card-title">Root-Finding Convergence: Bisection vs Newton-Raphson</div>
        <div class="card-subtitle">Solves journey minimum SoC reserve residual function f(S) = 0:</div>
        <div class="grid-3">
          <div class="form-group">
            <label class="form-label">Usable Capacity (kWh)</label>
            <input type="number" id="lab-rf-cu" class="form-control" value="60" />
          </div>
          <div class="form-group">
            <label class="form-label">Journey Distance (km)</label>
            <input type="number" id="lab-rf-dist" class="form-control" value="140" />
          </div>
          <div class="form-group">
            <label class="form-label">Consumption (kWh/km)</label>
            <input type="number" step="0.001" id="lab-rf-rate" class="form-control" value="0.20" />
          </div>
        </div>
        <button class="btn btn-primary" onclick="handleRunLabRootFinding()">Compare Convergence Iterations</button>
        <div id="lab-rf-output" style="margin-top:16px;"></div>
      </div>
    `;
  } else {
    // Regression & Error Metrics
    return `
      <div class="card">
        <div class="card-title">Least Squares Linear Regression & Error Metrics</div>
        <div class="card-subtitle">Computes slope, intercept, R², residuals, MAE, and RMSE:</div>
        <div class="grid-2">
          <div class="form-group">
            <label class="form-label">Distances in km (Comma Separated)</label>
            <input type="text" id="lab-reg-x" class="form-control" value="15, 30, 45, 60, 80, 100" />
          </div>
          <div class="form-group">
            <label class="form-label">Energy in kWh (Comma Separated)</label>
            <input type="text" id="lab-reg-y" class="form-control" value="2.8, 5.5, 8.4, 11.2, 15.1, 19.0" />
          </div>
        </div>
        <button class="btn btn-primary" onclick="handleRunLabRegression()">Fit Model & Calculate Error Metrics</button>
        <div id="lab-reg-output" style="margin-top:16px;"></div>
      </div>
    `;
  }
}

async function handleRunLabIntegration() {
  const tArr = document.getElementById("lab-int-t").value.split(",").map(v => parseFloat(v.trim()));
  const pArr = document.getElementById("lab-int-p").value.split(",").map(v => parseFloat(v.trim()));

  try {
    const res = await apiCall("/methods/compare", "POST", {
      category: "integration",
      dataset: { t_minutes: tArr, power_kw: pArr }
    });
    const out = document.getElementById("lab-int-output");
    out.innerHTML = `
      <div class="grid-2" style="margin-top:14px;">
        <div class="metric-box">
          <div class="metric-label">Trapezoidal Rule Result</div>
          <div class="metric-value">${res.trapezoidal.total_energy_kwh.toFixed(4)}<span class="metric-unit">kWh</span></div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Simpson's 1/3 Rule Result</div>
          <div class="metric-value">${res.simpsons ? res.simpsons.total_energy_kwh.toFixed(4) + '<span class="metric-unit">kWh</span>' : 'Ineligible'}</div>
          <div style="font-size:0.75rem; color:#64748b;">${res.simpson_eligible ? `Diff: ${res.absolute_difference_kwh.toFixed(6)} kWh` : res.simpson_ineligibility_reason}</div>
        </div>
      </div>
      <div class="banner banner-info" style="margin-top:14px;">
        <div>${res.academic_note}</div>
      </div>
      <div class="steps-container">
        <div style="font-weight:600; font-size:0.8rem; margin-bottom:6px;">TRAPEZOIDAL METHOD DERIVATION:</div>
        ${res.trapezoidal.steps.map(s => `<div class="step-row">${s}</div>`).join("")}
      </div>
      ${res.simpsons ? `
        <div class="steps-container" style="margin-top:14px;">
          <div style="font-weight:600; font-size:0.8rem; margin-bottom:6px;">SIMPSON'S 1/3 METHOD DERIVATION:</div>
          ${res.simpsons.steps.map(s => `<div class="step-row">${s}</div>`).join("")}
        </div>
      ` : ''}
    `;
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

async function handleRunLabInterpolation() {
  const ptsRaw = document.getElementById("lab-inter-pts").value.split(";");
  const pts = ptsRaw.map(pair => pair.split(",").map(v => parseFloat(v.trim())));
  const targetX = parseFloat(document.getElementById("lab-inter-target").value);

  try {
    const res = await apiCall("/methods/compare", "POST", {
      category: "interpolation",
      dataset: { points: pts, target_x: targetX }
    });

    const out = document.getElementById("lab-inter-output");
    out.innerHTML = `
      <div class="grid-2" style="margin-top:14px;">
        <div class="metric-box">
          <div class="metric-label">Linear Estimate (Local)</div>
          <div class="metric-value">${res.linear.result_y}</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Newton Polynomial Estimate</div>
          <div class="metric-value">${res.newton.result_y}</div>
          <div style="font-size:0.75rem; color:#64748b;">Degree ${res.newton.degree} | Absolute Diff: ${res.absolute_difference}</div>
        </div>
      </div>
      <div class="banner banner-info" style="margin-top:14px;">
        <div>${res.academic_summary}</div>
      </div>
      <div class="steps-container">
        <div style="font-weight:600; font-size:0.8rem; margin-bottom:6px;">NEWTON DIVIDED-DIFFERENCE DERIVATION:</div>
        <div class="formula-block">P(x) = ${res.newton.polynomial_str}</div>
        ${res.newton.steps.map(s => `<div class="step-row">${s}</div>`).join("")}
      </div>
    `;
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

async function handleRunLabRootFinding() {
  const cu = parseFloat(document.getElementById("lab-rf-cu").value);
  const dist = parseFloat(document.getElementById("lab-rf-dist").value);
  const rate = parseFloat(document.getElementById("lab-rf-rate").value);

  try {
    const res = await apiCall("/methods/compare", "POST", {
      category: "root_finding",
      dataset: { usable_capacity_kwh: cu, distance_km: dist, consumption_kwh_per_km: rate, reserve_percent: 10.0 }
    });

    const out = document.getElementById("lab-rf-output");
    out.innerHTML = `
      <div class="banner banner-success" style="margin-top:14px;">
        <div>Exact Analytical Root: <strong>${res.exact_analytical_root}% SoC</strong>. Both iterative numerical solvers converged successfully.</div>
      </div>
      <div class="grid-2">
        <div class="metric-box">
          <div class="metric-label">Bisection Method</div>
          <div class="metric-value">${res.bisection.root}%</div>
          <div style="font-size:0.75rem; color:#64748b;">${res.bisection.iterations_count} iterations (Linear convergence O(1/2^k))</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Newton-Raphson Method</div>
          <div class="metric-value">${res.newton_raphson.root}%</div>
          <div style="font-size:0.75rem; color:#64748b;">${res.newton_raphson.iterations_count} iterations (Quadratic convergence O(e_k^2))</div>
        </div>
      </div>
      <div class="banner banner-info" style="margin-top:14px;">
        <div>${res.iterations_comparison.convergence_rate}</div>
      </div>
    `;
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

async function handleRunLabRegression() {
  const xs = document.getElementById("lab-reg-x").value.split(",").map(v => parseFloat(v.trim()));
  const ys = document.getElementById("lab-reg-y").value.split(",").map(v => parseFloat(v.trim()));

  try {
    const res = await apiCall("/methods/regression-demo", "POST", {
      distance_km: xs,
      energy_consumed_kwh: ys
    });

    const out = document.getElementById("lab-reg-output");
    out.innerHTML = `
      <div class="grid-4" style="margin-top:14px;">
        <div class="metric-box">
          <div class="metric-label">Fitted Equation</div>
          <div style="font-family:var(--font-mono); font-size:0.92rem; font-weight:700; margin-top:6px;">${res.equation}</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Coefficient R²</div>
          <div class="metric-value">${res.r_squared}</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">MAE</div>
          <div class="metric-value">${res.mae_kwh}<span class="metric-unit">kWh</span></div>
        </div>
        <div class="metric-box">
          <div class="metric-label">RMSE</div>
          <div class="metric-value">${res.rmse_kwh}<span class="metric-unit">kWh</span></div>
        </div>
      </div>
      <div class="steps-container" style="margin-top:14px;">
        <div style="font-weight:600; font-size:0.8rem; margin-bottom:6px;">LEAST SQUARES DERIVATION STEPS:</div>
        ${res.steps.map(s => `<div class="step-row">${s}</div>`).join("")}
      </div>
    `;
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

// 7. DATA & HISTORY PAGE
function renderDataHistory(container) {
  container.innerHTML = `
    <div style="margin-bottom:16px;">
      <h2 style="font-size:1.15rem; font-weight:700;">Data Management & Analysis History</h2>
      <p style="font-size:0.82rem; color:#64748b;">Import/export CSV datasets and reset demonstration data.</p>
    </div>

    <div class="grid-2">
      <!-- Import CSV Card -->
      <div class="card">
        <div class="card-title">Import CSV Dataset</div>
        <div class="card-subtitle">Upload custom telemetry or classroom datasets:</div>
        <form id="csv-upload-form" onsubmit="handleUploadCSV(event)">
          <div class="form-group">
            <label class="form-label">Dataset Type</label>
            <select id="csv-type" class="form-control">
              <option value="charging">Charging Session Readings (time, soc, power, energy)</option>
              <option value="trips">Driving Trips History (distance, energy, date)</option>
              <option value="capacity">Capacity Measurements (date, capacity)</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Select CSV File</label>
            <input type="file" id="csv-file-input" class="form-control" accept=".csv" required />
          </div>
          <button type="submit" class="btn btn-primary" style="margin-top:8px;">Upload & Parse CSV</button>
        </form>
      </div>

      <!-- Export CSV Card -->
      <div class="card">
        <div class="card-title">Export Datasets</div>
        <div class="card-subtitle">Download current system records to CSV files:</div>
        <div style="display:flex; flex-direction:column; gap:10px; margin-top:14px;">
          <a href="/api/data/export-csv/charging" class="btn btn-secondary" style="justify-content:flex-start;">
            📥 Download Charging Readings CSV
          </a>
          <a href="/api/data/export-csv/trips" class="btn btn-secondary" style="justify-content:flex-start;">
            📥 Download Historical Trips CSV
          </a>
          <a href="/api/data/export-csv/capacity" class="btn btn-secondary" style="justify-content:flex-start;">
            📥 Download Capacity Measurements CSV
          </a>
        </div>
      </div>
    </div>

    <!-- Reset Demonstration Data Card -->
    <div class="card" style="border-color:#fecdd3;">
      <div class="card-title" style="color:#e11d48;">Reset Demonstration Data</div>
      <div class="card-subtitle">Restores all database tables to fresh, clean Synthetic Demonstration Data (ideal for laboratory evaluations):</div>
      <button class="btn btn-danger" onclick="handleResetDemoData()">Reset All Demo Datasets</button>
    </div>
  `;
}

async function handleUploadCSV(e) {
  e.preventDefault();
  const fileInput = document.getElementById("csv-file-input");
  const typeSelect = document.getElementById("csv-type");
  if (!fileInput.files || fileInput.files.length === 0) return;

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  formData.append("dataset_type", typeSelect.value);
  if (state.activeProfile) {
    formData.append("profile_id", state.activeProfile.id);
  }

  try {
    const res = await fetch(`${API_BASE}/data/import-csv`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");

    state.dataSourceLabel = "Imported CSV Dataset";
    updateHeaderProfile();
    showNotification(data.message, "success");
    // Reload sessions or trips
    const sessions = await apiCall("/charging/sessions");
    state.charging.sessions = sessions;
    if (sessions.length > 0) {
      state.charging.selectedSessionId = sessions[0].id;
      state.charging.readings = sessions[0].readings || [];
    }
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

async function handleResetDemoData() {
  if (!confirm("Are you sure you want to reset all data back to the clean Synthetic Demonstration Data?")) return;
  try {
    await apiCall("/data/reset-demo-data", "POST");
    state.dataSourceLabel = "Synthetic Demo Data";
    showNotification("All database tables reset to factory synthetic demonstration data.", "success");
    await initializeApp();
  } catch (err) {
    showNotification(err.message, "danger");
  }
}

// 8. ABOUT PROJECT PAGE
function renderAboutProject(container) {
  container.innerHTML = `
    <div class="card">
      <div class="card-title" style="font-size:1.25rem;">EVolve --- Intelligent EV Battery Analytics & Predictive System</div>
      <div class="card-subtitle">B.Tech Second-Year Engineering Project | Computational Methods Lab</div>
      
      <div class="banner banner-info" style="margin-top:14px;">
        <div>
          <strong>Syllabus Status:</strong> Initial implementation specification. Exact syllabus alignment to be confirmed against student's prescribed university syllabus.
        </div>
      </div>

      <div style="margin-top:18px;">
        <h3 style="font-size:1rem; font-weight:700; color:#1e293b; margin-bottom:6px;">1. Problem Statement</h3>
        <p style="font-size:0.86rem; color:#475569; line-height:1.6;">
          Electric vehicle drivers and energy analysts face substantial uncertainty estimating charging durations, delivered kilowatt-hours, and remaining driving range. Real-world charging power is not constant—it tapers significantly as battery cells reach saturation. Telemetry feeds frequently suffer sensor dropouts, and actual vehicle consumption deviates markedly from manufacturer claims due to driving speed and ambient weather. EVolve addresses these challenges by grounding all estimations in transparent, reproducible numerical methods.
        </p>
      </div>

      <div style="margin-top:18px;">
        <h3 style="font-size:1rem; font-weight:700; color:#1e293b; margin-bottom:6px;">2. Implemented Numerical Methods</h3>
        <ul style="margin-left:20px; font-size:0.86rem; color:#475569; line-height:1.8;">
          <li><strong>Linear & Newton Divided-Difference Interpolation:</strong> Fills sensor dropouts and constructs power taper polynomials.</li>
          <li><strong>Composite Trapezoidal Rule:</strong> Evaluates delivered charging energy over arbitrary discrete time intervals.</li>
          <li><strong>Simpson's 1/3 Rule:</strong> Delivers higher-order $O(h^4)$ precision on uniformly sampled parabolic power curves.</li>
          <li><strong>Variable-Power Curve Integration:</strong> Integrates $T = \int (C_u/100)/P(S) dS$ to model real-world taper above 80% SoC.</li>
          <li><strong>Least Squares Linear Regression:</strong> Derives marginal energy consumption (kWh/km) and auxiliary baseline overhead from trip logs.</li>
          <li><strong>Bisection & Newton-Raphson Root Finding:</strong> Evaluates nonlinear trip reserve constraints and demonstrates algorithm convergence rates.</li>
          <li><strong>Error Analysis:</strong> Quantifies Absolute Error, Relative Percentage Error, MAE, and RMSE against meter benchmarks.</li>
        </ul>
      </div>

      <div style="margin-top:18px;">
        <h3 style="font-size:1rem; font-weight:700; color:#1e293b; margin-bottom:6px;">3. System Architecture & Modularity</h3>
        <p style="font-size:0.86rem; color:#475569; line-height:1.6;">
          Strict architectural separation of concerns is maintained throughout:
          The Python FastAPI backend encapsulates independent, testable numerical calculation modules; data persistence is managed via relational SQLite; and the presentation layer renders responsive UI elements with live SVG charts.
        </p>
      </div>

      <div style="margin-top:18px;">
        <h3 style="font-size:1rem; font-weight:700; color:#1e293b; margin-bottom:6px;">4. Academic Disclaimer</h3>
        <p style="font-size:0.82rem; color:#64748b; line-height:1.6;">
          EVolve is an educational decision-support prototype. It does not interface directly with physical vehicle CAN buses or high-voltage equipment, nor does it substitute for certified Battery Management Systems (BMS) or OEM diagnostic tools.
        </p>
      </div>
    </div>
  `;
}

// Window Onload Bootstrap
window.addEventListener("DOMContentLoaded", () => {
  // Bind sidebar click events
  document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      const page = link.dataset.page;
      navigateTo(page);
    });
  });

  initializeApp();
});
