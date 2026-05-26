/**
 * header.js — Train badge & journey date selector
 */
import { TRAIN_18238 } from '../data/train_18238.js';
import { EventBus } from '../lib/eventbus.js';

const journeyDates = Object.keys(TRAIN_18238.journeys).sort();

/**
 * Populate the journey date dropdown
 */
export function initHeader() {
  const select = document.getElementById('journey-date-select');

  journeyDates.forEach(date => {
    const opt = document.createElement('option');
    opt.value = date;
    // Format: "Fri, 17 Jan 2026"
    const d = new Date(date + 'T00:00:00');
    opt.textContent = d.toLocaleDateString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
    });
    select.appendChild(opt);
  });

  // Add the dynamic option for 26th May 2026 (Live API Data)
  const opt26 = document.createElement('option');
  opt26.value = '2026-05-26';
  const d26 = new Date('2026-05-26T00:00:00');
  opt26.textContent = `🔴 Live: ${d26.toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric'
  })}`;
  select.appendChild(opt26);

  // Default to the most recent date
  select.value = journeyDates[journeyDates.length - 1];

  select.addEventListener('change', () => {
    // Note: The main listener in app.js will handle fetching if necessary.
    // We only emit here as a fallback/safety net for pre-loaded dates.
    if (TRAIN_18238.journeys[select.value]) {
      EventBus.emit('journeyChange', select.value);
    }
  });

  // Initial stats
  updateStats(select.value);

  EventBus.on('journeyChange', (date) => {
    updateStats(date);
  });
}

/**
 * Update header stat chips for a journey date
 */
function updateStats(date) {
  const journey = TRAIN_18238.journeys[date];
  if (!journey) return;

  const delays = journey
    .map(s => s.delayDeparture)
    .filter(d => d !== null && d !== undefined);

  const maxDelay = delays.length ? Math.max(...delays) : null;
  const avgDelay = delays.length ? (delays.reduce((a, b) => a + b, 0) / delays.length) : null;
  const onTimePct = delays.length
    ? Math.round((delays.filter(d => d <= 5).length / delays.length) * 100)
    : null;

  // Delay Recovery = Max Delay - Delay of the last station (BSP)
  const lastStation = journey[journey.length - 1];
  const lastStationDelay = lastStation
    ? (lastStation.delayArrival !== null ? lastStation.delayArrival : lastStation.delayDeparture)
    : null;
  const delayRecovery = (maxDelay !== null && lastStationDelay !== null)
    ? Math.max(0, maxDelay - lastStationDelay)
    : null;

  document.getElementById('val-max-delay').textContent =
    maxDelay !== null ? `${maxDelay > 0 ? '+' : ''}${Math.round(maxDelay)}m` : '—';

  document.getElementById('val-avg-delay').textContent =
    avgDelay !== null ? `${avgDelay > 0 ? '+' : ''}${Math.round(avgDelay)}m` : '—';

  document.getElementById('val-on-time').textContent =
    onTimePct !== null ? `${onTimePct}%` : '—';

  document.getElementById('val-recovery').textContent =
    delayRecovery !== null ? `${delayRecovery > 0 ? '+' : ''}${Math.round(delayRecovery)}m` : '—';

  document.getElementById('val-stations').textContent =
    `${journey.length}/85`;
}

/**
 * Get currently selected date
 */
export function getSelectedDate() {
  return document.getElementById('journey-date-select').value;
}
