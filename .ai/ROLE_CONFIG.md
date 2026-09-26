# Role Configuration

Roles are project responsibilities. Agent bindings are configurable defaults.

## Default Bindings

| Role | Default agent | Purpose |
| --- | --- | --- |
| Architect | Codex | Creates feature maps, causal sequencing, protected seams, and feature-to-task guidance. |
| Planner | Codex | Converts reviewed feature guidance into small UI-verifiable task definitions. |
| Implementer | Claude | Builds the active task, runs checks, and prepares the review packet. |
| Reviewer | Configurable independent agent | Reviews work independently from the author. |

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
codex exec "<the role brief>"
```

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

## Updating Bindings

Change bindings here when the team wants a different tool to own a role. Record
material changes in `.ai/DECISIONS.md` if they affect workflow, review
independence, or task ownership.

