---
description: Prepare or run the AssetOps Planner role for UI-verifiable task definitions.
---

Use the AssetOps Planner role.

Prefer the `assetops-planner` subagent/skill when available.

Read:

- `.ai/START_HERE.md`
- `.ai/ROLE_CONFIG.md`
- `.ai/PROJECT_RULES.md`
- `.ai/PLANNING_GUIDANCE.md`
- The reviewed feature map, if it exists

If `.ai/ROLE_CONFIG.md` still binds Planner to Codex, prepare a concise Codex
handoff prompt containing the feature guidance and expected task output. If the
binding has been changed to Claude, perform the Planner work directly.

Planner output should define small UI-verifiable tasks under features. Do not
skip the feature map unless the user explicitly provides equivalent direction.

$ARGUMENTS
