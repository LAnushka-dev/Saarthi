const $ = (id) => document.getElementById(id);

let GRAPH = null;
let gmap = null;
let directionsService = null;
let directionsRenderer = null;
let mapProvider = "none"; // google | osm
let osmMap = null;
let osmRouteLayer = null;
let osmMarkers = [];

const CITY_LATLNG = {
  Ahmedabad: { lat: 23.0225, lng: 72.5714 },
  Surat: { lat: 21.1702, lng: 72.8311 },
  Vadodara: { lat: 22.3072, lng: 73.1812 },
  Mumbai: { lat: 19.076, lng: 72.8777 },
  Pune: { lat: 18.5204, lng: 73.8567 },
  Nashik: { lat: 19.9975, lng: 73.7898 },
  Goa: { lat: 15.2993, lng: 74.124 },
  Hyderabad: { lat: 17.385, lng: 78.4867 },
  Bengaluru: { lat: 12.9716, lng: 77.5946 },
  Chennai: { lat: 13.0827, lng: 80.2707 },
  Kolkata: { lat: 22.5726, lng: 88.3639 },
  Patna: { lat: 25.5941, lng: 85.1376 },
  Delhi: { lat: 28.6139, lng: 77.209 },
  Lucknow: { lat: 26.8467, lng: 80.9462 },
  Kanpur: { lat: 26.4499, lng: 80.3319 },
  Jaipur: { lat: 26.9124, lng: 75.7873 },
  Bhopal: { lat: 23.2599, lng: 77.4126 },
  Indore: { lat: 22.7196, lng: 75.8577 },
  Nagpur: { lat: 21.1458, lng: 79.0882 },
  Ranchi: { lat: 23.3441, lng: 85.3096 },
  Bhubaneswar: { lat: 20.2961, lng: 85.8245 },
};

function populateCities(cities) {
  const originSel = $("origin");
  const destSel = $("destination");
  originSel.innerHTML = "";
  destSel.innerHTML = "";

  for (const c of cities) {
    const o = document.createElement("option");
    o.value = c;
    o.textContent = c;
    originSel.appendChild(o);

    const d = document.createElement("option");
    d.value = c;
    d.textContent = c;
    destSel.appendChild(d);
  }

  originSel.value = "Nashik";
  destSel.value = "Pune";
}

function setStatus(msg, kind = "muted") {
  const el = $("status");
  el.textContent = msg;
  el.style.color = kind === "danger" ? "var(--danger)" : "var(--muted)";
}

function ensureGoogleMapsLoaded() {
  return new Promise((resolve, reject) => {
    if (window.google && window.google.maps) return resolve();
    const key = window.GMAPS_API_KEY || "";
    if (!key) return reject(new Error("Missing Google Maps API key (set window.GMAPS_API_KEY in frontend/config.js)."));
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&v=weekly`;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Maps JS API."));
    document.head.appendChild(script);
  });
}

async function initMap() {
  try {
    await ensureGoogleMapsLoaded();
    mapProvider = "google";
  } catch (_e) {
    mapProvider = "osm";
  }

  if (mapProvider === "google") {
    gmap = new google.maps.Map($("gmap"), {
      center: { lat: 22.3511, lng: 78.6677 }, // India center-ish
      zoom: 5,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true,
    });

    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
      map: gmap,
      suppressMarkers: false,
      preserveViewport: false,
    });
    setStatus("Google Maps loaded.");
    return;
  }

  // No API key fallback: OpenStreetMap via Leaflet + OSRM route service.
  if (!window.L) {
    setStatus("Map failed to load. Add Google API key or check internet.", "danger");
    return;
  }

  osmMap = L.map("gmap").setView([22.3511, 78.6677], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(osmMap);
  setStatus("Using OpenStreetMap (no API key).");
}

function travelModeFor(mode) {
  // Google can't render "mixed road+rail" in one Directions call reliably.
  // We'll render DRIVING with waypoints that match the Dijkstra city path.
  if (mode === "rail") return google.maps.TravelMode.TRANSIT;
  return google.maps.TravelMode.DRIVING;
}

async function drawGoogleRoute(resp) {
  if (!gmap || !directionsService || !directionsRenderer) return;

  const cities = resp.path_cities || [];
  if (cities.length < 2) return;

  const origin = CITY_LATLNG[cities[0]] ? cities[0] : `${cities[0]}, India`;
  const destination = CITY_LATLNG[cities[cities.length - 1]] ? cities[cities.length - 1] : `${cities[cities.length - 1]}, India`;

  const waypoints = cities.slice(1, -1).map((c) => ({
    location: CITY_LATLNG[c] ? c : `${c}, India`,
    stopover: true,
  }));

  const request = {
    origin,
    destination,
    waypoints,
    optimizeWaypoints: false,
    travelMode: travelModeFor(resp.mode),
    provideRouteAlternatives: false,
  };

  directionsService.route(request, (result, status) => {
    if (status !== "OK") {
      console.warn("Directions failed:", status);
      return;
    }
    directionsRenderer.setDirections(result);
  });
}

function clearOsmRoute() {
  if (!osmMap) return;
  if (osmRouteLayer) {
    osmMap.removeLayer(osmRouteLayer);
    osmRouteLayer = null;
  }
  for (const m of osmMarkers) osmMap.removeLayer(m);
  osmMarkers = [];
}

function drawOsmFallbackPolyline(cities, color = "#f59e0b") {
  if (!osmMap || cities.length < 2) return;
  clearOsmRoute();
  const latlngs = cities
    .map((c) => CITY_LATLNG[c])
    .filter(Boolean)
    .map((p) => [p.lat, p.lng]);
  if (latlngs.length < 2) return;
  osmRouteLayer = L.polyline(latlngs, { color, weight: 5, opacity: 0.9 }).addTo(osmMap);
  osmMap.fitBounds(osmRouteLayer.getBounds(), { padding: [20, 20] });
  for (const c of cities) {
    const p = CITY_LATLNG[c];
    if (!p) continue;
    osmMarkers.push(L.marker([p.lat, p.lng]).addTo(osmMap).bindPopup(c));
  }
}

async function drawOsmRoute(resp) {
  if (!osmMap) return;
  const cities = resp.path_cities || [];
  if (cities.length < 2) return;

  // OSRM supports road routing only. For rail-only routes, fallback to joined city polyline.
  if (resp.mode === "rail") {
    drawOsmFallbackPolyline(cities, "#60a5fa");
    setStatus("Rail mode shown as city-to-city polyline on OpenStreetMap.");
    return;
  }

  const points = cities.map((c) => CITY_LATLNG[c]).filter(Boolean);
  if (points.length < 2) return;
  const coordString = points.map((p) => `${p.lng},${p.lat}`).join(";");
  const url = `https://router.project-osrm.org/route/v1/driving/${coordString}?overview=full&geometries=geojson`;

  try {
    const r = await fetch(url);
    const data = await r.json();
    if (!r.ok || !data.routes || !data.routes.length) {
      throw new Error("OSRM route unavailable");
    }
    const coords = data.routes[0].geometry.coordinates.map((p) => [p[1], p[0]]);
    clearOsmRoute();
    osmRouteLayer = L.polyline(coords, { color: "#f59e0b", weight: 5, opacity: 0.9 }).addTo(osmMap);
    osmMap.fitBounds(osmRouteLayer.getBounds(), { padding: [20, 20] });
    for (const c of cities) {
      const p = CITY_LATLNG[c];
      if (!p) continue;
      osmMarkers.push(L.marker([p.lat, p.lng]).addTo(osmMap).bindPopup(c));
    }
  } catch (_e) {
    drawOsmFallbackPolyline(cities, "#f59e0b");
    setStatus("OSRM unavailable. Showing city-to-city path on OpenStreetMap.");
  }
}

async function drawRouteOnMap(resp) {
  if (mapProvider === "google") {
    await drawGoogleRoute(resp);
    return;
  }
  if (mapProvider === "osm") {
    await drawOsmRoute(resp);
  }
}

function renderSegments(resp) {
  const tbody = $("segmentsTable").querySelector("tbody");
  tbody.innerHTML = "";
  let idx = 1;
  for (const seg of resp.segments) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${idx++}</td>
      <td>${seg.edge_type}</td>
      <td>${escapeHtml(seg.label)}</td>
      <td>${escapeHtml(seg.from_city)}</td>
      <td>${escapeHtml(seg.to_city)}</td>
      <td>${Number(seg.time_hours).toFixed(1)}h</td>
      <td>₹${Number(seg.cost_inr).toFixed(0)}</td>
    `;
    tbody.appendChild(tr);
  }
}

function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

async function loadGraph() {
  const r = await fetch("/api/graph");
  if (!r.ok) throw new Error("Failed to load graph");
  const graph = await r.json();
  GRAPH = graph;
  populateCities(graph.cities);
}

function renderAlerts(resp) {
  const ul = $("alerts");
  ul.innerHTML = "";

  if (!resp.alerts || resp.alerts.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No highway blockage alerts for this route.";
    ul.appendChild(li);
    return;
  }

  for (const a of resp.alerts) {
    const li = document.createElement("li");
    li.textContent = `${a.highway} (${a.severity}): ${a.message}`;
    ul.appendChild(li);
  }
}

function renderCargoNotes(resp) {
  const ul = $("cargoNotes");
  ul.innerHTML = "";
  for (const n of resp.cargo_notes || []) {
    const li = document.createElement("li");
    li.textContent = n;
    ul.appendChild(li);
  }
}

function renderTotals(resp) {
  const t = $("totals");
  t.innerHTML = `
    <div><b>Time:</b> ${Number(resp.totals.time_hours).toFixed(1)} hrs</div>
    <div><b>Cost:</b> ₹${Number(resp.totals.cost_inr).toFixed(0)}</div>
    <div><b>Distance:</b> ${Number(resp.totals.distance_km).toFixed(0)} km</div>
  `;
}

async function computeRoute() {
  setStatus("Computing route...");

  const origin = $("origin").value;
  const destination = $("destination").value;
  const mode = document.querySelector("input[name='mode']:checked").value;
  const optimize_by = $("optimizeBy").value;
  const cargo_type = $("cargoType").value;
  const use_ml = $("useMl").checked;
  const monthRaw = $("month").value;
  const month = monthRaw ? Number(monthRaw) : null;

  const payload = {
    origin,
    destination,
    mode,
    optimize_by,
    cargo_type,
    use_ml,
    month,
  };

  const r = await fetch("/api/route", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await r.json();
  if (!r.ok) {
    setStatus(data.detail || "Request failed", "danger");
    return;
  }

  await drawRouteOnMap(data);
  renderSegments(data);
  renderAlerts(data);
  renderCargoNotes(data);
  renderTotals(data);
  $("explanation").textContent = data.explanation || "";

  setStatus(data.used_ml ? "Used ML weight adjuster." : "ML not used.");
}

function init() {
  $("computeBtn").addEventListener("click", () => computeRoute());
  loadGraph().catch((e) => {
    console.error(e);
    setStatus("Failed to load graph.", "danger");
  });
  initMap();
}

init();

