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

T014 is built and in review. Branch
`task/T014-foundation-topology-devices-and-signal-mappings`, three commits, not
merged. Packet at `.agent/T014-review-packet.md`.
`USER_REVIEW_REQUIRED: false`.

**Causal Sequencing step 4 has started.** T014 is its first slice and the first
since T008 to add content rather than arrange it: the canonical Foundation now
carries topology, devices, signal mappings and control assumptions, the shipped
hybrid mini-grid template declares all four, a created Site copies them, and the
Foundation screen renders them instead of stating them as absent.

What it left behind, beyond the screen:

- One strict validator for the Foundation content, shared by the template parser
  and the Site parser, with a test asserting they expose the same object.
- `null` versus `[]`. `null` is a document declaring none; an empty list is
  refused everywhere, because `[]` renders as a table with a header row and no
  rows, which says the site HAS none. It is the only malformed body in this tree
  that would not look broken.
- The T008 stated absences survive with rewritten reasons. They explained the
  absence by what the M1 schema could carry, which stopped being true.
- `tools/layout-evidence.mjs` measures every table and visits Foundation at
  640px, because at 1280 and 1000 nothing overflows and the containment claim
  was about an empty set.

Next: T015, the SLD view model, then T016, the configured diagram and the user-
review checkpoint that owns the breaker/control vocabulary and the cold-room
symbol treatment. Neither is planned.

Still unjudged by anyone: whether these screens read well. Foundation now stacks
two rows, four tables under Topology, one under Controls, and the components
table below that.

## Current Site Foundation Sequence

Reworked Site Foundation tasks are T005-T013; T014 opens step 4.

- T005: shipped Site Template catalog in Simulator Lab, gated. Complete.
- T006: create a Site from a template; first user-review checkpoint. Complete.
- T007: Site Details by `site_id`. Complete.
- T008: read-only Site Configuration; second user-review checkpoint. Complete.
- T009: shared visual vocabulary. Complete.
- T010A: the fetch seam, split out of T010. Complete.
- T010: Lab template and create surfaces to mockup quality. Complete.
- T011: Sites index to canonical screen one. Complete.
- T011A: Foundation naming and the operator Site tab row. Complete; user
  review deferred to the pass after T011B.
- T011B: shell and dense content overflow containment. Complete; its browser
  evidence is measured by `tools/layout-evidence.mjs`.
- T011C: Site tab row treatment, from T011A's user review. Complete.
- T012: Site Details to canonical screen two. Complete.
- T013: Foundation to canonical screen three. Complete.
- T014: Foundation topology, devices and signal mappings. In review.
- T012-T013: staged visual fidelity, against the tab row and the name T011A
  settled, and under the viewport commitment.

The second checkpoint is closed. Causal Sequencing step 4 has begun: T014
carries topology, devices and signal mappings in the canonical Foundation. The
configured single-line diagram is still not built - T015 owns its view model and
T016 renders it - and no slice before T016 may render the diagram, an empty
frame for it, or its signal selector.

## Read For The Next Slice

T015 is causal step 4's second slice: the SLD view model over the topology T014
made canonical. It is not planned.

- `.ai/CODE_STATE.md`, the T013 and T014 entries. T014 settles the schema, the
  vocabularies, the `null`-versus-empty rule, and what the screen already
  renders; T013 settles where a panel may sit.
- `.ai/FEATURE_MAP.md`, `### 2. Topology, Components, Devices, And Single Line
  Diagram`, and within `## Canonical Screen Fidelity` the sections
  `#### Foundation name and subtabs` and `### Viewport and overflow
  commitment`. The viewport section is not reachable from the Feature Map
  Index, so it has to be named.
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-13-site-foundation-persistence`
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

Tasks T005-T014 inherit these exclusions unless a later reviewed task explicitly
changes them. T014 is the one deliberate change so far: the Foundation schema
now carries topology, devices, signal mappings and control assumptions, which
the "no Devices & Sensors screen" exclusion below never covered - what it
forbids is a device-management surface, and none exists.

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
