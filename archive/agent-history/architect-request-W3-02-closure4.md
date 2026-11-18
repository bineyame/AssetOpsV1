# Architect request: W3-02 closure round 4 (post-W3-01 seam re-check)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W3-02-build-spec.md`, all closures and amendments;
- `.agent/W3-02-seam-recheck.md`: 27 open items (6 Blocker, 14 Should, 7 Nit) with evidence against main, plus 15 items W3-01 already delivered;
- `.agent/W3-01-build-spec.md`, whose rulings are now the merged code;
- `.agent/post-W2-sequence.md` (ownership).

Close all 27 with exact artifacts verified against main:
- B1: extend the shared estate parser and cursor for the evidence/money roots, with a typed refusal and no 500. Give the 3- and 5-part cursor markers.
- B2: the W1 `GENERATOR_SUPPORT` connection-taking reader, plus a one-row-per-day ceiling and typed gap roles.
- B6: re-plan the commit order. If Lane A prerequisite commits are needed for existing files, give them the W3-01 sequential-handoff pattern, with exact functions and files, each prerequisite reviewed separately.
- Strike the 15 delivered items, using a supersession index.
- Keep every mock slot.

Size every commit for one builder run, and keep each builder's reading load small. Put a short per-commit "read only these sections" index at the top of the closure.

Append the result as "Review closure 4 (2026-10-21)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
