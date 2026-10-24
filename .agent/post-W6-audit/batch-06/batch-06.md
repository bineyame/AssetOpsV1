# Post-W6 audit batch 06: W2 cold Foundation/assessment (human ledger)

Every disposition is a **PROPOSAL** for the Architect. No register rows were added. Machine record: `batch-06.json`, `differences.json`; side-by-side: `index.html`.

## Frozen run

- **main_sha**: d44bb445 (product code identical to frozen fddf5cad)
- **branch**: audit/batch-06
- **worktree**: AssetOpsV1-review5
- **capture_revision**: d44bb445
- **api**: http://127.0.0.1:18601 (host/lab_app.py, DATABASE_URL=assetops_audit_b06_test)
- **frontend**: http://localhost:5186 Vite dev (ASSETOPS_API_PORT=18601); mock /mockups/v69/index.html#/<id>
- **cdp**: 9526
- **viewports**: ['1440x1000 full-page', '390x900 mobile emulation full-page']
- **db**: assetops_audit_b06_test (created, reseeded in place per phase by the producer, dropped; confirmed absent)
- **window**: 2026-10-06T19:00Z..20:05Z (selected); 2026-10-05 same hours (no-selection); inverted (refused)
- **capture_tool**: tools/capture-b6.mjs (batch-04 capture-b4.mjs with CDP 9526; capture-only)
- **producer**: `.agent/W2-F-evidence/seed.py` (the reviewed W2-F unit-5 capture seed), run unmodified with `ASSETOPS_TEST_DATABASE_URL=.../assetops_audit_b06_test`, `ASSETOPS_TEST_TEMPLATE=0`; phases excursion, normal, backup-failed. Logs in `logs/`.
- **pids**: API 19464 and Vite 30424 (spawned here) stopped by PID; capture Chrome killed by its own wrapper. No other process or DB touched (batch 5's s602b `_audit` DBs left alone).

## Route reconciliation

- cold-foundation / cold-readiness / cold-sld: `SITE_FOUNDATION_ROUTE_PATH`, `SITE_FOUNDATION_VIEW_ROUTE_PATH` (readiness, sld) mounted.
- temperature / coldbackup: `SITE_PERFORMANCE_SUBTAB_ROUTE_PATH` (`/performance/:capabilityId`) mounted.
- cold-finding: `SITE_FINDING_ROUTE_PATH` mounted. The spec row says 'selected backup Finding'; the producer's backup Finding is the start-failure Finding (...176 / ...17c).
- Spec error: `cold-finding-excursion` is mounted and produced by W2-03 (B6-23).

## Blockers

- None.

## Pairs (46, 12 representative)

| Screen | Case | Width | Rep | Order match | Max ratio | >1.3 panels | Dark band 390 | Console | Differences | App | Mock |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cold-foundation | stocked | 1440 | yes | True | 1.26 |  |  |  | B1-01, B1-04, B6-01, B6-02, B6-03, B6-04 | [app](excursion/cold-foundation-stocked-1440-app.png) | [mock](excursion/cold-foundation-stocked-1440-mock.png) |
| cold-foundation | stocked | 390 | yes | True | 1.72 | Operating interpretation | 92 |  | B1-01, B1-04, B1-03, B6-01, B6-02, B6-03, B6-04 | [app](excursion/cold-foundation-stocked-390-app.png) | [mock](excursion/cold-foundation-stocked-390-mock.png) |
| cold-foundation | no-version | 1440 |  | True | 0.28 |  |  |  | B1-01, B1-04, B6-01, B6-03, B6-04, B6-24 | [app](excursion/cold-foundation-no-version-1440-app.png) | [mock](excursion/cold-foundation-no-version-1440-mock.png) |
| cold-foundation | no-version | 390 |  | True | 0.49 |  | 143 |  | B1-01, B1-04, B1-03, B6-01, B6-03, B6-04, B6-24, B1-02 | [app](excursion/cold-foundation-no-version-390-app.png) | [mock](excursion/cold-foundation-no-version-390-mock.png) |
| cold-readiness | stocked | 1440 | yes | False | 2.15 | Readiness and commissioning evidence |  |  | B1-01, B1-04, B6-01, B6-03, B6-04, B6-05, B6-06, B6-07 | [app](excursion/cold-readiness-stocked-1440-app.png) | [mock](excursion/cold-readiness-stocked-1440-mock.png) |
| cold-readiness | stocked | 390 | yes | False | 1.59 | Readiness and commissioning evidence | 92 |  | B1-01, B1-04, B1-03, B6-01, B6-03, B6-04, B6-05, B6-06, B6-07 | [app](excursion/cold-readiness-stocked-390-app.png) | [mock](excursion/cold-readiness-stocked-390-mock.png) |
| cold-readiness | no-version | 1440 |  | False | 0.4 |  |  |  | B1-01, B1-04, B6-01, B6-03, B6-04, B6-07, B6-24 | [app](excursion/cold-readiness-no-version-1440-app.png) | [mock](excursion/cold-readiness-no-version-1440-mock.png) |
| cold-readiness | no-version | 390 |  | False | 0.31 |  | 92 |  | B1-01, B1-04, B1-03, B6-01, B6-03, B6-04, B6-07, B6-24 | [app](excursion/cold-readiness-no-version-390-app.png) | [mock](excursion/cold-readiness-no-version-390-mock.png) |
| cold-sld | stocked | 1440 | yes | False | 1.55 | What each part does |  |  | B1-01, B1-04, B6-01, B6-03, B6-04, B6-07, B6-08, B6-09 | [app](excursion/cold-sld-stocked-1440-app.png) | [mock](excursion/cold-sld-stocked-1440-mock.png) |
| cold-sld | stocked | 390 | yes | False | 1.43 | Cold replay lab | 92 |  | B1-01, B1-04, B1-03, B6-01, B6-03, B6-04, B6-07, B6-08, B6-09 | [app](excursion/cold-sld-stocked-390-app.png) | [mock](excursion/cold-sld-stocked-390-mock.png) |
| cold-sld | no-version | 1440 |  | False | 0.29 |  |  |  | B1-01, B1-04, B6-01, B6-03, B6-04, B6-07, B6-24 | [app](excursion/cold-sld-no-version-1440-app.png) | [mock](excursion/cold-sld-no-version-1440-mock.png) |
| cold-sld | no-version | 390 |  | False | 0.31 |  | 141 |  | B1-01, B1-04, B1-03, B6-01, B6-03, B6-04, B6-07, B6-24, B1-02 | [app](excursion/cold-sld-no-version-390-app.png) | [mock](excursion/cold-sld-no-version-390-mock.png) |
| temperature | excursion | 1440 | yes | True | 1.18 |  |  |  | B1-01, B1-04, B6-03, B6-04, B6-10, B6-11, B6-12 | [app](excursion/temperature-excursion-1440-app.png) | [mock](excursion/temperature-excursion-1440-mock.png) |
| temperature | excursion | 390 | yes | True | 1.29 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-10, B6-11, B6-12 | [app](excursion/temperature-excursion-390-app.png) | [mock](excursion/temperature-excursion-390-mock.png) |
| temperature | no-selection | 1440 |  | True | 1.18 |  |  |  | B1-01, B1-04, B6-03, B6-04, B6-10, B6-11, B6-14 | [app](excursion/temperature-no-selection-1440-app.png) | [mock](excursion/temperature-no-selection-1440-mock.png) |
| temperature | no-selection | 390 |  | True | 1.01 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-10, B6-11, B6-14 | [app](excursion/temperature-no-selection-390-app.png) | [mock](excursion/temperature-no-selection-390-mock.png) |
| temperature | refused | 1440 |  | True | 0.8 |  |  |  | B1-01, B1-04, B6-03, B6-04, B6-10, B6-11, B6-13 | [app](excursion/temperature-refused-1440-app.png) | [mock](excursion/temperature-refused-1440-mock.png) |
| temperature | refused | 390 |  | True | 0.59 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-10, B6-11, B6-13 | [app](excursion/temperature-refused-390-app.png) | [mock](excursion/temperature-refused-390-mock.png) |
| coldbackup | excursion | 1440 | yes | True | 1.67 | Evidence by causal step |  |  | B1-01, B1-04, B6-03, B6-04, B6-11, B6-15, B6-16 | [app](excursion/coldbackup-excursion-1440-app.png) | [mock](excursion/coldbackup-excursion-1440-mock.png) |
| coldbackup | excursion | 390 | yes | True | 1.62 | Evidence by causal step | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-11, B6-15, B6-16 | [app](excursion/coldbackup-excursion-390-app.png) | [mock](excursion/coldbackup-excursion-390-mock.png) |
| coldbackup | no-selection | 1440 |  | True | 0.97 |  |  |  | B1-01, B1-04, B6-03, B6-04, B6-11, B6-15 | [app](excursion/coldbackup-no-selection-1440-app.png) | [mock](excursion/coldbackup-no-selection-1440-mock.png) |
| coldbackup | no-selection | 390 |  | True | 0.95 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-11, B6-15 | [app](excursion/coldbackup-no-selection-390-app.png) | [mock](excursion/coldbackup-no-selection-390-mock.png) |
| coldbackup | refused | 1440 |  | True | 0.63 |  |  |  | B1-01, B1-04, B6-03, B6-04, B6-11, B6-13, B6-15 | [app](excursion/coldbackup-refused-1440-app.png) | [mock](excursion/coldbackup-refused-1440-mock.png) |
| coldbackup | refused | 390 |  | True | 0.45 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-11, B6-13, B6-15 | [app](excursion/coldbackup-refused-390-app.png) | [mock](excursion/coldbackup-refused-390-mock.png) |
| cold-finding | start-excursion | 1440 | yes | True | 1.04 |  |  |  | B1-01, B1-04, B6-03, B6-18, B6-19, B6-20, B6-21 | [app](excursion/cold-finding-start-excursion-1440-app.png) | [mock](excursion/cold-finding-start-excursion-1440-mock.png) |
| cold-finding | start-excursion | 390 | yes | True | 1.12 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-18, B6-19, B6-20, B6-21 | [app](excursion/cold-finding-start-excursion-390-app.png) | [mock](excursion/cold-finding-start-excursion-390-mock.png) |
| cold-finding | unknown-id | 1440 |  | True | 0.46 |  |  |  | B1-01, B1-04, B6-03, B6-18, B6-19, B6-20, B6-22 | [app](excursion/cold-finding-unknown-id-1440-app.png) | [mock](excursion/cold-finding-unknown-id-1440-mock.png) |
| cold-finding | unknown-id | 390 |  | True | 0.5 |  | 102 |  | B1-01, B1-04, B1-03, B6-03, B6-18, B6-19, B6-20, B6-22 | [app](excursion/cold-finding-unknown-id-390-app.png) | [mock](excursion/cold-finding-unknown-id-390-mock.png) |
| cold-finding | excursion-finding | 1440 |  | True | 1.19 |  |  |  | B1-01, B1-04, B6-03, B6-18, B6-19, B6-20, B6-21, B6-23 | [app](excursion/cold-finding-excursion-finding-1440-app.png) | [mock](excursion/cold-finding-excursion-finding-1440-mock.png) |
| cold-finding | excursion-finding | 390 |  | True | 1.36 | Bounded conclusion | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-18, B6-19, B6-20, B6-21, B6-23 | [app](excursion/cold-finding-excursion-finding-390-app.png) | [mock](excursion/cold-finding-excursion-finding-390-mock.png) |
| temperature | normal | 1440 |  | True | 1.18 |  |  |  | B1-01, B1-04, B6-03, B6-04, B6-10, B6-11, B6-12 | [app](normal/temperature-normal-1440-app.png) | [mock](normal/temperature-normal-1440-mock.png) |
| temperature | normal | 390 |  | True | 1.15 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-10, B6-11, B6-12 | [app](normal/temperature-normal-390-app.png) | [mock](normal/temperature-normal-390-mock.png) |
| coldbackup | normal | 1440 |  | True | 1.75 | Evidence by causal step |  |  | B1-01, B1-04, B6-03, B6-04, B6-11, B6-15, B6-16, B6-17 | [app](normal/coldbackup-normal-1440-app.png) | [mock](normal/coldbackup-normal-1440-mock.png) |
| coldbackup | normal | 390 |  | True | 1.74 | Evidence by causal step | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-11, B6-15, B6-16, B6-17 | [app](normal/coldbackup-normal-390-app.png) | [mock](normal/coldbackup-normal-390-mock.png) |
| cold-foundation | normal-replay | 1440 |  | True | 1.26 |  |  |  | B1-01, B1-04, B6-01, B6-02, B6-03, B6-04 | [app](normal/cold-foundation-normal-replay-1440-app.png) | [mock](normal/cold-foundation-normal-replay-1440-mock.png) |
| cold-foundation | normal-replay | 390 |  | True | 1.72 | Operating interpretation | 92 |  | B1-01, B1-04, B1-03, B6-01, B6-02, B6-03, B6-04 | [app](normal/cold-foundation-normal-replay-390-app.png) | [mock](normal/cold-foundation-normal-replay-390-mock.png) |
| temperature | backup-failed | 1440 |  | True | 1.18 |  |  |  | B1-01, B1-04, B6-03, B6-04, B6-10, B6-11, B6-12 | [app](backup-failed/temperature-backup-failed-1440-app.png) | [mock](backup-failed/temperature-backup-failed-1440-mock.png) |
| temperature | backup-failed | 390 |  | True | 1.29 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-10, B6-11, B6-12 | [app](backup-failed/temperature-backup-failed-390-app.png) | [mock](backup-failed/temperature-backup-failed-390-mock.png) |
| coldbackup | backup-failed | 1440 |  | True | 1.67 | Evidence by causal step |  |  | B1-01, B1-04, B6-03, B6-04, B6-11, B6-15, B6-16 | [app](backup-failed/coldbackup-backup-failed-1440-app.png) | [mock](backup-failed/coldbackup-backup-failed-1440-mock.png) |
| coldbackup | backup-failed | 390 |  | True | 1.62 | Evidence by causal step | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-11, B6-15, B6-16 | [app](backup-failed/coldbackup-backup-failed-390-app.png) | [mock](backup-failed/coldbackup-backup-failed-390-mock.png) |
| coldbackup | default-window | 1440 |  | True | 1.67 | Evidence by causal step |  |  | B1-01, B1-04, B6-03, B6-04, B6-11, B6-15, B6-16 | [app](backup-failed/coldbackup-default-window-1440-app.png) | [mock](backup-failed/coldbackup-default-window-1440-mock.png) |
| coldbackup | default-window | 390 |  | True | 1.62 | Evidence by causal step | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-04, B6-11, B6-15, B6-16 | [app](backup-failed/coldbackup-default-window-390-app.png) | [mock](backup-failed/coldbackup-default-window-390-mock.png) |
| cold-finding | start-backup-failed | 1440 |  | True | 1.04 |  |  |  | B1-01, B1-04, B6-03, B6-18, B6-19, B6-20, B6-21 | [app](backup-failed/cold-finding-start-backup-failed-1440-app.png) | [mock](backup-failed/cold-finding-start-backup-failed-1440-mock.png) |
| cold-finding | start-backup-failed | 390 |  | True | 1.12 |  | 92 |  | B1-01, B1-04, B1-03, B6-03, B6-18, B6-19, B6-20, B6-21 | [app](backup-failed/cold-finding-start-backup-failed-390-app.png) | [mock](backup-failed/cold-finding-start-backup-failed-390-mock.png) |
| cold-finding | start-refused-window | 1440 |  | True | 0.46 |  |  |  | B1-01, B1-04, B6-03, B6-18, B6-19, B6-20, B6-22 | [app](backup-failed/cold-finding-start-refused-window-1440-app.png) | [mock](backup-failed/cold-finding-start-refused-window-1440-mock.png) |
| cold-finding | start-refused-window | 390 |  | True | 0.5 |  | 93 |  | B1-01, B1-04, B1-03, B6-03, B6-18, B6-19, B6-20, B6-22 | [app](backup-failed/cold-finding-start-refused-window-390-app.png) | [mock](backup-failed/cold-finding-start-refused-window-390-mock.png) |

Panel titles and order match the mock on all pairs. App page horizontal overflow is 0 and clipped text is 0 on all pairs; no console errors. Inner scrollers at 390: Site tab row (also in the mock on Foundation/Performance), readiness table, backup tables (readable, as the mock).

## Differences and proposed dispositions

### B6-01 (cold-foundation, cold-readiness, cold-sld)

- Observed: Status strip carries extra W1 state-line items: 'Configuration only'/'Set up to report'/'Configured site' chip, 'Effective ... UTC to no end date', 'This is the configuration in effect now', version select 'In effect now', a cross-link and 'How this was worked out'; mock has 'Configuration v1 · Effective 6 Oct 2026' (readiness: 'Needs review · Configuration readiness is distinct...'). Panels close with a note line and a disclosure.
- Evidence: excursion/cold-foundation-stocked-1440-{app,mock}.png
- Proposed: Cite B1-05 (candidate D2 W1 state-line pattern); UTC part B2-21/B3-04.

### B6-02 (cold-foundation)

- Observed: Physical site 8 rows vs 6 (Site ID, Cold rooms, Power supply, Cooling equipment, Chamber temperature probe, Other sensors, Declared connections, Night outage rule) vs mock (Site ID, Primary operation, Power sources, Night outage rule, Cooling asset, Policy). Operating interpretation 6 rows vs 4, with green 'Configured' chips where the mock has plain text (Missing / Incomplete / Mapped / Mapped); adds Temperature policy and Effective period. Ratio 1.26 at 1440; 1.25 / 1.72 at 390.
- Evidence: excursion/cold-foundation-stocked-{1440,390}-{app,mock}.png
- Proposed: (b) candidate D4 (rows from the selected Foundation version replace illustrative rows) with B1-05 notes; the 390 1.72x Operating interpretation needs a measured-cap ruling (extra rows + note + disclosure).

### B6-03 (cold-foundation, cold-readiness, cold-sld, temperature, coldbackup, cold-finding)

- Observed: h1/badge/subtitle are record-derived: 'Cold replay lab', 'Demonstration data · COLD-LAB-001' (purple, so B1-14 green tone does not recur), subtitles 'Cold room · stored configuration for the period shown', 'Cold room · single line diagram', 'Cold replay lab · cold-chain finding' vs mock 'Produce cold room · 2–4°C policy · hybrid...'. Temperature/backup subtitles match the mock.
- Evidence: excursion/*-1440-{app,mock}.png
- Proposed: (b) candidate D4 (record-derived identity replaces illustrative copy; cf. B4-06).

### B6-04 (cold-foundation, cold-readiness, cold-sld, temperature, coldbackup)

- Observed: Closing note: Foundation, Readiness and SLD render it as an unboxed 14 px paragraph; mock has a bordered 11 px info callout with an icon. Temperature (amber) and Backup (blue) callouts are boxed but have no info icon.
- Evidence: excursion/cold-readiness-stocked-1440-{app,mock}.png
- Proposed: Cite B1-06 / B1-07 (shared callout/typography D3 candidate).

### B6-05 (cold-readiness)

- Observed: Readiness table 9 rows vs 4; Declared cells are a chip plus caption; every row is 'Unconfirmed' with the identical 'Commissioning record' (W2 M2 stays closed: no blank 'What is needed'); 8 of 9 Next step links are 'Single line diagram →'; note line + disclosure. Ratio 2.15 at 1440, 1.59 at 390 (inner table scroll 536/318, readable).
- Evidence: excursion/cold-readiness-stocked-{1440,390}-{app,mock}.png
- Proposed: Rows: (b) candidate D4 (areas of the selected version). The >1.3x needs a reviewed ruling (measured reason: 9 configured areas, chip+caption cells, note, disclosure). Cite B1-31 pattern.

### B6-06 (cold-readiness)

- Observed: Gateway panel: title 'Gateway status · edge-cold-lab-001' (raw gateway id); tiles 'No contact received yet' / 'Not available' / 'Not available' / 'Unknown'; contact bar is a hatched 'No history to draw' placeholder with a 4-item legend; Connected sources lists 11 reading chips with no reporting state (mock 6 device chips with Reporting / Never reported); Effect panel has two generic items; header link 'Evidence › Data sources →' (mock 'Health › Data sources →').
- Evidence: excursion/cold-readiness-stocked-1440-{app,mock}.png
- Proposed: Title: cite B1-30 (approved dynamic) and B1-53 for the raw id. Tiles/bar/chips: cite B1-32, candidate D1 (no gateway diagnostic history on the selected read). Link target: (a) R22 (Foundation Data sources points to cold-evidence) verified.

### B6-07 (cold-readiness, cold-sld)

- Observed: Breadcrumb adds the sub-tab leaf ('... / Foundation / Readiness', '... / Single line diagram'); the mock trail ends at Foundation.
- Evidence: excursion/cold-sld-stocked-1440-{app,mock}.png
- Proposed: (b) candidate D2 (minor), same as the W1 Foundation pages; Architect to rule once for W1+W2.

### B6-08 (cold-sld)

- Observed: Diagram is the replay site's 8 configured parts: no solar/battery/DC bus, no circuit breakers, feeders or kWh meter; every reporting dot is 'not assessed'; Monitoring row shows 11 reading names instead of 6 devices; title 'Cold replay lab' with no topology suffix and 'Topology type not stated in this version'; legend Power/Cooling/Sensing; 'Undeclared in this version: solar array, battery'.
- Evidence: excursion/cold-sld-stocked-1440-{app,mock}.png
- Proposed: Cite B1-40 / B1-41; candidate D4 (configured topology replaces illustrative hybrid) plus D1 (reporting status not assessed).

### B6-09 (cold-sld)

- Observed: 'What each part does' has 8 per-part rows whose Role is a type word (Cold room, Sensor, Cooling, Switch...) vs mock 5 grouped rows with descriptive roles; footnote 'Function description not recorded' + disclosure. Ratio 1.55 at 1440.
- Evidence: excursion/cold-sld-stocked-1440-{app,mock}.png
- Proposed: Cite B1-42; candidate D1 (no function description on the record). >1.3x measured reason: 8 configured parts.

### B6-10 (temperature)

- Observed: Strip: 'Outside policy' vs 'Needs attention'; the mock's 'Inspect temperature claim ↗' link is absent; the app adds '6 Oct 2026 19:00–20:05 UTC · Up to date for this window' and omits 'in policy 42–58% of the hour'.
- Evidence: excursion/temperature-excursion-1440-{app,mock}.png
- Proposed: Chip wording: candidate D2. Missing claim link: (c) D3 candidate (cold-evidence is built, so the link is renderable). UTC: B2-21/B3-04.

### B6-11 (temperature, coldbackup)

- Observed: KPI typography: values render as one string at one size ('At least 45 min', '4.8 °C', '19–23 °C·min'), while the mock sets a large number with a small unit. Text values ('Not determined', 'Start failed', 'Not recorded', 'Not assessed') render at about 17 px against mock 'Unknown' / 'Failed' at about 27 px. 'Not determined' vs mock 'Unknown'.
- Evidence: excursion/temperature-excursion-1440-{app,mock}.png; excursion/coldbackup-excursion-1440-{app,mock}.png
- Proposed: (c) D3 candidate (minor shared KPI typography). Wording: candidate D2.

### B6-12 (temperature)

- Observed: Chart legend 'Policy band' vs 'Upper policy limit'; axis labels carry 'UTC'; timeline 4 events vs 3; Excursion context adds a disclosure, the Power outage row has no 'Observed' chip, and 'Open the Finding →' stands where the mock has 'Open Incident INC-203 →'. Claim boundary adds a disclosure; its sentence is 14 px.
- Evidence: excursion/temperature-excursion-1440-{app,mock}.png
- Proposed: Legend/timeline: candidate D4. Incident link: candidate D1 (this producer links no Incident). Disclosures: B1-05. 14 px: B1-07. UTC: B2-21/B3-04.

### B6-13 (temperature, coldbackup)

- Observed: Refused window (from > to): strip and KPI tile row are dropped; a 'Window cannot be read' banner plus one italic gap line per panel remain. The mock always keeps strip + 4 tiles. W2-F applied the M3 'keep strip and Not assessed tiles' treatment only to Overview/Evidence/Financials. The amber 'Durations are bounded...' callout still shows. The refusal copy 'not a valid UTC window of at most 31 days' is the same for an inverted window as for an over-long one.
- Evidence: excursion/temperature-refused-1440-app.png; excursion/coldbackup-refused-1440-app.png
- Proposed: (c) D3 candidate: extend the W2-F M3 refused treatment (strip + 'Not assessed' tiles) to Temperature and Backup, or an Architect ruling that keeps the banner-only form. Generic copy: analogue of the domainActionClient window-error item.

### B6-14 (temperature)

- Observed: No-selection window (5 Oct): strip says 'Policy not recorded' and Excursion context 'Upper policy limit: Not recorded', while the Foundation version in effect declares 'Temperature policy 2–4 °C'. Chart panel stays full height (379 px) with one gap line.
- Evidence: excursion/temperature-no-selection-1440-app.png; excursion/cold-foundation-stocked-1440-app.png
- Proposed: Architect check: the policy is read from the selected assessment, so 'not recorded' may be literal; otherwise (c) D3 candidate copy ('not read for this window').

### B6-15 (coldbackup)

- Observed: Strip: 'Start failed' / 'Started' + 'Evidence: Observed' vs mock 'Degraded' + 'Confidence: High'; no confidence chip; the mock's 'Open INC-203 →' is absent.
- Evidence: excursion/coldbackup-excursion-1440-{app,mock}.png; normal/coldbackup-normal-1440-app.png
- Proposed: Chip wording: candidate D2. Confidence absent: (c) D3 candidate (W2-F M9/M13 added confidence to the Overview and Finding strips; Backup still lacks it) unless the Architect rules 'Evidence: Observed' the equivalent. Incident link: candidate D1.

### B6-16 (coldbackup)

- Observed: Backup event chains columns 'Power to compressor' / 'Compressor response' vs mock 'Power to load' / 'Load response'; Result chip 'Start failed' vs 'Fail'. Evidence by causal step 9 rows vs 5, each with a 'record' link, plus a 'Records not used' line and a disclosure: 1.67 at 1440, 1.62 at 390 (inner scrollers 810/318 and 447/318, as the mock 689/320, 447/320).
- Evidence: excursion/coldbackup-excursion-{1440,390}-{app,mock}.png
- Proposed: Columns: (a) R20 D2 built, verified, but R20's screen list names temperature and cold-finding, not coldbackup: register correction. Rows: candidate D4; >1.3x measured reason: nine selected causal steps + links + disclosure.

### B6-17 (coldbackup)

- Observed: Normal (successful start) case keeps failure copy: 'Which part failed, if any, is not determined here.' and the Start result row Limit 'A failed start needs inspection' beside 'Succeeded at 19:07'.
- Evidence: normal/coldbackup-normal-1440-app.png
- Proposed: (c) D3 candidate (minor copy: state-specific limit text).

### B6-18 (cold-finding)

- Observed: Finding chrome: rail selects Sites (mock Findings); breadcrumb is Site-rooted 'Sites / Cold replay lab / Findings / Finding' with a generic leaf and no code (mock 'Findings › F-118 › Overview · site: ...'); an extra Site tab row sits above the Finding sub-tabs (at 390 it scrolls 521/358 with a cut-off 'W'); the mock 'Open site' button is absent.
- Evidence: excursion/cold-finding-start-excursion-{1440,390}-{app,mock}.png
- Proposed: Cite B4-01 (rail), B4-03 (breadcrumb origin, Finding variant), B4-04 (extra Site tab row), B4-05 (Open site); code: (a) R65 D1 planned, verified.

### B6-19 (cold-finding)

- Observed: Sub-tab 'Recommendation · Not available yet' (mock live); Recommended next step is an italic gap 'No recorded next step. No Action or Recommendation record is linked to this Finding.' + 'Open the Backup view →' where the mock has a sentence and a 'Review recommendation' button (0.52x).
- Evidence: excursion/cold-finding-start-excursion-1440-{app,mock}.png
- Proposed: Register R40 lists cold-finding Recommendation as D5 'built' (destination built in W5), but cold Recommendation is still unbuilt (spec lists cold-recommendation as unimplemented): Architect to correct R40 for cold-finding to D1, or name the resolving unit.

### B6-20 (cold-finding)

- Observed: Strip 'Open · Cold replay lab · Confidence: Observed · 6 Oct 2026 19:00–20:05 UTC · Up to date ... · Selected source: Generated test data' (W2 M13 stays closed: confidence present); no Finding code chip. Refused / unknown states read 'Unknown  Confidence: Unknown Cold replay lab' with no separator before the site name.
- Evidence: excursion/cold-finding-unknown-id-390-app.png; backup-failed/cold-finding-start-refused-window-1440-app.png
- Proposed: Code: R65 D1. Missing separator: (c) D3 candidate (minor copy defect). UTC: B2-21/B3-04.

### B6-21 (cold-finding)

- Observed: Bounded conclusion lead 'A commanded automatic generator start failed.' (mock adds recovery and peak), adds the bullet 'Not observed: transfer to backup.' and 'Inspect the backup chain →' (mock 'Inspect claim evidence ↗'). Operational context adds an 'Accepted record' link per step, a 'Missing steps' line and a disclosure. The secondary sentence is 14 px.
- Evidence: excursion/cold-finding-start-excursion-1440-{app,mock}.png
- Proposed: Candidate D4 (selected chain, recovery not recorded) + B1-05 disclosure; 14 px: B1-07.

### B6-22 (cold-finding)

- Observed: Unknown ID and refused window: generic h1 'Finding', 'Not found' / 'Window cannot be read' banner, three panels with one gap line each, 'No recorded next step.' No mock state.
- Evidence: excursion/cold-finding-unknown-id-1440-app.png; backup-failed/cold-finding-start-refused-window-1440-app.png
- Proposed: Architect to confirm the shared error-state pattern (cf. B4-24); honest refusal, no Rxx.

### B6-23 (cold-finding)

- Observed: Inventory: 'cold-finding-excursion' is mounted on the same Finding route and produced by the W2-03 replay (Finding ...170), yet the spec lists it among IDs with no W1-W6 implementation. Captured here as an extra cold-finding state against mock #/cold-finding-excursion: panel titles and order match (Bounded conclusion, Temperature, Recommended next step).
- Evidence: excursion/cold-finding-excursion-finding-1440-{app,mock}.png
- Proposed: Spec route-table correction: move cold-finding-excursion into the audit target (88 implemented + 22), then give it its own representative pairs.

### B6-24 (cold-foundation, cold-readiness, cold-sld)

- Observed: No-version (?at=2026-09-01): h1 keeps the display name (B1-25 does not recur on cold); every panel is a single gap sentence (0.14-0.49x); at 390 the dark header band is 141-143 px.
- Evidence: excursion/cold-foundation-no-version-390-app.png
- Proposed: Gap state: candidate D1 (honest missing state). Header: cite B1-02.

## Cross-cutting findings cited (not re-described)

- B1-01: all pairs
- B1-03: all 390 pairs
- B1-04/B2-36: all pairs
- B1-02/B2-04: cold-foundation no-version 390 (143 px), cold-sld no-version 390 (141 px); all other 390 pairs 92-102 px
- B1-07/B2-03: temperature Claim boundary (14 px), coldbackup 'What the chain shows' second sentence, cold-finding conclusion sentence, Foundation/Readiness/SLD closing lines
- B1-53: cold-readiness gateway id 'edge-cold-lab-001' in the panel title
- B2-02: not present (no Window control on any batch-06 screen; window only via URL, see B1-01)
- B3-01: not present
- B2-21/B3-04: Foundation effective dates, temperature/backup strips and chart axis, cold-finding strip
- B4-03 / B4-04 / B4-01 / B4-05: cold-finding only (B6-18). On Foundation and Performance the mock has the same Site tab row and it also scrolls at 390 (511/360), so B4-04 does not apply there
- B4-19: not observed: event/step labels are mapped plain language, no raw kind fall-through and no duplicate-key console error

## Earlier W2 findings at this SHA

- M2 cold-readiness blank 'What is needed': stays CLOSED: every Unconfirmed row reads 'Commissioning record'
- M4 temperature panel 3 title: stays CLOSED: 'Claim boundary' in excursion, no-selection, refused, normal and backup-failed
- M13 cold-finding strip confidence: stays CLOSED: 'Confidence: Observed' (start) / 'Confidence: Bounded' (excursion) / 'Confidence: Unknown' (refused)
- H1 counter-evidence on coldbackup: consistent: 'Cooling resumed: Not recorded · Compressor off at 19:05; no running record'
- M6 exposure size on temperature: stays CLOSED: '19–23 °C·min · Observed excursion estimate'
- W2 residual peak 4.9 vs 4.8: CLOSED at this SHA: peak 4.8 °C on temperature, coldbackup and the excursion Finding
- R37 Loading / batch row (cold-performance): verified present in Excursion context, mock order

## Register checks

- R20: D2 built; Power-to-compressor / Compressor-response headings verified on coldbackup, but the row names temperature and cold-finding only (B6-16). Its 'Claim boundary' part is now the mock title (W2-F M4).
- R22: D3 (cold-health); not on these screens, but the readiness 'Evidence › Data sources' link follows it (B6-06).
- R23: cold-work-incidents; not on batch-06 screens
- R24: ev-work-incidents; not on batch-06 screens
- R37: built (W5-F1 42964500); Loading / batch row verified on temperature
- R38: cold-evidence-analysis; not on batch-06 screens
- R60: ev-health; not on batch-06 screens
- R40: D5 'built': Cooling destination now live on temperature/backup (verified); cold-finding Recommendation still 'Not available yet' (B6-19), so the cold-finding part is not expired
- R65: D1 planned; no public cold Finding code (verified on cold-finding)

## Mandatory UI-pass checks

- prose_14_vs_12: Observed (B1-07): .prose 14 px vs mock 12 px on temperature, coldbackup, cold-finding; panel text 10-12 px.
- tall_dark_header_390: Observed only on no-version Foundation/SLD (141-143 px); refused cold Temperature/Backup/Finding pages stay 92-93 px because their panels keep the page height.
- plural_1_incidents: Not applicable (no count+noun case copy). 'One outage in the selected window' reads correctly.
- raw_EV_CONNECTOR_label: Not applicable (cold Site).
- domainActionClient_generic_window_error: Not applicable to the client (no Action inputs). Analogue observed: the read refusal copy is identical for inverted and over-long windows (B6-13).
- R88_R112_window_control: Not applicable: no page-local Window control on these screens; R88/R112 not involved.

## Panels over 1.3x (measured reasons; each needs a reviewed ruling)

- cold-foundation Operating interpretation 1.72x at 390 (B6-02): 6 rows vs 4, chips, note and disclosure.
- cold-readiness table 2.15x / 1.59x (B6-05): 9 configured areas vs 4, chip+caption cells, note, disclosure.
- cold-sld parts table 1.55x at 1440 (B6-09); diagram 1.43x at 390 (measured; no inner scroller, page overflow 0).
- coldbackup Evidence by causal step 1.67x / 1.62x (B6-16): 9 selected steps vs 5, record links, disclosure.
- cold-finding excursion Bounded conclusion 1.36x at 390: longer selected sentence plus bullet and link.
