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

T016, the configured SLD and device/signal presentation, is in review on
`task/T016-foundation-sld-and-device-signal-presentation`. Not merged.

**It carries the M1A user-review checkpoint**, the first since T008. Two
decisions are presented on the screen and not taken: whether a breaker is a
device, component state or both and what the control vocabulary is, and how a
cold room's process symbol relates to mini-grid electrical topology. Both are
in the block headed `Open for review` inside the diagram section. Capability
planning for M1A stops until the user accepts or redirects.

Foundation now draws the configured diagram for a topology the hybrid
mini-grid archetype can arrange, and the explicit refusal with its reason for
one it cannot. The drawing is presentation over `deriveSiteSldView` and adds
nothing: rendered node, connection and component ids are compared to the
Foundation's for exact equality. Device and signal content still renders when
only the diagram is incompatible.

Seven slices of bans held the diagram out of this surface. None was deleted;
each is narrowed to where it still holds, by `withoutRegion`, which throws when
the region it excepts is not there. The details, and which assertion now says
what, are in `.agent/T016-review-packet.md` and `.ai/CODE_STATE.md` under T016.

Backend `441 passed`, frontend 20 files `629 passed`, both guards, typecheck,
the production build, and `node tools/layout-evidence.mjs` at 1280, 1000 and
640 all clean. Nine proofs, each committed first, each read for which
assertion answered. One of them is worth carrying: widening
`SldCandidateTreatment.settled` to `boolean` broke zero of 279 runtime
assertions and was caught only by `tsc`.

The habit this slice adds: **jsdom cannot see a diagram, so a diagram has to be
looked at.** Three defects survived a green suite and were found in a browser.

Local review data, gitignored and additive: `var/sites/mg-002.yaml` declares a
cold room and `mg-003.yaml` declares two AC buses, so both reviewable states
can be opened. `mg-001.yaml` is untouched.

T005 to T015 are complete, in `tasks/completed/` with their Review Outcomes.

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
- T014: Foundation topology, devices and signal mappings. Complete.
- T015: the hybrid mini-grid SLD view model. Complete.
- T016: the configured SLD and device/signal presentation. In review, and it
  carries the M1A user-review checkpoint.

Causal Sequencing step 4 is complete in code. The configured diagram renders,
inside one named section of Foundation; everywhere else on the surface the
diagram vocabulary is still banned, and the signal selector is still absent
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
