/**
 * charts.js — Three Chart.js panels:
 *   A) Delay Profile (line chart)
 *   B) Delay Distribution (bar/histogram)
 *   C) Segment Alpha (bar chart)
 */
import { TRAIN_18238 } from '../data/train_18238.js';
import { EventBus } from '../lib/eventbus.js';

// ─── Shared Config ────────────────────────────────────────────────────────────
const FONT = "'Space Grotesk', system-ui, sans-serif";
const BORDER = '#1a1a1a';
const MUTED = '#94a3b8';

Chart.defaults.font.family = FONT;
Chart.defaults.color = '#555555';
Chart.defaults.borderColor = '#e5e7eb';

// ─── Instances ────────────────────────────────────────────────────────────────
let chartProfile = null;
let chartDist = null;
let chartAlpha = null;

// ─── Delay Color Helpers ──────────────────────────────────────────────────────
function delayColor(minutes) {
  if (minutes === null || minutes === undefined) return MUTED;
  if (minutes <= 0)  return '#22c55e';
  if (minutes <= 10) return '#facc15';
  if (minutes <= 30) return '#f97316';
  return '#ef4444';
}

function delayColorArr(arr) {
  return arr.map(delayColor);
}

// ─── Chart A: Departure Delay Profile ─────────────────────────────────────────
function buildProfileData(date) {
  const journey = TRAIN_18238.journeys[date] || [];
  const dataMap = {};
  journey.forEach(r => { dataMap[r.stationCode] = r; });

  const labels = [];
  const delays = [];
  const colors = [];

  TRAIN_18238.route.forEach(code => {
    const row = dataMap[code];
    const d = row ? row.delayDeparture : null;
    labels.push(code);
    delays.push(d);
    colors.push(delayColor(d));
  });

  return { labels, delays, colors };
}

function initProfileChart(date) {
  const ctx = document.getElementById('chart-profile').getContext('2d');
  const { labels, delays, colors } = buildProfileData(date);

  chartProfile = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Dep Delay (min)',
        data: delays,
        backgroundColor: colors,
        borderColor: colors.map(c => c === MUTED ? '#cbd5e1' : '#1a1a1a'),
        borderWidth: 1,
        borderRadius: 2,
        barThickness: 'flex',
        minBarLength: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const code = items[0].label;
              return code;
            },
            label: (item) => {
              const v = item.raw;
              if (v === null || v === undefined) return 'No data';
              return `Dep Delay: ${v > 0 ? '+' : ''}${v} min`;
            },
          },
          titleFont: { weight: '800', size: 13 },
          bodyFont: { size: 12 },
          backgroundColor: '#fff',
          titleColor: '#1a1a1a',
          bodyColor: '#555',
          borderColor: BORDER,
          borderWidth: 1.5,
          cornerRadius: 3,
          padding: 8,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { size: 8, weight: '600' },
            maxRotation: 90,
            autoSkip: true,
            maxTicksLimit: 30,
            color: '#888',
          },
        },
        y: {
          grid: { color: '#f0f0f0' },
          ticks: { font: { size: 10 }, color: '#888' },
          title: {
            display: true,
            text: 'Minutes',
            font: { size: 10, weight: '700' },
            color: '#888',
          },
        },
      },
    },
  });

  // Reference lines as plugin
  addThresholdPlugin(chartProfile);
}

function updateProfileChart(date) {
  if (!chartProfile) return;
  const { labels, delays, colors } = buildProfileData(date);
  chartProfile.data.labels = labels;
  chartProfile.data.datasets[0].data = delays;
  chartProfile.data.datasets[0].backgroundColor = colors;
  chartProfile.data.datasets[0].borderColor = colors.map(c => c === MUTED ? '#cbd5e1' : '#1a1a1a');
  chartProfile.update('active');
}

// ─── Chart B: Delay Distribution ──────────────────────────────────────────────
const BRACKETS = [
  { label: 'Early',   min: -Infinity, max: 0,   color: '#22c55e' },
  { label: '0–5m',    min: 0,         max: 5,   color: '#86efac' },
  { label: '5–10m',   min: 5,         max: 10,  color: '#facc15' },
  { label: '10–20m',  min: 10,        max: 20,  color: '#fb923c' },
  { label: '20–30m',  min: 20,        max: 30,  color: '#f97316' },
  { label: '30–60m',  min: 30,        max: 60,  color: '#ef4444' },
  { label: '60m+',    min: 60,        max: Infinity, color: '#991b1b' },
];

function buildDistData(date) {
  const journey = TRAIN_18238.journeys[date] || [];
  const delays = journey.map(r => r.delayDeparture).filter(d => d !== null && d !== undefined);

  const counts = BRACKETS.map(b => ({
    label: b.label,
    count: delays.filter(d => d >= b.min && d < b.max).length,
    color: b.color,
  }));

  return {
    labels: counts.map(c => c.label),
    data: counts.map(c => c.count),
    colors: counts.map(c => c.color),
  };
}

function initDistChart(date) {
  const ctx = document.getElementById('chart-distribution').getContext('2d');
  const { labels, data, colors } = buildDistData(date);

  chartDist = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Stations',
        data,
        backgroundColor: colors,
        borderColor: BORDER,
        borderWidth: 1.5,
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `${item.raw} station${item.raw !== 1 ? 's' : ''}`,
          },
          backgroundColor: '#fff',
          titleColor: '#1a1a1a',
          bodyColor: '#555',
          borderColor: BORDER,
          borderWidth: 1.5,
          cornerRadius: 3,
          padding: 8,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10, weight: '700' } },
        },
        y: {
          grid: { color: '#f0f0f0' },
          ticks: {
            font: { size: 10 },
            stepSize: 1,
            precision: 0,
          },
          title: {
            display: true,
            text: 'Stations',
            font: { size: 10, weight: '700' },
            color: '#888',
          },
        },
      },
    },
  });
}

function updateDistChart(date) {
  if (!chartDist) return;
  const { labels, data, colors } = buildDistData(date);
  chartDist.data.labels = labels;
  chartDist.data.datasets[0].data = data;
  chartDist.data.datasets[0].backgroundColor = colors;
  chartDist.update('active');
}

// ─── Chart C: Segment Alpha ───────────────────────────────────────────────────
function buildAlphaData(date) {
  const journey = TRAIN_18238.journeys[date] || [];
  const dataMap = {};
  journey.forEach(r => { dataMap[r.stationCode] = r; });

  const labels = [];
  const alphas = [];
  const colors = [];

  const route = TRAIN_18238.route;
  for (let i = 0; i < route.length - 1; i++) {
    const fromCode = route[i];
    const toCode = route[i + 1];
    const fromRow = dataMap[fromCode];
    const toRow = dataMap[toCode];

    if (fromRow && toRow &&
        fromRow.delayDeparture !== null && fromRow.delayDeparture !== undefined &&
        toRow.delayDeparture !== null && toRow.delayDeparture !== undefined) {
      const alpha = toRow.delayDeparture - fromRow.delayDeparture;
      labels.push(`${fromCode}→${toCode}`);
      alphas.push(alpha);
      colors.push(alpha >= 0 ? '#ef4444' : '#22c55e');
    }
  }

  return { labels, alphas, colors };
}

function initAlphaChart(date) {
  const ctx = document.getElementById('chart-alpha').getContext('2d');
  const { labels, alphas, colors } = buildAlphaData(date);

  chartAlpha = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Alpha (min)',
        data: alphas,
        backgroundColor: colors,
        borderColor: colors.map(c => c === '#ef4444' ? '#991b1b' : '#15803d'),
        borderWidth: 1,
        borderRadius: 2,
        barThickness: 'flex',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => items[0].label,
            label: (item) => {
              const v = item.raw;
              return v >= 0 ? `+${v} min (adds delay)` : `${v} min (covers up)`;
            },
          },
          backgroundColor: '#fff',
          titleColor: '#1a1a1a',
          bodyColor: '#555',
          borderColor: BORDER,
          borderWidth: 1.5,
          cornerRadius: 3,
          padding: 8,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { size: 7, weight: '600' },
            maxRotation: 90,
            autoSkip: true,
            maxTicksLimit: 25,
            color: '#aaa',
          },
        },
        y: {
          grid: { color: '#f0f0f0' },
          ticks: { font: { size: 10 }, color: '#888' },
          title: {
            display: true,
            text: 'Δ Delay (min)',
            font: { size: 10, weight: '700' },
            color: '#888',
          },
        },
      },
    },
  });

  addZeroLinePlugin(chartAlpha);
}

function updateAlphaChart(date) {
  if (!chartAlpha) return;
  const { labels, alphas, colors } = buildAlphaData(date);
  chartAlpha.data.labels = labels;
  chartAlpha.data.datasets[0].data = alphas;
  chartAlpha.data.datasets[0].backgroundColor = colors;
  chartAlpha.data.datasets[0].borderColor = colors.map(c => c === '#ef4444' ? '#991b1b' : '#15803d');
  chartAlpha.update('active');
}

// ─── Plugins ──────────────────────────────────────────────────────────────────

/** Zero-line plugin for alpha chart */
function addZeroLinePlugin(chart) {
  // Use annotation via custom afterDraw to avoid needing the plugin
  const zeroLinePlugin = {
    id: 'zeroLine',
    afterDraw(chart) {
      const { ctx, scales: { y }, chartArea: { left, right } } = chart;
      if (!y) return;
      const yPos = y.getPixelForValue(0);
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(left, yPos);
      ctx.lineTo(right, yPos);
      ctx.strokeStyle = '#1a1a1a';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.restore();
    },
  };
  chart.options.plugins.zeroLine = {};
  Chart.register(zeroLinePlugin);
  chart.update();
}

/** Threshold lines for profile chart (+10, +30) */
function addThresholdPlugin(chart) {
  const threshPlugin = {
    id: 'threshLines',
    afterDraw(c) {
      const { ctx, scales: { y }, chartArea: { left, right } } = c;
      if (!y) return;
      const draw = (val, color, dash, label) => {
        const yPos = y.getPixelForValue(val);
        if (yPos < c.chartArea.top || yPos > c.chartArea.bottom) return;
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(left, yPos);
        ctx.lineTo(right, yPos);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.setLineDash(dash);
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.font = '600 9px ' + FONT;
        ctx.fillText(label, right - 2, yPos - 3);
        ctx.restore();
      };
      draw(0,  '#22c55e', [3, 3], 'on time');
      draw(10, '#f97316', [4, 4], '+10m');
      draw(30, '#ef4444', [4, 4], '+30m');
    },
  };
  Chart.register(threshPlugin);
  chart.update();
}

// ─── Public Init ──────────────────────────────────────────────────────────────
export function initCharts() {
  const dates = Object.keys(TRAIN_18238.journeys).sort();
  const initialDate = dates[dates.length - 1];

  initProfileChart(initialDate);
  initDistChart(initialDate);
  initAlphaChart(initialDate);

  EventBus.on('journeyChange', (date) => {
    updateProfileChart(date);
    updateDistChart(date);
    updateAlphaChart(date);
  });
}
