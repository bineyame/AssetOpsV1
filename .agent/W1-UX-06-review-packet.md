# W1-UX-06 review packet - W1 presentation closeout and combined owner walkthrough

- **Task:** `tasks/W1-UX-06-closeout.md` (phases 1-2), branch `task/W1-UX-06`, worktree `AssetOpsV1-review3`. Main merged in at `22df6d7d` (includes W1-UX-02).
- **Ruling:** `D-2026-10-17-w1-ux-06` (`.agent/architect-W1-UX-06-answers.md`).
- **Phase 1:** built and reviewed ACCEPT. The review is `.agent/W1-UX-06-phase-1-review.md` (cherry-picked as `c7b7fdc6`), and the details are in `.agent/W1-UX-06-phase-1-handoff.md`.
- **Reviewer diff:** `git diff 22df6d7d..HEAD -- ':!.agent'` (phase 2), plus `git diff a9b3b297..23afc7c4` for phase 1 if it is re-read.
- **USER_REVIEW_REQUIRED:** yes. A fresh independent slice review gates the merge. The owner then walks `.agent/W1-UX-combined-owner-walkthrough.md` once, and W1 closes only on that acceptance. Not merged.

## Outcome delivered (phase 2)

1. **Shared width check in `tools/w1-ux-02-evidence.mjs`.**
   - It now calls `widthGuard` after resize, after load and before capture, and its as-of claim uses `AS_OF_PATTERN`.
   - The script is in the inventory list in `tools/checks/test_evidence_checks.mjs`.
   - All 24 browser evidence scripts are now guarded. `run-store-browser-evidence.mjs` stays exempt, as in phase 1.
2. **W1-UX-02 re-review Lows.**
   - **N1:** `useRead` in `SiteFinancials.tsx` stores the deps each result answered, and treats a mismatch as still loading. A bridge can no longer be paired, even for one commit, with the earlier empty consequences answer.
   - **N2:** the `amountShown` check is scoped to the measured card (`c.querySelector`).
   - The local untimed helper in `siteFinancials.test.tsx` now wraps the shared `expectStateLineVisible`.
3. **Backend wording.**
   - `binding_service.py:88` `READINESS_STATEMENT` now reads "Set up to report means this configuration links a reading channel or names a configured control for every required role…", and stays configuration-only.
   - `registered_basis.py:116` now reads "No channel-link set of {site} was registered as effective …, so there is no configuration snapshot to run from."
   - The reason code `BINDINGS_NOT_REGISTERED` is unchanged.
   - The on-screen sentence in `SiteFoundationFrame.tsx:240` gets the same rewording.
   - Exact assertions are in `test_s1_bindings.py` (converted KOBO-001 is ready) and `test_s2_registered_basis.py` (knowledge instant before the bindings).
4. **Phase-1 review Lows.**
   - **L1:** `contactSummaryWords` falls back to "Gateway contact cannot be confirmed", with a next step, when `ALL_CURRENT` or `NOT_ALL_CURRENT` arrives with zero enabled gateways. The state line is tested at `siteHealthBoundary.test.tsx` (zero-enabled case).
   - **L3:** the proximity rule ignores guard calls that are commented out (line, trailing and block comments), with three unit cases. `layout-evidence.mjs` now prints a passing width check with both widths.
   - **L4:** `FoundationBindingsPanel` uses `Object.hasOwn` (`knownReadiness`). The unrecognised-Readiness test is an `it.each` over `SOMETHING_NEW`, `constructor` and `toString`.
5. **Product defect found by the final capture, and fixed.**
   - The s602b inconclusive Action Evidence page went blank with "Objects are not valid as a React child ({code, accepted_evidence_ids})".
   - Cause: `SourceSide.reasons` arrives as objects (`source_provenance.py:158`), but the type said `string[]`.
   - Fix: `SiteActionVerification.tsx` renders each reason's code, and `verificationClient.ts` corrects the type. A new test in `siteActionVerification.test.tsx` covers it. The served page was rerun and passed 60/60.
6. **Combined owner walkthrough.** `.agent/W1-UX-combined-owner-walkthrough.md` is one ordered script of 16 parts:
   - a plain-language overview of W1, then one-time setup;
   - a 26-screen index;
   - each part gives prerequisites, the exact `cd` and PowerShell commands, ports, the printed URLs beside the mock, what to look for (including keyboard, exact-link and reload checks), the data label, stop and cleanup, and the final capture table;
   - it closes with the owner's 13-item notes list and the gate.
   - Per-tool sources and run logs are in `.agent/W1-UX-06-evidence/`.
7. **Final 1440/390 evidence set.** Every capture was rerun with the fixed tools, one walkthrough at a time, and committed by tool. The results are in the table below.

## Final capture set (fixed tools; logs in `.agent/W1-UX-06-evidence/`, screenshots in `%TEMP%\w1ux06-final\<tool>\`, not in git)

| Part / tool | Screens | Script(s) | Claims | Commit |
| --- | --- | --- | --- | --- |
| v01a | sites, sites:empty, foundation (x2), readiness (x2), sld (x2) | w1-ux-02, w1-ux-05 | 144/144 | `7350857f` |
| s5 | mini p01, unassessed | w1-ux-01, w1-ux-02 | 74/74 | `a1ae7e7a` |
| s502 | mini (5 days), sitefindings (3), late, settled, closed | s502 evidence, w1-ux-02 | 261/261 | `bc3ef4c7` |
| s2demo | evidence all, window | w1-ux-01, w1-ux-03 | 72/72 | `08c81613` |
| s405 | finding-evidence, financials provenance/withheld | w1-ux-02 | 63/63 | `cf382bcd` |
| s302 | evidence-analysis supported, limited, stale | w1-ux-03 | 56/56 | `bf76f7ff` |
| s3dispatch | dispatch, analysis (limited, supported) | w1-ux-03 | 72/72 | `0a4da463` |
| s4_finding | finding, finding:stale, finding-history | w1-ux-02 | 59/59 | `c104f3cc` |
| s404 | sitefindings x6 days, page 2, late, settled | w1-ux-02 | 148/148 | `5f2fac28` |
| s402b | financials priced, not calculated, not worked out, empty price | w1-ux-02 | 84/84 | `26636869` |
| s402a | assumptions; assumptions:emptyprice (extra) | w1-ux-02 | **36/38** | `f4da5ec4` |
| s408 | assumptions default, T1, T3, closed, mixed; S4-08 history | w1-ux-02, s408 evidence | 193/193 | `1d1fcc8e` |
| s601b | recommendation x3, changes, action-overview x2, execution x2, history x3 | w1-ux-01 | **192/196** | `01bdfd9c` |
| s602b | plan/evidence/verification: replay pass, guardrail, withdrawn, target_miss, inconclusive | w1-ux-01 (+ tool capture 120/120) | **338/340** after rerun | `9517eb8e`, `693e4997` |
| s603 | sitework active, page, proved zero | w1-ux-01 | **50/52** | `21a5de79` |
| s701 | health KOBO-001, KOBO-002, asset | w1-ux-05 | 56/56 | `7f438f8f` |

**Totals:** 1898/1908 W1 card claims, plus the s602b tool's own capture at 120/120. Every width check passed: every 390 claim was measured at innerWidth 390 with clientWidth in [370, 390]. **All 10 failures are the same claim, "the card has a small visual":**
- recommendation latest (held) and unavailable;
- withdrawn-hold recommendation;
- sitework proved zero;
- assumptions with no price.

These cards draw no picture in held or empty states. The script exemption was not widened. The question is owner note 10.

Superseded runs are kept in the logs:
- **s502:** 82/84 after `tick` assessed the dirty day. The tool was re-prepared and rerun without `tick`.
- **s602b inconclusive:** 42/46 because of the crash above. It was fixed and rerun.

The final set supersedes the old UX-01/03/04/05 narrow claims.

**Not run (each reason is recorded):**
- Foundation `?at=2026-09-01` and the no-window `/work` page: no card by design.
- Health with a selected gateway: no tool prints a gateway ID. It has jsdom coverage.
- KOBO-002 asset refusal: no card.
- Site-level `evidence` labelled-source view in s405: `links` prints only Finding-level Evidence.
- An S4-08 missing-source case: the tool supports owner, mixed and closed only.
- The S4-08 source label is not re-checked after reload. The script checks it on load, and checks the moment and price list after reload.

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| Ph1: one shared width check on every cited evidence script; unguarded = not established | Met. Inventory 24 guarded and 1 exempt, enforced by the guard test. The guard was shown to fail with the w1-ux-02 guard removed. |
| Ph1: shared as-of helper and regex; negative lag nulled; three sentences; approved labels | Met in phase 1 (ACCEPT). Phase-1 Lows L1, L3 and L4 are fixed here, and L2 is item 3. |
| Ph2: one ordered non-developer script, 26 screens plus S4-08 default and `recorded_at` | Met: Parts 1-16 and Part 12. |
| Ph2: rerun every 1440/390 capture with the fixed tool; batches by tool; not-run reasons | Met: table above. Ten claims fail (no-visual) and are reported as failed. |
| Reconcile prior narrow claims | Met: superseded by the final set. |
| Guarded cleanup | Met. Every agent dropped its `*_w1ux06` databases and work folders and stopped its servers. No `w1ux06` database remains. Left in place: the shared templates `assetops_s4cases`, `assetops_s3cases`, and `assetops_s402bcases` (rebuilt in this run). |
| Final proof | See Checks. |

## Checks

- **Proved non-vacuous.** Each of the following was reverted with `git checkout` after a commit, and failed as expected:
  - w1-ux-02 without its guard: inventory test failed with "does not use the shared width check".
  - N1 test without the deps key: it failed with "an amount was drawn before its consequences read answered".
  - Commented-guard rule reverted: 1 test failed.
  - L1 and L4 reverted: 3 tests failed (zero-enabled, `constructor`, `toString`).
  - Reasons fix reverted: the test reproduced the exact React crash.
- **Focused:**
  - siteFinancials 75/75; siteFoundationRevision plus siteHealthBoundary 121/121; siteActionVerification 25/25; `test_evidence_checks.mjs` 9/9.
  - Backend: `test_s1_bindings`, `test_s2_registered_basis` and `test_s1_cutover` gave 91 passed on a private `w1ux06p2_test`.
- **Full backend suite at `b7d75daf`.** Backend is unchanged after it (`git diff --stat b7d75daf..HEAD -- backend contracts` is empty).
  - Command: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=…`, with PYTHONPATH set to all five entries, on `w1ux06p2_test` (now dropped).
  - Result: 2590 passed; JUnit tests=2590, skipped=0, failures=0, errors=0; wall 1416 s.
- **At `b7d75daf`:** tsc 0; full `npm.cmd test` 74 files, 1909 passed; `tools/check-all.ps1` all 10 guards passed (including Architecture, Agent workflow, Dependency registry, Evidence width check); `check_v69_dependency_registry.cjs` exit 0.
- **Final frontend at the closeout revision:** see "Final run" below.

## Known deviations

- **s3dispatch Analysis revision IDs** were read from the served API, because `serve` prints only the day address. The walkthrough tells the owner to open Analysis from the page link instead.
- **Some s601b and s602b pages** (pending Action, test-case `/plan` and `/evidence`) were reached by clicking from printed pages, or by the printed Action ID's path shape. This is recorded in Parts 13-14.
- **`tools/s502-overview-finding-list-evidence.mjs` stale selector fixed** (`41160b19`). It now reads the token from the shared exact references. This is a tool change, not a claim change.
- **The s602b crash fix** (item 5) is a product fix outside the packet's list. It was needed for an honest final capture.

## Residual risk

- **Ten no-visual failures** stay open for the owner's decision (note 10).
- **SLD at 390** scrolls inside its own box (note 11).
- **The window-bounds fallback** in `widthGuard` is still unexercised in real Chrome, because every run held the CDP override.
- **Tool IDs change on every prepare**, so the owner must use the IDs their own run prints. The walkthrough says so.

## User-review focus

Walk `.agent/W1-UX-combined-owner-walkthrough.md` in order, and decide owner notes 1-13. In particular:
- the money wording (L4) and the untimed money states (L6);
- the Readiness strip versus the contact split;
- card/panel duplication;
- held or empty cards without a picture.

## Final run (closeout revision)

At `9f0afe1a`: `npx.cmd tsc --noEmit` exit 0; full `npm.cmd test` 74 files, **1912 passed**, 131 s; `tools/check-all.ps1` all 10 guards passed; `check_v69_dependency_registry.cjs` exit 0; `tools/check-agent-workflow.ps1` passed (after the ACTIVE_CONTEXT update).

## Fix round 1 (review `678901f0`)

- M1 fixed: the walkthrough runs from `C:\Users\assef\Bineyame\AssetOpsV1` at the commit the coordinator gives (step 1, `git log --oneline -1`); `$wt = (Get-Location).Path` is set once per window; all 63 `AssetOpsV1-review3` paths became `$wt`; `npm.cmd ci` added; `var\sites` is checked, never copied onto itself; every PYTHONPATH line uses all five `$wt` entries. New guard in `tools/checks/test_evidence_checks.mjs` fails on any `AssetOpsV1-review` text (proved: appended a path, 1 failed; reverted, 10/10 pass).
- L2 fixed: Part 5 section 4 now opens `/sites/KOBO-001/evidence`; Part 16 section 4 says to click a gateway through "What to do" and look for "In contact; its latest report is old". Both table rows reworded from "not run" to "owner look".
- L3 fixed: "Most screens" with a pointer to note 10; money line says a current amount only when the current read proves it, history amounts labelled as history.
- L4 done: Action Evidence source reasons show `sourceProvenance` `reasonWords` beside the code (code-less reason reads "Reason not recognised."); test extended. `tsc --noEmit` clean; `siteActionVerification.test.tsx` 25/25.
- L5 not changed (preference).
