# T025g review, R1 verification - The run is the only join of scenario and site (S1)

Reviewer: Claude (Opus 5.5). This is a fresh reviewer instance. It did not
author any part of this slice and did not write the first review.

Binding: the Reviewer role is bound to Claude until the Codex reset at
2026-10-03 21:23 (`.ai/ROLE_CONFIG.md`). Codex reviews this slice
retrospectively after the reset.

Target:
- R1 commits `git log 3c37d60..HEAD`: `12b7bfe`, `8ea8a3a` and `dca8ce0`
  (head `dca8ce0`).
- Prior review `.agent/T025g-claude-review.md`.
- The packet's R1 section in `.agent/T025g-review-packet.md`.
- Task `tasks/T025g-run-binds-scenario-to-site.md`.
- Carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`, "Carried from T025g".
- Owner direction: fix F1 and F5; carry F2, F3, F4, F6 and the two named
  residual risks.

## Verdict: ACCEPT WITH CARRIES

F1 and F5 are fixed, and the carries are recorded faithfully. I found nothing
new in the R1 diff. The carried items stay open as recorded. F2 still needs
the owner or the Planner to amend AC6b's wording.

## F1: fixed

- **The fix:** `backend/assetops_backend/simulator_lab_api.py:653-658`.
  `scenario_public_summary` now renders `site_contract: null` when the block's
  `description` is `None`.
  - This is the first fix option the prior review offered.
  - The parser still accepts `site_contract: {}`, as
    `test_an_empty_site_contract_has_no_description` pins it.
  - The client check in `scenarioCatalogClient.ts:558` stays strict.
- **Detail is covered too:** `scenario_public_detail` spreads
  `**scenario_public_summary(scenario)` (`simulator_lab_api.py:665`), so the
  detail screen and run setup get the same null. `ScenarioFrame.tsx:909`
  already reads a null contract as "none".
- **Seam test:** `backend/tests/test_run_binds_scenario_to_site.py:483-500`.
  - It writes and compares `contract-fixtures/scenario-empty-site-contract.json`.
  - `frontend/src/shell/__tests__/scenarioEmptyContractSeam.test.ts` runs the
    real `isScenarioSummary` against that file.
  - This follows the existing pattern of `site-foundation-fetch-seam.json` and
    `fetchSeamContract.test.ts`. Neither side imports the other.
- **The tests are not vacuous:**
  - The backend asserts `summary["site_contract"] is None`. The pre-fix code
    rendered `{"description": None}`, so this assertion fails without the fix.
  - The frontend's second case shows that the client still refuses
    `{description: null}`. Without the backend fix, that is the shape the
    fixture would carry.
  - I did not re-execute the packet's two mutations. I read them as consistent
    with the assertions.
- **No stale pins:** no other backend, host or frontend test pins the old
  `{"description": null}` wire shape. I checked with grep.

## F5: fixed

- `.agent/scenario-site-targeting-architect.md:1` now reads "revision 3".
- `:235-236` now reads "owner signed off 2026-10-01".
- Both match what the prior review asked for.

## Carries: checked against the prior review

`.ai/MILESTONE_REVIEW_BACKLOG.md`, "Carried from T025g: four findings, two
residual risks":

- **F2, F3, F4 and F6:**
  - the severities match the prior review;
  - the file anchors match, and the entry notes they are "as of the review";
  - the reasoning matches;
  - each entry has a trigger.
- **F2's routing:** it is routed to the owner or Planner with the proposed
  AC6b wording, so it is not silently dropped.
- **The two residual risks:**
  - the picker reads each site's Foundation version once;
  - `test_every_shipped_scenario_is_v2_superseding_v1` hard-codes v2.

  Both are the ones the owner named, and they are recorded with triggers.
- **Not carried:** the prior review's third residual risk, an older build
  reading the new `site.template_lineage` run key. The owner's direction named
  two, and that risk was a reading of the parser, not a defect. I note it here
  only so that its absence from the backlog is a known choice. It is not a
  finding.

## Findings

None. The R1 diff is small and does what the prior review asked. I have
nothing to add to it.

## Checks I ran, serially, on `dca8ce0`

| Check | Result |
|---|---|
| `pytest backend/tests/test_run_binds_scenario_to_site.py -q` | 43 passed |
| `npm.cmd test -- --run` on `scenarioEmptyContractSeam.test.ts` and `fetchSeamContract.test.ts` | 2 files, 30 passed |
| `npx.cmd tsc --noEmit` (frontend) | clean, exit 0 |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `pytest backend/tests -q` | 1375 passed, which is the prior review's 1374 plus the new seam test |

- The targeted frontend run **did execute** in this session. The esbuild
  ancestor-directory sandbox failure did not occur.
- `git status` showed only the owner's untracked `Docs/` files, both before
  and after the runs.
- I did not read or touch `var/`.

## Not verified

- **The full frontend suite and `npm.cmd run build`.** I ran only the two seam
  files. The implementer reports 678 passed for `src/shell`. R1 adds one test
  file and changes no frontend source.
- **The `contract9_gate`.** I did not rerun it. R1 touches no contract, host
  or gate file, and `git diff 3c37d60..HEAD --stat` confirms this.
- **The packet's two mutations.** I did not re-execute them.
- **Live-stack checks: none, because R1 adds no layout-sensitive change.** F4,
  the layout evidence for the run header, stays carried as recorded.

## Residual risk

None beyond the carried items.
