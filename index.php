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
<meta name="description" content="Hightech 3D-Druck Werkbank: Modelle, technische Druckdaten, Live-Dateimetadaten, STL-Viewer und Kostenrechner.">
<link rel="stylesheet" href="site.css"><link rel="stylesheet" href="hightech.css">
</head>
<body>
<div class="bed-grid" aria-hidden="true"></div>
<header class="topbar"><a class="wordmark" href="#library"><span class="nozzle-mark"><i></i></span><span>PRINTBENCH <em>// LAB</em></span></a><nav class="topnav" id="topnav"><a class="active" href="#library">Modelle</a><a href="#viewer">3D Viewer</a><a href="#telemetry">Telemetry</a><a href="Druckkosten-Rechner/">Kosten</a><a href="https://github.com/jygnw29kms-bit/3d-Files" target="_blank" rel="noreferrer">Git ↗</a></nav><button class="menu-btn" id="menuBtn">MENÜ</button></header>
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
<section class="tool-section" id="telemetry"><header class="section-title"><p class="kicker">/ TOOL 02 // SERVER TELEMETRY</p><h2>Live Asset Telemetry</h2><p>PHP liest den tatsächlichen Dateibestand auf dem Webserver. Keine statischen Fantasiewerte: Existenz, Größe und Änderungszeit kommen direkt aus dem Dateisystem.</p></header><div class="telemetry-grid" id="telemetryGrid"><?php foreach($allFiles as $f): ?><div class="telemetry-row"><span><?= htmlspecialchars(basename($f['path'])) ?></span><b><?= $f['exists']?humanBytes($f['bytes']):'MISSING' ?></b><i class="<?= $f['exists']?'ok':'bad' ?>"></i></div><?php endforeach; ?></div><a class="tool-launch inline-launch" href="api.php" target="_blank">RAW JSON API <b>→</b></a></section>
<section class="material-section" id="materials"><header class="section-title"><p class="kicker">/ TOOL 03</p><h2>Print Economics</h2><p>Material, Energie, Maschinenzeit, Trocknung und Ausschuss werden getrennt kalkuliert. Bestehender Rechner bleibt als eigenes Tool erhalten.</p></header><div class="calculator-board compact"><div class="calc-visual"><div class="spool"><span></span></div><div class="filament-line"></div><div class="hotend"><i></i></div><div class="layer-stack"><i></i><i></i><i></i><i></i><i></i></div></div><div class="calc-copy"><div class="metric-row"><span>STROMBASIS</span><strong>0,40 €/kWh</strong></div><div class="metric-row"><span>INPUT</span><strong>STL · 3MF · G-CODE</strong></div><div class="metric-row"><span>DRYING</span><strong>AMS 2 PRO</strong></div><a class="tool-launch" href="Druckkosten-Rechner/">KOSTENRECHNER STARTEN <b>→</b></a></div></div></section>
</main><footer><span>PRINTBENCH // dezender.de/3d-druck</span><span>PHP + JavaScript + WebGL</span><a href="https://github.com/jygnw29kms-bit/3d-Files" target="_blank">SOURCE ↗</a></footer>
<script>window.PRINTBENCH={api:'api.php'};</script><script type="module" src="workbench.js"></script>
</body></html>
