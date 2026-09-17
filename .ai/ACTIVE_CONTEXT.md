# Active Context

Keep this file compact and current. It is the agent handoff for what matters
now; durable reasoning stays in `.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`,
`.ai/ARCHITECTURE.md`, `.ai/CODE_STATE.md`, and the task files.

Size rule: this file stays under 200 lines, enforced by
`tools/check-agent-workflow.ps1`. Every agent reads it in full, so it is the one
document whose growth is paid on every task. It was trimmed once for that reason
and grew back to nearly four times the trimmed size in six slices, because
per-slice records accumulated here. They now live in `.ai/CODE_STATE.md`. If a
section here grows by one entry per slice, it is in the wrong file.

## Current Milestone

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

## Active Task

No active task. T009 closed out 2026-09-17.

Independent review returned one medium finding, fixed on the branch: the Site
substrate's loading, not-found and unavailable states kept a raw `<h1>` while
their loaded states had moved to the shared `PageHeader`, leaving one surface
half on the vocabulary and half bespoke. The reviewer found no fault with the
Lab rail, the changed inherited assertions, the rendered values, or the badge
rule. The Review Outcome is in
`tasks/completed/T009-shared-visual-vocabulary.md`.

Two things it leaves for whoever picks up T010. Nobody has rendered any of this
in a browser and it is a visual slice, so the first fidelity slice to run the
app is checking T009's work as well as its own. And frontend flakiness under
CPU contention is broader than the single case T007 and T008 recorded: any file
can time out under load, so a single red run on a loaded machine should be
re-run before it is believed.

T005 to T008 are complete. Their task files are in `tasks/completed/` with
their Review Outcomes.

Next: T010, the Lab template and create surfaces to mockup quality.

## Current Site Foundation Sequence

Reworked Site Foundation tasks are T005-T013 in `tasks/`.

- T005: shipped Site Template catalog in Simulator Lab, gated. Complete.
- T006: create a Site from a template; first user-review checkpoint. Complete.
- T007: Site Details by `site_id`. Complete.
- T008: read-only Site Configuration; second user-review checkpoint. Complete.
- T009: shared visual vocabulary. Complete.
- T010-T013, with T011A inserted: staged visual fidelity after real
  content exists.

The second checkpoint is closed. Causal Sequencing step 4, topology, devices,
and the configured single-line diagram, is unblocked for planning and is not
yet planned. No T009-T013 slice may render the diagram, an empty frame for it,
or its signal selector.

## Read For T009

T009 is the shared visual vocabulary, applied to the surfaces T005-T008 made
real. It introduces no content, no control and no destination, which is what
makes it safe to run before the next capability step.

- `tasks/T009-shared-visual-vocabulary.md`
- `.ai/CODE_STATE.md`, the T006, T007 and T008 entries, for the Site record
  shape, the read path, the substrate, and what each surface renders today.
  Read the completed task files only if an entry there is not enough; the
  entries exist so that large task files do not have to be read for their code
  shape.
- `.ai/FEATURE_MAP.md` sections:
  - Feature Map Index
  - Product Spine
  - Enforceable Protected Seams
  - Early Feature: Site Foundation And Configuration-Only Site
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-13-site-foundation-persistence`
  - `D-2026-09-13-site-foundation-resequence`
  - `D-2026-09-13-shared-site-substrate`
  - `D-2026-09-13-provenance-status-vocabulary`
  - `D-2026-09-13-canonical-fidelity`
- `.ai/ARCHITECTURE.md` only if dependency direction, contracts, simulator
  boundaries, or protected seams are in play.

## Settled Direction

- M1 ships zero canonical Sites. First run has a genuinely empty Sites index.
- A template is not a Site and never has `site_id`, lifecycle status, location,
  or a place-bound timezone.
- Template browsing and Site creation are Simulator Lab surfaces behind
  `simulator_lab.enabled`.
- Sites index, Site Details, and the Foundation surface are operator surfaces
  and are never gated. T008 built the surface under the old Site Configuration
  name; the next Planner pass must use the Foundation naming guidance in
  `.ai/FEATURE_MAP.md`.
- A Site created from the Lab is a normal product Site with
  `source.mode = SIMULATED`; there is no Lab-owned Site store and no publish or
  promote step.
- Operator navigation does not grow for Site Foundation slices.
- Operator Site page and Lab Site page share one presentation substrate at
  `frontend/src/sites/`.
- Source mode, Site lifecycle, configuration origin, evidence readiness, and
  source health are separate concepts.

## What The Code Already Settles

In `.ai/CODE_STATE.md`, one entry per slice, so this file does not carry a
growing record. Read the entries the "Read For" list above names.

- What T006 settled: the Site record shape, the two stores, identity rules, the
  create and index APIs, the substrate modules.
- What T007 settled: the per-Site read path and its refusals, the detail wire
  shape, the operator site routes, the three stated-absence facts.
- Tooling: the per-seam architecture guard, and the settle helper that frontend
  tests must use instead of awaiting a heading or a landmark.

Carried-forward risk lives there too, per slice, with closed items marked
settled in place rather than deleted. Open at the time of writing: no
integration test binds the real frontend clients to the backend (third slice
running, and now a decision rather than a gap); the Site record has no created
or updated timestamp; integration readiness is a stated absence with no field
behind it.

## Standard Checks

- `tools/check-architecture.ps1`
- `tools/check-agent-workflow.ps1`
- Existing backend and frontend tests relevant to the active slice.

## Task Spec Hygiene

Follow `.ai/WORKFLOW.md`, Task Spec Size and Avoiding Spec Chaff. Large early M1
specs are acceptable only when they protect dangerous firsts.

## Inherited M1 Step 3 Exclusions

Tasks T005-T013 inherit these exclusions unless a later reviewed task explicitly
changes them:

- No in-place Site/Foundation editing, Save/Publish over an existing Site,
  rename, duplicate, delete, configuration history, rollback, approval flow, or
  disabled placeholder for those capabilities.
- No user-facing removal flow.
- No Single Line Diagram, empty diagram frame, signal selector, SLD view model,
  topology auto-layout, Devices & Sensors screen, or device-management surface.
- No scenarios, run setup, simulator execution, gateway staging, ingestion,
  source envelopes, evidence records, source health, charts, analytics, Replay,
  or Findings.
- No speculative database, ORM, migration tool, cache, query DSL, pagination,
  or port methods beyond the active slice.
- No operator navigation item, second simulator chokepoint, or weakening of
  previous route, API, navigation, architecture, or fabricated-value guards.
- No mockup value, timestamp, status, label, control, or destination unless the
  active slice supplies truthful backing content.
