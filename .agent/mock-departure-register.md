# V69 mock departure register

Architect classification, 2026-10-23. Counts below count distinct screen/element rulings, including resolved temporary and withdrawn rulings; repeated mentions of one ruling in a spec are one row. A proposed D3 correction is a merge gate under `.ai/ROLE_CONFIG.md`, not an accepted exception. `planned` means specified but not proven built here.

| Category | Count |
| --- | ---: |
| D1 data or feature unavailable | 31 |
| D2 improvement | 24 |
| D3 structural oversight | 6 |
| D4 illustrative placeholder | 28 |
| D5 build order | 5 |
| D6 technical constraint | 0 |
| **Total** | **94** |

## D1 — data or feature unavailable

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | W5-02 K2a M2 | `cold-work` | Work notice promises global create | First sentence only | D1 | No operator create flow exists; W4 command is service-only. | Future global Work create flow | planned |
| R02 | W5-02 K2a M4 | `cold-work` | Actions strip says same as global list and offers Manage | Cold-only scope text; global gap | D1 | W3 global Actions excludes cold roots. | Future cross-domain global Actions union | planned |
| R03 | W5-04 V2a/V3a E1 | `ev-work`, `ev-work-incidents`, `ev-work-maintenance` | Work notice promises global create | First sentence only | D1 | No operator create flow exists. | W5-04 V2a/V3a; future global Work create flow | planned |
| R04 | W5-04 V2a E4 | `ev-work` | Actions strip says same as global list and offers Manage | EV-only scope text; global gap | D1 | W3 global Actions excludes EV roots. | W5-04 V2a; future cross-domain global Actions union | planned |
| R05 | W5-01 C2 | `cold-cooling` | Recovery temperature curves | Chart frame and selected categorical marks; no curve | D1 | Selected records have no accepted numeric recovery series. | Future selected recovery-series producer | planned |
| R06 | W5-03 E3 | `energy` | Continuous import-power line | Selected sample marks and declared limit; no connecting path | D1 | Accepted samples do not establish continuous coverage. | Future coverage-capable EV evidence read | planned |
| R07 | W6-01 B2 | `maintenance` | Lifecycle notice describes active follow-up | Activity recorded, outcome unverified | D1 | No work-outcome evaluator or follow-up path exists. | Future work-outcome evaluator | planned |
| R08 | W6-01 B3 | `maintenance-preventive` | Overdue badge and due cards | Due status not assessed | D1 | Authored due dates do not prove an operating schedule or evaluator. | Future due evaluator | planned |
| R09 | W6-01 B3 | `maintenance-preventive` | Assets link in status strip and asset cells | Unavailable Assets control; plain asset label | D1 | General Assets destination is not mounted. | Future global Assets route | planned |
| R10 | W6-01 B3 | `maintenance-preventive` | Monthly/Quarterly trigger and due-state badges | Calendar/running-hours fact and Draft | D1 | W4 has no recurrence rule or due evaluator. | Future preventive schedule model | planned |
| R11 | W6-01 B3 | `maintenance-preventive` | Footer says completing a plan creates maintenance record | Completion unavailable; performed record is separate | D1 | No plan-completion command exists. | Future plan completion flow | planned |
| R12 | W6-01 E2 | `oprecords` | Manual-reading submission promise | Inert form and submission unavailable text | D1 | No authorized operator submission service exists. | Future operator record command | built: W6-01 E2 `173cfc73`; review pending |
| R35 | W4-01 B1; W2-04 | `cold-work`, `ev-work`, `cold-financials` | Global Work create flow and mock repair/stock money | Unavailable create destination and unpriced exposure gap | D1 | No operator create flow or declared stock-value/repair source supports those claims. | Future Work command and cold valuation units | built |
| R36 | W2-05a QM–QP | `ev-sld`, `ev-readiness` | Load manager, breakers, feeder meters, investigation Action | Unknown equipment slots and unavailable Action entry | D1 | These components and Action are undeclared/unbuilt. | Future EV Foundation and Action units | built |
| R41 | W6-01 C4 | `wr-history` | `Site visit started` (row 3) and `Verification pending` (row 5) in the authored chronology | Two in-table gaps, `Site visit start not recorded` and `Verification pending · no outcome assessment recorded`, with `—` in Time/By after the last authored row on the last page only | D1 | W4 has no selected site-visit event or work-outcome assessment; inserting undated gaps at the mock positions would imply an unsupported sequence among authored events. | Future site-visit event and work-outcome evaluator | planned |
| R51 | W5-03 E3 | `energy` | `Stationary battery: Not configured` conclusion value | `Unknown` and the Foundation limitation | D1 | The merged EV Foundation cannot declare battery presence or absence. | Future EV battery configuration; W5-03 E3 gap | planned |
| R56 | W5-03 E4 | `ev-health` | Stationary battery `Not applicable` / `None installed` | Always `Unknown` / `Battery configuration is not established by this Foundation.` | D1 | The merged EV Foundation cannot declare stationary storage present or absent. | Future EV battery configuration; W5-03 E4 | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |

## D2 — improvement on the mock; flag at walkthrough

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R13 | W5-01 C2/C3 | `cold-cooling`, `cold-health` | No currentness notice | Amber pending/stale/historical/unknown notice | D2 | Explicit selection state prevents a stale reading appearing current. | W5-01 C2/C3, owner walkthrough | planned |
| R14 | W5-01 C3 | `cold-health` | No condition ceiling notice | Amber condition/evidence limit notice | D2 | Fault/start evidence must not look like a physical diagnosis. | W5-01 C3, owner walkthrough | planned |
| R15 | W5-03 E2/E3/E4/E6 | `availability`, `energy`, `ev-health`, `ev-scenarios` | No live-selection notices | Amber cutoff/currentness/pending notices | D2 | Selected read state needs visible qualification. | W5-03 E2–E6, owner walkthrough | planned |
| R16 | W5-03 E4 | `ev-health` | No condition ceiling notice | Amber condition/evidence limit notice | D2 | Session/fault rows are not a charger diagnosis. | W5-03 E4, owner walkthrough | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |
| R17 | W6-01 A2 | `incidents` | Static source text | Selected-provenance disclosure | D2 | Exact source detail stays available without crowding the 390px table. | W6-01 A2, owner walkthrough | planned |
| R18 | W6-01 A2 | `incidents` | No adjustable cutoff control | URL-preserved explicit `known_at` only | D2 | Explicit historical links are reproducible without a misleading arbitrary selector. | W6-01 A2, owner walkthrough | planned |
| R19 | W6-01 C4 | `wr-history` | Short minute-only Time | UTC year and seconds; occurrence disclosure | D2 | One-second real events otherwise look tied. | W6-01 C4, owner walkthrough | planned |
| R20 | W1/W2 decision | `temperature`, `cold-finding` | Claim boundary / Power-to-load wording | Plain-language limit and compressor-response headings | D2 | Terms identify the actual cold-chain meaning more clearly. | W2-03; owner W2 walkthrough | built |
| R21 | W1 decision | Site/Finding/Work/Financials subtab screens | Mock live entries for unbuilt destinations | Visible noninteractive Not available yet entries | D2 | Preserves menu placement and prevents false navigation. | W1 F5; owner W1 walkthrough | built |
| R46 | W5-03 E3 | `energy` | Import chart only | Chart followed by a collapsed `Measure`/`Value` detail disclosure | D2 | Exact sample facts remain keyboard and screen-reader accessible within the measured panel cap; an always-open table exceeded the cap. | W5-03 E3; owner walkthrough | planned |
| R49 | W5-03 E3 | `energy` | No separate partial/unknown coverage disclosures under the cards | Selected partial-kWh and unknown-duration disclosure lines | D2 | Keeps incomplete meter evidence visible beside the summary without replacing any mock panel. | W5-03 E3; owner walkthrough | planned |
| R27 | W5-03 E6 | `ev-scenarios` | Empty placeholder block inside `Financial scenarios` | Persisted authored rows replace that empty block only when items exist | D2 | A real authored list makes the mock's designed empty state useful after a scenario is defined; no observed outcome is implied. | W5-03 E5/E6; owner walkthrough | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |
| R58 | W5-03 E4 | `ev-health` | Two condition-table rows: fault connector and Site meter | Optional third row for another selected connector with an honest no-assessment statement | D2 | The selected Foundation may include another connector that needs visible coverage. | W5-03 E4; owner walkthrough | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |

## D3 — structural oversight; correct before merge

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R22 | W5-01 C3 | `cold-health` | Mock ends after Condition and evidence | Additional Data sources panel | D3 | A faithful alternative exists: keep cold Health panel set and point Foundation Data sources to the existing `cold-evidence` source panel. | W5-F1 F1-1: remove added panel and fix fragment destination; re-review | built: W5-F1 f0812934 |
| R60 | W5-03 E4 | `ev-health` | Mock ends after Condition and evidence | Proposed additional S7 Data sources panel, withdrawn before build | D3 | Same structural oversight as R22; retain the sole mock panel and point Foundation at `/sites/{code}/ev/evidence#ev-site-sources-heading`. | W5-03 E4 correction and review | corrected in spec; never ship extra panel |
| R23 | W5-02 K3a M5 withdrawn | `cold-work-incidents` | Site-local Window date/time | Fixed EAT/UTC formatting was proposed | D3 | `SiteDetailReadModel.timezone` already exists. Correct with `siteWindowText(occurred_at, site.timezone)` and two-zone/date-boundary tests. | W5-02 K3a | resolved |
| R24 | W5-04 V3a E5 withdrawn | `ev-work-incidents` | Site-local Window date/time | Fixed UTC/offset formatting was proposed | D3 | Stored EV Site timezone already exists. Reuse K3a `siteWindowText` and test both zones/date boundary. | W5-04 V3a | resolved |
| R37 | W2-03 retro correction | `cold-performance` | Loading / batch row | Row was omitted in first build | D3 | The mock row can be rendered faithfully; restore it in its original order. | W5-F1 F1-2: keep row, prove mock order and capture; re-review | built: W5-F1 42964500 |
| R38 | W2-03 retro correction | `cold-evidence-analysis` | Exact target record links | Links were offered before target integration proof | D3 | Keep link placement but show labelled references/unavailable state until exact target is proved. | W5-F1 F1-3: remove unproved anchor and capture; re-review | built: W5-F1 89b88a40 |

## D4 — illustrative mock placeholder

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R25 | W5-01 C5 | `cold-scenarios` | Empty illustrative scenarios only | Persisted authored rows/basis and honest pending state | D4 | Real selected authored facts replace a static example without claiming observed outcome. | W5-01 C4/C5 | planned |
| R26 | W5-03 E2 | `availability` | Fixed percentages and 08:00/12:00/16:00 axis | Selected spans, derived percentages and window times | D4 | Mock numbers are examples, not accepted Site evidence. | W5-03 E1a/E2 | planned |
| R57 | W5-03 E4 | `ev-health` | Connector card notes and `Needs attention`/gray/amber values for the illustrative fault pattern | Same positions and tones with selected fault count and honest Unknown when no condition assessment exists | D4 | The mock's normal and single-fault sentences are illustrative; no completed session proves hardware health. | W5-03 E4 | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |
| R59 | W5-03 E4 | `ev-health` | Site-meter row says `Power limit respected in observed samples` | Always `Power limit not assessed from selected samples` for a selected `SITE_METER` | D4 | Health DTO carries no peak/limit comparison or interval-wide proof; the mock's positive statement is illustrative. | W5-03 E4; future reviewed Health claim field | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |
| R28 | W6-01 B3 | `maintenance-preventive` | PM-0455/INC-203 narrative | No incident link or cause established | D4 | Selected stored plans have no cited incident relation. | W6-01 B3 | planned |
| R29 | W6-01 E2 | `oprecords` | Cards 2–4 example counts/REC codes | No publication, review workflow or request list established | D4 | Mock counts and codes are illustrative; selected store cannot substantiate them. | W6-01 E2 | built: W6-01 E2 `173cfc73`; review pending |
| R30 | W6-01 E2 | `oprecords` | Requested/accepted/in-review example rows and role names | Persisted Submitted heads and stored actor IDs | D4 | W4 stores submitted authored records and actor IDs, not example roles/statuses. | W6-01 E2 | built: W6-01 E2 `173cfc73`; review pending |
| R31 | W6-01 E2 | `oprecords` | Prose says requested records support conclusions | Two bounded paragraphs on authored records and missing requests | D4 | Requested-record ledger and accepted-evidence link are absent. | W6-01 E2 | built: W6-01 E2 `173cfc73`; review pending |
| R39 | W6-01 A2 and C4 | `incidents`, `wr-history` | Example incident rows and named people | Selected stored rows; stored actor disclosure or Name not recorded | D4 | Example people and statuses cannot be attributed to selected records. | W6-01 A2/C4 | planned |
| R42 | W6-01 C4 | `wr-history` | `Marked completed · witness test outstanding` | `Completed · outcome not established · maintenance record {id}`; witness-test text only when authored | D4 | The mock witness-test phrase is illustrative; COMPLETE supplies a maintenance-record ID but no witness-test fact or verified outcome. | W6-01 C4 | planned |
| R43 | W5-03 E2 | `availability` | `2 connectors × 8 scheduled hours = 16 connector-hours` status text | Same form with selected count/hours, or a truthful varying-schedule/unknown sentence | D4 | Fixed mock count and hours are examples. | W5-03 E1a/E2 | planned |
| R44 | W5-03 E2 | `availability` | Four fixed card notes and 93.75% example | Mock note forms with selected numerator/denominator and honest unknown values | D4 | Fixed amounts and coverage cannot represent another Site. | W5-03 E2 | planned |
| R45 | W5-03 E2 | `availability` | Fixed connector-2 chart note, bound prose and missing-hour next-evidence text | Same forms with selected connector, durations and accepted transition timestamps | D4 | The example connector/hour and aggregation claim are not selected facts. | W5-03 E2 | planned |
| R47 | W5-03 E3 | `energy` | `Complete session meter records · incomplete session energy excluded` for the example | Same sentence only when supported; limited-basis sentence otherwise | D4 | A missing/partial selection cannot assert complete records. | W5-03 E3 | planned |
| R48 | W5-03 E3 | `energy` | Four fixed card notes, including aborted-session kWh and scenario tariff | Mock note forms with selected aborted kWh/window/tariff or honest fallback | D4 | Fixed amounts are illustrative. | W5-03 E3 | planned |
| R50 | W5-03 E3 | `energy` | `Energy basis: measured` badge | `Energy basis: limited` when complete selected basis is unsupported | D4 | The mock measured badge assumes its example data. | W5-03 E3 | planned |
| R52 | W5-03 E3 | `energy` | Conclusion note asserts a revenue estimate | Selected estimate note only when eligible; otherwise no eligible estimate/payment evidence sentence | D4 | A withheld/unpriced selection has no estimate. | W5-03 E3 | planned |
| R53 | W5-03 E3 | `energy` | Bridge row 1 fixed 120 kWh, tariff and $36 | Selected quantity/tariff/amount or an unpriced gap | D4 | Mock money is illustrative, not selected consequence. | W5-03 E3 | planned |
| R54 | W5-03 E3 | `energy` | Bridge row 2 `Incomplete session` / `Unavailable` | Same gap when no partial amount; selected partial kWh / `Not priced` when present | D4 | The selected partial amount should remain visible without pricing it. | W5-03 E3 | planned |
| R55 | W5-03 E3 | `energy` | Fixed import chart axis and 76/80 kW example | Selected sample marks, derived axes and selected declared limit | D4 | Mock values are examples; no continuous sample coverage is proved. | W5-03 E1b/E3 | planned |

## D5 — temporary build order

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R32 | W6-01 B2→C2 | `maintenance` | Request row opens Overview | Interim same-window Site maintenance link | D5 | Detail route is mounted by C2. | W6-01 C2 link promotion and review | planned |
| R33 | W6-01 B2→B3 | `maintenance` | Preventive View detail link | Interim unavailable slot | D5 | Preventive route is mounted by B3. | W6-01 B3 link promotion and review | planned |
| R34 | W6-01 C3→E2 | `wr-record` | Live Operational records link | Interim plain REC codes | D5 | Operational records route is mounted by E2. | W6-01 E2 link promotion and review | resolved: W6-01 E2 `173cfc73`; review pending |
| R40 | W2-03→W5-01; W2-06→W5-03 | `cold-performance`, `cold-finding`, `sessions`, `ev-finding` | Cooling, Recommendation, Availability and Energy destinations | Visible Not available yet entries in mock order | D5 | Destinations were built in later W5 units; no early link may point to an unbuilt page. | W5-01/W5-03 route promotion and review | built |

## D6 — technical constraint

No unresolved D6 ruling was found. The W5 C2/E3 chart substitutions originally attributed to the SVG allowlist were withdrawn: the feasible correction is to register a graphics module and restore the mock chart form. The W6 source disclosure and Time precision are classified as D2 choices, not platform necessities.


## W5-02 Site-screen additions (2026-10-23)

These rows use the register columns above and are included in its category counts.

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R65 | W5-02 K2a/K3a/K4a | `cold-work`, `cold-work-incidents`, `cold-action` | Mock Finding codes F-118/F-119 | `Finding {id8}` in the same source/status cells | D1 | No public cold Finding code exists on the selected wire. | Future public Finding code; W5-02 preserves selected UUID | planned |
| R66 | W5-02 K2a/K3a/K4a | `cold-work`, `cold-work-incidents`, `cold-action` | Linked Finding and Open source Finding | Plain selected label, revision disclosure and unavailable exact-revision control | D1 | Cold Finding frame ignores `revision_id`; following current URL may show another revision. | Future exact-revision cold Finding API/client/frame | planned |
| R67 | W5-02 K2a | `cold-work` | `Due dates are not yet set in this example` | Selected-data phrase Due dates are not yet set | D4 | Example qualifier is not true for arbitrary Sites. | W5-02 K2a | planned |
| R68 | W5-02 K3a/K4a | `cold-work-maintenance`, `cold-action` | WR and Inspect target `workverification` | Selected W6 request Overview in same slots | D1 | W6 Verification destination is unavailable; Overview is mounted. | Future W6 request Verification destination | planned |
| R69 | W5-02 K2a to K4a | `cold-action` and W1 Action detail | Actions active in operator rail | Sites active on interim cold placeholder until K4a | D5 | K4a restores the mock Action-root selection for every Site Action detail path, including W1, with a pathname-scoped override. | W5-02 K4a rail override, W1/cold tests and review | resolved: W5-02c K4a (merge f8137643) |
| R70 | W5-02 K3a | `cold-work-maintenance` | Activity Completed chip only | Same chip plus stored activity in in-cell disclosure | D2 | Exposes attested text without changing column/order. | W5-02 K3a; owner walkthrough | planned |
| R71 | W5-02 K3a | `cold-work-maintenance` | Outcome Unverified badge only | Same badge plus selected outcome note in in-cell disclosure | D2 | Qualifies unverified state in the mock cell. | W5-02 K3a; owner walkthrough | planned |
| R72 | W5-02 K3a | `cold-work-maintenance` | Next evidence witnessed automatic-start test | Selected next-evidence copy or `No next evidence recorded` | D1 | No selected instruction proves the mock witness test. | Future authored next-evidence producer | planned |
| R73 | W5-02 K3a | `cold-work-incidents` | INC code opens Incident detail | Plain INC code in same Case cell | D1 | No Incident detail route is mounted. | Future W6 Incident detail route | planned |

- Register IDs: the W5-02b R56-R64 were renumbered R65-R73 because they collided with the W5-03b IDs (coordinator, 2026-10-23).

## W5-04 pre-flight additions (2026-10-23)

Mock selectors are `SITE_WORK.ev`, `WORK_COLS`, `WORK_EMPTY`, `siteWorkScreen('ev',…)`, and `add('ev-action'…)` in `frontend/mockups/v69/index.html`. R74–R85 are planned, not built.

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R74 | W5-04 V2a/V3a | `ev-work`, `ev-work-incidents` | Source/Linked findings mock F-130 code | `Finding {id8}` from selected public UUID | D1 | Selected EV Finding has no public F-130 code. | V2a/V3a; future public Finding code | planned |
| R75 | W5-04 V2a/V3a | `ev-work`, `ev-work-incidents` | Finding link opens selected source | Plain `Finding {id8}` and `Finding version` disclosure containing `The selected Finding revision cannot be opened here yet.`; no pseudo-link in the list cell | D1 | EV Finding frame ignores `revision_id`; a window-only link can show another revision. | V2a/V3a; future exact-revision Finding frame | ruled correction |
| R76 | W5-04 V2a | `ev-work` | `Due dates are not yet set in this example` | `Due dates are not yet set` only for all-null selected due dates | D4 | Example qualifier cannot describe arbitrary persisted rows. | V2a | planned |
| R77 | W5-04 V2a/V4a | `ev-work`, `ev-action` | Fixed EAT topbar example window | Page-local Work `Window` labels `From (UTC)` and `To (UTC, exclusive)`; EV detail preserves URL query without a control. Fixture `Etc/UTC` equals UTC; separate non-UTC Site-zone display is deferred. | D4 | The selected window is UTC and the app has no topbar picker; a Site-zone abbreviation beside UTC dates would mislead. | V2a/V4a | ruled correction |
| R78 | W5-04 V2a | `ev-work` | Example connector/power subtitle | Always `EV charging operations at this site.` under stored display name | D4 | Site read has no subtitle field or selected Foundation facts for the example configuration. | V2a | ruled correction |
| R79 | W5-04 V2a | `ev-work` | `1 actions` in scope strip | `1 action` | D2 | Correct singular grammar improves clarity. | V2a; owner walkthrough | planned |
| R80 | W5-04 V2a/V3a/V4a | `ev-work`, `ev-work-incidents`, `ev-work-maintenance`, `ev-action` | No currentness notice in example | Selected historical/pending/stale/unknown notice below Work strip and before first panel, or before detail plan | D2 | Selected cutoff/source state must remain visible. R104 owns tone only. | V2a/V3a/V4a; owner walkthrough | planned |
| R81 | W5-04 V3a | `ev-work-maintenance` | Activity Completed chip only | Completed chip plus stored activity disclosure | D2 | Exposes attested text in the existing cell. | V3a; owner walkthrough | planned |
| R82 | W5-04 V3a | `ev-work-maintenance` | Outcome Unverified badge only | Badge plus attested outcome note disclosure | D2 | Clarifies what was recorded without claiming verified outcome. | V3a; owner walkthrough | planned |
| R83 | W5-04 V3a | `ev-work-maintenance` | WR opens Verification | WR opens mounted W6 Overview | D1 | Request Verification destination is unavailable. | V3a; future W6 request Verification | planned |
| R84 | W5-04 V3a | `ev-work-maintenance` | Mock witnessed next-evidence instruction | Selected copy or `No next evidence recorded` | D1 | No selected instruction proves the mock witness test. | V3a; future authored next-evidence producer | planned |
| R85 | W5-04 V3a | `ev-work-incidents` | INC code opens detail | Plain INC code | D1 | No Incident detail route is mounted. | V3a; future Incident detail route | planned |

## W5-03a review correction (2026-10-23)

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R86 | W5-03a E2 | `availability` | Connector right-hand local service period | Selected `HH:mm–HH:mm UTC` occurrence or window, explicitly labelled UTC | D1 | The depth DTO carries UTC instants without a Site-local offset, so local time cannot be asserted. | Future Site-timezone read; W5-03a E2 | planned correction; owner walkthrough |
| R87 | W5-03a E3 | `energy` | Green `Yes` for example peak below limit | Selected `Yes` green, `No` red or `Unknown` neutral from the selected sample peak and time-valid limit | D4 | The example 76/80 kW result cannot stand for another selected window. | W5-03a E3 | planned correction |
| R88 | W5-02 K2a | `cold-work`, `cold-work-incidents`, `cold-work-maintenance` | v69 topbar range picker | Compact `Window` control after Work subtabs, before scope strip | D1 | The app has no topbar or range-picker slot; URL-only selection is unusable. | W5-02 K2a; future shared Site topbar candidate; owner walkthrough | ruled correction |
| R89 | W5-02 K3a | `cold-work-maintenance` | Example `GEN-CR-01 · backup generator` Asset cell | Returned COLD-LAB-001 `generator-1 · backup generator` with selected ID disclosure | D4 | The mock asset code is illustrative; Foundation registers `generator-1`. | W5-02 K3a | ruled correction |
| R90 | W5-02 K2a | `cold-work`, `cold-work-incidents`, `cold-work-maintenance` | Example Site-specific cold subtitle | `Cold-room operations at this site.` under stored Site name | D4 | Site read has no subtitle field; Foundation `summary` is a configuration-document summary. | W5-02 K2a | ruled correction |
| R91 | W5-02 K2a/K3a/K4a | `cold-work`, `cold-work-incidents`, `cold-work-maintenance`, `cold-action` | No live currentness notice between strip and panel | Selected-state notice between strip and first panel, blue for Historical/Unknown and amber for Pending/Stale | D2 | A live selected cutoff or source limit must be visible without changing the mock panel order. | W5-02 K2a (Actions), K3a (cases), K4a (Action detail); owner walkthrough | ruled correction; K4a extension |
| R92 | W5-02 K3a | `cold-work-incidents`, `cold-work-maintenance` | Case panel has table or empty card and subtitle, no basis disclosure | Selected `What this list is based on` disclosure at panel foot after table/pager or empty card | D2 | Makes the W4 selected window, cutoff and provenance inspectable on cold case tabs. | W5-02 K3a; owner walkthrough | ruled pre-flight |
| R93 | W5-02 K3a | `cold-work-incidents`, `cold-work-maintenance` | One illustrative row in a horizontally scrollable five-column table | Selected `Showing a–b of N` below-table `Pages` block with `Showing a–b of N`, `Scroll the table for more columns →` and page controls | D2 | Real selected case lists can exceed the mock's one example row and mobile width. | W5-02 K3a; owner walkthrough | ruled pre-flight |
| R94 | W5-02 K3b | `cold-work-incidents`, `cold-work-maintenance` | Short text in Case, What happened, Activity and Outcome cells | Two-line previews with `Read full text` disclosures for selected long values in the same cells | D2 | Full selected 160-code-point values must remain readable without changing columns or clipping. | W5-02 K3b; owner walkthrough | ruled pre-flight |

## W5-03b E4/E6 UI pre-flight refresh (2026-10-23)

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R95 | W5-03b E4 | `ev-health` | Cards labelled `Connector 1` and `Connector 2` | Selected Foundation `display_name` per `CONNECTOR` row | D4 | Mock names are illustrative; the selected Foundation label identifies the actual configured connector. | E4 | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |
| R96 | W5-03b E4 | `ev-health` | Exactly two connector cards, then battery | One card per selected connector, then battery; zero connectors show the Health empty sentence and battery | D2 | The selected Foundation may have zero, one or more than two connectors; hiding configured assets would mislead. | E4; owner walkthrough | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |
| R97 | W5-03b E4 | `ev-health` | Site-meter row in `Condition and evidence` | No Site-meter row when the selected meter lacks a Site-import role (`kind:"UNKNOWN"`) | D1 | The meter cannot be identified as a Site meter from the selected binding. | E4; future Site-import binding | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |
| R98 | W5-03b E6 | `ev-scenarios` | Empty placeholder panel with no list paging | First page of at most 50 authored rows; a non-null cursor shows `Showing first {items.length} authored scenarios. More exist; later pages are not available in this view.` | D1 | E6 has no later-page control, so the list must disclose its visible limit. | E6; future scenario paging | built: W5-03b E4/E6 (`task/W5-03b-ev-health-ui`), review pending |

## W5-02c K4 Action-detail pre-flight refresh (2026-10-24)

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R99 | W5-02c K4a/K4b | `cold-action` | Short one-line ACT-051 heading and 44 px strip with `Maintenance lead` | Full selected 160-code-point Action title and owner wrap within the heading and strip; selected Finding version stays inspectable | D2 | Stored titles and owners can exceed the illustrative mock values; full text must remain readable at 390 px. | K4a presentation, K4b both-width capture; owner walkthrough | ruled pre-flight |
| R100 | W5-02c K4a/K4b | `cold-action` | Completed WR-019 sentence in `Related activity` | `No completed inspection is linked to this Action.` when the selected cutoff has no completed linked inspection | D2 | A selected Action may exist before its WR link; completion cannot be inferred from the mock example. | K4a selected presenter, K4b cutoff capture; owner walkthrough | ruled pre-flight |
| R101 | W5-02c K4a | `cold-action` | Two headed loaded panels | One untitled state panel during loading, 404 or 403/422/503 refusal | D2 | A read without loaded detail cannot truthfully populate either mock panel. | K4a; owner walkthrough | ruled pre-flight |
| R102 | W5-02c K4a | `cold-action` | `Related activity` says completed WR-019 inspection | Selected linked OPEN/IN_PROGRESS request is named with its actual state and the witnessed-test requirement; Inspect opens that request | D2 | The selected request can be ongoing; saying it is complete or hiding its link would misstate the record. | K4a; owner walkthrough | ruled build-time; inform owner |

## W5-03b E4/E6 build-time refresh (2026-10-24)

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R103 | W5-03b E4 | `ev-health` | Subtitle `2 × 60 kW connectors · 80 kW site limit · no stationary battery` | `Health · site-level asset-condition summary` | D4 | The mock equipment values describe its illustrative Site and the E4 Health DTO does not supply ratings or battery absence for every selected Foundation. | E4; inform owner | built: W5-03b E4 fix round (label in `EvHealthDepth.tsx`), review pending |

## W5-04 readiness refresh (2026-10-24)

R104–R110 carry the named cold departures to EV without changing the cold rows. Mock: `frontend/mockups/v69/index.html` `SITE_WORK.ev`/`siteWorkScreen` (334–343), `ev-action` (710–713).

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R104 | W5-04 V2a/V3a/V4a | `ev-work`, `ev-work-incidents`, `ev-work-maintenance`, `ev-action` | No currentness notice in example | Blue tone for Historical/Unknown; amber tone for Pending/Stale (cold R91); placement is R80 | D2 | Severity follows selected source state. | V2a/V3a/V4a; owner walkthrough | planned |
| R105 | W5-04 V3a | `ev-work-incidents`, `ev-work-maintenance` | Case panel has no basis disclosure | `What this list is based on` at panel foot (cold R92) | D2 | Selected W4 basis remains inspectable. | V3a; owner walkthrough | planned |
| R106 | W5-04 V3a | `ev-work-incidents`, `ev-work-maintenance` | Example table has no pager | `Showing a–b of N` Pages block below table (cold R93) | D2 | Real selected case list may exceed one row. | V3a; owner walkthrough | planned |
| R107 | W5-04 V3a/V3b | `ev-work-incidents`, `ev-work-maintenance` | Short example cell text | Two-line previews with `Read full text` in the same cells (cold R94) | D2 | Full 160-character values stay readable. | V3a/V3b; owner walkthrough | planned |
| R108 | W5-04 V2a/V2b | `ev-work` | One Action example row | First four visible Action rows with `Show all {n} Actions` for remaining selected page rows | D2 | A five-row selected page needs a readable fold without losing rows. | V2a/V2b; owner walkthrough | planned |
| R109 | W5-04 V4a/V4b | `ev-action` | Short one-line title/owner | Full selected 160-character title/owner wrap (cold R99) | D2 | Stored text can exceed the illustrative example. | V4a/V4b; owner walkthrough | planned |
| R110 | W5-04 V4a | `ev-action` | Loaded headed panel | One untitled state panel for loading, 404, 409 and other refused reads (cold R101) | D2 | No criteria can be shown before a valid detail read; Retry re-reads a changed basis. | V4a; owner walkthrough | planned |

## W5-04a Q6-Q12 producer correction (2026-10-24)

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R111 | W5-04 V2a/V3a/V4a | `ev-work`, `ev-work-incidents`, `ev-work-maintenance`, `ev-action` | Illustrative Depot Charging Hub Site name | Stored EV-LAB-001 display name; `Depot` remains a private manifest label | D4 | The registered unshifted EV replay is bound to EV-LAB-001, and the Site read has no short-name field. | V1b producer, V2a/V3a/V4a presentation | planned; owner walkthrough |

## W5-04 UI readiness additions (2026-10-24)

Mock: `frontend/mockups/v69/index.html:337-343,710-713`. These follow R111, the previous last row.

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R112 | W5-04 V2a/V3a | `ev-work`, `ev-work-incidents`, `ev-work-maintenance` | v69 topbar range picker | Compact page-local `Window` control after subtabs and before scope strip (cold R88) | D1 | The app has no topbar picker; Site-local selection must remain usable. | V2a/V3a; owner walkthrough | planned |
| R113 | W5-04 V2a/V3a/V4a | `ev-work`, `ev-work-incidents`, `ev-work-maintenance`, `ev-action` | Linked EV Action code opens `ev-action` | EV Action code plain text until V4a mounts EV detail, then live selected link from the Work Action row and both case-row `UTC and IDs` disclosures; carry selected `from`, `to` and explicit `known_at` | D1 | A domain ID would otherwise reach the W1 battery presenter during interim merges; live case links must retain the selected read scope. | V2a/V3a interim; V4a resolves all named screens | planned temporary; close in V4a |
