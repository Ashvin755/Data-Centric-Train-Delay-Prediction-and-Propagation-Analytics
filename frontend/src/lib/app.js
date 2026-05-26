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
import { initHeader } from '../components/header.js';
import { initMap } from '../components/map.js';
import { initCharts } from '../components/charts.js';
import { initAmplifiers } from '../components/amplifiers.js';

async function switchTrain(trainNo) {
  try {
    const module = await import(`../data/train_${trainNo}.js`);
    currentTrainData = module[`TRAIN_${trainNo}`];
    
    // Perturb all initial static journeys
    Object.keys(currentTrainData.journeys).forEach(date => {
      perturbJourneyData(currentTrainData.journeys[date]);
    });

    // Update Header Text
    document.getElementById('train-number-label').textContent = currentTrainData.trainNumber;
    document.getElementById('train-name-label').textContent = currentTrainData.trainName;
    const rt = currentTrainData.route;
    document.getElementById('train-route-label').textContent = `${rt[0]} → ${rt[rt.length - 1]}`;

    // 1. Header (populates select + stats)
    initHeader(currentTrainData);

    // 2. Map (Leaflet + markers)
    initMap(currentTrainData);

    // 3. Charts (Chart.js)
    initCharts(currentTrainData);

    // 4. Delay Amplifiers Widget
    initAmplifiers(currentTrainData);
    
    // Trigger initial load for the last available date in the newly populated dropdown
    const select = document.getElementById('journey-date-select');
    if (select.options.length > 0) {
      select.value = select.options[select.options.length - 1].value;
      loadJourneyData(select.value);
    }
  } catch (err) {
    console.error("Failed to load train data:", err);
    showToast(`Failed to load train ${trainNo}`, 'error');
  }
}

async function init() {
  const trainSelect = document.getElementById('train-select');
  trainSelect.addEventListener('change', () => {
    switchTrain(trainSelect.value);
  });
  
  await switchTrain(trainSelect.value);

  // 5. Wire up select → dynamic loader
  const select = document.getElementById('journey-date-select');
  select.addEventListener('change', () => {
    loadJourneyData(select.value);
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
 * Asynchronously loads a journey date. If it's not already in memory, fetches it from proxy.
 */
async function loadJourneyData(date) {
  // If data already exists, simply notify components
  if (currentTrainData.journeys[date] && currentTrainData.journeys[date].length > 0) {
    EventBus.emit('journeyChange', date);
    return;
  }

  const select = document.getElementById('journey-date-select');
  const liveBtn = document.getElementById('live-tracking-btn');

  // Put UI into loading state
  if (liveBtn) {
    liveBtn.classList.add('loading');
    liveBtn.disabled = true;
    liveBtn.textContent = 'Fetching...';
  }

  try {
    showToast(`Fetching live data for ${date}...`, 'success');
    console.log(`[Live Tracking] Fetching live data for date ${date} via proxy...`);
    
    const response = await fetch(`/api/live?journeyDate=${date}&trainNo=${currentTrainData.trainNumber}`);
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.message || `Server returned status ${response.status}.`);
    }
    
    const resData = await response.json();
    const formattedJourney = resData.journey;
    
    if (!formattedJourney || formattedJourney.length === 0) {
      throw new Error('No tracking route points returned.');
    }
    
    // Perturb the freshly fetched dynamic journey
    perturbJourneyData(formattedJourney);

    // Dynamic loading into the global dataset
    currentTrainData.journeys[date] = formattedJourney;
    
    // Notify map, charts, stats, and widgets
    EventBus.emit('journeyChange', date);
    showToast(`Loaded journey for ${date}!`, 'success');
  } catch (err) {
    console.error(err);
    showToast(err.message || `Could not fetch live data for ${date}.`, 'error');
    
    // Falling back to the last valid static option in the dropdown list
    const validDates = Object.keys(currentTrainData.journeys).filter(d => currentTrainData.journeys[d] && currentTrainData.journeys[d].length > 0);
    if (validDates.length > 0) {
      select.value = validDates[validDates.length - 1];
      EventBus.emit('journeyChange', select.value);
    }
  } finally {
    // Revert loading state
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
  const select = document.getElementById('journey-date-select');
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
      
      // Add selection option if not already in dropdown selector
      let optExists = false;
      for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value === journeyDate) {
          optExists = true;
          break;
        }
      }
      
      if (!optExists) {
        const opt = document.createElement('option');
        opt.value = journeyDate;
        const d = new Date(journeyDate + 'T00:00:00');
        opt.textContent = `🔴 Live: ${d.toLocaleDateString('en-IN', {
          day: 'numeric', month: 'short', year: 'numeric'
        })}`;
        select.appendChild(opt);
      }
      
      select.value = journeyDate;
      
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
