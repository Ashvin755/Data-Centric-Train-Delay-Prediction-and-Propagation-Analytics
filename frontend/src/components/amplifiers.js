import { STATIONS } from '../data/stations.js';
import { EventBus } from '../lib/eventbus.js';

let currentTrainData = null;
let isEventBusAttached = false;

export function initAmplifiers(trainData) {
  currentTrainData = trainData;
  const widget = document.getElementById('delay-amplifiers-widget');
  const minimizeBtn = document.getElementById('widget-minimize-btn');
  const header = document.querySelector('.widget-header');

  if (!widget) return;

  // Prevent Leaflet map from panning when interacting with widget
  if (window.L && L.DomEvent) {
    L.DomEvent.disableClickPropagation(widget);
    L.DomEvent.disableScrollPropagation(widget);
  } else {
    // Fallback if L isn't ready
    widget.addEventListener('mousedown', e => e.stopPropagation());
    widget.addEventListener('wheel', e => e.stopPropagation());
    widget.addEventListener('dblclick', e => e.stopPropagation());
  }

  // Minimize toggle
  // Avoid attaching multiple times
  if (!widget.dataset.initialized) {
    minimizeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      widget.classList.toggle('minimized');
      minimizeBtn.textContent = widget.classList.contains('minimized') ? '+' : '−';
    });

    // Drag logic
    let isDragging = false;
    let startX, startY, initialLeft, initialTop;

    header.addEventListener('mousedown', (e) => {
      if (e.target.id === 'widget-minimize-btn') return;
      
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      
      const rect = widget.getBoundingClientRect();
      const parentRect = widget.parentElement.getBoundingClientRect();
      
      initialLeft = rect.left - parentRect.left;
      initialTop = rect.top - parentRect.top;
      
      // Switch to explicit left/top positioning for dragging
      widget.style.right = 'auto';
      widget.style.left = initialLeft + 'px';
      widget.style.top = initialTop + 'px';
      
      header.style.cursor = 'grabbing';
      e.preventDefault(); // prevent text selection
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      widget.style.left = (initialLeft + dx) + 'px';
      widget.style.top = (initialTop + dy) + 'px';
    });

    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        header.style.cursor = 'grab';
      }
    });

    widget.dataset.initialized = "true";
  }

  if (!isEventBusAttached) {
    EventBus.on('journeyChange', updateAmplifiers);
    isEventBusAttached = true;
  }

  // Initialize with the latest journey date
  const dates = Object.keys(currentTrainData.journeys).sort();
  if (dates.length > 0) {
    updateAmplifiers(dates[dates.length - 1]);
  }
}

function updateAmplifiers(date) {
  if (!currentTrainData) return;
  const journey = currentTrainData.journeys[date];
  if (!journey) return;
  
  const dataMap = {};
  journey.forEach(r => { dataMap[r.stationCode] = r; });
  
  const route = currentTrainData.route;
  const alphas = [];
  
  for (let i = 0; i < route.length - 1; i++) {
    const fromCode = route[i];
    const toCode = route[i + 1];
    const fromRow = dataMap[fromCode];
    const toRow = dataMap[toCode];
    
    if (fromRow && toRow && fromRow.delayDeparture !== null && toRow.delayDeparture !== null) {
      // Alpha = delay added between fromCode and toCode
      const alpha = toRow.delayDeparture - fromRow.delayDeparture;
      if (alpha > 0) {
        alphas.push({
          stationCode: toCode,
          stationName: STATIONS[toCode]?.name || toCode,
          alpha: alpha
        });
      }
    }
  }
  
  // Sort descending by delay added
  alphas.sort((a, b) => b.alpha - a.alpha);
  
  // Take top 3
  const top3 = alphas.slice(0, 3);
  
  const list = document.getElementById('amplifier-list');
  list.innerHTML = '';
  
  if (top3.length === 0) {
    list.innerHTML = '<li class="amp-empty">No delays added on this journey!</li>';
    return;
  }
  
  // Normalize impact score relative to the worst segment (or at least 15 mins to avoid 100/100 for tiny delays)
  const maxAlpha = alphas[0].alpha;
  
  top3.forEach((item, index) => {
    const score = Math.round((item.alpha / Math.max(15, maxAlpha)) * 100);
    const scoreClamped = Math.min(100, score);
    
    // Assign color class based on severity
    let colorClass = 'low'; // yellow
    if (item.alpha >= 15) colorClass = 'high'; // red
    else if (item.alpha >= 8) colorClass = 'med'; // orange
    
    const li = document.createElement('li');
    li.className = 'amp-item';
    li.innerHTML = `
      <div class="amp-rank">${index + 1}</div>
      <div class="amp-details">
        <div class="amp-station-name">${item.stationName} (${item.stationCode})</div>
        <div class="amp-impact">Impact Score: ${scoreClamped}/100</div>
      </div>
      <div class="amp-delay ${colorClass}">+${item.alpha} mins</div>
    `;
    list.appendChild(li);
  });
}
