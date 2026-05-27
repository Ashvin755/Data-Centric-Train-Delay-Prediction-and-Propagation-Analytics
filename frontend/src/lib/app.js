/**
 * app.js — Application entry point
 *
 * Initializes all components and wires them together
 * via the shared event bus.
 */
import { EventBus } from './eventbus.js';
export { EventBus } from './eventbus.js';

export let currentTrainData = null;

// ─── App Init ─────────────────────────────────────────────────────────────────
import { initHeader } from '../components/header.js?v=2';
import { initMap } from '../components/map.js?v=2';
import { initCharts } from '../components/charts.js?v=2';
import { initAmplifiers } from '../components/amplifiers.js?v=2';

async function switchTrain(trainNo) {
  try {
    // Show loading state in the header badge
    document.getElementById('train-number-label').textContent = trainNo;
    document.getElementById('train-name-label').textContent = 'Loading...';
    document.getElementById('train-route-label').textContent = '';

    // 1. Fetch train metadata + available journey dates from Supabase via server proxy
    const res = await fetch(`/api/supabase/train/${trainNo}`);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.message || `Server returned status ${res.status} for train info.`);
    }

    const trainMeta = await res.json();

    // 2. Build the currentTrainData shell (journeys loaded lazily on demand)
    currentTrainData = {
      trainNumber: trainMeta.trainNumber,
      trainName: trainMeta.trainName,
      route: [],         // populated after first journey load
      journeys: {},      // filled lazily: { "YYYY-MM-DD": [...stations] }
      _journeyDates: trainMeta.journeyDates,   // ordered list of available dates from DB
    };

    // 3. Update header badge text
    document.getElementById('train-number-label').textContent = currentTrainData.trainNumber;
    document.getElementById('train-name-label').textContent = currentTrainData.trainName;
    document.getElementById('train-route-label').textContent = ''; // cleared until first journey loads

    // 4. Init sub-components with the shell data
    //    Pass a synthetic trainData that has journeys as an object keyed by dates
    //    so initHeader() can build the dropdown.
    initHeader(currentTrainData);
    initMap(currentTrainData);
    initCharts(currentTrainData);
    initAmplifiers(currentTrainData);

    // 5. Auto-select and load the most recent available date
    const input = document.getElementById('journey-date-picker');
    if (currentTrainData._journeyDates && currentTrainData._journeyDates.length > 0) {
      await loadJourneyData(currentTrainData._journeyDates[currentTrainData._journeyDates.length - 1]);
    }
  } catch (err) {
    console.error("Failed to load train data:", err);
    showToast(`Failed to load train ${trainNo}: ${err.message}`, 'error');
  }
}


async function init() {
  const trainSelect = document.getElementById('train-select');
  trainSelect.addEventListener('change', () => {
    switchTrain(trainSelect.value);
  });
  
  await switchTrain(trainSelect.value);

  // 5. Wire up input → dynamic loader
  const input = document.getElementById('journey-date-picker');
  input.addEventListener('change', () => {
    if (input.value) {
      loadJourneyData(input.value);
    }
  });

  // 6. Setup direct live tracking API integration
  setupLiveTracking();

  console.log('[RailDash] Initialized successfully');
}

// ─── Live Train Tracking & Notification Functions ─────────────────────────────

/**
 * Randomly adds or subtracts a value between 2 and 6 minutes (inclusive)
 * to the actual arrival and departure times, and updates the delay minutes.
 */
function perturbJourneyData(journey) {
  if (!journey) return;
  const nowSecs = Date.now() / 1000;
  
  journey.forEach(station => {
    // Check if station is in the future
    const isUpcoming = (station.actualArrival !== null && station.actualArrival > nowSecs) || 
                       (station.actualDeparture !== null && station.actualDeparture > nowSecs);
                       
    if (isUpcoming) {
      // 1. Perturb Arrival (Add 2 to 5 mins)
      if (station.actualArrival !== null && station.actualArrival !== undefined) {
        const deltaMinutes = Math.floor(Math.random() * 4) + 2;
        station.actualArrival += deltaMinutes * 60;
        if (station.delayArrival !== null && station.delayArrival !== undefined) {
          station.delayArrival += deltaMinutes;
        }
      }

      // 2. Perturb Departure (Add 2 to 5 mins)
      if (station.actualDeparture !== null && station.actualDeparture !== undefined) {
        const deltaMinutes = Math.floor(Math.random() * 4) + 2;
        station.actualDeparture += deltaMinutes * 60;
        if (station.delayDeparture !== null && station.delayDeparture !== undefined) {
          station.delayDeparture += deltaMinutes;
        }
      }
    }
  });
}

/**
 * Returns current date in Indian Standard Time (IST) in "YYYY-MM-DD" format.
 */
function getISTDate() {
  const d = new Date();
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
  return formatter.format(d);
}

/**
 * Displays a premium neo-brutalist toast alert notification popup.
 */
function showToast(message, type = 'success') {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = 'toast-notification';
    document.body.appendChild(toast);
  }
  
  toast.className = `toast-notification toast-${type}`;
  const icon = type === 'success' ? '✅' : '❌';
  toast.innerHTML = `<span class="toast-icon">${icon}</span><span>${message}</span>`;
  
  // Trigger transition
  toast.classList.add('show');
  
  // Hide after 3.5 seconds
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}

/**
 * Asynchronously loads a journey date.
 * - If already cached in memory, just re-emits.
 * - If the date is in the DB (listed in _journeyDates), fetches from Supabase via the server proxy.
 * - Falls back to the last successfully loaded journey on error.
 */
async function loadJourneyData(date) {
  // If data already cached, simply re-notify components
  if (currentTrainData.journeys[date] && currentTrainData.journeys[date].length > 0) {
    EventBus.emit('journeyChange', date);
    return;
  }

  const input = document.getElementById('journey-date-picker');
  const liveBtn = document.getElementById('live-tracking-btn');

  // Put UI into loading state
  if (liveBtn) {
    liveBtn.classList.add('loading');
    liveBtn.disabled = true;
    liveBtn.textContent = 'Fetching...';
  }

  try {
    const isDbDate = currentTrainData._journeyDates && currentTrainData._journeyDates.includes(date);

    let formattedJourney;

    if (isDbDate) {
      // ── Supabase DB fetch (historical data) ───────────────────────────────
      showToast(`Loading journey data for ${date}...`, 'success');
      console.log(`[DB] Fetching journey for train ${currentTrainData.trainNumber} on ${date}...`);

      const response = await fetch(`/api/supabase/journey/${currentTrainData.trainNumber}/${date}`);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.message || `Server returned status ${response.status}.`);
      }

      const resData = await response.json();
      formattedJourney = resData.journey;

      if (!formattedJourney || formattedJourney.length === 0) {
        throw new Error('No station data returned from database.');
      }

    } else {
      // ── RailRadar live fetch (for today / non-DB dates) ───────────────────
      showToast(`Fetching live data for ${date}...`, 'success');
      console.log(`[Live] Fetching live data for date ${date} via proxy...`);

      const response = await fetch(`/api/live?journeyDate=${date}&trainNo=${currentTrainData.trainNumber}`);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.message || `Server returned status ${response.status}.`);
      }

      const resData = await response.json();
      formattedJourney = resData.journey;

      if (!formattedJourney || formattedJourney.length === 0) {
        throw new Error('No tracking route points returned.');
      }

      // Perturb only live/future data
      perturbJourneyData(formattedJourney);
    }

    // Derive route array from station codes on first load
    if (currentTrainData.route.length === 0 && formattedJourney && formattedJourney.length > 0) {
      currentTrainData.route = formattedJourney.map(s => s.stationCode);
      // Update the route label now that we have a route
      const rt = currentTrainData.route;
      document.getElementById('train-route-label').textContent = `${rt[0]} → ${rt[rt.length - 1]}`;
    }

    // Cache and notify
    currentTrainData.journeys[date] = formattedJourney;
    EventBus.emit('journeyChange', date);
    showToast(`Loaded journey for ${date}!`, 'success');

  } catch (err) {
    console.error(err);
    showToast(err.message || `Could not load data for ${date}.`, 'error');

    // Revert to the last successfully loaded journey
    const validDates = Object.keys(currentTrainData.journeys).filter(
      d => currentTrainData.journeys[d] && currentTrainData.journeys[d].length > 0
    );
    if (validDates.length > 0) {
      const lastValid = validDates[validDates.length - 1];
      if (input._flatpickr) {
        input._flatpickr.setDate(lastValid, false);
      }
      EventBus.emit('journeyChange', lastValid);
    }
  } finally {
    if (liveBtn) {
      liveBtn.classList.remove('loading');
      liveBtn.disabled = false;
      liveBtn.innerHTML = `<span class="live-pulse"></span>Live Tracking`;
    }
  }
}


/**
 * Attaches the click listener for the Live Tracking button to call our local proxy endpoint
 */
function setupLiveTracking() {
  const liveBtn = document.getElementById('live-tracking-btn');
  const input = document.getElementById('journey-date-picker');
  if (!liveBtn) return;

  liveBtn.addEventListener('click', async () => {
    // Show premium loading state
    liveBtn.classList.add('loading');
    liveBtn.disabled = true;
    liveBtn.textContent = 'Connecting...';

    try {
      console.log('[Live Tracking] Fetching live data via local server proxy...');
      
      const response = await fetch(`/api/live?trainNo=${currentTrainData.trainNumber}`);
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.message || `Server returned status ${response.status}.`);
      }
      
      const resData = await response.json();
      const journeyDate = resData.date;
      const formattedJourney = resData.journey;
      
      if (!formattedJourney || formattedJourney.length === 0) {
        throw new Error('No tracking route points returned.');
      }
      
      // Perturb the freshly fetched live journey
      perturbJourneyData(formattedJourney);

      // Dynamic loading into the global dataset
      currentTrainData.journeys[journeyDate] = formattedJourney;
      
      // Update the flatpickr picker with the live date if it wasn't there
      if (input._flatpickr) {
        const enabledDates = input._flatpickr.config.enable || [];
        const exists = enabledDates.some(d => {
          if (typeof d === 'string') return d === journeyDate;
          if (d instanceof Date) return flatpickr.formatDate(d, 'Y-m-d') === journeyDate;
          return false;
        });
        
        if (!exists) {
          enabledDates.push(journeyDate);
          input._flatpickr.set('enable', enabledDates);
        }
        
        input._flatpickr.setDate(journeyDate, false);
      }
      
      // Notify map, charts, stats, and widgets
      EventBus.emit('journeyChange', journeyDate);
      
      showToast('Live tracking active!', 'success');
      
    } catch (err) {
      console.error(err);
      showToast(err.message || 'Could not connect to live train tracker.', 'error');
    } finally {
      // Revert loading state
      liveBtn.classList.remove('loading');
      liveBtn.disabled = false;
      liveBtn.innerHTML = `<span class="live-pulse"></span>Live Tracking`;
    }
  });
}

// Run after DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
