# Architect fix round - A-finding-index (review RETURN M1)

You are the AssetOps Architect (Codex). Review `.agent/A-finding-index-review.md` (RETURN: M1 Medium; L1-L4 Low) of your resolution `.agent/architect-A-finding-index-answers.md` / `D-2026-10-15-a-finding-index`.

Amend (in place, short):
1. M1: a closed S3 source/Performance gate forbids `CURRENT` rows and any zero ("no Findings") claim, consistent with `finding_api.py:86-90,104-117` (409 `PERFORMANCE_CUTOVER_CLOSED`) and S5-01 (`STALE_PROJECTION`, no `ABSENT`). Decide: the index refuses with the same 409, or returns audit-only rows with the reason - pick one and state it. Add a closed-gate case to the `D-site-finding-index-empty` acceptance target (and any affected node) in the registry.
2. L1: define "complete discovery" concretely: every UTC-day window the selected window intersects plus neighbours reachable by the 20-minute continuity rule, each through its current selection seq; bound the selectable window length.
3. L2: S4-04 adds a new read; it must not change `findings_over` in place (used by `scheduling/health.py`, `scheduling/upstream.py`, `finding_read.py:617`).
4. L3: require a test that on the same basis the first index row is the S5-01 card Finding.
5. L4: fix `tasks/README.md:9` and the S4-04 outline wording that says A-finding-index is open; fix the registry evidence anchor casing to match sibling nodes.

Keep the registry valid (`node frontend/docs/architecture/check_v69_dependency_registry.cjs`). No code. Print a short summary.
