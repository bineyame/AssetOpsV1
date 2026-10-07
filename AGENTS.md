# AssetOps Agent Guide

Start here:

1. Read `.ai/START_HERE.md`.
2. Read `.ai/ACTIVE_CONTEXT.md` and the active task, or `.ai/PLANNING_GUIDANCE.md` if no task exists.
3. For current S1-S7 work, use the current `frontend/docs/architecture/production-shaped-mvp.md`, `frontend/docs/architecture/production-shaped-mvp-technical-design.md`, and `frontend/docs/architecture/site-first-execution-plan.md`.
4. Use `frontend/mockups/v69/index.html` and its screen manifest as the interaction/content reference for the named Site or Lab surface. Implement only the supported slice with honest missing states.
5. Read `.ai/PRODUCT.md`, `.ai/ARCHITECTURE.md`, or `.ai/DECISIONS.md` only when compatible additional semantics, boundaries, or prior decisions matter.

The open T0xx queue and earlier feature maps are superseded planning history. `tasks/README.md` is the current S1-S7 queue; completed T packets remain built-state history, not implementation instructions.

Default responsibility roles are Architect, Planner, Implementer, and Reviewer.
Their default agent bindings live in `.ai/ROLE_CONFIG.md` and may be changed
there when the project needs a different setup.

Do not work directly on `main`. Use one branch per vertical slice or task, such as
`task/S1-01-persisted-foundation`.

Keep context small. Prefer reviewable vertical slices that produce observable
product behavior over broad horizontal subsystem work.
