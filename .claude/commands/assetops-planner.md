---
description: Prepare or run the AssetOps Planner role for UI-verifiable task definitions.
---

Use the AssetOps Planner role.

Prefer the `assetops-planner` subagent/skill when available.

Read:

- `.claude/agents/assetops-planner.md` and `.ai/ROLE_CONFIG.md`
- `AGENTS.md`, `.ai/START_HERE.md`, `.ai/ACTIVE_CONTEXT.md`, and `tasks/README.md`
- The three accepted documents under `frontend/docs/architecture/` named in `START_HERE.md`
- The named mock surfaces in `frontend/mockups/v69/index.html` and `screen-manifest.json`

If `.ai/ROLE_CONFIG.md` still binds Planner to Codex, prepare a concise Codex
handoff prompt containing the feature guidance and expected task output. If the
binding has been changed to Claude, perform the Planner work directly.

Planner output should define small UI-verifiable tasks under features. For S1-S7, refine the accepted queue after predecessor review; do not use the
superseded feature map or T0xx task order.

$ARGUMENTS
