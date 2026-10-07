---
description: Prepare or run the AssetOps Architect role for feature mapping and causal sequencing.
---

Use the AssetOps Architect role.

Prefer the `assetops-architect` subagent/skill when available.

Read:

- `.claude/agents/assetops-architect.md` and `.ai/ROLE_CONFIG.md`
- `AGENTS.md`, `.ai/START_HERE.md`, and `.ai/ACTIVE_CONTEXT.md`
- The three accepted documents under `frontend/docs/architecture/` named in `START_HERE.md`
- The named mock surfaces in `frontend/mockups/v69/index.html` and `screen-manifest.json`

If `.ai/ROLE_CONFIG.md` still binds Architect to Codex, prepare a concise Codex
handoff prompt containing the user request, relevant files, and expected feature
map output. If the binding has been changed to Claude, perform the Architect
work directly.

Do not implement code. Do not create implementation tasks until the feature map
is ready for user review.

$ARGUMENTS
