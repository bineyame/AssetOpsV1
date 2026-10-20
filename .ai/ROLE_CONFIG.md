# Role Configuration

Roles are project responsibilities. Agent bindings are configurable defaults.

## Default Bindings

| Role | Default agent | Purpose |
| --- | --- | --- |
| Architect | Codex; scoped Claude exception for the v6.9 site mock-up work on `arch/canonical-v69-pivot` (2026-10-06; see below) | Creates feature maps, causal sequencing, protected seams, and feature-to-task guidance. |
| Planner | Codex (Claude exception ended at the 2026-10-03 21:23 reset; see below) | Converts reviewed feature guidance into small UI-verifiable task definitions. |
| Implementer | Claude | Builds the active task, runs checks, and prepares the review packet. |
| Reviewer | Configurable independent agent; Codex by default (see below) | Reviews work independently from the author. |

## Rules

- Keep role responsibilities stable even if the bound agent changes.
- Do not assume Planner, Architect, or Implementer means a specific vendor unless
  this file says so.
- Implementer may refine implementation steps, but should not redefine feature
  sequencing without Architect or user review.
- Reviewer must be independent from the agent that authored the implementation.
- Claude Code commands in `.claude/commands/` should read this file before
  acting so they can either run the role or prepare a handoff for the configured
  agent.

## Decision Requests Go To The Active Architect

Set by the owner on 2026-10-04 (verbatim in `.agent/owner-T028-closeout-2026-10-04.md`):
"for all decsion requests, let the active architect make them and inform me if
the architect wants me to weigh in as well with its justification and decision".

So the coordinator does not put decision requests to the owner. It sends them
to the Architect bound above, which decides, records the decision with its
justification, and informs the owner. Where the Architect wants the owner to
weigh in, it says so, giving its decision and justification, and the owner may
confirm or overrule. Owner acceptance of a slice (USER_REVIEW_REQUIRED) is not
a decision request and still goes to the owner.

## Scoped Claude Architect Exception: v6.9 Site Mock-ups (2026-10-06)

The owner set Architect to Claude for one piece of work: comparing the site
pages of the static mock-ups in `frontend/mockups/v69/` with v6.9 sections
8.18-8.26 (mini-grid), 8.28-8.31 (cold chain), 8.35 (readiness) and 8.36
(financials), and **updating the mock-up screens** with the enhanced version.
Owner text verbatim: `.agent/owner-v69-site-mockup-comparison-2026-10-06.md`.

- Extended by the owner the same day (follow-up 2 in the same file): EV
  recommendations, interactive site selection across mini-grid, cold chain
  and EV, a date-range selection bar, and the site single line diagram.
- Extended again (follow-ups 3-6 in the same file): beyond the site pages to
  the global Assets (incl. warranty/vendor economics, registration/edit),
  Findings, Evidence, Work (Actions, Incidents, Maintenance, Operational
  records) and a limited-demo Settings area of the mock-ups, and site
  creation (form, template, batch upload; follow-up 8).
- Scope: branch `arch/canonical-v69-pivot`, mock-up files only. Backend,
  frontend app, gateway and simulator realization planning stay Codex-bound.
- For this scope the Architect also edits the mock-up files directly (owner
  instruction); the usual Architect/Implementer split does not apply to them.
- Outputs state they were produced by Claude under this exception.
- Revert this row to plain Codex when the owner accepts the enhanced mock-ups
  or says so.

## Architect, Reviewer And Planner Were Claude Until 2026-10-03 21:23

Ended: the reset passed and the rows above are Codex again (reverted
2026-10-04). Retrospective Codex reviews are queued in
`.agent/coordinator-handoff.md`. The original record follows.

On 2026-09-30 Codex hit its usage limit during an Architect review of the T025d
cockpit layout and playback flicker, with reset at 2026-10-03 21:23. The user
set **Architect** and **Reviewer** to Claude until that reset:
`assetops-architect` and a fresh `assetops-reviewer` subagent do the work
directly. Later the same day the user extended this to **Planner**:
`assetops-planner` does the work directly, following the same guidance a Codex
Planner would (this file, `.ai/PLANNING_GUIDANCE.md`, the task conventions).

Revert all three rows in the table above when the reset has passed. Until then,
every Architect pass, Planner task definition and review report states it was produced by Claude under
this exception, so a later reader can decide whether a judgement should go back
to Codex. Reviewer independence still applies: a fresh reviewer instance, never
the implementer.

**Nothing waits for Codex** (owner, 2026-10-01): "we do not wait for codex
review, codex will review what is available to review when it returns." Every
round in this window, first reviews and contract moves included, goes to a fresh
Claude reviewer and the slice proceeds. After the reset Codex reviews,
retrospectively, the slices reviewed only by Claude here: T025e (live-follow
delta and merge mechanism), T025f (template fingerprints and lineage) and T025g
(scenario-site contract, including the no-move contract reading that reversed
the earlier 9 -> 10 clause).

## Architect Was Temporarily Claude, And Is Codex Again

On 2026-09-24 the user set Architect to Claude because Codex had exhausted its
usage limit twice in one day while the task queue waited on an Architect
review. That entry said to revert when capacity allowed. Codex capacity
returned at 18:21 the same day and the binding was reverted at 18:53, so the
exception is closed and the rule below applies again without qualification.

Two Architect passes were produced under the exception, both on
`arch/queue-review-feedback` and both merged: the queue resequencing at
`2970d74` and the hardening-gate removal at `e02d267`. A later reader checking
who authored them should know they were Claude by an explicit, recorded
decision rather than by the coordinator routing around this file.

The lesson worth keeping is the one the exception was written to respect: when
a binding has to change, change it here first and then act. Routing around a
control is worse than the mistake the control prevents.

## Invoking A Codex-Bound Role

A role bound to Codex is run by invoking Codex, not by dispatching the
same-named Claude subagent and merging what it returns. Codex is on PATH and
runs non-interactively:

```
codex exec "<the role brief>" < /dev/null
```

Always close stdin (`< /dev/null`). Without it, `codex exec` can block on
"Reading additional input from stdin" indefinitely; on 2026-10-18 this stalled
an Architect call overnight.

**The obligation is the coordinator's, not the subagent's.** On 2026-09-23 the
Architect correctly flagged three times that it was producing Architect output
while this file bound the role to Codex. Each time the coordinator relayed the
flag to the user as a question and merged the output anyway. A subagent noticing
a binding violation is not a control, because it has already done the work by
the time it can tell anyone. The control is that the coordinator invokes the
bound tool in the first place.

So: before dispatching `assetops-architect` or `assetops-planner`, check the
binding above. If it is Codex, run `codex exec`. The Claude subagents of those
names refuse Codex-bound work rather than producing it.

## The Reviewer Binding, And Its Backup

The Reviewer is **Codex by default**. When Codex is unavailable - usage limit,
outage, or a reset hours away - the backup is a **fresh Claude
`assetops-reviewer` subagent**, and the substitution needs no permission. A
slice waiting a day for quota is worse than a slice reviewed by the weaker of
two independent readers.

**Independence is the rule the backup must not break.** The backup is a NEW
agent instance. It is never the agent that implemented the slice, and never
that agent resumed with a different instruction. An implementer asked to
review its own work will confirm it, which is why the binding exists.

State in the report which reviewer produced it. A Claude review of Claude
implementation is genuinely weaker than a Codex one on the same slice, and a
later reader deciding how much weight to give a verdict needs to know which
they are reading. Where the substitution happened because of quota, say so and
say what was left unjudged, so the question can go back to Codex if it matters
enough to wait for.

## Which Reviewer For Which Round

Set by the user on 2026-09-26 to conserve Codex quota, which has been the
binding constraint on this milestone three times. This is not the same as the
backup rule above: it applies whether or not Codex is available.

**Codex reviews discovery.** The first review of any slice, a contract version
move, a new mechanism or a restructure, and any round where the Implementer had
to choose between legitimate treatments. T020B's R1 was that round - state a
rule for unaligned windows or refuse them at setup - and it needed the stronger
reader.

**A fresh Claude `assetops-reviewer` reviews verification.** A correction round
where an independent reviewer has already named the defects and the fix needs
no design choice: prose, docstrings, claim corrections, test assertions,
deletions. The job is confirming the named items closed and nothing else moved.
Fresh rather than resumed, because there is no context worth preserving for
checking named sentences and a clean reader is worth more.

The honest risk, recorded so it is not discovered later: this relies on the
previous review having found everything discoverable in that area. Four
consecutive rounds on T020B each found something the last missed, which is the
argument against cheap re-reviews. **So a Claude verification pass that finds
something unexpected is a signal to escalate that round back to Codex, not a
cheap verdict to accept.** Finding an unnamed defect means the round was
discovery after all and was misclassified.

Two classification traps worth naming, both seen on T020B:

- **A correction round can widen under the Implementer's hand.** The R1a/R1b
  round was three sentences and a deletion when dispatched; it came back having
  also corrected an unnamed fourth sentence and added a property-based guard
  over thirteen windows. Classify on what came back, not on what was sent.
- **"Small" will drift to "everything" if it is not tested against the two
  lists above.** The question is not how many lines changed. It is whether a
  reader had to decide anything.

## Owner Review Routing From S3 Onward (2026-10-11)

Owner (verbatim, `.agent/owner-review-routing-and-merge-2026-10-11.md`): "codex usage optimizaion is important, so keep the same arragment for S2 going forward". For every slice from S3 onward: a fresh Claude `assetops-reviewer` does the slice's first review and every re-review; small written-list fix rounds run on a Sonnet implementer; one batched Codex review covers each milestone's slices together at the milestone's end; Codex Architect/Planner questions are batched rather than sent per question file. This overrides "Codex reviews discovery" below for per-slice first reviews; Codex remains the Architect, the Planner and the milestone reviewer.

## Do Not Write The Review In The Brief

Recorded on 2026-09-26 at the user's instruction, because this project had
been doing the opposite. Reviewer briefs had grown to eight numbered questions,
each naming the thing to judge and supplying the arguments on both sides. That
is not a brief; it is a draft verdict with blanks. A reviewer steered to eight
questions inspects eight things, and the ninth - the one nobody thought to ask
about - is the one that reaches production.

A brief gives the Reviewer:

- the target: branch, commit, spec, packet, and where prior reviews live;
- the standing criteria it is reviewing against, which live in the task file
  and this project's records, not in the brief;
- **what has already been run and verified**, with results, so quota is not
  spent re-running a green suite. This is factual and does not steer;
- the constraints: do not merge, do not fix, where to write, what not to touch.

A brief does **not** give the Reviewer:

- an enumerated list of what to judge;
- the arguments for or against a conclusion;
- which findings the coordinator considers important;
- a named preferred outcome, or a hint of one.

Pointing at an artifact is not steering; summarising what that artifact says is.
Where a genuine question must be asked - a decision only the user can take, a
constraint the Reviewer cannot infer - ask it plainly and separately, and do not
dress an opinion as a question.

The Implementer's packet already states its own uncertainties and residual
risks. That is the right channel for "look at this": the author declaring what
it is unsure of, in a document the Reviewer reads anyway.

## Sort Findings Before Forwarding Them

Recorded on 2026-09-26 after the user asked whether the Reviewer was applying
`D-2026-09-22-milestone-speed-over-purity`. It was; all three T020A1 reviews
cited it, and Codex used it to carry an HTTP-reachable 500, five overflow
sites and several residuals rather than block on them. **The coordinator was
the leak.**

That decision's stopping rule is narrow. Stop only for a defect expensive to
reverse, a claim that would mislead an Implementer, or a decision only the user
can take. **Everything else is recorded and carried.** A Reviewer that rates a
finding low and does not demand it has already applied the rule; forwarding it
as fix work overrides the Reviewer in the direction the decision forbids.

So when a review returns, the coordinator sorts every finding into block or
carry against those three conditions before putting any of it to the user, and
says which is which. A finding that is carried goes to
`.ai/MILESTONE_REVIEW_BACKLOG.md` with the reason, not into the next round.

T020A1 is the case to remember: five implementation rounds and three review
passes, of which two rounds closed comment counts, a docstring and a Draft
count that had drifted. Each was real. None was a reason to reopen a slice.

## Using Codex Efficiently

Codex quota is **account-level and shared across every model**. On 2026-09-24
it was exhausted twice in one day, the second time mid-review, and switching
to `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-sol` and `gpt-5.5` all returned the
identical limit with the identical reset time. **You cannot route around an
exhausted limit by changing model.** The only lever is spending less per call,
before the limit is reached.

What it cost that day, measured from the run logs:

| Pass | Tokens | Shell calls | Started |
| --- | --- | --- | --- |
| Reviewer pass 1 | 145,247 | 31 | cold |
| Reviewer pass 2 | 145,568 | 38 | cold |
| Reviewer pass 3 | 25,259, then died | 5 | cold |

Pass 2 spent 145k tokens re-deriving what pass 1 had already established.

### Resume instead of restarting

`codex exec resume <session-id> "<follow-up prompt>"` continues an existing
session with its context intact. `--last` resumes the most recent. The session
id is printed in the header of every run, so **capture it whenever a Codex
role may be returned to** - which is every review, because a review that finds
defects is returned to by definition.

A second pass on the same slice is a follow-up, not a new engagement. Resume
it and say what changed. Start cold only when the subject is genuinely
different or the earlier session would mislead.

**`resume` does not take the same flags as `exec`, and this cost two failed
invocations on 2026-09-25 before it was pinned down.** Two rules:

- Options go **before** the session id: `codex exec resume [OPTIONS]
  <session-id> "<prompt>"`. After it they are parsed as the prompt.
- **`--sandbox` does not exist on `resume`.** Pass it as config instead:
  `-c sandbox_mode="workspace-write"`. `resume` accepts `-c`, `--last`,
  `--all`, `-m`, `--skip-git-repo-check`, `--json`, `-o` and a few others;
  run `codex exec resume --help` rather than assuming a flag carries over.

The working form, verified:

```
codex exec resume -c sandbox_mode="workspace-write" --skip-git-repo-check   <session-id> "<follow-up prompt>" < /dev/null
```

Both failures were argument parsing, rejected before any model call, so they
cost seconds and no quota. The point of recording them is that guidance which
fails on first use is worse than none.

A session resumes across a quota interruption: the third-pass review that died
mid-run at its usage limit was resumed the next day into the same session id
with its context intact.

### Match the model to the work

`-m <model>` selects one. `gpt-6-astra` is the default and the most expensive;
`gpt-6-sol` is the workhorse coding model; `gpt-6-luna` is the cheap one. Full
list: `gpt-6-astra`, `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`,
`gpt-5.6-luna`, `gpt-5.5`.

Reserve Astra for genuine architecture and review judgement. Mechanical passes
- a fix round against a written list, a routine Planner expansion, a
consistency sweep - do not need it.

### Never spend a full session on a probe

`~/.codex/config.toml` sets `model_reasoning_effort = "high"` globally, while
the models' own default is `low`. A one-line availability probe therefore runs
at high reasoning. If you must probe, use
`-m gpt-6-luna -c model_reasoning_effort=low`. Better: attempt the real work
and detect the limit from the error, which costs nothing when the limit is
already hit.

### Put verification in the brief, not in the session

Every fact the brief states is work the session does not repeat. Say what you
already ran and what you already verified - test counts, check results,
confirmed line numbers - and say plainly that repeating it is not wanted.
Ask Codex for judgement, not for re-running a green suite.

### Invocation mechanics that have already gone wrong

- **Pass the prompt as an argument, never on stdin.** `codex exec ... - < file`
  blocked for three hours with no output on 2026-09-23. Always redirect
  `< /dev/null`.
- **Do not double-background.** `nohup codex ... &` inside an already
  backgrounded call returns instantly, and the harness reports a completion
  that has not happened. Background the call once.
- **A branch carries a snapshot of these rules.** A session started on a task
  branch reads that branch's `.ai/`, not main's. Merge main into the branch
  before a review if a rule has changed.

## Using The Claude Implementer Efficiently

Set by the owner on 2026-09-29 after T023, T022B and T024 each cost 80-200M
re-read tokens and one to three hours. Measured from the transcripts: cost is
context size times turns, and context grew from resumed agents and from source
code read whole into context. The agent's own rules are in
`.claude/agents/assetops-implementer.md` "Context budget"; these are the
coordinator's:

- **A fresh implementer per build and per fix round. Never resume one.**
  T024's build started at 209k tokens because the read-only planning agent was
  resumed; T023's fix rounds started at 458k. If a slice needs a planning pass,
  the planner writes its plan to `.agent/T0NN-implementer-plan.md` and a fresh
  agent builds from that file.
- **Fix rounds run on Sonnet** (`model: sonnet` on dispatch), briefed with the
  review file and the findings to fix. New slices stay on the session model,
  where design judgement matters.
- **Keep slices small.** A task the implementer sizes at several times a
  previous slice is a split candidate before it is built, not after.
- **Build large slices in phases, a fresh agent per phase.** Set by the owner
  on 2026-09-29 after T025a: bounded reads cut read volume by about two thirds,
  but 508 turns still took context to 467k and cost 142M re-read tokens,
  because cost grows with the square of the turn count. A slice beyond one
  focused change is dispatched as phases (for example contracts and core, then
  model and setup, then Lab and frontend). Each phase ends with committed work
  and a short handoff at `.agent/T0NN-phase-N-handoff.md` (what landed, file
  anchors, what is next, open risks); the coordinator dispatches a fresh agent
  for the next phase from that file. Full suites and the packet belong to the
  last phase.
- **Hand off at about 120k context.** Set by the owner on 2026-10-02 after
  usage showed 66% of tokens spent above 150k context and 67% in implementer
  subagents. An implementer that nears 120k commits what is safe, writes its
  handoff and stops, even mid-phase; a fresh agent continues from the handoff.
  The coordinator plans phases so that none is expected to reach that size,
  splitting a phase into sub-phases (2a, 2b) rather than letting one run long.
- **Backend tests: focused per phase, full once per slice** (OPS-01,
  `backend/TESTING.md`). Each phase runs the focused and adjacent backend files
  it touched; the real-Postgres full suite runs once per slice, on the final
  revision, with the guide's normal command and JUnit zero-skip check.
  Reviewers (Claude or Codex) cite that same-revision full evidence and run
  focused files; they rerun the full suite only for a finding that needs it.
  Before any full run start `tools/keep-awake-during-tests.ps1` and cap the run
  at twice its expected wall time; a run past the cap is stopped and reported,
  never waited on. One full suite on this machine at a time.
- **Mechanical sub-steps run on Sonnet.** Work fixed by an agreed contract or
  handoff - tests written against a settled interface, an AC-by-AC evidence
  pass, closeout records - is dispatched with `model: sonnet`, like fix rounds.
  Steps that decide a design stay on the session model.

## Token Efficiency Without Lowering Quality (owner, 2026-10-18)

Owner: be very efficient without compromising quality, in every session. Lessons
from W1 rework and W2-00..W2-03 (about 30-40% avoidable rework, then 15-20%):

- **All acceptance rules in the brief from the start.** Layout contract,
  recurring-defect checklist, height rule, plain-language rules, proof list.
  Never introduce a rule mid-build; it forces trimming passes on every slice.
- **Build specs answer the known question classes before coding.** A W2+ build
  spec is ready only when it fixes, against the actual code: identifier
  grammars and formats; exact fixture Site/Foundation values and how bindings
  are published; every seam with path:symbol; guard allowlists the new code
  must satisfy (rule 8 writers, sqlalchemy import allowlist, dependency
  direction); refusal codes; freshness/time references; UI empty/unavailable
  copy and the panel map; how Lab/run projections and stored artifacts look.
  W2-02 needed six question rounds because its first spec skipped these.
  Then the Architect does an **implementer dry-read**: walk the spec commit by
  commit against the real code, write down every question a mid-level
  implementer would have to ask (multiplicity such as per-connector channels,
  which component owns each device, new Foundation keys, readiness codes for
  each missing input, cadence sources, fixture Sites vs revisions, migration
  numbering against in-flight slices), and answer each in the spec. W2-05a
  stopped with eight such questions after the gate alone.
  The dry-read includes a **copy dry-read**: every user-visible string (labels,
  gap/empty/unavailable/refused copy, limitation and reason sentences, notices)
  and the exact response field that feeds it, per mock element. W2-04 commit 3
  left seven response fields empty for want of wording or shape.
  The dry-read covers **every** spec commit, not only the first, and also
  settles: JSON shapes/keys/types, a total order for same-time events, full
  state-transition tables including unreached states, hash input row forms,
  UI component choice with 403/404/503 copy, per-panel height budgets against
  measured mock heights with column widths/wrapping, chip tones, null/missing
  copy, and migration index/constraint/downgrade details plus existing-test
  count updates. W2-05b run 1 still stopped on 14 such questions. Before the first build run of any new
  build spec, a fresh Claude reviewer (Opus) dry-reads it as the implementer and checks it
  against merged code; the Architect closes every item, and a Sonnet check confirms closure.
  On 2026-10-20 this found 66 questions in the W4-01 and W3-01 specs before any code was written.
- **Mock measurements before the spec.** Codex cannot drive Chrome in its sandbox (W3-02, 2026-10-20). Before an Architect spec request, the coordinator runs `node tools/measure-mock-panels.mjs <out-dir> <screen-id>...` and commits the measurements as `.agent/<slice>-mock-measurements.md`. The request must cite that file for the 1440/390 panel budgets.
- **Size builder runs to one spec commit each**, with a handoff after each, so
  no run dies mid-commit and the next run reads only the handoff.
- **Model by risk.** First review of a new build and design-deciding work on
  the session model; fix rounds, re-reviews (scoped to prior findings) and
  mechanical steps on Sonnet. A capture- or copy-only fix may be verified by
  the coordinator directly (view the evidence, record a short verify note).
- **Serialize slices that edit the same shared UI files**; parallelize only
  disjoint work (backend vs frontend, different domains).
- **One full suite per round, only when no builder is running.** Do not rerun
  full suites after doc-, test- or CSS-only changes; rerun the touched files.
- **Batch Architect/Planner questions into one Codex call**, and fold a
  preemptive sweep of the slice's remaining commits into that same call.
- **No duplicate agents.** Check for a live agent on a worktree before
  dispatching; never reuse a worktree a reviewer is still using.
- **Mockup drives the design; implementers never decide (owner, 2026-10-18).**
  Every spec maps each mock panel, row, column and chip of each owned screen to
  its data source or an honest gap; no mock element is trimmed or redesigned to
  fit the backend. Any implementer choice the spec did not fix is a defect:
  reviewers flag it Medium (High if user-visible vs the mock), and the Architect
  rules it and amends the spec before merge
  (`.agent/owner-fidelity-and-design-ownership-2026-10-18.md`).
- **Test databases are owner-authorized (2026-10-18).** Agents may create and
  drop private `*_test` databases in the local `assetopsv1-postgres-1`
  container for tests, captures and fixtures; never non-test databases
  (`.agent/owner-test-db-authorization-2026-10-18.md`).
- **Briefs point to files; they do not restate them.** Coordinator replies to
  interim agent notifications stay to one line.

## Updating Bindings

Change bindings here when the team wants a different tool to own a role. Record
material changes in `.ai/DECISIONS.md` if they affect workflow, review
independence, or task ownership.

