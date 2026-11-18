# W2 structural audit: app versus v69 mock (2026-10-20)

Independent agent audit replacing the owner's W2 walkthrough as the gate before W5 (`.agent/owner-walkthrough-after-w6-2026-10-20.md`). It is read-only and checks structure only. Worktree `AssetOpsV1-plan2` on `main` at `04ebdcfc`.

## Method

- Panel titles, order and geometry: I compared app and mock panel boxes in every `evidence.json` pair (W2-01, W2-03-followup, W2-04, W2-05a, W2-06, W2-07), across all 104 app captures (52 at 1440 and 52 at 390). I also checked them against `frontend/docs/architecture/v69-rendered-panels.json`.
- I viewed the 1440 app and mock pictures for the main state of all 22 screens. I also looked at a sample of the no-version, missing-probe, empty and refused states, and at the 390 captures for the cold overview and sessions.
- Mock PNGs already existed beside every app capture, so I did not run `tools/measure-mock-panels.mjs`.
- Result of the geometry pass: **every screen has the mock's panel set in the mock's order**. The only title mismatches are:
  - temperature, where the third panel is named differently (finding M4);
  - gateway and diagram names that come from the site's data, which is by design.
- Big height differences come from the amount of data (fewer or more rows), or from empty and refused states that shrink to one line of gap copy. Neither counts as a prominence defect.

Capture paths are relative to `.agent/`.

## Findings

### H1 (High): cold-evidence says "Full" for cooling recovery when no recovery was recorded
- App: `W2-04-evidence/cold-evidence-stocked-1440-app.png`, in "What we can conclude now".
  - Cooling recovery is **Full**: "Selected records support this claim for the covered window", with "Nothing required for this claim".
- The same window elsewhere:
  - Backup (`W2-03-followup-evidence/coldbackup-stocked-1440-app.png`) shows "Cooling resumed: Not recorded · Compressor off at 19:05; no running record".
  - The cold overview (`W2-04-evidence/cold-stocked-1440-app.png`) shows "Recovery comparison not assessed".
- Product exposure is also **Full**, yet its "What is missing" reads "Nothing required for this claim · Stock identity and value are not declared".
- Mock evidence: `cold-evidence-stocked-1440-mock.png` rates Cooling recovery and Product exposure as Limited and None, and lists what is missing.
- Why it matters: the evidence page claims full support for a conclusion the rest of the site says was not observed.

### M2 (Medium): readiness "What is needed" is blank on every unconfirmed row (cold and EV)
- App: `W2-01-evidence/cold-readiness-stocked-1440-app.png` (9 rows) and `W2-05a-evidence/ev-readiness-stocked-1440-app.png` (rows 1-2).
  - Every row is "Unconfirmed", yet "What is needed" shows "—", which reads as nothing needed.
- The note in the panel says confirmation needs a commissioning record.
- Mock: `cold-readiness-stocked-1440-mock.png` fills this column ("Calibration record", "Map position to the gateway").

### M3 (Medium): refused-window states on W2-04 cold screens drop the status strip and the tiles, with no refusal banner
- App:
  - `W2-04-evidence/cold-refused-1440-app.png`
  - `W2-04-evidence/cold-financials-refused-1440-app.png`
  - `W2-04-evidence/cold-evidence-refused-1440-app.png`
- What happens: the selected-window line, the status strip and the 4-5 tile row disappear. Only the panels remain, each with one italic line of gap copy.
- Temperature handles the same refusal correctly: `W2-04-evidence/temperature-refused-1440-app.png` keeps a "Window cannot be read" banner.
- The cold-evidence refused footer also degrades to "Record-level detail and claim limits are on No linked page for this item.", although the Analysis subtab exists.
- Mock: the strip and tile row are always present (`cold-stocked-1440-mock.png`, `cold-financials-stocked-1440-mock.png`).

### M4 (Medium): the temperature screen's third panel has a different title
- App: `W2-03-followup-evidence/temperature-stocked-1440-app.png` and `W2-04-evidence/temperature-*-app.png` call it "How each limit is set".
- Mock: "Claim boundary" (`temperature-stocked-1440-mock.png`; `v69-rendered-panels.json` "temperature").
- This difference is already known, but it is a wrong panel title.

### M5 (Medium): the "consequence line" count does not match the table (cold and EV financials)
- `W2-04-evidence/cold-financials-stocked-1440-app.png`: the chip says "1 consequence line", but the table has 2 rows.
- `W2-07-evidence/ev-financials-interrupted-1440-app.png`: the chip says "1 consequence line", but the table has 3 rows.
- Mock: the chip matches the row count ("2 consequence lines" and "3 consequence lines").

### M6 (Medium): cold exposure size is stated two different ways across screens
- `W2-04-evidence/cold-financials-stocked-1440-app.png`: "at least 19 °C-minutes (upper bound unknown)".
- `W2-04-evidence/temperature-stocked-1440-app.png`: "19–23 °C·min" for the same window and capture set.

### M7 (Medium): the cold assumption set differs between Financials and Assumptions
- `W2-04-evidence/cold-financials-stocked-1440-app.png` ("Assumptions in use") lists 4 rows: Stock quantity, Stock unit value, Product exposure rule, Currency.
- `W2-04-evidence/cold-assumptions-stocked-1440-app.png` lists 3 rows: Stock value in chamber, Product exposure rule, Currency.
- Mock: both screens list the same 3 rows.

### M8 (Medium): the EV overview says the single line diagram is "Not available yet", but it is built
- App: `W2-07-evidence/ev-interrupted-1440-app.png`, in "Charging activity and site power": "Open single line diagram · Not available yet".
- The `ev-sld` screen was built in W2-05a.
- The text is hard-coded at `frontend/src/sites/EvSiteViews.tsx:590` and locked by a test at `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx:603`.
- Mock: `ev-interrupted-1440-mock.png` has a live "Single line diagram →" link.

### M9 (Medium): the EV overview status strip has no overall status or confidence chip
- App: `W2-07-evidence/ev-interrupted-1440-app.png` shows only "Evidence limited" and "Generated test data".
- Mock: `ev-interrupted-1440-mock.png` shows "Needs attention" and "Confidence: Medium".
- The cold overview does show both chips ("Degraded" and "Confidence: Bounded").

### M10 (Medium): shortened record IDs make different records look like one
- `W2-06-evidence/ev-finding-interrupted-1440-app.png`: the chip "Finding 00000502" and the line "Record 00000502" are identical labels for two different objects.
- `W2-07-evidence/ev-evidence-analysis-interrupted-1440-app.png`: every row reads "Record 00000502 · No analysis link".
- `W2-07-evidence/ev-interrupted-1440-app.png`: every timeline event reads "Record 00000502".
- `W2-04-evidence/cold-evidence-analysis-stocked-1440-app.png`: every row starts "00000002-0…".
- Mock: distinct readable IDs (F-130, SES-011) or an "Open record" link.

### M11 (Medium): EV evidence says nothing is missing on rows rated Limited
- App: `W2-07-evidence/ev-evidence-interrupted-1440-app.png`.
  - Connector availability is "Limited", with "Not assessed" and "No required role missing".
  - Cause of interruption is "Limited", with "No required role missing".
- Mock: `ev-evidence-interrupted-1440-mock.png` names what is missing ("Connector 2 status for one hour", "Charger diagnostics and vehicle request").

### M12 (Medium): the EV Financials "Scenarios" subtab is dropped
- App: `W2-07-evidence/ev-financials-interrupted-1440-app.png` and `ev-assumptions-interrupted-1440-app.png` show only Overview and Assumptions.
- Cold shows "Scenarios · Not available yet" (`W2-04-evidence/cold-financials-stocked-1440-app.png`).
- Mock: `ev-financials-interrupted-1440-mock.png` has Overview, Assumptions and Scenarios.

### M13 (Medium): finding status strips leave out confidence (cold and EV) and lifecycle status (EV)
- `W2-03-followup-evidence/cold-finding-stocked-1440-app.png` and `cold-finding-excursion-stocked-1440-app.png` show "Open · site · evidence observed/bounded · window", with no confidence.
- `W2-06-evidence/ev-finding-interrupted-1440-app.png` shows "Finding 00000502 · Observed interruption", with no Open status and no confidence.
- Mock: every finding strip shows "F-xxx · site · Open · confidence … · evidence limited".

### M14 (Medium): an EV diagram parts-table row has lost its name
- App: `W2-05a-evidence/ev-sld-stocked-1440-app.png`, "What each part does", third row: Part is "Not declared", Role is "Not declared", Reports is "Not declared".
- The diagram labels the same slot "Charger 2 · Not declared".
- Mock: the row is named "Charger 2 · CHG-002".

## Per screen

| # | Screen | Result |
|---|---|---|
| 1 | cold-foundation | OK |
| 2 | cold-readiness | M2 |
| 3 | cold-sld | OK |
| 4 | cold | M3 |
| 5 | temperature | M4 |
| 6 | coldbackup | OK (supplies the counter-evidence for H1) |
| 7 | cold-evidence | H1, M3 (refused footer) |
| 8 | cold-evidence-analysis | M10 |
| 9 | cold-financials | M3, M5, M6, M7 |
| 10 | cold-assumptions | M7 (cross-screen) |
| 11 | cold-finding | M13 |
| 12 | cold-finding-excursion | M13 |
| 13 | ev-foundation | OK |
| 14 | ev-readiness | M2 |
| 15 | ev-sld | M14 |
| 16 | ev | M8, M9, M10 |
| 17 | sessions | OK |
| 18 | ev-evidence | M11 |
| 19 | ev-evidence-analysis | M10 |
| 20 | ev-financials | M5, M12 |
| 21 | ev-assumptions | M12 |
| 22 | ev-finding | M10, M13 |

## Summary

- 14 findings: 1 High, 13 Medium.
- 5 screens are OK (cold-foundation, cold-sld, coldbackup, ev-foundation, sessions). The other 17 have at least one finding.
- None is a missing, extra or reordered panel. All 22 screens match the mock's panel set and order at both widths.
- The findings are mostly data that contradicts its label, consistency between screens, and mock slots that were dropped (strip and tiles in refused states, the Scenarios subtab, the diagram link).

Residual (not counted): within one capture set, at the same revision `6d23d87d`, the cold peak shows 4.9 °C on temperature but 4.8 °C on backup and on the excursion finding. All three read the same field (`peak_observed`, `frontend/src/sites/ColdAssessmentViews.tsx:709`), so this is probably data captured at different moments rather than a code defect. A fresh capture should confirm it.

Polish (UI/UX pass): "W2" appears in the cold-assumptions subtitle; "3.8 degC" units; "steps below" sits under steps that are above it; placeholder items "No further evidence request recorded"; truncated session IDs; the app shell has no top site and window selector bar.
