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

No active task. T016 closed out 2026-09-20, and **M1A is complete.**

Every planned task T001-T016 is in `tasks/completed/` with its Review Outcome.
`tasks/` is empty. No M1B task exists, and none should be created without
planning.

T016 drew the configured Single Line Diagram inside Foundation and carried the
M1A user-review checkpoint. Independent review: accept, no findings - the first
clean first-pass review since T011. User review: accepted as built.

### The checkpoint settled one question and not the other

**Cold-room symbol treatment: accepted as proposed.** A declared cold room draws
in the lane its topology role puts it in, with its own shape. It is still marked
`Proposed treatment` on screen, and `SldCandidateTreatment.settled` is still the
literal `false`. Removing that marker is a visible product change and should be
its own commit.

**Breaker and control vocabulary: still open.** It was presented with candidates
the project had considered and not chosen, and no proposal - so accepting the
screen chose nothing. It stays banned everywhere outside the review block, and
T014's `frozenset` scan keeps it out of schema names.

Nothing in M1A draws a breaker, so nothing was blocked. **The first slice that
renders or stores a breaker state needs the answer first, and it should come
back to the user rather than choosing quietly.**

### State

Backend `441 passed`, frontend `629 passed` across 20 files, both guards,
typecheck and build clean at 240.35 kB. `tools/layout-evidence.mjs` reports all
claims holding at 1280, 1000 and 640 wide.

`var/sites/` holds `mg-001` plus `mg-002` (declares a cold room) and `mg-003`
(two AC buses), added for the T016 checkpoint. **The user asked that these be
kept as fixtures.** They are gitignored, so nothing in the repo protects them:
do not clear this directory, and add rather than replace when a slice needs
another shape. `mg-002` is the only local Site declaring a cold room and
`mg-003` the only one the SLD archetype refuses, so both are the only way to
open those two states in a browser.

### Two seam questions, settled 2026-09-20

The Architect recommended, the user accepted, and both entries are now in
`.ai/DECISIONS.md`.

- Layout evidence is standing closeout evidence for layout-sensitive slices,
  carried in the review packet, still outside `tools/check-architecture.ps1`. A
  missing precondition records `not run` and leaves the claim unverified, never
  green. See `.ai/WORKFLOW.md` Review Packet and Closeout.
- No guard ties a merged slice's task status to branch state. Closeout is
  manual: Review Outcome recorded and status set before the merge.

The breaker and control vocabulary is **still open**. An Architect
recommendation the user has not yet accepted is in
`.agent/breaker-vocabulary-recommendation.md`: a breaker is topology and, when
instrumented, something a device reports about; position is evidence, not
Foundation configuration; M1 carries nothing beyond T014's control assumptions.

## Current Site Foundation Sequence

**Every planned task is complete.** T001-T016, including T010A and T011A-T011C,
are in `tasks/completed/`, each with its Review Outcome. The per-slice record of
what each settled is in `.ai/CODE_STATE.md`; this file deliberately no longer
carries one line per slice, which is what pushed it over its cap.

Causal Sequencing steps 3 and 4 are complete in code. The configured diagram
renders inside one named section of Foundation; everywhere else on the surface
the diagram vocabulary is still banned, and the signal selector is still absent,
because there is nothing to show for the signal a reader would have picked.

## Read For The Next Slice

Nothing is planned beyond T016. M1B, Scenario Catalog And Run Setup, is not
planned or started until this checkpoint is accepted or redirected, and the
user may reorder, split or remove what follows.

For reviewing T016:

- `tasks/T016-foundation-sld-and-device-signal-presentation.md`
- `.agent/T016-review-packet.md`, whose `Absence Assertions Changed` section
  names every ban that moved and what it says now.
- `.ai/CODE_STATE.md`, the T014, T015 and T016 entries.
- `.ai/FEATURE_MAP.md`, `### 2. Topology, Components, Devices, And Single Line
  Diagram` and `### Viewport and overflow commitment`.
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-13-shared-site-substrate`
  - `D-2026-09-13-canonical-fidelity`

## Settled Direction

- M1 ships zero canonical Sites. First run has a genuinely empty Sites index.
- A template is not a Site and never has `site_id`, lifecycle status, location,
  or a place-bound timezone.
- Template browsing and Site creation are Simulator Lab surfaces behind
  `simulator_lab.enabled`.
- Sites index, Site Details, and the Foundation surface are operator surfaces
  and are never gated. T008 built the surface under the working name Site
  Configuration; T011A renames it to Foundation and keeps the old address as a
  redirect. `configuration` stays as the domain word.
- A tab is a destination only when a route behind it renders a truthful surface
  for the identified site. A canonical aspect with no content yet is labelled in
  place, never disabled: disabled says the capability exists and is switched
  off.
- M1 commits to desktop-class width, at least 1280px, and claims no mobile,
  phone or portrait-tablet form. Page-level overflow is not an allowed answer to
  density: shell chrome stays anchored and dense content owns its own scroll.
  Nothing may be dropped to fit - not a Sites index column, not a rail label,
  not one of the eight Site tabs.
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

Tasks T005-T016 inherit these exclusions unless a later reviewed task explicitly
changes them. Two deliberate changes so far. T014: the Foundation schema now
carries topology, devices, signal mappings and control assumptions, which the
"no Devices & Sensors screen" exclusion below never covered - what it forbids is
a device-management surface, and none exists. T016: the Single Line Diagram, its
view model and the diagram region are built, which is what causal step 4 is for.
Everything else in that exclusion still holds - no empty diagram frame, no
signal selector, no topology auto-layout, no Devices & Sensors screen and no
device-management surface - and the bans are narrowed to the rest of the
surface rather than removed.

- No in-place Site/Foundation editing, Save/Publish over an existing Site,
  rename, duplicate, delete, configuration history, rollback, approval flow, or
  disabled placeholder for those capabilities.
- No user-facing removal flow.
- No empty diagram frame, signal selector, topology auto-layout, drag/drop or
  diagram editing, Devices & Sensors screen, or device-management surface. The
  Single Line Diagram and its view model are built, by T015 and T016; the rest
  of this line is unchanged.
- No scenarios, run setup, simulator execution, gateway staging, ingestion,
  source envelopes, evidence records, source health, charts, analytics, Replay,
  or Findings.
- No speculative database, ORM, migration tool, cache, query DSL, pagination,
  or port methods beyond the active slice.
- No operator navigation item, second simulator chokepoint, or weakening of
  previous route, API, navigation, architecture, or fabricated-value guards.
- No mockup value, timestamp, status, label, control, or destination unless the
  active slice supplies truthful backing content.
