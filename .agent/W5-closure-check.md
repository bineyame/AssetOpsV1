# W5-01 / W5-03 readiness closure check

Checker: independent Claude reviewer (did not author the specs or the closure), 2026-10-22.
Tree: `C:\Users\assef\Bineyame\AssetOpsV1-plan2`, `main` at `5531abf5`. Read-only apart from this file. No DB created, no commit.
Inputs: `.agent/W5-readiness-review.md` (46 items), the "Readiness closure" tables and updated cards in `.agent/W5-01-build-spec.md` (S1) and `.agent/W5-03-build-spec.md` (S3).

## Verdicts

| Spec | Verdict | Open items |
| --- | --- | --- |
| W5-01 cold depth | **NOT READY** | 7 (R1-R7) |
| W5-03 EV depth | **NOT READY** | 6 (V1-V6) |

Of the 46 review items, 41 are closed by a literal artifact consistent with merged code. Review items 4 and 31 (registry rows) are not closed: the literal rows fail the registry guard. Review items 14 and 40 (Health composition) are closed on paper but the chosen composition creates a new open item. Review items 16-18 and 42 are literal, but the contract they fix has two defects (R3/R4, V3/V4). The new items below came out of the closure, not the original review.

## Checks run

| Check | Result |
| --- | --- |
| `tools/check-all.ps1`, with plan2 `.venv\Scripts` first on PATH | **11/11 guards PASS, exit 0.** The estate self-test passed (3 tests, 116.78 s). Screen ledger: 110 screens, 258 panels valid. This confirms the "guards pass" statements at S1:13 and S3:13. |
| Worst-content mock measurement: scratch copy of `tools/measure-mock-panels.mjs` (`--no-sandbox`, own port), plus DOM injection of a 166-character sentence with a 36-character UUID into the first metric note, first panel prose and first notice | Ran for the 7 screens at 1440x1000 and 390x900. **Every cap holds** (table below). Document scroll width equals client width on all 14 pairs (1425/1425, 390/390). Every Chrome process I started has exited (0 left with my profile marker). |
| Real-literal card injection at 390 (the card values and notes from the specs) | Cooling 308 (cap 360), cold Health 385 (cap 430), EV Health with a 45-character connector label 323 (cap 380), Availability 264 (cap 350), Energy 292 (cap 340). All hold. |
| Registry simulation: scratch copy of `frontend/docs/architecture` and `tasks`, the spec's literal nodes and panel rows applied, `check_v69_dependency_registry.cjs` run | Fails; see R1/V1. Fixed step by step it passes only with five additions the specs do not state. |
| Code spot-checks | See "Verified against merged code" below. |

### Worst-content measurements (px, 1440 / 390; mock content, injected)

| Screen | Measured worst | Spec cap | Holds |
| --- | --- | --- | --- |
| cooling | status 45/99, cards 161/344, panels 386/398, notice 42/78, next 234/268, page 1360/2223 | status 85/140, cards 180/360, panel 470/500, notice 90/150, next 300/360, page 1600/2350 | yes |
| cold-health | cards 166/393, condition 198/269, page 1001/1323 | cards 200/430, condition 330/430, page 1200/1550 | yes |
| cold-scenarios | panel 316/392, notice 42/78, page 1001/1162 | panel 430/560, notice 90/135, page 1250/1500 | yes |
| availability | status 44/71, cards 161/344, state 245/293, bounds 180/176, next 180/180, page 1103/1794 | status 90/125, cards 180/350, state 340/390, bounds and next 260/280, page 1300/1950 | yes (390 cards have 6 px headroom) |
| energy | status 44/113, cards 161/328, panels 374/308, bridge 243/401, page 1296/2167 | status 90/155, cards 180/340, panels 440/430, bridge 350/520, page 1500/2320 | yes |
| ev-health | cards 166/380, panel 198/286, page 1001/1307 | cards 200/380, panel 330/440, page 1200/1550 | yes (390 cards sit exactly at the cap, zero headroom) |
| ev-scenarios | panel 316/392, notice 42/78, page 1001/1162 | panel 430/560, notice 90/135, page 1250/1500 | yes |

My card, status and bridge numbers match the specs' recorded worst values for all four 390 card results (344, 393, 380, 328). My page heights differ by up to 36 px from the specs' (for example availability 390: 1794 against 1816), because I placed the prose injection differently. No cap is affected. The cap tables hold, but the app's real tables and refusal overlays are not covered by a mock measurement. That is already the specs' stated position.

### Verified against merged code

- Cold clock (review item 1): the cold cutoff is `known_at or max(ingestion_disposition.decided_at)` (`postgres_assessment_store.py:2000-2002`). The w202 chain uses a wall-clock decision clock (`test_w202_cold_replay_postgres.py:222`) and the ledger without an override uses `clock_timestamp()` (`postgres_evidence_ledger.py:525-528`). The window `[19:00,20:05)` and the `before["window"]["known_at"]` pattern match `test_w204_cold_reads.py:44, 390`. The cold producers (`opened("backup-failed", chain)` at `test_w203_cold_reads_postgres.py:123`, `late-reading`, `missing-probe`) exist.
- EV clock (item 28): `FIRST_DECISION` 09:00 and `LATE_DECISION` 09:05, set through `test_decision_clock_override=self.decision_clock` (`test_w205b_ev_replay_postgres.py:111-112, 235-238, 334`). The scenario window is `08:00-09:00` (`config/scenarios/ev-fault.yaml:5-8`). Saved first watermark `09:00:00.000000Z` is asserted at line 968.
- Alembic head is `0030_w4_mini_decisions`; no 0031 or later file exists. `0032` with down `0030`, `0034` with down `0033_w5_cold_work` are consistent, and the 0033 obligation is recorded in `tasks/W5-03-ev-depth.md:12-14` and `post-W2-sequence.md:18`.
- Scenario store columns and constraint names track `0030_w4_mini_decisions.py:49-90` (public-number sequence, create key and hash, revision chain check, the four unique constraints, the order index).
- File lists: `ColdAssessmentViews.tsx:782` holds the `Cooling` unavailable tab; `EvAssessmentViews.tsx:572-573` hold `Availability` and `Energy / site power`; `EvSiteViews.tsx:380` holds the EV `Scenarios` tab; `SiteAnalyticsFrames.tsx:993` holds the shared `Scenarios` literal (`:1180-1188` the cold-only refusal branch); `navigation-truthfulness.ps1:752-753` holds `$expectedTabs` (`Scenarios, Scenarios, Cooling, ..., Availability, Energy / site power, Analysis`). `ev_gate` (`ev_assessment_api.py:85`) is already importable, so E1b needs no extraction. `cold_site_api.opened` is a nested closure (`:65`), so the C1 extraction is real and owned.
- Existing literals: `cold_reads.HISTORICAL_NOTE`, `NO_SELECTION_NOTE`, `ev_reads.HISTORICAL_NOTE`, `NO_SELECTION_NOTE` match the specs; the two new pending strings are labelled new. `energy_complete(state, supported_kwh, unknown_meter_seconds)` matches E5. `ev-status-cadence` is a required connector property (ceiling 1 minute) and is set in `tests/fixtures/w2/ev-lab-001.yaml`. A `weekly: []` schedule is valid (`ev_foundation.py:288-297`). `cold-roles-1` has `grid_power_event` and `door_event` (`binding_roles.py:177-186`). The EV connector state vocabulary is `UNPLUGGED, PLUGGED, AUTHORIZING, CHARGING, FAULTED` (`profiles.py:2078`), so `AVAILABLE` and `DISABLED` in the E1a mapping can only arise from fixtures; this is harmless.

## Item-by-item closure

Closed unless marked.

| Item | Status | Note |
| --- | --- | --- |
| 1 | closed | Clock restated; matches the merged chain. |
| 2 | closed | API links by `site_code`, keys `temperature, backup, evidence, health`. |
| 3 | closed | C1 owns the `opened` extraction and names the router test; C2 owns `ColdAssessmentViews.tsx`. Residual: client ownership, see R7. |
| 4 | **open** | See R1. |
| 5 | closed with caveat | Context table is literal, but see R5. |
| 6 | closed | Derivation table is literal and consistent with the cold producers. The source key is named `cooling_recovery.state`; in code it is the `cooling` field built from the `COOLING_RESPONSE` capability (`cold_site_reads.py:323, 363`). Builder can resolve it; note only. |
| 7 | closed | `envelope_on(...)["source_provenance"]` exists. |
| 8, 9, 10, 11, 12 | closed | State matrix, breadcrumb rule, live 403 capture and real-literal 390 cap (308 measured) all present. |
| 13 | closed with caveat | See R6. |
| 14 | closed on paper | Composition is stated, but see R2. |
| 15 | closed | Deviations are named. |
| 16 | closed | Literal schema. See R4 for a gap in the window model. |
| 17 | closed with defect | See R3. |
| 18 | closed | List DTO carries `selection.state`; the HISTORICAL predicate is literal. See R4. |
| 19, 20, 21, 22, 23, 24 | closed | |
| 25, 26, 27 | closed | Guards confirmed 11/11. |
| 28 | closed | |
| 29, 30 | closed | File lists and routes match code. The Sessions link replaces the dead Session-detail link. Residual: client ownership, see V6. |
| 31 | **open** | See V1. |
| 32, 33, 34, 35, 36, 38, 39, 41, 43, 44, 45, 46 | closed | The hold rule is cadence-bounded and literal, battery is always Unknown, E1a/E1b split is real, STALE is test-only. |
| 37 | closed with caveat | Producers are new persisted fixtures. Whether `EvReplayBuilder` can inject accepted status rows or a swapped Foundation is not shown; residual risk, not an open item. See V5 for the schedule literal. |
| 40 | closed on paper | See V2. |
| 42 | closed with defects | See V3 and V4. |

## Open items: W5-01

**R1. Registry rows are not literal enough to pass the registry guard (review item 4 not closed).** S1:69-78, 108.
The spec gives `kind`, `area`, `status`, `task` for the four new nodes and `area`, `requires`, `status`, `reason` for the five panel rows. I applied them to a scratch copy and ran `check_v69_dependency_registry.cjs`; it fails in sequence on five facts the spec does not state:
1. `I-W5-cold-depth-read: requires must be an array` (nodes need `requires`).
2. `implementation has no architecture prerequisite` (`check_v69_dependency_registry.cjs:151-154`): each node must reach an `A-` architecture node; the spec names none (for example `A-cold-site-projections`).
3. `missing UI or projection gate` (`:343`): nodes need `layer` values, `projection` for the read and `ui` for the UI (also `effort`, `owner`, `acceptance_target`).
4. `claim panel lacks data gate` (`:344`): every panel row needs a `kind:data` node in `requires` (for example `D-cold-domain`) or `structural:true`. The rows as written have none, so they fail.
5. `cooling: ledger and registry node IDs diverge` (`:320-326`): `frontend/docs/architecture/v69-screen-ledger.json` needs `registry_dependencies.{product_node_id,node_ids}` for `cooling`, `cold-health` and `cold-scenarios`. That file is in no unit's file list (precedent: the W3-03 and W6-01 closures edited it).
With those five additions the guard passes. Why it matters: C3 and C5 as written leave the builder deciding fields and a file, and a red check-all. Fix: give the full node objects and the data-node ids, add `v69-screen-ledger.json` to C3 and C5 (and name the ledger fields), and state who creates each node (see R7).

**R2. Health composition drops the S7 gateway panel and orphans a live link.** S1:67.
C3 omits `Data sources · data quality, not equipment condition` from the COLDCHAIN Health route and says gateway contact "remains reachable from Evidence". The panel is the only place that renders the S7 gateway read (`SiteHealth.tsx:313-326`, `client.getSourceHealth`). The cold Evidence `Data sources` panel (`coldSiteViews.tsx:865`) is evidence-source analysis, not S7 gateway contact. The cold Foundation gateway panel links to it with a live `Health › Data sources →` (`ColdFoundationViews.tsx:646`). The spec names neither this link, nor the existing tests that assert the panel (`siteHealthBoundary.test.tsx`, `coldSiteViews.test.tsx`), nor an S7 acceptance that must be amended. Fix: either keep the gateway panel below `Condition and evidence` and re-measure the page cap, or rule the removal explicitly and name the link, the tests and the S7 criterion to change.

**R3. Attestation refusal status contradicts merged code.** S1:90, 96.
The spec says malformed attestation is 403 `DECISION_ATTESTATION_INVALID` while reusing `mini_decisions.scenarios.authorize`. Merged `model.py:34` maps `DECISION_ATTESTATION_INVALID` to 422 (and the `scenarios.py` docstring says 422). A test written to the spec fails against the reused code. Fix: state 422 in the C4 text and refusal table, or state that C4 overrides the status.

**R4. The scenario window is not an immutable root property.** S1:84-88, 102.
The root table has no window columns, but the list rule keeps "roots whose stored `[from,to)` equals the requested period". The window lives only in each revision's `authored_basis` JSON. A correction POST takes its own `from,to` query, and nothing says a correction must repeat the root's window or is refused otherwise. A correction on another window would put one root in two lists. Fix: state that a correction's resolved `from,to` must equal revision 1's, refused as `COLD_SCENARIO_INVALID` otherwise, and that the list filters on revision 1's `authored_basis` window (or add window columns to the root with a check).

**R5. Context row sources: door pair path unnamed, ambient rationale false.** S1:53, 74.
(a) `Door-open duration` is Observed "only from a matched accepted door_event OPEN/CLOSE pair with positive elapsed time". The selected excursion result stores only door evidence IDs as `CONTEXT` links (`cold.py:517`); the event kind and time need an accepted-evidence read, which the spec does not name, and C1 owns no file that exposes one. (b) The ambient row says "no ambient binding role"; `cold-roles-1` defines optional `ambient_temperature` (`binding_roles.py:188`), and the registry reason says "Ambient, loading and defrost roles are absent". The literal outcome (always Unknown) is acceptable, but the stated reason is false and would be copied into the registry. Fix: name the read used for door pair classification (or the store method C1 may add), and reword the ambient reason ("not selected by the W2 assessment").

**R6. Health `LIMITED` is not in the payload enum.** S1:19, 67.
The payload `condition_state` is `NEEDS_INVESTIGATION`, `UNKNOWN`, `NOT_CONFIGURED`, but the C3 matrix keys Temperature sensing on `LIMITED` ("accepted one probe"). Two probes are not covered either. Fix: add `LIMITED` to the enum, or give a separate coverage field, and state the two-probe case.

**R7. Ownership and node creation inconsistencies.** S1:59, 65, 69, 108.
C2 creates `ColdDepthClient.ts` but only the cooling read is described; C3 needs the health fetch and DTO validator, owns only new files, and cannot edit that client. C3 lists the two `I-W5-cold-scenario-*` nodes among the nodes it creates (S1:69) and C5 says "Add `I-W5-cold-scenario-read` and `-ui` nodes" (S1:108), which would be a duplicate-node failure (`Duplicate node` in the checker). Fix: give C2's client both reads (or let C3 own the edit) and make one unit own each node.

Notes (do not block): the empty-window cooling capture names the missing-probe producer but not the empty window (`EMPTY` is `2026-10-05`, `test_w204_cold_reads.py:43`); the `from`/`to` pair is optional in the merged gate (neither given is allowed) while C4's POST requires both, so the extracted gate needs a flag.

## Open items: W5-03

**V1. Registry rows are not literal enough to pass the registry guard (review item 31 not closed).** S3:83-98, 141.
Same defects as R1 for `I-W5-ev-depth-read/-ui`, `I-W5-ev-health-ui`, `I-W5-ev-scenario-*` and the nine panel rows (`availability` 1-3, `energy` 1-3, `ev-health` 1, `ev-scenarios` 1; the contract panel counts 3, 3, 1, 1 match): no `requires`, `layer`, `effort`, `owner`, architecture ancestor (for example `A-ev-site-projections`) or data gate, and no ledger edit. `v69-screen-ledger.json` is in no unit's list (E3, E4, E6). Fix as R1.

**V2. EV Health also drops the S7 gateway panel.** S3:96-98.
E4 removes `Data sources · data quality, not equipment condition` from EV Health and says gateway contact "remains on existing Evidence routes". The EV Evidence panel (`EvSiteViews.tsx:879`) is evidence-source analysis, not the S7 gateway read. The EV Foundation has an inert `Health › Data sources` entry (`EvFoundationViews.tsx:631, 688`) that is consistent today and becomes a promise to a page without the panel. Existing tests that assert the shared Health panels are not named. Fix as R2.

**V3. Attestation refusal status contradicts merged code.** S3:121, 127.
Same as R3 (`model.py:34` is 422; the spec says 403).

**V4. The scenario window is not an immutable root property.** S3:106-108, 133.
Same as R4: the `ev_scenario` root has no window; correction POST takes its own `from,to`; the list filter reads a "stored `[from,to)`" that exists only in revision JSON.

**V5. Schedule-absent versus declared-empty-schedule is inconsistent and has no literal.** S3:19, 31-32, 56.
The calculation says no unambiguous time-valid schedule gives `scheduled_seconds=null` and all rates null. E1a's no-schedule fixture uses `weekly: []` and asserts `scheduled_seconds=0`. E2's literal `Service schedule not established for this window.` is tied to "schedule absent". Which of null or 0 a declared empty schedule produces, and what the page says for 0, is not decided. Fix: rule `weekly: []` as 0 with a literal (for example `No service hours are declared in this window.`) or as null, and align the E1a assertion and the E2 capture.

**V6. Client ownership.** S3:66, 70, 96.
E2 creates `evDepthClient.ts` for availability; E3 (energy) and E4 (health) need their reads and DTO validators in the same client and own only new files. Fix: E2 (or E1b's wire section) fixes the client to cover all three, or E3/E4 may edit it.

Notes (do not block): the E1a persisted fixtures assume `EvReplayBuilder` can inject accepted `ev_connector_state` rows and swap in a `weekly: []` Foundation; neither mechanism is shown to exist, so E1a may grow past one run. The `ev-health` 390 card cap is met with zero headroom (380 against 380 on the injected mock); a real two-line connector label would need a rule.

## Cross-spec consistency

Consistent: route shapes (`/cold|ev/financials/scenarios`), DTO and code naming, pending/refusal wording, the 36/166-character test rules, the `0032`/`0033`/`0034`/`0035` chain, the shared column set and constraint names, and the clock statements. Inconsistent: the S7 panel decision is the same in both and carries the same defect (R2/V2); the registry gap and the two scenario-contract defects are shared (R1/V1, R3/V3, R4/V4). Navigation multiset: C5 says two `Scenarios` remain, which holds only if it merges before E6 (queue order W5-01 then W5-03 satisfies this).

No unit exceeds the size cap on the stated cards; C4 and E5 are the largest and are literal. No file listed in a unit is missing from the tree (new files aside); the unowned file is `v69-screen-ledger.json`.
