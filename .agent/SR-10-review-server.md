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
