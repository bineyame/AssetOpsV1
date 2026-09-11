# Workflow

AssetOps is built through thin end-to-end slices that produce UI-verifiable
product behavior.

## Lanes

Planned lane:

Architect or Planner -> Implementer -> Reviewer -> User review

Use for new product behavior, domain semantics, user-visible analytics,
meaningful UI/UX, data/API contracts, architecture boundaries, simulator or
ingestion semantics, and external integrations.

Fast lane:

Implementer -> Reviewer

Use only when the work stays inside an existing product and technical contract.

## Vertical Slice Standard

Each planned task should include the minimum required domain semantics, backend
logic, data contract, UI, tests, and demo evidence needed for a reviewable
result. Not every task needs every layer, but each task should either deliver a
UI-verifiable outcome or explicitly unlock a named UI-verifiable slice.

Features and tasks are different planning objects. A feature is a complete
product function that may require several tasks. A task is a reviewable
implementation slice that delivers or materially advances one UI-verifiable part
of a feature.

Prefer sequences such as:

- Build the first canonical app shell with Sites, Site Details, and Simulator
  Lab entry points visible.
- Load one known demo site and show its current operating state in the Site
  Details screen.
- Show one simulator run in the Simulator Lab and expose the same published
  observations through the Site Details screen.
- Ingest one simulated telemetry stream and reflect it on the Site Details
  screen.
- Detect one meaningful fuel discrepancy and expose the evidence.
- Show the discrepancy as an actionable finding in the UI.
- Allow the user to inspect supporting evidence.
- Run the same capability across multiple sites.

Avoid building whole layers before there is useful product behavior.

## Planning Before Tasks

Do not predefine implementation tasks before the Architect has analyzed the
feature map. The Architect should first inspect the canonical UI references,
identify causal prerequisites between visible features, and define feature
boundaries before tasks are created.

For example, `SimulatorLab1.png` shows site information, an operational
overview, a single-line diagram, devices/sensors, gateway output, events, and
run state. Those visible details imply prior capabilities: sites must be
managed, components and devices must be configured, and the single-line diagram
must be derived from configuration before Simulator Lab can meaningfully display
them.

The Architect may wear Product, Architecture, UI/UX, and Domain hats as needed
to produce a feature map. That feature map can then be broken into reviewable
tasks by the Architect or later by the Implementer under architectural guidance.

## Review Packet

Provide concise evidence:

- Task.
- Outcome delivered.
- Files materially changed.
- Acceptance criteria status.
- Checks run.
- Known deviations.
- Residual risk.
- User-review focus.

The review packet is evidence, not implementation history.

## User Review

Use `USER_REVIEW_REQUIRED: true` when the slice materially affects product
direction, domain semantics, UI/UX, evidence interpretation, user-visible
analytics, information hierarchy, or demo narrative.

After a user-review checkpoint, do not assume the next planned slice is still
correct. The user may approve, revise, reorder, remove, split, expand, or
redirect later work.
