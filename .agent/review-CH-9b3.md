# Review: CH-9b3 mill verdict

- Reviewer: fresh Claude reviewer (did not author the slice), 2026-11-06.
- Branch `task/CH-9b3-mill-verdict`, head `f79559e77`, worktree `AssetOpsV1-ch9b3`. Diff base `5fe2cf42d` (main with the CH9b3-R rulings), `.agent` excluded: 17 files, +1233/-11.
- Judged against: build sheet CH-9b (CH9b3-R, CH9b2-R, SCOPE-1), the owner's P1 decision (`owner-mill-pass-margin-2026-11-05.md`), and `review-packet-CH-9b3.md`.

## Verdict: ACCEPT

There are no High or Medium findings. The five Low findings below are copy or display edges outside the demo path, plus one optional test. They can be fixed on the branch or logged; none of them blocks the merge.

## What I verified

**The owner's rule** (`verification_families.py` `assess`)
- The code checks `10*Σlater*nb >= 11*Σbase*nl` in Decimal and integers only. This is algebraically identical to `10*mean(later) >= 11*mean(baseline)`, because nb and nl are positive.
- Both means are taken over COMPLETE days only. `judged_grades` also demotes a COMPLETE day that has no kWh value.
- The effective day is excluded from both windows: `baseline_candidates` starts at -1 and `later_candidates` at +1. The L0 test plants 999 kWh on the effective day and shows it is ignored.
- A later day counts only after it has ended (`< today`, Site-local).
- The look-ahead closes only after day +14 has ended.

**When VERIFIED can be claimed**
- A SHORT baseline returns before any other branch, so nothing is ever stored for it, even after the look-ahead closes.
- If a frozen baseline day is no longer COMPLETE, the result is "not judged".
- A baseline sum of 0 gives INCONCLUSIVE BASELINE_ZERO, whether later use is 0 or not. A zero baseline therefore never claims a rise.
- The boundary is exact: 11.0 against 10.0 passes and 10.999 fails.

**Lifecycle and reserve-trial bytes**
- `_OUTCOMES` keeps the same output column names.
- For a reserve row, `COALESCE(o.action_id, …)` returns `action_id` unchanged, and the `CASE … ELSE` falls through to the old `_CHANGE_OF` expression. The join and the ordering are unchanged.
- `OUTCOME_COLUMNS` is untouched. `DOMAIN_OUTCOME_COLUMNS` is derived from it.

**Stage trigger**
- `_evaluate_mill_plans` catches `Exception` and reports `{"code":"FAILED"}`. The only access outside the `try` is `site.site_type`, which `consume` already uses. So the trigger cannot fail the stage.
- It uses the stage's own `site_today` (wall-clock `clock_timestamp`) and wall-clock `now`, so the two are consistent.
- Cost of checking every MINIGRID tick: one engine create and one indexed `NOT EXISTS` query when no plan is undecided. With an undecided plan it adds one read of about 29 days of rows. Once a plan has an outcome, it drops out of the work list. I consider this acceptable.

**Origin guard in `domain_summary`**
- It now checks only `domain == "MINI"`. This is sound: only `freeze` can create a midday plan, and `freeze` already refuses an Action without an opportunity origin.
- A MINI Action without an opportunity origin reads NO_PLAN ("No verification plan yet"), which is honest.
- Keeping the origin-reader allowlist at 5 was the right call.

**Copy**
- "Target met", "Target not met", "Could not conclude" and "Too few fully checked days" are plain.
- The VERIFIED sentence matches SCOPE-1 verbatim. The BASELINE_ZERO line matches Q3 verbatim. The LATER_SHORT text is the CH9b3-R Q2 wording.
- The builder's LATER_SHORT line, "Only {n} of 3 fully checked days after the change in the 14 days allowed, so no verdict is given", is plain and makes no claim.

**"run" exemption**
- The exemption is sound. The guard defines "user-owned name" as one of its three allowed exemptions.
- In production, `domain_action.title` is operator-entered through `POST /domain-work/actions`, and `ColdScenarios.tsx:196` is a precedent.
- The exemption wraps only the single title value, and the authored words around it are still scanned.

**Mock deviation**
- The page carries `data-mock-deviation="R700"`.
- R700 is a row in `.agent/mock-departure-register.md:676`.
- `node tools/checks/mock-deviation-labels.mjs` reports: OK, 157 files.

**Merge traps with lane 1 (CH-6a3)**
- `git merge-tree --write-tree HEAD task/CH-6a3-composers` is clean, with exit 0.
- No file is changed on both branches.
- Lane 1's only change to `chain/reader.py` adds public wrappers (`day_grade`, `counts`). `_day_grade`, which this branch imports, is still there. I found no trap.

## Findings

**L1 (Low, copy). The BASELINE_ZERO table shows a pass threshold of 0.00.**
- Where: `verification_families.py` `summary_wire` and `assess` (`threshold` is set before the zero check); `SiteMillVerification.tsx` "Needed to pass" cell.
- What is wrong: a zero baseline renders "At least 10% above before: 0.00 kWh a day" right under "a 10% rise cannot be measured". A later value above 0.00 then looks as if it passed.
- Fix: return `threshold: null` for BASELINE_ZERO, or show the cell as "Cannot be set from a zero baseline".
- Preference-adjacent. The demo never shows this state.

**L2 (Low, display). Cent rounding can make a miss look like a pass.**
- Where: `mean_text` rounds half-even to cents.
- What is wrong: with later = 10.999 against a threshold of 11.00 (the L0 test case), the page reads "After 11.00 kWh a day / Needed 11.00" with "Target not met". The verdict itself is exact. Only the display is ambiguous within half a cent of the threshold.
- Fix: round the shown threshold up, round the shown after-mean down, or show one more place when the two rounded values tie.

**L3 (Low, honesty). The not-judged table can contradict its own line.**
- Where: `summary_wire` not-judged branch.
- What is wrong: `days_before` is `len(plan baseline days)`. When a frozen baseline day is no longer COMPLETE, the table says "3 of 3" before, while the line says "only 2 of 3 fully checked days before the change".
- Fix: take `days_before` from the live count of still-COMPLETE baseline days.
- The demo never shows this state.

**L4 (Low, test gap). The new GET has no HTTP-level test.**
- Where: `action_api.py:315`.
- What is wrong: the route is a thin pass-through over tested parts: `open_scope`/`run`, which are shared with tested routes; the service, tested at L2; and the client, tested in vitest. No test proves that the route is registered at this path, that an unknown or foreign Site is refused, that a bad UUID returns 422 (which the page shows as "refused"), or that `ActionRefused` 404/409 reaches the wire.
- Fix: one TestClient case in the existing Postgres file, covering 200 VERIFIED, 404 for a random id, and 409 for a COLD domain Action.
- My view: recommended but not required to merge, because DD-1b's F-THREADS and the clone collect will exercise the page path.

**L5 (Low, register and nit).**
- `millHeadline` adds the headline "No verification plan yet", which the R700 row does not list. Add it to the row.
- `operatorSiteRoutes.ts:379` has lost a space: `ACTION_CHILD_VIEWS =["plan", …`. This is a formatting nit.

## Residual risk beyond the packet

1. **Grade-at-time choice of later days.** The evaluator picks the first 3 COMPLETE later days that exist when it runs. If day +1 is late, for example graded PARTIAL until a backfill, then +2, +3 and +4 can be judged and stored once +4 ends, and +1 is excluded for good. The choice is by grade, never by value, so this is not cherry-picking. Still, the stored verdict depends on when the data arrived. The outcome's `pins` and `site_today` record this.
2. **No deadline gate on the trigger.** The evaluator runs after the drain even when the drain used up `deadline_at`, so a tick can overrun its bound by one small query plus a snapshot read.
3. **Outcomes are final.** A revision to a later or baseline snapshot after the decision never re-opens it. This is by design (one decisive outcome per plan, with pins), but it should be stated to the client if a figure is ever corrected.

## Checks I ran

All at `f79559e77`, with PYTHONPATH set to the worktree's absolute paths, the plan2 venv, and `ASSETOPS_GUARD_PYTHON` set.

| Check | Result |
|---|---|
| `pytest test_ch9b3_mill_verdict.py test_ch9b2_midday_plan.py` | 22 passed, 0.87 s |
| `tools/run-host-tests.ps1 -- test_ch9b3_mill_verdict_postgres.py` (default `assetops_test` at 127.0.0.1) | 5 passed, 26 s |
| `npx.cmd tsc --noEmit` | exit 0; no stray build-info file afterwards |
| `npx.cmd vitest run src/sites/__tests__/millVerification.test.tsx` | 7 passed |
| Guard V: `vitest run src/ui/__tests__/w1Vocabulary.test.tsx src/test` | 3 files, 48 passed |
| Guard A: `check-architecture.ps1` | passed, 255 s |
| Guard W: `check-agent-workflow.ps1` | passed |
| `node tools/checks/mock-deviation-labels.mjs` | OK |
| `git merge-tree` against `task/CH-6a3-composers` | clean |

## Not verified by me

- I did not rerun `test_ch9b2_reserve_byte_equal_postgres.py`, including its new reserve lifecycle case. I hold the packet's pass as a claim, backed by my static reading of the SQL above.
- I did not run the clone run, the adjacent Postgres files, the full frontend suite or the build. The packet reports 1453 passed over 62 files.
- I did not run the full backend suite, per the rules.
- I did not check the MD-0 mill story, which is DD-1b's.

## Coordinator verification (fix round 1, 3bc722e29) — ACCEPT
- L1–L5 fixed per builder report; display-only plus one TestClient test (200/404/422). Coordinator ran the frontend vocabulary guard (t028/sharedVisual/w1 Vocabulary): 36 passed. Builder: L0 16, Postgres 9 (incl. reserve byte-equal), mill vitest 7, tsc clean, mock-deviation labels OK.
- Residual risks (late later-day exclusion, no trigger deadline gate, outcomes never reopen on revision) recorded in packet — post-demo.
