# Architect request: rule on the W5-01b pre-flight batch (C4–C5)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Builder pre-flight and quiet-machine suites" and "Token Efficiency";
- the C4 and C5 cards and the shared sections in `.agent/W5-01-build-spec.md`;
- the pre-flight list in branch `task/W5-01b-cold-scenarios`: run `MSYS_NO_PATHCONV=1 git show task/W5-01b-cold-scenarios:.agent/W5-01b-phase-handoff.md`.

The list has 47 items. W5-01a code is on `task/W5-01a-cold-selected-depth`, built and reviewed, and merges before W5-01b starts. The mock screen is `cold-scenarios` in `frontend/mockups/v69/index.html`.

1. Rule on every item with literal artifacts: file lists, wire fields, copy, producers with working clocks, guard edits, and the tests that break. In particular:
   - P-C4-1: the 16 backend test files that pin `0030` as the latest head, with the exact edits, including the downgrade paths;
   - P-C5-6/7: the W1/T028 vocabulary scan bans "scenario"/"scenarios". Give the guard or scan change and the `coldSiteViews.test.tsx` edit;
   - P-C4-2: a probe block placement in `tools/writer_guard_probes.py` that doesn't raise NameError, given `WRITER_CONTROLS` at :798 and `_work_control` at :860;
   - P-G-1: the branch base, which must be W5-01a merged first.
2. Restore the page heading, empty-state copy and panel subtitle to the mock (P-C5-1/2/3), along with any other unlabelled departure. Where a value has no source, show an honest gap inside the mock's own structure, or label a true exception `MOCK DEVIATION`.
3. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w5-01-w5-03-buildspec`.

Write only `.agent/W5-01-build-spec.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the key rulings in one line each, every new `MOCK DEVIATION`, and any item left open.
