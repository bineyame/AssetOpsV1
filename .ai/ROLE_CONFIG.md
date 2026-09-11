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

## Updating Bindings

Change bindings here when the team wants a different tool to own a role. Record
material changes in `.ai/DECISIONS.md` if they affect workflow, review
independence, or task ownership.

