# 3B3 packet: the structure read and evaluator, mini-grid

Implementer (Claude), 2026-11-20. Branch `task/3B3-structure-read` off `main` `bf72c735d`, worktree
`/opt/assetecon/AssetOpsV1-3b3`. Spec rev 2, rulings D-3B3.1-16 and round 1. Not merged. `USER_REVIEW_REQUIRED`:
false (non-screen). Review: discovery (W5).

## Commits

- `b934fd52f` code and tests (evaluator, sources, read, composition, registry v2, check codes, `month_sum`).
- `590ca267f` guard fix (composition through the domain builders), R7 coverage test.
- (third commit) bookkeeping: packet, mid-build questions, spec Status, `specs/INDEX.md`, `.ai/state`.

## Module path (P9)

`PYTHONPATH=<wt>/backend:<wt>/backend/tests:<wt>/contracts:<wt>/simulator:<wt>/gateway:<wt>/field:<wt>/host:<wt>/tools`
prints `/opt/assetecon/AssetOpsV1-3b3/backend/assetops_backend/__init__.py
/opt/assetecon/AssetOpsV1-3b3/contracts/assetops_contracts/__init__.py`. `fixtures` resolves as a namespace package
that also takes in main's `host/fixtures`; harmless here (no 3B3 test imports it).

## Done (spec §7)

| # | Answer | Proof |
|---|---|---|
| 1 | Yes: 47 nodes x Kobo/Kisiwa/Mto x actual and plan equal `derived-values.json` to the cent; every `SUM` factor equals `portfolio.lakeside-power.actual.sums`; Kisiwa `om` blocks and the plan groups' `blocks_of` equal the pack | T1, T2, T3 |
| 2 | Yes: own record, true cause, evaluator-computed blocks, never 0; nodes above have no value; any gap day gives no value | T4, T6, Postgres 1-2, 4 |
| 3 | Yes: weakest part, `NEUTRAL` skipped; assumed/TARGET leaves make ancestors ESTIMATED; prices ASSUMED with literal words | T1, T2, T7, T6 prices |
| 4 | Yes: empty portfolio None; `included`/`excluded` per factor; currency mismatch, version/key, tenant, duplicate refused | T3, T6 portfolio |
| 5 | Yes: L1, context, `/0`, floor/ceil, neutral literals, parse once (16 parses over two evaluations) | T5 |
| 6 | Yes, every case planted | T5 leaf-value and start-up cases |
| 7 | Yes: `month_sum`, `local_days`, `SnapshotReader.latest`, `select_window_price` via the existing builders; nothing stored; no route | code, Postgres tests |
| 8 | Yes, plus bookkeeping (spec Status, `specs/INDEX.md`, `.ai/state/data.md` + `index-2.md`, this packet, mid-build file) | `git diff --stat main` |

## Tests

- Focused (no DB): `test_3b3_structure_evaluate.py` + `test_3b1_structure_registry.py`: 143 passed, 2.8 s.
- Postgres (`--db`, routed `assetops_test`): `test_3b3_structure_read_postgres.py`: 4 passed, 6.0 s.
- `select-tests --base main`: selected 326 of 524 (not full). Docker is off-limits for this dispatch, so the
  selection ran on the host: `heavy-slot.sh --db -- pytest <326 files> -n 2` at `b934fd52f`, 1:33:51 wall:
  4137 passed, 32 failed, 11 errors, 1 skipped, 1 xfailed. The 28 failed files re-run at base `bf72c735d`: 29
  failed, the same set less 3; those 3 (`test_w205b_ev_replay_api` gate, `test_w503_ev_depth`/`_scenarios` mounts)
  pass on this branch alone (3 passed): order/xdist flakes. No failure names `structure` or `month_sum`.
  The 11 errors are `TEMPLATE_STALE` (mechanism template fingerprint covers `chain/outcomes.py`).
- `_month_reading` regression: `test_ch6_evaluator`, `test_ch6_contract`, `test_out_d4_board`, `test_a3_idle_fuel`,
  `test_k10_declared_none_board`, `test_walk1_productive_sales` pass; `test_demo_combined_finish_rows::kis8` fails
  identically with main's `outcomes.py` (pre-existing).
- Fast check-all: exit 0, 79.5 s (first run failed configuration-persistence on adapter imports; fixed).

## Plants (each reverted; all in a detached scratch worktree)

All failed as expected: neutral dropped from `extra_l`; `tariff` SUM; float tolerance; the NEUTRAL, COMPOSES and
L1-finite checks disabled; each leaf-value check disabled; a held leaf as MEASURED or 0; no `copy_abs`; no or any-zero
neutral short cut; empty sum 0; partial or open month counted; depth-first blocks; no currency mismatch; `/0` as 0;
coverage max or last-on-tie. L1's `0` and `-Infinity` cases fail on `> 0` alone (expected).

## Parity

T1/T2: 47 x 3 x 2 nodes equal the pack to the cent; T3: 38 SUM factors equal the pack's sums.

## Mid-build questions: 4 (`mid-build-questions.md`)

Q1 `month_sum` built in the adopted handshake form `(rows, measure, lo, hi, key)` (spec text drops `measure`);
Q2 a COMPLETE day without `unserved_kwh` is skipped (zero-like), no guard added; Q3 "closed" uses `known_at` or the
wall clock; Q4 which set is "n".

## Known deviations

- P2 wiring: the configuration-persistence guard refuses adapter imports outside `chain/` and `financials/`
  compositions, so `structure/composition.py` uses `chain.composition.build_snapshot_store` and the existing
  `financials.composition` builders (`build_trial_comparison_ports(...).price_selection` for diesel,
  `build_productive_price_selection`), same `snapshot` + `select_window_price(key, unit)`. Workaround cost: the
  builders' assumption-store engines are not disposed by `dispose()` (the diesel builder also makes an unused trial
  store, which is disposed).
- Neutral product: the result carries only the neutral's sources, coverage and currency (nothing of the other operand).
- Portfolio `assumed_leaves` are `SITE:leaf`, like `missing_leaves`.

## Not verified

- The mechanism-template tests (`test_ch6_mechanism_postgres`, `test_ch5a1_mechanism`, `test_ch5b_why`,
  `test_ch6b_estate`, `test_md0_mechanism`): need `tools/mechanism_dataset.py build` for this fingerprint; not run,
  because a new template can drop another lane's (two newest kept).
- The selection in the Docker runner (forbidden here); frontend untouched, so no typecheck/build.
