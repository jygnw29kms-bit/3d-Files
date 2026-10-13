<?php
declare(strict_types=1);
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: strict-origin-when-cross-origin');
$root = __DIR__;
function fmeta(string $path): array {
  global $root;
  $full = $root . '/' . ltrim($path, '/');
  return [
    'path' => $path,
    'exists' => is_file($full),
    'bytes' => is_file($full) ? filesize($full) : 0,
    'mtime' => is_file($full) ? filemtime($full) : 0,
  ];
}
function humanBytes(int $bytes): string {
  if ($bytes < 1024) return $bytes . ' B';
  if ($bytes < 1048576) return number_format($bytes / 1024, 1, ',', '.') . ' KiB';
  return number_format($bytes / 1048576, 1, ',', '.') . ' MiB';
}
$parts = [
  [
    'id'=>'P-001','name'=>'LST-Klammer 4 mm','type'=>'GROW / FÜHRUNG','status'=>'GEOMETRIE OK','statusClass'=>'verified',
    'preview'=>'LST-Klammer/P2S-Druckplatte.png','stl'=>'LST-Klammer/LST-Klammer-4mm.stl',
    'primary'=>'LST-Klammer/LST-Klammer-P2S-24x-4mm.3mf','package'=>'LST-Klammer/LST-Klammer-Download.zip',
    'report'=>'LST-Klammer/Pruefbericht.json','count'=>'24','build'=>'20 × 149,83 × 4 mm','material'=>'Generic PLA Silk','layer'=>'0,20 mm',
    'copy'=>'Verstärkte 4-mm-LST-Klammer. Platte für 256 × 256 mm vorbereitet; STL, vollständige 3MF-Platte, Paket und Prüfbericht liegen direkt vor.'
  ],
  [
    'id'=>'P-002','name'=>'LST-Clips · 428er Platte','type'=>'GROW / CLIP-SYSTEM','status'=>'GESLICED','statusClass'=>'sliced',
    'preview'=>'LST-Clips/P2S-KINGROON-HS-PLA/plattenbelegung.png','stl'=>'',
    'primary'=>'LST-Clips/P2S-KINGROON-HS-PLA/LST_428_P2S_KINGROON_HS_PLA.3mf','package'=>'LST-Clips/P2S-KINGROON-HS-PLA/P2S_KINGROON_LST_Druckpaket.zip',
    'report'=>'LST-Clips/P2S-KINGROON-HS-PLA/Druckhinweise_P2S_HS_PLA.md','count'=>'428','build'=>'volle P2S-Platte','material'=>'KINGROON HS-PLA','layer'=>'0,24 mm',
    'copy'=>'Drei Winkel und zwei Öffnungsgrößen auf einer vollen Platte. Vor Serienlauf steht eine separate 6er-Passprobe bereit.'
  ],
];
$allFiles=[];
foreach($parts as $p){ foreach(['primary','package','report','stl'] as $k){ if(!empty($p[$k])) $allFiles[] = fmeta($p[$k]); } }
$totalBytes = array_sum(array_column($allFiles,'bytes'));
$lastChange = max(array_merge([0], array_column($allFiles,'mtime')));
?>
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0a0d0c">
<title>PRINTBENCH // 3D Druck Technik</title>
<meta name="description" content="Hightech 3D-Druck Werkbank: Modelle, technische Druckdaten, Live-Dateimetadaten, STL-Viewer und integrierter Druckkosten-Rechner.">
<link rel="stylesheet" href="site.css"><link rel="stylesheet" href="hightech.css"><link rel="stylesheet" href="calculator-integrated.css">
</head>
<body>
<div class="bed-grid" aria-hidden="true"></div>
<header class="topbar"><a class="wordmark" href="#library"><span class="nozzle-mark"><i></i></span><span>PRINTBENCH <em>// LAB</em></span></a><nav class="topnav" id="topnav"><a class="active" href="#library">Modelle</a><a href="#viewer">3D Viewer</a><a href="#telemetry">Telemetry</a><a href="#costs">Kosten</a><a href="https://github.com/jygnw29kms-bit/3d-Files" target="_blank" rel="noreferrer">Git ↗</a></nav><button class="menu-btn" id="menuBtn">MENÜ</button></header>
<aside class="rail"><div class="rail-unit"><span class="rail-label">NODE</span><strong>PHP</strong><small><?= PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION ?></small></div><div class="rail-unit"><span class="rail-label">LIB</span><strong><?= count($parts) ?></strong><small>Sets</small></div><div class="rail-unit rail-live"><span class="dot"></span><small>LIVE FS</small></div></aside>
<main>
<section class="hero-tech" id="library"><div><p class="kicker">/ ADDITIVE MANUFACTURING CONTROL SURFACE</p><h1>3D PRINT<br><span>WORKBENCH</span></h1><p class="hero-lead">Keine Shop-Fassade. Eine technische Werkbank mit echten Dateien, Live-Metadaten, STL-Inspektion, Druckprofilen und Kalkulation.</p></div><div class="hero-hud"><div><span>DATASET</span><b><?= count($allFiles) ?> FILES</b></div><div><span>PAYLOAD</span><b><?= humanBytes($totalBytes) ?></b></div><div><span>LAST ASSET</span><b><?= $lastChange ? date('d.m.Y H:i',$lastChange) : '—' ?></b></div><div><span>PIPELINE</span><b>PHP + WEBGL</b></div></div></section>
<section class="scanline"><span>BED 256×256</span><span>STL / 3MF / ZIP / JSON</span><span>WEBGL INSPECTION</span><span>FILE HASH READY</span><span>NO BRAND // JUST PRINT</span></section>
<section class="toolbar"><div class="filter-group"><button class="filter active" data-filter="all">ALLE</button><button class="filter" data-filter="grow">GROW</button><button class="filter" data-filter="stl">STL VIEW</button></div><label class="search"><span>QUERY</span><input id="searchInput" type="search" placeholder="Teil / Material / Datei"></label></section>
<section class="library-grid" id="libraryGrid">
<?php foreach($parts as $p): $primary=fmeta($p['primary']); $pack=fmeta($p['package']); ?>
<article class="print-card tech-card" data-tags="grow <?= htmlspecialchars(strtolower($p['material'])) ?> <?= $p['stl']?'stl':'' ?>">
<div class="card-media plate-grid"><img src="<?= htmlspecialchars($p['preview']) ?>" alt="<?= htmlspecialchars($p['name']) ?>" loading="lazy"><span class="media-index"><?= htmlspecialchars($p['id']) ?></span><span class="media-badge">FS <?= $primary['exists']?'ONLINE':'MISS' ?></span><div class="crosshair"></div></div>
<div class="card-body"><div class="card-title-row"><div><span class="eyebrow"><?= htmlspecialchars($p['type']) ?></span><h2><?= htmlspecialchars($p['name']) ?></h2></div><span class="status <?= $p['statusClass'] ?>"><?= htmlspecialchars($p['status']) ?></span></div><p class="card-copy"><?= htmlspecialchars($p['copy']) ?></p>
<dl class="spec-grid"><div><dt>TEILE</dt><dd><?= $p['count'] ?></dd></div><div><dt>BAURAUM</dt><dd><?= htmlspecialchars($p['build']) ?></dd></div><div><dt>MATERIAL</dt><dd><?= htmlspecialchars($p['material']) ?></dd></div><div><dt>LAYER</dt><dd><?= htmlspecialchars($p['layer']) ?></dd></div><div><dt>3MF</dt><dd><?= humanBytes($primary['bytes']) ?></dd></div><div><dt>PAKET</dt><dd><?= humanBytes($pack['bytes']) ?></dd></div></dl>
<div class="actions"><a class="download primary" href="<?= htmlspecialchars($p['primary']) ?>" download>3MF ↓</a><?php if($p['stl']): ?><button class="download js-view" data-stl="<?= htmlspecialchars($p['stl']) ?>" data-name="<?= htmlspecialchars($p['name']) ?>">3D VIEW</button><a class="download" href="<?= htmlspecialchars($p['stl']) ?>" download>STL</a><?php endif; ?><a class="download" href="<?= htmlspecialchars($p['package']) ?>" download>PAKET</a><a class="download" href="<?= htmlspecialchars($p['report']) ?>" target="_blank">DATEN</a></div>
</div></article>
<?php endforeach; ?>
</section><div class="no-results" id="noResults" hidden>QUERY // 0 MATCHES</div>
<section class="viewer-section" id="viewer"><header class="section-title"><p class="kicker">/ TOOL 01 // GEOMETRY INSPECTION</p><h2>STL 3D Viewer</h2><p>WebGL-Inspektion direkt im Browser: Orbit, Zoom, Auto-Rotate, Bounding-Box und Dreiecksanzahl. Ein STL-fähiges Modell per „3D VIEW“ laden.</p></header><div class="viewer-shell"><div id="viewerCanvas" class="viewer-canvas"><div class="viewer-idle"><b>NO MODEL LOADED</b><span>SELECT // 3D VIEW</span></div></div><aside class="viewer-data"><div><span>MODEL</span><b id="vName">—</b></div><div><span>TRIANGLES</span><b id="vTriangles">—</b></div><div><span>SIZE X/Y/Z</span><b id="vSize">—</b></div><div><span>RENDER</span><b>THREE.JS / WEBGL</b></div><button id="autoRotate" class="tool-launch" type="button">AUTO ROTATE <b>↻</b></button></aside></div></section>
<section class="tool-section" id="telemetry"><header class="section-title"><p class="kicker">/ TOOL 02 // SERVER TELEMETRY</p><h2>Live Asset Telemetry</h2><p>PHP liest den tatsächlichen Dateibestand auf dem Webserver. Existenz, Größe und Änderungszeit kommen direkt aus dem Dateisystem.</p></header><div class="telemetry-grid" id="telemetryGrid"><?php foreach($allFiles as $f): ?><div class="telemetry-row"><span><?= htmlspecialchars(basename($f['path'])) ?></span><b><?= $f['exists']?humanBytes($f['bytes']):'MISSING' ?></b><i class="<?= $f['exists']?'ok':'bad' ?>"></i></div><?php endforeach; ?></div><a class="tool-launch inline-launch" href="api.php" target="_blank">RAW JSON API <b>→</b></a></section>

<section class="cost-workbench" id="costs">
<header class="section-title"><p class="kicker">/ TOOL 03 // PRINT ECONOMICS</p><h2>Druckkosten Rechner</h2><p>Direkt in PRINTBENCH integriert: STL, 3MF oder G-Code analysieren und Material, P2S-Energie, AMS 2 Pro, Maschinenzeit, Vorbereitung und Marge in einer Kalkulation zusammenführen.</p></header>
<div class="cost-shell">
  <div class="cost-upload">
    <label class="cost-drop" id="dropZone"><input id="fileInput" type="file" accept=".stl,.3mf,.gcode,.gco,.bgcode"><strong>Printdatei analysieren</strong><span>DROP / SELECT // STL · 3MF · G-CODE</span></label>
    <div class="cost-file-meta" id="fileMeta">NO FILE // manuelle Kalkulation aktiv</div>
  </div>

  <div class="cost-grid">
    <section class="cost-panel"><div class="cost-panel-head"><h3>Druckdaten</h3><span id="qualityBadge" class="badge">manuell</span></div><div class="cost-fields"><label>Druckdauer / h<input id="hours" type="number" min="0" step="0.01" value="1"></label><label>Filament / g<input id="grams" type="number" min="0" step="0.1" value="20"></label><label>Filamentlänge / m<input id="meters" type="number" min="0" step="0.1" value="6.7"></label><label>Anzahl Teile<input id="parts" type="number" min="1" step="1" value="1"></label></div><p class="cost-hint" id="parseHint">Geslicte G-Code-/3MF-Daten werden automatisch übernommen. STL-Werte sind Schätzwerte und bleiben editierbar.</p></section>
    <section class="cost-panel"><div class="cost-panel-head"><h3>Material</h3><button id="reloadPrices" class="cost-ghost" type="button">Preise neu laden</button></div><div class="cost-fields"><label>Marke<select id="brand"></select></label><label>Material<select id="material"></select></label><label>Preis / €/kg<input id="priceKg" type="number" min="0" step="0.01"></label><label>Dichte / g/cm³<input id="density" type="number" min="0.5" step="0.01"></label></div><div class="cost-source" id="priceSource">PRICE FEED // loading</div></section>
  </div>

  <div class="cost-grid">
    <section class="cost-panel"><h3>P2S / Energie</h3><div class="cost-fields"><label>Strom / €/kWh<input id="electricity" type="number" min="0" step="0.01" value="0.40"></label><label>Dauerleistung / W<input id="steadyWatts" type="number" min="0" step="1" value="200"></label><label>Aufheizleistung / W<input id="heatWatts" type="number" min="0" step="1" value="1200"></label><label>Aufheizzeit / min<input id="heatMinutes" type="number" min="0" step="1" value="5"></label><label>Maschine / €/h<input id="machineRate" type="number" min="0" step="0.01" value="0.65"></label><label>Ausschussreserve / %<input id="wastePercent" type="number" min="0" step="1" value="5"></label></div></section>
    <section class="cost-panel"><h3>AMS 2 Pro</h3><div class="cost-fields"><label>Betrieb<select id="amsMode"><option value="off">Aus</option><option value="feed">Materialzuführung</option><option value="dry">Trocknen</option><option value="dryprint">Trocknen + Drucken</option></select></label><label>Trocknungsdauer / h<input id="amsDryHours" type="number" min="0" step="0.25" value="6"></label><label>Betrieb / W<input id="amsFeedWatts" type="number" min="0" step="1" value="12"></label><label>Trocknen / W<input id="amsDryWatts" type="number" min="0" step="1" value="80"></label></div><p class="cost-hint">Trocknungsenergie wird separat zur Druckenergie kalkuliert. Die Leistungswerte können für reale Messwerte überschrieben werden.</p></section>
  </div>

  <div class="cost-grid">
    <section class="cost-panel"><h3>Vorbereitung / Aufbereitung</h3><div class="cost-fields"><label>Grundaufwand / €<input id="prepBase" type="number" min="0" step="0.10" value="2.50"></label><label>Basis-Aufschlag / %<input id="prepPercent" type="number" min="0" step="1" value="15"></label><label>je Druckstunde / %<input id="prepPerHour" type="number" min="0" step="0.1" value="1.5"></label><label>Marge / %<input id="marginPercent" type="number" min="0" step="1" value="20"></label></div><p class="cost-hint">Aufbereitung skaliert mit der Druckdauer: Basis-Aufschlag + Druckstunden × Stundenaufschlag.</p></section>
    <section class="cost-panel" id="stlOptions" hidden><h3>STL / Schätzung</h3><div class="cost-fields"><label>Infill / %<input id="infill" type="number" min="0" max="100" step="1" value="15"></label><label>Wand + Deckel / %<input id="shellPercent" type="number" min="0" max="100" step="1" value="25"></label><label>Volumenstrom / mm³/s<input id="flowRate" type="number" min="1" step="1" value="16"></label><label>Zeitfaktor<input id="timeFactor" type="number" min="1" step="0.1" value="1.8"></label></div><p class="cost-hint">Für belastbare Angebote eine geslicte 3MF-/G-Code-Datei verwenden.</p></section>
  </div>

  <section class="cost-results"><div class="cost-results-head"><h3>Kalkulation / Live</h3><button id="resetBtn" class="cost-ghost" type="button">Reset</button></div><div class="cost-result-grid"><article><span>Material</span><strong id="materialCost">0,00 €</strong></article><article><span>P2S Strom</span><strong id="energyCost">0,00 €</strong></article><article><span>AMS 2 Pro</span><strong id="amsCost">0,00 €</strong></article><article><span>Maschine</span><strong id="machineCost">0,00 €</strong></article><article><span>Vorbereitung</span><strong id="prepCost">0,00 €</strong></article><article><span>Selbstkosten</span><strong id="subtotalCost">0,00 €</strong></article><article class="primary"><span>Kalkulierter Preis</span><strong id="totalCost">0,00 €</strong></article></div><div class="cost-details" id="details"></div><p class="cost-local">LOCAL PROCESSING // Preis-Overrides verbleiben im Browser</p></section>
</div>
</section>
</main><footer><span>PRINTBENCH // 3D DRUCK</span><span>PHP + JavaScript + WebGL</span><a href="https://github.com/jygnw29kms-bit/3d-Files" target="_blank">SOURCE ↗</a></footer>
<script>window.PRINTBENCH={api:'api.php'};</script><script type="module" src="workbench.js"></script>
<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script><script type="module" src="Druckkosten-Rechner/app.js"></script>
</body></html>
