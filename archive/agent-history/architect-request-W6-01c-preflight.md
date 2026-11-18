# Architect request: rule on the W6-01c pre-flight batch

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Builder pre-flight and quiet-machine suites" and "Token Efficiency";
- the W6-01c unit cards and §3.1 (including CL3, the retrospective and the W6-01b pre-flight rulings) in `.agent/W6-01-build-spec.md`;
- the pre-flight list in branch `task/W6-01c-request-overview`: run `MSYS_NO_PATHCONV=1 git show task/W6-01c-request-overview:.agent/W6-01c-phase-handoff.md`.

The list has 33 items, 17 of them blocking. Also read the W5-02 K4a and C2 ordering notes in `.agent/W5-02-build-spec.md`. The mock screens are `wr-overview` and `wr-record` in `frontend/mockups/v69/index.html`.

1. Rule on every item with literal artifacts: wire fields with sources (for example, Finding and Action hrefs in `work_detail`), the route's case-type rule, where the missing-CREATED 503 lives, how case-linked operational records are selected and coded, a single `known_at` rule for tab links (reconciling the spec, its example and W5-02), and which unit owns linking the maintenance list rows to the Overview (`links.detail`, `GlobalMaintenance.tsx`). Also give the REC links before E2 mounts `/operational-records`, the breadcrumb, Open site and loading/refusal h1 literals, a 403 capture producer, a historical capture cutoff distinct from current, and the C2 test that C3's tab promotion breaks.
2. Restore every unlabelled departure from the mock to the mock: the Work done Type/Asset/Linked action rows, the 6-step Lifecycle, Source, and C3's table rows and notice. Where a value has no source, show an honest gap inside the mock's own structure, or label a true exception `MOCK DEVIATION`.
3. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w6-01-buildspec`.

Write only `.agent/W6-01-build-spec.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the key rulings in one line each, every new `MOCK DEVIATION`, and any item left open.
