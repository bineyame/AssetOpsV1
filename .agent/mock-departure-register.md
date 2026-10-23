# V69 mock departure register

Architect classification, 2026-10-23. Counts below count distinct screen/element rulings, including resolved temporary and withdrawn rulings; repeated mentions of one ruling in a spec are one row. A proposed D3 correction is a merge gate under `.ai/ROLE_CONFIG.md`, not an accepted exception. `planned` means specified but not proven built here.

| Category | Count |
| --- | ---: |
| D1 data or feature unavailable | 16 |
| D2 improvement | 11 |
| D3 structural oversight | 5 |
| D4 illustrative placeholder | 19 |
| D5 build order | 4 |
| D6 technical constraint | 0 |
| **Total** | **55** |

## D1 — data or feature unavailable

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R01 | W5-02 K3a M2 | `cold-work` | Work notice promises global create | First sentence only | D1 | No operator create flow exists; W4 command is service-only. | Future global Work create flow | planned |
| R02 | W5-02 K3b M4 | `cold-work` | Actions strip says same as global list and offers Manage | Cold-only scope text; global gap | D1 | W3 global Actions excludes cold roots. | Future cross-domain global Actions union | planned |
| R03 | W5-04 V3a E1 | `ev-work` | Work notice promises global create | First sentence only | D1 | No operator create flow exists. | Future global Work create flow | planned |
| R04 | W5-04 V3b E4 | `ev-work` | Actions strip says same as global list and offers Manage | EV-only scope text; global gap | D1 | W3 global Actions excludes EV roots. | Future cross-domain global Actions union | planned |
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

## D2 — improvement on the mock; flag at walkthrough

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R13 | W5-01 C2/C3 | `cold-cooling`, `cold-health` | No currentness notice | Amber pending/stale/historical/unknown notice | D2 | Explicit selection state prevents a stale reading appearing current. | W5-01 C2/C3, owner walkthrough | planned |
| R14 | W5-01 C3 | `cold-health` | No condition ceiling notice | Amber condition/evidence limit notice | D2 | Fault/start evidence must not look like a physical diagnosis. | W5-01 C3, owner walkthrough | planned |
| R15 | W5-03 E2/E3/E4/E6 | `availability`, `energy`, `ev-health`, `ev-scenarios` | No live-selection notices | Amber cutoff/currentness/pending notices | D2 | Selected read state needs visible qualification. | W5-03 E2–E6, owner walkthrough | planned |
| R16 | W5-03 E4 | `ev-health` | No condition ceiling notice | Amber condition/evidence limit notice | D2 | Session/fault rows are not a charger diagnosis. | W5-03 E4, owner walkthrough | planned |
| R17 | W6-01 A2 | `incidents` | Static source text | Selected-provenance disclosure | D2 | Exact source detail stays available without crowding the 390px table. | W6-01 A2, owner walkthrough | planned |
| R18 | W6-01 A2 | `incidents` | No adjustable cutoff control | URL-preserved explicit `known_at` only | D2 | Explicit historical links are reproducible without a misleading arbitrary selector. | W6-01 A2, owner walkthrough | planned |
| R19 | W6-01 C4 | `wr-history` | Short minute-only Time | UTC year and seconds; occurrence disclosure | D2 | One-second real events otherwise look tied. | W6-01 C4, owner walkthrough | planned |
| R20 | W1/W2 decision | `temperature`, `cold-finding` | Claim boundary / Power-to-load wording | Plain-language limit and compressor-response headings | D2 | Terms identify the actual cold-chain meaning more clearly. | W2-03; owner W2 walkthrough | built |
| R21 | W1 decision | Site/Finding/Work/Financials subtab screens | Mock live entries for unbuilt destinations | Visible noninteractive Not available yet entries | D2 | Preserves menu placement and prevents false navigation. | W1 F5; owner W1 walkthrough | built |
| R46 | W5-03 E3 | `energy` | Import chart only | Chart followed by a collapsed `Measure`/`Value` detail disclosure | D2 | Exact sample facts remain keyboard and screen-reader accessible within the measured panel cap; an always-open table exceeded the cap. | W5-03 E3; owner walkthrough | planned |
| R49 | W5-03 E3 | `energy` | No separate partial/unknown coverage disclosures under the cards | Selected partial-kWh and unknown-duration disclosure lines | D2 | Keeps incomplete meter evidence visible beside the summary without replacing any mock panel. | W5-03 E3; owner walkthrough | planned |

## D3 — structural oversight; correct before merge

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R22 | W5-01 C3 | `cold-health` | Mock ends after Condition and evidence | Additional Data sources panel | D3 | A faithful alternative exists: keep cold Health panel set and point Foundation Data sources to the existing `cold-evidence` source panel. | W5-F1 F1-1: remove added panel and fix fragment destination; re-review | built: W5-F1 f0812934 |
| R23 | W5-02 K3a M5 withdrawn | `cold-work-incidents` | Site-local Window date/time | Fixed EAT/UTC formatting was proposed | D3 | `SiteDetailReadModel.timezone` already exists. Correct with `siteWindowText(occurred_at, site.timezone)` and two-zone/date-boundary tests. | W5-02 K3a | resolved |
| R24 | W5-04 V3a E5 withdrawn | `ev-work-incidents` | Site-local Window date/time | Fixed UTC/offset formatting was proposed | D3 | Stored EV Site timezone already exists. Reuse K3a `siteWindowText` and test both zones/date boundary. | W5-04 V3a | resolved |
| R37 | W2-03 retro correction | `cold-performance` | Loading / batch row | Row was omitted in first build | D3 | The mock row can be rendered faithfully; restore it in its original order. | W5-F1 F1-2: keep row, prove mock order and capture; re-review | built: W5-F1 42964500 |
| R38 | W2-03 retro correction | `cold-evidence-analysis` | Exact target record links | Links were offered before target integration proof | D3 | Keep link placement but show labelled references/unavailable state until exact target is proved. | W5-F1 F1-3: remove unproved anchor and capture; re-review | built: W5-F1 89b88a40 |

## D4 — illustrative mock placeholder

| ID | Wave/slice/unit | Screen (v69 id) | Mock element | What is shown instead | Category | One-line reason | Owning or resolving unit | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R25 | W5-01 C5 | `cold-scenarios` | Empty illustrative scenarios only | Persisted authored rows/basis and honest pending state | D4 | Real selected authored facts replace a static example without claiming observed outcome. | W5-01 C4/C5 | planned |
| R26 | W5-03 E2 | `availability` | Fixed percentages and 08:00/12:00/16:00 axis | Selected spans, derived percentages and window times | D4 | Mock numbers are examples, not accepted Site evidence. | W5-03 E1a/E2 | planned |
| R27 | W5-03 E6 | `ev-scenarios` | Illustrative scenario rows | Stored authored revisions and honest pending state | D4 | Mock values cannot stand in for selected authored facts. | W5-03 E5/E6 | planned |
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
