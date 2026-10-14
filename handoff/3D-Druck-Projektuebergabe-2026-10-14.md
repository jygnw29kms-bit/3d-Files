# 3D-Druck / PRINTBENCH — Projektübergabe

Stand: 14.10.2026, Europe/Berlin. Dieses Dokument übergibt ausschließlich das
3D-Druck-Projekt an einen anderen Chat. Grow Central bleibt ein getrenntes
Grow-/Sensorprojekt. Die Desktop-App-Entwicklung wurde auf Nutzerwunsch gestoppt.

## 1. Auftrag für den übernehmenden Chat

Arbeite ausschließlich am 3D-Druck-Projekt PRINTBENCH / DEZENDER im Repository
https://github.com/jygnw29kms-bit/3d-Files . Keine Drucker-/Slicer-Funktionen in
Grow Central einbauen. Lies zuerst diese Übergabe, den Collector-README und den
Checkpoint. Unterscheide veröffentlichte Quelltexte, laufende Installation,
Hardwareprüfung und neue Entwürfe. Bestehende Dateien und Lizenzangaben erhalten.

Der aktuelle Zielwunsch: eine plattformübergreifende lokale App ähnlich
OrcaSlicer, mit Slicer, P2S-Steuerung, AMS-2-Pro-Daten und dem bestehenden
Webprojekt. Optional kann der Nutzer seinen eigenen Webspace verbinden und
eine Fernbedienungs-/Dashboard-Kopie ohne Slicer im Web betreiben. Ohne laufenden
PC sind fehlende Live-Daten ausdrücklich akzeptabel. Ein Pi ist damit optional,
keine zwingende Voraussetzung für die spätere App.

Der Nutzer möchte JL1976 P2S Control als mögliche Basis und OrcaSlicer nutzen.
Der Nutzer hat die Link-Anfrage inzwischen ausdrücklich zurückgestellt;
der Name der künftigen App bleibt offen. Der genaue JL1976-Repository-Link fehlt.
Nicht irgendein ähnlich benanntes
Projekt übernehmen. Vollständige Bambu-Unabhängigkeit und „alle Funktionen“
sind Zielwünsche, keine bereits nachgewiesenen Eigenschaften.

## 2. Repositories, Website und Branches

3D-Repository: https://github.com/jygnw29kms-bit/3d-Files

Bisherige öffentliche Website: https://www.dezender.de/3d-druck/
Der aktuelle Livezustand wurde für diese Übergabe nicht erneut hardwareseitig geprüft.

Collector-Korrekturen:
https://github.com/jygnw29kms-bit/3d-Files/tree/fix/collector-camera-on-demand

Übergabe samt ausgelagerten Dateien und gestopptem Desktop-Entwurf:
https://github.com/jygnw29kms-bit/3d-Files/tree/handoff/3d-printing-2026-10-14

Grow-Central-Trennung:
https://github.com/jygnw29kms-bit/135er-Grow-Central/tree/refactor/separate-3d-printing

Diese Änderungen liegen auf separaten Branches; kein Merge nach main/master und
kein Live-Deployment wurden für die Übergabe durchgeführt. Historische Releases
und Git-Historie behalten ihre ursprünglichen Inhalte. Durch einen Branch-Push
werden vorhandene Dateien auf einem Webserver nicht automatisch entfernt.

## 3. Was aus Grow Central ausgelagert wurde

18 Dateistände wurden unverändert und mit SHA256-Abgleich gesichert:
OpenSCAD-Quelle, sieben STL-Dateien, zwei P2S-Prozessprofile, drei Vorschaubilder,
ein historischer Deployment-Trigger und vier Workflow-Archive (einschließlich
der späteren Deployment-Version und Firewall-Diagnose von origin/master).

Neuer Modellpfad: Hardware/Grow-Central-RPi4/
Provenienz und vollständige Dateiliste:
handoff/grow-central-extraction/manifest.json
Quellstand: b793ec426e378bd728ec2de8c43b2305fe34c68e.

In Grow Central entfernt: PRINTBENCH-Deployment-Workflow, Gehäuse-STL-Buildworkflow,
3D-Downloads/Modelle/Profile/Vorschaubilder, Gehäusebereich und Navigation der
öffentlichen Website. Der Grow-Website-Deployment-Workflow wurde auf die
verbleibenden Grow-Dateien beschränkt.

Die Workflow-Archive sind bewusst inaktive .txt-Dateien im 3D-Repository.
Sie referenzieren alte Pfade und Grow-Central-Secrets. Keine Zugangsdaten wurden
kopiert. Aktivierung erfordert eine separate Anpassung und Transportprüfung.

Grow-Central-Kamera/FFmpeg für Pflanzenkameras ist keine Druckerfunktion und
bleibt erhalten. Ein pauschales Entfernen von FFmpeg würde Grow-Funktionen stören.
Die Sensor-/USB-/Home-Assistant-Arbeit gehört nicht in dieses 3D-Projekt.

## 4. Drucker, Filament und ursprünglicher Auftrag

Drucker: Bambu Lab P2S, AMS 2 Pro. Für die optimierten Clip-Platten wurde eine
0,4-mm-Standarddüse und Textured-PEI-Platte zugrunde gelegt.

Hochgeladene Ausgangsdatei: LST_clips_petg.3mf. Nutzer wollte drei Platten auf
eine zusammenführen, Teile etwas kleiner für ungefähr 3–5 mm starke Triebe,
volle Platte, kurze Druckzeit und gute Qualität. Das Pflanzenalter allein ist
kein belastbares Maß für die Clip-Passform. 85 % war eine frühere Annahme;
entscheidend sind die tatsächlich erzeugten Öffnungen und ein Probeausdruck.

Filamentfoto: KINGROON 3D, HCGS002, schwarz, HS-PLA 1,75 mm.
Etikett: Düse 210–230 °C, Bett 50–70 °C, Charge 0616-6.
Das Material ist HS-PLA, nicht PETG, obwohl der Upload PETG im Dateinamen trägt.
Etikettwerte sind Materialangaben, kein Nachweis eines kalibrierten maximalen
Volumenstroms oder optimaler Geschwindigkeit auf der konkreten Maschine.

## 5. Fertige Clip-Dateien und Prüfstand

Pfad: LST-Clips/P2S-KINGROON-HS-PLA/
Volle Platte: LST_428_P2S_KINGROON_HS_PLA.3mf
Passprobe: LST_Passprobe_6_P2S_KINGROON_HS_PLA.3mf
Komplettpaket: P2S_KINGROON_LST_Druckpaket.zip
Details: README.md, Druckhinweise_P2S_HS_PLA.md, plattenbelegung.png.

428 Clips, drei Winkel und zwei Öffnungsgrößen, ungefähr 3,83 und 5,18 mm.
Profil: 0,24-mm-Schichten, drei Wandlinien, P2S/0,4 mm, HS-PLA schwarz.
Erfolgreich in Bambu Studio 2.08.02.61 gesliced. Slicer-Schätzung für die
VOLLE 428er-Platte: 5 h 32 min und 72 g PLA. Diese Zeit ist nicht die Druckzeit
der sechs Passproben und keine gemessene reale Laufzeit.

Keine physische Passform-/Druckqualitätsprüfung bestätigt. Vor einer ganzen
Platte sechs Passproben drucken. Eine absolute „maximal mögliche Geschwindigkeit
bei guter Qualität“ einschließlich optimaler Verfahrwege wurde nicht bewiesen.

Designer MDKaiser; Ausgangs-3MF nennt MakerWorld Exclusive License.
Designer-/Lizenzmetadaten sind in den 3MF erhalten. Keine neue Modelllizenz und
keine pauschale Freigabe zur Verbreitung ableiten.

Direkter Plattenlink:
https://github.com/jygnw29kms-bit/3d-Files/raw/refs/heads/main/LST-Clips/P2S-KINGROON-HS-PLA/LST_428_P2S_KINGROON_HS_PLA.3mf

## 6. Separates LST-Klammer-Projekt

Pfad: LST-Klammer/. Datei: LST-Klammer-P2S-24x-4mm.3mf.
Einzel-STL: LST-Klammer-4mm.stl. Paket: LST-Klammer-Download.zip.
Prüfbericht: Pruefbericht.json.

24 Klammern. Gerade Schenkel von ca. 1,33 auf 4 mm verstärkt.
Außenmaße ca. 20 × 149,83 × 4 mm. Innere gerade Öffnung ca. 8,67 mm.
Mindestabstand ca. 1,49 mm; Plattenrand ca. 4,76 mm.
Geometrie wasserdicht/manifold geprüft. Dieses Projekt wurde NICHT gesliced und
nicht physisch gedruckt. Übernommenes Profil nennt Generic PLA Silk in Slot 2;
nicht mit dem kalibrierten HS-PLA-Clip-Profil verwechseln.

Originalmodell: „LST helper (low stress training for plants)“, extrawitz.
Die Ausgangsdatei nennt Standard Digital File License. Originalbedingungen gelten.

## 7. Bestehendes Webprojekt

PHP/HTML/CSS/JavaScript, noch keine fertige Crossplattform-Desktop-App.
Wichtige Dateien: index.php, final-master.js, final-master.css, ingest.php,
live-data.php, media-ingest.php, media-data.php, api.php, assets/.

Vorhandene Bereiche: Übersicht, Live-Druck, Historie, Material, AMS, Statistiken,
Kosten und Projekte. Druckkosten-Rechner/ verarbeitet STL/3MF/G-Code und rechnet
Filament, Strom, Maschinenzeit, Ausschuss, Vorbereitung und Marge.
Strompreis bisher standardmäßig 0,40 €/kWh. Tatsächliche kWh sind ohne Messgerät
nicht nachgewiesen; berechnete Werte sichtbar von Messwerten unterscheiden.

Checkpoint-Datei PRINTBENCH-CHECKPOINT-2026-10-13.md hat inhaltlich den Stand
14.10.2026. Sie dokumentiert frühere Kamera-/FTPS-/Live-Prüfungen, ist aber kein
neuer Hardwaretest dieser Übergabe.

## 8. Collector und Druckerschnittstellen

Pfad: tools/printbench_collector/.
Dauerlauf: daemon.py. Telemetrie/Normalisierung: collector.py.
Website-Push: push_live.py. Fallback-Transport: server_transport.py.
Medien: media_worker.py, native_media.py.
Drucksitzungen: session_tracker.py, session_export.py.
Lokale Datenbank: printbench.db; Laufzeitdaten, nicht nach Git kopieren.

Protokolle laut bisherigem Checkpoint: MQTT/TLS 8883; RTSPS-Kamera 322;
implizites FTPS 990 mit TLS-Session-Reuse. Native Medien unter /timelapse und
/timelapse/thumbnail. Gemeldeter Kamerastream: H.264, 1920×1080, 30 FPS.
Diese Werte beim erneuten Hardwarezugriff verifizieren.

Erfasst werden u. a. Druckstatus, Fortschritt, Restzeit, Layer, Temperaturen,
Geschwindigkeit, Lüfter, Fehler/HMS sowie AMS-Slots und Trocknungsdaten, soweit
die Druckerfirmware sie meldet. Historien und Drucksitzungen werden lokal gespeichert.
Vollständige bidirektionale Orca-ähnliche Druckersteuerung ist im bestehenden
Collector noch nicht implementiert.

## 9. Nervende SSH-/CMD-Fenster: Ursache und Korrektur

Nutzer: Druckerdaten weiter, Fenster weg, Kamera bei Bedarf; anschließend klar
präzisiert: FFmpeg nicht auf dem PC, Verarbeitung auf dem Webserver.

Ursache im Code: wiederholte SSH-Fallback-Aufrufe bei fehlgeschlagenem HTTPS-Push
und früher ein dauerhaft neu gestarteter FFmpeg-Medienworker. Versteckter Start
von Python allein versteckt seine SSH-/FFmpeg-Kindprozesse nicht zuverlässig.
Die tatsächliche Herkunft jedes PC-Fensters ist ohne PC-Prozessprüfung offen.

Commit ee5a5ca: quiet_process.py, CREATE_NO_WINDOW für SSH/FFmpeg;
explizite, ablaufende Kamera-Freigabe statt Dauerstart.
Commit dde2731: Windows/Standard-daemon überträgt nur Telemetrie und lädt keinen
Medienworker. Linux --server-media erlaubt den Kamera-Worker. Windows lehnt diese
Option ab. Serverzugänge per geschützter JSON-Datei statt Bambu-Studio-Windowsdatei.
Commit 2ce5239: fix-windows-quiet.ps1 für gezielte Aktualisierung/Neustart.

Sieben automatisierte Python-Tests bestanden für Kamera-Aus/Ablauf, versteckte
Windows-Kindprozesse, Servermodus und Zugangsdateien. PowerShell-Skript wurde
hier nicht auf Windows ausgeführt: Windows/Pwsh ist nicht verfügbar.

Die Korrektur ist im Git-Branch, nicht auf dem Nutzer-PC installiert. Das Skript
lädt drei gepinnte Python-Dateien mit SHA256-Prüfung, sichert alte Dateien,
beendet nur erkannte Collector-Prozesse/direkte SSH-/FFmpeg-Kinder und startet
pythonw. Es kann den Ordner über -CollectorPath erhalten. Vorhandene passende
Startup-Verknüpfungen werden angepasst; andere Autostartmechanismen sind separat
zu prüfen. Zugangscodes, Token, Datenbank und Medien sollen erhalten bleiben.

Direkter Skriptlink:
https://raw.githubusercontent.com/jygnw29kms-bit/3d-Files/fix/collector-camera-on-demand/tools/printbench_collector/fix-windows-quiet.ps1

## 10. Webserver ohne VPN und optionale Bridge

Ein öffentlicher Webserver kann den privaten Drucker ohne Netzwerkbrücke nicht
direkt erreichen. Der Browser selbst ersetzt keine serverseitige Kameraverarbeitung.
Nutzer möchte kein VPN. Mögliche Lösung: lokale Bridge mit ausgehender,
verschlüsselter Stream-/Datenverbindung; FFmpeg verarbeitet auf dem Webserver.
Diese vollständige Streaming-Bridge wurde noch NICHT implementiert.

Pi 3 ist voraussichtlich ausreichend ohne Video-Neukodierung, bevorzugt per LAN.
Pi Zero 2 W ist eine kompakte Alternative, abhängig von WLAN/Streamstabilität.
ESP32/klassischer Arduino sind keine geeignete vollwertige RTSPS-/Video-Bridge.
Diese Einschätzung ist keine gemessene Last-/Stabilitätsprüfung.

Der spätere App-Wunsch akzeptiert ausdrücklich: PC aus = keine neuen Live-Daten.
Damit kann die erste Desktop-Version ohne Pi auskommen. Webbefehle bei offline
lokaler App dürfen nicht später unbemerkt ausgeführt werden. Befehle brauchen
kurze Gültigkeit, Authentifizierung, Rückmeldung und Schutz vor Wiederholung.
Druckerports nicht öffentlich freigeben.

## 11. OrcaSlicer / JL1976 / gestoppter App-Entwurf

Geprüftes Orca-Upstream: https://github.com/OrcaSlicer/OrcaSlicer
Geprüfter Main-Commit: 6e42a9b0ae572b6b57454cd9f18c648d0ac55571.
GitHub meldete neuestes Release v2.4.2 mit Windows-, macOS- und Linux-Artefakten.
Lizenz: AGPL-3.0 laut LICENSE.txt und README. Das optionale Bambu-Netzwerkplugin
basiert laut README auf nicht freien Bibliotheken. Fork/Verteilung müssen die
jeweiligen Lizenzbedingungen berücksichtigen. Die Modelllizenzen bleiben getrennt.

Ein Fork namens PRINTBENCH-OrcaSlicer wurde über die GitHub-API versucht;
HTTP 403 „Resource not accessible by integration“. KEIN Fork wurde erstellt.
Kein Orca-Quellcode wurde in Grow Central integriert. JL1976-Code wurde nicht
übernommen; Link und Lizenz bleiben offen.

Gestoppter, ungetesteter Entwurf: handoff/desktop-draft/apps/printbench/.
Vorhanden sind nur pyproject.toml, __init__.py, storage.py und printer.py.
Angedacht: Python/FastAPI, Qt/PySide6-Hülle, lokale Datenbank, System-Keyring,
MQTT-Teilberichte zusammenführen, TLS-Fingerprint-Pinning, begrenzte Kommandos.

NICHT fertig: Launcher/Entry-Point, Desktop-UI, API-Authentifizierung, Webkopie,
Befehlsrückkanal, Slicer-Einbettung, AMS-Steuerung, Installer und Build-Pipeline.
Die prototypischen Pause/Resume/Stop/Speed/Light-Payloads sind kein Nachweis der
Kompatibilität mit realer P2S-Firmware. Entwurf nicht als produktive App installieren.

## 12. Zugriff und sichere Übergabe

Diese Sitzung läuft in einer Cloud-Umgebung /workspace, obwohl der Nutzer die
Desktop-App auf seinem PC nutzt. Kein verfügbarer SSH-Zugang zum PC „bnd“, keine
SSH-Schlüssel/-Konfiguration und kein nutzbares DCO-Werkzeug wurden gefunden.
Nicht behaupten, der PC sei repariert oder ein Server bereits umgestellt.
Bestehende Zugänge in einer neuen lokalen/verbundenen Sitzung erneut prüfen.

Keine Passwörter, LAN-Zugangscodes, Push-Token, SSH-Schlüssel, rohe RFID-IDs oder
private Laufzeitdaten befinden sich in dieser PDF. Secret-Dateien nicht in Git
aufnehmen und Werte nicht im Chat anfordern. Historische SSH-Hostkey-Bypassoptionen
und ungeschützte öffentliche Steuerendpunkte nicht aus Altcode übernehmen.

## 13. Empfohlene nächste Arbeit im separaten Chat

1. Übergabe-Branch holen; Grow-Central-Trennung als separate Änderung prüfen.
2. Tatsächlichen Windows-Collector feststellen und den Fenster-Fix anwenden.
3. JL1976-Anfrage vorerst ignorieren; App-Namen/Basis erst mit dem Nutzer klären.
4. Entscheiden, ob echte Orca-Fork-Integration oder separate Desktop-Hülle mit
   Orca-Anbindung umgesetzt wird; den Unterschied klar benennen.
5. Lokales P2S/AMS-Lesen und unterstützte Steuerbefehle mit der realen Firmware
   testen; Verbindung, Aktualität und Ausführungsbestätigung sichtbar machen.
6. Plattformübergreifenden Launcher/UI/Installer bauen, das vorhandene Webprojekt
   einschließlich Kosten/Projekte/History integrieren.
7. Optionale authentifizierte Webkopie und ausgehenden Befehlsrückkanal bauen.
   Ohne lokale App: offline zeigen, keine alten Befehle nachträglich ausführen.
8. Kamera-Verarbeitung auf Webserver optional ergänzen; ohne laufende lokale
   Bridge/App keine neue Kamera behaupten. Pi-Bridge nur bei Bedarf weiterbauen.
9. Reale abgeschlossene Drucksitzung, Historienkosten und Medienretention prüfen.
10. Erst nach Passprobe eine ganze 428er-Clip-Platte drucken; Zeiten/Qualität messen.

## 14. Unmittelbar in den anderen Chat kopierbarer Startauftrag

„Übernimm ausschließlich das separate 3D-Druck-Projekt PRINTBENCH/DEZENDER aus
jygnw29kms-bit/3d-Files, Branch handoff/3d-printing-2026-10-14. Lies die beigefügte
PDF vollständig. Grow Central darf keine Drucker-/Slicer-/PRINTBENCH-Funktionen
mehr erhalten. Zuerst den SSH/CMD-Fenster-Fix auf meinem tatsächlichen PC prüfen
und anwenden. Danach die lokale Crossplattform-App mit P2S/AMS-Steuerung,
OrcaSlicer-Anbindung und bestehendem Webprojekt entwickeln. Optional eigene
Webspace-Kopie ohne Slicer, mit authentifizierter Fernsteuerung. Kein VPN nötig;
PC aus und keine Live-Daten ist akzeptiert. JL1976-P2S-Control-Repository erst
nach eindeutigem Link/Lizenzcheck verwenden. Vorhandene Druckmodelle und ihre
Lizenzen erhalten. Nicht getestete Entwürfe und noch nicht installierte
Änderungen nicht als fertig melden.“
