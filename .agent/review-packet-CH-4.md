# Review packet CH-4: opportunity threads

**Branch:** `task/CH-4-opportunity`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch4`. It was cut from plan2 main `e207f328f`.
**Head:** `003f4baa6`, plus this packet's commit.
**Build sheet:** `AssetOpsV1-plan2\.agent\build-sheet-CH-4.md`, with rulings CH4-R R1–R7.
**Handoffs:**
- `.agent/CH-4-phase-1-handoff.md` holds the pre-flight answers P1–P8.
- `.agent/CH-4-phase-2-handoff.md` is the second handoff.

**Commits:**
- `fbb6d29a6` backend core;
- `ce5d6a901` L0 tests;
- `066ad51f9` the Findings count rule;
- `65d1b50bd` coherence;
- `cf08e1cbd` frontend;
- `e8f26789a` L2 and the Postgres fixes;
- `003f4baa6` the Site-substrate guard fix.

## Phase-3 audit of the uncommitted helper work (kept, in `e8f26789a`)

**`chain/lookup.py`, KEPT.** This is a real bug fix.
- `OPPORTUNITY_LOOKUP` read `s.site_name`, but the `site` column is `name` (M/0001; see the other readers, such as `postgres_estate_read.py:118`).
- Every Postgres opportunity read therefore raised UndefinedColumn. The sheet's illustrative §3 SQL has the same mistake.
- The fix is `'site_name', s.name`.

**`mini_decisions/opportunities.py`, KEPT.**
- This is sheet §2.3 / R3: each detail `day_rows[]` gains `headroom_kw` (equal to `opportunity_kwh`) and `window_hours: 1`.
- It is additive only. Stored revisions are untouched.

**Test-side changes:**
- `setup_cache.py` registers `seed_opportunities`.
- `test_ch2_thread_store_postgres.py` drops the `None` sources (R1).
- `test_w303_portfolio_scope_snapshot_postgres.py` changes UNSUPPORTED to NONE (old → new below).
- `test_w403_opportunity_read_postgres.py` adds the two new keys to `DAY_KEYS`.
- `test_ch4_opportunity_postgres.py` is new (L2).

## Acceptance (sheet §0, §4, §6, §7)

| Item | Status |
|---|---|
| R1: only `eligible_days >= 1` becomes an occurrence | Met. L0, L2, and L3 (`skipped_ineligible: 2`; the thread holds OPP-000003 and OPP-000004) |
| R2: the episode is the eligible days | Met. On the L3 SQL, OPP-000003 runs 31 Oct to 1 Nov 00:00 Addis, and OPP-000004 runs 31 Oct to 2 Nov 00:00 Addis (that is, 31 Oct–1 Nov). This matches L4 |
| R3: `headroom_on_every_eligible_day` and the `observed_headroom_range` alias; `headroom_kw`/`window_hours` on the wire | Met (L0, L2 `test_w403_opportunity_read_postgres`) |
| R4: an unpaged `opportunities` array from one builder for both screens | Met. COH-16 is 0 on L3 and fires when mutated (below) |
| R5: `thread_signal_key` and `lens_flags` only in `outcome_map.py` (OL-1) | Met. The item shows `lens_flags: ["OPPORTUNITY"]` |
| R6: SUPPORT_LOST for an opportunity thread | Met (L0, both directions) |
| R7: the board signal source is kept; only the href and `ref` change | Met. The 31 Oct board issue links to `/sites/KOBO-001/opportunities/<id>` |
| §0: Findings › Opportunities panel, lens table and All table | Met in the body and in vitest. See the verbatim text below |
| §0: Portfolio strip and panel from data; no fixed UNSUPPORTED/"Not established" | Met. FOUND, with 1 item and count 1 |
| §4.3: Site helper text and link | Met. The link is now passed in by the shell (`003f4baa6`) |
| §6: COH-6 with no expected entries, the COH-10 opportunity leg, COH-16 | Met. All are 0 on L3, and the legs fire on mutated real data |
| §7: P4 `G-portfolio-opportunity` retired | Met. M passes (42 tagged, 10 baselined) |
| MD-CH4-1..5 labels present | Met in `cf08e1cbd` (V passes, 14/14) |

## L3 on clone `assetops_chainclone_ch4_test`

The clone was made from `assetops_polish_full_test` with `tools/chain_clone.py`.
- **Create and migrate:** exit 0, 2 s.
- **Backfill a,b,c,d:**
  - a 139;
  - b 9 (NEW_THREAD 5, ADDED 4, ALREADY_PLACED 4, `skipped_ineligible: 2`);
  - c 3 (LINKED);
  - d 6 (ACTION_IN_HAND 3, CHANGE_APPLIED 2, RESOLVED_MONITORING 1), with skipped 0.
  - The headroom thread `2fc15fab-6652-5dfd-b337-57f8a6877268` is OPEN, with an effective day of 31 Oct.
- **Rerun:** a 0, b 0 (ALREADY_PLACED 13, skipped_ineligible 2), c 0 and d 0.
- **Settle:**
  - s2-comparison: exit 0, 2 s, "Evidence cutover: permitted".
  - tick: exit 0, 46 s, COMPLETED.
  - performance: exit 0, 2 s.
  - 2 files were recorded.
- **Collect:** 56 requests, all 200, in 152 s. It used `--work` set to the scratch `polish_work` copy, so nothing was written to polC.
- **Check against `expected-today.json`:**
  - COH-1 12/12, COH-2 2/2, COH-5 6/6, COH-7 10/10, COH-8 3/3;
  - COH-0/3/4/6/9/10/11/13/14/15/16: 0, with 0 new;
  - self-check 33 pass, 0 fail (39 before, minus the 6 deleted COH-6 entries).
- **Non-vacuity on the real bundle** (a mutated copy, then deleted):
  - With the board `ref.thread.id` changed and Portfolio `occurrences` set to 1, COH-10 reports 2 new: "split across 2 thread ids" and "shows 1 occurrences on portfolio.week; expected 2".
  - With the Portfolio item's `evidence` set to SUPPORTED, COH-16 reports 1 new: "Findings lists [('OPP-000004', 'OPEN', 'LIMITED')], Portfolio lists [('OPP-000004', 'OPEN', 'SUPPORTED')]".
  - COH-16 compares `(thread_id, code, state, evidence)` as specified. A changed `seen_line` alone does not fire it.
- **Episode ends:** SQL on the clone, in Addis local time.

  | Study | Occurrence | Start | End |
  |---|---|---|---|
  | OPP-000003 | #1 | 2026-10-31 00:00 | 2026-11-01 00:00 |
  | OPP-000004 | #2 | 2026-10-31 00:00 | 2026-11-02 00:00 |

- **Drop:** "dropped assetops_chainclone_ch4_test", "deleted 2 file(s) settle created under var/". The worktree is clean.
  - `assetops_chainclone_ch1b_test` (the other lane's clone) was left alone.
  - `assetops_demo3_full_test` was not touched.

### Verbatim

The texts are from the bundle bodies. The rendered texts are composed by the committed component code from those bodies; they were not taken from a browser.

**Findings › Opportunities item** (week, month and S are identical):
- title: "Daytime solar unused at Kobo mini-grid"
- seen_line: "Seen on 2 of 4 well-observed days · 28 Oct–1 Nov"
- limit_line: "Limited evidence: readings come from mixed sources, so the size is not worked out yet"
- state_label: "Open"
- short_label: "Kobo mini-grid daytime solar"
- study: OPP-000004, LIMITED, eligible 2 of 4 assessed, `headroom_kw` null, `window_hours` 1.

**Portfolio strip:** "1 opportunity: Kobo mini-grid daytime solar" (`summary.opportunity_count` 1, `opportunity_labels` `["Kobo mini-grid daytime solar"]`).

**Portfolio panel** (`opportunity.state` FOUND, 1 item, destination `/findings/opportunities`):
- Header: "GROW USEFUL DEMAND", "An opportunity beyond reducing cost", and the badge "What-if".
- Left: "Size not worked out yet" and "Daytime solar unused at Kobo mini-grid".
- Right: "No what-if yet" and "No what-if value worked out yet" (MD-CH4-4).
- Note: "Seen on 2 of 4 well-observed days · 28 Oct–1 Nov · Limited evidence: readings come from mixed sources, so the size is not worked out yet".
- Links:
  - "Review opportunity Finding →" goes to `/sites/KOBO-001/opportunities/f3e8d13f-3b7c-4348-824c-e912fd0869aa`;
  - "Inspect physical headroom →" goes to `/sites/KOBO-001/performance/renewable?from=2026-10-27T21:00:00Z&to=2026-11-01T21:00:00Z`.

**PRODUCTIVE_USE card:**
`{"basis": null, "basis_text": "Listed under Findings › Opportunities", "currency": null, "destination": "/findings/opportunities", "detail": "Kobo mini-grid daytime solar", "display_value": null, "group_key": null, "key": "PRODUCTIVE_USE", "line_keys": [], "state": "FOUND", "tone": "green"}`

**Kobo board, 31 Oct, OPPORTUNITY issue** (rows 0–2 carry the same issue; row 0 has role MOVES):
`{"href": "/sites/KOBO-001/opportunities/f3e8d13f-3b7c-4348-824c-e912fd0869aa", "kind": "OPPORTUNITY", "ref": {"code": "OPP-000004", "opportunity_id": "f3e8d13f-3b7c-4348-824c-e912fd0869aa", "thread": {"id": "2fc15fab-6652-5dfd-b337-57f8a6877268", "occurrence_no": null, "occurrences": 2, "segment_no": null, "state": "OPEN", "state_day": "2026-10-31", "state_effective_day": "2026-10-31"}}, "role": "MOVES", "text": "Productive-use headroom"}`

## Checks (counts)

**L0 and the related non-Postgres set** (17 files, phase 1 command): 377 passed, 1 skipped, at `dd9bfe2b5`.

**Non-Postgres rerun after the product changes at `e8f26789a`:** `test_ch4_opportunities`, `test_w403_opportunity_result`, `test_w301_estate_api` and `test_w303_portfolio_api` gave 49 passed.

**`tools/checks/test_chain_coherence.py`:** 84 passed, at head.

**Postgres, scoped, at `e8f26789a`:**

| Tests | Passed | Time |
|---|---|---|
| `test_ch4_opportunity_postgres` | 2 | 20 s |
| `test_ch2_thread_store_postgres` and `test_ch3_lifecycle_postgres` | 8 | 83 s |
| `test_w301_estate_index_postgres` and `test_w303_portfolio_fixture_postgres` | 22 | 495 s |
| `test_w303_portfolio_scope_snapshot_postgres` | 10 | 677 s |

- The helper's batch 1 gave 29 passed in 33 min on the same code before it was committed: ch4, ch2 thread store, ch3 lifecycle, `test_out_b4_board_postgres`, and w403 read, links and work_links. Of those, b4 and the w403 read/links tests were not rerun by me.
- Every run's harness template build calls `pg_harness.sweep_orphans()`, so the killed run's DBs were swept.

**Frontend:**
- At `cf08e1cbd`: typecheck clean, and scoped vitest 2831/2832. The one failure was the unrelated `siteFinancials` 409 test, which passes alone.
- At `003f4baa6`:
  - typecheck clean;
  - `miniDecisions.test.tsx` 56/56;
  - `s404SiteFindingIndex`, `estateRoots` and `estatePortfolio` 118/118.

**Guards:**
- A first FAILED at `e8f26789a`, because `frontend/src/sites/SiteFindingIndex.tsx` imported `FINDINGS_OPPORTUNITIES_PATH` from shell (the Site-substrate leaf rule).
  - The fix in `003f4baa6` gives `links.opportunities`, passed in by `SiteAnalyticsFrames.tsx`, the same pattern as `links.renewable`.
  - A now passes.
- W passes, N passes, V passes (14/14) and M passes.
- The estate guard self-tests were not run, because `configuration-persistence.ps1` and `test_estate_guard.py` are unchanged (P1).

## Deviations

**D1:** when the opportunity read raises, the Portfolio `opportunity.state` and the PRODUCTIVE_USE card read `UNKNOWN`, with "Opportunities could not be read". The sheet names only FOUND and NONE.

**D2:** Findings `summary.opportunity_count` is null unless the read is complete (the existing summary rule).
- On the polish data, every Findings window reads `status` UNKNOWN, so the Findings count is null while `opportunities` holds 1 item.
- The Portfolio count is 1.

**D3:** the board issue `ref.thread` carries `occurrence_no` and `segment_no` as null (an opportunity-level thread).

**D4, copy vs sheet §0:**
- The sheet's example text is "Daytime solar unused at Kobo" and "1 opportunity: Kobo daytime solar".
- The data gives "…at Kobo mini-grid" and "Kobo mini-grid daytime solar", because the copy uses the Site `name`.
- The values were not tuned.

**D5:** the Site helper's "Findings › Opportunities" is a link only when the shell passes `links.opportunities` (MINIGRID); otherwise it is plain text. The sheet's direct import breaks guard A.

**Frontend deviations:**
1. The whole empty block is hidden when items exist.
2. The NONE chart note keeps `OPPORTUNITY_NOTE`.
3. The strip reads "0 opportunities", and five WALK1-1 checks were updated.
4. The panel's Findings link carries the window through `estateHref`.
5. The `miniDecisions.test.tsx` helper test was updated (and again in `003f4baa6` for `links.opportunities`).
6. The registry entry was deleted, because no "retired" form exists.
7. The quantity is always "lo–hi".

**MOCK DEVIATION (labelled):**
- **MD-CH4-1:** no Portfolio priority-table opportunity row (that is CH-6). **Reported to the owner.**
- **MD-CH4-2:** no Depot "Chargers mostly idle" item (CH-8).
- **MD-CH4-3:** the item shows the study code OPP-000004, not an F-number.
- **MD-CH4-4:** "No what-if yet" instead of "$2.50".
- **MD-CH4-5:** the Kobo item reads "Limited evidence: readings come from mixed sources…" until CH-9.

**DS-R1:**
- Fixed:
  - Portfolio PRODUCTIVE_USE "Not established" and the opportunity `UNSUPPORTED`;
  - the WALK1-6 D5 two-count workaround;
  - 0-eligible studies placed as occurrences (R1);
  - the whole-window episode (R2);
  - "Opportunity index unavailable" (§4.3).
- Labelled keep:
  - the one-noon-hour basis and the board signal source (CH-9, CH-6);
  - the stored `opportunity_kwh` key (R3).
- Not touched: ASSET_LIFE (SWEEP-DS) and "Verified on example data" (CH-5a2).

**Expected body changes (old → new):**
- `opportunity` changes from `{state: UNSUPPORTED, …, destination: null}` to `{state: NONE|FOUND, items: [...], …, destination: "/findings/opportunities"}`.
- The PRODUCTIVE_USE card changes from UNSUPPORTED to NONE or FOUND.
- `summary.opportunity_count` changes from the board-derived count to the item count, and `opportunity_labels` is new.
- Detail `day_rows[]` gain `headroom_kw` and `window_hours`.
- `sources()` now yields `None` for ineligible revisions, after the placed ones.

## Residual risk

- The Findings count is null on the demo data (D2), while the Portfolio says 1. A screen that shows the Findings summary count would read "Unknown" beside a listed item.
- The board, `test_out_b4_board_postgres` and the w403 read/links Postgres tests were last run by the helper, before the commit, on the same product code. They were not rerun after `003f4baa6`, which is frontend-only.
- `vitest related` crashes on `findingLinkWordsParity.test.ts` (`.py?raw`). The scoped run excluded that file.
- There is no browser render of the panel or strip at 390 px beyond the vitest no-overflow-class case. Layout evidence was not run.

## Overlap with CH-1b (expect textual conflicts at merge)

- `tools/checks/test_chain_coherence.py`, and the `tools/checks/fixtures/chain_coherence/` bundles: every bundle gained or changed `findings_opp`/`portfolio` opportunity bodies. There are new bundles `clean_opportunity`, `coh16_opportunity_disagree` and `coh6_opportunity_missing`, plus `expected-threads.json` and `expected-today.json`.
- `backend/tests/test_ch2_thread_store_postgres.py`: the `None` filter at :124 and :164-166.
- `backend/assetops_backend/chain/backfill.py`: `_placeable` and `skipped_ineligible` in step b, in both the live and dry-run paths.
- `backend/assetops_backend/chain/adapters/postgres_thread_sources.py`:
  - in `_OPPORTUNITY_SOURCES`, `eligible_days` and `day_rows`;
  - the `sources()` order;
  - `opportunity_threads()`, and `lookup(site_id=, opportunity_window=)`.
- CH-4 does not edit `configuration-persistence.ps1`.

## User review

The sheet routes MD-CH4-1 to the owner as a report. Nothing else needs owner sign-off before the review. Do not merge before the Reviewer's verdict.
