# Recreated implementation queue

Recreated from main a7417dd and D-2026-09-24-v4-roadmap-replan.
All tasks are planned; this file does not activate implementation.
Direction: [feature map](../.ai/FEATURE_MAP.md),
[starter handoff](../.ai/PLANNING_HANDOFF_T020A_T023.md),
[Lab cockpit handoff](../.ai/PLANNING_HANDOFF_LAB_COCKPIT.md),
[v4](../Docs/simulator_design_v4.md), and
[demo roadmap](../Docs/mini-grid-demo-architecture-and-roadmap.md).
The six existing starter files are replacements, not amendments.

## Order and observable checkpoints

Replanned on 2026-10-02 under `D-2026-10-02-demo-led-recommendation`: the
owner-approved `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` (section 7) sets the
order from T027 onward and supersedes the 2026-09-24 order for those rows.
T027 and T028 are phased; T029B (thin follow-on, Sites ranking; landing from T027)
and T034A (Portfolio-lite) are new; T025h is parked; the breadth order (rows
26-30) was set by the Planner's T030 -> T031 dependency check
(recommendation 6.3), which found no content coupling.

Resequenced on 2026-09-24 from `Docs/queue-review-feedback-verbatim.md`, then
adjusted again from its round-two section. See
`D-2026-09-24-queue-resequenced-for-demo` for what moved and why.
T022B precedes T024 under `D-2026-09-29-run-store-libyaml` and owns
T022A's outstanding inventory-cost criterion 2.
T025 is split into T025a then T025b under
`D-2026-09-29-t025-generator-policy-package`; T025b is A's acceptance checkpoint.
The owner accepted `D-2026-09-30-lab-cockpit-cadence`,
`D-2026-09-30-lab-cockpit-history` and
`D-2026-09-30-lab-cockpit-presentation` on 2026-09-30. T025c (L1a) then
T025d (L1b) and T025e (organisation and playback smoothness, added after the
owner's T025d hands-on check) run sequentially before T026; A remains accepted.
Under `D-2026-10-01-run-binds-scenario-to-site` (owner accepted 2026-10-01),
the scenario-site contract slices S0-S2 are T025f (template versioning) and
T025g (the run is the only join) before T026, T025h (picker compatibility)
after T026 (parked on 2026-10-02), and T025i (purpose assumptions) after T026 and before T036. T025h
gates nothing and may float later; T025i may move earlier if the owner wants
its label in the C/D demo. The T025 letters say where the slices were cut, not
when they run, as with T022B.

| Order | Task | Map | Reviewable result |
| --- | --- | --- | --- |
| 1 | T020A | A | Typed component properties in Foundation and frozen Draft |
| 2 | T020A1 | A | Two same-type components resolve independently |
| 3 | T020B | A | Shipped Fuel Loss setup reaches READY |
| 4 | T021 | A | Independent causal fuel trajectory; unlocks T022 |
| 5 | T021A | A | Observation declarations lose execution requirement |
| 6 | T022 | A | Start/step a Draft; inspect truth versus generated reading |
| 7 | T022A | A hardening | A run read that does not cost the whole store |
| 8 | T023 | B preparation | Inspect persisted canonical staged envelopes |
| 9 | T022B | A hardening | Responsive Runs inventory and Draft setup with libyaml |
| 10 | T024 | A | Daytime PV/storage serves three addressed loads |
| 11 | [T025a](T025a-healthy-generator-runtime.md) | A | Healthy full-site generator physics and contract-9 reproduction |
| 12 | T025b | A completion | Policy recipes, reported status and owner acceptance of A |
| 13 | [T025c](completed/T025c-persisted-lab-history-and-charts.md) | Lab cockpit L1a | Reloadable addressed history, charts and run identity |
| 14 | [T025d](completed/T025d-lab-cockpit-inspection-and-playback.md) | Lab cockpit L1b | Run-bound SLD, causal inspection and guarded playback |
| 15 | [T025e](completed/T025e-cockpit-organisation-and-live-playback.md) | Lab cockpit L1c | Organised cockpit layout and smooth playback |
| 16 | [T025f](completed/T025f-template-versioning.md) | A/B hardening | Template v2 and site lineage staleness note |
| 17 | [T025g](completed/T025g-run-binds-scenario-to-site.md) | A/B hardening | User picks the site; shipped scenario READY or BLOCKED by contract |
| 18 | [T026](completed/T026-dispatch-capable-evidence.md) | B | Dispatch evidence with one gap and one delayed publication |
| 19 | [T027](completed/T027-commit-ingestion-and-site-overview.md) (phase 1, phase 2) | B completion | Phase 1: Commit -> ingestion -> Site > Evidence with record drill-down; three real Site tabs. Phase 2: mini-grid Site Overview |
| 20 | [T028](completed/T028-dispatch-finding-and-evidence.md) (phased, done 2026-10-04) | C | Dispatch -> Finding -> drawer; Findings root; capability declaration; Evidence capability table (one row) |
| 21 | [T029](T029-bounded-dispatch-financials.md) | D | Site Financials with live editable assumptions; point-2 seed |
| 22 | [T029B](T029B-sites-ranking-and-landing.md) | B/C presentation | Sites ranks by assessment and evidence (landing inherited from T027) |
| 23 | [T029A](T029A-immutable-intervention-artifacts.md) | H prerequisite | Frozen policy intervention changes a run |
| 24 | [T034](T034-policy-action-and-verification.md) | H | Recommendation -> Action -> Foundation > Changes -> Verification; point-3 seed |
| 25 | [T034A](T034A-portfolio-lite.md) | Strong product demo | Portfolio lands, three seeded sites, ranked Findings |
| 26 | [T031](T031-renewable-headroom-opportunity.md) | F | Desta: evidence-backed recurring headroom opportunity; appears on Portfolio |
| 27 | [T032](T032-paired-load-addition-comparison.md) | F completion | Paired load addition with isolated comparison history |
| 28 | [T030](T030-fuel-records-and-reconciliation.md) | E | Genda: fuel balance with separate delivery/dip records; appears on Portfolio |
| 29 | [T035](T035-start-failure-and-service-assessment.md) | I prerequisite | Bahir: start failure and bounded service assessment; appears on Portfolio |
| 30 | [T033](T033-battery-stress-and-replacement-exposure.md) | G | Arsi: battery stress trajectory and replacement exposure; appears on Portfolio |
| 31 | T025i | Scenario contract | Unchanged: after T026, before T036 (awaiting planning) |
| 32 | [T036](T036-portfolio-and-client-demo.md) (rescoped) | I completion | Six sites, conditional global Evidence, Lab reveal, rehearsal |
| - | T026A | B hardening | Unchanged: unscheduled, gates nothing |
| - | [T025h](T025h-picker-compatibility.md) | A/B hardening | **Parked, in the backlog** (`.ai/MILESTONE_REVIEW_BACKLOG.md`): not before T029; gates nothing |

Task dependency declarations identify the required artifacts.
The order above is the intended delivery order; a user checkpoint may redirect
later tasks. T021A stays after T021 and is not a kernel prerequisite.
T023 is preparatory B work; A completes before B's internal demo.
L3's C7 enrichment, C8 health/log breadth and C9 setup/authoring are
feedback-selected after their prerequisites, normally after T036. No L3 task
or demo gate is allocated now.

**Rows 29 and 30 are an interchangeable pair.** T033 and T035 consume nothing
from each other; both depend only on T027's evidence, T029's assumptions and
T034's rule set. The default is the owner's priority intent, "Service before
battery unless feedback says otherwise" (recommendation 6.3), and whichever
runs second is unaffected.

**Breadth order is priority intent, not strategy.** The spine (rows 19-25)
is load-bearing. Rows 26-30 follow the owner's priority intent after the 6.3
dependency check: opportunity (T031, T032) before fuel (T030), at a cost of
two slices ahead of fuel. Keeping the opportunity/fuel pair before the
service/battery pair is the existing group order kept as a default, not a
decision. Point-2 feedback may redirect any of rows 26-30. Each breadth
slice adds its own seeded site to the Portfolio as it lands
(`D-2026-10-02-demo-point-seed-rule`).

**Delta p95 performance task (carried, no task file).** The server delta p95
miss carried from T025e/T026 (`.ai/MILESTONE_REVIEW_BACKLOG.md`, "Carried
from T026") runs before the T036 rehearsal only if playback visibly
stutters (recommendation 6.5).

**T026A has no position and is a prerequisite of nothing**, including T036.
Run it before or after the portfolio demo as feedback and time decide. It is
listed here so its ownership of the deferred gateway behavior stays visible,
not to schedule it.

## Four demo points, not one

Commercial and feedback exposure happens in stages. Treating the portfolio as
the first credible client milestone is the mistake this queue now avoids.

| Point | Task | What it is |
| --- | --- | --- |
| 1 | T027 | Internal architecture demo (live run; no seed) |
| 2 | T028 / T029 | Domain-expert and early-prospect demo: one site, one strong Finding, its evidence, its money; seed owned by T029 |
| 3 | T034 + T034A Portfolio-lite | Strong product demo, opening on Portfolio; seeds owned by T034 (post-action window) and T034A (three sites) |
| 4 | T036 | Full portfolio and polished client demo; seed owned by T036 |

Journey per point (recommendation 5.2):

1. Lab run -> stage -> Commit -> Sites -> Kobo Overview -> Evidence (source
   health, coverage, record drill-down) -> Lab off, history stays.
2. Sites -> Kobo Overview -> Dispatch -> Finding -> drawer -> Financials
   (change price).
3. Portfolio (three sites) -> Kobo -> Finding -> money -> Action ->
   Verification -> Lab proof.
4. The full recommendation 5.1 journey: Kobo runs uninterrupted from detect to
   verify, breadth after, Lab last.

Every point from 2 onward ships an idempotent, rehearsed seed checked with the Lab gate off
(`D-2026-10-02-demo-point-seed-rule`).

Seek domain-expert feedback at point 2, before the portfolio exists. A former
mini-grid operator does not need six sites to tell you whether the Finding is
useful. **After T028/T029, reassess T030-T036 against what the expert actually
said rather than treating the remaining order as immutable.**
A task does not authorize contacting anyone automatically.

## Shared implementation and review requirements

Each task inherits these checks and the exclusions below.
Use the role bindings and planned lane in .ai/ROLE_CONFIG.md and .ai/WORKFLOW.md.
Use one task branch, preserve unrelated changes, and leave an independent
Reviewer a packet mapping acceptance criteria to evidence.
USER_REVIEW_REQUIRED marks review of the delivered result, not permission to
begin ordinary implementation. Record the actual review before closeout.

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/check-agent-workflow.ps1
powershell -ExecutionPolicy Bypass -File tools/check-architecture.ps1
```

For changed backend behavior, from backend/:

```powershell
..\.venv\Scripts\python.exe -m pytest
```

For changed frontend behavior, from frontend/:

```powershell
npm.cmd test
npm.cmd run typecheck
npm.cmd run build
```

T021 established the simulator and neutral host test roots. Run them from their
own directories:

```powershell
cd simulator; ..\.venv\Scripts\python.exe -m pytest
cd host;      ..\.venv\Scripts\python.exe -m pytest
```

A test that composes the backend and the simulator lives in `host/tests` and
nowhere else: the dependency guard scans the whole backend tree including
`backend/tests`, and a composing test is not an exception to it. The three
editable installs the setup needs are in `README.md`.
Layout-sensitive work also runs, from the root:

```powershell
node tools/layout-evidence.mjs
```

Record any non-default base URL, exact command and final result.
Unavailable browser/server prerequisites mean unverified layout, not a pass.
Measurements must establish that the measured set contains rendered content.
Include task-specific causal/boundary proofs in addition to these checks.

Under the accepted conditional L2 rule: a slice adding a physical state,
accepted flow, reported signal, transition, reporting/publication behavior or
intervention updates its applicable Lab history and chart/SLD/timeline/inspector
in the same slice. Show addressed identity, time/interval, units, provenance
and missingness; prove reload and gate isolation. A slice with no new Lab facts
records that applicability in its packet. This does not create telemetry or
operator health from truth. See the [Lab cockpit handoff](../.ai/PLANNING_HANDOFF_LAB_COCKPIT.md)
and the 2026-09-30 Lab cockpit decisions in
[DECISIONS](../.ai/DECISIONS.md).

## Shared scope and protected seams

- Follow .ai/ARCHITECTURE.md; v4 section 3 owns the truth/composition boundary.
- Keep both the lexical and semantic control restriction in v4 section 5.1.
- Keep the existing mg-001/mg-002/mg-003 and var/ data intact.
  Instantiate new fixtures explicitly; templates copy, they do not migrate Sites.
- Product history comes only from accepted canonical envelopes.
  Lab projection and private oracle/trace objects remain gated and private.
- Cite durable decisions rather than reopening vocabulary or repeating rationale.
  D-2026-09-22-milestone-speed-over-purity governs implementation and review.
- Compare contract versions relatively under
  D-2026-09-22-contract-version-scope. Preserve old frozen identities/readback;
  incompatible execution gets an explicit refusal rather than reinterpretation.
- Use roadmap section 8 exclusions: no general optimizer, AC solver, CMMS,
  precise RUL, generic pack framework, second vertical or broad authoring suite.

Specs sit under the workflow's size ceilings, which have no minimum.
References carry durable mechanics; local criteria carry delivery obligations.
Each spec is written to pass the workflow's cold-start test: an implementer with
the file, its named references and the built state can start without asking, and
any legitimate stop is named in the file rather than left silent.
If implementation exposes a further independently reviewable cut, report it
before dropping a criterion.

## Assigned gaps and explicit waits

Every row in FEATURE_MAP's unowned-requirements table has an implementation
owner in the queue above, including component controls (T020A), addressed
bindings (T020A1), intervention artifacts (T029A), comparison history (T032)
and Bahir assessment (T035).

The starter contracts T020A, T020A1 and T020B are time-boxed: they are cheap
enabling work, not product progress, and should not absorb design debate.

Three slices carry explicit restraint rules rather than extra scope. T021A is a
narrow parser closure to be time-boxed, not a checkpoint. T023's stage inspector
stays utilitarian. T032 implements exactly one load-addition comparison, not a
generalized experimentation platform. T033 is the first major story to move
behind early client feedback if schedule pressure appears; deferring it does not
weaken the core proposition.

These followers have no separate implementation file in this queue:

- Gateway outage, buffering, retry, out-of-order release, buffer exhaustion and
  numeric bias moved out of T026 into the unscheduled T026A, which gates
  nothing. If T026's implementer finds part of it already free in the T023
  publication path, they include it and report that T026A shrank.
- Full Replay UI and broad source-health dashboard wait until after C feedback
  identifies useful breadth. T027 supplies evidence inspection and reconstructible
  accepted history now; later Replay must read that history, never re-simulate.
- Generic second-vertical packs, broad CMMS/authoring/reports and advanced solvers
  wait for a mini-grid need, real pilot or second-vertical trigger (roadmap 8).
- Model-owned Foundation need declaration (Option C) is a conditional obligation
  in T024, the first new physical laws. If its trigger is absent there, the first
  later law needing an undeclared Foundation input owns it; no speculative
  framework task is required.
- Reset/injection UI waits for T029A's first run-scoped intervention control.
  T022 has frozen execution only. T029A owns immutable artifacts, reset and
  frozen-history behavior; T032 adds paired comparison over that mechanism.

Fuel authored-number correction is assigned to T021; fuel-model expectation
basis and uncertainty to T030. These are not unowned waits.

## User choices and limits of testability

Roadmap 12.1 financial assumptions belong to T029 before external exposure;
12.2 recognizable productive load belongs to T032 before demo recording;
12.3 lifecycle monetization belongs to T033 before external exposure.
Demo point 2 is external exposure, so 12.1 is due at T029, not at T036.
Use the roadmap defaults internally, visibly labelled, without inventing approval.

Physical balance, causality, evidence coverage and claim ceilings have objective
proofs in the owning tasks. Practitioner usefulness, physical calibration to a
real installation and client credibility cannot be certified by automated tests.
T025b asks the owner to judge physical behavior; T028 collects expert feedback;
T034 asks whether the detect-to-verify path is showable; T036 carries the 13.3
walkthrough. These remain human review criteria, not
assertions that passing fixtures establish field validity.
