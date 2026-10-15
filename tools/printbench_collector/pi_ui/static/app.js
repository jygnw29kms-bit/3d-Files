const $ = id => document.getElementById(id);
const fmt = v => v == null || v === '' ? '-' : v;
const c = v => v == null ? '-' : `${Math.round(Number(v) * 10) / 10}°C`;
const esc = v => String(v ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const api = p => fetch('/api/v1' + p, {cache:'no-store'}).then(async r => {
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || body.error || `HTTP ${r.status}`);
  return body;
});

let lastHistory = [];
let cameraStarted = false;
let currentView = 'overview';
let nativeControlAuthorized = false;
let latestCaps = {controls:{}, features:{}};
let latestLive = {};
let commandBusy = false;

function drawChart(points) {
  const cv = $('chart'), ctx = cv.getContext('2d'), dpr = devicePixelRatio || 1;
  const w = Math.max(320, cv.clientWidth || 900), h = 160;
  cv.width = w * dpr; cv.height = h * dpr; ctx.scale(dpr, dpr); ctx.clearRect(0, 0, w, h);
  if (!points?.length) return;
  let vals = [];
  for (const p of points) {
    if (p.nozzle_c != null) vals.push(+p.nozzle_c);
    if (p.bed_c != null) vals.push(+p.bed_c);
    if (p.chamber_c != null) vals.push(+p.chamber_c);
  }
  if (!vals.length) return;
  let min = Math.min(...vals), max = Math.max(...vals);
  if (max - min < 10) { min -= 5; max += 5; }
  ctx.strokeStyle = '#26303a'; ctx.lineWidth = 1;
  for (let y = 0; y <= 3; y++) {
    const yy = 10 + (h - 20) * y / 3; ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(w, yy); ctx.stroke();
  }
  function line(key, color) {
    ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.beginPath(); let started = false;
    points.forEach((p, i) => {
      const v = +p[key]; if (!Number.isFinite(v)) return;
      const x = i / (points.length - 1 || 1) * w, y = h - 10 - (v - min) / (max - min) * (h - 20);
      if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
    });
    if (started) ctx.stroke();
  }
  line('nozzle_c', '#43d7ff'); line('bed_c', '#9aa6b2'); line('chamber_c', '#6f7f8e');
}

function slotHtml(s, active) {
  const col = /^[0-9A-Fa-f]{8}$/.test(s.color || '') ? '#' + s.color.slice(0, 6) : '#26303a';
  return `<div class="slot ${String(s.id) === active ? 'active' : ''}"><span class="n">SLOT ${Number(s.id) + 1}</span><div class="swatch" style="background:${col}"></div><b>${esc(s.material || 'NICHT GESETZT')}</b><small>${s.remain != null ? 'Rest ' + Number(s.remain) + '%' : 'keine Restdaten'}</small><em>Quelle: ${esc(s.source || 'printer_report')}</em></div>`;
}

function renderSlots(ams) {
  const active = String(ams.active_slot ?? '');
  const html = (ams.slots || []).map(s => slotHtml(s, active)).join('') || '<p class="empty">Keine Slotdaten gemeldet.</p>';
  $('slots').innerHTML = html; $('slotsFull').innerHTML = html;
}

function sec(v) {
  if (v == null) return '-';
  const d = Math.floor(v / 86400), h = Math.floor((v % 86400) / 3600), m = Math.floor((v % 3600) / 60);
  return d ? `${d}d ${h}h` : `${h}h ${m}m`;
}

function dryTime(v) {
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0) return '-';
  const h = Math.floor(n / 60), m = Math.floor(n % 60);
  return h ? `${h}h ${String(m).padStart(2, '0')}m` : `${m} min`;
}

function renderCaps(caps) {
  const f = caps.features || {};
  $('caps').innerHTML = Object.entries(f).map(([k, v]) => `<div><span>${esc(k.replaceAll('_',' '))}</span><b class="${v ? 'yes' : 'no'}">${v ? 'JA' : 'NEIN'}</b></div>`).join('');
  const controls = caps.controls || {};
  $('controlCaps').innerHTML = Object.entries(controls).map(([k, v]) => `<div><span>${esc(k)}</span><b class="${v.enabled ? 'yes' : 'no'}">${esc(v.status || '-')}</b></div>`).join('');
  const controlReady = nativeControlAuthorized && Object.values(controls).some(v => v.enabled);
  $('controlState').textContent = controlReady ? 'ORCA CONTROL AKTIV · TOKEN + POLICY' : 'BROWSER READ ONLY · ORCA TOKEN ERFORDERLICH';
  $('controlOverview').textContent = controlReady ? 'ORCA CONTROL' : 'READ ONLY';
  $('quickControlStatus').textContent = controlReady ? 'CONTROL AKTIV' : 'READ ONLY';
  refreshControlButtons();
}

function renderRfid(rows) {
  $('rfidRows').innerHTML = (rows || []).map(r => `<div class="rfidrow"><b>S${Number(r.slot_id)+1}</b><span>${esc(r.tray_type || 'kein Material')} · State ${esc(fmt(r.tray_state))} · ${r.reading ? 'liest' : 'idle'}</span><i class="tag ${r.confidence === 'reported' ? 'ok' : ''}">${esc(r.confidence || 'transient')}</i></div>`).join('') || '<p class="empty">Noch keine RFID-Beobachtungen.</p>';
}

function renderExternalTags(x) {
  $('externalTagRows').innerHTML = (x.items || []).map(r => `<div class="rfidrow"><b>S${Number(r.slot_id)+1}</b><span>${esc(r.reader_id)} · ${esc(r.tag_type || 'unknown')} · ${esc(r.spool_id || 'nicht zugeordnet')}</span><i class="tag ${r.matched ? 'ok' : ''}">${r.matched ? 'MATCH' : 'UNMATCHED'}</i></div>`).join('') || '<p class="empty">Noch keine Beobachtung eines externen NFC-Readers.</p>';
}

function renderSessions(rows) {
  const item = s => `<div class="session"><b>${esc(new Date(s.started_at).toLocaleString('de-DE'))}</b><span>${esc(s.outcome || s.state || '-')}</span><span>${esc((s.filament_vendor || '') + ' ' + (s.filament_type || '-'))}</span><span>${s.planned_filament_g != null ? Math.round(s.planned_filament_g) + ' g' : '-'}</span><span>${s.actual_time_sec ? Math.round(s.actual_time_sec / 60) + ' min' : '-'}</span><span>${s.self_cost_eur != null ? Number(s.self_cost_eur).toFixed(2) + ' €' : '-'}</span></div>`;
  $('sessions').innerHTML = (rows || []).map(item).join('') || '<p class="empty">Keine Drucksessions gespeichert.</p>';
  const recent = (rows || []).slice(0, 4);
  $('sessionsOverview').innerHTML = recent.length ? recent.map(item).join('') : '<p class="empty">Noch keine Drucksessions.</p>';
}

function renderFirmware(x) {
  $('firmwareRows').innerHTML = (x.items || []).map(r => `<div class="firmware-row"><b>${esc(r.name || '-')}</b><span>${esc(r.hw_ver || '-')}</span><strong>${esc(r.sw_ver || '-')}</strong></div>`).join('') || '<p class="empty">Noch keine Firmwaredaten empfangen.</p>';
}

function renderSpools(x) {
  $('spoolCount').textContent = x.items?.length || 0; $('matchCount').textContent = x.matched_count || 0;
  $('proposalCount').textContent = x.ready_proposals || 0; $('blockedProposalCount').textContent = x.blocked_proposals || 0;
  $('spoolRows').innerHTML = (x.items || []).map(s => {
    const col = /^#[0-9a-f]{6}$/i.test(s.color_hex || '') ? s.color_hex : '#26303a';
    return `<div class="spool"><i style="background:${col}"></i><b>${esc(s.display_name || s.spool_id)}</b><span>${esc(s.vendor || '-')} · ${esc(s.material || '-')} · ${esc(s.color_name || '-')}</span><span>${s.remaining_g != null ? Math.round(s.remaining_g) + ' g' : '-'}</span><span>${s.ams_slot != null ? 'AMS ' + (Number(s.ams_slot)+1) : 'nicht zugewiesen'}</span></div>`;
  }).join('') || '<p class="empty">Noch keine synchronisierten Spulen.</p>';
}

function renderDrying(ams) {
  const ds = ams?.dry_setting || {}, active = Number(ams?.dry_time || 0) > 0;
  $('dryState').textContent = active ? 'AKTIV' : 'AUS';
  $('dryTemps').textContent = `${c(ams?.temp_c)} / ${ds.dry_temperature != null ? c(ds.dry_temperature) : '-'}`;
  $('dryProfile').textContent = ds.dry_filament ? `${ds.dry_filament} · ${fmt(ds.dry_duration)}h` : '-';
  $('dryTime').textContent = dryTime(ams?.dry_time);
}

function updateCamera(camOk, live, sys) {
  $('camera').textContent = camOk ? 'MJPEG Bridge bereit' : live.camera?.printer_liveview ? 'P2S Stream aktiv / Bridge wartet' : 'Bridge aus';
  $('cameraAge').textContent = sys.camera_snapshot_age_sec != null ? 'letztes Bild ' + Math.round(sys.camera_snapshot_age_sec) + ' s' : 'kein aktuelles Bild';
  const shouldStream = camOk && currentView === 'overview';
  $('cameraOverlay').style.display = shouldStream ? 'none' : 'grid';
  $('cameraOverlay').textContent = camOk ? 'Livefeed pausiert ausserhalb der Übersicht' : 'warte auf Kamera...';
  if (shouldStream && !cameraStarted) { $('cameraImage').src = '/camera/stream.mjpg'; cameraStarted = true; }
  else if (!shouldStream && cameraStarted) { $('cameraImage').removeAttribute('src'); cameraStarted = false; }
}

function controlArgs(button) {
  const name = button.dataset.control;
  if (name === 'printer.light') return {mode:button.dataset.mode};
  if (name === 'printer.speed') return {level:Number(button.dataset.level)};
  if (name === 'printer.fan') return {fan:Number($('fanIndex').value), speed:Number($('fanSpeed').value)};
  if (name === 'printer.nozzle_temp') return {temp:Number($(button.dataset.input).value)};
  if (name === 'printer.bed_temp') return {temp:Number($(button.dataset.input).value)};
  if (name === 'printer.chamber_temp') return {temp:Number($(button.dataset.input).value)};
  return {};
}

async function sendControl(button) {
  if (commandBusy || button.disabled) return;
  const name = button.dataset.control, cap = latestCaps.controls?.[name];
  if (!cap?.enabled) return;
  const destructive = cap.risk === 'destructive';
  if (destructive && !window.confirm('Druck wirklich sofort stoppen?')) return;
  commandBusy = true; refreshControlButtons();
  $('controlResult').textContent = `${name} · sende…`; $('controlResult').className = 'control-result busy';
  try {
    const r = await fetch('/api/v1/control/' + name.replaceAll('.', '/'), {
      method:'POST', cache:'no-store', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({args:controlArgs(button), confirm:destructive})
    });
    const body = await r.json().catch(() => ({}));
    if (r.status === 403 && body.error === 'control_authorization_required') throw new Error('Nur im autorisierten Orca-Tab steuerbar');
    if (!r.ok || !body.ok) throw new Error(body.detail || body.verification || body.error || `HTTP ${r.status}`);
    $('controlResult').textContent = `${name} · ${body.verification || 'OK'}`; $('controlResult').className = 'control-result ok';
    setTimeout(refreshFast, 500);
  } catch (err) {
    $('controlResult').textContent = `${name} · ${err.message}`; $('controlResult').className = 'control-result bad';
  } finally {
    commandBusy = false; refreshControlButtons();
  }
}

function refreshControlButtons() {
  const state = String(latestLive.print_state || '').toUpperCase();
  const active = ['RUNNING','PREPARE','PRINTING'].includes(state), paused = ['PAUSE','PAUSED'].includes(state);
  document.querySelectorAll('[data-control]').forEach(b => {
    const name = b.dataset.control, cap = latestCaps.controls?.[name];
    let enabled = !!cap?.enabled && !commandBusy && latestLive.online !== false;
    if (name === 'print.pause') enabled = enabled && active;
    if (name === 'print.resume') enabled = enabled && paused;
    if (name === 'print.stop') enabled = enabled && (active || paused);
    if (name === 'ams.stop_drying') enabled = enabled && Number(latestLive.ams?.dry_time || 0) > 0;
    b.disabled = !enabled;
    b.title = cap ? `${cap.status} · ${cap.risk}` : 'Capability nicht gemeldet';
  });
}

async function refreshFast() {
  try {
    const [live, sys] = await Promise.all([api('/live'), api('/system')]); latestLive = live;
    $('onlineText').textContent = live.online ? 'ONLINE' : 'STALE'; $('onlineDot').style.background = live.online ? '#3fe58b' : '#ff6474';
    $('printerStatusText').textContent = live.online ? 'ONLINE / BEREIT' : 'TELEMETRIE STALE';
    $('printerStatusDot').style.background = live.online ? '#4ee59b' : '#ff5f72';
    $('printerStatusAge').textContent = `vor ${fmt(live.age_sec)} s`;
    $('age').textContent = `letztes Telegramm vor ${fmt(live.age_sec)} s`; $('state').textContent = live.print_state || 'UNBEKANNT'; $('stateHero').textContent = live.print_state || 'UNBEKANNT';
    const p = Math.max(0, Math.min(100, Math.round(live.progress || 0))); $('progress').textContent = p + '%'; $('progressBar').style.width = p + '%';
    $('layer').textContent = `${fmt(live.layer_current)} / ${fmt(live.layer_total)}`; $('remain').textContent = live.remaining_min != null ? Math.round(live.remaining_min) + ' min' : '-';
    $('speed').textContent = live.speed_mag != null ? Math.round(live.speed_mag) + '%' : fmt(live.speed_level);
    $('nozzle').textContent = c(live.nozzle_c); $('nozzleMini').textContent = c(live.nozzle_c); $('nozzleTarget').textContent = 'Ziel ' + c(live.nozzle_target_c);
    $('bed').textContent = c(live.bed_c); $('bedMini').textContent = c(live.bed_c); $('bedTarget').textContent = 'Ziel ' + c(live.bed_target_c);
    $('chamber').textContent = c(live.chamber_c); $('chamberMini').textContent = c(live.chamber_c);
    if (document.activeElement !== $('nozzleSet') && live.nozzle_target_c != null) $('nozzleSet').value = Math.round(live.nozzle_target_c);
    if (document.activeElement !== $('bedSet') && live.bed_target_c != null) $('bedSet').value = Math.round(live.bed_target_c);
    $('amsTemp').textContent = c(live.ams?.temp_c); $('amsHum').textContent = fmt(live.ams?.humidity_raw ?? live.ams?.humidity);
    const a = live.ams?.active_slot; $('amsActive').textContent = (a == null || a === '' || String(a) === '255') ? '-' : 'SLOT ' + (Number(a)+1);
    renderSlots(live.ams || {}); renderDrying(live.ams || {});
    $('wifi').textContent = live.wifi_rssi != null ? Math.round(live.wifi_rssi) + ' dBm' : '-'; $('hms').textContent = fmt(live.hms_count);
    $('collector').textContent = sys.collector || '-'; $('collector2').textContent = sys.collector || '-'; $('readerBridge').textContent = sys.reader_bridge || 'inactive';
    $('collectorSide').textContent = `Collector ${sys.collector || '-'}`; $('piTemp').textContent = c(sys.pi_temp_c); $('piTemp2').textContent = c(sys.pi_temp_c);
    $('hostName').textContent = sys.hostname || '-'; $('uptime').textContent = sec(sys.uptime_sec); $('disk').textContent = sys.disk ? `${sys.disk.free_gb} / ${sys.disk.total_gb} GB frei` : '-';
    const camOk = sys.camera_bridge === 'active' && sys.camera_snapshot_age_sec != null && sys.camera_snapshot_age_sec < 75; updateCamera(camOk, live, sys);
    $('updated').textContent = 'aktualisiert ' + new Date().toLocaleTimeString('de-DE'); refreshControlButtons();
  } catch (e) {
    latestLive = {online:false}; $('onlineText').textContent = 'OFFLINE'; $('onlineDot').style.background = '#ff6474'; refreshControlButtons(); console.error(e);
  }
}

async function refreshSlow() {
  try {
    const [rfid, external, sessions, hist, spools, caps, firmware, control] = await Promise.all([
      api('/rfid'), api('/external-tags?limit=24'), api('/sessions?limit=30'), api('/history?hours=24&limit=180'), api('/spools'), api('/capabilities'), api('/firmware'), api('/control-capabilities')
    ]);
    nativeControlAuthorized = !!control.browser_write_endpoint;
    latestCaps = {...caps, controls:control.items || {}};
    renderRfid(rfid); renderExternalTags(external); renderSessions(sessions); renderSpools(spools); renderCaps(latestCaps); renderFirmware(firmware);
    lastHistory = hist.points || []; drawChart(lastHistory);
  } catch (e) { console.error(e); }
}

const mobileNavToggle = $('mobileNavToggle');
const navScrim = $('navScrim');
function setMobileNav(open) {
  document.body.classList.toggle('nav-open', !!open);
  mobileNavToggle?.setAttribute('aria-expanded', open ? 'true' : 'false');
}
mobileNavToggle?.addEventListener('click', () => setMobileNav(!document.body.classList.contains('nav-open')));
navScrim?.addEventListener('click', () => setMobileNav(false));
document.addEventListener('keydown', e => { if (e.key === 'Escape') setMobileNav(false); });

document.querySelectorAll('[data-control]').forEach(b => b.addEventListener('click', () => sendControl(b)));
document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => {
  currentView = b.dataset.view;
  document.querySelectorAll('.side-nav [data-view],.top-nav [data-view]').forEach(x => x.classList.toggle('active', x.dataset.view === currentView));
  document.querySelectorAll('[data-view-panel]').forEach(x => x.classList.toggle('active', x.dataset.viewPanel === currentView));
  $('pageTitle').textContent = {overview:'Bambu Lab P2S', control:'Steuerung', ams:'AMS 2 Pro', spools:'Material / Spulen', prints:'Drucke / Historie', system:'System / Bridge'}[currentView] || 'PRINTBENCH';
  setMobileNav(false);
  if (currentView !== 'overview' && cameraStarted) { $('cameraImage').removeAttribute('src'); cameraStarted = false; }
}));

refreshFast(); refreshSlow(); setInterval(refreshFast, 5000); setInterval(refreshSlow, 30000); window.addEventListener('resize', () => drawChart(lastHistory));
