# CH-5a1 phase 1 handoff (commit 2e0c6d971 on task/CH-5a1-chain-reader)

Authority: Part A of `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-sheet-CH-5a.md` (incl. §A12 rulings) and
`C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\CH-5a1-preflight.md` (§1 field table, §2 P1-P9, §6 anchors).

## Landed
- `backend/assetops_backend/read_scope.py`: `ReadScope` (ledger `(name, argkey)->count`, `ms`, `hits`,
  `max_per_key()`, `repeated()`, `names()`, `top_ms()`), `scope(route)` (nested reuses outer), `memo(name, fn, *args,
  key=None)` (deep-frozen; raising call not memoised; outside scope = plain call), `record(name, args, ms)`,
  `freeze`, `thaw`. Memo hits are NOT ledger executions (ledger max 1 = no same-argument read executed twice).
- `perf.route` enters `read_scope.scope(name)` (`perf.py` route()). `mini.Reads.call` records `(name, args)` into the
  ledger (`site_outcomes/mini.py` Reads.call finally block).
- `PostgresAssessmentStore._window` memoised (key: repr(query with knowledge_at -> `_MEMO_NOW` when cutoff None),
  analytic, basis `__qualname__`, cutoff, all_jobs); body moved to `_window_read`. `claim_limit_snapshot_on`
  memoised on `(t, s, day, revision_id, known_at)`; body `_claim_limit_snapshot_on`.
  NOTE: memoised `WindowSnapshot` now has `MappingProxyType`/tuple fields. Any consumer that mutates or
  `json.dumps` them must use `read_scope.thaw` - watch scoped tests under a route (TestClient) for TypeError.
- `chain/read.py` (pure): `site_cutoff`, `readiness_of(rows, days, measures)`, `day_grade`, `day_settled`,
  `day_gaps`, `board_day(d, tz)`, `summary_day(to, tz)`, `local_days(lo, hi, tz)`, `assessment_state(status)`,
  `SITE_TYPE_OF_DOMAIN`, dataclasses `DayFacts/FindingHead/ActionFacts/MoneyHead`, `ChainReadPort` protocol,
  `ChainRequest` (`day`, `findings`, `findings_settled`, `action_facts`, `money_head`, all via `read_scope.memo`),
  `ChainReader(ports, verification=, money=)`. `money_head`'s body parsing is a placeholder: align it with the real
  `site_overview/read.py` `_money` (`:274-343`) output; adjust freely, the dataclass names are the contract.
- L5: `chain/lookup.py` `LOOKUP` binds `:k` (occurrence rows and `cnt` bounded by
  `coalesce(source_known_at, joined_at) <= :k`); both callers pass `"k": known_at`
  (`chain/adapters/postgres_thread_sources.py` `_lookup`, `estate/adapters/postgres_estate_read.py` threads).
- §A5 tuples: `board.py` THREAD_APPLIED/VERIFIED/LATER_STATES and THREAD_WIRE_KEYS deleted. Thread entries carry
  `lookup.state_classes(state)` = `applied/verified/later/wire_keys`; `lifecycle.thread_view` carries
  `applied_states/verified_states` (for `_state_on` reads on another day). `lifecycle.LATER_STATES` added.
  `test_ch3_rows.py` updated (fixtures use `state_classes`).
- L0: `backend/tests/test_ch5a1_reader.py`, `test_ch5a1_scope.py` (31 + scope cases); with test_ch3_rows and
  test_qw1_perf: 78 passed.

## Next (phase 2: wiring, L1, L2) - not started
1. `chain/adapters/postgres_chain_read.py` (SELECT only): `snapshots` (reuse SnapshotReader/store), `finding_heads`
   (sheet §A3 SQL; confirm column names vs `postgres_finding_store.py:478-550`), `findings_settled` (R8 / P8
   statement), `has_change` (EXISTS action_policy_change). Register in `tools/checks/configuration-persistence.ps1`
   `$pgReaders` (`:904-916`) with a ruling comment; run estate guard self-tests.
2. `chain/composition.py` `build_chain_reader(url, consequences=...)`; `site_outcomes/composition.py:60-73` passes
   `chain_reader` (consequences = `site_overview.upstream.consequence_read`, never disposed by the reader).
3. mini `compose` (`mini.py:372-511`): drop `mini_overview`, `finding_index`, `estate.site_readiness`; per §A4 table
   and Q2/Q4/Q5/Q9; `_lineage` (`:640-667`), `refresh_chain`/`linked_actions` (`board.py:534,567`) deleted and
   `test_link_lineage.py` rewritten; action_read x2 -> `action_facts`. Shared selected-revision link helper (C4).
4. cold/EV `evidence_readiness` -> `readiness_of` over `local_days` (`cold.py:108-117`, `ev.py:124-133`).
5. R6 board day; `mini_summary_day` -> `summary_day`; `board_cutoff` (`read.py:605-608`) and `index.py:168-169`
   `_cutoff` through `site_cutoff`; R2 `EstateIndexService.site_list` replacing `estate.scope` at
   `outcome_api.py:158-159`.
6. L1 `test_ch5a1_board_contract.py`, L2 `test_ch5a1_reader_postgres.py` (incl. the L5 count at k before a third
   occurrence, which L0 could not cover - it is SQL), scoped existing tests (§A9 item 4), collector update (§A9 item 5).

Phase 3: L3 polish clone A/B + coherence + perf probe (`tools/chain_perf_probe.py`) + P1 cProfile; L3m after MD-0.
