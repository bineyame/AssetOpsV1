# Architect request: W4-01 and W3-01 build specs, with full pre-build closure

You are the AssetOps Architect. First read:
- `.ai/ROLE_CONFIG.md`, in full, especially the readiness gate, "Mockup drives the design; implementers never decide", the expanded dry-read rule, and "Token Efficiency";
- `.agent/post-W2-sequence.md`;
- the new packets `tasks/W4-01-work-case-core.md` and `tasks/W3-01-estate-claim-action-roots.md`;
- the format of the closed W2 build specs: `.agent/W2-07-build-spec.md`, with its concrete-artifact closure and reconciliation;
- the merged code on main that these slices consume, namely the Findings index, Action reads, currentness and selected reads, the S4-05 classifier, the tab guard, the shell and the registry;
- the v69 mock screens named in each packet.

Write `.agent/W4-01-build-spec.md` and `.agent/W3-01-build-spec.md`. Each must cover:
- spec commits;
- schemas, with the literal migration body, constraints, indexes and downgrade;
- the domain model and state-transition tables, including unreached states;
- APIs, with literal JSON request and response examples, the refusal table (403/404/409/422/503 codes and copy) and cursor rules;
- currentness and provenance, using exactly the merged W2 DTO names;
- fixtures;
- named tests;
- per-panel layout, with measured mock heights, the ≤1.3x budget, column widths and wrapping, chip tones, and every user-visible string with its source field, including null and missing copy;
- tab-inventory guard changes, stated as an exact multiset;
- updates to existing test counts.

Do this as a full implementer dry-read of every commit, so the builder never stops on a question.

The W4-01 work-case contract is frozen once merged. State the frozen surface explicitly.

Also resolve the sequence's flagged `source_provenance` seam: one shared public DTO/enum mapping and provenance basis rule across W1, cold and EV, with exact-ID tests. Record it as decision `D-2026-10-20-shared-provenance-dto`, and say which slice implements it before W3-02 and W5.

Record the build specs as `D-2026-10-20-w4-01-w3-01-buildspec` in `.ai/DECISIONS.md`. Write only the two specs and the DECISIONS entries. Do not commit.
