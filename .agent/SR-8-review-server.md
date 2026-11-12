# SR-8 server review: `GET /api/sites/{code}/renewable-range` + `all_hours_headroom_kw`

Reviewer: fresh Claude reviewer (did not author the slice), 2026-11-12.
Branch `task/SR-8-renewable-range`, HEAD 21addec2e, base `git merge-base HEAD main` = f4dd7f9b8.
Spec: rev 10 §10.1/§10.4, §10a.3, §10d.7, §10d.8; D-SR.9/23/27/45/47/48.

## Verdict: REJECT (one High, mechanical; the code itself is acceptable)

Fix H1 on the branch and this becomes ACCEPT WITH NOTES. No re-review of the code is needed for H1, only a
`git diff --stat` check showing 10 files.

## Findings

### H1 (High, acceptance/hygiene): 475 ignored `__pycache__/*.pyc` files committed
- Commit 21addec2e (HEAD) adds 475 `.pyc` files (374 under `backend/assetops_backend`, 58 `backend/migrations`,
  43 `backend/tests`). Main tracks none; `.gitignore:10` ignores `__pycache__/`, so they were force-added.
- Why it matters: it breaks the lane rule ("never force-add `__pycache__`"), it would put binaries on main, and
  every later test run rewrites tracked files, so all worktrees show dirty trees.
- Fix: a new commit `git rm -r --cached` on those paths (or the coordinator's preferred unpublished-history fix),
  then `git diff --stat $(git merge-base HEAD main) HEAD` lists only the 10 real files.

### L1 (Low, wording vs D-SR.48): `totals.average_label` still "average daylight headroom"
- `backend/assetops_backend/sites/renewable_range.py:41`. D-SR.48 (later than 10a.3 Q9) words the totals "average
  headroom available in every eligible hour". The page is not built, so it can still render its own words, but a
  server label that disagrees with the ruling invites the page to show the superseded wording. Fix: change the
  constant and the route test's expected totals (`test_sr8_renewable_range_route.py:158`), or drop the label from
  the body and let the page own it. Decide in the page part.

### L2 (Low, refusal order): window rule checked after `known_at` is parsed
- `backend/assetops_backend/mini_depth_api.py:214-221`. `estate_request` (UTC midnight, from<to, <=31 days) runs
  after `_instant(known_at)`, so `from>to` plus a malformed `known_at` answers INVALID_KNOWN_AT, while the docstring
  (and the shared estate parser) put the window first. Also a malformed `from`/`to` refuses through the one-day
  `REFUSALS` message (`_instant` -> `_refuse`), not `RANGE_REFUSALS["INVALID_WINDOW"]`'s text; code and status
  match. Fix: call `estate_request` before parsing `known_at`; optionally pass a range refuser to `_instant`.

### L3 (Low, test precision)
- `backend/tests/test_sr8_renewable_range_postgres.py:157`: `mean.quantize(Decimal("0.01"))` uses the default
  HALF_EVEN, not HALF_UP; it only differs on an exact tie, and the stub test (`..._route.py:157`, 20.625 -> "20.63")
  does pin HALF_UP. Use `rounding=ROUND_HALF_UP`. The EXCLUDED branch at :137-139 does not assert
  `all_hours_headroom_kw is None`. The module docstring (:10) still says the band "equals" the `headroom_kw` card.

## What was checked and holds

- Day states (`renewable_range.py:71-89`): no row -> NO_DATA; NO_DATA/PENDING/NOT_EXPECTED win; LOW ->
  NOT_ENOUGH_READINGS before the value is looked at (never counted, bounds nulled); empty value -> NO_VALUE;
  `result_state` CONFLICT/LIMITED/MISSING_HOUR before decision; ELIGIBLE -> COUNTED, EXCLUDED -> EXCLUDED (bounds
  shown); unknown decision -> NO_VALUE. `partial: true` only on a shown day with PARTIAL grade. Matches D-SR.47 Q2/Q4.
- Averages over COUNTED days with both bounds only, low and high separately, Decimal sum, HALF_UP to 0.01 on the
  two totals only; per-day bounds are the stored text unrounded. `partial` = counted < requested (10a.3 Q9).
- Hours: `covered_hours`/`operating_hours` from the row's `covered_seconds`/`required_seconds` (the operating-hours
  period of `RenewableHeadroom`), `window_hours` = stored ELIGIBLE hour count.
- D-SR.48 equality: `summarize_renewable` computes min low / min high over the ELIGIBLE hours of ELIGIBLE days,
  the same hours `RenewableHeadroom.measure` (`chain/measure_impls.py:211-219`) uses for an ELIGIBLE day; null
  exactly when `headroom_kw` is null. The Postgres test asserts exact low and high equality on sampled COUNTED days
  (`sampled >= 1` guards vacuity) and card high >= stored high.
- Placement in `cards` next to `headroom_kw`: a reasonable reading of "the backend depth envelope gains". The
  envelope is the one-day response body (`read.py _envelope`), the figure is card-level with the card's null rule,
  and the ruling puts it on a line under that card. Renewable cards are composed on read (`compose_renewable`), not
  read from stored `result.cards`, so no backfill is needed.
- One-day behaviour: only the added key (cards dict and `NULL_CARDS`); existing card values and status untouched;
  `test_w402_reads`/`test_w402_rules` updated by addition only.
- Stored route: key `{site, from, to, known_at}`, `sites`/`watermark_sites` = the Site; `perf.route` wraps;
  refusal codes 401/403/404 SITE_NOT_FOUND/404 RENEWABLE_RANGE_NOT_APPLICABLE/422 INVALID_WINDOW/422
  INVALID_KNOWN_AT/503 SITE_RENEWABLE_RANGE_UNAVAILABLE; one `ChainRequest.day` over `window_days` (D-SR.45 J1).
- `main.py:698-701` (include at :699): included after `responses`, `estate_portfolio`, the outcome board and the chain router
  (D-SR.23), using the same `outcome_board.s.chain_reader` accessor the chain router uses.
- Tests are not vacuous: every state, the absent row, HALF_UP tie, LOW-with-value, PARTIAL-counted, the 31-day
  edge, refusals and the stored key each have a distinguishing assertion.

## Checks run (this reviewer, PYTHONPATH = the worktree, PYTHONDONTWRITEBYTECODE=1)

- `pytest tests/test_sr8_renewable_range_route.py tests/test_w402_reads.py tests/test_w402_rules.py -q`:
  54 passed, 3 skipped (the 3 skips are `test_w402_reads.py:361`, no DB URL), 3.5 s.
- `pytest tests/test_sr8_renewable_range_postgres.py -q` on `assetops_sr8_test`: 1 passed, 78 s.
- Not run (per dispatch): check-all (builder/coordinator: 19/19 on head), frontend, parity, full suite.

## Residual risk

- Stored measure nulls a day's bound if any ELIGIBLE hour lacks a headroom bound; the card skips such hours. Not
  reachable if every ELIGIBLE hour carries a bound; parity (0 mismatches) is the gate that would catch it.
- Future `known_at` is not refused (only malformed is); the spec names no rule for it. Parity and the page are later
  gates.

## D-SR.62 fix review (fresh Claude reviewer, 2026-11-12)

Scope: 6377fea9e, b28fec415, 1a4d94dd5, 223783035 (`26c4845a7..HEAD`, 8 files). Basis: D-SR.62 in the build sheet,
sequence doc §10e.1, packet "D-SR.62 fix".

**Verdict: ACCEPT WITH NOTES.** The fix matches the ruling. Nothing blocks the merge. The notes are below.

Verified:
- The `missing` flag is carried through `hour_windows` (collector), `_Hour.missing` (last field, default False),
  `_hour`, `_read`, `_job_fallback` (keeps the row's flag through `replace`), `build_period` (renewable branch only)
  and `hour_json`/`hour_from_json`. A body with no `missing` key reads False. `BUILDER_VERSION` is `mini-depth-rows-2`.
- `compose_renewable` leaves missing hours out of the decision, the cards and the UNKNOWN test. A headless daylight
  hour still gives UNKNOWN. `partial_days` blocks `recurrence_established`. `missing_hours` is present on the
  renewable envelope only.
- 1a4d94dd5 (a day where every hour is missing stays UNKNOWN) is right on its merits. `RenewableHeadroom.inputs`
  returns payload None when there are no heads, so `measure` gives MISSING_HOUR and null. Dropping that day would
  invent a value the stored side does not have. The `test_w402_reads_postgres` expectations are unchanged.
- Fuel, service and backup: `hour_windows` and the envelope are unchanged apart from the shared version bump. The
  Grow board fixtures are unchanged and the board tests pass.
- Tests are not vacuous. The Finding-day test asserts the flagless call is UNKNOWN. The pin calls the real
  `RenewableHeadroom.measure`. The Postgres partial day asserts `missing_hours` 4, equal to the range row's uncovered
  hours, and value equality.
- No stray or ignored files: the worktree is clean and only the 8 named files changed.

Checks I ran (PYTHONPATH = this worktree):
- No-DB: sr8 route, w402 rules and reads, ar2 mini period rows, ch9 measures, and 8 board files (ch5a1, out_b1, out_c2,
  out_d4, mb1, idx_gaps, k10, polish_pa1): **208 passed, 3 skipped**.
- Postgres on `assetops_sr8_test`: `test_w402_reads_postgres.py` + `test_sr8_renewable_range_postgres.py`:
  **8 passed** (4 m 03 s).
- I did not run check-all (coordinator) or the parity rerun (needs the rebuild).

Notes (none blocking):
1. **Low. The packet says something inaccurate about old rows, and there is a risk for D-SR.63.** Packet line 67 says
   a `-1` row "reads PENDING_RECOMPUTE". It does not. `hour_from_json` reads it safely (missing=False). But
   `_from_rows` then looks up provenance under `pr.BUILDER_VERSION` (read.py:622). Stored blocks are keyed by builder
   version (`_PROVENANCE ... AND builder_version = :v`), so any v1 row that has a head raises `MiniReadUnavailable`
   (read.py:626), which is a 503. That is loud, not silent, and the mini kinds are off today. But the D-SR.63
   `serve_env` switch, which is not built yet, keys on `period-rows.json ok: true`. A DB whose rows were built at v1
   would turn the mini kinds on and 503 every stored mini read. Fix:
   - correct the packet line;
   - have the D-SR.63 switch also require no stale `mini_depth.*` rows (`stale_rows`) or the current builder version;
   - otherwise, the rebuild in §10e.1 must come before any switch-on.
2. **Low. The non-MINIGRID renewable envelope has no `missing_hours`.** `mini_depth_api.unsupported_envelope`
   (mini_depth_api.py:88-105) builds a renewable envelope without the key, so the shape differs by Site type. When the
   page work adds the field to `miniDepthClient.ts`, it must be optional, or the server should send
   `"missing_hours": 0` there.
3. **Residual risk (note only). A missing hour that still has a stored head.** This could happen when a revision was
   written while the hour was covered and coverage was later withdrawn. The cards exclude such an hour, as the stored
   measure does, but `renewable_envelope` still lists its rows and limitations. Rare. Watch for it in the parity rerun.
4. **Residual risk (note only). Absent-row days.** An absent row renders the NO_PV_BINDING noon hour with
   `missing_hours` 0. A live compose of a day with a binding but no readings gives 0 daylight hours plus N missing
   hours. The status is UNKNOWN on both paths, but `missing_hours` differs. The parity runs after the rebuild, so it
   should see no absent rows.
