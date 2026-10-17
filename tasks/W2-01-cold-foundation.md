# W2-01 — Cold Foundation, readiness and configured topology

Status: active (activated 2026-10-17 from main `8e0af014`; W2-00 and W1-F1 merged); was implementation-ready (planned). Size S; two phases. Branch `task/W2-01-cold-foundation` from merged main. USER_REVIEW_REQUIRED: true through the owner's later W2 walkthrough, after independent slice review. W1-F1 must merge before phase 2 UI work/review. This slice makes a selected `COLDCHAIN` configuration visible; it makes no temperature, commissioning or equipment-health claim from configuration alone.

## Architect answers and dependent-packet impacts

`D-2026-10-17-w2-01-answers` in `.agent/W2-technical-design-cold.md` §3 closes build questions A–I. Phase 1 must implement its exact topology node roles/media and directed `topology.connections`, event unit/IDENTITY validation, thirteen carrier-typed properties and property-specific bounds, one `backup_start_event` channel plus `grid_power_event`, and role-specific state ENUM maps. The two room policy roles are Foundation controls, never channel bindings. The selected read returns `UNCONFIRMED`/empty commissioning IDs, maps gateway contact `CURRENT|STALE|UNKNOWN` by the §3 diagnostic rule, and returns the fixed `cold-roles-1` 300-second cadence for periodic channels, null for transition event channels. W2-02's frozen publication profile must match. The three existing Foundation routes switch by selected Site type. Add `cold-readiness:2` and `cold-sld:1` to `APPROVED_TITLE_CHANGES` with selected gateway/Site values and the stated fallback, before the panel-structure proof. Default labels are `Configured`/`Needs a source`, not `Mapped`/`Not mapped`.

W2-02 packet impact: its registered producer must emit both start kinds through the one `backup_start_event` binding and power events through `grid_power_event`; it must add all named profile/model/mapping/host/Stage v4 seams in the §3 closure and prove no unknown-profile fuel fallback. W2-03 packet impact: its cold worker must select typed event and measurement evidence, extend the shared assessment/Finding stores and `0022` transition/split constraints, and update rule 8 as specified in §3; it cannot reuse numeric dispatch selection or dispatch Finding constants. Neither packet is yet an executable task in `tasks/README.md`; these are binding handoff requirements when each is refined.

## Binding design and dependencies

- `.agent/W2-technical-design-cold.md:25-32` owns `0021_w2_cold_config`; `:49-68` owns `cold-roles-1`, topology, policy and readiness; `:107-111` owns selected Foundation read; `:120-131,160` owns exact panel destinations and honest gaps; `:191-194` owns acceptance cases. `.agent/architect-W2-design.md:59-64,73` sets sequence/layout gate; `.agent/architect-W1-fidelity.md:5-23` and `D-2026-10-17-mockup-layout-spec` set shared W1-F1 structure/capture rules. `D-2026-10-17-w2-design` and `D-2026-10-17-w2-techdesign-cold` remain authority. Use v69 named routes/manifest and `frontend/docs/architecture/v69-rendered-panels.json`.
- Requires merged S1 Foundation/binding and S7 source-health reads; phase 2 additionally requires merged W1-F1 shared guard/CSS. W2-00 is the source-event prerequisite for later producer W2-02, not a reason to invent W2-01 observations.

## Phase 1 — persisted configuration and selected read

Publish complete and missing-probe `COLDCHAIN` Sites through existing time-valid Foundation JSON, immutable binding revisions and registered gateway/source/device/signal records. `0021` is a no-op SQL revision after `0020`: add code-owned `TEMPERATURE_PROBE`, `COMPRESSOR`, `TRANSFER_SWITCH`, `degC` rating and the typed `cold-thermal-capacity`, `cold-heat-leak`, `cold-cooling-capacity`, `cold-door-heat`, `cold-control-low/high`, `cold-policy-low/high`, `cold-min-excursion`, `cold-return-hysteresis`, `cold-start-timeout`, `cold-probe-error` properties and units exactly as design line 32; no new table or backfill. Register immutable `cold-roles-1`: chamber temperature/probe, room policy band, compressor state/power, grid state, backup request/result, generator state, backup bus state, optional transfer/door/ambient/manual temperature, with cardinality, asset and unit rules from design lines 51-68. Validate topology edges, primary probe uniqueness, finite positive thermal values, ordered band, hysteresis/error/timeout and time-valid bindings. Reuse S1 revision/history; rollback `0021` changes no SQL data and old-role readers still work.

Serve authenticated `GET /api/sites/{code}/cold/foundation?at=<UTC>` for the selected effective revision, with exact rooms, policy/revision, topology, bindings, readiness, commissioning and contact fields from design line 111. Keep registration/read 401/403/404 and invalid selection refusal scoped to the requested tenant/Site. Gateway contact and commissioning are separately sourced; absent facts stay unknown.

Acceptance tests: complete and missing-probe fixtures persist and reload; selected old/current revisions change room policy, bindings and topology without rewriting history. Reject low>=high, wrong unit, duplicate probe-room link, cycles/duplicate edges, stale or overlapping binding and undeclared transfer; wrong tenant/Site cannot read or bind. Confirm missing probe says what to add, missing policy and start events name their gaps, and absent transfer/contact/commissioning remain unconfirmed. Upgrade `0020→0021`, verify the code-owned vocabulary/fixture check and old Site reads; downgrade the no-op revision without touching stored rows. Probe statement-level rule 8 for any new writer/fixture SQL and run focused backend/API tests.

## Phase 2 — three selected Site routes

Use the merged W1-F1 shared guard and CSS to render `cold-foundation`, `cold-readiness` and `cold-sld` from the selected read. Preserve every v69 main panel in exact order, title, prominence and grid: Foundation 2 panels, Readiness 4, SLD 2, mapped in design lines 124-131. Dynamic Site/gateway text replaces illustrative names. In-panel gaps cover undeclared equipment, unavailable per-source contact, unassessed confidence, absent part-function description and unknown live state. Keep exact IDs and lineage in contextual detail, with plain default copy and selected-time/source labels.

Acceptance tests: each route has a panel-structure test reading indexed expected titles from `v69-rendered-panels.json`, asserting count, DOM order, approved dynamic title, grid/prominence and in-panel gaps for stocked and meaningful empty/refused states. Capture served app and v69 mock side by side at 1440 and 390 for all three routes with matched Site, revision and state using W1-F1's shared guard; review top fold, panel widths/heights, density and mobile flow. A structure mismatch is High and blocks the owner walkthrough. Verify reload/old-current selection, missing-probe and no-contact states, accessible gaps, no mock values or evidence claim. Run focused frontend tests/typecheck, applicable guards and one full backend suite on final slice revision using a private `*_test` database per `backend/TESTING.md`, with JUnit zero failed/skipped. Independent review precedes the later owner W2 walkthrough.

## Registry

Existing open `A-cold-role-set`, `I-configuration-breadth-store` and `D-configuration-variants` point to this packet via `task`; broader `A-cold-site-projections` also covers W2-04 and remains unassigned. No node is marked resolved or promoted by planning. Proposed UI/fixture nodes wait for reviewed graph work and owner scope decision.

## Architect questions

None; the cited design specifies the contract and labels the missing reads.

## Plan review notes (coordinator, 2026-10-17)

- Phase 1 requires W2-00 merged (migration `0021` builds on `0020`); phase 2 requires W1-F1 merged (shared layout guard and CSS).
- Phase 2 acceptance also runs the plain-language vocabulary scan on the three routes (`.agent/architect-W2-design.md:73`) and records the capture-log fields the fidelity contract requires.
- The cold-readiness panel 2 and cold-sld panel 1 title changes in the cold design table (lines 127, 130) are Architect-approved under `D-2026-10-17-w2-techdesign-cold`; the reviewer treats them as approved title-map entries.
- `binding_roles.py` citations in the design have drifted: the role-set registries are now at lines 99 and 103.
