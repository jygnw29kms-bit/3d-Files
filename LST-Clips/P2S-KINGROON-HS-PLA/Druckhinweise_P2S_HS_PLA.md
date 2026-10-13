# Volle LST-Platte · P2S · KINGROON HS-PLA

## Ergebnis

`LST_428_P2S_KINGROON_HS_PLA.3mf` enthält **eine Platte mit 428 Clips**. Die geprüfte Belegung und Größenmischung bleiben erhalten: 296 kleine Clips mit ungefähr 3,83 mm Öffnung und 132 größere mit ungefähr 5,18 mm Öffnung, jeweils in 50°, 70° und 90°. Alle sind in Z auf 85 % skaliert, Druckhöhe ungefähr 6,38 mm. Der Abstand zwischen den konvexen Modellumrissen beträgt mindestens 1,5 mm. Die alte PETG-Datei bleibt unverändert.

## Identifiziertes Material

Das vom Nutzer bereitgestellte Rollenfoto zeigt **KINGROON HS-PLA**, Schwarz, **1,75 mm**, Kennzeichnung HCGS002, Charge 0616-6. Das Etikett nennt **210–230 °C** Düsentemperatur und **50–70 °C** Betttemperatur. Es nennt keinen maximalen Volumenstrom und keine individuell kalibrierte Flussrate.

Die neue Datei verwendet PLA statt PETG und das vollständige **offizielle P2S-Profil für die Standard-0,4-mm-Düse**. P1S-Start-/Endskripte wurden durch die originalen P2S-Skripte einschließlich ihrer Kühl- und Prüfabläufe ersetzt. Nicht mehr genutzte Materialzuordnungen aus dem ursprünglichen Fünf-Material-Projekt wurden entfernt. Ein High-Flow-Hotend wird nicht vorausgesetzt.

## Enthaltene Einstellungen

| Einstellung | Wert |
|---|---|
| Drucker / Platte | Bambu Lab P2S, 0,4 mm Standard, Textured PEI |
| Material | KINGROON HS-PLA Schwarz, einfarbig |
| Düse | erste Schicht 220 °C, danach 225 °C |
| Bett | erste Schicht 60 °C, danach 55 °C |
| Schichten | erste Schicht 0,20 mm, danach 0,24 mm |
| Wände | 3, Arachne; dünne Bereiche sind geometrisch begrenzt |
| Außen / Innen / Oberfläche | 100 / 160 / 80 mm/s |
| Kleine Konturen | 80 % der jeweiligen normalen Geschwindigkeit |
| Erste Kontur / erste Füllung | 35 / 50 mm/s |
| Volumenstrom | maximal 14 mm³/s als vorsichtiger, unkalibrierter Ausgangswert |
| Flussfaktor | 0,98 als Ausgangswert des Generic-PLA-High-Speed-Profils |
| Füllung | 15 % Gyroid, 3 Deck- und 3 Bodenschichten |
| Kühlung | erste Schicht ohne Teilelüfter; danach PLA-Kühlung bis 100 %; originale P2S-Kammerregelung bleibt erhalten |
| Leerfahrten | direktere Wege, bis 600 mm/s; Rückzug, Wischen und Auto-Lift aus dem P2S-Profil bleiben erhalten |
| Druckfolge | schichtweise; keine Stützen, kein Brim, kein Reinigungsturm |

14 mm³/s sind **keine vom Etikett bestätigte Leistungsgrenze**. Das mitgelieferte Generic-PLA-High-Speed-P2S-Profil erlaubt 18 mm³/s; für diese konkrete Rolle fehlt jedoch ein Durchflusstest. Höhere Sollgeschwindigkeiten können ohne diese Prüfung die tatsächliche Materialförderung überfordern. Der Drucker erreicht die nominalen 600 mm/s auf kurzen Leerfahrten nicht durchgehend.

## Vergleich und Validierung

Bambu Studio **2.08.02.61** hat die beiden Varianten bei gleicher Belegung, 3 Wänden und 14-mm³/s-Limit gesliced:

| Variante | Außen / Innen | Geschätzte Gesamtzeit | Material |
|---|---|---:|---:|
| **Enthaltene, gemäßigtere Variante** | **100 / 160 mm/s** | **5 h 32 min** | **72,12 g PLA** |
| Höhere Wandgeschwindigkeit | 120 / 180 mm/s | 5 h 29 min | 72,12 g PLA |

Die schnellere Variante spart nur ungefähr 3 Minuten. Deshalb enthält die Hauptdatei die gemäßigtere Wandgeschwindigkeit als Ausgangspunkt für saubere kleine Konturen. Dass sie auf deinem Drucker tatsächlich bessere Oberflächen liefert, muss ein Probeausdruck zeigen. Ein absolutes Geschwindigkeitsmaximum oder physisch bestätigte Druckqualität wird nicht behauptet.

Beide Slicer-Läufe endeten mit `Success`, Rückgabecode 0, einer Platte, einer verwendeten PLA-Sorte und leerer plattenbezogener Warnmeldung. Die Hauptdatei enthält weiterhin genau 428 Instanzen. Die Geometrie und Abstände wurden in der vorherigen Bearbeitung geprüft und bei der Profilumstellung unverändert übernommen. Die neue P2S-Passprobe wurde ebenfalls erfolgreich gesliced.

Die CLI meldet fehlende externe, vollständig aufgelöste Preset-Dateien und verwendet die vollständig eingebetteten Einstellungen. Ihr Gcode-Zeitparser meldet außerdem `Invalid T command (T65535)`: Diese Zeile steht unverändert im offiziellen P2S-Endskript im Abschnitt „pull back filament to AMS“, zwischen `M620 S65535` und `M621 S65535`. Die Meldung ist damit dem Zeitparser und dem offiziellen Endablauf zugeordnet, nicht einer selbst erfundenen Werkzeugwechselanweisung. Der Herstellerablauf wurde nicht entfernt oder verändert. Physisches Ausführen dieses Ablaufs wurde hier nicht getestet.

## Vor dem Druck

Die neue Datei in einer aktuellen Bambu-Studio-Version **als Projekt öffnen** und **P2S, die tatsächlich verbaute 0,4-mm-Standarddüse, Textured PEI und die schwarze HS-PLA-Rolle** kontrollieren. Bei anderer Düse, High-Flow-Hotend oder anderer Druckplatte braucht das Profil eine Anpassung. Neu slicen und die Vorschau prüfen; nicht das alte PETG-Projekt zum Drucken verwenden.

`LST_Passprobe_6_P2S_KINGROON_HS_PLA.3mf` enthält je einen Clip pro Winkel und Größe mit denselben Einstellungen. Vor der vollen Platte die Passprobe auf saubere Konturen, ausreichenden Zusammenhalt und passende Öffnung prüfen. PLA ist weniger elastisch und wärmebeständig als PETG; Clips nicht gewaltsam auf den Trieb drücken. Mit wachsendem Durchmesser rechtzeitig wechseln. Die Eignung folgt aus Triebmaß und Passprobe, nicht allein aus der vierten Pflanzenwoche.

## Quellen

- Rollenetikett im vom Nutzer bereitgestellten Foto: Material, Durchmesser und Temperaturbereiche.
- Offizielles Bambu-Studio-AppImage 2.08.02.61, dessen SHA-256 beim Herunterladen gegen den veröffentlichten Release-Digest geprüft wurde: [Bambu Studio Release](https://github.com/bambulab/BambuStudio/releases/tag/v02.08.02.61).
- Darin enthaltene Profile: `Bambu Lab P2S 0.4 nozzle`, `0.20mm Standard @BBL P2S`, `Generic PLA High Speed @BBL P2S` einschließlich ihrer Vererbungen und P2S-Gcode-Vorlagen.
- Die angepassten 0,24-mm-/Temperatur-/Geschwindigkeitswerte sind projektspezifische Ausgangswerte, kein separat validiertes KINGROON-Werksprofil.
