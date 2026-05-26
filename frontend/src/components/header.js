/**
 * header.js — Train badge & journey date selector
 */
import { EventBus } from '../lib/eventbus.js';

let currentTrainData = null;
let isEventBusAttached = false;

/**
 * Populate the journey date dropdown
 */
export function initHeader(trainData) {
  currentTrainData = trainData;
  const journeyDates = Object.keys(currentTrainData.journeys).sort();
  const select = document.getElementById('journey-date-select');
  
  select.innerHTML = '';

  journeyDates.forEach(date => {
    const opt = document.createElement('option');
    opt.value = date;
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
  if (journeyDates.length > 0) {
    select.value = journeyDates[journeyDates.length - 1];
    updateStats(select.value);
  } else {
    updateStats(null);
  }

  if (!isEventBusAttached) {
    EventBus.on('journeyChange', (date) => {
      updateStats(date);
    });
    isEventBusAttached = true;
  }
}

/**
 * Update header stat chips for a journey date
 */
function updateStats(date) {
  if (!currentTrainData || !date) return;
  const journey = currentTrainData.journeys[date];
  if (!journey) return;

  const delays = journey
    .map(s => s.delayDeparture)
    .filter(d => d !== null && d !== undefined);

  const maxDelay = delays.length ? Math.max(...delays) : null;
  const avgDelay = delays.length ? (delays.reduce((a, b) => a + b, 0) / delays.length) : null;
  const onTimePct = delays.length
    ? Math.round((delays.filter(d => d <= 5).length / delays.length) * 100)
    : null;

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

  const totalRoute = currentTrainData.route.length;
  document.getElementById('val-stations').textContent =
    `${journey.length}/${totalRoute}`;
}

/**
 * Get currently selected date
 */
export function getSelectedDate() {
  return document.getElementById('journey-date-select').value;
}
