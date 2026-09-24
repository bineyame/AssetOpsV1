# Recreated implementation queue

Recreated from main a7417dd and D-2026-09-24-v4-roadmap-replan.
All tasks are planned; this file does not activate implementation.
Direction: [feature map](../.ai/FEATURE_MAP.md),
[starter handoff](../.ai/PLANNING_HANDOFF_T020A_T023.md),
[v4](../Docs/simulator_design_v4.md), and
[demo roadmap](../Docs/mini-grid-demo-architecture-and-roadmap.md).
The six existing starter files are replacements, not amendments.

## Order and observable checkpoints

| Order | Task | Map | Reviewable result |
| --- | --- | --- | --- |
| 1 | T020A | A | Typed component properties in Foundation and frozen Draft |
| 2 | T020A1 | A | Two same-type components resolve independently |
| 3 | T020B | A | Shipped Fuel Loss setup reaches READY |
| 4 | T021 | A | Independent causal fuel trajectory; unlocks T022 |
| 5 | T021A | A | Observation declarations lose execution requirement |
| 6 | T022 | A | Start/step a Draft; inspect truth versus generated reading |
| 7 | T023 | B preparation | Inspect persisted canonical staged envelopes |
| 8 | T024 | A | Daytime PV/storage serves three addressed loads |
| 9 | T025 | A completion | Generator/policy change and healthy full-site run |
| 10 | T026 | B | Dispatch evidence survives gateway outage/recovery |
| 11 | T027 | B completion | Commit -> ingestion -> persistent Site Overview |
| 12 | T028 | C | Dispatch Finding, Evidence and bounded fuel quantity |
| 13 | T029 | D | Versioned assumptions translate quantity into money |
| 14 | T030 | E | Fuel balance with separate delivery/dip records |
| 15 | T031 | F | Evidence-backed recurring headroom opportunity |
| 16 | T032 | F completion | Paired load addition with isolated comparison history |
| 17 | T033 | G | Battery stress trajectory and replacement exposure |
| 18 | T034 | H | Policy action -> post-action evidence -> verification |
| 19 | T035 | I prerequisite | Bahir start failure and bounded service assessment |
| 20 | T036 | I completion | Independent six-site portfolio and client walkthrough |

Task dependency declarations identify the required artifacts.
The order above is the intended delivery order; a user checkpoint may redirect
later tasks. T021A stays after T021 and is not a kernel prerequisite.
T023 is preparatory B work; A completes before B's internal demo.
T028 is the expert-feedback checkpoint. Seek that feedback before the portfolio;
a task does not authorize contacting anyone automatically.

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

T021 establishes runnable simulator and neutral host test roots and records
their exact commands; subsequent runtime tasks run those relevant suites.
Layout-sensitive work also runs, from the root:

```powershell
node tools/layout-evidence.mjs
```

Record any non-default base URL, exact command and final result.
Unavailable browser/server prerequisites mean unverified layout, not a pass.
Measurements must establish that the measured set contains rendered content.
Include task-specific causal/boundary proofs in addition to these checks.

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

Specs use the workflow's recommended bands as sizing limits rather than adding
prose to reach a minimum. References carry durable mechanics; local criteria
carry delivery obligations. No proposed slice needs an over-band specification.
If implementation exposes a further independently reviewable cut, report it
before dropping a criterion.

## Assigned gaps and explicit waits

Every row in FEATURE_MAP's unowned-requirements table has an implementation
owner in the queue above, including component controls (T020A), addressed
bindings (T020A1), comparison history (T032) and Bahir assessment (T035).

These followers have no separate implementation file in this queue:

- Full Replay UI and broad source-health dashboard wait until after C feedback
  identifies useful breadth. T027 supplies evidence inspection and reconstructible
  accepted history now; later Replay must read that history, never re-simulate.
- Generic second-vertical packs, broad CMMS/authoring/reports and advanced solvers
  wait for a mini-grid need, real pilot or second-vertical trigger (roadmap 8).
- Model-owned Foundation need declaration (Option C) is a conditional obligation
  in T024, the first new physical laws. If its trigger is absent there, the first
  later law needing an undeclared Foundation input owns it; no speculative
  framework task is required.
- Reset/injection UI waits for T032's first run-scoped intervention control.
  T022 has frozen execution only. T032 owns immutable history and reset behavior.

Fuel authored-number correction is assigned to T021; fuel-model expectation
basis and uncertainty to T030. These are not unowned waits.

## User choices and limits of testability

Roadmap 12.1 financial assumptions belong to T029 before external exposure;
12.2 recognizable productive load belongs to T032 before demo recording;
12.3 lifecycle monetization belongs to T033 before external exposure.
Use the roadmap defaults internally, visibly labelled, without inventing approval.

Physical balance, causality, evidence coverage and claim ceilings have objective
proofs in the owning tasks. Practitioner usefulness, physical calibration to a
real installation and client credibility cannot be certified by automated tests.
T025 asks the owner to judge physical behavior; T028 collects expert feedback;
T036 carries the 13.3 walkthrough. These remain human review criteria, not
assertions that passing fixtures establish field validity.
