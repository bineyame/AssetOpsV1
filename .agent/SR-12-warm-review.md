# Review: task/SR-12-warm-routes (SR-12 warm routes + SR-12b + D-SR.74 fix round)

- Reviewer: fresh Claude reviewer, 2026-11-13. Head e3b7dbe18, base 21db0dc4a (merge-base with main).
- Rulings checked against: D-WARM.1-8, D-SR.29/34/39/74 (`build-sheet-OWN-GAPS-2026-11-08.md`); packets `.agent/SR-12b-packet.md`, `.agent/WARM-1-packet.md`.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. The notes below are Low and do not block the merge.

## What was checked, and how

### (1) WARM-1 range routes (`tools/warm_ranges.py`)
- The seven routes are added per warmed range, for mini-grid Sites only (`range_requests`, MINI_GRID branch, lines 184-189).
  - Each one is sent as `?from&to` with the same encoding as every other warmed range.
  - Each route exists on the server with `from`/`to` as its documented params: `outcome_api.RANGE_ROUTE`, `source_health_api.HEALTH_RANGE_ROUTE`, `mini_depth_api` SERVICE/RENEWABLE/DAY_RANGE_ROUTES, `claim_limit_api.RANGE_ROUTE`.
  - No page client is on main yet, so the URLs are not yet pinned to a frontend request. **Re-check each route against its page client after the SR-5..SR-11 pages merge.** The packet and code comments already say this.
- **No regression.** I loaded main's `warm_ranges.py` beside the branch's and built both plans (`--today 2026-11-17`, the four Sites through 16 Nov).
  - With the new routes filtered out, the branch's plan is identical to main's: 1251 targets, same order.
  - The 1022 added requests are all `{KOBO,KISIWA}-001/*-range?from=..`.
  - Unstored: main 54 -> branch 64. The only additions are the nights reads.
- **Gate probe.** `exclude_closed_gate` (lines 629-640) probes each Site's first planned `claim-limit-range` request.
  - It does not copy the gate predicate. The route checks its gate before the stored serve (`claim_limit_api.py:139-145`), so a 409 is the gate's own answer.
  - Closed Sites are listed as `{site, route}` under `excluded_closed_gate`.
  - `main()` (lines 553-556) applies the filter before the mode split, so warm and `--verify` replay one plan.
  - A 409 on a planned request is `failed`, so `pass` is false (`summarise`, line 474; test `test_a_409_on_a_planned_request_fails_warm_and_verify`).
- **Kisiwa nights** is in `unstored_plan` only. It is not in `plan` (test `test_kisiwa_nights_stay_unstored_and_are_timed`).
  - Its URL equals `fuelBalanceClient.getNights` (`warmUrls.test.ts`).
  - The <=2 s reading on the VPS has not been measured yet. The packet says so.

### (2) SR-12b
- **Window parsing.** `analytics_api._window` accepts both ends or neither, as UTC instants with `from < to`. Anything else is 422 `INVALID_WINDOW`; 5 parametrised cases cover this, including one end only and an empty window.
- **`in_window` matches D-SR.74.**
  - A stated window is half-open.
  - A zero-length window counts when it falls in `[lo, hi)`.
  - The observed-bounds fallback stays closed.
  - All four ruled edges are pinned.
- **The ranged copy is the ruling's text, word for word** (`READINESS_STATEMENT_RANGED`, `plain.READINESS_SCOPE_RANGED`). The unranged copy is unchanged.
- **The declaration list is unranged.** Every non-readiness key of each row is equal between the ranged and unranged reads (asserted).
- **"All dates" line.** It is removed from the analytics panel only; the rejections panel keeps it (asserted, exactly one line remains).
- **Range sent by the page.** `SiteEvidence` sends both ends or neither. `getDeclaration` encodes them as `%3A` (asserted from the real client).
- **Refusal copy.** `CapabilityReadiness.refusalMessage` shows `NOT_ASSESSABLE_YET` whenever `awaitingMigration(declaration)` is true.

### (3) Tests are not vacuous; no stray files
I made each mutation below on the working tree, ran the tests, then reverted it with `git checkout`. The tree is clean afterwards.

| Mutation | Result |
|---|---|
| `refusalMessage` returns the server message again | both D-SR.74 vitests fail (t028EvidenceCapability, siteEvidenceScreen): 2 failed / 29 passed |
| stated-window rule made closed (`end >= lo`) | sr12b: 1 failed |
| fallback made open (`last > lo`) | sr12b: 1 failed |

- **Diff contents.** The diff is 14 tracked files: source, tests, and the two `.agent` packets. No cache, `__pycache__`, `node_modules` or other ignored file is committed.

## Checks run (VPS, worktree PYTHONPATH, no DB)
| Check | Result |
|---|---|
| pytest `test_sr12b_analytics_readiness_range.py`, `test_warm1_ranges.py`, `test_t028_dispatch_analytic.py`, `test_t028_fix_round_1.py`, `test_t028_presentation_profile.py` | 91 passed, 0 skipped (5.4 s) |
| vitest `siteEvidenceScreen` + `warmUrls` | 20 passed |
| vitest `t028EvidenceCapability` | 13 passed |
| `tsc --noEmit` | clean |

- There is no separate CapabilityReadiness test file. Its tests live in `t028EvidenceCapability`, which was run.
- **Not run:** check-all (left to the coordinator), Postgres, and live serve/warm/verify. The full suite was not run (test-suite policy).

## Findings (all Low; none is an acceptance gap)
- **L1: `main()`'s gate wiring is not pinned by a test.** `tools/warm_ranges.py:555-556`.
  - Replacing the condition with `if False:` leaves all 25 `test_warm1_ranges` tests passing. The "warm and verify share one plan" claim therefore rests on reading the code, which is correct today.
  - Fix: one test that runs `main(["--base-url", ..., "--verify", ...])` with `http_fetch` patched to a fake that returns 409 for one Site, then asserts the report's `excluded_closed_gate` and that the Site's gated requests were not sent.
- **L2: a closed-gate exclusion is only in the JSON report.** `tools/warm_ranges.py:584-586`.
  - The console's PASS/FAIL line does not mention it. D-SR.74 makes a non-empty list a prepare failure, so an operator who reads only the console can see PASS and miss it.
  - Fix: print `excluded_closed_gate: N Sites` on the summary line, or a warning when the list is non-empty.
- **L3: the probe treats any 409 as a closed gate.** `tools/warm_ranges.py:637`.
  - It does not check the code `PERFORMANCE_CUTOVER_CLOSED`. Today the route's only pre-compose 409 is the gate, so this is correct; a future 409 code would be reported as a closed gate.
  - Optional: match on `detail.code`.

## Residual risk (beyond what the packets already name)
- **The live D-SR.74 check is pending.** The vitests mock the client; the real pages have not been checked.
  - The ruling asks for a live check that the Kobo and Kisiwa Evidence pages carry no "migration" or "legacy" word.
  - `EvidenceClaimLimit.tsx:498-500` still prints `CODE: message` for its own refusals. That is not migration wording, but on a closed gate it would show `PERFORMANCE_CUTOVER_CLOSED:`. It is out of this slice's scope, and should be looked at during the same live check.
- **SR-12b is not visible on the demo Sites.** `/analytics` 409s on imported Sites, as the packet's Known deviations say. Only the refusal copy shows there.
- **The size of the warm plan grows about 80%.** Wall time on the demo DB is unmeasured; the first VPS warm should record it.
