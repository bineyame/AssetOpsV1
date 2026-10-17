# W1-UX-06 phase 1 handoff

Branch `task/W1-UX-06` (worktree `AssetOpsV1-review3`, base main `a9b3b297`). Phase 1 is complete and committed. Nothing is merged. Packet: `tasks/W1-UX-06-closeout.md`. Ruling: `D-2026-10-17-w1-ux-06`, recorded in `.agent/architect-W1-UX-06-answers.md`.

## What landed (commits after `23afc7c4`)

| Commit | What |
| --- | --- |
| `134570eb` | Shared `expectStateLineVisible` now checks the as-of line against `AS_OF_PATTERN` (`frontend/src/test/productPresentation.ts`). The pattern accepts only a formatted UTC instant or `As of: time not recorded`. Three local substitutes now use the shared helper: Health `expectRefusedStateLine`, Foundation unavailable, and Site Work unread. `productStatus.test.tsx` imports the shared helper and checks the pattern in both directions. |
| `d2fb258d` | **One shared width check**, `tools/evidence-checks.mjs` (`widthGuard`, `widthVerdict`, `AS_OF_PATTERN`):<br>- It waits for `innerWidth === width` and requires `clientWidth` to be in `[width-20, width]`.<br>- If that fails, it retries once with a width-specific window (`Browser.setWindowBounds`) and the override re-sent.<br>- Every check records a claim naming both widths, and a failure throws before anything is measured.<br>- It is applied after every resize, page load, reload, history back/forward and capture resize, in every browser evidence script (inventory below).<br>- The w1-ux-01/03/05 claims use `AS_OF_PATTERN`.<br>- Guard: `tools/checks/test_evidence_checks.mjs`, added to `tools/check-all.ps1`. It covers unit cases, the frontend/evidence pattern being byte-identical, the inventory, and a proximity rule (every trigger is followed by a guard call within 6 lines). |
| `abab6111` | `source_health.receipt_lag()`: a report observed after its receipt gives `null`, never a negative lag. Nonnegative lag (including 0) is kept.<br>- Fixture `s7_health_api_contract.json`: `-90` is now `null`.<br>- Direct tests: rules (`test_s7_source_health_rules.py`), contract (`test_s7_health_contract_postgres.py`) and UI (`siteHealthBoundary.test.tsx`). |
| `2a5f7179` | The three backend no-set sentences now say "No channel-link set is in effect…" (`foundation_api.py`, `binding_service.py` x2). The `NO_CHANNEL_LINKS_*` overrides in `FoundationBindingsPanel.tsx` are removed, and the screen shows the server sentence as sent. Exact assertions: `test_s1_bindings.py`, plus the Readiness test in `siteFoundationRevision.test.tsx`, which asserts the readiness, bindings and snapshot text and that "signal binding set" is absent. |
| `90699341` | The Architect labels:<br>- Badge `Set up to report` with the configured tone, and the legend updated.<br>- Strip titled `Set-up steps`.<br>- Selected gateway: `In contact; its latest report is old` (CURRENT + OLD, trusted known age), or `In contact; its latest report's age cannot be confirmed` (unknown, untrusted or observed-after-receipt age). Both have tone limited, and the age is still shown separately.<br>- Unrecognised Readiness: headline `Set-up state not recognised`, the "Readings linked" step is `not-known`, and the badge is neutral and named.<br>- Health: an unrecognised summary code, or zero enabled outside `NO_REGISTERED_SOURCE`, gives `Gateway contact cannot be confirmed`.<br>- Tests cover old and unknown age, unrecognised Readiness and Health codes, all-disabled, none-registered, zero-enabled under another code, and no readiness-dependent step done on an unrecognised code. |

## Width-check inventory (packet "records the list")

**Guarded: 23 scripts.** All use `tools/evidence-checks.mjs`, and the inventory test enforces it:

- w1-ux-01, w1-ux-03, w1-ux-05
- v01a-foundation, v01b-lab-evidence
- s3-dispatch, s302-claim-limit, s4-finding, s402a-assumptions, s402b-fuel-cost
- s404-finding-index, s405-provenance, s408-assumption-history
- s5-overview, s502-overview-finding-list
- s601b-action, s602b-verification, s603-site-work, s701-health
- g01-firmware, g02-gap, lr01-money, layout-evidence

Notes on three of them:

- **s302** counts a width failure, logs it and skips that width's measurement.
- **layout-evidence** checks the width inside `visit()`, immediately before MEASURE.
- **g01** is guarded in `size`, `load`, capture and reload.

**Exempt, with its reason in the test: 1 script.** `run-store-browser-evidence.mjs` measures timing only at a fixed 1280 px and makes no layout claim. It is not cited by the walkthrough.

**Not yet present: `tools/w1-ux-02-evidence.mjs`.** It lands with W1-UX-02. Until it is guarded, its narrow claims are **not established**. The inventory test will fail on it after the merge if it sets a viewport without the shared guard, which is intended.

"Navigation" here means a document load or history traversal. In-app SPA clicks keep the same CDP override, so they are not re-checked.

## Proof (phase 1)

- **Real Chrome:** `node tools/evidence-checks.mjs --self-test` gave 4/4.
  - A real 390 passes (innerWidth 390, clientWidth 390).
  - A real 1440 passes (1440/1440).
  - A 1400 px page at mobile 390 **fails** (innerWidth 1400, clientWidth 980).
  - A deliberately wrong width **fails**: override 1440 against a claimed 390 gave 1440/1440.
- **Guard is non-vacuous.**
  - Deleting the `go()` guard in s408 failed the inventory test at `s408…:104 Page.navigate`.
  - Deleting the import in s5-overview failed it with "does not use the shared width check".
  - Both were reverted with `git checkout`.
- **Label tests are non-vacuous.** Removing `|| enabled.length === 0` and the `unrecognised` step branch failed the zero-enabled and unrecognised-Readiness tests. Both were reverted.
- **Focused tests:**
  - Frontend: Health, Foundation, Site Work, productStatus and evidenceClaimLimit pass.
  - Backend on private `w1ux06_test`: `test_s7_source_health_rules.py`, `test_s7_health_contract_postgres.py` and `test_s7_source_health_postgres.py` gave 16 passed. `test_s1_bindings` passed on the no-set case.
- **Suite and checks at `90699341`:**
  - `npx.cmd tsc --noEmit` exit 0.
  - Full `npm.cmd test`: 74 files, 1812 passed, 135 s.
  - `tools/check-all.ps1`: all 10 guards passed, including the new "Evidence width check (W1-UX-06)".
- **Full backend suite at `90699341`:**
  - Command: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml` on private `w1ux06_test`, with `var/sites/*.yaml` copied from main. The DB and the copies were removed afterwards.
  - Result: 2590 passed, JUnit cases=2590 skipped=0 failed=0, wall 1494 s (24.9 min).
  - An earlier attempt was stopped at its 20-min cap (63%, with 9 failures). The cause was the environment: PYTHONPATH named only the worktree and `backend`, so `assetops_contracts` was imported from the main checkout's editable install (`test_s405b_registered_release` failed on `SOURCE_PUBLICATION_REFUSED`).
  - **Worktree runs need** `PYTHONPATH=<wt>;<wt>\backend;<wt>\contracts;<wt>\gateway;<wt>\simulator`.

## Phase 2 must, once W1-UX-02 merges

1. `git merge main` into `task/W1-UX-06`. Rerun `node --test tools/checks/test_evidence_checks.mjs`.
2. Extend the shared width check to the UX-02 evidence script, using the same three insertions as the others:
   - import `widthGuard`, and `AS_OF_PATTERN` if it has an as-of claim;
   - `const requireWidth = widthGuard({ send, claim })`;
   - calls in `size`, `go`, `shot` and after each reload/back/forward.

   Then add its name to the inventory list in the test. Confirm that the UX-02 merge brings no new local `As of` substitute, by grepping `time not recorded` in the tests.
3. Complete `.agent/W1-UX-combined-owner-walkthrough.md` from `tasks/W1-UX-mockup-fidelity.md` "Combined walkthrough coverage and authorship", including the S4-08 default and `recorded_at` history cases.
4. Rerun **every** 1440/390 capture with the fixed tools as the final evidence set:
   - Commit the captures in batches by tool.
   - Record any failing tool as **not run**, with its reason.
   - Supersede the old UX-01/03/04/05 narrow claims with these measurements, or leave them unestablished and keep the owner gate closed.
5. Then write the review packet, `CODE_STATE`, `ACTIVE_CONTEXT`, and task `Status: in_review`.

## Open risks / deviations

- **Server statement still says "Ready to report".** `binding_service.py:88` `READINESS_STATEMENT` reads "Ready to report means…", and the Readiness view shows it under the new `Set up to report` badge. The ruling covers the badge only, so I did not change it. Recommend batching it into the W1 plain-language task, or an Architect one-liner.
- **`registered_basis.py:116` is unchanged.** It still says "No signal binding set of … was registered", which is outside the packet's three sentences.
- **The window fallback is unproven in real Chrome.** `Browser.setWindowBounds` is exercised only by the unit fake, because every real run held the CDP override.
