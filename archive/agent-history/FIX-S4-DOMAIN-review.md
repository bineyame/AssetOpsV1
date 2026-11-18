# FIX-S4-DOMAIN review

Reviewer: fresh Claude reviewer (did not author the slice). Branch `task/FIX-S4-domain-filter`, head `fdc852515`,
base main `ee678cbe5`. Reviewed from a `git archive fdc852515` snapshot; the worktree was not touched.
Spec: Addendum 3, ruling 1 of `.agent/build-sheet-DEMO-SPARSE.md`.

## Verdict: ACCEPT

There are no High or Medium findings. The three Low findings below are notes. None of them blocks the merge.

## What was checked

- **Filter correct and complete.** `episodes` (`postgres_finding_store.py:133-146`) now filters on
  `f.domain = :d AND f.analytic_id = :a`, with defaults `mini_grid` / `dispatch`. That is the `_index_snapshot`
  predicate (`:544`). Every Finding inserter is in this one file:
  - mini at `:185` writes `DOMAIN`/`analytic_id`;
  - cold at `:641` writes `'cold_chain'`;
  - EV at `:738` writes `'ev_charging'`.

  So the filter keeps every mini Finding and drops both cold and EV Findings. There are two callers:
  `finding_service.py:67` (production) and `test_s4_finding_store_postgres.py:171`. Both use the defaults. No fake or
  protocol implements `episodes`; `git grep "def episodes"` returns only the store.
- **Other matcher-path readers.**
  - `assessed_days` filters on `analytic_id`.
  - `bases` reads the dispatch assessment store.
  - `plan_pass` sees only `episodes`.
  - `_fence` (`:109-122`) still counts every domain's `finding_revision` rows, and every non-mini recompute job. Judgement:
    this changes when the matcher re-runs, not what it writes. A cold write moves the fence. As a result, the
    `stages.py:164-165` unchanged-fence skip does not fire, or `apply` raises `FindingFenceMoved` and the matcher
    re-plans. A re-plan is idempotent: the new Postgres test asserts that a replay plans nothing. I agree with the
    packet's residual-risk classification. See L3.
- **A missing mini `episode_end` still fails loudly.** `finding_episode.py` and `finding_service.py` are unchanged
  (`git diff ee678cbe5 fdc852515` on those files is empty). There is no NULL special case.
- **Trigger deviation is sound.** `DISABLE TRIGGER` / `ENABLE TRIGGER` run inside the single `engine.begin()`
  transaction (`test_s4_finding_domain_filter_postgres.py:57-73`).
  - Postgres DDL is transactional: an exception in between rolls back the disable as well.
  - Other sessions never see the uncommitted state; they can only wait on the lock.
  - `pg_harness` gives each worker its own run-owned clone database and drops it.

  So the trigger state cannot leak, either to other tests or to the shared `assetops_test`. The ALTER takes an
  ACCESS EXCLUSIVE lock on `finding_revision` for a few milliseconds, which is harmless in a per-worker database.
- **The new test fails on the old code.** I planted the break described in the next section and the test caught it.
  The packet's revert proof is consistent with what I saw.

## Planted break

I broadened the predicate to
`... AND f.domain = :d AND f.analytic_id = :a OR f.domain = 'cold_chain'`, so the SQL still contains the substring
that the pure test checks.

- The pure tests **passed**. The substring check is blind to this break (see L2).
- The Postgres test **failed** at `:89`: the default read returned the cold episode.
- I then removed `:89` and ran again. The matcher itself crashed in `plan_pass` → `_unsupported_write` with
  `finding_episode.py:287 TypeError: '<' not supported between 'NoneType' and 'datetime'`. This is the reported bug.

Both files were restored, and I confirmed they are byte-identical to `fdc852515`.

## Checks run (plan2 venv, snapshot PYTHONPATH, `assetops_test` on 55432)

| Run | Result | Time |
|---|---|---|
| `test_s4_finding_domain_filter.py`, `test_s4_finding_domain_filter_postgres.py`, `test_s4_finding_episode.py`, `test_s4_finding_store_postgres.py` | 47 passed | 176 s |
| Cold set: `test_w204_cold_{consequence,migration,reads,worker}.py`, `test_w402_cold_enqueue_gate_postgres.py` | 72 passed | 566 s |
| Planted break | Caught by the Postgres test only, as described above | |

Not run by me:
- the architecture and workflow guards, and check-all. The packet reports check-all as 11/11 on `5fd7a0fdb`; the only
  later commit, `fdc852515`, changes just the packet.
- `test_idx_gaps_*` and `test_s4_finding_index_postgres.py`;
- `-Tier all`. The implementer is running it now and it is not yet evidenced.

The packet's scoped run (653 passed, run `20261031-132002-84e54d`) is on the slice's code. I did not reproduce it.

## Findings

- **L1 (preference, latent coupling): `finding_service.py:67`.** `match` takes `analytic = self.model.ANALYTIC_ID`
  for `fence` and `apply`, but calls `episodes(tenant_id, site_id)` with the default `dispatch.ANALYTIC_ID`. Today
  every model shares `ANALYTIC_ID = "dispatch"` (`dispatch_v3` imports it), so there is no effect. A future model with
  its own analytic id would read the wrong episodes and duplicate Findings. Suggested fix: pass `analytic_id=analytic`.
  This is optional; the ruling specified defaults.
- **L2 (test strength): `test_s4_finding_domain_filter.py:36`.** The pure test asserts on a substring, so a broadened
  predicate passes it. The Postgres test is the real guard, and it does catch the break. No change is required.
- **L3 (residual, agreed): `postgres_finding_store.py:118-121`.** The fence counts every domain's revisions, and the
  recompute marker includes cold and EV jobs. The effect is extra non-skipped or re-planned mini passes on Sites with
  cold activity. A sustained interleave would raise `fence_moved_streak`; it would never produce wrong Findings.
  Scoping the fence to the mini domain could be a later slice if streaks are seen in practice.

## Residual risk not named in the packet

The full-suite (`-Tier all`) evidence is still pending. The merge should cite that run's revision and its
case, skip and fail counts.
