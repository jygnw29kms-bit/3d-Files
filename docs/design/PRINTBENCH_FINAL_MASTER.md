# PRINTBENCH FINAL MASTER GUI

Status: **VERBINDLICH / DESIGN SOURCE OF TRUTH**
Freigabe: 2026-10-14
Native Desktop-Festlegung: 2026-10-15

Diese Datei beschreibt den freigegebenen PRINTBENCH FINAL-MASTER. Das zugehörige Masterbild liegt unter `docs/design/PRINTBENCH_FINAL_MASTER.webp` und ist die verbindliche visuelle Referenz.

## Unverhandelbare Regel

**FINAL ist FINAL.** Die Oberfläche wird nicht frei interpretiert und nicht nur "ähnlich" umgesetzt. Position, Hierarchie, Größenverhältnisse, Informationsdichte, Kartenaufbau, Hero-Gewichtung, Farbwelt und Navigationsstruktur werden am Master ausgerichtet. Technische Zwänge dürfen die Oberfläche intern beeinflussen, aber nicht als Ausrede für eine andere Produktoptik dienen.

## Verbindliche Desktop-Struktur

Die native PRINTBENCH-Ansicht unter `Device` folgt dieser Reihenfolge und Gewichtung:

1. PRINTBENCH-Kopfbereich mit Produktidentität und Gerätezustand.
2. Dominanter Hero mit Bambu Lab P2S + AMS 2 Pro als visuellem Kernelement.
3. Rechts davon Druckerstatus und Live-Kamera wie im Master.
4. Schnellsteuerung mit direkt erreichbaren Druck-/Licht-/Geschwindigkeitsaktionen.
5. Zweite Ebene: `Aktueller Druck`, `Temperaturen (Live)`, `AMS 2 Pro`.
6. Untere Ebene: `Gerätestatus`, `Letzte Drucke`, `System & Aktionen`.
7. Navigationspunkte, Kartenabstände und visuelle Gewichtung entsprechen dem Master und werden nicht durch Standard-Orca-Device-Layout ersetzt.

## Verbindliche Designregeln

- zentrale Hero-Zone mit P2S + AMS 2 Pro bleibt dominant
- Live-Kamera ist Bestandteil des sichtbaren Hauptbereichs, keine versteckte Unterseite
- dunkle Navy-/Schwarz-Grundfläche mit blauen Highlights, Grün für Online/Erfolg, Orange für Wärme/Trocknung und Rot für Stop/Fehler
- technische, dichte Dashboard-Optik statt generischer Landingpage
- keine Standard-Orca-Kartenoptik im PRINTBENCH-Bereich
- keine generische AI-Landing-Page-Optik
- Funktionen, die technisch noch nicht verfügbar sind, werden deaktiviert oder eindeutig als noch nicht verfügbar dargestellt; sie werden nicht vorgetäuscht
- bestehende Slicer-Funktionen dürfen erhalten bleiben, aber `Device -> PRINTBENCH` ist visuell ein eigenes Produkt

## Native Desktop-Architektur

Für die installierte Windows-Anwendung gilt verbindlich:

- Produktname/Ziel: **135er-PRINTBENCH**
- Orca dient als technische Slicer-Basis, nicht als sichtbare Produktidentität des Device-Centers
- `Device -> PRINTBENCH` ist ein **natives wxWidgets-Panel**
- keine WebView als finale PRINTBENCH-Desktopoberfläche
- kein Raspberry Pi als Pflicht für den Desktopbetrieb
- kein Bambu Studio erforderlich
- P2S und AMS 2 Pro werden direkt vom PC im LAN abgefragt und gesteuert
- der native Collector verwendet die lokale Orca/Bambu-Maschinen- und Netzwerklogik und ergänzt PRINTBENCH-spezifische Zustände
- das gepinnte native LAN-Netzwerkmodul wird vom PRINTBENCH-Build bereitgestellt und beim Start integritätsgeprüft
- Kamera wird nativ über den lokalen P2S-Stream eingebunden
- Steueraktionen sind zustands- und capability-gated; keine unvalidierten Raw-MQTT-/G-Code-Fluchtwege in der UI

Der Pi bleibt optional für Browser-/Mobile-/Always-on-Funktionen, ist aber **keine Desktop-Abhängigkeit**.

## Desktop

- Desktop ist die primäre Referenzansicht.
- Zielbereich: 1440–1920 px Breite.
- Der Hero bleibt dominant und die Dashboard-Karten behalten die im Master gezeigte visuelle Gewichtung.
- Bei kleineren Fenstern darf umgebrochen/gescrollt werden; Karten dürfen nicht abgeschnitten oder in eine andere Informationshierarchie verschoben werden.

## Tablet und Mobile

Die Browser-/Mobile-Ausgabe verwendet dieselbe Designsprache und Informationshierarchie, aber mit responsive Reflow statt Desktop-Zoom.

- Zielbereiche: Tablet ca. 768–1366 px, Mobile ca. 360–480 px.
- Live-Kamera und Schnellsteuerung bleiben unmittelbar erreichbar.
- Navigation wird touchfreundlich umgesetzt.
- Karten werden sinnvoll gestapelt statt gequetscht.
- AMS-Slots werden als 2er-Raster oder horizontal scrollbare Cards umgesetzt.
- Touch-Ziele und Statuswerte müssen auf iPhone/Safari vollständig sichtbar und bedienbar sein.
- keine abgeschnittenen Tabellen, Panels oder versteckten Kernfunktionen.

## Abnahmekriterium

Ein Build ist optisch **nicht fertig**, solange ein direkter Vergleich mit dem Master deutliche Abweichungen bei Grundlayout, Hero, Kartenanordnung, Größenverhältnissen oder Informationshierarchie zeigt. Funktionierende Technik allein ist keine Freigabe des UI.
