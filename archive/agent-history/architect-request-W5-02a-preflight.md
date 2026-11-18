# Architect request: rule on the W5-02a pre-flight batch (K1a–K2b, 114 items)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Builder pre-flight and quiet-machine suites" and "Token Efficiency";
- `.agent/W5-02-build-spec.md` (K1a–K2b, closures and rechecks) and `.agent/W5-02-04-readiness-review.md`;
- the pre-flight list in branch `task/W5-02a-cold-action-root`: run `MSYS_NO_PATHCONV=1 git show task/W5-02a-cold-action-root:.agent/W5-02a-phase-handoff.md`.

W5-01b (`0032`) is built on `task/W5-01b-cold-scenarios`, and W6-01b (B1) on `task/W6-01b-maintenance`. Both merge before W5-02a starts. The mock screens are `cold-action` and `cold-work` in `frontend/mockups/v69/index.html`.

1. Rule on every item with literal artifacts. In particular:
   - readiness item 29: a generated-scenario registration path, cold parsing beyond `COLD-LAB-001`, and producible STALE/UNKNOWN modes. If it is still not producible, say exactly which unit and test defers it;
   - the head-pin tests moving from `0032` to `0033` (list them);
   - the S6 collision assertion;
   - `work/global_index.py` with a null `action_event_id`, and `postgres_work_store.py`;
   - `siteWorkCases.tsx` and the four `SiteActionFrame` tests;
   - the union-index fields for W1 battery rows;
   - the W4 list refusal messages and the default limit (match the code, or change it with the tests);
   - the probe names in `writer_guard_probes.py` format;
   - the trigger SQL and errcode, the case-link table and response, and the token prefix.
2. Restore the unlabelled departures from the mock to the mock: the W1 window form, the leftover W1 helper copy, the page-header subtitle, the empty-state markup and the `Actions` breadcrumb target. Label any true exception `MOCK DEVIATION`.
3. Gates. Confirm the order: W5-01b and W6-01b merge, then K1a, K1b, K1c, then K2a/K2b.
4. If more than about 6 builder-runs of work remain in this sub-slice, split it.
5. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w5-02-w5-04-buildspec`.

Write only `.agent/W5-02-build-spec.md`, `tasks/W5-02-cold-work.md` if the scope changes, and `.ai/DECISIONS.md`. Do not commit. End your output with: the key rulings in one line each, any split, every new `MOCK DEVIATION`, and any item left open.
