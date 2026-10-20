# W3-02 pre-build seam re-check against merged W3-01 + W4-01 (2026-10-20)

Base: worktree `AssetOpsV1-plan2`, main `a1b29f81` (W3-01 merge `b5d0a7d6`, W4-01 merged earlier). Read-only. Spec under check: `.agent/W3-02-build-spec.md` (body + closures 1-3 + group-key, Run 5 and Run 6 amendments). Line refs are `file:line` on this revision.

Checks run: read the code and grepped it; computed the empty-scope digests with `estate.scope` in `.venv` (output under S5). No tests run. None were needed for a seam read.

**Count: 27 questions. 6 Blocker, 14 Should, 7 Nit.** Plus 15 items W3-01 already delivered (section D).

## Blockers

**B1. The shared parser and cursor do not admit `evidence`/`financials`.**
- Evidence: `estate/scope.py:40-42` `KEYS` has only `scope|findings|actions`, so `parse_request("evidence", ...)` raises `KeyError` at `scope.py:98`, which is a 500, not a typed 422.
- `decode_cursor` (`scope.py:185-211`) accepts only the Finding or Action key sets. It requires `page_one_mode`, and requires `after` to be exactly 2 strings whose first is a UTC instant.
- `EstateIndexService._fence`/`_cursor` (`index.py:108-136`) hard-code the 2-tuple and `kind:"actions"`.
- The spec cursor (`W3-02-build-spec.md:161`) has `kind:"evidence|financials"`. Evidence `after` is a 3-tuple of strings; money `after` is a 5-tuple with a nullable first element. It has no `page_one_mode`, and continuation basis semantics depend on that key (`index.py:97-99`).
- To decide: the exact v1 cursor key sets for the two kinds (add `page_one_mode`: yes or no), the `after` validation per kind, and who edits `scope.py`. It is an existing Lane A file, and Run 6 (`spec:364`) leaves no Lane A slot.

**B2. W1 `GENERATOR_SUPPORT` has no connection-taking source, and its per-day meaning is undefined.**
- Evidence: `ClaimLimitReadService.read` (`analytics/claim_limit_read.py:221-235`) calls `store.claim_limit_snapshot`, which opens its own transaction (`analytics/adapters/postgres_assessment_store.py:624-635`). The spec bans that call (`spec:22`, `spec:149`). W3-01 added no `claim_limit_*_on`.
- Semantics: a day's window revision "carries no single dispatch classification" (`claim_limit_read.py` WINDOW branch, `own.ceiling=None`). Ceilings and `support` exist only per interval revision (`interval_ceiling`, `:185-214`).
- Typed role reasons (`MISSING_ROLE`/`POOR_QUALITY`/`CONFLICTING` with `role`) come only from interval coverage. Window-limit reasons have no `role` (`_reasons`, `:158-182`), so a window-level read yields no admissible W1 gaps.
- The spec says one row per day citing "that day's assessment ID" (`spec:151`).
- To decide: (a) a Lane A `claim_limit_on(c, ...)` prerequisite, or (b) a pure re-derivation in Lane B. Also: which revision(s) feed a day row (window or intervals); how interval ceilings and support reduce to one day row; which reasons feed gaps.

**B3. Several cold/EV selected windows per Site, but four rows per Site.**
- Evidence: `estate_snapshots_on` returns one pinned snapshot per selected window intersecting `[from,to)` (`postgres_assessment_store.py:1848-1862` cold, `:2470-2481` EV).
- The UI default is seven days (`frontend/src/estate/estateShared.tsx:26-29`), so a Site normally has several windows.
- The spec gives cold and EV four rows per Site, keyed `(site_code_key,site_id,capability_key)` with no window suffix (`spec:32`, `spec:151`, `spec:155`). W1 got `@YYYY-MM-DD`.
- To decide: one row per window (key suffix?) or a reduction across windows. For a reduction, define the state rule, which `limitation`/`next_evidence` wins, and the `selected_revision_ids` union.

**B4. Cold/EV capability and money projections are private and unpinned.**
- Evidence: `EvSiteReads._capabilities(ctx)` (`ev_site_reads.py:386`) and `_select`/`_consequence` (`:237-266`) need a `ctx` that only `_ctx` builds, via the **unpinned** `open_on` (`:231-235`; `postgres_assessment_store.py:2711-2713`).
- Cold `ColdSiteReadService._capabilities(c,snap)` / `_money` (`analytics/cold_site_reads.py:424`, `:197`) are private.
- Neither service is in W3-01's composition. `estate/composition.py:327-334` builds `ColdReadService`/`EvReadService`, not the Site read services, and has no `EvMoneyReads`.
- Lane B may not edit these files (`spec:360`, `spec:364`).
- To decide: build `ctx={"c","t","s","code","snap"}` from a pinned estate snapshot and call the private methods, or have Lane A add public `capabilities_on(c,snap)` / `money_on(c,snap)` (needs a prerequisite slot).

**B5. The spec's Site link templates produce refused or empty Site pages.**
- Evidence: the spec carries the estate `from,to,known_at` onto cold/EV Site routes (`spec:191`, N4 `spec:325`).
- The cold Site read refuses a `known_at` later than the Site watermark with 422 `COLD_TIME_INVALID` (`cold_site_reads.py:161-166`). The estate `known_at` defaults to DB read time (`index.py:84`).
- Site reads select an exact stored window (`sel.window_start = :lo AND sel.window_end = :hi`, `postgres_assessment_store.py:1782-1800`), not a 7-day estate window.
- EV's own links use the selected window's `lo/hi/known` (`ev_site_reads.py:279-286`).
- To decide: the row's selected window plus the Site evidence cutoff, or the base route with `Opens current Site view`.

**B6. Commit sizing: "1-4 only" no longer holds.**
- Run 6 (`spec:364`) deletes every Lane A prerequisite.
- B1 (`scope.py`), B2 (`claim_limit_read.py` / assessment store), B4 (public `_on` wrappers, if chosen), S1 (`consequence_read.py`), S9 (`estate/composition.py`) and S7 (`estate_api.py`, if extended) all touch existing Lane A files before or inside commits 1 and 3.
- The integration column says only "Mount API" (`spec:11`, `spec:13`).
- To decide: restore a reviewed Lane A prerequisite `0` (scope/cursor kinds, claim-limit-on, composition, money fields), or explicitly let Lane B edit named files.

## Should

- **S1. The W1 money row lacks fields.** `select_consequence_on` returns no `window_start/end`, no `quantity_low/high` and no `overlap_group` (`financials/consequence_read.py:290-357`). The store's `head` has them (`SELECT *`, `financials/adapters/postgres_consequence_store.py:523`), but they are dropped. The spec row mapping needs them (`spec:173`). Decide: a Lane A extension, or a private `_store.selected_on`.
- **S2. There is no `power_interval_id`.** `financial_consequence_power_interval` has PK `(consequence_revision_id, evidence_id)` and no interval ID (`migrations/versions/0011_financial_consequences.py:157-172`). The spec names `...power_interval.power_interval_id` (`spec:173`). If technical IDs become `evidence_id`, they equal the cited power evidence (`consequence_read.py:313`), and the "technical vs citation overlap" tests degenerate. Decide the ID.
- **S3. Domain wire spelling.** W3-01 uses `mini_grid|cold_chain|ev_charging` (`estate/coverage.py:25-26`, in `coverage.sites` and the token `domain`). The spec says `MINIGRID|COLDCHAIN|EV_CHARGING` (`spec:155`) and `line_key "{domain}:{uuid}"` (`spec:177`).
- **S4. Envelope enums diverge.**
  - W3-01 `_status` returns `PENDING_RECOMPUTE`/`STALE_SOURCE` (`index.py:26-33`).
  - W3-01 empty scope gives `coverage.state:"COMPLETE"`, `status:"CURRENT"` (`index.py:36-40`, `all([])`).
  - The frontend types have no `EMPTY`/`EMPTY_SCOPE`/`PENDING` (`frontend/src/estate/estateClient.ts:16-22`, `:46-55`).
  - W3-01 historical responses add `summary.as_of` (`index.py:204`). The W3-02 spec has none.
  - The spec says `CURRENT|HISTORICAL|PENDING|UNKNOWN|EMPTY_SCOPE` and `EMPTY` (`spec:155`). Decide: reuse W3-01's enums, or keep new ones and add new frontend types.
- **S5. The literal empty-scope selection token is the `/1` digest.** `spec:206-207` shows `sha256:82eb9c5a…`, which equals `estate-selection/1`. Merged `/2` gives `sha256:5944cb919416dc307e7ce4b40c4cc4d047bcee9ec2d72b1a41815716b1d8765e`. `access_basis` `df70eb23…` is correct.
- **S6. Token arrays: reuse coverage or build per kind?**
  - W3-01 `site_coverage` fills mini-grid consequence and assumption IDs (`coverage.py:154-157`).
  - Cold picks one consequence per Finding revision regardless of `kind` (`estate/adapters/postgres_estate_read.py:211-214`), which misses a second `RECORDED_REPAIR`/`PRODUCT_EXPOSURE` head.
  - The spec wants these empty for Evidence and complete for Financials (`spec:163`).
  - Decide: Evidence/Financials build their own token items. Also whether the per-item `domain` is the coverage domain.
- **S7. The refusal wrapper has no endpoint extras.** `EstateRefusal.detail` (`scope.py:54`), `store_down` and 401 (`estate_api.py:260-269`) emit only `rows,total_count`. The spec needs `gaps:null` or `groups/exclusions/diagnostics:null` (`spec:159`, `spec:223`). Decide: a new `serve()` in `estate_evidence_money_api.py` that re-wraps, or a Lane A extension of `estate_api.py`.
- **S8. Scope, fence and envelope helpers are private to `EstateIndexService`.** They live at `index.py:76-147`, not in `scope.py`, contrary to the spec's "reuse W3-01 `estate/scope.py` authorization, snapshot and cursor" (`spec:7`). Decide: import the static privates, subclass, or have Lane A extract them.
- **S9. Snapshot and composition wiring.** One transaction must run W3-01 `site_coverage` (which needs `EstateSnapshot` methods) plus the new reads. Decide whether to subclass `PostgresEstateRead`/`EstateSnapshot` in `postgres_evidence_money_read.py`. Composition must go through `estate/composition.py`, because the guard admits adapter imports only from composition (`tools/checks/configuration-persistence.ps1:158-165`). That file is existing and Lane A owned.
- **S10. No `site_code_key`.** `imported_sites` orders by it but does not return it (`postgres_estate_read.py:84-91`). Row order and cursor `after` need the value (`spec:32`, `spec:161`).
- **S11. `total_count` on partial scope.** W3-01 nulls it unless coverage is complete (`index.py:211`, `:265`). The spec counts placeholders in `total_count` and nulls only the summary counts (`spec:155`). Decide: null or number.
- **S12. Who builds Site links?** The wire carries server `links.*` (`spec:35`, `:57`, `:191`) as W3-01 does (`index.py:182`). N4 (`spec:325`) tells the UI to build them with `siteEvHref`. Pick one owner.
- **S13. Registry shape.**
  - W3-01 added panels needing new `I-estate-finding-root`/`I-estate-action-root` nodes, with status `gap` (`frontend/docs/architecture/v69-dependency-registry-pilot.json` panels `findings:1`, `actions:1`).
  - W3-02 names only existing nodes and `globalevidence:1-2` / `globalfinancials:1-2` (`spec:139`, `:185`).
  - Decide: new `I-estate-evidence-root`/`I-estate-money-root` nodes, panel titles, and the post-review status.
  - Note: the merged W3-01 panel reasons still say "awaits independent review".
- **S14. Frontend client seam.** `App` has one `estateIndex?: EstateClient` prop (`frontend/src/App.tsx:209-236`). The frames live in `shell/EstateRootFrames.tsx` (Lane A). Decide: extend the existing `EstateClient` interface (`estateClient.ts:179-183`) or add a new `estateEvidenceMoneyClient.ts` with a new App prop. Name the frame file owner.

## Nit

- **N1. Mock measurement rounding.** `.agent/W3-02-mock-measurements.md:33-38` floors (290/313/315/702/292/447). Closure 1 (`spec:193`) ceils (291/314/316/703/293/448). Closure governs; fix the doc.
- **N2. Date bar wording.** The spec says `Window: {from}–{to exclusive} · UTC` (`spec:185`). The shared bar says `Window {from} to {last included} (UTC days)` (`estateShared.tsx:118-120`). Use the shared bar.
- **N3. Tones and StatusBar.** "Neutral" card tone is `MetricTone` `muted` (`ui/V69Layout.tsx:16`). The `StatusBar` doc suggests `ProductStatus inline` (`V69Layout.tsx:181-186`), but the spec forbids `ProductStatus` (`spec:185`). Add a one-line note.
- **N4. Superseded body text is still present.** Examples: limit 25, a cursor with `limit`, 403/404 codes, the 25 default, the `consequence_revision_id asc` order, the gap-row key (`spec:32`, `:52`, `:107`). The API module path `estate_evidence_money_api.py` is not located (W3-01 put `estate_api.py` at package top). Prune or mark these.
- **N5. Required test count.** "+19" includes three guard tests that already exist (D7), so the W3-02 delta is +16 (`spec:201`).
- **N6. EV `STALE_BASIS` is a read guard.** It returns `state:"WITHHELD", reason:"STALE_BASIS"` and is never stored (`ev_site_reads.py:13`, `:249`, `:255-263`). Clarify the eligibility table row (`spec:175`, `:268`).
- **N7. Test location drift.** Closure-3 C2 names `test_w301_estate_index_postgres.py::test_selection_token_v2_endpoint_cursor_compatibility`; it is actually `backend/tests/test_w301_estate_api.py:133`.

## D. Already delivered by W3-01: remove from the W3-02 spec

1. `select_dispatch_days_on` and the multiday/historical selector proof: `postgres_assessment_store.py:685`; `test_w301_w1_snapshot_helpers_postgres.py:108`, `:161`.
2. Former `0a`, `ConsequenceReadService.select_consequence_on`: `consequence_read.py:274`; tests in `test_w301_w1_money_snapshot_helpers_postgres.py:116`, `:141`, `:283`.
3. Former `0b`, `MoneyEligibility.for_finding_on`: `money_eligibility.py:192`; tests in the same file at `:177`, `:260`, `:271`.
4. `estate-selection/2` with the four extra arrays: `scope.py:23`, `:153-175`.
5. The strict shared parser (unknown/repeated keys): `scope.py:90-123`. Only the evidence/financials key sets are missing (B1).
6. `$pgReaders` already lists `estate/adapters/postgres_evidence_money_read.py`, and the `estate` domain entry exists: `configuration-persistence.ps1:794-795`, `:158-165`.
7. Guard self-tests `test_pg_reader_import_allowed`, `test_pg_reader_write_rejected`, `test_domain_driver_import_rejected`: `tools/checks/test_estate_guard.py:79`, `:89`, `:100`.
8. Former `0c` endpoint proof: `test_w301_estate_api.py:67`, `:107`, `:133`; `test_w301_estate_index_postgres.py:224`, `:261`.
9. Refusal codes and messages, the 401 `WWW-Authenticate`, and UI refusal copy: `scope.py:25-37`; `estate_api.py:266-269`; `estateClient.ts:146-157`.
10. The shared date bar with the seven-complete-UTC-day default and `known_at` omitted: `estateShared.tsx:26-29`, `:91-157`.
11. The six-key public provenance projection: `evidence/public_provenance.py:199-201`.
12. The seven-key `coverage.sites` item and `scope.tenant_id`: `index.py:43-47`, `:139-147`.
13. The 390 px 2+1 card grid comes from shared CSS (`ui/primitives.css:4561-4566`, `estate/estate.css:134-138`), so no page CSS is needed for it.
14. Migration head: `0027_w4_work_cases.py` is the single head, and `0028` remains unused (`backend/migrations/versions/`).
15. The estate router mount pattern and 503-without-database: `main.py:465-469`, `estate/composition.py:337-339`. W3-02 adds only its own mount.
