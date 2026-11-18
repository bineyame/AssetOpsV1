---
description: Run the AssetOps Implementer role for the active task.
---

Use the AssetOps Implementer role. Prefer the `assetops-implementer` subagent
or skill when available.

The standing brief is `.claude/agents/assetops-implementer.md`. Read it first,
then the spec the dispatch names (or the active lane in `.ai/NOW.md`).

Read the bindings table in `.ai/ROLE_CONFIG.md` before acting. If it binds the
Implementer to Claude, implement directly. Otherwise prepare a handoff prompt
for the configured agent that points at the standing brief and adds only what
is specific to this task.

Build only the active task, run the checks the brief names (including
`tools/check-agent-workflow.ps1` when governance or task files changed), and
finish with the review packet.

$ARGUMENTS
