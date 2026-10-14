# ApolloX P2S Calibration v2 – Geometry validation

Validated 2026-10-14.

## Target
- Bambu Lab P2S
- 0.4 mm nozzle
- FormFutura ApolloX ASA, blue
- AMS 2 Pro (physical slot mapping remains a printer-side mapping)

## Label fix
All labels are now physically joined to their parent geometry with at least 0.15 mm volumetric overlap.

- A / B / C: embossed into first-layer coupons
- WALL 1.2: attached to front wall
- HOLES 3 5 8 10: attached to coupon front wall
- STRING: attached to the common stringing-test foot
- BRIDGE 10-40: attached to identification strip connected to the first bridge pair
- OVERHANG: attached to the solid front face
- 255 / 250 / 245 / 240 / 235: attached to the solid right side wall of each temperature segment
- TEMP: attached to the tower base
- 20mm XYZ: attached to cube front wall
- WALL FLOW: attached to a low identification strip
- APOLLOX P2S 0.4: attached to title tag

## Mesh validation
OpenSCAD CGAL render completed successfully.

Standalone temperature tower:
- watertight: yes
- connected components: 1
- tiny/floating components <20 mm³: 0
- bounds: 24.55 × 24 × 42 mm

Full calibration plate:
- watertight: yes
- connected components: 15
- tiny/floating components <20 mm³: 0
- the 15 components are intentional calibration objects, not text fragments
- bounds: about 188.55 × 184.5 × 42 mm

The former defect was reproduced and eliminated: temperature digits were originally placed over the tower's front calibration window and therefore had no solid wall to intersect. They now use the solid right side wall with 0.15 mm material overlap.
