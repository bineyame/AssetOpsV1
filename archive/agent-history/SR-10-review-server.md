# SR-10 server + SR-10/11 shared core: independent review

Reviewer: fresh Claude (Opus 5.5), 2026-11-12. Branch `task/SR-10-fuel-range`, head `95a71e92d`, diff
`git diff $(git merge-base HEAD main) HEAD` (base `8d08f3226`, 16 files, +1250/-21). Spec: rev 10b.1-10b.3, 10d.11;
D-SR.31/32/36/45/51-54/58 (+ D-SR.60, which withdraws 58 Q2); D-E5.47. Pages not built (out of scope).

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. Three Low notes, none blocking.

## What was checked against the spec

- **Day kinds.** `mini_depth.fuel_day` / `mini_depth.backup_day` in `period_rows.DAY_KINDS` and `KINDS`;
  `MiniDepthDayKindBuilder` calls `build_period(..., whole_day=True)`, which takes `hours_within(local midnight,
  next local midnight, tz)` and every hour through the existing `_hour`. No migration, no `BUILDER_VERSION` bump
  (pinned in `test_day_kinds_are_registered_with_whole_day_builders`). Noon kinds unchanged; the AR-2 Postgres test
  now builds only the four board kinds. Register lines carry the noon kinds' inputs. Tick rebuild is pinned on
  Postgres: event -> pending -> STILL_PROCESSING -> consume + drain -> revision + 1, and the rebuilt 09:00 hour
  shows the live job, so the test is not vacuous.
- **day_summary.py.** Pending = PENDING_RECOMPUTE or PENDING/LEASED; sums, counts, limitations and sequences use
  assessed hours only (D-SR.51.1). Absent day: `stored: false`, every count/figure null, `sequences` null; a stored
  day with no sequence gives `[]` (D-SR.51.3, D-SR.58 Q1). `slowest_recovery`: largest seconds, null skipped,
  same-sequence target, earliest `outage_start` on a tie (D-SR.51.2, pinned with a tie case). Sequences
  de-duplicated by `chain_id` in the day (latest hour) and in the window totals (latest day) (D-SR.51.4). The
  start-success hour-card sum with its null rule matches D-SR.60. No outage key anywhere. Day-state order matches
  rev 10b.1.
- **Route.** Generic `build_day_range_router`; order: auth, grant, lookup (503), type (404), window (422, estate
  rule, at most 31 days), `known_at` (422), then one period read of the day kind over `window_days` (D-SR.45) plus
  one `ChainRequest.day`. StoredRoute key `{site, from, to, known_at}`, `sites` and `watermark_sites` set to the
  Site. The route name is the full path, the same as SR-8's convention. Refusal codes cover both domains.
- **Kill switch (D-SR.52).** `PeriodReader.read` does not consult `served_kinds()`, and the router does not
  either. The code comment names D-SR.52, and the stub test reads rows with the switch set to empty. The hour
  link (local 12:00) stays on absent days, so the live drill-in remains available.
- **Prepare (D-SR.54).** `build_period_rows` passes the four board kinds explicitly under the unchanged
  15-minute cap. `build_day_rows` runs after it in its own 30-minute step (deadline restored, wall cap re-raised).
  On failure or the cap it prints the rerun line, not the switch. The wall cap adds 900 s when `finish` is set.
  Tests pin the order, the explicit kinds, the cap and the rerun line.
- **Diff hygiene.** No stray files. The only force-added ignored file is `.agent/SR-10-packet.md`, as intended.
  `git status` is clean.

## The side effect: non-connection `DBAPIError` now gives 500 instead of 503

**Not a D-E5.47 regression.** I probed it with stubs: `OperationalError` gives 503
`SITE_FUEL_RANGE_UNAVAILABLE`, as does a `DBAPIError` with `connection_invalidated`. `ProgrammingError` and
`RuntimeError` give 500.

- D-E5.47 rule 1 defines infrastructure as exactly the `is_transient` set and says a deterministic failure is not
  one. A SQL or contract bug labelled "unavailable right now" (503, retry) would be the less honest answer.
- The 500 escapes `ResponseStore.serve` before any insert, so nothing is stored and nothing is shown as a data
  fact. That is what D-E5.47 protects.
- The peers are looser. SR-7 and SR-8 (`mini_depth_api.py` on their branches) and `chain_api.py` catch only
  `(SiteStoreUnavailable, *unavailable)`, so on those routes even a connection error surfaces as 500. SR-10 is
  stricter than every peer.
- The remaining gaps are L-1 and L-2 below.

## Findings

- **L-1, test gap (Low).** `backend/assetops_backend/mini_depth_api.py:251-253`, `test_sr10_fuel_range_route.py`.
  The new `is_transient` branch has no test. Every existing 503 case raises `SiteStoreUnavailable`.
  - Why it matters: the fix-round behaviour change (transient gives 503, other DB errors propagate) is unpinned,
    and SR-11 inherits it.
  - Fix: add two stub cases. An `OperationalError` from the period reader (or a wrapper raised `from` one) should
    give 503 `SITE_FUEL_RANGE_UNAVAILABLE`. A `ProgrammingError` should not give 503.
- **L-2, residual against D-E5.47 rule 3 (Low, not a regression).** `mini_depth_api.py:251-252`. A transient
  error inside `compose()` raises an `HTTPException` out of `ResponseStore.serve`.
  - What happens: the store's degraded path never runs. There is no stale `latest_good` row, no
    `TEMPORARILY_UNAVAILABLE` and no `Retry-After`. The client gets a typed 503 with no retry hint.
  - Why it is not a regression: the pre-fix code behaved the same way, and the peers do worse.
  - Fix: when SR-10c/SR-11 pages are built, treat `SITE_*_RANGE_UNAVAILABLE` as the retrying state (D-E5.47
    rule 4), never as data. A store-level fix belongs with the other range routes, not in this slice.
- **L-3, metric off by 2x (Low).** `tools/demo_combined.py:595` computes
  `hours = considered * 24 // len(DAY_KINDS)`. `considered` counts period rows (days x kinds), and each row is
  24 `_hour` reads.
  - The problem: D-SR.54 counts hour reads across both kinds. AR-2's 128 KOBO periods are 32 days, and
    32 x 24 x 2 = 1,536, which is the "about 1,500". This code halves the hour reads, so `seconds_per_hour_read`
    in `day-rows.json` is doubled. A true 0.55 s would read as 1.1 s, over the D-SR.54 stop line of 1.0 s.
  - The test pins the halved figure (`test_ar2_prepare_period_rows.py`, `hour_reads == 96` for 8 periods; it
    should be 192).
  - Also: D-SR.54 asks for the figure in `period-rows.json`, but it is written to a new `day-rows.json`. That is
    acceptable if the coordinator knows where to look.
  - Fix: use `considered * 24` (or the per-kind count). Until then, read the gate from the CLI's own
    `seconds`/`considered`.

## Checks run (PYTHONPATH = this worktree)

- No-DB: `test_sr10_day_summary.py test_sr10_fuel_range_route.py test_ar2_prepare_period_rows.py
  test_ch1b_register.py test_ch1b_drain.py test_any1_period_read.py`: **114 passed** (2.3 s).
- Postgres `assetops_sr10_test`, one file at a time: `test_sr10_day_kinds_postgres.py` **4 passed** (160 s);
  `test_ar2_mini_period_rows_postgres.py` **3 passed** (143 s). `assetops_polish_vps1_test` was not touched.
- `tools/check-architecture.ps1`: passed. `python -m assetops_backend.chain.graph check` ran without error (only
  the known "not chain-sourced" notices).
- Stub probe of the error mapping (scratch script, not committed): results as above.
- **Not run:** check-all (the coordinator queues it; the packet's "All 19 guards passed" is on `3ed855559`, not
  head). The D-SR.36 backfill, parity JSON and 2 s timing are still pending for the coordinator. No frontend,
  because no page is built.

## Residual risk not named in the packet

- The packet's residual-risk bullet about the 15-minute cap is superseded by the D-SR.54 split. It is now stale
  text in the packet.
- `mini_depth_api.py` and `main.py` will conflict with SR-8 (`build_renewable_range_router`) and SR-11 on imports,
  `__all__` and router inclusion. The second merger resolves this, as the packet says.
- A whole-day backfill without `--from/--to` builds up to today. Today's row is partial, and it is refreshed only
  by dirtying events or job completions. That is harmless for the historical demo windows (D-SR.29).

## D-SR.70-72 review (fresh Claude reviewer, 2026-11-12)

Scope: SR-10 fix commit 347d9765a (round `2dac39de2..347d9765a`; the other commits in that range are main's
architect/frontend commits brought in by merge 90f140ee8, not this round) and SR-11 d99445bfa (merge 6532eba6d plus
the backup NO_DATA route test). Judged against D-SR.70-72 (build sheet) and sequence doc 10e.4-10e.5.

**Verdict: ACCEPT WITH FINDINGS FIXED ON BRANCH** (M-1 before merge; Lows at the Implementer's discretion).

### Findings

- **M-1 (Medium, ruling gap) `backend/assetops_backend/mini_depth/day_summary.py:177-179`.** `pending` is computed
  only when a row is stored (`if read is not None`). D-SR.70 step 2 makes "pending at k (`read.pending` or
  `result.is_pending`)" win over NO_DATA, because "a day being reprocessed may just have received readings", and
  `PeriodReadResult.pending` is documented to hold pending days *with or without* a stored row. So a no-row day with an
  unconsumed reading event (a pre-data day or gateway-offline day whose first readings just arrived; the chain
  snapshot not yet regraded) now reads "No readings this day" instead of "Still being prepared". Before this round the
  absent-row branch caught it, so this is a regression introduced by the reorder. Fix: start with
  `pending = result.is_pending(site_id, d, kind)` and OR `read.pending` when `read` exists; add a pure/stub pin
  (absent row + `is_pending` + `no_readings` -> STILL_PROCESSING). The parity harness passes `pending=False` and is
  unaffected on the static demo DB.
- **L-1 (Low, test gap) `backend/tests/test_sr10_day_summary.py:221-235`.** The ruling asks that `none_declared` and
  NOT_EXPECTED measures be shown left out. No fixture has a NOT_EXPECTED measure on a NO_DATA candidate day, so
  deleting `and g != NOT_EXPECTED` keeps every test green. The `none_declared` lines are vacuous: `days_of` only drops
  `productive_kwh` with no row (`applicable_measures`), so `(keys[1],)` and `tuple(keys)` drop nothing, and line 235
  is empty because of the PARTIAL measure, not because "none is left" as the comment says. Fix: pin a day with one
  measure NOT_EXPECTED and the rest NO_DATA/missing (-> in the set); correct the comment.
- **L-2 (Low, test) `AssetOpsV1-sr11 backend/tests/test_sr11_backup_range_route.py:148`.** The last assertion is a
  tautology over a literal tuple and tests nothing; the docstring says "uncounted" but `totals` is never asserted.
  Fix: assert `body["totals"]["days_counted"]` and `partial is True`, and that the backup totals exclude D3/D5.
- **L-3 (Low, harness) `.agent/SR-10-parity-script.py:135`.** The D-SR.71 cross-check is "no NO_DATA day has an hour
  matching the precise predicate" (role + overlap). The script also requires `eligible`, so a NO_DATA day holding
  domain evidence under a missing/partial binding passes silently. Fix: gate `cross` on `match` alone (or list
  ineligible matches separately). Nit, same query (lines 88-90): no `tenant_id` filter, unlike the trigger; harmless
  with one tenant.

### Checked and found correct

- `no_reading_days`: same `days_of` entry as `day_grades`; `measures` minus `none_declared` and NOT_EXPECTED, at least
  one left, all NO_DATA; a missing snapshot is NO_DATA via `read.day_grade` (Q9); a PENDING measure disqualifies.
- `day_state` order NOT_EXPECTED -> pending -> NO_DATA -> absent -> rest, as ruled (apart from M-1's input).
- NO_DATA entry = `absent_day` + real `stored`, nulls, `partial` false, `hour_link` kept; not in `COUNTED_STATES`,
  so `totals.partial` turns true, which D-SR.70 states explicitly.
- Route: one `chain.request(...).day(...)` read feeds both grades and `no_readings`; no extra query per day; the same
  `known` snapshot for periods and chain.
- D-SR.72 cases have faithful equivalents: stored 24-head fuel row graded NO_DATA (11-06 fuel ASSESSED) -> NO_DATA in
  pure `day_state` and `compose`; stored no-assessment row (10-31 NO_ASSESSMENT) and stored backup row without a
  sequence (11-06 NO_SEQUENCE) -> NO_DATA in the fuel and backup route stubs; the Postgres test pins a real pre-data
  day with no row through the real chain reader.
- Parity D-SR.71 SQL against the migrations: `accepted_evidence.role`, `interval_start`, `interval_end`,
  `source_time` (0005, no later rename) and `signal_binding_set_revision.role_set`, `valid_from`, `valid_to`,
  `superseded_at`, `site_id` (0002) all exist. The binding query is the same as `mini_enqueue_hour`'s gate (count = 1
  and `bool_and` covers). Half-open overlap with `+ interval '1 microsecond'` equals the trigger's hour loop (it starts
  at the hour that holds `lo`, so `hour_end > lo` always holds). `DOMAIN_ROLES` is loaded from 0029 (verified:
  `mini_fuel` = `generator_power, fuel_level`); 0048/0049 do not change the fuel/backup pairs. String hour bounds bind
  as they already did in `evid()`. The `AssetOpsV1-build/var/polish_vps1/parity/sr10_sr11_parity.py` working copy is
  byte-identical to the committed copy. The SQL has not been run (the base `assetops_sr10_test` has no schema), so
  not verified against a live schema.
- No regression in existing states: the original 7-day stub sequence and every earlier test still pass. No stray
  files: 347d9765a touches 7 files, d99445bfa 2, all in scope. The build sheet diff is additions only.

### Checks run

- SR-10 at 347d9765a, worktree PYTHONPATH: `pytest test_sr10_day_summary.py test_sr10_fuel_range_route.py` -> 33
  passed.
- SR-11 at d99445bfa: `pytest test_sr11_backup_range_route.py test_sr10_day_summary.py` -> 35 passed.
- `pytest test_sr10_day_kinds_postgres.py`, base `assetops_sr10_test` (harness run DBs) -> 5 passed, 140.8 s.
- Not run: check-all (coordinator), the parity rerun (coordinator; D-SR.71 gates and the named NO_DATA day list are
  still unproven), frontend (no page in this round).
