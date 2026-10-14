# PRINTBENCH FINAL MASTER GUI

Status: **VERBINDLICH / DESIGN SOURCE OF TRUTH**
Freigabe: 2026-10-14

Diese Datei beschreibt den freigegebenen PRINTBENCH FINAL-MASTER. Das zugehörige Masterbild liegt unter `docs/design/PRINTBENCH_FINAL_MASTER.webp`.

## Verbindliche Regeln

- Das Masterbild ist die visuelle Referenz für PRINTBENCH.
- Layout, Proportionen, Panel-Anordnung, Informationsdichte, Hierarchie, Dark-Mode-Sprache und Hero-Aufbau sind verbindlich.
- Die zentrale Hero-Zone mit Bambu Lab P2S + AMS 2 Pro bleibt das visuelle Kernelement.
- Navigation, Live-Kamera, Schnellsteuerung, Druckstatus, Temperatur-/Telemetrie-Karten, AMS-Slots, Historie, Gerätestatus und Systemaktionen orientieren sich an exakt dieser Informationsarchitektur.
- Keine generische AI-Landing-Page-Optik und keine freie Neuinterpretation des Masters.
- Funktionen, die technisch noch nicht verfügbar sind, werden sichtbar deaktiviert oder als `In Progress` gekennzeichnet; sie werden nicht vorgetäuscht.

## Desktop

- Desktop ist die primäre Referenzansicht.
- Zielbereich: 1440–1920 px Breite.
- Der Hero bleibt dominant und die Dashboard-Karten behalten die im Master gezeigte visuelle Gewichtung.

## Tablet und Mobile

- Responsive Umsetzung ohne Desktop-Zoom-Tricks.
- Zielbereiche: Tablet ca. 768–1366 px, Mobile ca. 360–480 px.
- Der Hero bleibt erhalten, wird aber kompakter angeordnet.
- Live-Kamera und Schnellsteuerung bleiben unmittelbar erreichbar.
- Navigation wird für Mobile touchfreundlich umgesetzt.
- Karten werden sinnvoll gestapelt statt gequetscht.
- AMS-Slots werden als 2er-Raster oder horizontal scrollbare Cards umgesetzt.
- Touch-Ziele und Statuswerte müssen auf iPhone/Safari zuverlässig bedienbar und vollständig sichtbar sein.
- Keine abgeschnittenen Tabellen, Panels oder versteckten Kernfunktionen.

## Architekturbezug

Die visuelle Umsetzung bleibt von der Device-API getrennt. PRINTBENCH/Orca zeigt Zustände und Controls; Rohzugänge, Tokens und Protokolldetails bleiben hinter dem sicheren Device-/Bridge-Layer.
