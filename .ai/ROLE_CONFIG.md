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

