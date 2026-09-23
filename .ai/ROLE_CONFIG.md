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

## Updating Bindings

Change bindings here when the team wants a different tool to own a role. Record
material changes in `.ai/DECISIONS.md` if they affect workflow, review
independence, or task ownership.

