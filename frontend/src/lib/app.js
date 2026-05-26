/**
 * app.js — Application entry point
 *
 * Initializes all components and wires them together
 * via the shared event bus.
 */
import { EventBus } from './eventbus.js';
export { EventBus } from './eventbus.js';

// ─── App Init ─────────────────────────────────────────────────────────────────
import { initHeader } from '../components/header.js';
import { initMap } from '../components/map.js';
import { initCharts } from '../components/charts.js';

function init() {
  // 1. Header (populates select + stats)
  initHeader();

  // 2. Map (Leaflet + markers)
  initMap();

  // 3. Charts (Chart.js)
  initCharts();

  // 4. Wire up select → event bus (header.js also does this, safety net)
  const select = document.getElementById('journey-date-select');
  select.addEventListener('change', () => {
    EventBus.emit('journeyChange', select.value);
  });

  console.log('[RailDash] Initialized successfully');
}

// Run after DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
