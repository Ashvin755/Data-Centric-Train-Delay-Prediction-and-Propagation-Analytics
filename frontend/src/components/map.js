/**
 * map.js — Leaflet map with gradient route line & invisible hover markers
 *
 * Instead of individual dot markers, we draw thick colored polyline segments
 * between consecutive stations. Each segment is colored by the departure
 * delay at the "from" station, giving the appearance of a gradient stripe.
 * Invisible hit-area markers on each station still fire tooltip events.
 */
import { STATIONS } from '../data/stations.js';
import { TRAIN_18238 } from '../data/train_18238.js';
import { EventBus } from '../lib/eventbus.js';
import { showTooltip, moveTooltip, hideTooltip } from './tooltip.js';

let map = null;
/** Holds all removable layers: segment polylines + hit markers */
let layers = [];
/** Static base route polyline (very thin, dark background track) */
let basePolyline = null;

// ─── Color helpers ─────────────────────────────────────────────────────────────

function delayColor(minutes) {
  if (minutes === null || minutes === undefined) return '#94a3b8';
  if (minutes <= 0)  return '#22c55e';
  if (minutes <= 10) return '#facc15';
  if (minutes <= 30) return '#f97316';
  return '#ef4444';
}

/** Linearly interpolate between two hex colors by t ∈ [0,1] */
function lerpColor(hex1, hex2, t) {
  const parse = (h) => [
    parseInt(h.slice(1, 3), 16),
    parseInt(h.slice(3, 5), 16),
    parseInt(h.slice(5, 7), 16),
  ];
  const [r1, g1, b1] = parse(hex1);
  const [r2, g2, b2] = parse(hex2);
  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);
  return `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`;
}

// ─── Build route coords ────────────────────────────────────────────────────────

function buildRouteLatLngs() {
  return TRAIN_18238.route
    .filter(code => STATIONS[code])
    .map(code => [STATIONS[code].lat, STATIONS[code].lon]);
}

// ─── Init ─────────────────────────────────────────────────────────────────────

export function initMap() {
  map = L.map('leaflet-map', {
    zoomControl: true,
    attributionControl: true,
  });

  // CartoDB Positron — muted tiles so data colors pop
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    subdomains: 'abcd',
    maxZoom: 18,
  }).addTo(map);

  // Thin dark background track (always visible, shows the full route)
  const routeLatLngs = buildRouteLatLngs();
  basePolyline = L.polyline(routeLatLngs, {
    color: '#1a1a1a',
    weight: 7,
    opacity: 0.12,
    lineCap: 'round',
    lineJoin: 'round',
  }).addTo(map);

  map.fitBounds(basePolyline.getBounds(), { padding: [30, 30] });

  EventBus.on('journeyChange', renderGradientLine);

  const dates = Object.keys(TRAIN_18238.journeys).sort();
  renderGradientLine(dates[dates.length - 1]);
}

// ─── Clear ────────────────────────────────────────────────────────────────────

function clearLayers() {
  layers.forEach(l => map.removeLayer(l));
  layers = [];
}

// ─── Gradient line renderer ───────────────────────────────────────────────────

function renderGradientLine(date) {
  clearLayers();

  const journey = TRAIN_18238.journeys[date];
  if (!journey) return;

  // Build lookup: stationCode → row data
  const dataMap = {};
  journey.forEach(row => { dataMap[row.stationCode] = row; });

  const route = TRAIN_18238.route;

  // ── 1. Draw colored segments between consecutive stations ──────────────────
  //
  // For each pair (A→B) we draw a thick polyline.
  // We interpolate the color between A's delay color and B's delay color
  // by splitting the segment into ~5 sub-segments for a smooth gradient look.
  //
  const SUB_STEPS = 6; // number of sub-segments per station pair
  const LINE_WEIGHT = 6;

  for (let i = 0; i < route.length - 1; i++) {
    const fromCode = route[i];
    const toCode   = route[i + 1];

    const fromMeta = STATIONS[fromCode];
    const toMeta   = STATIONS[toCode];
    if (!fromMeta || !toMeta) continue;

    const fromRow = dataMap[fromCode];
    const toRow   = dataMap[toCode];

    const colorA = delayColor(fromRow ? fromRow.delayDeparture : null);
    const colorB = delayColor(toRow   ? toRow.delayDeparture   : null);

    // Interpolate sub-segments A→B
    for (let s = 0; s < SUB_STEPS; s++) {
      const t0 = s / SUB_STEPS;
      const t1 = (s + 1) / SUB_STEPS;

      const lat0 = fromMeta.lat + (toMeta.lat - fromMeta.lat) * t0;
      const lon0 = fromMeta.lon + (toMeta.lon - fromMeta.lon) * t0;
      const lat1 = fromMeta.lat + (toMeta.lat - fromMeta.lat) * t1;
      const lon1 = fromMeta.lon + (toMeta.lon - fromMeta.lon) * t1;

      const segColor = lerpColor(colorA, colorB, (t0 + t1) / 2);

      const seg = L.polyline([[lat0, lon0], [lat1, lon1]], {
        color: segColor,
        weight: LINE_WEIGHT,
        opacity: 0.92,
        lineCap: 'round',
        lineJoin: 'round',
        interactive: false, // don't intercept mouse on line
      }).addTo(map);

      layers.push(seg);
    }
  }

  // ── 2. Invisible hit-area markers on each station ─────────────────────────
  //
  // These are transparent large circles that capture hover events for
  // the tooltip. No visual presence — the gradient line is the visual.
  //
  const HIT_RADIUS = 8; // pixels

  route.forEach(code => {
    const stationMeta = STATIONS[code];
    if (!stationMeta) return;

    const row = dataMap[code] || null;

    const hitIcon = L.divIcon({
      className: '',
      html: `<div style="
        width:${HIT_RADIUS * 2}px;
        height:${HIT_RADIUS * 2}px;
        background:transparent;
        border-radius:50%;
        cursor:crosshair;
      "></div>`,
      iconSize: [HIT_RADIUS * 2, HIT_RADIUS * 2],
      iconAnchor: [HIT_RADIUS, HIT_RADIUS],
    });

    const hitMarker = L.marker([stationMeta.lat, stationMeta.lon], {
      icon: hitIcon,
      interactive: true,
      zIndexOffset: 500,
    });

    hitMarker.on('mouseover', (e) => {
      showTooltip(e.originalEvent, {
        code,
        name: stationMeta.name,
        delayArrival:        row ? row.delayArrival        : null,
        delayDeparture:      row ? row.delayDeparture      : null,
        scheduledArrival:    row ? row.scheduledArrival    : null,
        actualArrival:       row ? row.actualArrival       : null,
        scheduledDeparture:  row ? row.scheduledDeparture  : null,
        actualDeparture:     row ? row.actualDeparture     : null,
      });
    });

    hitMarker.on('mousemove', (e) => moveTooltip(e.originalEvent));
    hitMarker.on('mouseout', ()  => hideTooltip());

    hitMarker.addTo(map);
    layers.push(hitMarker);
  });
}
