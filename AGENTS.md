# AssetOps Agent Guide

Start here:

1. Read `.ai/START_HERE.md`.
2. If no task exists yet, read `.ai/PLANNING_GUIDANCE.md`.
3. If an active task exists, read that task.
4. Read `.ai/PRODUCT.md` only when product semantics matter.
5. Read `.ai/ARCHITECTURE.md` only when architecture boundaries matter.
6. Read `.ai/DECISIONS.md` only when a current choice depends on prior decisions.

Default responsibility roles are Architect, Planner, Implementer, and Reviewer.
Their default agent bindings live in `.ai/ROLE_CONFIG.md` and may be changed
there when the project needs a different setup.

Do not work directly on `main`. Use one branch per vertical slice or task, such as
`task/T004-generator-runtime-site-page`.

Keep context small. Prefer reviewable vertical slices that produce observable
product behavior over broad horizontal subsystem work.
