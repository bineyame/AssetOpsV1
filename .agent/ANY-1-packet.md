# ANY-1 packet: card A6 = AR-0 + AR-1 (fast Site boards for any date range)

Branch `task/ANY-1-rows` (worktree `AssetOpsV1-any1`), from main `31f741f85`.
Spec: `.agent/architect-answer-any-range-speed-2026-11-10.md` §4 (AR-0, AR-1, risks); D-ANY.1-4, D-MONEY.1-4
(`build-sheet-OWN-GAPS-2026-11-08.md`); D-I18N.1 (UQ-6a `i18n.messages.Message`).

## Phase 1 (no Postgres) - done

Commits: `db3fe0734` (AR-1), `d7ffd0314` (AR-0).

### AR-1 read-row foundation

| Item | Where |
|---|---|
| Migration `0059_site_period_read` (down 0058): `site_period_read` (spec columns; PK `(tenant_id, site_id, kind, period_start, revision)`; FK to `site`; CHECKs on kind/state/fp/body/period), index `site_period_read_day`, `revision_provenance`; `ledger_append_only()` triggers on both; downgrade refuses while rows exist | `backend/migrations/versions/0059_site_period_read.py` |
| Port records `PeriodKey`, `PeriodRow`, `ProvenanceBlock`, `PendingEvent`, protocol `PeriodReadStore` | `chain/ports.py` |
| Postgres adapter (sole writer, INSERT-only, one `DISTINCT ON` read per Sites x days x kinds, `known_at` via `computed_at`; PENDING reads over `event_outbox`/`event_consumption` at k and live `snapshot_dirty`) | `chain/adapters/postgres_period_read_store.py` |
| Generic builder (fingerprint/revision rules of `SnapshotBuilder`; builder version in fp), reader (1 row statement + 1 ledger statement + live dirty statement), PENDING-at-k (event recorded <= k, not consumed by k; live dirty mark; older `builder_version`), row contract (words `{key, params}`; money lines with receipt, half-up cents reproduced, original currency, no fx/segments, no totals; `rate_ref`s folded into `input_fp`), `served_kinds()` switch `ASSETOPS_PERIOD_READ_KINDS` | `chain/period_read.py` |
| Register schema: optional `kinds:` section (`<area>.<name>`, grain hour/s3_day/local_day, site_types, measure input keys); `resolve` dirties kinds through the same `snapshot_dirty` queue; live register `kinds: {}` | `chain/events.py`, `config/chain/event-register-v1.yaml` |
| Drain routes kind rows to the period builder (optional arg); tick stage passes it; composition wires store/builder/reader, `period_kind_builders()` returns `{}` | `chain/drain.py`, `scheduling/stages.py`, `chain/composition.py` |
| Backfill CLI `python -m assetops_backend.chain.period_backfill build|show` (`--stale-only` rebuilds days with an older builder version) | `chain/period_backfill.py` |
| Writer guard rule 8: period writer registered, sole writer, insert-only, non-vacuous | `tools/checks/configuration-persistence.ps1`, `tools/checks/test_estate_guard.py::test_period_writer_insert_only_and_not_vacuous` |

### AR-0 parity and speed guard

- `tools/checks/period_read_parity.py`: story requests (`chain.prebuild.paths()`) + seeded cases (board any day on
  KOBO/KISIWA; Portfolio 1-31 days, aligned and unaligned; a 31-day month; historical `known_at`); oracle (kinds off)
  vs candidate (`--kinds`) byte for byte, store off, fetched oracle-candidate-oracle (UNSTABLE when the oracle is not
  deterministic). `--self-test` on fakes; added to `check-all.ps1`.
- `tools/checks/perf_budget.py --any-range [--seed --random --story]`: the same seeded cases, cold, store off (store on
  refused), budgets `config/chain/perf-budgets-any-range-v1.json` (board 2000 ms, Portfolio range 2000 ms); fixtures
  `tools/checks/fixtures/perf_budget_any_range/` run under `--fixture`.

### Checks run (phase 1)

- `pytest backend/tests/test_any1_period_read.py` + adjacent (`test_ch1b_drain`, `test_ch1b_register`,
  `test_ch5b_graph`, `test_dd1b2b_drain*`, `test_fix_cold_drain_stage`, `tools/checks/test_event_register.py`):
  143 passed, 4 skipped (Postgres-gated).
- `pytest tools/checks/test_perf_budget.py tools/checks/test_period_read_parity.py`: 20 passed.
- `pytest tools/checks/test_estate_guard.py -k "pg_reader_import_allowed or period_writer"`: 2 passed (the real tree
  passes the configuration-persistence seam; three mutations of the period writer each fail it).
- Non-vacuity: parity self-test catches one deliberate byte mismatch, a status difference and an unstable oracle;
  a neutered `compare` makes the self-test fail (`test_self_test_is_not_vacuous`). perf any-range fixtures include
  the measured 11.2 s / 36.1 s breach.
- `python -m assetops_backend.chain.graph check`: exit 0 (existing warnings only).
- `tools/check-architecture.ps1` on `d7ffd0314`: "Architecture check passed." (exit 0).

### Known deviations

1. `revision_provenance` PK is `(assessment_revision_id, builder_version)` and carries `tenant_id`, `computed_at`
   (spec: `assessment_revision_id PRIMARY KEY, block`): a builder change must be able to store a new block without
   overwriting (spec risk "builder version changes"). No FK: the revision may come from several selection tables.
2. No `UNIQUE (..., input_fp)` like 0043: a fingerprint may legitimately return to an earlier value.
3. PENDING-at-k for a historical k sees the outbox/consumption ledgers only; the short gap between consumption and the
   same tick's drain is visible live (`snapshot_dirty`) but not historically (the dirty queue keeps no history).
4. The AST guard "site_outcomes/* and estate/* call no raw-reading reads on the serve path" (risks table) is left to
   AR-2, where the first page part switches; AR-1 switches nothing.
5. Kind bodies' word fields are checked by name (`WORD_FIELDS`); a word under another key is not detected.

## Phase 2 (D-ANY.5 steps 1-6) - done; step 7 waits for the baseline go-ahead

Merged main (`770ce4e08`, clean). Commits: `83fd09370` (M3 tests + `absent`), `15c8c86d4` (parity/perf), `90f5d67b4`.

| D-ANY.5 step | Where |
|---|---|
| 1-2 M3 Postgres tests first: 0059 catalogue + insert-only + CHECK, store round-trip (latest, provenance once, never overwritten), downgrade refused with rows then allowed + upgrade head; late reading live (PENDING "event") and historical: k between revision 1 and 2 (after consumption) serves rev 1 not pending; k between event recorded and consumed serves rev 1 PENDING; k before rev 1 = `absent`, `NO_DATA` | `backend/tests/test_any1_period_read_postgres.py` |
| 3 every `<= k` stays on `computed_at` / `recorded_at` / `processed_at` (no story clock added); the test asserts `rev1 < recorded < processed < rev2` on one wall clock | adapter unchanged |
| 4 `PeriodReadResult.absent` (every requested (site, day, kind) with no row at k, sorted), `is_absent`, `day_state` = PENDING > `NO_ROW_STATE` (= `grading.NO_DATA`, today's no-row rule) > None; live absent logged `period_row_absent` and counted (`absent_count()`); no fallback compose | `chain/period_read.py` |
| 5 parity keeps story-time k cases and adds `any.between_revisions.<table>`: k = first whole second after a revision 1 whose revision 2 is later (site_period_read, else site_day_snapshot; `known_at` is whole seconds on the wire); no such row = `MISSING` failure, never a silent pass | `tools/checks/period_read_parity.py` |
| 6 Low: unaligned Portfolio cases randomise the end too (self-test check); `perf_budget --any-range --kinds` (child env), per-case `period_row_absent` counts | `period_read_parity.py`, `perf_budget.py` |

Checks (phase 2): `test_any1_period_read_postgres.py` on own `assetops_any1_test` (routed run DBs, gate <150
connections): **3 passed, 0 skipped**. No-DB: `test_any1_period_read`, `test_ch1b_drain`, `test_ch1b_register`,
`tools/checks/test_event_register`, `test_perf_budget`, `test_period_read_parity`: 116 passed. Parity self-test PASS;
`perf_budget --fixture` any-range 4/4. Non-vacuity: dropping `computed_at <= :k` fails the late-reading test
(`[2, 2] == [1, 1]`); a fixed end fails the parity self-test ("no Portfolio case whose end is off a UTC midnight").

Known deviations (phase 2): 6. The test sleeps 1.0 s between revisions so a whole-second k exists between them.
7. The between-revisions case falls back to `site_day_snapshot` while no kind writes rows (AR-1 declares none).

### Remaining for the baseline (owner go-ahead, after the Thursday demo and PB-1b; never on client6 before then)

- AR-0 baseline: `period_read_parity.py` (no `--kinds`; must show `any.between_revisions.*` PASS, not MISSING) and
  `perf_budget.py --any-range --report`.
- D-ANY.5 step 7 / M2: time `_UNCONSUMED_AT` in the baseline and report p95 here; above 20 ms p95 → low-water bound
  and drop `payload` from the select in AR-2.
