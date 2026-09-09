/**
 * SIH 2026 Ocean Agentic AI — Dashboard Application Logic (Phase 9)
 */

const API_BASE = "http://localhost:8000";

document.addEventListener("DOMContentLoaded", () => {
  checkApiHealth();
  setupEventListeners();
});

// Check if FastAPI backend is reachable
async function checkApiHealth() {
  const statusEl = document.getElementById("api-status");
  try {
    const res = await fetch(`${API_BASE}/health`, { method: "GET" });
    if (res.ok) {
      statusEl.textContent = "Online (v0.1.0)";
      statusEl.style.color = "#00e676";
    } else {
      statusEl.textContent = `Error ${res.status}`;
      statusEl.style.color = "#ffab00";
    }
  } catch (err) {
    statusEl.textContent = "Offline (start uvicorn on port 8000)";
    statusEl.style.color = "#ff5252";
  }
}

function setupEventListeners() {
  // Preset selector
  document.getElementById("preset-select").addEventListener("change", (e) => {
    const val = e.target.value;
    if (val === "custom") return;

    const [lat, lon, imd, noaa, ndbc, port] = val.split(",");
    document.getElementById("input-lat").value = lat || "";
    document.getElementById("input-lon").value = lon || "";
    document.getElementById("input-imd-stn").value = imd || "";
    document.getElementById("input-noaa-stn").value = noaa || "";
    document.getElementById("input-ndbc-stn").value = ndbc || "";
    document.getElementById("input-tides-port").value = port || "";
  });

  // Fetch button
  document.getElementById("btn-fetch").addEventListener("click", fetchMarineData);
}

async function fetchMarineData() {
  const btn = document.getElementById("btn-fetch");
  const info = document.getElementById("fetch-info");
  const lat = document.getElementById("input-lat").value;
  const lon = document.getElementById("input-lon").value;

  if (!lat || !lon) {
    alert("Please enter valid Latitude and Longitude.");
    return;
  }

  // Build provider filter list
  const selectedProviders = Array.from(document.querySelectorAll('input[name="provider"]:checked'))
    .map(cb => cb.value);

  const params = new URLSearchParams({
    latitude: lat,
    longitude: lon,
  });

  if (selectedProviders.length > 0 && selectedProviders.length < 7) {
    params.set("providers", selectedProviders.join(","));
  }

  const imdStn = document.getElementById("input-imd-stn").value.trim();
  if (imdStn) params.set("imd_station_id", imdStn);

  const noaaStn = document.getElementById("input-noaa-stn").value.trim();
  if (noaaStn) params.set("noaa_station_id", noaaStn);

  const ndbcStn = document.getElementById("input-ndbc-stn").value.trim();
  if (ndbcStn) params.set("noaa_ndbc_station_id", ndbcStn);

  const tidesPort = document.getElementById("input-tides-port").value.trim();
  if (tidesPort) params.set("tidesatlas_port", tidesPort);

  btn.disabled = true;
  btn.innerHTML = `<span class="btn-icon">⏳</span> Querying Providers...`;
  info.textContent = `Gathering concurrent data for (${lat}, ${lon})...`;

  const startTime = performance.now();

  try {
    const res = await fetch(`${API_BASE}/api/marine/data?${params.toString()}`);
    const elapsed = Math.round(performance.now() - startTime);

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData?.error?.message || `HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    info.textContent = `Successfully aggregated in ${elapsed} ms`;
    renderDashboard(data);
  } catch (err) {
    info.textContent = `Fetch error: ${err.message}`;
    alert(`Could not fetch unified marine data: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="btn-icon">⚡</span> Fetch Unified Marine Data`;
  }
}

function renderDashboard(data) {
  // Banner
  document.getElementById("stat-coords").textContent = `${data.location.latitude}° N, ${data.location.longitude}° E`;
  document.getElementById("stat-sources").textContent = data.sources.join(", ") || "None";
  document.getElementById("stat-timestamp").textContent = data.timestamp ? new Date(data.timestamp).toLocaleString() : "—";

  // Weather Card
  const wx = data.weather || {};
  document.getElementById("badge-weather-src").textContent = wx.source || "No Source";
  document.getElementById("val-temp").textContent = wx.temperature != null ? wx.temperature : "--";
  document.getElementById("unit-temp").textContent = wx.temperature_unit || "°C";
  document.getElementById("val-condition").textContent = wx.condition || "—";
  document.getElementById("val-wind").textContent = wx.wind_speed != null ? `${wx.wind_speed} ${wx.wind_speed_unit || 'm/s'}` : "—";
  document.getElementById("val-wind-dir").textContent = wx.wind_direction != null ? `${wx.wind_direction}°` : "—";
  document.getElementById("val-humidity").textContent = wx.humidity != null ? `${wx.humidity} %` : "—";
  document.getElementById("val-pressure").textContent = wx.pressure != null ? `${wx.pressure} ${wx.pressure_unit || 'hPa'}` : "—";
  document.getElementById("val-rain").textContent = wx.precipitation != null ? `${wx.precipitation} ${wx.precipitation_unit || 'mm'}` : "—";

  // Waves Card
  const wv = data.waves || {};
  document.getElementById("badge-waves-src").textContent = wv.source || "No Source";
  document.getElementById("val-wave-ht").textContent = wv.height != null ? wv.height : "--";
  document.getElementById("unit-wave-ht").textContent = wv.height_unit || "m";
  document.getElementById("val-wave-period").textContent = wv.period != null ? `${wv.period} ${wv.period_unit || 's'}` : "—";
  document.getElementById("val-wave-dir").textContent = wv.direction != null ? `${wv.direction}°` : "—";
  document.getElementById("val-swell-ht").textContent = wv.swell_height != null ? `${wv.swell_height} ${wv.swell_height_unit || 'm'}` : "—";
  document.getElementById("val-swell-period").textContent = wv.swell_period != null ? `${wv.swell_period} s` : "—";

  // Ocean Card
  const oc = data.ocean || {};
  const cur = data.currents || {};
  document.getElementById("badge-ocean-src").textContent = oc.sst_source || "No Source";
  document.getElementById("val-sst").textContent = oc.sea_surface_temperature != null ? oc.sea_surface_temperature : "--";
  document.getElementById("unit-sst").textContent = `${oc.sst_unit || '°C'} (SST)`;
  document.getElementById("val-chlorophyll").textContent = oc.chlorophyll != null ? `${oc.chlorophyll} ${oc.chlorophyll_unit || ''}` : "Unavailable (Extraction Pending)";
  document.getElementById("val-salinity").textContent = oc.salinity != null ? `${oc.salinity} ${oc.salinity_unit || 'PSU'}` : "—";
  document.getElementById("val-current-vel").textContent = cur.velocity != null ? `${cur.velocity} ${cur.velocity_unit || 'm/s'}` : "—";
  document.getElementById("val-current-dir").textContent = cur.direction != null ? `${cur.direction}°` : "—";

  // Tides Card
  const td = data.tides || {};
  document.getElementById("badge-tides-src").textContent = td.source || "No Source";
  document.getElementById("val-water-level").textContent = td.water_level != null ? td.water_level : "--";
  document.getElementById("unit-water-level").textContent = td.water_level_unit || "m";
  document.getElementById("val-datum").textContent = td.datum || "—";
  document.getElementById("val-tide-state").textContent = td.prediction || (td.data_type ? `Type: ${td.data_type}` : "—");
  document.getElementById("val-extremes-count").textContent = td.extremes && td.extremes.length ? `${td.extremes.length} predictions recorded` : "—";

  // Discrepancies
  const allDiscrepancies = [
    ...(wx.discrepancies || []),
    ...(wv.discrepancies || []),
    ...(oc.discrepancies || []),
    ...(td.discrepancies || []),
  ];

  const discBox = document.getElementById("discrepancies-box");
  const discList = document.getElementById("discrepancies-list");
  const discStat = document.getElementById("stat-discrepancies");

  if (allDiscrepancies.length > 0) {
    discBox.classList.remove("hidden");
    discStat.textContent = `${allDiscrepancies.length} Preserved`;
    discStat.className = "stat-value badge badge-warning";

    discList.innerHTML = allDiscrepancies.map(d => `
      <div class="discrepancy-card">
        <strong>${d.parameter.toUpperCase()} Discrepancy:</strong> Primary selected is 
        <em>${d.primary.source}</em> (${d.primary.value} ${d.primary.unit || ''}).
        ${d.delta != null ? `<span class="badge badge-warning">Delta: ${d.delta}</span>` : ''}
        <div style="margin-top: 4px; color: #8b9bb4;">
          Candidate Values: ${d.candidates.map(c => `${c.source}: <strong>${c.value} ${c.unit || ''}</strong>`).join(" vs ")}
        </div>
      </div>
    `).join("");
  } else {
    discBox.classList.add("hidden");
    discStat.textContent = "0 Detected";
    discStat.className = "stat-value badge badge-neutral";
  }

  // Bulletins & Alerts
  const bullContainer = document.getElementById("bulletins-container");
  if (data.bulletins && data.bulletins.length > 0) {
    bullContainer.innerHTML = data.bulletins.map(b => {
      const isWarn = b.severity && (b.severity.toLowerCase().includes("warn") || b.severity.toLowerCase().includes("mod"));
      return `
        <div class="bulletin-item ${isWarn ? 'alert-warning' : ''}">
          <div class="bulletin-title">${b.title} <span class="badge badge-source">${b.source}</span> ${b.severity ? `<span class="badge badge-warning">${b.severity}</span>` : ''}</div>
          <div class="bulletin-text">${b.text}</div>
          ${b.timestamp ? `<div style="font-size: 0.72rem; color: #8b9bb4; margin-top: 4px;">Valid / Issued: ${b.timestamp}</div>` : ''}
        </div>
      `;
    }).join("");
  } else {
    bullContainer.innerHTML = `<p class="placeholder-text">No active marine bulletins or warnings for this coordinate.</p>`;
  }

  // Provider Status & Traceability Table
  const statusTbody = document.getElementById("provider-status-tbody");
  const statuses = data.provider_status || {};
  const statusKeys = Object.keys(statuses);

  if (statusKeys.length > 0) {
    statusTbody.innerHTML = statusKeys.map(k => {
      const st = statuses[k];
      let badgeClass = "badge-neutral";
      if (st.status === "success") badgeClass = "badge-success";
      else if (st.status === "failed") badgeClass = "badge-danger";
      else if (st.status === "not_configured" || st.status === "not_implemented") badgeClass = "badge-warning";

      return `
        <tr>
          <td><strong>${k.toUpperCase().replace("_", " ")}</strong></td>
          <td><span class="badge ${badgeClass}">${st.status}</span></td>
          <td>${st.latency_ms != null ? `${st.latency_ms} ms` : '—'}</td>
          <td>${st.message || 'Operational'}</td>
        </tr>
      `;
    }).join("");
  } else {
    statusTbody.innerHTML = `<tr><td colspan="4" class="text-center">No provider statuses reported.</td></tr>`;
  }

  // Sensor Observations Table
  const obsTbody = document.getElementById("observations-tbody");
  if (data.observations && data.observations.length > 0) {
    obsTbody.innerHTML = data.observations.map(o => `
      <tr>
        <td><code>${o.parameter}</code></td>
        <td><strong>${o.value != null ? o.value : 'null'}</strong></td>
        <td>${o.unit || '—'}</td>
        <td>${o.station_id || 'Coordinates'}</td>
        <td><span class="badge badge-source">${o.source}</span></td>
        <td class="text-mono">${o.timestamp ? new Date(o.timestamp).toLocaleTimeString() : '—'}</td>
      </tr>
    `).join("");
  } else {
    obsTbody.innerHTML = `<tr><td colspan="6" class="text-center">No discrete buoy or station observations available.</td></tr>`;
  }
}
