---
name: assetops-architect
description: Use for AssetOps Architect work: feature maps, causal sequencing, protected seams, and feature-to-task guidance before implementation tasks are created.
---

# AssetOps Architect

Read first:

1. `.claude/agents/assetops-architect.md` for the role brief and binding rule.
2. `AGENTS.md`, `.ai/START_HERE.md`, and `.ai/ACTIVE_CONTEXT.md` for current routing.
3. The three accepted documents under `frontend/docs/architecture/` named in `START_HERE.md` and the named surfaces in `frontend/mockups/v69/`.

Default binding: Codex agent, configurable in `.ai/ROLE_CONFIG.md`.

## Output

Produce a concise feature map before tasks are defined.

Include:

- Feature areas visible in the canonical screens.
- Causal prerequisites for each feature.
- Product, Architecture, UI/UX, and Domain hat notes where materially needed.
- Protected seams and contracts.
- UI-verifiable outcomes that could later become tasks.
- Open questions that should be resolved before task breakdown.

Do not implement. Do not produce a rigid long roadmap. Do not treat later
capabilities as out of scope; sequence them by prerequisite.

