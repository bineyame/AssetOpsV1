---
description: Run the AssetOps Implementer role for the active task.
---

Use the AssetOps Implementer role.

Prefer the `assetops-implementer` subagent/skill when available.

The standing brief for the role - reading order, work standard, checks, and how
to finish - is `.claude/agents/assetops-implementer.md`. Read it first, then the
active task file named in `.ai/ACTIVE_CONTEXT.md`.

Read `.ai/ROLE_CONFIG.md` before acting. If it still binds Implementer to
Claude, implement the active task directly. If the binding has changed, prepare
a handoff prompt for the configured Implementer agent: point it at the standing
brief rather than restating the brief in the prompt, and add only what is
specific to this task.

Build only the active task. Run the checks the standing brief names, including
`tools/check-agent-workflow.ps1` when governance files or task files changed.
Finish with the standard review packet.

$ARGUMENTS
