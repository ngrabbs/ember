# Samtec connector pad acceptance — 2026-09-09

Source: Samtec ESQ series drawing revision CM, Figure 4 socket opening view, interpreted as mating face; ESQ-SDT specifies 2.54 mm pitch and 1.02 mm holes. Physical stack alignment is NOT yet accepted.
https://suddendocs.samtec.com/prints/esq-1xx-xx-x-x-xxx-xx-x-xx-mkt.pdf
https://suddendocs.samtec.com/prints/esq-sdt.pdf

## ESQ-120-14-G-S

All pins passive. Front/mating view at zero rotation; coordinates relative to footprint center. Single row runs 1–20 downward. Double row runs odd right/even left; viewing the solder side reverses left/right.

| Symbol pin / physical lead / pad | x (mm) | y (mm) | Readback |
|---|---:|---:|---|
| 1 | 0.00 | -24.13 | Pass |
| 2 | 0.00 | -21.59 | Pass |
| 3 | 0.00 | -19.05 | Pass |
| 4 | 0.00 | -16.51 | Pass |
| 5 | 0.00 | -13.97 | Pass |
| 6 | 0.00 | -11.43 | Pass |
| 7 | 0.00 | -8.89 | Pass |
| 8 | 0.00 | -6.35 | Pass |
| 9 | 0.00 | -3.81 | Pass |
| 10 | 0.00 | -1.27 | Pass |
| 11 | 0.00 | 1.27 | Pass |
| 12 | 0.00 | 3.81 | Pass |
| 13 | 0.00 | 6.35 | Pass |
| 14 | 0.00 | 8.89 | Pass |
| 15 | 0.00 | 11.43 | Pass |
| 16 | 0.00 | 13.97 | Pass |
| 17 | 0.00 | 16.51 | Pass |
| 18 | 0.00 | 19.05 | Pass |
| 19 | 0.00 | 21.59 | Pass |
| 20 | 0.00 | 24.13 | Pass |
## ESQ-126-39-G-D

All pins passive. Front/mating view at zero rotation; coordinates relative to footprint center. Single row runs 1–20 downward. Double row runs odd right/even left; viewing the solder side reverses left/right.

| Symbol pin / physical lead / pad | x (mm) | y (mm) | Readback |
|---|---:|---:|---|
| 1 | 1.27 | -31.75 | Pass |
| 2 | -1.27 | -31.75 | Pass |
| 3 | 1.27 | -29.21 | Pass |
| 4 | -1.27 | -29.21 | Pass |
| 5 | 1.27 | -26.67 | Pass |
| 6 | -1.27 | -26.67 | Pass |
| 7 | 1.27 | -24.13 | Pass |
| 8 | -1.27 | -24.13 | Pass |
| 9 | 1.27 | -21.59 | Pass |
| 10 | -1.27 | -21.59 | Pass |
| 11 | 1.27 | -19.05 | Pass |
| 12 | -1.27 | -19.05 | Pass |
| 13 | 1.27 | -16.51 | Pass |
| 14 | -1.27 | -16.51 | Pass |
| 15 | 1.27 | -13.97 | Pass |
| 16 | -1.27 | -13.97 | Pass |
| 17 | 1.27 | -11.43 | Pass |
| 18 | -1.27 | -11.43 | Pass |
| 19 | 1.27 | -8.89 | Pass |
| 20 | -1.27 | -8.89 | Pass |
| 21 | 1.27 | -6.35 | Pass |
| 22 | -1.27 | -6.35 | Pass |
| 23 | 1.27 | -3.81 | Pass |
| 24 | -1.27 | -3.81 | Pass |
| 25 | 1.27 | -1.27 | Pass |
| 26 | -1.27 | -1.27 | Pass |
| 27 | 1.27 | 1.27 | Pass |
| 28 | -1.27 | 1.27 | Pass |
| 29 | 1.27 | 3.81 | Pass |
| 30 | -1.27 | 3.81 | Pass |
| 31 | 1.27 | 6.35 | Pass |
| 32 | -1.27 | 6.35 | Pass |
| 33 | 1.27 | 8.89 | Pass |
| 34 | -1.27 | 8.89 | Pass |
| 35 | 1.27 | 11.43 | Pass |
| 36 | -1.27 | 11.43 | Pass |
| 37 | 1.27 | 13.97 | Pass |
| 38 | -1.27 | 13.97 | Pass |
| 39 | 1.27 | 16.51 | Pass |
| 40 | -1.27 | 16.51 | Pass |
| 41 | 1.27 | 19.05 | Pass |
| 42 | -1.27 | 19.05 | Pass |
| 43 | 1.27 | 21.59 | Pass |
| 44 | -1.27 | 21.59 | Pass |
| 45 | 1.27 | 24.13 | Pass |
| 46 | -1.27 | 24.13 | Pass |
| 47 | 1.27 | 26.67 | Pass |
| 48 | -1.27 | 26.67 | Pass |
| 49 | 1.27 | 29.21 | Pass |
| 50 | -1.27 | 29.21 | Pass |
| 51 | 1.27 | 31.75 | Pass |
| 52 | -1.27 | 31.75 | Pass |

Scratch placement and top SVG render inspected. Pad 1 rectangular, remaining pads round; 1.8 mm lands are a design choice (0.39 mm annular ring), not a manufacturer-specified land diameter. Courtyard includes nominal body plus 0.5 mm. No 3D model supplied. Reference/silkscreen placement must be reviewed on final board.

The project pin-map schematic is an electrical diagram, not a physical mating view. Confirm stack connector side, rotation and origin against the mating boards before routing. J6/J7 must align to opposite Pico rows with the intended physical pin mapping.
