# DISP-1 review (fix/DISP-1-money-eligibility, head f75b01377)

Reviewer: fresh Claude, read-only, no DB. Spec D-ANY.11. DISP-1's own commits are bb6ebb6e4 + f75b01377; the branch merged
main at 506e035e1 (AR-4 + PR-2a), so `git diff 118866a17` also shows PR-2a files that are not DISP-1's.

**Verdict: ACCEPT** (no High/Medium; one Low test to add before or with merge, coordinator's call).

## Checked
- `money_eligibility.py:204` fail-closed now `(select_days is None and self.days is None)`; with `select_days=None` the call
  `self.days.select_dispatch_days_on(c, t, s, lo_t, hi_t, known_at)` has the same arguments as before (lo_t/hi_t are the
  old inline expressions) and the gap guard is skipped, so the None path is behaviour-identical. `for_finding` untouched.
  `financials` has no `estate` reference.
- `postgres_estate_read.py:211-213` lambda `dispatch_days(self, t, s, f, to, k)` matches `coverage.dispatch_days(snapshot,
  t, s, from_, to, k)`. Local import, no cycle.
- Kill switch: provider returns None -> `snapshot.dispatch_days(t, s, f, to, k)` = `select_dispatch_days_on(self._c, ...)`,
  the old call on the same connection; only difference is a day missing from compose now yields
  HISTORICAL_DAY_UNAVAILABLE instead of a KeyError (strictly better).
- New refusal surface: none in practice. `day_window` is the UTC day, so `dispatch_spans(_start(spans[0]),
  _start(spans[-1])+1d)` == `spans`; `DispatchDayRows` returns one entry per span day; absent days are composed per
  D-ANY.10 and, if compose lacks the day, keep `absent_day` (available, no selection -> unmatched, as before). Bracket days
  outside the request range are read by their own provider call over the bracket, so they compose the same way. The guard
  only fires on a provider contract break.
- Live vs explicit: a live page reads latest rows rather than compose at k; this is the D-ANY.11 rule and identical to the
  coverage read in the same request.

## Findings
- **Low** `backend/tests/test_disp1_money_eligibility_select_days.py` (whole file): the adapter wiring and the D-ANY.10
  absent-run path under eligibility are only covered by parity, which does not label ELIGIBLE-with-amount / PENDING /
  outside-range cases (packet GAP). Add one no-DB test: an `EstateSnapshot`-like stub (`basis_historical=True`,
  `dispatch_days` returning compose days) with `coverage.dispatch_rows_provider` monkeypatched to return, for a 2-day
  bracket, one stored day and one `ABSENT_MARK` day (outside a nominal request range), then call
  `coverage.dispatch_days`-backed `for_finding_on` and assert it equals the `select_days=None` compose result, plus the
  provider-returns-None (kill switch) case equals compose. Not merge-blocking: the code path is traced above and parity is 61/0/0.
- **Low** `.agent/DISP-1-packet.md`: main has moved to fc7fe817d since the 506e035e1 merge; parity/timings are on that
  base. Coordinator merges main again; the newer main commits touch only `.agent` docs (build sheet,
  handoff), not DISP-1's code files.
- **Low** `estate/adapters/postgres_estate_read.py:211`: `DispatchRowsUnavailable` (no Site row) can now be raised from
  `eligibility`; the coverage read of the same Site in the same request raises it first, so no new user-visible state.

## Checks run
- No-DB: `test_disp1_money_eligibility_select_days.py`, `test_lr01_money_eligibility.py`,
  `test_estate_coverage_local_days.py`: 22 passed (1.8 s), worktree PYTHONPATH.
- check-architecture: see coordinator report (run by reviewer; result recorded there).
- Not verified: parity 61/0/0, timings and the profile claim (DB jobs, not run per lane rules); frontend not touched by DISP-1.
