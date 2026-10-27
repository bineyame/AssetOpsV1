# Role Configuration

Roles are project responsibilities. Agent bindings are configurable defaults.

## Default Bindings

| Role | Default agent | Purpose |
| --- | --- | --- |
| Architect | Codex (Claude exception 2026-10-22 08:52-13:00 ended; see below); scoped Claude exception for the v6.9 site mock-up work on `arch/canonical-v69-pivot` (2026-10-06; see below); scoped Claude exception for revision 3 of `Docs/demo-sprint/telemetry-integration-plan-claude.html` (2026-10-27; see below) | Creates feature maps, causal sequencing, protected seams, and feature-to-task guidance. |
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

## Scoped Claude Architect Exception: Telemetry Integration Plan HTML (2026-10-27)

Reopened again 2026-10-27 by the owner for revision 3 (adjustments plus bounded implementation tasks; owner text verbatim: `.agent/owner-telemetry-plan-feedback-2026-10-27.md`). Ends when revision 3 is delivered. Earlier: revision 2 delivered to the owner. Reopened 2026-10-27 by the owner for one revision of the same document (owner text verbatim: `.agent/owner-claude-architect-telemetry-revision-2026-10-27.md`). Ends when the revised document is delivered to the owner. First delivery ended the original scope; the original record follows.

The owner set Architect to Claude for one deliverable: the telemetry integration
plan (owner prompt `.agent/owner-telemetry-integration-plan-2026-10-27.md`), with
BeagleBone Black integration details, building on `modbustcp.html` and covering the
Waveshare ESP32-S3-RS485-CAN. Output: `Docs/demo-sprint/telemetry-integration-plan-claude.html`
on `plan/commercial-capability-assessment`, kept beside the Codex Architect's
`telemetry-integration-plan.html` for comparison. Owner text verbatim:
`.agent/owner-claude-architect-telemetry-2026-10-27.md`.

- The scope is that one HTML document. All other Architect work stays Codex.
- The output states that Claude produced it under this exception.
- This exception ends when the document is delivered to the owner. Then remove this row note.

## Scoped Claude Architect Exception: Commercial Capability HTML (2026-10-27) — ended

Ended 2026-10-27: the document, with the Implementer's questions worked in, was delivered to the owner. The row is Codex again. The original record follows.

The owner set Architect to Claude for one deliverable: an implementer-friendly,
code-grounded version of `Docs/demo-sprint/commercial-capability-readiness.md`,
written as `Docs/demo-sprint/commercial-capability-readiness.html` on
`plan/commercial-capability-assessment`. The Implementer then reads it and
sends open questions, and the Claude Architect works them in. The owner wants
to compare this output with the Codex Architect's. Owner text verbatim:
`.agent/owner-claude-architect-commercial-html-2026-10-27.md`.

- The scope is that one HTML document. All other Architect work stays Codex.
- The output states that Claude produced it under this exception.
- This exception ends when the document, with the Implementer's questions
  worked in, is delivered to the owner. Then remove this row note.

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

## Architect Was Claude Until The Codex Quota Reset (2026-10-22)

Ended about 13:00, when Codex accepted the retrospective request. The row is Codex again, and Codex has reviewed the Claude rulings (merge of `plan/retro-claude-arch`).

Owner (verbatim, `.agent/owner-claude-architect-2026-10-22.md`): "use a fresh
claude architect instead of codex until  the codex quota is reset". Codex hit
its usage limit at 08:52 on 2026-10-22 with the W5-01 C1 and W6-01 A1 ruling
requests ready. Until the reset, a fresh `assetops-architect` subagent does the
Architect work directly. Every ruling it writes states that Claude produced it under
this exception. After the reset the row reverts to Codex, and Codex reviews
those rulings retrospectively; the queue is in `.agent/coordinator-handoff.md`.

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
  Owner 2026-10-20 (`.agent/owner-test-suite-policy-2026-10-20.md`):
  (1) the full suite starts at the final revision **in parallel with the
  first independent review**, not before it; a failure still blocks merge and
  is routed like a review finding. (2) A slice that changes no shared code
  (no existing module, guard, router/shell/registry or shared DTO) and no
  schema may skip the full suite: focused tests plus check-all suffice, with
  that scope recorded in the packet. Merges to main keep the full run.
  The default full-suite command is `tools/run-backend-suite-in-container.ps1`
  (OPS-03, about 42-50 min, cap 100 min); the host command in `backend/TESTING.md`
  is the fallback. Never run a bare `docker compose up` for tests: it can
  recreate the shared `assetopsv1-postgres-1`.
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
- **Never kill all browser processes.** A capture or measurement script stops only the Chrome process it launched, by PID or by its own user-data-dir. `taskkill /IM chrome.exe` is forbidden, because it closes the owner's and other agents' browsers (W3-01, 2026-10-21).
- **`git add -f` only on named `.agent/` paths.** Never run `git add -f .`, `git add -A -f`, or force-add a directory. Doing so commits ignored build output (`node_modules/`, `dist/`, `*.tsbuildinfo`). W4-02 committed about 5,300 `node_modules` files that way (2026-10-21). Before every commit, `git diff --cached --stat` must show no ignored paths.
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
- **Departure categories and register (owner, 2026-10-23,
  `.agent/owner-departure-categories-2026-10-23.md`).** Every departure from the v69
  mock carries one category code in its `MOCK DEVIATION` label and one row in
  `.agent/mock-departure-register.md`. The row records the ID, screen, mock element,
  what is shown instead, the category, the reason, the owning unit and the status.
  - **D1 Data or feature not available.** Show an honest gap inside the mock's
    structure. It becomes a future-work candidate, which the owner prioritises
    at the walkthrough.
  - **D2 Improvement on the mock** (better organisation, precision or clarity).
    Flag it to the owner at the walkthrough for approval or reversal.
  - **D3 Structural oversight by the Architect or Planner** (a missed or altered
    mock panel, element or order). This is a defect, not a deviation: correct it
    before merge. A reviewer finding one is High.
  - **D4 Mock placeholder content** (illustrative text that would be false for real
    data). Replace it with real data or an honest gap; inform the owner only.
  - **D5 Temporary, because of build order.** Name the unit that resolves it; that
    unit's review verifies it is resolved.
  - **D6 Technical constraint** (guard or platform). Rare; list the alternatives
    considered. The owner is informed, and the Architect prefers changing the
    constraint over the mock.
  The Architect assigns the code. The reviewer checks the code and the register row,
  and an unlabelled or uncategorised departure is High. The walkthrough index groups
  departures by category.
- **Builder pre-flight and quiet-machine suites (owner, 2026-10-22,
  `.agent/owner-speed-preflight-quiet-suite-2026-10-22.md`).**
  - **Pre-flight.** Before writing any code for a sub-slice, the builder dry-reads
    every unit card in it against main and the v69 mock. It lists every point the
    card leaves open: files, literals, producers, guards, broken tests and mock
    differences. It commits that list as one batch to the handoff and stops. The
    coordinator sends the batch to the Architect as one request, and the builder
    starts code only after those rulings merge. A mid-build stop afterwards counts
    as a missed pre-flight item, and a missed item is recorded in the readiness lessons.
  - **Quiet-machine suites (refined 2026-10-23,
    `.agent/owner-build-during-suite-2026-10-23.md`).** One full backend suite runs
    at a time. While it runs, builders keep writing code and may run database-free
    unit tests, type checks and check-all. They hold Postgres-backed tests, browser
    captures, the full vitest run, production builds and any second suite until the
    suite ends, then run them in one batch. Spec, Architect and review-reading
    work proceeds freely.
- **Tiered testing (owner, 2026-10-22, `.agent/owner-tiered-testing-2026-10-22.md`;
  refines the 2026-10-20 suite policy).**
  - **Each unit:** its focused tests.
  - **Each slice merge, scoped regression:** every backend test file for the changed
    packages; every test file importing a changed shared module (found by grep on
    the module name); the full frontend vitest suite; and check-all. The packet
    records the selected files and how they were chosen.
  - **Full backend suite before merge** only when the slice adds or changes a
    migration or schema, or touches shared plumbing: `main.py`, `*/composition.py`,
    `tools/checks/*`, `tools/writer_guard_probes.py`, seed tools, or
    `conftest.py`/fixtures.
  - **Safety net:** a full backend suite on main after every 2–3 merges, run
    while builders work, so it stays off the critical path but on a quiet
    machine where possible. A failure is traced to that merge range and fixed
    before the next merge.
- **Both Architects (Codex and Claude) check every screen-affecting spec,
  ruling and design against the v69 mock (owner, 2026-10-22,
  `.agent/owner-architect-mock-fidelity-2026-10-22.md`).** Each ruling that touches a
  screen cites the mock element it implements (screen, panel, row/column/chip)
  and keeps its form: a chart stays a chart, a column heading stays the mock's.
  A guard, file list or backend gap is never a reason to trim or redesign a mock
  element. Change the file ownership or guard registration, or show an honest
  gap inside the mock's own structure, instead. An unavoidable deviation is
  labelled `MOCK DEVIATION` in the ruling. It states the mock element, why
  it cannot be kept, and the alternatives considered that would have kept it.
  The coordinator relays each deviation to the owner in plain words. Every
  Architect request carries this rule. Reviewers treat an unlabelled deviation
  as High.
- **Test databases are owner-authorized (2026-10-18).** Agents may create and
  drop private `*_test` databases in the local `assetopsv1-postgres-1`
  container for tests, captures and fixtures; never non-test databases
  (`.agent/owner-test-db-authorization-2026-10-18.md`).
- **Briefs point to files; they do not restate them.** Coordinator replies to
  interim agent notifications stay to one line.

## Build-Spec Readiness Gate For W5 And W6 (owner, 2026-10-21)

Owner decision, recorded in `.agent/owner-W5-W6-spec-readiness-2026-10-21.md`: "yes, apply that to W5 and W6".

- **Readiness gate.** Before any W5 or W6 build starts, a reviewer dry-reads the closed spec against main for every user-visible copy string, label, status/enum value, wire field and shape, ID source, link target and route, fixture producer, capture state and height cap. Every item must name a literal or a source. The Architect closes every open item, and a Sonnet check confirms none remain. Only then is the first build unit dispatched.
- **Size cap.** A slice with more than 6 build units, or with both a backend pipeline and more than 2 new pages, is split into two slices, each with its own review and merge.
- **Mid-build stops count against the spec.** Record each mid-build ruling round in the handoff. More than 2 rounds on one slice triggers a fresh readiness pass on the remaining units before continuing.

### W3/W4 lessons applied to W5 and W6 (owner, 2026-10-21)

The owner asked to "adopt best practices and learning for waves 5 and 6 for quality and speed". Each rule below cites the W3/W4 defect it prevents.

**Spec quality (before the readiness gate passes)**
1. **Guard-checked literals.** Every registry row, `mock_gaps` entry, copy string and nav entry in a spec is checked against the actual checkers: `check_v69_dependency_registry.cjs`, the missing-claim, vocabulary and navigation guards, and check-all. A literal that a guard would reject is not closed. (W3-03 r2 registry rows and P-2-1 copy both failed guards mid-build.)
2. **Worst-case content in measurements.** Mock measurements include each text slot's worst-case length at 390 px: long IDs, the longest gap or empty copy, and refusal overlays. The spec states the scroll or truncation rule per slot. (W4-03 Scenarios, Opportunity and Incidents, and the W3-03 empty card, all broke caps at capture.)
3. **Producible states.** Every capture state and persisted test variant names a real producer path, which the readiness reviewer has run or traced to its rows, with a pinned clock. A state with no producer is ruled up front as a pure or fake-snapshot test, or as an honest limitation. (W4-03 KOBO Alternatives, Opportunity supported and DB-time 409; W3-03 cold `normal` and P-1b-1..6.)
4. **One clock per fixture.** Each fixture states its frozen clock, and how every read and pin uses it. (W3-03 0b re-pin H1; W4-03 PR-11.)
5. **Consolidated unit cards.** After any ruling round, the Architect folds the rulings into the affected unit's section as one current card: literals, tests and reading index. Builders read one card, not a stack of appended rulings. (W4-03 builders read u1–u9c layers and ran out of context 4 times.)
6. **Mock-consistency pass.** The readiness reviewer checks the spec against the mock and against itself for contradictions. (W4-03 u5 breadcrumb vs mock; W3-03 L3 prompt-Site rule.)
7. **File ownership per unit.** Each unit names every existing shared file it may edit, and the lane that owns it. (W3-03 L1 implied edits.)

**Build and review flow**
8. **Unit size.** One builder run per unit: one to three commits, with a reading index of 4 sections or fewer. Split before dispatch, not after a context stop.
9. **Per-unit review for shared code or schema.** Any unit touching shared files, schema or a cross-slice seam gets an independent review before the next unit builds on it. Pure-UI units may batch into the final review. (W3-03's per-unit reviews caught H/M defects early; W4-03 deferred everything to one large final review.)
10. **Rulings in parallel.** Builder readings go to the Architect while the next unit builds. The builder applies the rulings at its next commit boundary.
11. **One full suite at a time, never alongside 3+ heavy builders.** (W3-02 had 2 load-timing failures.)
12. **Captures are part of the unit that builds the page,** not a separate late unit, so cap and state failures surface while the code is fresh.
13. **Builders stop every process they start** (gateway/dev servers, capture browsers) and drop their `*_test` DBs before reporting; worktrees are created after `.gitattributes` changes or re-checked out (`git ls-files --eol`), and every new byte-pinned fixture gets an `eol=lf` entry. The coordinator checks for orphaned `assetops_gateway serve` processes after each slice (2026-10-22: 214 orphans held about 2 GB).

## Modern UI/UX Guidance For UI Decisions (owner, 2026-10-25)

Owner: "for UI/UX related question, it is important to take inspiration from modern UI guidelines and techniques, this is for the architect as well as the implementer".

Architects, Implementers and Reviewers use [the UI/UX decision guide](../frontend/docs/architecture/ui-ux-decision-guide.md) for standing screen defaults, long-content and cap proofs, state and copy patterns, mock-deviation handling, and the builder's decide-versus-escalate boundary. Builders make covered choices without a decision request, cite the guide section under **Choices made** in their packet, and escalate only the exceptions named there; specific active rulings and the v6.9 mock still govern their named screens.

The Architect (UI rulings, cap fallbacks, copy) and Implementers (pre-flight defaults, choices where rulings are silent) ground UI answers in current guidance and practice (WCAG 2.2, Material 3, Apple HIG, GOV.UK/USWDS, Carbon, NN/g heuristics, responsive data-table patterns) and name the pattern relied on. Broadened the same day: "not just when there are questions but state of the art UI/UX should be used(within bounds of demo speed)". It is a standing quality bar for all UI work (Architect specs, Implementer builds, Reviewer checks): hierarchy, readable type, strong 390 px behaviour, WCAG 2.2 AA focus/keyboard, purposeful loading/empty/error states, scroll affordances, plain copy. Bounded by demo speed: prefer cheap local improvements; batch larger ideas as proposals. The v6.9 mock remains the layout spec; layout/content changes it would imply are proposed as labelled D2 departures. Detail: `.agent/owner-ui-ux-guidance-2026-10-25.md`.

## Updating Bindings

Change bindings here when the team wants a different tool to own a role. Record
material changes in `.ai/DECISIONS.md` if they affect workflow, review
independence, or task ownership.

14. **Line-ending check before every full suite (2026-10-23).** The command is
    `git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'`. The attribute sits in
    field 4, so an awk test on `$3` silently finds nothing. A main merge in a Windows
    worktree can rewrite LF-pinned golden files as CRLF; on 2026-10-23 this caused 8
    false failures. Delete and re-checkout every listed file before the run. Never
    kill processes by image name (`taskkill /IM node.exe`): stop only the PIDs you
    started.
15. **Rule layout caps once, with the worst case in view (2026-10-24).** W5-02 K2 and
    K3 each needed 3-4 Architect rounds about caps alone (447>440, 907>650, 664>650).
    The worst-case fixtures, five rows of 160-character text, never fit caps sized
    from the mock's one short row. In every pre-flight and review ruling, the
    Architect sizes each cap from the worst-case content, gives user-expanded
    states (all disclosures open) an explicit exemption up front, and states what
    happens if a remeasure still exceeds a cap. Builders flag likely cap misses in
    the pre-flight, not after captures.
