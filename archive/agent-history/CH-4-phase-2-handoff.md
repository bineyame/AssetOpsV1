# CH-4 phase 2 handoff (PARTIAL: coherence and frontend landed; L2 work uncommitted; L3, guards and packet open)

Branch `task/CH-4-opportunity`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch4`. Read phase 1 handoff first.

## Landed this phase
- L0 plus the related non-Postgres set, rerun at `dd9bfe2b5`: 377 passed, 1 skipped.
- `65d1b50bd` coherence (§6), in `tools/checks/chain_coherence.py`:
  - COH-6 reads `_opportunity_items` (Findings `opportunities`, Portfolio `opportunity.items` + FOUND);
  - COH-10 opportunity leg `_coh10_opportunity_thread` (one thread id across Findings, Portfolio and board
    `ref.thread`; `occurrences == len(expected)` when `known_at` is null);
  - COH-16 `coh16_opportunity_agreement`;
  - a new manifest stamp `opportunities` (collector, as `threads`/`lifecycle`).
  - Fixtures: `clean_opportunity`, `coh16_opportunity_disagree`, and `coh6_opportunity_missing` (renamed from
    `_missing_row`). Every bundle moved to the item bodies.
  - `expected-threads.json` kobo-headroom is OPP-000003/4, and the 6 COH-6 expected entries are deleted.
  - `test_chain_coherence.py`: 84 passed, including the non-vacuity test
    `test_clean_opportunity_bundle_passes_and_judges_the_headroom_thread`.
- `cf08e1cbd` frontend (§5, §4.3, P4 retirement).
  - Typecheck is clean, and the missing-claim, registry, mock-gap and MD-label guards all pass.
  - Scoped vitest: 2831/2832. The one failure was an unrelated `siteFinancials` 409 test, which passes when run alone
    (likely load).
  - `vitest related` crashes on `findingLinkWordsParity.test.ts` (`.py?raw`), so it was run with that file excluded.
  - Frontend deviations for the packet:
    1. the whole empty block is hidden when items exist;
    2. the NONE chart-note keeps `OPPORTUNITY_NOTE`;
    3. the strip reads "0 opportunities", and five WALK1-1 checks were updated;
    4. the panel links carry the window via `estateHref`;
    5. `miniDecisions.test.tsx` helper test updated;
    6. the registry entry was deleted, because no "retired" form exists;
    7. the quantity is always "lo–hi".
  - A `frontend\node_modules` junction to plan2 is present and uncommitted.

## UNCOMMITTED (a subagent was still running when this session ended)
The L2 subagent (steps 1–2 and the §2.3 detail `day_rows` `headroom_kw`/`window_hours`) left these files modified and
not committed:
- `backend/assetops_backend/chain/lookup.py`
- `backend/assetops_backend/mini_decisions/opportunities.py`
- `backend/tests/setup_cache.py`
- `test_ch2_thread_store_postgres.py`
- `test_w303_portfolio_scope_snapshot_postgres.py`
- `test_w403_opportunity_read_postgres.py`
- probably the untracked `backend/tests/test_ch4_opportunity_postgres.py`

Resume steps:
1. Review `git diff` of those files, especially `chain/lookup.py`, a product change whose cause the subagent did not report.
2. Run the Postgres scoped set from the phase-1 handoff step 2, plus `test_ch4_opportunity_postgres.py`, and commit.

## Remaining
1. Finish and commit L2 and the Postgres fixes (above).
2. Guards A (`tools/check-architecture.ps1`), W (`tools/check-agent-workflow.ps1`), N and V.
3. L3 on the `ch4` clone, per sheet §8.5. A scratch copy of the polish work dir's top-level JSON is at
   `C:\Users\assef\AppData\Local\Temp\claude\C--Users-assef-Bineyame-AssetOpsV1\809ecc09-3853-48b6-b795-60539b50a963\scratchpad\polish_work`
   (pass it as `--work`). Check the episode ends with SQL on the clone, and record the verbatim texts. Then drop the
   clone.
4. Write the packet `.agent/review-packet-CH-4.md` with D1–D3, the frontend deviations above, and MD-CH4-1..5.
