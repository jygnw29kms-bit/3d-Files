const $ = (id) => document.getElementById(id);
const euro = (n) => new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(Number(n || 0));
const dur = (seconds) => {
  const s = Number(seconds || 0);
  return `${Math.floor(s / 3600)}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
};
let DATA = {};

function setText(id, value) {
  const el = $(id);
  if (el) el.textContent = value;
}

function drawChart(history) {
  const c = $('tempChart');
  if (!c) return;
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth || 600;
  const h = c.clientHeight || 180;
  c.width = w * dpr;
  c.height = h * dpr;
  const ctx = c.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = '#243039';
  ctx.lineWidth = 1;
  for (let i = 0; i < 5; i++) {
    const y = 20 + i * (h - 35) / 4;
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
  }
  for (const [key, color] of [['nozzle_c', '#ff7900'], ['bed_c', '#40bfff']]) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((p, i) => {
      const xx = i / Math.max(1, history.length - 1) * w;
      const yy = h - 15 - (Number(p[key] || 0) / 260) * (h - 30);
      if (i === 0) ctx.moveTo(xx, yy); else ctx.lineTo(xx, yy);
    });
    ctx.stroke();
  }
}

function calc(data) {
  const s = data.slicer || {};
  const hours = Number(s.total_time_sec || 0) / 3600;
  const grams = Number(s.filament_g || 0);
  const priceKg = Number($('priceKg')?.value || 18.99);
  const powerPrice = Number($('powerPrice')?.value || 0.40);
  const machineRate = Number($('machineRate')?.value || 0.65);
  const marginPct = Number($('margin')?.value || 20);
  const material = grams / 1000 * priceKg;
  const electricity = (0.2 * hours + 0.1) * powerPrice;
  const machine = hours * machineRate;
  const self = material + electricity + machine;
  const margin = self * marginPct / 100;
  const total = self + margin;
  [['cMat', material], ['cPower', electricity], ['cMachine', machine], ['cSelf', self], ['cMargin', margin], ['cTotal', total]]
    .forEach(([id, value]) => setText(id, euro(value)));
}

function fill(data) {
  DATA = data;
  const live = data.live || {};
  const slicer = data.slicer || {};
  const ams = data.ams || {};
  const progress = Math.round(Number(live.progress || 0));
  setText('progress', `${progress}%`);
  const bar = $('barFill'); if (bar) bar.style.width = `${progress}%`;
  const ring = $('ring'); if (ring) ring.style.background = `conic-gradient(var(--orange) ${progress * 3.6}deg,#202930 0)`;
  setText('layer', `${live.layer_current ?? '--'} / ${live.layer_total ?? '--'}`);
  setText('rest', `~ ${Math.round(Number(live.remaining_min || 0))} min`);
  setText('speed', live.speed_level ?? '--');
  setText('nozzle', `${Math.round(Number(live.nozzle_c || 0))} \u00b0C`);
  setText('bed', `${Math.round(Number(live.bed_c || 0))} \u00b0C`);
  setText('wifi', live.wifi_rssi || '--');
  setText('profile', slicer.filament_profile || '--');
  setText('dProfile', slicer.filament_profile || '--');
  setText('vendor', slicer.filament_vendor || '--');
  setText('material', slicer.filament_type || '--');
  setText('filament', `${Number(slicer.filament_g || 0).toFixed(2)} g / ${Number(slicer.filament_m || 0).toFixed(3)} m`);
  setText('layers', slicer.layer_count ?? '--');
  setText('lh', `${slicer.layer_height ?? '--'} mm`);
  setText('infill', `${slicer.infill_percent ?? '--'} % ${slicer.infill_pattern || ''}`);
  setText('walls', slicer.wall_loops ?? '--');
  setText('modelTime', dur(slicer.model_time_sec));
  setText('totalTime', dur(slicer.total_time_sec));
  setText('slot', ams.active_slot ?? '--');
  setText('amsMat', ams.material || '--');
  setText('amsTemp', `${ams.temp_c ?? '--'} \u00b0C`);
  setText('amsHum', `${ams.humidity_raw ?? '--'} raw`);
  setText('rfid', ams.tag_uid_present ? 'UID erkannt' : '\u2014');
  if (slicer.origin_path) setText('jobName', slicer.origin_path.replace(/\.3mf$/i, '').replace(/_/g, ' '));
  drawChart(data.history || []);
  calc(data);
  const view = document.body.dataset.view;
  if (view && view !== 'uebersicht') renderView(view, data);
}

async function load() {
  const endpoint = window.LIVE_ENDPOINT || 'data.json';
  const response = await fetch(`${endpoint}?t=${Date.now()}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`live data ${response.status}`);
  fill(await response.json());
}

const viewMap = {
  'ÜBERSICHT': 'uebersicht',
  'LIVE DRUCK': 'live',
  'HISTORIE': 'historie',
  'MATERIAL': 'material',
  'AMS 2 PRO': 'ams',
  'STATISTIKEN': 'statistik',
  'KOSTEN': 'kosten',
  'PROJEKTE': 'projekte'
};

function renderView(view, data) {
  let host = $('subview');
  if (!host) {
    host = document.createElement('section');
    host.id = 'subview';
    host.className = 'subview';
    document.querySelector('main').appendChild(host);
  }
  const live = data.live || {};
  const slicer = data.slicer || {};
  const ams = data.ams || {};
  const stats = data.stats || {};
  const jobs = data.jobs || [];
  const img = (n) => `assets/bambu-official/p2s-${n}.jpg`;
  const views = {
    live: `<div class="view-title"><h2>LIVE DRUCK</h2><p>P2S / MQTT / 5-Sekunden-Stream</p></div><div class="live-work"><img src="${img(2)}"><div class="view-kpis"><b>${Math.round(Number(live.progress || 0))}%</b><span>Layer ${live.layer_current ?? '--'} / ${live.layer_total ?? '--'}</span><span>Düse ${Math.round(Number(live.nozzle_c || 0))} °C · Bett ${Math.round(Number(live.bed_c || 0))} °C</span><span>Restzeit ${Math.round(Number(live.remaining_min || 0))} min</span></div></div>`,
    historie: `<div class="view-title"><h2>HISTORIE</h2><p>Zuletzt erkannte Slicer-Jobs</p></div><div class="history-list">${jobs.map(j => `<div><b>${j.origin_path || 'Job'}</b><span>${j.filament_vendor || ''} ${j.filament_type || ''}</span><span>${Number(j.filament_g || 0).toFixed(1)} g</span><span>${dur(j.total_time_sec)}</span></div>`).join('') || '<p>Noch keine Jobs.</p>'}</div>`,
    material: `<div class="view-title"><h2>MATERIAL</h2><p>Aktuelles Druckmaterial</p></div><div class="material-view"><img src="${img(11)}"><div><h3>${slicer.filament_vendor || '--'} ${slicer.filament_type || '--'}</h3><p>${slicer.filament_profile || '--'}</p><dl><dt>Dichte</dt><dd>${slicer.density ?? '--'} g/cm³</dd><dt>Durchmesser</dt><dd>${slicer.diameter ?? '--'} mm</dd><dt>Aktiver Slot</dt><dd>${ams.active_slot ?? '--'}</dd><dt>AMS Temp.</dt><dd>${ams.temp_c ?? '--'} °C</dd></dl></div></div>`,
    ams: `<div class="view-title"><h2>AMS 2 PRO</h2><p>Materialsystem / Live-Status</p></div><div class="ams-view"><img src="${img(11)}"><div class="view-kpis"><b>Slot ${ams.active_slot ?? '--'}</b><span>${ams.material || '--'}</span><span>${ams.temp_c ?? '--'} °C</span><span>Feuchte ${ams.humidity_raw ?? '--'} raw</span><span>Trocknung ${ams.drying ? 'AKTIV' : 'AUS'}</span></div></div>`,
    statistik: `<div class="view-title"><h2>STATISTIKEN</h2><p>Collector / SQLite</p></div><div class="stat-grid"><article><span>Samples</span><b>${stats.samples || data.sample_count || 0}</b></article><article><span>Düse Ø</span><b>${Number(stats.nozzle_avg || 0).toFixed(1)}°</b></article><article><span>Düse Max</span><b>${Number(stats.nozzle_max || 0).toFixed(1)}°</b></article><article><span>Bett Ø</span><b>${Number(stats.bed_avg || 0).toFixed(1)}°</b></article><article><span>Fortschritt Max</span><b>${Number(stats.progress_max || 0).toFixed(0)}%</b></article></div>`,
    kosten: `<div class="view-title"><h2>KOSTEN</h2><p>Live-Kalkulation aus dem aktuellen Slicer-Job</p></div><div class="cost-standalone"><div><span>Filament</span><b>${$('cMat')?.textContent || '0,00 €'}</b></div><div><span>Strom</span><b>${$('cPower')?.textContent || '0,00 €'}</b></div><div><span>Maschinenzeit</span><b>${$('cMachine')?.textContent || '0,00 €'}</b></div><div><span>Selbstkosten</span><b>${$('cSelf')?.textContent || '0,00 €'}</b></div><div class="total"><span>Verkaufspreis</span><b>${$('cTotal')?.textContent || '0,00 €'}</b></div></div>`,
    projekte: `<div class="view-title"><h2>PROJEKTE</h2><p>Produktionsdateien und reale Druckplatten</p></div><div class="project-grid"><article><img src="assets/lst-clips.png"><h3>428er LST Clips</h3><a href="LST-Clips/P2S-KINGROON-HS-PLA/LST_428_P2S_KINGROON_HS_PLA.3mf">3MF öffnen</a></article><article><img src="assets/lst-klammer.png"><h3>24er LST Klammer</h3><a href="LST-Klammer/LST-Klammer-P2S-24x-4mm.3mf">3MF öffnen</a></article></div>`
  };
  host.innerHTML = views[view] || '';
}

document.querySelectorAll('.sidebar nav a').forEach((a) => {
  const view = viewMap[a.textContent.trim()] || 'uebersicht';
  a.href = `#${view}`;
  a.dataset.view = view;
  a.addEventListener('click', (event) => {
    event.preventDefault();
    document.querySelectorAll('.sidebar nav a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.body.dataset.view = view;
    document.querySelectorAll('main > .grid').forEach(x => { x.hidden = view !== 'uebersicht'; });
    const host = $('subview');
    if (view === 'uebersicht') {
      if (host) host.hidden = true;
    } else {
      if (host) host.hidden = false;
      renderView(view, DATA);
    }
    history.replaceState(null, '', `#${view}`);
  });
});

['priceKg', 'powerPrice', 'machineRate', 'margin'].forEach(id => $(id)?.addEventListener('input', () => calc(DATA)));
setInterval(() => setText('clock', new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })), 1000);
load().catch(console.error);
setInterval(() => load().catch(console.error), 5000);

function activateInitialView(){
  const requested=(location.hash||'#uebersicht').slice(1);
  const link=[...document.querySelectorAll('.sidebar nav a')].find(a=>a.dataset.view===requested);
  if(link && requested!=='uebersicht') link.click();
}
window.addEventListener('DOMContentLoaded',activateInitialView);
