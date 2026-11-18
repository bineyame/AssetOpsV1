# G-01 review packet - Mock-gap catalogue and orphan guard

Task: `tasks/G-01-mock-gap-catalogue-and-guard.md` (Status `in_review`, USER_REVIEW_REQUIRED: true).
Branch `task/G-01-mock-gap-catalogue-and-guard`, diff base `db98e54` (activation). Decisions:
`D-2026-10-12-mock-gap-closure-mechanism` sections 1-2, `D-2026-10-13-g-gap-packet-activation` (F2/F3).
Design and phase log: `.agent/G-01-handoff.md`. Questions: `.agent/G-01-questions-1.md` (Q1-Q4, defaults shipped).

Commits: `825e62b` phase a (schema, validator, next-work invariance), `f2945bd` phase b (typed MissingClaim and the
firmware placement), `87ccf63` phase c (orphan scan, baseline, check-all), `e976e08` evidence tool (run by the coordinator, see Layout evidence),
plus the closeout records commit.

## Outcome delivered

- Visible: the Readiness gateway panel has its own line, "Firmware not available yet: no reviewed source reports
  what firmware a gateway runs.", carrying `data-gap-id="G-readiness-gateway-firmware"` and
  `data-gap-placement="readiness.gateway.firmware"` (no visible ID, no firmware value). The older line now names
  only uptime trend, completeness and signal strength.
- The registry has a versioned `mock_gaps` catalogue that the checker validates. A typed UI mirror and component
  make an unknown gap or placement a compile error and a runtime throw. An AST orphan scan in check-all fails on
  unknown or unused placements, new untagged missing-capability copy (with file:line), and growth of the dated
  legacy baseline.

## Files materially changed

- `frontend/docs/architecture/v69-dependency-registry-pilot.json`: schema v3; `mock_gaps` holds one gap.
- `frontend/docs/architecture/v69-screen-ledger.json`: `readiness.gap_ids`.
- `frontend/docs/architecture/mock_gaps.cjs` (new validator).
- `frontend/docs/architecture/check_v69_dependency_registry.cjs` and `check_v69_ledger.py`: v3, plus the validator call.
- `frontend/docs/architecture/delivery_next_work.cjs`: validates and refuses on `mock_gaps`; reports `gap_catalogue`.
- `frontend/docs/architecture/test_mock_gaps.cjs` (new, 13 tests) and `test_delivery_next_work.cjs` (+2 tests).
- `frontend/src/ui/gapCatalogue.ts`, `frontend/src/ui/MissingClaim.tsx` and `frontend/src/ui/index.ts` exports.
- `frontend/src/sites/ReadinessOverview.tsx`: firmware split out and rendered through `MissingClaim`.
- Tests: `frontend/src/ui/__tests__/MissingClaim.test.tsx` (new, 3) and `siteFoundationRevision.test.tsx` (+3 in
  "G-01: the catalogued gateway firmware missing state"; the existing `NOT_YET` constant is updated to the split copy).
- `tools/checks/missing-claim-scan.mjs`, `missing-claim-baseline.json` and `test_missing_claim_scan.mjs` (new);
  `tools/check-all.ps1` gains 3 guards.
- `tools/g01-firmware-evidence.mjs` (new; 1440/390 CDP evidence; run, see Layout evidence).

## Acceptance criteria

1. **Versioned schema with `mock_gaps`: met.**
   - Every gap carries all the decision fields.
   - Allowed values are enforced: `missing_kind`, `status`, `source_status`, and `target_wave` as a wave key or `unplanned`.
   - `unplanned` requires `allocation: "pending owner review"`.
   - `owner_withheld` requires `owner_decision {evidence, reason, revisit_trigger}`.
   - `requires` may name only known non-product nodes or gaps. The firmware gap has `requires: []`, because no reviewed node proves it.
   - An open gap needs exactly one of: placements, or `unplaced_reason`.
   - Reuse is the same ID at several placements. One placement belongs to exactly one gap.
2. **Checker rejections: met** (`test_mock_gaps.cjs`, one test per rule).
   - Rejected: duplicate IDs, malformed IDs, IDs that collide with nodes or gates, and wrong prefixes.
   - Rejected: unknown screen, portion or element references, and a gap with neither a portion nor an element.
   - Rejected: invalid wave/status/source/allocation combinations, and unknown or product `requires`.
   - Rejected: gap cycles; open gaps without a placement or reason; "not built" on a W1 screen.
   - Rejected: a resolved gap without source, UI, visual and reviewed-by evidence, an existing source, a planned wave and resolved prerequisites. A resolved gap still placed in the UI also needs `ui_transition`.
   - Rejected: one-way portion `gap_ids` joins, and ledger `gap_ids` that differ from the screens' gaps.
   - Full coverage applies only to `gap_enrolled_screens`, which is `[]`. Readiness is not enrolled.
   - Real-registry mutations fail the checker, then were reverted: emptied placements gave `gap_placement`; ledger `gap_ids: []` gave `gap_ledger`.
3. **Typed missing-state component: met.**
   - `MissingClaim<G extends GapId>` takes `placement: GapPlacement<G>`. An unknown pair is a TS error (`@ts-expect-error` tests) and throws at runtime.
   - The gap ID is metadata only.
   - The mirror allows only `open` or `resolved_transition`, which the scan derives from `ui_transition`.
4. **Orphan scan in check-all: met.**
   - Scope: product `frontend/src`. Tests, `src/test` and comments are excluded.
   - Runtime copy (`unavailable`, `not recorded`) is not matched; see Q1.
   - Baseline: dated 2026-10-13, 16 entries, 16 occurrences. Each entry has a scope and a reason naming its G-02..G-05 backfill packet.
   - The counts must match exactly. Entries can be dropped, never added.
   - Growth is blocked two ways: against the merge-base baseline on `main` (absent at G-01) and against `SEED_CEILING = 16`.
5. **First real placement and tests: met in jsdom; 1440/390 not measured.**
   - Vitest: firmware with a populated (CURRENT) contact read; UNKNOWN, 503-unavailable, 404 and empty-gateway branches; reload by remount; exact `[data-gap-id]` set `== ["G-readiness-gateway-firmware"]`, equal to the mirror's readiness gaps.
   - Mutation tests fail on: an unknown UI ID; an unused open catalogue placement without `unplaced_reason`; new untagged copy (file:line); baseline expansion (new entry, higher count, over ceiling).
6. **next-work reads and validates but does not score: met.**
   - Fixture `mock_gaps never changes decision, eligible IDs, scores or path distances (G-01 F3)` runs next-work twice: with no catalogue, then with three open absent-source gaps, one linked to the core open portion `site:1#b`. Status, decision, sorted eligible IDs and every candidate's score, reach, blocks and path `d`/proof/portions are identical.
   - The fixture is non-vacuous. A mutation that adds 0.001 to the score when `mock_gaps` is present made it fail (34 pass, 1 fail). The mutation was then reverted.
   - The existing 33 ranking/refusal fixtures pass unchanged. K=10 and the W1 core paths are untouched.
   - The live report decision: `stop: G-01 is in_review`.

## Checks run (actual results)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 212 nodes, 11 linked pilot panels`.
- `python frontend/docs/architecture/check_v69_ledger.py`: `v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels`.
- `node --test test_delivery_next_work.cjs`: 35 pass. `test_mock_gaps.cjs`: 13 pass. `tools/checks/test_missing_claim_scan.mjs`: 10 pass.
- `node tools/checks/missing-claim-scan.mjs`: `passed: 1 tagged placement use(s), 16 baselined legacy occurrence(s)`.
- Real-tree scan mutations, each reverted:
  - Untagged probe string: `untagged_copy ReadinessOverview.tsx:513`.
  - Unknown gapId: `ui_unknown_gap` + `unused_placement`; tsc TS2322.
  - MissingClaim removed: `unused_placement` + `untagged_copy :300`.
  - Baseline count +1: `baseline_count` + `baseline_growth`.
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python .venv/Scripts/python.exe`: `All 9 guards passed` (Architecture seams, Navigation truthfulness, Agent workflow, Dependency registry, Delivery checker fixtures, Mock-gap catalogue fixtures, Missing-claim orphan scan, Missing-claim scan fixtures, Screen ledger). It was re-run after the records commit; see the final report.
- Frontend `npx vitest run`: 58 files, 1391 tests passed. `npx tsc --noEmit`: clean. `npm run build`: built (chunk-size warning only).
- Backend `pytest -q`: `1771 passed, 127 skipped`. Postgres was unreachable during the run, so Postgres-backed tests may be among the skips. G-01 changed no backend code.

## Layout evidence

**Run by the coordinator after Postgres returned; result `113/113 claims passed`.**
- Store: `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py --db assetops_g01evwalk --empty-db assetops_g01evempty --work-name g01-evidence prepare`, then `serve --port 8898 --web-port 5398 --empty-port 8899 --empty-web-port 5399` and Vite from `frontend/` (`$env:ASSETOPS_API_PORT="8898"; npm.cmd run dev -- --port 5398 --strictPort`).
- Tool: `node tools/g01-firmware-evidence.mjs http://localhost:5398 <dir>`. Result line: `113/113 claims passed; screenshots in C:\Users\assef\AppData\Local\Temp\g01-evidence-run`.
- Five contact shapes at 1440x1000 and 390x900: stale (a real stored read), and current, unknown, 503 and 404 (in-browser response substitutions, which prove only what the screen renders).
- Per run: firmware element exactly once with the expected gap id, placement and status `open`; exact text; visible and inside the panel; no horizontal scroll (`scrollWidth` = `innerWidth`); page `data-gap-id` set exactly `["G-readiness-gateway-firmware"]`; gap id not in visible text; no firmware value.
- Screenshots `g01-firmware-1440-stale.png` and `g01-firmware-390-unknown.png` were inspected: the firmware line is the last line inside the panel, with no clipping.
- Cleanup: servers stopped; `drop` removed both databases and the work folder (verified by a `pg_database` listing). The kill used a loose command-line pattern and also ended some unrelated processes.
- `tools/layout-evidence.mjs` was not run; the dedicated tool above covers the claim.

## Known deviations

- The firmware placement is one unconditional element, not one per branch (Q2). Every branch is still asserted.
- The copy is reworded so that no test-guarded "firmware v" pattern appears. The new wording is "what firmware a gateway runs".

## Residual risk

- The phrase set is narrow (Q1). Missing-capability copy phrased differently, such as "not tracked yet" or "not recorded", passes untagged until the set is widened.
- Same-name const detection is by identifier name across product files. A different const with the same name rendered outside `MissingClaim` would mark the literal untagged. That errs toward failing.
- The merge-base comparison is skipped while `main` has no baseline. The seed ceiling covers growth until G-01 merges.

## User-review focus

- Owner: the separate firmware missing-state line in Gateway status (`.agent/G-01-owner-walkthrough.md`, ports 8864/8865/5364/5365, private `assetops_g01walk`/`assetops_g01empty`). Acceptance stays conditional and does not make the panel or the screen Real.
- Reviewer: sample the catalogue -> ledger -> mirror -> `data-gap-id` joins, and re-run the mutation proofs above.

## Fix round 1

Against `.agent/G-01-review.md` (RETURN). Commits `fb8df38`, `68dfe64` plus the records commit.
- Finding 1: `missing-claim-scan.mjs` now reports `ui_duplicate_placement` (both file:line locations) when a (gapId, placement) pair is used more than once. Fixture `mutation: a catalogued placement used twice fails, naming both locations` in `test_missing_claim_scan.mjs` (11 scan fixtures pass).
- Demonstration on the real tree: a second `<MissingClaim gapId="G-readiness-gateway-firmware" placement="readiness.gateway.firmware">` wrapping "Uptime not available yet: probe." gave `[ui_duplicate_placement] frontend/src/sites/ReadinessOverview.tsx:492: G-readiness-gateway-firmware placement readiness.gateway.firmware is already used at frontend/src/sites/ReadinessOverview.tsx:491; ...`, `Missing-claim scan FAILED: 1 problem(s).`, exit 1. Reverted with `git checkout`; the scan then passed (1 tagged use, 16 baselined).
- Finding 2: resolved by the coordinator's evidence run (Layout evidence above).
- C8: `tasks/README.md` G-01 row set to in review. C1-C7 appended to `.ai/MILESTONE_REVIEW_BACKLOG.md` under "G-01 carries (2026-10-13)".
- Checks: vitest 58 files / 1391 tests passed; `tsc --noEmit` exit 0; `tools/check-all.ps1` All 9 guards passed; `test_delivery_next_work.cjs` 35 pass; `test_mock_gaps.cjs` 13 pass; scan fixtures 11 pass.
