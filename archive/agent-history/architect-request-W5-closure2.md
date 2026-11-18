# Architect request: W5 closure round 2

You are the AssetOps Architect. The closure check `.agent/W5-closure-check.md` confirms 41 of 46 readiness items are closed. It found 7 open items in W5-01 (R1-R7) and 6 in W5-03 (V1-V6). Close each one in place in `.agent/W5-01-build-spec.md` and `.agent/W5-03-build-spec.md`, with a literal artifact verified against merged code.

Key items:
- **Registry rows:** write the full rows for review items 4 and 31, including `requires`, `layer`, `effort`, the architecture ancestor, and the data-kind gate per panel. Then APPLY them to a scratch copy, run `node frontend/docs/architecture/check_v69_dependency_registry.cjs` against it, and record that it passes. Assign the `v69-screen-ledger.json` edits to a named unit. Remove the double creation of nodes across C3 and C5.
- **Health:** rule on the S7 gateway panel and the `Health › Data sources →` link at `ColdFoundationViews.tsx:646` for both cold and EV Health, matching v69.
- **`DECISION_ATTESTATION_INVALID`:** use the status code the code actually returns (`model.py:34` returns 422).
- **Scenario window:** make it immutable per root, or rule how a correction handles it.
- **W5-01:** name the door-pair source, resolve the `ambient_temperature` role, add `LIMITED` to the `condition_state` enum or handle it explicitly.
- **W5-03:** settle `scheduled_seconds` for `weekly:[]` (zero or null, consistently) and give the UI literal for a declared-empty schedule.
- **Depth client files:** settle ownership of `ColdDepthClient.ts` and `evDepthClient.ts` so later page units may edit them.

Add rows to each spec's "Readiness closure" table. Append an amendment line to `D-2026-10-22-w5-01-w5-03-buildspec`. Write nothing else. Do not commit.
