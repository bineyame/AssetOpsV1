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

## Task Spec Size

Task specs are guardrails for fast implementation, not miniature design
documents. Keep durable reasoning in `.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`,
or `.ai/ARCHITECTURE.md`; keep task files slice-specific and executable.

Recommended size bands:

- Normal UI/content slice: 100-180 lines.
- Boundary-changing slice: 180-260 lines.
- First write path, evidence contract, ingestion, simulator truth boundary, or
  analytics/finding semantics: 250-400 lines.

If a task grows beyond its band, either split the slice or move durable
reasoning into the canonical planning and architecture files. Early M1 tasks may
temporarily sit near the upper band only when they settle dangerous firsts such
as Site identity, YAML authority, storage posture, simulator/operator
separation, provenance, or no-fabricated-UI rules.

Every task spec should include:

- User-visible outcome.
- Why this slice is next.
- Acceptance criteria tied to behavior or contracts.
- Only the product/domain semantics needed for this slice.
- Protected seams and exact checks.
- Scope limits.
- Whether user review is required.

Leave to implementation:

- Component factoring.
- Helper names.
- Styling mechanics.
- Test structure.
- Local code organization below established boundaries.

## Avoiding Spec Chaff

When writing or revising task specs, prefer behavior and contract guardrails over
defensive repetition.

- Put inherited exclusions in one shared place and reference them from tasks.
- Repeat a prohibition inside a task only when the slice has a special local
  risk or exception.
- Specify the required property and proof, not the exact implementation
  mechanics, unless the mechanism is itself the protected seam.
- Avoid exact wording requirements unless the user has reviewed that copy as
  product language; otherwise require clear, accessible meaning.
- Avoid telling implementers where to put helpers, how to factor components, or
  how to shape tests below established boundaries.
- Treat a high count of `do not`, `must not`, `never`, or `exactly` as a smell
  during planning review. It may be justified, but it should trigger a trim or a
  move into shared guidance.

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
- Layout evidence, when the slice is layout-sensitive.
- Known deviations.
- Residual risk.
- User-review focus.

The review packet is evidence, not implementation history.

**For the rest of the simulator milestone, a Reviewer raises three things and
records the rest.** Under `D-2026-09-22-milestone-speed-over-purity`: a defect
that would be expensive to reverse later, a claim that would mislead an
Implementer, and a decision only the user can take. Everything else - naming
that is imperfect but honest, a redundant but true restatement, a vocabulary
that would be better shaped and is not wrong - goes to
`.ai/MILESTONE_REVIEW_BACKLOG.md` as a residual-risk entry rather than
blocking the slice. *This would be better named* is a backlog entry; *this
name is false* is still a finding, because a false name misleads. The complete
review, including a possible refactor, follows milestone completion and proper
testing, and the backlog is what it reads first.

A slice is layout-sensitive when it changes shell layout, dense tables,
intrinsic-width drawings, SVG geometry, tab or subtab treatment, or viewport
behaviour. Such a slice runs `tools/layout-evidence.mjs` and records the exact
command, the base URL when non-default, and the final result line. A missing
precondition is not a pass: when Chrome, the backend or the dev server is
unavailable, record `layout evidence: not run` with the blocking precondition,
and the affected layout claim is unverified rather than green. Every new
measured claim about overflow, visibility or rendered content carries at least
one measurement proving its set is non-empty.

## Closeout

Before a slice is merged, its Review Outcome is recorded in the task file and
its status is set to complete, or the task says explicitly what is still open.
Nothing checks this, so it is the Reviewer's and the user's to hold: T011B and
T011C reached `main` at `in_review`, and the user noticed rather than a guard.

## User Review

Use `USER_REVIEW_REQUIRED: true` when the slice materially affects product
direction, domain semantics, UI/UX, evidence interpretation, user-visible
analytics, information hierarchy, or demo narrative.

After a user-review checkpoint, do not assume the next planned slice is still
correct. The user may approve, revise, reorder, remove, split, expand, or
redirect later work.
