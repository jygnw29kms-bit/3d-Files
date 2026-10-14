<?php header('Content-Type: text/html; charset=UTF-8'); ?>
<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DEZENDER // P2S Control Center</title>
<link rel="stylesheet" href="final-master.css">
</head>
<body data-view="overview">
<div class="shell">
<aside class="side">
  <div class="brand"><div class="brandmark">D</div><div><b>DEZENDER</b><small>ADDITIVE SYSTEMS</small></div></div>
  <nav id="mainNav">
    <a data-view="overview" class="active"><i>01</i>&Uuml;BERSICHT</a>
    <a data-view="live"><i>02</i>LIVE DRUCK</a>
    <a data-view="history"><i>03</i>HISTORIE</a>
    <a data-view="material"><i>04</i>MATERIAL</a>
    <a data-view="ams"><i>05</i>AMS 2 PRO</a>
    <a data-view="stats"><i>06</i>STATISTIKEN</a>
    <a data-view="costs"><i>07</i>KOSTEN</a>
    <a data-view="projects"><i>08</i>PROJEKTE</a>
    <a data-view="spools"><i>09</i>SPULEN</a>
  </nav>
  <div class="side-machine"><img src="assets/bambu-official/p2s-1.jpg"><b>Bambu Lab<br>P2S</b><small>mit AMS 2 Pro</small></div>
  <div class="system-list"><strong>SYSTEM</strong><span><i></i>Online</span><span><i></i>MQTT Verbunden</span><span><i></i>Collector Aktiv</span><span><i></i>Daten werden gespeichert</span></div>
  <div class="sidefoot">DEZENDER.DE<br>3D-DRUCK</div>
</aside>
<main>
<header class="topbar">
  <div class="machine-head"><div class="machine-icon">D</div><div><h1 id="pageTitle">BAMBU LAB P2S</h1><p id="pageSub">PROFESSIONAL ADDITIVE MANUFACTURING</p></div></div>
  <div class="head-state"><span class="dot"></span><b id="machineState">ONLINE</b></div>
  <div class="clock"><b id="dateLabel">--.--.----</b><b id="clock">--:--</b><small>LIVE DATEN</small></div>
  <div class="ranges"><button class="active" data-range="live">LIVE</button><button data-range="24h">24H</button><button data-range="7d">7D</button><button data-range="30d">30D</button></div>
</header>
<div id="overviewView" class="view active">
  <section class="upper-master">
    <article class="machine-live panel-edge">
      <img id="machineLiveImage" class="machine-photo" src="runtime/media/latest.jpg" data-fallback="assets/bambu-official/p2s-2.jpg">
      <div class="machine-brand">Bambu Lab</div>
      <div class="cam-overlay"><b>LIVE LIVE</b><span>1080P &middot; LAN</span></div>
    </article>
    <div class="center-stack">
      <article class="panel status-panel">
        <div class="panel-title"><span class="title-icon">D</span> DRUCKSTATUS</div>
        <div class="job-row"><img src="assets/lst-clips.png"><div class="job-copy"><h2 id="jobName">Aktueller Druck</h2><p id="profile">--</p></div><div class="progress-ring" id="ring"><strong id="progress">--%</strong><small>Fortschritt</small></div></div>
        <div class="progressbar"><i id="barFill"></i></div>
        <div class="metrics three"><div><span>Layer</span><b id="layer">-- / --</b></div><div><span>Restzeit</span><b id="rest">--</b></div><div><span>Speed Level</span><b id="speed">--</b><small id="speedMag">--%</small></div></div>
        <div class="speed-strip"><span>OUTER <b id="outerSpeed">--</b></span><span>INNER <b id="innerSpeed">--</b></span><span>INFILL <b id="infillSpeed">--</b></span><span>TRAVEL <b id="travelSpeed">--</b></span></div>
      </article>
      <article class="panel temp-panel">
        <div class="panel-title"><span class="title-icon">02</span> TEMPERATUREN <span>LIVE</span></div>
        <div class="temp-head"><div class="orange"><span>D&Uuml;SE</span><b id="nozzle">--&deg;C</b></div><div class="blue"><span>BETT</span><b id="bed">--&deg;C</b></div></div>
        <canvas id="tempChart"></canvas>
      </article>
    </div>
    <div class="right-stack">
      <article class="panel hotend-panel"><div class="panel-title">HOTEND <span>SCHNITTANSICHT</span></div><img src="assets/hotend-blueprint.svg"><div class="hotend-read"><span>D&uuml;se (0,4 mm) <b id="nozzleTop">--&deg;C</b></span><span>Ziel <b id="nozzleTarget">--&deg;C</b></span></div></article>
      <article class="panel wifi-panel"><div class="panel-title">NET WLAN</div><div class="wifi-body"><div class="wifi-value"><b id="wifi">--</b><small>dBm</small></div><div class="signal-bars"><i></i><i></i><i></i><i></i></div></div><div class="mini-status"><span>MODE</span><b>LAN ONLY</b></div></article>
    </div>
  </section>
  <section class="middle-master">
    <article class="panel ams-panel"><div class="panel-title">AMS AMS 2 PRO <span>Material System</span></div><div class="ams-layout"><div class="ams-visual"><img src="assets/bambu-official/p2s-11.jpg"></div><div class="ams-slot"><span>Aktiver Slot</span><strong id="slot">--</strong><div class="spool-mini"></div><div id="amsSlotStrip" class="ams-slot-strip"></div><dl><div><dt>Material</dt><dd id="amsMat">--</dd></div><div><dt>Temperatur</dt><dd id="amsTemp">--&deg;C</dd></div><div><dt>Feuchte (raw)</dt><dd id="amsHum">--</dd></div><div><dt>RFID UID</dt><dd id="rfid">&mdash;</dd></div></dl></div></div></article>
    <article class="panel slicer-panel"><div class="panel-title">DATA SLICER / DRUCKDATEN</div><div class="slicer-body"><dl><div><dt>Profil</dt><dd id="dProfile">--</dd></div><div><dt>Hersteller</dt><dd id="vendor">--</dd></div><div><dt>Material</dt><dd id="material">--</dd></div><div><dt>Filament</dt><dd id="filament">--</dd></div><div><dt>Layer</dt><dd id="layers">--</dd></div><div><dt>Layerh&ouml;he</dt><dd id="lh">--</dd></div><div><dt>Infill</dt><dd id="infill">--</dd></div><div><dt>W&auml;nde</dt><dd id="walls">--</dd></div><div><dt>Modellzeit</dt><dd id="modelTime">--</dd></div><div><dt>Gesamtzeit</dt><dd id="totalTime">--</dd></div></dl><img src="assets/lst-clips.png"></div></article>
    <article class="panel cost-panel"><div class="panel-title">07 KOSTENRECHNER <span>KOMPAKT</span></div><div class="costrows"><span>Filament<b id="cMat">0,00 &euro;</b></span><span>Strom<b id="cPower">0,00 &euro;</b></span><span>Maschinenzeit<b id="cMachine">0,00 &euro;</b></span><span>Selbstkosten<b id="cSelf">0,00 &euro;</b></span><span>Marge<b id="cMargin">0,00 &euro;</b></span></div><div class="sell"><span>Verkaufspreis</span><strong id="cTotal">0,00 &euro;</strong></div><details><summary>PARAMETER</summary><div class="inputs"><label>&euro;/kg<input id="priceKg" value="18.99"></label><label>&euro;/kWh<input id="powerPrice" value="0.40"></label><label>&euro;/h<input id="machineRate" value="0.65"></label><label>Marge %<input id="margin" value="20"></label></div></details></article>
  </section>
  <section class="lower-master">
    <article class="panel toolpath-panel"><div class="panel-title">PATH TOOLPATH VISUALISIERUNG</div><img src="assets/toolpath-map.svg"><pre id="gcode">G1 X62.318 Y104.227 E0.013\nG1 X62.412 Y104.318 E0.011\nG1 X62.501 Y104.403 E0.012\nG1 X62.612 Y104.512 E0.014\nG1 X62.723 Y104.621 E0.014</pre></article>
    <article class="panel camera-panel"><div class="panel-title">NET LIVE KAMERA</div><img id="cameraLiveImage" src="runtime/media/latest.jpg" data-fallback="assets/bambu-official/p2s-2.jpg"><span class="rec">LIVE REC</span></article>
    <article class="panel gallery-panel"><div class="panel-title">GALLERY PRODUKTIONSGALERIE</div><div class="gallery"><figure><img src="assets/lst-clips.png"><figcaption><b>428er LST Clips</b><small>Aktueller Druck</small></figcaption></figure><figure><img src="assets/lst-klammer.png"><figcaption><b>24er LST Klammer</b><small>Projekt</small></figcaption></figure><figure><img src="assets/bambu-official/p2s-9.jpg"><figcaption><b>Individuelle Teile</b><small>Prototyping</small></figcaption></figure></div></article>
  </section>
</div>
<div id="subview" class="view"></div>
</main>
</div>
<script>window.LIVE_ENDPOINT='live-data.php';</script><script src="assets/qrcode.min.js"></script><script src="spool-manager.js"></script><script src="final-master.js"></script>
</body></html>