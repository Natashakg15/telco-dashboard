/* Shared date/format/chart helpers for the static telco-dashboard-web rebuild.
   Pairs with assets/spot-ci.css. Every page's inline <script> reuses these instead
   of re-deriving date math / Plotly boilerplate per page. */

const PALETTE = {
  hypermint: '#13f460', sonicBlue: '#2d40e9', ultraviolet: '#52bec0',
  highvolt: '#f44610', zeroWhite: '#12141a', surface1: '#ffffff', border: '#e3e5ea',
};
const CHART_PALETTE = [PALETTE.highvolt, PALETTE.hypermint, PALETTE.sonicBlue, PALETTE.ultraviolet, '#a0a0a0'];
const DAY_MS = 86400000;

function toDate(s) { return new Date(s + 'T00:00:00Z'); }
function dateStr(d) { return d.toISOString().slice(0, 10); }
function addDays(d, n) { return new Date(d.getTime() + n * DAY_MS); }
function fmtDay(d) { return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' }); }
function fmtDayName(d) { return d.toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', timeZone: 'UTC' }); }
function fmtMonth(d) { return d.toLocaleDateString('en-GB', { month: 'short', year: '2-digit', timeZone: 'UTC' }).replace(' ', " '"); }
function fmtMonthLong(d) { return d.toLocaleDateString('en-GB', { month: 'long', year: 'numeric', timeZone: 'UTC' }); }
function fmtWeek(d) { return "Wk " + fmtDay(d) + " '" + String(d.getUTCFullYear()).slice(2); }
function fmtNum(n) { return Math.round(n).toLocaleString('en-US'); }
function fmtPct(n, decimals) { return (n * 100).toFixed(decimals == null ? 1 : decimals) + '%'; }
function fmtCurrency(n) { return 'R' + fmtNum(n); }

function mondayOf(d) {
  const dow = d.getUTCDay(); // 0=Sun..6=Sat
  const diff = (dow === 0 ? -6 : 1 - dow);
  return addDays(d, diff);
}
function monthStart(d) { return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1)); }

function denseDateRange(dateStrs) {
  const dates = dateStrs.map(toDate).sort((a, b) => a - b);
  const min = dates[0], max = dates[dates.length - 1];
  const out = [];
  for (let t = min.getTime(); t <= max.getTime(); t += DAY_MS) out.push(new Date(t));
  return out;
}

function aggregateWeekly(series) {
  const buckets = {};
  series.forEach(({ date, value }) => {
    const wk = dateStr(mondayOf(date));
    buckets[wk] = (buckets[wk] || 0) + value;
  });
  return Object.keys(buckets).sort().map(k => ({ date: toDate(k), value: buckets[k] }));
}

function aggregateMonthly(series) {
  const buckets = {};
  series.forEach(({ date, value }) => {
    const m = dateStr(monthStart(date));
    buckets[m] = (buckets[m] || 0) + value;
  });
  return Object.keys(buckets).sort().map(k => ({ date: toDate(k), value: buckets[k] }));
}

function rollingAvg(series, window) {
  const out = [];
  for (let i = 0; i < series.length; i++) {
    const start = Math.max(0, i - window + 1);
    const slice = series.slice(start, i + 1);
    const avg = slice.reduce((a, r) => a + r.value, 0) / slice.length;
    out.push({ date: series[i].date, value: series[i].value, rolling: Math.round(avg * 10) / 10 });
  }
  return out;
}

function baseLayout(title) {
  return {
    title: { text: title, font: { color: PALETTE.zeroWhite, size: 14 }, x: 0 },
    paper_bgcolor: PALETTE.surface1, plot_bgcolor: PALETTE.surface1,
    font: { color: '#888', size: 11 },
    margin: { l: 44, r: 8, t: 40, b: 36 },
    xaxis: { showgrid: false, linecolor: PALETTE.border, tickfont: { size: 10, color: '#888' } },
    yaxis: { showgrid: true, gridcolor: PALETTE.border, linecolor: 'rgba(0,0,0,0)', tickformat: ',' },
    bargap: 0.3,
  };
}
const PLOTLY_CFG = { displayModeBar: false, responsive: true };

function spotBar(elId, x, y, title, colour) {
  Plotly.newPlot(elId, [{
    x, y, type: 'bar', marker: { color: colour, line: { width: 0 } },
    hovertemplate: '%{x}<br><b>%{y:,}</b><extra></extra>',
  }], baseLayout(title), PLOTLY_CFG);
}

function spotMultiBar(elId, x, series, title) {
  // series: [{name, y, color}]
  const traces = series.map(s => ({
    x, y: s.y, type: 'bar', name: s.name,
    marker: { color: s.color, line: { width: 0 } },
    hovertemplate: '%{x}<br>' + s.name + ': <b>%{y:,}</b><extra></extra>',
  }));
  const layout = baseLayout(title);
  layout.barmode = 'group';
  layout.legend = { orientation: 'h', y: 1.14, font: { color: PALETTE.zeroWhite, size: 10 }, bgcolor: 'rgba(0,0,0,0)' };
  Plotly.newPlot(elId, traces, layout, PLOTLY_CFG);
}

function spotStackedBar(elId, x, series, title) {
  const traces = series.map(s => ({
    x, y: s.y, type: 'bar', name: s.name,
    marker: { color: s.color, line: { width: 0 } },
    hovertemplate: '%{x}<br>' + s.name + ': <b>%{y:,}</b><extra></extra>',
  }));
  const layout = baseLayout(title);
  layout.barmode = 'stack';
  layout.legend = { orientation: 'h', y: 1.14, font: { color: PALETTE.zeroWhite, size: 10 }, bgcolor: 'rgba(0,0,0,0)' };
  Plotly.newPlot(elId, traces, layout, PLOTLY_CFG);
}

function spotLine(elId, x, series, title) {
  const traces = series.map(s => ({
    x, y: s.y, type: 'scatter', mode: 'lines', name: s.name,
    line: { color: s.color, width: 2 },
    hovertemplate: '%{x}<br>' + s.name + ': <b>%{y:,}</b><extra></extra>',
  }));
  const layout = baseLayout(title);
  layout.hovermode = 'x unified';
  if (series.length > 1) {
    layout.legend = { orientation: 'h', y: 1.14, font: { color: PALETTE.zeroWhite, size: 10 }, bgcolor: 'rgba(0,0,0,0)' };
  }
  Plotly.newPlot(elId, traces, layout, PLOTLY_CFG);
}

function spotCombo(elId, x, barSeries, lineSeries, title) {
  const traces = [
    { x, y: barSeries.y, type: 'bar', name: barSeries.name, opacity: 0.7,
      marker: { color: barSeries.color, line: { width: 0 } },
      hovertemplate: '%{x}<br>' + barSeries.name + ': <b>%{y:,}</b><extra></extra>' },
    { x, y: lineSeries.y, type: 'scatter', mode: 'lines', name: lineSeries.name,
      line: { color: lineSeries.color, width: 2 },
      hovertemplate: '%{x}<br>' + lineSeries.name + ': <b>%{y:,.1f}</b><extra></extra>' },
  ];
  const layout = baseLayout(title);
  layout.legend = { orientation: 'h', y: 1.12, font: { color: PALETTE.zeroWhite, size: 11 }, bgcolor: 'rgba(0,0,0,0)' };
  layout.hovermode = 'x unified';
  Plotly.newPlot(elId, traces, layout, PLOTLY_CFG);
}

function renderKpiRow(elId, tiles) {
  // tiles: [{label, value, delta}] — delta optional (number, +/- rendered)
  document.getElementById(elId).innerHTML = tiles.map(t => {
    let deltaHtml = '';
    if (t.delta !== undefined && t.delta !== null) {
      const cls = t.delta >= 0 ? 'up' : 'down';
      const sign = t.delta >= 0 ? '+' : '';
      deltaHtml = `<div class="kpi-delta ${cls}">${sign}${fmtNum(t.delta)}</div>`;
    }
    return `<div class="kpi-tile"><div class="kpi-label">${t.label}</div>
      <div class="kpi-value">${t.value}</div>${deltaHtml}</div>`;
  }).join('');
}

function renderChips(elId, groups, onToggle) {
  const row = document.getElementById(elId);
  const selected = new Set();
  groups.forEach(g => {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = g;
    chip.onclick = () => {
      if (selected.has(g)) { selected.delete(g); chip.classList.remove('active'); }
      else { selected.add(g); chip.classList.add('active'); }
      onToggle(selected);
    };
    row.appendChild(chip);
  });
  return selected;
}

function updateFilterNote(elId, selected) {
  const note = document.getElementById(elId);
  if (selected.size === 0) { note.textContent = ''; return; }
  const list = Array.from(selected);
  note.textContent = '⬟ Filtered: ' + list.slice(0, 3).join(', ') + (list.length > 3 ? '…' : '');
}

function renderLeagueTable(rows, accentColour, caption, valueLabel) {
  const medals = { 1: '🥇', 2: '🥈', 3: '🥉' };
  const body = rows.map((r, i) => {
    const rank = i + 1;
    const medal = medals[rank] || (rank + '.');
    return `<tr><td class="rank">${medal}</td><td>${r.label}</td>
      <td class="num" style="color:${accentColour}">${r.formatted != null ? r.formatted : fmtNum(r.value)}</td></tr>`;
  }).join('');
  return `
    <div>
      <div class="table-caption">${caption}</div>
      <table class="league">
        <thead><tr><th>#</th><th>Tenant</th><th class="num">${valueLabel || 'Activations'}</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
    </div>`;
}

// ── Tenant grouping — mirrors utils' map_tenant_group Python logic exactly ──
const DEFINED_GROUPS = [
  "Spar Retail", "Build It", "Midas", "Mica", "Fashion Fusion",
  "Progas", "Aheers", "The Unlimited", "Ladysmith Office National",
  "OnAir", "Pet Pool & Home", "Spot Mobile", "Spot Connect App & Digital",
];

function mapTenantGroup(name) {
  const nl = (name || '').toLowerCase();
  if (nl.includes('build it')) return 'Build It';
  if (nl.includes('midas') || nl.includes('kr motor spares') || nl.includes('aca auto parts') || nl.includes('aca autoparts')) return 'Midas';
  if (nl.includes('mica') || nl.includes('greenfields hardware')) return 'Mica';
  if (nl.includes('spargs') || nl.includes('savemor') || nl.includes('spar')) return 'Spar Retail';
  if (nl.includes('fashion')) return 'Fashion Fusion';
  if (nl.includes('progas')) return 'Progas';
  if (nl.includes('aheers')) return 'Aheers';
  if (nl === 'the unlimited') return 'The Unlimited';
  if (nl.includes('ladysmith office national')) return 'Ladysmith Office National';
  if (nl.includes('onair') || nl.includes('on air')) return 'OnAir';
  if (nl.includes('pet pool')) return 'Pet Pool & Home';
  if (nl === 'spot mobile') return 'Spot Mobile';
  if (nl.includes('uconnect app') || nl.includes('uconnect digital')) return 'Spot Connect App & Digital';
  return 'Other Tenants';
}
