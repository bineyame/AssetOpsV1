# CH-9b1 handoff (PARTIAL - stopped at the context cap)

Branch `task/CH-9b1-opportunity-actions`. Main `b1ed2d3e4` merged (`6f8e70822`). Build commit `15cdc456d`.
Rulings: `AssetOpsV1-plan2\.agent\build-sheet-CH-9b.md` section "CH9b1-R" (binding). Pre-flight: `.agent/CH-9b1-preflight.md`.

## Landed (committed, L0 green: 123 passed - ch9b1 x2, ch2_threads, ch3_lifecycle, ch3_rows, ch4_opportunities)
- `backend/migrations/versions/0051_action_opportunity_origin.py` (down `0050_chain_response_expiry`): MINI domain,
  `domain_action_one_origin` + `domain_action_mini_origin` CHECKs, opportunity FKs, Finding pair DROP NOT NULL,
  `mini_opportunity_revision_opportunity_scope` UNIQUE, `chain_action_thread.origin_opportunity_id` +
  `chain_action_thread_one_origin`, trigger matches `IS NOT DISTINCT FROM` both, view appends 2 columns.
  Downgrade refuses while an opportunity-origin Action/link exists. **Not yet run against Postgres.**
- `work/domain_action.py`: `MINI_SPEC`, `ACTION_DOMAINS` (DOMAINS stays Cold/EV, intent-capable), `origin_of`,
  `DomainSpec.origin/site_type`, MINI closed body (opportunity pair only).
- `work/domain_intent.py`: create branches on origin (`tx.opportunity_revision_selected`), MINI intent refused 422.
- `work/adapters/postgres_domain_intent.py`: `opportunity_revision_selected`, MINI INSERT, `_ACTION_COLS` + opp cols.
- `work/adapters/postgres_domain_action_index.py`: `origin_opportunity_id IS NULL` (Finding-only surface).
- `work/adapters/postgres_work_read.py`: `_DOMAIN_LINKS` opp cols; `revision_links` adds `opportunity_revision_id`
  only for MINI; `link_selections` appends MINI rows (lineage = study revision exists by cutoff, pin None).
- `work/site_index.py`: `action_selection_key` uses `opportunity_revision_id`; MINI link has no verification href.
- `chain/threads.py`: `Origin` (+`of`, `columns`), `link_action(kind, action_id, origin)`, MINI_TRIAL Finding-only.
- `chain/adapters/postgres_thread_store.py`: opportunity occurrence lookup + separate INSERT (Finding INSERT text
  unchanged); `_SITE_LINKS` COALESCE. `postgres_thread_sources.py`: `_UNLINKED(_FOR)`/`all_actions` opp column,
  `unlinked_actions_for(..., opportunity_ids=())`; `scheduling/stages.py:247` passes placed opportunity ids.
- `chain/lookup.py` A-row, `chain/adapters/postgres_chain_read.py` `_SITE_ACTIONS`, `chain/site_chain.py:116`,
  `chain/backfill.py:99` (dry-run link key only for its origin) handle both origins.
- Markers `CH-9b1 origin: Finding-only` in `work/domain_action_index.py`, `work/site_index.py`,
  `work/adapters/postgres_work_store.py`, `site_outcomes/cold.py`, `site_outcomes/ev.py`.
- Tests: `tests/test_ch9b1_origin_readers.py` (Q5 allowlist guard, 5 non-vacuous mutations),
  `tests/test_ch9b1_opportunity_actions.py` (L0 origin/link/body/lifecycle + R6). `test_ch2_threads.py:182` updated
  to the typed origin.

## Next (in order)
1. Find the test DB URL (`backend/TESTING.md`, `backend/README-db.md`); run `test_ch2_thread_store_postgres.py`,
   `test_ch3_lifecycle_postgres.py`, `test_ch4_opportunity_postgres.py` to prove 0051 + link SQL.
2. L2 `tests/test_ch9b1_opportunity_actions_postgres.py`: reuse `seed_opportunities` (`test_ch4_opportunity_postgres.py:99`,
   MINIGRID site via `test_w402_reads_postgres._setup`) and the Cold service path (`test_w502_domain_intent_postgres.py:109`);
   create the mill Action via `DomainIntentService.create_action(domain="MINI", ...)`, a work case + `post_case_link`,
   COMPLETE it, `run_threads(steps=("b","c"))`, `run_lifecycle` -> ACTION_IN_HAND then CHANGE_APPLIED (day =
   case `occurred_at`); CHECK both ways (raw INSERT with both / neither pair -> 23514); upgrade/downgrade 0050<->0051
   (refusal with a MINI row); CH-4 R6 with linked Action at L2.
3. Byte-equality (Q6): the code at this revision cannot read a 0050 schema (readers name the new columns), so a
   literal "capture at 0050 with this code" is impossible. Proposed proof: seed Finding-origin S6 reserve trial
   (`test_s6_action_store_postgres` `harness`/`run_case`) + a Cold domain Action at head; capture board, Actions list,
   thread, verification and work-read bodies; add the mill Action, link, complete, run lifecycle; capture again;
   assert the Finding-origin bodies byte-equal. Plus: rows of `action`/`domain_action`/`chain_action_thread` are
   identical across a downgrade-to-0050/upgrade round trip. Record as a Known Deviation in the packet.
4. Scoped suites: `test_ch2_*`, `test_ch3_*`, `test_ch4_*`, `test_ch9_*`, `test_s6_*verification*`, `test_w50*`
   (domain intent/work), then guards A, W, N, V, M + outcome-id ratchet (one at a time, PowerShell, 10-min cap).
5. Polish clone (create -> migrate -> settle -> W6 0 violations -> fresh -> collect -> COH 0 new -> drop).
6. `git log main`: if lane-1 CH-5b2 added a migration, re-point 0051's `down_revision`.
7. Packet `.agent/review-packet-CH-9b1.md`; list the case/intent domain CHECKs: only `domain_action_domain_chk`
   (0035:47 -> 0051); `work_case` has no domain CHECK (`0027_w4_work_cases.py:15-31`).

## Open risks
- `all_actions` (dry-run) now reads `domain_action.origin_opportunity_id`, so dry-run no longer reads a DB below 0051.
- No outbox event is emitted on domain Action creation; a MINI Action created after its opportunity's placement is
  linked by backfill step c or the next `opportunity.revised` event, not immediately by the tick.
- Not yet checked: Postgres execution of any changed SQL; W6 on the new columns.
