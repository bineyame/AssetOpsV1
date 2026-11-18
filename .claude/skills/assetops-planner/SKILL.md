---
name: assetops-planner
description: Use for AssetOps Planner work: convert reviewed feature guidance into small UI-verifiable task definitions.
---

# AssetOps Planner

Read `.claude/agents/assetops-planner.md` (role brief and binding check), then
the start path in `AGENTS.md`. The binding is whatever the bindings table in
`.ai/ROLE_CONFIG.md` says; this skill does not restate it.

## Output

One or a few task-ready vertical slices. Each names its outcome and the
UI-verifiable behaviour it enables, why it is the next causal step, acceptance
criteria, needed semantics, protected seams, focused checks, scope limits and
`USER_REVIEW_REQUIRED`, within `.ai/RULES.md` §5.
