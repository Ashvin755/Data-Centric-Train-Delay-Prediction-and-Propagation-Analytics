/**
 * tooltip.js — Custom station hover tooltip
 */

const tooltip = document.getElementById('station-tooltip');

/**
 * Format a Unix timestamp to IST time string
 */
function formatTime(unix) {
  if (!unix) return '—';
  const d = new Date(unix * 1000);
  return d.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Kolkata',
  });
}

/**
 * Get delay color and label
 */
function delayInfo(minutes) {
  if (minutes === null || minutes === undefined) {
    return { color: '#94a3b8', bg: '#f1f5f9', label: 'No data' };
  }
  if (minutes <= 0) return { color: '#15803d', bg: '#dcfce7', label: `${Math.abs(minutes)}m early` };
  if (minutes <= 10) return { color: '#92400e', bg: '#fef9c3', label: `+${minutes}m` };
  if (minutes <= 30) return { color: '#c2410c', bg: '#ffedd5', label: `+${minutes}m` };
  return { color: '#991b1b', bg: '#fee2e2', label: `+${minutes}m` };
}

/**
 * Show tooltip near an event position
 * @param {MouseEvent} e
 * @param {object} stationData - { code, name, delayArrival, delayDeparture, scheduledArrival, actualArrival, scheduledDeparture, actualDeparture }
 */
export function showTooltip(e, stationData) {
  const { code, name, status, delayArrival, delayDeparture,
          scheduledArrival, actualArrival,
          scheduledDeparture, actualDeparture } = stationData;

  const depInfo = delayInfo(delayDeparture);
  const arrInfo = delayInfo(delayArrival);

  let statusBadge = '';
  if (status === 'Current') {
    statusBadge = `<div class="tooltip-status-badge status-current">🔴 Train is Here</div>`;
  } else if (status === 'Passed') {
    statusBadge = `<div class="tooltip-status-badge status-passed">✓ Passed</div>`;
  } else if (status === 'Upcoming') {
    statusBadge = `<div class="tooltip-status-badge status-upcoming">⌛ Upcoming</div>`;
  }

  const arrLabel = status === 'Upcoming' ? 'Predicted Arr' : 'Actual Arr';
  const depLabel = status === 'Upcoming' ? 'Predicted Dep' : 'Actual Dep';

  tooltip.innerHTML = `
    <div class="tooltip-station-code">${code}</div>
    <div class="tooltip-station-name">${name}</div>
    ${statusBadge}
    <div class="tooltip-row">
      <span class="tooltip-row-label">Sched. Arr</span>
      <span class="tooltip-row-value">${formatTime(scheduledArrival)}</span>
    </div>
    <div class="tooltip-row">
      <span class="tooltip-row-label">${arrLabel}</span>
      <span class="tooltip-row-value">${formatTime(actualArrival)}</span>
    </div>
    <div class="tooltip-row">
      <span class="tooltip-row-label">Sched. Dep</span>
      <span class="tooltip-row-value">${formatTime(scheduledDeparture)}</span>
    </div>
    <div class="tooltip-row">
      <span class="tooltip-row-label">${depLabel}</span>
      <span class="tooltip-row-value">${formatTime(actualDeparture)}</span>
    </div>
    <div class="tooltip-row" style="margin-top:4px">
      <span class="tooltip-row-label">Arr Delay</span>
      <span class="tooltip-row-value" style="color:${arrInfo.color};font-weight:800">${delayArrival !== null ? (delayArrival > 0 ? '+' + delayArrival + 'm' : delayArrival + 'm') : '—'}</span>
    </div>
    <div class="tooltip-delay-badge" style="background:${depInfo.bg};color:${depInfo.color};border-color:${depInfo.color}">
      Dep Delay: ${depInfo.label}
    </div>
  `;

  positionTooltip(e);
  tooltip.setAttribute('aria-hidden', 'false');
  tooltip.classList.add('visible');
}

/**
 * Move tooltip to follow mouse
 */
export function moveTooltip(e) {
  positionTooltip(e);
}

/**
 * Hide tooltip
 */
export function hideTooltip() {
  tooltip.classList.remove('visible');
  tooltip.setAttribute('aria-hidden', 'true');
}

function positionTooltip(e) {
  const margin = 14;
  const tw = tooltip.offsetWidth || 220;
  const th = tooltip.offsetHeight || 160;
  let x = e.clientX + margin;
  let y = e.clientY + margin;

  if (x + tw > window.innerWidth - 10) x = e.clientX - tw - margin;
  if (y + th > window.innerHeight - 10) y = e.clientY - th - margin;

  tooltip.style.left = x + 'px';
  tooltip.style.top  = y + 'px';
}
