---
name: assetops-planner
description: Use for AssetOps Planner work: convert reviewed feature guidance into small UI-verifiable task definitions.
---

# AssetOps Planner

Read first:

1. `.claude/agents/assetops-planner.md` for the role brief and binding rule.
2. `AGENTS.md`, `.ai/START_HERE.md`, `.ai/ACTIVE_CONTEXT.md`, and `tasks/README.md` for current routing.
3. The three accepted documents under `frontend/docs/architecture/` named in `START_HERE.md` and the named surfaces in `frontend/mockups/v69/`.

Default binding: Codex agent, configurable in `.ai/ROLE_CONFIG.md`.

## Output

Produce one or a small number of task-ready vertical slice definitions.

Each task should:

- Identify the feature it contributes to.
- Name the UI-verifiable screen behavior it enables.
- Explain why it is the next causal step.
- Define acceptance criteria as observable UI behavior and required guarantees.
- Identify required product/domain semantics.
- Identify protected seams.
- List focused tests/checks.
- Mark whether user review is required.

For S1-S7, refine the accepted queue after predecessor review; do not revive the old feature map or T0xx sequence.

