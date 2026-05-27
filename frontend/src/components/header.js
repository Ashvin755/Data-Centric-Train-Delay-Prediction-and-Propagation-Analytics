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
  // Use _journeyDates from the DB response (journeys map starts empty until lazy-loaded)
  const journeyDates = (currentTrainData._journeyDates || Object.keys(currentTrainData.journeys)).slice().sort();
  const input = document.getElementById('journey-date-picker');

  // Destroy existing flatpickr instance if we switch trains
  if (input._flatpickr) {
    input._flatpickr.destroy();
  }

  // Initialize Flatpickr calendar
  flatpickr(input, {
    dateFormat: "Y-m-d",
    altInput: true,
    altFormat: "D, j M, Y",
    enable: journeyDates.length > 0 ? journeyDates : [new Date()],
    minDate: "2026-01-17",
    defaultDate: journeyDates.length > 0 ? journeyDates[journeyDates.length - 1] : null,
    disableMobile: true, // Uses our custom CSS instead of native mobile pickers
    onDayCreate: function(dObj, dStr, fp, dayElem) {
      if (!dayElem.dateObj) return;
      
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const diffTime = today.getTime() - dayElem.dateObj.getTime();
      const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays >= -1 && diffDays <= 4) {
        // Only add pulse if this date is actually enabled (has journeys)
        if (!dayElem.classList.contains('flatpickr-disabled')) {
           dayElem.innerHTML += '<span class="live-pulse calendar-live-dot"></span>';
        }
      }
    }
  });

  // Default to the most recent date (dropdown auto-populated from DB dates)
  if (journeyDates.length > 0) {
    updateStats(journeyDates[journeyDates.length - 1]);
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
