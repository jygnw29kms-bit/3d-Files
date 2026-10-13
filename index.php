<?php header('Content-Type: text/html; charset=UTF-8'); ?>
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DEZENDER // Additive Systems</title>
  <link rel="stylesheet" href="final-master.css">
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="logo"><div class="mark">D</div><div><b>DEZENDER</b><span>ADDITIVE SYSTEMS</span></div></div>
    <nav>
      <a class="active">&Uuml;BERSICHT</a><a>LIVE DRUCK</a><a>HISTORIE</a><a>MATERIAL</a>
      <a>AMS 2 PRO</a><a>STATISTIKEN</a><a>KOSTEN</a><a>PROJEKTE</a>
    </nav>
    <div class="printer-mini"><img src="assets/bambu-official/p2s-1.jpg" alt="Bambu Lab P2S"><b>Bambu Lab P2S</b><span>mit AMS 2 Pro</span></div>
    <div class="sys"><span><i></i>Online</span><span><i></i>MQTT verbunden</span><span><i></i>Collector aktiv</span><span><i></i>Daten werden gespeichert</span></div>
    <div class="sidefoot">DEZENDER.DE<br>3D-DRUCK</div>
  </aside>
  <main>
    <header class="top">
      <div><h1>BAMBU LAB P2S</h1><p>PROFESSIONAL ADDITIVE MANUFACTURING</p></div>
      <div class="online"><i></i> ONLINE</div>
      <div class="time"><b id="clock">--:--</b><span>LIVE DATEN</span></div>
      <div class="range"><button class="active">LIVE</button><button>24H</button><button>7D</button><button>30D</button></div>
    </header>
    <section class="grid hero">
      <article class="printer-view"><img class="printer-photo" src="assets/bambu-official/p2s-2.jpg" alt="Bambu Lab P2S"><div class="livebadge">LIVE</div></article>
      <article class="status">
        <div class="section-head">DRUCKSTATUS</div>
        <div class="status-main"><img src="assets/lst-clips.png" alt="Druckplatte"><div class="job"><h2 id="jobName">LST Clips Platte 428er</h2><p id="profile">KINGROON HS-PLA Black @BBL P2S</p></div><div class="ring" id="ring"><strong id="progress">--%</strong><span>Fortschritt</span></div></div>
        <div class="bar"><i id="barFill"></i></div>
        <div class="triples"><div><span>Layer</span><b id="layer">-- / --</b></div><div><span>Restzeit</span><b id="rest">-- min</b></div><div><span>Speed Level</span><b id="speed">--</b></div></div>
      </article>
      <article class="hotend"><div class="section-head">HOTEND <small>SCHNITTANSICHT</small></div><img src="assets/bambu-official/p2s-5.jpg" alt="P2S Hotend"></article>
    </section>
    <section class="grid mid">
      <article class="ams"><div class="section-head">AMS 2 PRO</div><div class="ams-body"><div class="ams-photo"><img src="assets/bambu-official/p2s-11.jpg" alt="AMS 2 Pro"><div class="ams-slot-glow">2</div></div><div class="ams-info"><b>Aktiver Slot <strong id="slot">2</strong></b><span>Material <strong id="amsMat">PLA</strong></span><span>Temperatur <strong id="amsTemp">--&deg;C</strong></span><span>Feuchte <strong id="amsHum">--</strong></span><span>RFID UID <strong id="rfid">&mdash;</strong></span></div></div></article>
      <article class="temps"><div class="section-head">TEMPERATUREN <small>(LIVE)</small></div><div class="temp-kpis"><div class="orange"><span>D&uuml;se</span><b id="nozzle">--&deg;C</b></div><div class="blue"><span>Bett</span><b id="bed">--&deg;C</b></div></div><canvas id="tempChart"></canvas></article>
      <article class="wifi"><div class="section-head">WLAN</div><b id="wifi">-- dBm</b><div class="bars"><i></i><i></i><i></i><i></i></div></article>
    </section>
    <section class="grid data">
      <article class="slicer"><div class="section-head">SLICER / DRUCKDATEN</div><dl><div><dt>Profil</dt><dd id="dProfile">--</dd></div><div><dt>Hersteller</dt><dd id="vendor">--</dd></div><div><dt>Material</dt><dd id="material">--</dd></div><div><dt>Filament</dt><dd id="filament">--</dd></div><div><dt>Layer</dt><dd id="layers">--</dd></div><div><dt>Layerh&ouml;he</dt><dd id="lh">--</dd></div><div><dt>Infill</dt><dd id="infill">--</dd></div><div><dt>W&auml;nde</dt><dd id="walls">--</dd></div><div><dt>Modellzeit</dt><dd id="modelTime">--</dd></div><div><dt>Gesamtzeit</dt><dd id="totalTime">--</dd></div></dl><img src="assets/lst-clips.png" alt="Slicer Platte"></article>
      <article class="cost"><div class="section-head">KOSTENRECHNER <small>(KOMPAKT)</small></div><div class="costrows"><span>Filament <b id="cMat">0,00 &euro;</b></span><span>Strom <b id="cPower">0,00 &euro;</b></span><span>Maschinenzeit <b id="cMachine">0,00 &euro;</b></span><span>Selbstkosten <b id="cSelf">0,00 &euro;</b></span><span>Marge <b id="cMargin">0,00 &euro;</b></span></div><div class="sell"><span>Verkaufspreis</span><strong id="cTotal">0,00 &euro;</strong></div><details><summary>Kalkulation anpassen</summary><div class="inputs"><label>&euro;/kg<input id="priceKg" value="18.99"></label><label>&euro;/kWh<input id="powerPrice" value="0.40"></label><label>&euro;/h<input id="machineRate" value="0.65"></label><label>Marge %<input id="margin" value="20"></label></div></details></article>
    </section>
    <section class="grid bottom">
      <article class="toolpath"><div class="section-head">TOOLPATH VISUALISIERUNG</div><img src="assets/toolpath-map.svg" alt="Toolpath"><pre id="gcode">G1 X62.318 Y104.227 E0.013
G1 X62.412 Y104.318 E0.011
G1 X62.501 Y104.403 E0.012
G1 X62.612 Y104.512 E0.014
G1 X62.723 Y104.621 E0.014</pre></article>
      <article class="camera"><div class="section-head">LIVE KAMERA</div><img src="assets/bambu-official/p2s-2.jpg" alt="P2S Live Camera"><span>REC</span></article>
      <article class="gallery"><div class="section-head">PRODUKTIONSGALERIE</div><div class="gallery-row"><figure><img src="assets/lst-clips.png" alt="428er Clips"><figcaption>428er LST Clips</figcaption></figure><figure><img src="assets/lst-klammer.png" alt="24er Klammern"><figcaption>24er LST Klammer</figcaption></figure><figure><img src="assets/bambu-official/p2s-9.jpg" alt="Individuelle Teile"><figcaption>Individuelle Teile</figcaption></figure></div></article>
    </section>
  </main>
</div>
<script>window.LIVE_ENDPOINT='live-data.php';</script>
<script src="final-master.js"></script>
</body>
</html>
