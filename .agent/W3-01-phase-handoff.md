# W3-01 phase handoff (commit 1, Lane B part complete, 2026-10-20)

Branch `task/W3-01-estate-claim-action-roots` (worktree `AssetOpsV1-review2`). Lane B commits: `1c409a3d` (core),
`990f2113` + `2951b66c` (completion, Run 1 rulings 2/4/5/6). **Branch released to Lane A** (ruling 1). No Lane A
call site, migration or Alembic head touched.

## Landed (`backend/assetops_backend/evidence/public_provenance.py`)
- Ruling 2 `*_selection` helpers; `finding_revision`/`consequence_revision` default to the W1 row sets.
- Ruling 4 `PublicProvenance.ev_selected(..., persisted_class)` with `SOURCE_CLASS_MISMATCH`.
- Ruling 5 `dual_blocks(selected, pending)`; ruling 6 `estate_projection`; `LinkRowsReads` for one-connection
  set reads.
- Tests (`backend/tests/test_w301_provenance_dto_postgres.py`): `test_empty_foreign_broken_and_mixed_precedence`,
  `test_persisted_ev_class_disagreement_unknown`, `test_w1_revision_selection_sets_and_estate_projection`,
  `test_pending_dual_blocks`.

## Checks (private `w301b_test`, dropped after)
- Focused file: 4 passed (22.6 s). Mutations after commit, each reverted with `git checkout`: UNKNOWN override
  removed -> FAIL; consequence default selection minus Finding revision -> FAIL; `dual_blocks` alias -> FAIL.
- `tools/check-architecture.ps1` passed. Full suites, workflow guard: not run (out of scope).

## Next
1. **Lane A** (exclusive checkout): compatibility commit per `.agent/W3-01-lane-a-adapter-contract.md`.
   Open q2 items in `.agent/W3-01-pending-rulings.md` (empty-envelope shape; cold pending set) block parts of
   its cold/EV envelope work.
2. **Lane B** after Lane A releases: `test_w1_cold_ev_exact_cited_id_mapping` (ruling 7) against the integrated
   public reads; then review of `1c409a3d..<that commit>`; then W4 cherry-pick per ruling 1.
3. Then W3 commit 2 (estate read/API) per spec.

## Lane A compatibility run (2026-10-20): stopped on rulings, no code committed
Merged main into the branch (`1f731005`, clean, Run 2 rulings present). Dry-read all ruling-1 call sites, then
stopped per the no-decision rule: `.agent/W3-01-pending-rulings.md` (q3) items 1-3 block the cold/EV envelope
work (EV no-head unassessable read vs empty DTO; detail-read top-level DTO; row DTO key and EV session cited
set); items 4-6 are readings (composition wiring via new `build_public_provenance` and a `ColdReadService`
`link_rows` kwarg; fail-closed `unresolved` blocks keep their shape; `dual_blocks(None, None)` still raises,
so Lane B's q2-ruling-1 change is a precondition). No test, DB or check-all run (no code changed).
Anchors for the resumed run: cold `_envelope` `postgres_assessment_store.py:1655`, fence reads 1864/1892,
`cold_site_reads.py:505`; EV `_snapshot` 2102, `_envelope` 2184, `_page` 2320, `page_on` 2362; W1 resolver
injection `analytics/composition.py:build_finding_read_service`, `financials/composition.py:45-63`.
**Branch released** (Lane A holds nothing). Next: Architect answers q3 and Lane B lands the `dual_blocks`
empty case; then Lane A resumes the one compatibility commit.
- Lane B q2/q3: dual_blocks(None, None) now returns the literal six-key EMPTY_CITATION_SET alias plus two null siblings (no signature change); test_pending_dual_blocks updated; 4 passed on w301d_test.

## Lane A compatibility run 2 (2026-10-20): stopped on q4, no code committed
Resumed at `9239fb45` (Lane B both-null `dual_blocks` present). Built the q3 map except EV money, then stopped:
`.agent/W3-01-pending-rulings.md` q4 item 1 (EV money rows have `finding_revision_id` always NULL, so the
literal q3 refusal would 503 every stored EV money read); items 2-6 are readings built into the patch.
Partial diff (uncommitted code, reverted from the tree): `.agent/W3-01-lane-a-partial.patch`
(`git apply` on this branch). It covers: `evidence/composition.py:build_public_provenance`; W1 injection in
`analytics/composition.py` (+ `build_cold_read_service` `link_rows`) and `financials/composition.py`; cold
`ColdReadService` (`_public`, `selected_basis`, `_pending_ids`, `_provenance_blocks`, `_envelope(c, ...)`,
`envelope_on(c, ...)`, row DTO in `_item`, detail override, `consequence_provenance_on`); `cold_site_reads.py`
(`envelope_on(c, ...)`, private cursor basis, `consequences[].source_provenance`); EV (`job` flag in
`_snapshot`, `_provenance_blocks`, `_envelope`, session union row DTO, Finding row DTO, `_page(basis)`,
`page_on` route|basis). Imports verified; no test, DB or check-all run yet.
Not yet done: EV money row blocks (`ev_site_reads.py`, `EvMoneyReads._with_links`) pending q4; all q3 test
changes; `frontend/src/sites/sourceProvenance.tsx` + its tests. **Branch released** (Lane A holds nothing).

## Lane A compatibility commit (2026-10-20): landed, branch released to Lane B
Merged main (q4 rulings + selection token v2 present), applied `.agent/W3-01-lane-a-partial.patch`, finished the q3
map with the q4 corrections. One commit (`W3-01 Lane A: compatibility integration`). Lane B files untouched.
- EV money (q4 ruling 1): `EvReadService.money_row_provenance_on` (`postgres_assessment_store.py`, after
  `_provenance_blocks`) selects `{row id, stored assessment, every ev_consequence_session revision}`, cites only
  `ev_consequence_evidence`; NULL Finding pin expected; non-null pin, missing assessment or a linked session not in
  the tenant/Site naming that assessment -> `EvReadUnavailable`. `ev_site_reads.py:financials` adds it to the current
  stored row and every history row; guard rows get none. `_EV_REVISION_SQL` also selects `r.finding_revision_id`.
- Frontend: `sourceProvenance.tsx` (optional public keys, `classification ?? state`, `detail` first, safe empties,
  `SOURCE_CLASS_MISMATCH` copy); cold/EV client types gain the two siblings (`ColdSourceBlock`, `EvSourceBlock`).
- Tests: W1 compat `test_s4_power_demo_case_postgres.py::test_source_state_compatibility_all_w1_consumers`; q3/q4
  edits in w203, w204, w206 (incl. `test_session_row_cites_meter_interval_outside_session_evidence`), w207 site,
  w207 money (`test_ev_money_row_provenance_uses_stored_window_links_without_finding_pin`), S4 Finding read /
  evidence history / Finding API, S4 consequence history, S5 overview, S6 action records; frontend
  `sourceProvenance`, `coldRoutes`, `evAssessmentRoutes`.
Readings (none blocking; confirm at review):
1. q4 EV money set is inlined (sorted distinct) and passed to `cited_set`; no Lane B helper added.
2. EV money integrity failures tested by direct `money_row_provenance_on` calls on the real DB (FKs prevent
   storing an inconsistent row); the public path covers present/history/zero-link/page-size.
3. Cold overview's Finding projection (`cold_site_reads.overview.findings.items`) is unchanged; the rows it
   consumes (`current_findings_on` -> `_item`) carry `source_provenance`, as do `/cold/findings` items.
4. Public reasons keep resolver extras, so w206 `_reasons` now requires `{code, accepted_evidence_ids}` as a subset.
5. Test-only DB edits: w206 marks open EV jobs DONE then restores them (no-job vector), inserts one EXCLUDED
   `ev_meter_interval` row (meter vector); w203 inserts then retires (DONE) a cold job (rows are never deleted).
6. S6 harness keeps `build_source_provenance`; the S6 test checks the production `build_finding_read_service`
   block for the same origin revision instead (golden contract bodies unchanged).
7. Open copy item: EV Finding detail "Assessment basis (SHA-256)" (`EvAssessmentViews.tsx:673`, and :324 for the
   envelope) now shows the public row/envelope digest, not the stored assessment basis; label left unchanged.
Checks (private `w301e_test`, dropped): final w203+w204+w206 44 passed; w207 site+money 32 passed; S4 Finding read,
power demo, consequence history, S5 overview 20 passed; evidence history + consequence read 8 passed; S6 1 passed;
Finding API 17 passed. Frontend: typecheck clean; 9 files 344 passed. check-all: 9/10, the one FAIL is pre-existing
on main (`Evidence width check`: `tools/measure-mock-panels.mjs` from main `29dea85f`, untouched here).
**Next:** Lane B `test_w1_cold_ev_exact_cited_id_mapping` (use the q4 EV money set), then commit-1 review.

## Lane B ruling-7 test (2026-10-20): landed; commit-1 unit ready for review
Merged main (`96b86c83`, clean). `6823d7d0` adds `test_w301_provenance_dto_postgres.py::test_w1_cold_ev_exact_cited_id_mapping`
(params `w1`, `cold`, `ev`). Each digest is recomputed by the file's own `digest()` from scoped DB sets; page size 1
(all cursors) vs 200 gives identical row and envelope blocks. W1: `power_site` + P01, consequence read, Finding read,
history at limit 25 vs 1. Cold: findings envelope, Finding rows/detail, `financials.consequences[]`. EV: all six
replays, sessions/findings rows + detail, envelope, q4 money set on the UNPRICED and priced stored rows.
Readings (none blocking; confirm at review):
- L-B1: cold uses `normal` (named) plus `excursion`, which adds the Finding and consequence rows so the row
  mapping is proven on non-empty sets (the test asserts it saw at least one of each).
- L-B2: the contract fixtures are pinned replay manifests rather than input data. The test builds each case through the
  same W2 replay `Chain`, using an inline copy of the `chain` fixture body, because both modules name their
  fixture `chain`.
- L-B3: W1 is read through the public service layer, as `test_source_state_compatibility_all_w1_consumers` does.
  The test makes no HTTP call for W1. Cold/EV selected IDs come from the public read (watermark
  `assessment_revision_ids`, item `revision_id`s); pins and cited sets come from the DB.
Checks: whole file 7 passed (264 s) on private `w301f_test`, which was dropped afterwards. Mutation after commit: dropping the cold
episode revision and the EV money session links from the expected selection made cold and ev FAIL on
`basis_sha256`. Reverted with `git checkout`. check-all: 10/10 passed.
**Next:** review `1c409a3d..HEAD` as the W3 commit-1 unit, then the W4 cherry-pick per ruling 1.

## Fix round r1 (commit-1 review rulings M1, M2, M3.1, M3.2, L1-L5)
| Finding | Fix | Test |
| --- | --- | --- |
| M1 digest copy | Cold claim refs and EV sessions refs read `selected_source_provenance` (`Selected source basis (SHA-256)`, `Not recorded` when null); EV Finding detail `Finding source basis (SHA-256)` on the row block | `coldRoutes::selected_source_basis_survives_pending`; `evAssessmentRoutes::selected_and_finding_source_basis_survive_pending` |
| M2 source owner | `selectedSourceBlock`/`selectedClassification` (`sourceProvenance.tsx`) used by cold claim facts, cold Site record/claim-rule rows, EV strip badge, EV Site claim line, financials line, assumptions badge; pending class shown only as `Current accepted evidence source`; EV Evidence Analysis record line and sessions `SourceReasons`/`sourceDetail` labelled current-set; backend `claim_rules[].source_class` from the selected block (`ev_site_reads.py`) | `coldRoutes::pending_source_does_not_relabel_cold_claim_or_site_rows` (+ `coldSiteViews.test` row case); `evAssessmentRoutes::pending_source_does_not_relabel_ev_selected_badges_or_rows`; `evSiteMoneyRoutes::selected_claim_rules_and_money_lines_ignore_pending_class`, `::current_accepted_record_line_names_pending_class`; `test_w207_ev_site_reads_postgres::test_claim_rules_source_class_is_selected_not_pending` (fails with the old line) |
| M3.1 withdrawn, dropped session | `_findings` selects `fr.transition`; lifecycle and transition NO_LONGER_SUPPORTED with a stored session id and zero matches use `ev_withdrawn_finding_row_selection` (two IDs); every other missing/duplicate session still refuses | `test_w206_ev_reads_postgres::test_withdrawn_finding_dropped_session_detail_has_two_id_provenance` (real second loop via rebind START + `select_exact`; SUPPORTED-with-missing-session 503 inside) |
| M3.2 historical cutoff | cold `pending_since` and EV `job` queried only when `not historical and known is not None`, plus `created_at <= :k` | `test_w203::test_historical_cutoff_precedes_pending_job`; `test_w206::test_historical_cutoff_precedes_pending_job` (extended existing test) |
| L1 | test only | `test_w206::test_public_selected_ev_class_mismatch_unknown` |
| L2, L5 | accepted as backlog, no change | none |
| L3 | named test maps to `test_w203::test_pending_historical_reload` plus the M2 tests above | none |
| L4 | `.agent/W3-01-lane-a-partial.patch` removed | none |
Readings to confirm: (1) M3.2 `:k` is the explicit `known_at` only (NULL on default reads): a default read has `known` = watermark and a job's `created_at` is after it, so `:k = known` would hide every real pending job (`test_w203::test_typed_errors_and_unknown_200` fails). (2) EV historical test name already existed; extended, not duplicated. (3) `evSiteRoutes.test.tsx` does not exist; the two named tests are in `evSiteMoneyRoutes.test.tsx`. (4) Test updates to `assessment_revision` use `SET LOCAL session_replication_role = replica` (append-only trigger), restored in `finally`. (5) The Finding strip falls back to the row's own block when no `selected_source_provenance` sibling exists. (6) Open copy item 7 above is now closed.
Checks (private `w301g_test`, dropped): w203 6 passed (5 full-file run + new test alone); w206 reads + w207 site reads 42 passed (1702 s); frontend cold/ev/coldSite/sourceProvenance files passed; tsc clean; check-all 10/10.

## Lane B commit-2 run (2026-10-20): stopped on q5, no code written
Merged main (already up to date at `e0d7ab04`). Read the full spec, including the review closures, q1-q4, r1, the token v2
amendment and the W3-02/W3-03 amendments (token v2, the W3-02 Q8 `$pgReaders` guard, the parser key rule and the
`group_key` owner = W3-02). Stopped before writing code because of the no-decision rule. `.agent/W3-01-pending-rulings.md` (q5) holds
blocking items 1-3: every W1 selection read (`postgres_finding_store.index_snapshot/fence/index_lineage`,
`DispatchReadService.window`, `postgres_action_store.site_window`) opens its own transaction, so a one-transaction
estate read needs connection-taking variants in Lane A files; the W1 mini-grid read has no as-of `known_at`
selection (W3-02 `0a`'s `select_dispatch_days_on` appears to be that dependency); and the estate adapter's driver
import fails rule 8 until Lane A adds `$pgReaders`. Readings 4-9 are listed there. Lane A asks are in
`.agent/W3-01-lane-a-requests.md`. No DB was created and no test or check-all was run, because no code changed.
**Next:** the Architect answers q5; then the Lane A prerequisites land; then Lane B builds commit 2 from this spec.

## Lane A q5 prerequisite (2026-10-20): ready for its review
Merged main (`Run 5 rulings (q5)` + W3-02 amendment, no conflict). ONE commit (see `git log -1 -- backend/tests/test_w301_w1_snapshot_helpers_postgres.py`):
- `postgres_finding_store.py`: `fence_on`, `index_snapshot_on`, `index_lineage_on` (+ `FindingPinRefused`); `index_snapshot`/`index_lineage` are wrappers over shared `_index_snapshot`/`_index_lineage` (output unchanged).
- `postgres_assessment_store.py`: `select_dispatch_days_on` (+ `_dispatch_day_on`, `_transaction_time`); `_window` gains keyword-only `cutoff`/`all_jobs` (defaults keep the S3 read byte-identical).
- `postgres_action_store.py`: `site_window_on`; `site_window` wraps `_site_window(..., None)`.
- `configuration-persistence.ps1`: the exact `$pgReaders` line and `$isPgReader` refusal branch only.
- `backend/tests/test_w301_w1_snapshot_helpers_postgres.py`: the three named q5 tests.
Readings (confirm at review):
- R1 `$pgReaders` timing: the dispatch put the allowance here; ruling 3 puts "this guard/domain change" in Lane A's second handoff. Landed the `$pgReaders`/`$isPgReader` part (inert until the files exist); **deferred** the `$domains` `estate` entry and `test_pg_reader_*`/`test_domain_driver_import_rejected` to the second handoff, since ruling 3 says the domain entry fails anti-vacuity before `estate/composition.py` exists.
- R2 `index_snapshot_on` returns no `fence` (use `fence_on`), adds `known_at` and `selected_runs` {window_start: run_id} (the "selected IDs"); the wrapper drops `selected_runs` so W1 output is unchanged. Merge links in heads and `merges` are filtered by `finding_merge.created_at`.
- R3 `index_lineage_on` refuses with `FindingPinRefused(missing, later, known_at)` (a `LookupError`) before reading anything.
- R4 `select_dispatch_days_on` day dict keys: `day, window_start, window_end, known_at, available, unavailable_reasons, status, status_reasons, selection{seq,selected_at,selected_by_job,run_id}, run_id, assessment_revision_ids, window_assessment_revision_id, accepted_reading_count, input_sha256, configuration_sha256, accepted_watermarks (run.watermarks), jobs`. `status` is `derive_status` at the cutoff basis (`EvidenceQuery(knowledge_at=known_at)`); the estate layer labels it HISTORICAL. `from_ >= to` returns `[]`.
- R5 job state at a cutoff: `recompute_job` has no transition time. If `known_at >= now()` (caller's transaction time) jobs are read exactly as S3 does (`_LIVE_JOBS`, `created_at <= k`). Below it: PENDING/LEASED now = outstanding then; DONE with a selection of that job `selected_at <= k` = finished; anything else (DONE without such a selection, FAILED) makes the day `available=False` with `JOB_STATE_AT_CUTOFF_UNKNOWN`. A selected run with `completed_at > k` or a revision `created_at > k` is also unavailable. Known limit: a job widened after `k` (`UPDATE window_start/window_end`) can appear as overlapping at `k`.
- R6 `selected_at` is the worker's lease-time clock, not a commit fence (`CUTOFF_LABEL`); the cutoff filter uses it as ruled.
- R7 the test pins `_transaction_time` to the fixture's present via `monkeypatch` (the fixture clock, 2026-10-30, runs ahead of the DB clock), so both cutoffs exercise the historical branch and the present exercises the live branch.
- R8 adapter now imports `assessment_worker` (`DISPATCH_ROLES`, `DOMAIN`, `input_basis`) and `dispatch_read` (`day_window`, `derive_status`); no import cycle.
Checks (private `w301i_test`, dropped after): new file 3 passed (33 s). Existing touched-store tests: `test_s4_finding_index_postgres`, `test_s4_finding_store_postgres`, `test_s3_dispatch_assessment_postgres`, `test_s3_dispatch_read_postgres`, `test_s3_claim_limit_postgres`, `test_s6_action_store_postgres`, `test_s6_site_action_index_postgres`, `test_s6_site_action_index`: 85 passed (462 s). Mutations after commit, reverted with `git checkout`: drop `_window` `selected_at` cutoff, drop event `recorded_at` cutoff, drop Finding head `created_at` cutoff -> all 3 tests FAIL. Guard probe (temp files, removed): reader driver import not flagged; non-reader driver import flagged; INSERT in a reader flagged. check-all: 10/10 PASS (143 s).
**Branch released.** Prerequisite commit `a75b0291`. Next: independent review of this commit; then Lane B retakes the branch for the estate core.

Prerequisite fix r1: applied M1 (DONE job reconstructed at cutoff via min(selected_at); outstanding jobs normalized PENDING; DONE-no-selection and FAILED stay JOB_STATE_AT_CUTOFF_UNKNOWN), L1 (as-of day rule), L2 disclosed (carry to commit-2 packet), L3 confirmed. Tests: snapshot-helpers + S3 dispatch read 13 passed on w301k_test (dropped); check-all 10/10.

## Lane B commit-2 run 2 (2026-10-20): stopped on q6, no code written
Resumed at `15dae742` (`git merge main`: already up to date; prerequisite `a75b0291` + fix r1 present). Read the
commit-2 spec, q1-q5, r1, the prerequisite r1 rulings, the token v2 amendment and the W3-02 Run 5 amendment, then
dry-read the consumed seams. Stopped under the no-decision rule. `.agent/W3-01-pending-rulings.md` (q6) has two
blocking items:
1. The cold and EV `_snapshot` reads select only a run whose window covers (cold, `:1728`) or equals (EV, `:2311`)
   the requested window. Their selection windows are data-bracketed (hourly in the fixtures), so a whole-day
   estate window selects nothing.
2. Mini-grid consequence/Cost needs `select_consequence_on`/`for_finding_on`/source gate on the estate
   connection. These are W3-02 `0a`/`0b`, which are scheduled after W3-01.

Readings 3-9 there cover the auth seam, historical rule, mini-grid state, unsettled-Site rows, read_at, Action
coverage and the reduce input. No DB was created, and no test or check-all was run, because no code changed.
**Carry to the commit-2 packet (prerequisite r1 L2, accepted):** a PENDING job's window can be widened in place
after `k`, and no stored window history records its earlier bounds. Such a job can therefore show as outstanding
on a historical mini-grid day it did not cover at `k`. That day is reported as pending, not unavailable.
**Branch released.** Next: the Architect answers q6, then Lane B builds the estate core.

## Lane A q6 prerequisites (2026-10-20): four commits, each ready for its own review
Merged main at start (Run 6 rulings, W3-02 amendment) and again after `0b` (W4-01 Run 3 ruling 6; `.agent/*` only).
No `estate/` module written. Private DB `w301m_test` (dropped after).

1. **`2a1b59cf` prereq re-review Low.** `postgres_assessment_store.py:_dispatch_day_on`: the
   `JOB_STATE_AT_CUTOFF_UNKNOWN` reason now ends `no stored completion selection establishes its state at the
   cutoff` (code and outcome unchanged). Test asserts the exact suffix and absence of the old phrase.
   Reading 1a: the old phrase was followed by "at the cutoff"; the whole tail was replaced so the text does not
   read "at the cutoff at the cutoff". Checks: snapshot-helpers + S3 dispatch read 13 passed.
2. **`c55dadd4` `0a`.** `ConsequenceReadService.select_consequence_on(c,t,s,finding_revision_id,known_at)`;
   adapters `PostgresAssumptionStore.snapshot_on`, `PostgresConsequenceStore.load_input_on(..., known_at=None)`
   and `selected_on` (public `snapshot`/`load_input` now wrap them, same SQL). Returns `consequence_revision_id`,
   `revision_no`, `consequence_state`, `currentness{state,reasons}`, `amount_low/high`, `currency`, `basis`,
   `price`, `cited{assessment_revision_ids,assumption_revision_ids,power_evidence_ids,price_revision_id}`.
   Readings: 2a `financial_consequence_revision` has no `created_at`; its insert time `recorded_at`
   (`clock_timestamp()`) is the `<= :k` filter, order `(revision_no DESC, id DESC)`. 2b inputs at `:k`: the
   FindingRevision `created_at <= k`, power readings with `ingestion_disposition.decided_at <= k`, the price
   timeline `snapshot_on(recorded_at=k)`. 2c states: no revision at `:k`/foreign -> `UNKNOWN`
   `FINDING_REVISION_NOT_AT_CUTOFF`; no consequence by `:k` -> `PENDING` `NO_CONSEQUENCE_AT_CUTOFF`; head without
   assessment links -> `UNKNOWN CONSEQUENCE_LINEAGE_MISSING`; PRICED head whose price revision is not recorded by
   `:k` -> `UNKNOWN PRICE_NOT_AT_CUTOFF`; not the Finding's latest revision at `:k` -> `HISTORICAL`; else W1
   basis comparison -> `CURRENT`/`STALE` with W1 reasons. Amount null for UNKNOWN/PENDING, stored amount
   otherwise (presentation and Cost eligibility stay the estate's). 2d W1's `source_open`/`AUDIT_ONLY` input is
   not part of the signature; the caller's day/source gates replace it. 2e the state is basis currentness at
   `:k`; the live-vs-historical label is the caller's (`read_at`). Tests: `test_consequence_on_excludes_later_
   revision_and_price`, `test_consequence_on_exact_finding_pin_and_stale_basis` (also HISTORICAL after
   supersession). They use `EarlySite` (PowerSite with the fixture clock one day behind the DB clock, since
   prices/consequences are DB-clocked and Findings fixture-clocked). Regressions: 7 consequence/assumption
   files 80 passed. Mutations (reverted): drop consequence `recorded_at` cutoff; price snapshot at `None` -> both
   tests FAIL.
3. **`da15d71f` `0b`.** `MoneyEligibility.for_finding_on(c,t,s,finding_id,known_at)` (new keyword `days`,
   default `windows.store`); `PostgresFindingStore.money_revision_on` (claim + generator); the q5 day dict's
   `selection` gains `model_version` and `cohort` (additive); `ProvenanceReadsOn(c)` in
   `postgres_evidence_ledger.py` (the ledger's `finding_revision_evidence`/`consequence_inputs` delegate to it).
   Source gate on `c`: `source_gate(estate_projection(PublicProvenance(ProvenanceReadsOn(c)).consequence_revision(
   t,s,cid)))`. Readings: 3a the judged revision is the Finding's latest at `:k` (`index_snapshot_on` head, W1
   rule). 3b a day is matched when the pass completed by `:k` reached that day's selected seq and did not defer
   its window. 3c an unavailable day adds `HISTORICAL_DAY_UNAVAILABLE: ...` and forces `PENDING_REASSESSMENT`;
   no revision/foreign Site -> `NO_FINDING_REVISION_AT_CUTOFF`; refused pin -> `FINDING_PIN_REFUSED`; DB errors
   propagate (the shared transaction is aborted anyway). 3d the result adds `known_at`. Tests:
   `test_money_eligibility_on_uses_cutoff_days_and_refuses_unknown` (LR-01 Walk; live == W1 ELIGIBLE, k2 PENDING
   with LIVE_JOB, k1 == W1 as read at k1), `test_money_source_gate_exact_citations` (block == W1 resolver block,
   evidence = Finding cited ∪ power IDs, AUTHORED permits), plus control `test_money_source_gate_mixed_union_
   withholds` (separate test: two PowerSites cannot share one test's store). Regressions: 9 files 74 passed.
   Mutations (reverted): days read at the live cutoff; power IDs dropped -> tests FAIL.
4. **`4442d33c` cold/EV pinned mode (q6 Blocker 1, shape per W4-01 Run 3 ruling 6).**
   `ColdReadService._snapshot` / `EvReadService._snapshot(c,t,s,code,lo,hi,known_at,*,selection_cutoff=None,
   selection_seqs=None)`; default path SQL untouched; pinned mode: exact window, `sel.seq` pin,
   `selected_at/completed_at/created_at <= selection_cutoff`, same-tenant/Site run join, snapshot adds
   `selection_seqs` and `selection_cutoff`; inconsistent pin raises `SelectionPinRefused` (LookupError, the
   caller's 409). Module `selected_windows_on(c,t,s,analytics,from_,to,cutoff)` (intersection predicate, greatest
   qualifying seq per exact key, sorted `(ws,we,analytic,seq)`); wrappers `estate_snapshots_on(c,t,s,code,from_,to,
   known_at,selection_cutoff)` on both services (cold groups both analytics per exact window). Readings: 4a pinned
   SQL uses window equality (exact stored key), not the covering predicate. 4b **open question Q7-1**
   (`.agent/W3-01-pending-rulings.md`): the selection filters on the clamped watermark select nothing on the
   fixtures (selections are written after the last decided evidence), so the API keeps `known_at` (clamped) and
   `selection_cutoff` (requested) separate; tests use that split. 4c the four q6-named estate tests
   (`test_w301_estate_index_postgres.py`, tokens/409/page invariants) need the estate core; this commit has
   adapter-level tests instead: `test_w301_cold_selection_on_postgres.py` (day intersection vs the empty whole-day
   Site read; reselection invisible at the earlier cutoff; pin refusal) and `test_w301_ev_selection_on_postgres.py`
   (same, plus two windows in one day, EV unclamped `known_at` still 422, clamped + later selection cutoff no 422).
   Finding-row estate rules (episode intersection, `finding_revision.created_at <= k`, EV withdrawal) stay in
   Lane B's projection.
   Follow-up test commits on the same unit (review with `4442d33c`): `8d73c035` (EV: a selection written after k0
   over committed evidence is absent/refused at k0) and `9956b6b8` (cold: a test-appended reselection of an old,
   completed run is invisible and refused at the earlier cutoff; the one shape no writer produces today).
   Checks: the 2 new files + `test_w203_cold_reads`, `test_w206_ev_reads`, `test_w207_ev_site_reads`,
   `test_w301_provenance_dto`, `test_w301_w1_snapshot_helpers`: 63 passed (38 min); new cold reselection test
   passed after. Mutations (reverted): drop `selected_at` from `selected_windows_on`, drop it from the pinned SQL
   -> `test_cold_reselection_of_an_old_run_is_invisible_earlier` FAILS for each (the earlier late-reading/EV
   tests alone did not catch them, because `knowledge_cutoff`/`completed_at` also excluded those rows).

check-all (once, at the end): 10/10 PASS. DB `w301m_test` dropped. No full suite run (per dispatch).
**Branch released.** Ready for separate review, in order: `2a1b59cf`, `c55dadd4`, `da15d71f`,
`4442d33c` (+`8d73c035`, `9956b6b8`). Open: Q7-1 (selection cutoff vs clamped watermark) for Lane B's core.

Prerequisite Lows fix: select_consequence_on returns HISTORICAL for a superseded FindingRevision with no consequence (W1 precedence); cold/EV `_snapshot` raise ValueError for selection_seqs without selection_cutoff and for unknown cold analytic keys, and SelectionPinRefused when pinned with no evidence basis; Run 7 q7-1 applied to `selected_windows_on` (new `evidence_cutoff` keyword bounds only run knowledge_cutoff; estate_snapshots_on passes known_at as it and returns [] when None). Private DB w301o_test: 17 passed (4 files); check-all 10/10.

## Lane B commit-2 core (2026-10-20): landed, partial on mini-grid DB tests; branch released to Lane A
Merged main (up to date at `381cf1a2`). Commits `0b56f150`, `58b00bb6`, the HISTORICAL assert, `c951dd8b`.
- `estate/scope.py` strict parser/refusals/access basis/`estate-selection/2` token/cursor; `estate/coverage.py`
  `site_coverage(snapshot,t,s,domain,from_,to,known_at)` (mini-grid days+matcher+money gates, pinned cold/EV windows
  with the q7 split, Action reduce); `estate/index.py` full-set rows/summaries/token before paging;
  `estate/adapters/postgres_estate_read.py` one READ ONLY REPEATABLE READ snapshot over the Lane A `*_on` helpers;
  `estate/composition.py` (`build_estate_index_service`, `registry_tenant`); `estate_api.py` (`build_estate_router`).
- Tests (private `w301p_test` + harness clones, all dropped): `test_w301_estate_api.py` 5 passed (refusals, empty
  zeros, token v2 + W20 D3 digest literal, pure mini-grid gates, Action reduce); `test_w301_estate_index_postgres.py`
  5 passed (cold: q7 reselection proof, day intersection, outside-day UNKNOWN, scope/foreign/missing Site, cursor
  fence); `test_w301_estate_index_ev_postgres.py` 3 passed (EV day intersection, multiwindow dedupe/fence, q7).
- Mutations after commit (reverted with `git checkout`): drop the token from the cursor fence -> cursor test FAILS;
  serve mini-grid rows from an unsettled Site -> pure gate test FAILS; cold historical state -> CURRENT -> q7 test FAILS.
- check-all: 9/10; the one failure is the expected missing `estate` guard domain (Lane A, `.agent/W3-01-lane-a-requests.md`).
- Readings q8 1-11 in `.agent/W3-01-pending-rulings.md` (non-blocking). Test notes: cold and EV replays each build
  their own DB, so the "same estate" cold+EV tests are split by file; tests re-date `site_import.imported_at`
  (replays import at today's DB time, after their 2026-10-06 data); EV `decided_at` is fixture-clocked, so its q7
  test compares rows/IDs/coverage without the watermark, while cold proves whole-token equality.
**Not built (resume here, Lane B):** mini-grid Postgres tests `test_late_support_change_recurrence_at_exact_cutoff`,
`test_cost_risk_opportunity_eligibility_without_mock_seed`, `test_action_event_and_verification_counts_full_basis`,
`test_cost_lens_only_exact_eligible_current_rows` (S4 `CaseRunner`/S6 harness/`PowerSite` chains; mind their
fixture clock vs DB `now()` and re-date `site_import`). The golden manifest `w301-estate-golden.json` is not built.
**Carry to the commit-2 packet (prerequisite r1 L2, accepted):** a PENDING job's window can be widened in place
after `k`, with no stored window history, so it can show as outstanding on a historical mini-grid day it did not
cover at `k`; that day reads pending, not unavailable.
**Branch released.** Next: Lane A guard domain + `main.py` mount; the remaining mini-grid tests; then review.

## Lane B commit-2 mini-grid tests (2026-10-20): landed; golden manifest blocked on q9; branch released
Merged main (`e7ab7dbe`, clean). Commit `187a7020`:
- `test_w301_estate_index_postgres.py` adds `test_late_support_change_recurrence_at_exact_cutoff` (S4 F03/F05: distinct
  recurrence rows; explicit cutoff unchanged after later revisions; 1 us before the late match -> UNKNOWN, no rows;
  late accepted evidence -> live PENDING_RECOMPUTE), `test_cost_risk_opportunity_eligibility_without_mock_seed`
  (unbound PowerSite: UNPRICED and gate-withheld PRICED stay in All, Cost/Risks/Opportunities complete zero),
  `test_cost_lens_only_exact_eligible_current_rows` (P01 PowerSite: exact PRICED interval in Cost; historical cutoff
  and stale v4 price leave Cost until recompute), `test_action_event_and_verification_counts_full_basis` (S6 chain:
  event cutoffs, later-window edges, VERIFIED and 30-day lookback edges, full-basis cards vs page).
  TEST-SCOPED `pin_read_at` pins `EstateSnapshot.read_at` and `PostgresAssessmentStore._transaction_time` to the
  fixture clock (S4/S6 fixtures run 2026-10-29..11-02, ahead of the DB clock).
- Code fix (`estate/coverage.py:_mini_grid`): an overlapping PENDING/LEASED/FAILED job now makes the day
  PENDING_RECOMPUTE ahead of S3 STALE (spec selection rule + q5 ruling 5); before, late evidence read STALE_SOURCE.
- Checks (private `w301q_test`, dropped): estate files 17 passed (3 min 5 s): index 9, EV 3, API 5. Mutations after
  commit, each reverted with `git checkout`: drop the job-pending rule -> late-support test FAILS; drop the CURRENT
  money check -> Cost test FAILS; `later_end` inclusive -> Action counts test FAILS.
- check-all: 9/10; the only failure is the expected missing `estate` domain in `configuration-persistence.ps1` (Lane A).
**Not built:** `backend/tests/fixtures/w3/w301-estate-golden.json` (q9 item 1: fresh UUIDs per replay, separate DBs per
domain). q9 item 2 (awaiting-verification predicate) is built as-is; its test pins 0 and is marked q9.
**Branch released.** Next: Architect rules q8 + q9; then a Lane B fix round (rulings + golden); Lane A guard domain and
`main.py` mount.

## Lane B commit-2 q8/q9 round (2026-10-20): Lane B part complete; ready for Lane A integration
Merged main (`6f87e923`; handoff conflict took main's version, the mini-grid section above restored). Commits:
- `9b2c09cd` q8: ruling 2 `estate/index.py:_scope` uses the cursor's six-digit cutoff for every page two (supplied
  `known_at` must equal it or be its wire-second copy, else 409; page two below read time is HISTORICAL with
  `as_of`); ruling 3 Finding wire `estate-finding-index-2`, every consequence carries `amount_low`/`amount_high`
  (null unless PRICED; `amount` aliases `amount_low`), `estate/coverage.py:_consequence`; fixture (a)
  `imported_before(engine, tenant_id, site_id, at)` constrained by tenant+Site, rowcount 1; fixture (b) EV q7 proof
  now asserts identical full coverage/rows/summary/token at K with the late dispositions re-dated after K
  (TEST-SCOPED `SET LOCAL session_replication_role = replica` over the append-only trigger, private DB only), and
  `test_ev_backdated_disposition_limitation_fences` keeps the backdated case as a named limitation; q9 ruling 2
  honest zero: card 0 at `later_start` with the Action window card 1, selected F01 revision != origin, origin
  revision 0 before a plan, `later_end` exclusive and RESOLVED controls.
- `4a311ae5` q9 ruling 1: `backend/tests/fixtures/w3/w301-estate-golden.json` (`w301-estate-golden/2`) and
  `test_w301_estate_golden_postgres.py::test_w301_golden_manifest_public_replay` (mini_grid 14, cold 8, ev 8 cases;
  independent token/access rebuild; cursor decode + page two). `mixed` ships `cases: []` pending **q10** (one private
  DB not reachable with the existing replay fixtures); no stale/leased/failed replay exists (q10 item 3).
- Checks (private `w301r2_test`, dropped): estate API 5 passed; index + EV 13 passed (EV 4 incl. new limitation
  test); golden 3 passed (70 s). Mutations, reverted with `git checkout`: omitted-cutoff cursor reads live -> cursor
  test FAILS; golden `total_count` 2->3 and an emptied token-rebuild array -> golden test FAILS.
- check-all: 9/10; the only failure is the expected missing `estate` domain (`configuration-persistence.ps1`).
**For Lane A (integration handoff):** add the `estate` guard domain and the `main.py` mount; update the typed UI
Finding DTO to `estate-finding-index-2` (`amount_low`, `amount_high`, `episode_start`, `status`); UI copy for the
honest zero (q9 ruling 2): label `Awaiting verification`, zero-state `No Actions from selected Finding revisions are
awaiting verification in this window.`, disclosure `Counts Actions from the exact selected Finding revision with an
open frozen verification window and no resolved outcome.`; unpriced copy `No consequence recorded` (q8 ruling 4).
**Open:** q10 (mixed branch; readings 2-4). Residual risk: a live page one with open cold/EV jobs pages to a
HISTORICAL page two that does not project today's jobs, so its `job_state` (in the token) moves and page two is 409
(ruling 2 + ruling 6 as written). Optional: `.gitattributes` `backend/tests/fixtures/w3/*.json text eol=lf`.
**Branch released.**

## Lane A commit-2 integration (2026-10-20): commit 2 complete, ready for review; branch released
Merged main (already up to date at `da3f6f3c`). Commit `d9039997`:
- `tools/checks/configuration-persistence.ps1`: `estate` `$domains` entry (q5 ruling 3; `$pgReaders`/`$isPgReader` kept as landed).
- `tools/checks/test_estate_guard.py`: `test_pg_reader_import_allowed`, `test_pg_reader_write_rejected`,
  `test_domain_driver_import_rejected` (untracked probe modules, deleted after; no tracked `estate/` file touched).
- `backend/assetops_backend/main.py`: `build_estate_router(build_estate_index_service(database_url()), registry_tenant(registry),
  access=development_access, unavailable=(SiteStoreUnavailable,))` after the Site Action index router.
- Not built: typed UI DTO and q8/q9 copy. No Lane A-owned estate frontend file exists; the spec places it in commit 3
  (q11 item 1). Readings q11 1-4 are in `.agent/W3-01-pending-rulings.md`; none blocks.
Checks: private `w301s_test` (dropped): estate API, index, index EV and golden, plus the 3 guard tests: 24 passed (556 s).
Ad hoc `create_app()` without a DB: `/api/estate/scope` returned 503 `ESTATE_STORE_UNAVAILABLE`. Mutations after commit,
each reverted with `git checkout`: with the `estate` domain disabled, `test_domain_driver_import_rejected` FAILS; with the
`$isPgReader` branch dropped, `test_pg_reader_import_allowed` FAILS. check-all: 10/10 PASS. No full suite.
**Next:** independent review of the contiguous commit-2 range (`a75b0291` prerequisite onward through `d9039997`); then commit 3.
**Branch released.**

## Lane B q10 round (2026-10-20): commit 2 ready for review; branch released
Merged `main` at `a37eeb56` (`.agent/W3-01-pending-rulings.md` conflict: main's version). Commit `5d8c5794`
applies "Run 10 rulings (q10)":
1. `test_w301_estate_golden_postgres.py`: `mixed` in `REPLAYED`/`BRANCH_REPLAY`; validator requires nonempty cases.
   `mixed_replay` calls `fresh_database()` once, suppresses the cold/EV `Chain.open()` resets, runs cold `normal`,
   EV `complete`, the S4 runner (own `PostgresFoundationStore`, no `store` fixture) with F03, adds
   `W301-EMPTY-001`, re-dates the four imports. Manifest `mixed.cases`: `scope-mixed`, `findings-mixed-week`,
   `actions-mixed`, `findings-mixed-kobo-day`; `assert_mixed` checks four codes, one tenant, counts, Action rule.
2. `test_w301_estate_coverage.py` (new): `test_windowed_stale_probe`, `test_windowed_leased_and_failed_jobs` (unit).
3. `EstateSnapshot.continuation` (set in `index._scope`); `coverage._windowed` evaluates `open_jobs` on a live
   read or a cursor page. `test_live_open_cold_ev_page_two_keeps_work_fence`; proven non-vacuous (fails 409
   without the fix, reverted).
4. `test_w301_estate_index_ev_postgres.py::reselect_at` monkeypatches `w205b.LATE_DECISION` to a DB-clock instant
   after `k1`; no trigger bypass, no row update.
Checks (private `w301t_test`, dropped): estate files + `tools/checks/test_estate_guard.py` 28 passed, 0 skipped
(744 s); `check-all` 10/10. Open: q11 reading (historical page one + cursor, pending-rulings). Risk: the mixed
read clock is `max(S4 fixture now + 1 min, DB now)`; after 2026-10-30 the cold watermark/KOBO literals may move.

**Branch released.** Next: independent review of commit 2, `a75b0291..HEAD`.
