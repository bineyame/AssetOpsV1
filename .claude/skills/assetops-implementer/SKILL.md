---
name: assetops-implementer
description: Use for AssetOps Implementer work: build the active UI-verifiable task, run checks, and prepare a concise review packet.
---

# AssetOps Implementer

The standing brief for this role - what to read and in what order, the work
standard, the checks, and how to finish - is
`.claude/agents/assetops-implementer.md`. Read it and follow it. It is kept in
one place so a dispatch does not have to restate it and cannot drift from it.

Default binding: Claude agent, configurable in `.ai/ROLE_CONFIG.md`.

In short: read the routing documents rather than the tree, build only the
active task, keep changes scoped, prove any guard you add can fail, run the
architecture and workflow checks plus the suites, typecheck and build, and
finish with the review packet in `.agent/`, the task at `Status: in_review`,
and `.ai/CODE_STATE.md` updated with what the slice settled.

Do not redefine feature sequencing, product semantics, or architecture seams
without Architect or user review.
