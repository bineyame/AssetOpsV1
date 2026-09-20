# T015 - Hybrid Mini-Grid SLD View Model

Status: complete
USER_REVIEW_REQUIRED: false

Intended branch: `task/T015-hybrid-mini-grid-sld-view-model`

## Feature

Topology, Devices, And SLD.

## UI-Verifiable Screen Behavior

Foundation can resolve whether the configured Site is compatible with
the hybrid mini-grid SLD archetype and can expose that result to tests and to
the next UI slice. For a compatible Site, the view model contains the diagram
nodes, connections, labels, ratings, device/signal availability, and empty
runtime/evidence value slots needed to render the configured SLD later. For an
incompatible Site, the view model returns an explicit unavailable state with a
reason.

No diagram renders yet. The visible Foundation screen still shows the
record-sourced topology and device/signal facts from T014 in the Foundation
subtab architecture, with no SLD panel, empty frame, signal selector, runtime
values, evidence values, source health, product health, telemetry, charts,
Replay, or Findings.

## Why This Is Next

T014 makes topology, devices, and mappings canonical Foundation facts. The next
dependency is the logical SLD view-model boundary that binds those facts to the
hybrid mini-grid archetype without letting the archetype become a second
topology model.

This slice also resolves the four-slice Architect guidance inside the
three-task M1A range by folding runtime/evidence value slots into the view
model. The slots are named and empty only. They do not bind simulator runtime,
accepted evidence, latest values, quality, freshness, health, or overlays.

Keeping this as a non-rendering view-model slice gives T016 a small, reviewable
UI task: render exactly what this boundary produces and show the incompatible
state honestly.

## Acceptance Criteria

- A reusable SLD view-model layer consumes the validated Site Foundation from
  the shared Site substrate and produces either a compatible hybrid mini-grid
  view model or an explicit incompatible/unavailable result.
- The hybrid mini-grid archetype binds components by canonical type and role,
  never by Site-specific identifiers such as `MG-001`, display names, mockup
  labels, fixture order, or array position.
- The SLD archetype owns presentation concerns only: visual roles, approximate
  node positions, symbol placement, connection routing, and named value slots.
  It does not create, remove, rename, reorder, or reinterpret canonical
  components, topology connections, devices, signals, mappings, or ratings.
- Compatible view-model output preserves canonical component IDs, connection
  IDs, device IDs, signal IDs, mapping IDs, display names, ratings, and units so
  T016 can assert agreement between SLD labels and device/signal rows.
- Incompatible topology produces a structured unavailable result with a stable
  reason that the UI can render. It does not silently hide unmatched
  components, drop unsupported connections, draw a partial diagram as if it
  were complete, or fall back to a generic graph.
- Runtime/evidence value slots exist as empty named slots on nodes or
  connections where later Simulator Lab runtime or AssetOps evidence overlays
  may bind. They carry no value, timestamp, freshness, quality, health, source,
  run, or evidence metadata in this slice.
- The view-model contract leaves the future signal selector inert: it may expose
  available configured signals, but it does not choose a signal, bind a latest
  value, or render a selector.
- Unit tests compare the view-model component and connection identities against
  canonical Foundation topology and prove no extra or missing topology element
  is introduced by the archetype.
- Unit tests cover at least one compatible hybrid mini-grid Site and at least
  one incompatible topology, including the explicit unavailable reason.
- Foundation visible UI remains unchanged from T014 except for any
  invisible data plumbing needed by tests. A UI test continues to assert no SLD
  panel, diagram container, diagram heading, empty frame, signal selector,
  runtime value, evidence value, source-health term, or product-health term is
  in the DOM.
- The view model lives in the shared Site presentation/domain substrate and
  remains shell-neutral. It imports no simulator runtime, no evidence store, no
  feature flag, and no shell code.

## Required Product And Domain Semantics

- M1 implements the Single Line Diagram with a reusable archetype template and
  data bindings, not arbitrary topology auto-layout or electrical CAD behavior.
- Canonical Site Foundation remains the source of truth for components,
  topology, connectivity, ratings, devices, signal availability, mappings, and
  control assumptions. The SLD view model is a presentation adapter over that
  truth.
- Unsupported topology is an unavailable/incompatible state. It is not a
  partial diagram, a hidden asset list, or a generic graph.
- Runtime and evidence value slots are interface preparation only. Runtime
  values arrive later from Simulator Lab runtime, and evidence values arrive
  later only from accepted AssetOps evidence. This slice must not bridge either
  boundary.
- Breaker/control state vocabulary and whether breakers are devices, component
  state, or both remains undecided. The view model may carry declared controls
  as configuration facts, but it must not use UI copy or type names that settle
  the final product vocabulary before T016 review.
- How cold-room process symbols relate to mini-grid electrical topology remains
  undecided. The archetype may reserve a presentational treatment for a declared
  cold-room/load component only as a reviewable candidate for T016, not as a
  silent domain decision.

## Protected Seams

- SLD presentation boundary: unit/contract test.
  The archetype owns layout and symbol metadata only and never mutates canonical
  topology.
- Canonical topology authority: unit/contract test.
  View-model output is traceable back to Foundation IDs and introduces no
  component or connection.
- Unsupported-topology unavailable state: unit test.
  Incompatible Sites produce an explicit result instead of a misleading or
  partial diagram.
- Device-to-signal mapping: unit/contract test.
  Signal availability and later value slots come only from declared mappings.
- Simulator/product boundary: CI guard.
  The view model does not import simulator runtime or private truth.
- Evidence loop boundaries: CI guard.
  Empty value slots do not import or query accepted evidence, staged envelopes,
  ingestion, source health, or product conclusions.
- Shared Site presentation substrate: CI guard.
  The view model remains shell-neutral and lives with the shared Site substrate.

## Focused Tests And Checks

- View-model unit test for a compatible hybrid mini-grid Site asserting every
  rendered node and connection traces to a canonical Foundation component or
  topology connection.
- View-model unit test asserting labels, ratings, units, devices, signals, and
  mapping IDs match the expanded Foundation and are not derived from mockup text
  or array position.
- View-model unit test for incompatible topology asserting a structured
  unavailable result and reason.
- View-model unit test asserting no extra component, connection, device, signal,
  or mapping is introduced by the archetype.
- View-model unit test asserting runtime/evidence value slots are present but
  empty and carry no value, timestamp, freshness, quality, source, run, or
  evidence metadata.
- Import/architecture check asserting the SLD view-model modules import no
  simulator runtime, no evidence store, no shell code, and no feature flag.
- UI regression test asserting Foundation still renders no diagram
  panel, diagram heading, empty frame, signal selector, runtime/evidence value,
  source-health term, product-health term, telemetry, chart, Replay, or Finding.
- Run `tools/check-architecture.ps1`.
- Run `tools/check-agent-workflow.ps1`.
- Existing backend and frontend suites, typecheck, and production build stay
  green.

## Scope Limits

- Do not render the SLD. T016 owns the visible configured SLD and device/signal
  presentation inside Foundation.
- Do not implement arbitrary graph auto-layout, drag/drop schematic editing,
  generic electrical CAD behavior, topology editing, or automatic routing
  beyond the fixed hybrid mini-grid archetype.
- Do not bind runtime values, accepted evidence values, source health, product
  health, quality, freshness, timestamps, simulator truth, staged envelopes,
  ingestion records, Replay, analytics, or Findings to the value slots.
- Do not build a Simulator Lab Site view or Lab SLD surface.
- Do not decide breaker/control vocabulary or cold-room/electrical symbol
  treatment silently. T016 carries the user-visible review checkpoint.

## User Review

User review is not required for this slice. The slice creates the logical
boundary and tests the compatibility behavior, but it deliberately does not put
the archetype, incompatible-topology language, cold-room symbol treatment, or
device/signal wording in front of the user yet. T016 carries that checkpoint.

## Review Outcome

Two independent reviews by Codex. First: **accept with findings fixed on the
branch**, two Medium. After the fixes: **accept, no findings.**

### How this slice was built, which shaped the review

The Implementer agent stalled with a watchdog failure before committing
anything, before running a single check and before writing a packet. Its work
was found uncommitted, committed verbatim and unreviewed by the coordinating
session so it could not be lost, then verified and extended from the outside.
783 lines of new logic were never verified by their author, and there is no
record of authorial intent. The Reviewer was told this and asked to weigh
reading over sampling.

### Finding 1: the anti-vacuity anchor was itself vacuous

The test proving the Foundation screen renders none of the archetype's
presentation vocabulary built its matcher with
``new RegExp(`\b${token}\b`)``. Inside a JavaScript template string `\b` is a
backspace character, U+0008, not a word-boundary escape.

Verified rather than accepted: the first character of that regex source is code
8; escaped it is code 92, and only the escaped form matches a screen showing
`BUSBAR`. The test passed on a screen rendering the token exactly as readily as
on one that did not - and its job was to be the anchor proving the view model
stays invisible.

Fixed, with the token escaped as well, since these strings come from the
archetype and one carrying a metacharacter would change what is searched for.
Proved: rendering `BUSBAR` in a panel body now fails exactly that test and no
other. Before the fix, the same probe failed nothing.

**This is the same escape as the two dead PowerShell patterns in T011A, in a
different language.**

### Finding 2: a broken reference wearing an unplaced costume

`deriveSiteSldView` validated topology node components, connection endpoints
and mapping device/signal references, but not `device.component_id` or
`mapping.component_id` against the declared component set. Those arrived as
`unplaced` entries instead.

The two look alike and are not. A device naming a component the archetype does
not place is unplaced: the component exists and the diagram has nowhere for it.
A device naming a component the foundation never declared is a broken
reference - and it produced a model reporting `compatible` while carrying
device and signal facts anchored to something that does not exist.

Both now return `REFERENCE_UNRESOLVED` naming the offending id, so that code
covers every kind of reference this view model reads. Proved: removing the
device check fails two of the three new tests.

### The re-review

Accept, no findings. It verified the repaired matcher, **swept live source for
the same literal-backspace bug and found none**, re-read the reference
validation paths, and confirmed `unplaced` still covers declared-but-unplaced
components rather than having been collapsed into the refusal.

That sweep was repeated independently here across TypeScript, PowerShell, Node
and Python. No live template literal or double-quoted string carries an
unescaped `\b`, and the single embedded control character in the tree is
deliberate: `test_site_parsing.py` uses a BEL to prove free text containing a
control character is refused.

### Checks

Reviewer, both passes: architecture guard, workflow guard, backend `441 passed`
and `tsc --noEmit` all passed. The frontend suite and build could not run under
its sandbox for the known esbuild reason.

Implementing session, after both fixes: backend `441 passed`, frontend 20 test
files, `tsc` clean, build clean at 221.31 kB - unchanged from `main`, because
nothing imports the view model outside tests until T016.

### Not verified

Nothing renders, so there is nothing to see and no browser evidence to gather.
The archetype's geometry is tested for determinism and non-collision, not for
whether it makes a sensible diagram; T016 inherits it either way.
