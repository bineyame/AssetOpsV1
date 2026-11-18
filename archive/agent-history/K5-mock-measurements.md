# K5 mock measurements (v69 `fuel`, tools/measure-mock-panels.mjs, main 97505484a)

Command: `node tools/measure-mock-panels.mjs .agent/K5-mock-measurements fuel` (headless Chrome, 2026-11-08).
Raw output: `.agent/K5-mock-measurements/mock-measure.json` and `mock-fuel-1440.png`, `mock-fuel-390.png`.
Heights/widths in px; budget rule per W3-02 closure: max = mock + max(24px, 10%).

## fuel @ 1440 (page 1477px, scrollW 1425/1425)

| kind | title | top | h | w | budget |
|---|---|---:|---:|---:|---:|
| statusbar | Fuel balance: evidence limited ... | 354 | 44 | 1161 | 68 |
| cards | Opening evidence / Recorded deliveries / Expected use / Residual | 416 | 129 | 1161 | 153 |
| panel | Fuel balance at a glance | 563 | 271 | 1161 | 298 |
| panel | Balance bridge | 852 | 332 | 1161 | 366 |
| notice | A fuel residual is unexplained inventory movement ... | 1202 | 42 | 1161 | 66 |
| panel | Inspect existing generator fuel interpretation | 1262 | 149 | 1161 | 173 |

## fuel @ 390 (page 2125px, scrollW 390/390)

| kind | title | top | h | w | budget |
|---|---|---:|---:|---:|---:|
| statusbar | Fuel balance: evidence limited ... | 523 | 71 | 360 | 95 |
| cards | Opening evidence / Recorded deliveries / Expected use / Residual | 612 | 264 | 360 | 291 |
| panel | Fuel balance at a glance | 894 | 287 | 360 | 316 |
| panel | Balance bridge | 1199 | 526 | 360 | 579 |
| notice | A fuel residual is unexplained inventory movement ... | 1742 | 78 | 360 | 102 |
| panel | Inspect existing generator fuel interpretation | 1839 | 192 | 360 | 216 |

## PRE-FLIGHT (d): do the existing mini classes meet these budgets?

Yes. The numbers are identical to `.agent/W4-02-mock-measurements.md` (fuel), from which the existing classes in
`frontend/src/sites/w4-mini-performance.css` were sized: `mini-max--fuel-cards` 153/291 px, `mini-max--fuel-bridge`
366/579 px, `mini-max--fuel-interpretation` 173/216 px. Night mode reuses them unchanged; no new CSS.

- The cards row and the bridge reuse `mini-max--fuel-cards` and `mini-max--fuel-bridge` (same four cards, same five
  bridge rows).
- "Deliveries and tank dips" (MD-FUEL-K5-1) has no mock panel. It reuses the bridge's table bound
  (`mini-max--fuel-bridge`, 366/579 px), and its rows sit behind `ShowAll` after 6 rows; the bounded table scrolls inside
  its own panel up to 10 rows (worst case today: 2 dips plus at most 1 delivery a night).
- "Finding for this night" (MD-FUEL-K5-2) takes the place of the interpretation panel and reuses
  `mini-max--fuel-interpretation` (173/216 px).

Captures of the built pages against these budgets are owed (review packet, "Layout evidence owed").
