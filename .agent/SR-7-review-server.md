# SR-7 server review (fresh Claude reviewer, 2026-11-12)

Branch `task/SR-7-service-claim-range`, head 7fc12167d, diff `git diff $(git merge-base HEAD main) HEAD` (merge-base bbec56c26).
Scope: SR-7a `service-range` and SR-7b `claim-limit-range` servers only. Pages are not built yet.
Judged against: rev 10 §10.1 and §10.3, revs 10a.2 and 10d.4 (and 10d.7 for the shared LOW, NO_VALUE and `known_at` rules), and D-SR.9, D-SR.15/16, D-SR.23-26, D-SR.45 and D-SR.47.

## Verdict: ACCEPT WITH NOTES. Fix M1 on the branch before merge.

The server code matches the spec and the rulings. M1 is repository hygiene in the last commit, not a code defect. It still has to be removed before merge.

## Findings

**M1 (Medium): commit 7fc12167d force-adds 515 ignored cache files.**
- What: 510 `__pycache__/*.pyc` files and 5 `backend/.pytest_cache/*` files, about 8 MB of bytecode in total. All of these paths are in `.gitignore`, so they were most likely swept in by a `git add -f` that was meant for `.agent`.
- Why it matters: merging puts machine-specific bytecode for CPython 3.12 and pytest 9.2 into main. Every later diff would show stale binary files.
- Fix: run `git rm -r --cached` on these paths and commit:

  ```
  git rm -r --cached $(git diff --name-only $(git merge-base HEAD main) HEAD | grep -E '__pycache__|\.pytest_cache')
  ```

  Then confirm that `git diff --stat <merge-base> HEAD` lists only the 4 source files, the 4 test files, `main.py`, and `.agent`.

**L1 (Low, acceptance detail of D-SR.45 J3): not every refusal code is pinned in the route tests.**
- `backend/tests/test_sr7_claim_limit_range.py:214-215` checks only the status (409) and `claim_limit` null. It does not check the code `PERFORMANCE_CUTOVER_CLOSED`.
- Neither route test checks the `SITE_NOT_FOUND` code on the `NOPE` 404:
  - `test_sr7_claim_limit_range.py:207`
  - `test_sr7_service_range.py:193`
- The claim-limit route has no Site-store 503 case (`SITE_STORE_UNAVAILABLE`). The service test has one, at `test_sr7_service_range.py:196`.
- Fix: one assert for each.

**L2 (Low, D-SR.45 J1 "pin a 7-day Nairobi window to 7 rows").**
- `test_sr7_service_range.py:165-176` sends a 7-day Nairobi window but asserts only the first two states.
- The body tests pass `D` directly, so this no-DB file would not catch a revert to `local_days`, which gives 8 rows.
- `test_sr7_service_range_postgres.py:145` does pin the row count, but for a 6-day Nairobi window.
- Fix: assert `len(r.json()["days"]) == 7`, plus the first and last `local_day`, in the no-DB route test.

**L3 (Low): only the stored-route key's names are checked, not its values.**
- `test_sr7_service_range.py:175` and `test_sr7_claim_limit_range.py:195` check the key names.
- They do not check `from`, `to` and `known_at`, or that `known_at` takes part in the key.
- Fix: compare the key to the expected dict, and add a second request with `known_at`.

## Verified correct

**SR-7a service-range body** (`backend/assetops_backend/mini_depth/service_range.py`):
- Each day's state follows the chain grade:
  - COMPLETE or PARTIAL with a value → SERVED_ALL or SHORTFALL. These are the only counted days.
  - COMPLETE or PARTIAL without a value → NO_VALUE.
  - LOW → NOT_ENOUGH_READINGS. Never counted, and the value is hidden.
  - PENDING → STILL_PROCESSING.
  - NO_DATA, and a missing row → NO_READINGS. A missing row reads as `grade` None, which becomes NO_DATA (the chain rule, D-SR.16).
  - NOT_EXPECTED → NOT_EXPECTED.
- `partial` is true only on a counted PARTIAL day.
- Hours = row seconds ÷ 3600 (D-SR.26).
- Totals are Decimal sums over the counted days only. They are null when no day is counted.
- There is exactly one `ChainRequest.day` over `window_days` (D-SR.45 J1).

**SR-7b claim-limit-range body** (`backend/assetops_backend/estate/claim_limit_range.py`):
- It follows `mini_grid_rows` (`estate/evidence_money.py:252-268`) step for step: `dispatch_days` → `note_page_days` → `day_revision` → `claim_limit_on` → `reduce_day`.
- It applies the same refusal-reason merge.
- `current_ceiling` is taken only from `reduce_day`, which nulls it under the historical basis, so no ceiling is invented.
- A null revision → NO_SELECTION, with no link.
- The summary follows D-SR.25.

**Routes:**
- Admission uses `board_site`.
- Cold and EV Sites → 404 `*_RANGE_NOT_APPLICABLE`.
- Windows → 422 `INVALID_WINDOW`, from `estate_request`. The claim-limit route uses the "evidence" kind (J5).
- Unavailable → 503 `SITE_*_RANGE_UNAVAILABLE`.
- The claim-limit route checks the 409 gate before the stored route, so a stored body can never bypass a closed cutover.
- The StoredRoute key is `{site, from, to, known_at}`, and `sites` = `watermark_sites` = the Site.

**`main.py:698-706`:** both routers are included after `responses` (606) and `estate_portfolio` (618), right after `build_chain_router`. This follows D-SR.23.

**D-SR.9:** Service and the claim limit apply to mini-grid Sites only. Kobo and Kisiwa (both MINIGRID) take the same path, and Cold and EV get an explicit 404 (the n/a cells in 10.5's table). No Site-type disparity is introduced.

**The tests are not vacuous:**
- Each state, the LOW-with-value case, the absent-row case, `partial`, and the totals are pinned to exact values.
- The Postgres service test derives day 1 end to end from 24 `mini-service/2` heads, and checks stored = live, both on the first serve and on the stored hit.
- The Postgres claim test compares each row with `reduce_day(claim_limit_on)` and asserts at least one compared row (`checked >= 1`). It also checks rows on (absent run) = rows off, and that each row link opens with a 200.

## Checks run (by me, on 7fc12167d, PYTHONPATH = the worktree; module path confirmed)

| Check | Result |
|---|---|
| `test_sr7_service_range.py` and `test_sr7_claim_limit_range.py` (no DB) | **23 passed** |
| `test_out_b4_main_binding.py` and `test_e4_prebuilt_routes_source.py` | **7 passed** |
| `test_sr7_claim_limit_range_postgres.py` on `assetops_sr7_test` | **3 passed** in 20 s |
| `test_sr7_service_range_postgres.py` on `assetops_sr7_test` | **2 passed** in 78 s |

Not run, as instructed: `check-all`. The packet's 19/19 result is from de8e18504, not from the head commit. Not run: the frontend, since there are no pages yet.

## Residual risk (beyond the packet's known open items)

The known open items are the 3 sampled hours and parity.

- The Postgres service test has no PENDING day. Spec §10.3 lists one. PENDING is covered only by the no-DB stub.
- The claim-limit route (its gate and stored route) is tested only with stubs. The Postgres tests call the body directly.
