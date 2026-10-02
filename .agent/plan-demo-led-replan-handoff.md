# Handoff: demo-led replan (Planner, 2026-10-02)

**Status: complete.** The remaining work below was finished in `db4203f` by three fresh Planner agents working from this file; the packet is `.agent/plan-demo-led-replan-review-packet.md`. Kept as the record of the mid-run handoff.

Planner: Claude under the Codex-reset exception in `.ai/ROLE_CONFIG.md`.
Branch `plan/demo-led-replan` (cut from `arch/demo-led-recommendation` at
`446906e`). Brief: `.agent/planner-guide-demo-led-replan-2026-10-02.md` (the
"guide"); its source is `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` at `57ea23e`
(the "recommendation"). Do not push or merge. No code, no `Docs/`, no owner
files, no recommendation edits, no `tools/`/`frontend/`/`backend/` edits.

## Done

- `2e33f94` step 0 (guide section 3): `.ai/DECISIONS.md` gains
  `D-2026-10-02-demo-led-recommendation`,
  `D-2026-10-02-rendered-tabs-per-capability` (amends
  `D-2026-09-13-canonical-fidelity` and
  `D-2026-09-17-foundation-screen-architecture`, pointers added to both index
  rows and entry bodies), `D-2026-10-02-grammar-ownership-test`,
  `D-2026-10-02-presentation-profile-and-capability-declaration`,
  `D-2026-10-02-demo-point-seed-rule`; `.ai/ARCHITECTURE.md` Presentation
  Honesty and Shared Presentation Substrate notes; `.ai/PRODUCT.md`,
  `.ai/PLANNING_GUIDANCE.md`, `.ai/START_HERE.md`, `.ai/ACTIVE_CONTEXT.md`
  routed to T027 phase 1. `.ai/FEATURE_MAP.md` unchanged: its unowned table's
  owner cells name map letters (C, D, I...), not task ids, so none moves.
- `7842aa3` queue (guide section 4): `tasks/README.md` rows 19-32 and demo
  points replaced; T025h task file brought in from `f4274f2` (file only) and
  parked. New ids chosen: **T029B** (thin follow-on, file
  `tasks/T029B-sites-ranking-and-landing.md`) and **T034A** (Portfolio-lite,
  file `tasks/T034A-portfolio-lite.md`); README already links those paths.

## Check outcomes (guide section 6), already decided; apply, do not redo

- **6.1 T030 -> T031: no content coupling.** T031 (`Depends on: T027-T030 and
  A's curtailment/dispatch model.`, L112; `Delivery order: after T030; next
  T032 completes F.`, L113) consumes only: T026/T027 evidence/envelope path
  (AC2, AC3), A's physics (AC1, AC3), T028's Finding/evidence/claim structure
  (AC7), T027 Site Overview (AC7), T029 price context only via the
  price-invariance proof, the Lab cockpit PV/load curves. T031 AC9 ("Repeated
  analysis is deterministic/versioned and avoids duplicate Findings.") needs no
  revision history. T030 AC13 and AC2 are not consumed. T032 header (L7-8)
  depends on T031, T027, T029, T029A only. T033/T035 name no T030 artifact
  (T035:74 is a regression guard only). **Order: T031, T032, T030, T035, T033.**
  Two-slice cost: T031 and T032 both run ahead of T030.
  - **T028 AC13 falls short** (T028:80-82: "Rerunning on the same accepted
    evidence/model version yields the same assessment without duplicate
    active Findings. Changed accepted evidence creates an inspectable
    assessment revision."). It never says prior assessments are persisted
    and kept. So put **persisted, inspectable revision history** explicitly
    into T028 phase 1 (prior assessment retained and inspectable after a
    revision), which removes any later dependency on T030 AC9 ("A delayed
    delivery record can revise the assessed window after acceptance; original
    evidence and assessment history remain available."). Do not reorder.
  - Stale line: T031 Scope limits L173 "No immutable interventions or paired
    runs yet; T032 owns them together" - T029A now owns the mechanism; fix.
- **6.2 evidence-limited site: suitable.**
  `config/scenarios/kobo-mini-grid-degraded-evidence.yaml` drops battery
  discharge-capability readings 09:00-10:00 (L367-379, no substitution), delays
  the 10:00 SOC publication to 10:10 (L383-395), and loses the 08:00 operator
  override record (L354-365; override real, `issued_by: OPERATOR`). All inside
  the generator run (STARTING offset 40, STOPPED 250). Maps to T028 AC3
  ("Missing battery capability cannot be replaced from simulator truth"), AC5
  (Indeterminate names missing evidence), AC7 (override "none observed"),
  Proof rows L94/L98. T028's analytic gives a segmented/limited claim, not
  nothing. Caveat: no "capability lost throughout" case; not needed for
  Portfolio-lite. T034A uses this scenario through normal ingestion.
- **6.3 Portfolio-lite sizing:** still to do (draft T034A, test against
  ceilings 120/160/220 and cold-start in `.ai/WORKFLOW.md` Task Spec Size; if
  it does not fit, split into seed recipes then Portfolio page, both directly
  after T034, point 3 completing at the second; if fitting needs dropping a
  site or a lens, STOP and write an owner question).
- **6.4 facts:** rechecked; guide matches files except T028 AC13 (above). T027
  AC10 (L72-74): "Preserve missingness and quality during normalization.
  Coverage names the required signals and selected window; no sample
  carry-forward becomes an undocumented fresh measurement." No other T027
  sentence ties "required signals" to analytics (Deliver L43-44 lists Overview
  metrics; Proof L112 "| Missing capability/report | Coverage gap, no
  fabricated value |" is compatible). T027 AC11 (L75-77), AC18 (L91-94), Scope
  limit L135 "No full Replay UI or broad source-health dashboard is required
  for C." T036 AC1 L44-46, AC4-AC7 L51-59, AC13 L71-73 (still walks roadmap
  13.3 order). T034 Delivery order L8-10 "after T029A; next T030. ...".
- **"Labelled in place" (guide 3.2 [Verify]):** no non-operator surface renders
  it; non-operator mentions are comments only (`simulatorLabRoutes.tsx:422`,
  `ui/DataTable.tsx:26`). Operator anchors: `operatorSiteTabs.tsx` L29, 66,
  76, 83-88, 126/130 `labelledAspectsSentence`, 178, 199;
  `FoundationSubtabs.tsx` L15, 27, 57, 77 (Readiness `labelled_in_place`);
  tests `operatorSiteTabs.test.tsx`, `foundationScreen.test.tsx:35`,
  `ui/__tests__/overflowContainment.test.tsx:239`;
  `tools/checks/navigation-truthfulness.ps1` L220, 316, 333.

## Remaining (commit group 3, then group 4)

Per guide section 5, one file each, following its general rules (header form,
section order, ceilings, cite decisions, rendered rail + Site tabs stated for
nav-changing slices, `node tools/layout-evidence.mjs`, UI check per phase,
"Planner: Claude under the Codex-reset exception" line in the header):

- T027 (phases 1 and 2, every AC assigned to a phase, AC10/AC11 rewording,
  scope-limit wording, AC18 landing stated, Sites columns + landing moved to
  T029B, code anchors above);
- T028 (three phases, ACs 1-15 kept and assigned, capability declaration ACs
  and three rules with expected-orphan list, persisted revision history in
  phase 1, Sites Assessment/Top issue moved to T029B);
- T029 (Financials destination, editable assumptions, site-scoped
  BusinessContext + revisit trigger, point-2 seed AC);
- T029B new (thin follow-on, 120-line ceiling);
- T029A (Delivery order only);
- T034 (guide's list, point-3 seed AC, Delivery order -> next T034A);
- T034A new (Portfolio-lite; check 6.3);
- T031, T032, T030, T035, T033 (positions, Depends on, own-site seed, joins
  capability declaration, per-slice notes in guide 5);
- T036 (rescope per guide 5).
Then the review packet `.agent/plan-demo-led-replan-review-packet.md` (guide
section 8) and commit it with `git add -f`.

Architect readings to list in the packet (guide section 6 of section 8): the
roadmap is not edited (queue's demo story lives in README/PRODUCT); profile
rules apply to backend capability ids, not Overview domain cards; breadth
slices seed their own sites; breadth pair order (opportunity/fuel before
service/battery) is a default; the step 0 "update the roadmap's demo story"
read as the queue's demo story. Planner readings added: FEATURE_MAP left
unchanged (letters, not tasks); T029B/T034A ids.
