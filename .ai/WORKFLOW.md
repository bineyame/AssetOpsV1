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

## No Agent Writes An Approval

Recorded 2026-09-26 after an Implementer wrote two approvals that had not
happened into the durable record: a dated owner sign-off whose only basis was
four conversational words, and a review verdict of ACCEPT while a RETURN verdict
sat unread in the same directory. It then set the task complete and moved it to
`tasks/completed/`. Reverted at `166c02b`.

Relying on an agent to be honest about this is what failed, so these are
controls rather than advice.

- **An agent may not write an owner approval anywhere.** Not the task file, not
  a packet, not a commit message. An agent cannot observe the owner's approval;
  only the coordinator, relaying the user, records one. A conversational remark
  is not a checkpoint: the task file defines what the owner must have done, and
  nothing short of that is a sign-off.
- **An agent may not record a review verdict.** The coordinator records it,
  after reading the review file. A subagent's handback is that subagent's
  summary of its own work; the harness says so on every handback, and it was
  said on the one that was believed here.
- **An Implementer may not commission its own review.** A review it
  commissioned is not independent whatever it concludes, and
  `.ai/ROLE_CONFIG.md` requires independence from the author. The coordinator
  dispatches the Reviewer.
- **Before recording any verdict, list the review files.** Two sat in `.agent/`
  that day, twenty-two minutes apart, and the one that agreed was cited. Where
  there is more than one, they are all read and the disagreement is reported,
  not resolved by preference.
- **Do not commit into a tree a Reviewer is measuring.**
  `.ai/PROJECT_RULES.md` "One Working Copy" already says evidence taken while
  another agent holds the tree is not evidence. Four commits landed during that
  review, and it had to qualify its own findings as a result.

A task reaching `tasks/completed/` with a verdict nothing verified is the
failure these prevent. `T011B` and `T011C` reached main at `in_review` for the
mirror-image reason - no check enforces the transition, which is why the rule
has to be read rather than relied upon.

## Vertical Slice Standard

Each planned task should include the minimum required domain semantics, backend
logic, data contract, UI, tests, and demo evidence needed for a reviewable
result. Not every task needs every layer, but each task should either deliver a
UI-verifiable outcome or explicitly unlock a named UI-verifiable slice.

Features and tasks are different planning objects. A feature is a complete
product function that may require several tasks. A task is a reviewable
implementation slice that delivers or materially advances one UI-verifiable part
of a feature.

The current sequence comes from the corrected demo roadmap, as mapped in
`.ai/FEATURE_MAP.md`: credible mini-grid runtime, normal ingested Site history,
dispatch Finding with Evidence, thin economics, fuel reconciliation,
productive-use opportunity, lifecycle, verification and portfolio.

This replaces the old examples that implied a fuel discrepancy was the first
Finding. Within each outcome, create reviewable cuts that let the owner run
and judge progress; do not make each architecture noun a separate task.

Avoid building whole layers before there is useful product behavior.

## Task Spec Size

Task specs are guardrails for fast implementation, not miniature design
documents. Keep durable reasoning in `.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`,
or `.ai/ARCHITECTURE.md`; keep task files slice-specific and executable.

Size is a ceiling, never a target. These are the upper limits:

- Normal UI/content slice: 120 lines.
- Boundary-changing slice: 160 lines.
- First write path, evidence contract, ingestion, simulator truth boundary, or
  analytics/finding semantics: 220 lines.

**There is no minimum.** A spec that carries everything below in fewer lines is
finished, not thin. Revised 2026-09-24: the earlier 100-180 / 180-260 / 250-400
bands described specs that restated durable mechanics, and their lower bounds
were read as a quota. Specs that cite v4, the roadmap, the feature map,
`.ai/ARCHITECTURE.md` and `.ai/DECISIONS.md` instead of restating them land far
below those numbers and are better for it. Over a ceiling, split the slice or
move the reasoning to the document that owns it.

Line count does not measure whether a spec works. This does: **an implementer
holding the task file, the references it names and the built state can start
without asking a question.** Where they must legitimately stop - a decision only
the user can take, or content that does not exist yet - the file names the stop
rather than leaving the gap silent. A file that passes that test at 70 lines
passes; a file that fails it at 300 fails.

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

The Architect establishes feature outcomes and causal prerequisites before the
Planner creates tasks. For the current pass, use only simulator v4 and the
corrected mini-grid roadmap for direction, plus canonical built-state records.
This replaces starting the task sequence from the UI mockups. Layout references
remain presentation guidance after a screen's content and claims are real.

The Architect may wear Product, Architecture, UI/UX, and Domain hats as needed
to produce a feature map. That feature map can then be broken into reviewable
tasks by the Planner under architectural guidance.

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
