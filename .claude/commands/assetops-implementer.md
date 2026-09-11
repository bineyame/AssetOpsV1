---
description: Run the AssetOps Implementer role for the active task.
---

Use the AssetOps Implementer role.

Prefer the `assetops-implementer` subagent/skill when available.

Read:

- `.ai/START_HERE.md`
- `.ai/ROLE_CONFIG.md`
- `.ai/PROJECT_RULES.md`
- The active task file
- `.ai/PRODUCT.md` or `.ai/ARCHITECTURE.md` only when relevant

If `.ai/ROLE_CONFIG.md` still binds Implementer to Claude, implement the active
task directly. If the binding has changed, prepare a handoff prompt for the
configured Implementer agent.

Build only the active task. Run relevant checks, including
`tools/check-agent-workflow.ps1` when governance files or task files changed.
Finish with the standard review packet.

$ARGUMENTS
