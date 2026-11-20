> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 6 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## S4-01 phase 1 - Finding store, episode matcher, `s4-finding-cases-v1` (active, review pending)

Built on `task/S4-01-finding-identity` (`bcbc3f4`, `6b891ef`, closeout; fix round 1 `7781821`..`71dd0b6`). Packet `archive/agent-history/S4-01-phase-1-review-packet.md` (Fix round 1 section); questions Q1-Q9 in `archive/agent-history/S4-01-questions-1.md`, Q10-Q15 in `archive/agent-history/S4-01-questions-2.md`.

### What it settled in code

- Migration 0009: `finding` (immutable key/anchor/cohort/matcher version, `recurs_after_finding_id`, `split_from_finding_id`), `finding_revision` (UNIQUE `(finding_id, revision_no)` and `(finding_id, basis_sha256, transition)`, primary `assessment_revision_id`), `finding_revision_assessment`, `finding_revision_evidence` (cited only), `finding_merge`; all append-only. Alembic head is 0009.
- `analytics/finding_episode.py` (pure, `finding-episode-1`): CURRENT windows of the current model only; <=20-min bridges only through observed Necessary or modelling-reason Indeterminate; recurrence link only across an observed OFF; window revision cited but not in the basis hash.
- `analytics/finding_service.FindingMatcher` reads via `DispatchReadService.window` under a fence; `adapters/postgres_finding_store.py` is the fifth guarded writer (INSERT-only, advisory lock, `FindingFenceMoved`, `rows()` reload).
- Composition `build_finding_matcher` / `build_finding_store`; CLI `assess_dispatch match-findings|finding-rows`.
- `tools/checks/configuration-persistence.ps1`: only the Finding store writes Finding tables, insert-only.
- `backend/conversions/s4-finding-cases-v1.json` + `tools/s4_finding_cases.py run|verify` (DB `assetops_s4cases`, TLS 8763; labelled authenticated Batch V2; per-run IDs in `%LOCALAPPDATA%/AssetOps/s4-finding-cases/s4-finding-cases-run.json`). Run on `6b891ef`: all checks OK, VERIFY PASSED (`.agent/S4-01-finding-cases-run.txt`).
- `backend/tests/test_s4_finding_store_postgres.py`: all cases in one Site, stale window, F07 test-scoped upgrade, append-only, moved fence.
- Fix round 1: anchor-first split ownership (B1); fence counts the Site's `finding_revision` rows (B2); recurrence only with proven gap coverage and both OFFs observed (B3); bridges need full observed coverage incl. stop spans (Q2); basis includes window revision IDs and input digests (Q4); `support_sha256` + `BASIS_REFRESHED` for provenance-only changes (Q5); `REOPENED` after NO_LONGER_SUPPORTED (C3). Pure `tests/test_s4_finding_episode.py` (16).
- Producer `F01-gateway` (Q6): a Lab run sealed by the durable registered gateway (epoch `s4-gateway-epoch-1`) over TLS on 2026-10-02 opens a SUPPORTED Finding. Run on `71dd0b6`: 11 Findings / 30 revisions, VERIFY PASSED.

### Open

- No Finding read API/UI yet (phases 2-3). F07 is test-scoped: no reviewed later `dispatch-3.x`.
- Backdated controls append collateral BASIS_REFRESHED to Findings on earlier days; every same-day reassessment appends BASIS_REFRESHED to that day's Findings - phase 2/3 History must group them (Q14).
- Lab refuses a 0-minute minimum runtime, so the gateway case runs on 10-02, outside the fixture controls (Q15).
- 3+-way merge untested by fixture (pure test only); matcher is linear in assessed days.

## S4-01 phase 2 - Exact Finding root/revision read (active, review pending)

Packet `archive/agent-history/S4-01-phase-2-review-packet.md`; questions `archive/agent-history/S4-01-questions-3.md` (Q16-Q20).

- Read service `backend/assetops_backend/analytics/finding_read.py` (`FindingReadService.finding`,
  `.window_state`, `revision_groups`); routes `backend/assetops_backend/finding_api.py`:
  `GET /api/sites/{site_code}/findings/{finding_id}?revision_id=&after_revision_no=&limit=` and
  `GET /api/sites/{site_code}/finding-windows/{day}`; wired in `main.py` via
  `composition.build_finding_read_service` (manifest env `ASSETOPS_FINDING_CASES_MANIFEST`, else
  `ASSETOPS_DEMO_FIXTURE_MANIFEST`).
- Status matrix: `access` seam gives 401/403 before lookup (default admits the development tenant's operator
  context and says so in `access_basis`, Q16); unknown/foreign Site, root or revision 404; malformed ID 422;
  no DB or store failure typed 503 `FINDING_STORE_UNAVAILABLE`.
- Selection: omitted revision = latest recorded; exact ID pins; `selection.replay` states no `knowledge_at`
  replay. Every revision returned in `revision_no` order (paged) with prior/new window and interval IDs,
  Foundation/binding revisions of the cited runs, basis/support digests, `support_changed`; groups are a hint.
- Currentness compares the revision's own cited WINDOW assessments with the S3 read's current selection
  (`CURRENT`, `FINDING_MATCH_PENDING`, `STALE`, `PENDING`, `FAILED`, `NOT_ASSESSED`; merged =
  `MERGED_INTO_CANONICAL`). `window_state` returns `NO_FINDING` only for a CURRENT window without Candidate or
  Finding.
- Matcher (`finding_episode.py`) now records `claim.continuity` (bridged gaps: segments+reasons, observed stops
  with both OFF times, `candidate_minutes_added "0"`) and `claim.recurrence` (LINKED with both OFF bounds and
  covered windows, or NOT_ESTABLISHED + reason; split parts NOT_APPLICABLE). Not in the basis digest. The read
  resolves OFF evidence IDs from the cited interval revision's evidence at the recorded time
  (`PostgresFindingStore.revision_lineage`).
- Store reads added: `finding_detail`, `revision_lineage`, `findings_over` (SELECT only; the existing
  persistence guard still limits Finding writes to the store - proven by a write in `finding_read.py`).
- `DemoManifestAnnotations` also labels an opt-in `gateway_sealed` case (`DEMO_MANIFEST_GATEWAY_CASE`).
- Producer: R2 asserts F01-gateway cites only gateway-sealed batch evidence (102 IDs, 0 outside); writes
  `s4-finding-cases-manifest.json`; `verify` reads every Finding through `assess_dispatch finding-reads`.
- Open: Q17 (contradictory report between stop OFFs is invisible to the matcher); Q18 window-state route vs
  S4-04; no UI (phase 3); R1 gateway-day labelling for the owner walkthrough.

### S4-01 phase 2 fix round 1 (review B1/B2/C3; Q17-Q20)

Commit `254b843`; packet "Fix round 1" section; questions `archive/agent-history/S4-01-questions-4.md` (Q21-Q24).
- Matcher `finding-episode-2`: `FindingMatcher.bases` reads each CURRENT window's selected run input evidence
  once per run (`DispatchReadService.run`) into typed `StateReport`s; `_stop_proof` confirms a stop only when both
  OFF endpoints are in the run evidence and every report between last ON and next first ON is accepted, GOOD,
  in-cohort and OFF, in CURRENT non-Indeterminate windows with no generator cohort limit; otherwise the stop does
  not bridge (two Findings) and recurrence is `NOT_ESTABLISHED: SEPARATION_STOP_NOT_CONFIRMED: <reason>` (Q21).
  Continuity stops carry `proof` (evidence IDs, run/window IDs, `reports_sha256`).
- Q20: relation facts in `support_sha256`, full continuity/recurrence records in `basis_sha256`; the opening
  recurrence record is carried on `Episode.recurrence` into every later revision. Old v1 rows would get an
  appended revision (basis includes the matcher version); 0009 reached only disposable DBs.
- Q18: `finding_match_pass` (append-only, added to unmerged 0009; persistence guard table list extended) records
  each committed pass's fenced `selection_seq`; `window_state` says `NO_FINDING` only when a v2 pass covers the
  window's current selection, else `FINDING_MATCH_PENDING`. B1: Indeterminate window = `NOT_DETERMINABLE`; body
  has `window_claim_level`, `window_limitations`, `selected_run_id`, watermarks, `finding_match`.
- B2: a pinned non-latest revision's currentness is `SUPERSEDED_BY_LATER_REVISION` + `latest_revision_id`;
  `state.claim_is_current_refers_to = LATEST_REVISION`.
- Q19: `build_finding_router(gate=...)` reuses `main.performance_gate`; an unconfigured gate is closed. Closed:
  default detail and window reads 409 `PERFORMANCE_CUTOVER_CLOSED`; pinned `revision_id` 200 with
  `audit_only`, `SOURCE_CLOSED` projection, no S3 read and S3 links withheld (`links.performance`). The
  `finding-reads` operator CLI is ungated (Q23).
- Open: Q21-Q24; phase 3 UI.


## S4-01 phase 3 - Site Finding detail UI and closeout (in_review)

Task `tasks/S4-01-finding-identity.md`; packet `archive/agent-history/S4-01-review-packet.md` (all phases); questions
`archive/agent-history/S4-01-questions-5.md` (Q25-Q30); owner steps `archive/agent-history/S4-01-owner-walkthrough.md`.

### What it settled in code

- Route `SITE_FINDING_ROUTE_PATH` = `/sites/:siteId/findings/:findingId`, exact version `?revision_id=` (the API
  parameter), view `?view=analysis`, block `?portion=` (`frontend/src/shell/operatorSiteRoutes.ts`,
  `siteFindingHref`). Frame `SiteFindingFrame` (`frontend/src/shell/SiteAnalyticsFrames.tsx`): trail Sites > site >
  Findings > Finding, Findings tab current, h1 from the lifecycle. The T028 file-backed `/findings/:siteId/:assessmentId`
  stays as it was.
- `frontend/src/sites/findingClient.ts`: the 401/403/404/409 `PERFORMANCE_CUTOVER_CLOSED`/503 responses map to
  named states, plus `getFindingWindow` for `finding-windows/{day}`. `findingWords.ts` holds the plain words for
  lifecycle, transition, currentness and window states.
- `frontend/src/sites/SiteFinding.tsx` leads with the most limiting state, in this order: closed source (audit
  record only, C7), merged, earlier version, lifecycle, then currentness. It then shows the panels:
  - What happened: separate minutes cards, money "Not yet available", and a keyboard-selectable block bar.
  - What limits this conclusion: limitations, joined gaps and stop bridges with the sparse-reporting caveat, and
    recurrence that never implies the earlier Finding is open.
  - What to do next: not yet available.
  - Where to look next: Dispatch days carrying the interval revision, records, related Findings.
  - Versions: BASIS_REFRESHED runs grouped with count and exact links.
  - Records summary: demo-manifest kind in plain words.
  The Analysis view holds the full IDs and codes behind `data-vocabulary-exempt`.
- Dispatch day (`PerformanceDispatch` `DayFindings`) reads `finding-windows/{day}`. It links non-merged Findings
  and names NO_FINDING / NOT_DETERMINABLE / FINDING_MATCH_PENDING / NOT_ASSESSED without a link.
- Tools: `tools/s4_finding_walkthrough.py` (DB `assetops_s4walk` copied from `assetops_s4cases`, API 8840, web
  5340, staged PENDING 2026-10-09; `links` prints this run's addresses) and `tools/s4-finding-evidence.mjs`
  (CDP 9343; 36 claims at 1440/390; run record `.agent/S4-01-phase-3-evidence-run.txt`).

### Open

- Q25 the S3 `unavailable.finding` text remains; Q27 no priority/confidence chip; Q28 the generic
  `layout-evidence.mjs` needs a Lab backend and was not run to completion; Q29 ledger row unchanged.
- Carries still open: C5 one-hop canonical, C6/C9 read and pass cost (S4-04), C8 recurrence record only on the
  opening revision.
- `?portion=` is an index into the selected version's blocks (Q30).

## S4-03 - Finding Evidence and History (in_review)

- Reads (phase 1): `GET /api/sites/{code}/findings/{id}/evidence?revision_id=&offset=&limit=` and
  `/history?revision_id=&after_revision_no=&limit=` (`finding_api.py:142-209`, `finding_read.py` `evidence()`/`history()`,
  `postgres_finding_store.py` `revision_evidence`/`revision_times`). Same scope/gate/refusals as the S4-01 root;
  unpinned read is 409 while the Performance cutover is closed; broken lineage is 200 `lineage.status=BROKEN` with
  named link codes and product-safe words (`BROKEN_WORDS`, parity-tested against frontend `LINK_WORDS`).
- Evidence membership is `finding_revision_evidence` (cited set), counted separately from the run input set;
  `provenance.cited_evidence_by_source` and `cited_evidence_by_role` are whole-set aggregates (phase 3, N1).
- History rows carry `cited_evidence.accepted_rows` (row existence only, never a lineage verdict) and five time kinds;
  no `knowledge_at` replay anywhere.
- UI: child views of the canonical Finding root, `FINDING_CHILD_VIEWS = ["evidence","history"]`
  (`operatorSiteRoutes.ts`), rendered by `SiteFindingFrame` (`SiteAnalyticsFrames.tsx`); `SiteFindingEvidence.tsx`
  (50-record pages, `offset`/`record` local to Evidence) and `SiteFindingHistory.tsx` (loads every page, 100 per
  request, checks loaded == total, selected/latest marked separately, late-acceptance note from stored times).
  `revision_id` is the only context carried between Finding, Evidence and History (Architect Q3).
- Legacy `/findings/{site}/{assessment}/evidence` lists overlapping same-day Findings as a day-level aid, never a
  redirect (Architect Q1).
- Retired: `UNAVAILABLE.evidence_tab/history_tab`, S4-01 history placeholder (baseline 16 -> 15).
- Tools: `tools/s4_finding_walkthrough.py --db/--work` (protected names refused; `prepare` refuses a foreign
  non-empty folder; `drop` removes only a marked folder), `tools/s4-finding-evidence.mjs` suites
  all/finding/evidence/history/closed/broken (110/110 + closed 8/8 at 1440/390 on phase 3).
- Open: Architect Q4-Q6 (`archive/agent-history/S4-03-questions-2.md`, incl. M4 shape); registry "knowledge cutoff" rewording and
  node/portion/ledger promotion proposed in the packet, not applied; legacy tab not browser-captured (no readable
  assessment on KOBO-001); Coverage/Use stay catalogued gaps; ActionEvent/recommendation/Alternatives for G-04;
  `ASSESSMENT_CITATION` assumption (phase-1 C1) carried.

## S4-02a - Site price publication and exact assumption history (in_review)

Branch `task/S4-02a-site-assumptions`; phase 1 `28668d9`..`5159b96`, phase 2 `408e9e6`..HEAD. Packet `archive/agent-history/S4-02a-review-packet.md`.

- Store: migration `0010_financial_assumptions` (head). `financial_assumption_revision` (immutable, append-only) and `financial_assumption_assignment` (valid x recorded, GiST exclusion, set-once `recorded_to` that must be later than the series' latest `recorded_from`, containment trigger). Sixth product DB writer `financials/adapters/postgres_assumption_store.py` (guard rule 8).
- Publication: SYSTEM only, `python -m assetops_backend.publish_assumption publish|fixture` (no actor flag). Retry digest = canonical publication step; fixture file bytes/version and authorization prose are stored in provenance but not digested (`PROVENANCE_NOT_DIGESTED`). Fixture `backend/conversions/demo-diesel-price-publications.json`: v1 INITIAL 1.25 from 2026-01-01, v2 SUCCESSION 1.32 from 2030-01-01, v3 CORRECTION 1.19 over June 2026. (S4-02b phase 1 added v4 CORRECTION 1.28 over October 2026; `publish_assumption fixture` without `--step` now also publishes v4, the S4-02a walkthrough pins v1-v3 - review L7.)
- Reads: `financial_read_api.py` `GET /api/sites/{site}/financial-assumptions?key=&valid_at=&recorded_at=&after_revision_no=&limit=` (PRICED/NO_PRICE/CONFLICT selection, timeline at cutoff, paged revisions) and `/{revision_id}` (exact, Site-scoped, 404 never latest); Finding read scope semantics, 503 `ASSUMPTION_STORE_UNAVAILABLE`. Write route `financial_api.py` keeps `no_verified_principal` (no success path).
- Finding bridge: `GET /api/sites/{site}/findings/{id}/financials?revision_id=` in `finding_api.py`; `consequence_state` returns `QUANTITY_UNAVAILABLE` (always, until `fuel-cost-1`) or `UNPRICED`; a priced amount raises.
- UI: Financials tab live; `/sites/{site}/financials` (bridge with `finding_id`+`revision_id`, pinned into the URL on first load; price in use) and `/financials/assumptions?revision_id=&recorded_at=` (`sites/SiteFinancials.tsx`, `sites/financialsClient.ts`, frame `SiteFinancialsFrame` in `shell/SiteAnalyticsFrames.tsx`). Finding frame links "What this finding means in money"; Foundation's open `G-foundation-financial-assumptions` line has a sibling link to Assumptions.
- Gap: `G-assumptions-human-edit` (`build`, placement `assumptions.price.human-edit`) in `ui/gapCatalogue.ts` and registry `mock_gaps`.
- Omitted for G-05: Scenarios subtab, Impact preview, maintenance line/accrual, metric cards, Trade-offs, cash flow, FX, extrapolation.
- Walkthrough/evidence: `tools/s402a_assumptions_walkthrough.py` (private `assetops_s402a*` DBs), `tools/s402a-assumptions-evidence.mjs` (69/69 at 1440/390).
- Open: L2 (SUCCESSION exactly at an open assignment's start is refused) for an Architect batch; C3 (S4-02b needs a Finding-window correction step); registry closeout for `I-S4-02a` and the Foundation gap is the coordinator's; `tools/layout-evidence.mjs` has pre-existing fixture-precondition failures on the Finding-case store.

## S4-02b phase 1 - `fuel-cost-1` and the consequence store (active, review pending)

Branch `task/S4-02b-fuel-consequence`, `7cbdef7`..HEAD. Handoff `archive/agent-history/S4-02b-phase-1-handoff.md`; questions `archive/agent-history/S4-02b-questions-1.md` (Q1-Q10).

- Pure `financials/fuel_cost.py`: immutable conditional `PARAMETER_VERSION` (1.10, digest pinned in fixture), `quantify` (Architect C4 fail-closed containment over stored observed `CANDIDATE_AVOIDABLE` segments, cited-run input membership, as-accepted SFC/binding valid over each interval; exact Fraction, upper stored at 50 digits ceiling plus exact fraction), `select_window_price` (whole-window only, typed UNPRICED reasons), `consequence` (exact amount, basis digest incl. considered price assignments). Fixture `conversions/fuel-cost-1-cases-v1.json` (P1-P4, U1-U17).
- Migration `0011_financial_consequences` (head): append-only `financial_consequence_revision` (number/amount CHECKs, window = FindingRevision episode, chain +1 trigger, unique revision_no and basis), assessment/assumption/power-interval links, trigger-only `financial_consequence_work` (on assumption publication and FindingRevision insert) and append-only `financial_consequence_work_attempt`.
- Seventh product DB writer `financials/adapters/postgres_consequence_store.py` (`load_input`, idempotent `append`, `pending_work`, `record_attempt`, `rows`); guard rule 8 confines it and forbids any module writing work rows.
- Carry C3: price fixture v4 CORRECTION 1.28 USD over October 2026; S4-02a tests and walkthrough pinned to v1-v3.
- Open: no read/recompute worker (2a) or UI (2b); ordinary Findings (review M2 correction): 8 `POWER_MISSING`, 2 `FINDING_NOT_SUPPORTED`, 1 F01-gateway `POWER_COVERAGE_GAP` (5-minute means every 15 minutes, one third coverage), so none qualify - only the power-mean Postgres case is positive (2.75 L; 3.4375 / 3.52 USD at v1 / v4); `finding_api.consequence_state` still the S4-02a placeholder; display rounding and STALE/PENDING are 2a.

## S4-02b phase 2a - read and recompute (built, review pending)

Branch `task/S4-02b-fuel-consequence`, `5d400d6`..HEAD. Handoff `archive/agent-history/S4-02b-phase-2a-handoff.md`; questions `archive/agent-history/S4-02b-questions-2.md` (Q1-Q9).

- Phase-1 carries: consequence basis uses window-clipped `(revision_id, from, to)` price boundaries (`PriceSelection.considered`, column `price_considered`), never assignment IDs (M1); work CHECK `<=` (L1); reviewer field final, digest `18595762…` (L2); `INTERVAL_NOT_WHOLE_SECONDS` (L3); 0011 enqueues pre-existing FindingRevisions (L4); L5 tests; L6 price value/currency trigger and deferred `financial_consequence_links_complete`. 0011 edited in place (unmerged).
- Worker `financials/recompute.py` (`derive`, `ConsequenceRecomputeWorker`), CLI `python -m assetops_backend.recompute_consequences run|pending --site`; typed FAILED attempts stay pending and retry; replay keeps IDs across restart and append-then-crash.
- Read `financials/consequence_read.py`: `CURRENT/STALE/PENDING/HISTORICAL` by comparing the head basis with a fresh derivation; outward display rounding to ISO minor units (`MINOR_UNIT_UNKNOWN` otherwise). Route `GET /api/sites/{site}/findings/{id}/financial-consequences` in `finding_api.py` (exact/pinned/paged, lineage links, 404 never falls back, 503 `CONSEQUENCE_STORE_UNAVAILABLE`). `/financials` bridge now `bridge_consequence` (amount only for a CURRENT PRICED head); `consequence_state` removed.
- Owner demo (`owner/owner-S4-02b-money-demo-2026-10-14.md`): spec `conversions/s4-power-demo-cases-v1.json` (P01-power 2026-10-23, labelled AUTHORED DEMONSTRATION; 12.65 L, 15.8125 USD at v1, 16.192 at v4); producer `tools/s402b_power_cases.py` (S4 cases + P01-power into its own `assetops_s402b*` DB). `s4-finding-cases-v1` unchanged.
- Open: no UI (2b); S4-02a frontend mis-words the new bridge states until 2b (`SiteFinancials.tsx:481`); evidence acceptance enqueues no work (Q2); worker is a one-shot CLI (Q6).

## S4-02b phase 2b - Financials UI, walkthrough and evidence (in_review)

Branch `task/S4-02b-fuel-consequence`, `dbaba10`..HEAD. Packet `archive/agent-history/S4-02b-review-packet.md` (whole slice); handoff `archive/agent-history/S4-02b-phase-2b-handoff.md`; questions `archive/agent-history/S4-02b-questions-3.md` (Q10-Q15); owner steps `archive/agent-history/S4-02b-owner-walkthrough.md`.

- Review carries: read takes `source_open` (S3 gate); closed gate gives currentness `AUDIT_ONLY` (`SOURCE_CLOSED`), never presented as current, bridge state `AUDIT_ONLY` with no amount (M1). Tests: HISTORICAL over a superseded FindingRevision (M2, test-scoped model upgrade), 401/403 and failing-store 503 on `/financial-consequences` (L1), assessment-completeness trigger (L2), latest-revision filter and `skip_if_succeeded` (L3), pending-work scope (L4). Bridge STALE says "queued" only when pending work exists, and carries `recalculation_queued`, `currentness_reasons`.
- `backend/assetops_backend/demonstration_label.py`: labels the P01-power Finding from the spec's declared Site/day; bridge and consequence read carry `demonstration` (Q11).
- Frontend: `sites/FindingConsequence.tsx` (`FindingBridge`: headline range only for CURRENT PRICED with display, "From finding to money" table, "How this is worked out" lineage disclosure, pinned earlier version panel, "Fuel cost versions" history); `financialsClient.ts` types + `getFindingConsequences`; `SiteFinancials.tsx` Overview reads bridge + consequences (`consequence_revision_id` in the address), S4-02a `:481` wording replaced; Assumptions "Show later versions" appends (S4-02a L5). `settled.ts` knows "Loading the fuel cost versions".
- Tools: `tools/s402b_fuel_cost_walkthrough.py` (one code tree per DB so each keeps its own source gate; prepare/links/serve/publish-v4/recompute/close-gate/open-gate/drop; `assetops_s402b*` non-test names only); `tools/s402b-fuel-cost-evidence.mjs` (90 claims at 1440/390, mutates its own evidence DBs).
- Open: Site-level consequence list on Assumptions (Q12); authorship label at ingestion (Q11); Architect Q2 (evidence acceptance enqueues no work); G-05 itemization in the packet; owner checkpoint after fresh review.

## S4-02c phase 1 - transactional acceptance work (reviewed: ACCEPT with carries)

Branch `task/S4-02c-evidence-consequence-work`, `5af9f214`..HEAD. Handoff `archive/agent-history/S4-02c-phase-1-handoff.md`; no open questions file.

- Migration `0012_evidence_consequence_work` (head): `financial_consequence_work.accepted_evidence_id` with scoped FK `(tenant_id, site_id, accepted_evidence_id)` -> `accepted_evidence`; cause CHECK adds `EVIDENCE_ACCEPTED`; three-arm `financial_consequence_work_cause_shape` (evidence arm requires accepted, Finding and revision locators and a non-empty `[affected_from, affected_to)`); `UNIQUE (finding_revision_id)` replaced by partial unique index `..._finding_revision_once WHERE cause = 'FINDING_REVISION_APPENDED'`; new partial `..._evidence_once (accepted_evidence_id, finding_revision_id)`; index `..._work_finding (tenant_id, site_id, finding_id)`; attempt index `(work_id, attempt_no DESC)`; `financial_consequence_work_attempt.no_op_reason` (enum CHECK, only on SUCCEEDED with `[]` IDs).
- Triggers: `financial_consequence_dirty_on_evidence` (AFTER INSERT on `ingestion_disposition` WHEN ACCEPTED; stored role `generator_power`, non-empty interval; one row per same tenant/Site Finding's highest-`revision_no` revision with a non-empty episode strictly overlapping). 0011 `financial_consequence_dirty_on_finding_revision` replaced with `ON CONFLICT ... WHERE`. Both take `pg_advisory_xact_lock(hashtextextended('financial_consequence_enqueue:' || NEW.site_id::text, 0))` (evidence: after the role check).
- Downgrade refuses while any `EVIDENCE_ACCEPTED` row or `no_op_reason` exists; otherwise restores the 0011 body, two-arm CHECK and UNIQUE. No backfill of pre-0012 acceptances.
- `PostgresConsequenceStore.chain()` pending matches unsucceeded `EVIDENCE_ACCEPTED` by `finding_id` (selects `accepted_evidence_id`); read `pending_work` items carry `finding_revision_id`, `accepted_evidence_id`; STALE with no pending work adds typed `NO_WORK_RECORDED` (`consequence_read.NO_WORK_RECORDED`); bridge keeps `REASONS["STALE"]`, no new copy.
- `recompute.py`: explicit cause dispatch; `EVIDENCE_ACCEPTED`/unknown -> FAILED attempt `CAUSE_NOT_SUPPORTED` (stays pending), never the assumption-range path.
- Guard rule 8 comment and message name 0011/0012 triggers; logic unchanged.
- Tests: `backend/tests/test_s4_evidence_consequence_work_postgres.py` (12), `backend/tests/test_s4_consequence_cause_dispatch.py` (2).
- Open (phase 2): scoped drain of `EVIDENCE_ACCEPTED` (recheck, typed no-op, N1 predicate), runner/Site claim/retry schedule; phase 3 walkthrough. Until phase 2, the CLI `run` records `CAUSE_NOT_SUPPORTED` attempts for evidence work and exits 1.

## S4-02c phase 2 - scoped drain and run plan (reviewed: ACCEPT with carries)

Branch `task/S4-02c-evidence-consequence-work`, `0a79be14`..HEAD. Handoff `archive/agent-history/S4-02c-phase-2-handoff.md`; no questions file.

- `recompute.py`: `EVIDENCE_ACCEPTED` dispatched via `PostgresConsequenceStore.evidence_target` (tenant/Site-scoped snapshot of accepted reading, queued revision, same tenant/Site/Finding max `revision_no`). Unreadable locator -> FAILED `EVIDENCE_LOCATOR_NOT_IN_SITE`; no ACCEPTED disposition -> FAILED `EVIDENCE_NOT_ACCEPTED`; other-Site work dict -> `WORK_SCOPE_MISMATCH` (unrecorded). `evidence_no_op` gives `FINDING_REVISION_SUPERSEDED` / `EVIDENCE_ROLE_NOT_RELEVANT` / `EVIDENCE_ASSET_NOT_RELEVANT` / `EVIDENCE_OUTSIDE_CANDIDATE_TIME` (strict overlap with merged positive-width claim spans), never quality; otherwise the same revision is derived from its own inputs.
- No-ops: `record_attempt(..., no_op_reason=)` -> SUCCEEDED, `[]` IDs, typed reason.
- Runner: `ConsequenceRecomputeWorker.run(tenant, site, limit, now=None)` with injectable `clock`; `claim_site` session lock `financial_consequence_runner:<site>` on a dedicated connection, unlocked in `finally`; due = never attempted or `now >= retry_due_at(last finished_at, last attempt_no)` (1/2/4/8/16 then 16 min, no cap); ordered by eligible-since instant (no starvation); `RunReport.counts()`. `run_pending` unchanged (unscheduled helper). `pending_work` returns last-attempt fields.
- CLI `recompute_consequences run --tenant --site [--limit 100]`: tenant required, non-dev tenant exit 2, summary JSON line, skipped Site exit 0. Runbook in `backend/README-db.md`.
- Tests: `test_s4_evidence_drain_postgres.py` (10), `test_s4_evidence_drain.py` (12); phase 1 file gains L3 no-op downgrade refusal and the L1-scoped race probe.
- Open (phase 3): two-leg late-power walkthrough (N2 price, N5 precondition, C5 IDs). R1 (S3/S4 commands unscheduled) and I1 (concurrent overlapping chunks) remain named risks.

## S4-02c phase 3 - late-power walkthrough and slice wrap-up (built, review pending)

Branch `task/S4-02c-evidence-consequence-work`, `6d4a1995`..HEAD. Packet `archive/agent-history/S4-02c-review-packet.md`, handoff `archive/agent-history/S4-02c-phase-3-handoff.md`, evidence `archive/agent-history/S4-02c-walkthrough-evidence.md`; no questions file.

- Phase-2 carries: `tools/s402b_fuel_cost_walkthrough.py` `recompute` now runs `recompute_consequences run --tenant demo --site KOBO-001` in bounded runs until backlog 0 and counts only `work_id` lines (M1, proved on private DBs); `tools/s402b-fuel-cost-evidence.mjs` claims the recompute exit status; runbook (`backend/README-db.md`) names repeated `skipped` as the hung-runner alarm (no timeout) and the uncapped permanent-failure retry volume; tests assert backlog after a failed run and the per-Site runner key.
- Fixture `backend/conversions/s4-power-late-demo-cases-v1.json` (`P02-power-late`, 2026-10-24): P01-power's shape with the 20 kW mean `[07:00, 07:05)` withheld and delivered later; `power_rules.sequence_rule = SOURCE_ORDER` (the late mean keeps its source sequence, the first delivery leaves a gap). Existing S4/S4-02b specs unchanged.
- Tool `tools/s402c_late_power_walkthrough.py run|drop` (DB `assetops_s402c3walk*`, ports 8918/8919): price v1 first (N2); N5 asserted (stops otherwise); Leg A STALE/TECHNICAL_INPUT_CHANGED + STALE_QUEUED with the EVIDENCE_ACCEPTED work ID, runner drain -> same revision consequence 2 CURRENT POWER_NOT_IN_ASSESSMENT_INPUTS, not S5-eligible; Leg B process-jobs + match-findings -> r2 SUPPORT_CHANGED citing the late ID, its FRA work -> CURRENT PRICED 12.65 L / 15.8125 USD, S5-eligible; replay selects 0; no duplicate basis. Reads use `ConsequenceReadService.read` with `source_open=True`.
- Finding: appending a late mean after the epoch's last sequence makes S3 dispatch-3.1 report `SEQUENCE_ORDER_INVERTED` and shortens the revised Finding (run 1, recorded).
- Open: R1 (S3/S4 commands unscheduled), I1 (permanent-failure attempt growth), I2 (hung runner visible only as `skipped`), I3 clock skew, I4 concurrent overlapping chunks unmeasured; pre-0012 stale heads `NO_WORK_RECORDED` without backfill; late-delivery sequence numbering on real gateways unproved.

## S4-02d phase 1 - bounded orchestration and schedule storage (built, review pending)

Branch `task/S4-02d-analytic-finding-worker-schedule`, `7851b4da`..HEAD. Handoff `archive/agent-history/S4-02d-phase-1-handoff.md`; questions `archive/agent-history/S4-02d-questions-1.md` (conservative choices built).

- Migration `0013_schedule_state` (head): `schedule_tick_head`, `schedule_site_head`, `schedule_cursor`, `schedule_enrolment`; one row per environment/Site, FK to `site(tenant_id, id)`, no trigger.
- Eighth writer `scheduling/adapters/postgres_schedule_store.py` (D-2026-10-14-s402d-schedule-storage-and-install-gate): expiring DB-time claims for tick and Site, heartbeat only on a completed tick, back-off on failure, fair cursor, enrolment, `site_inventory` read. Port `scheduling/ports.py`; composition `scheduling/composition.py` (adapter-isolation domain `scheduling`).
- Guard rule 8: schedule writer allowlist with named UPDATE columns per table, one-line UPDATE rule, no DELETE/TRUNCATE/DDL/upsert, reverse ownership; probes `archive/agent-history/S4-02d-phase-1-probes.py guard` all caught.
- `scheduling/tick.py` `ScheduleTick.tick()`: discover child (`reconcile_all()` timed + inventory + live jobs + pending work) -> active predicate (imported, not DECOMMISSIONED/ARCHIVED, any `accepted_evidence` row or enrolment; PLANNED qualifies; Sites with live work kept as `EXCLUDED_WITH_WORK`) -> `max_sites` after the cursor -> per Site claim, `s3` -> `s4` (skipped unless matcher version/fence changed) -> `consequence` (DB `now`), each a killable child with `PGOPTIONS` statement/lock timeouts. CLI `python -m assetops_backend.scheduling.run tick|enrol|heads`. No timer installed.
- S3: `lease_job` Site-scoped option, `run_site`, reads `live_jobs`/`job`. S4: `MatchOutcome.fence`. Consequence: `pending_work_sites()`. `assess_dispatch requeue --job-id` re-enqueues a live FAILED job's window.
- Tests `backend/tests/test_s4_schedule_tick_postgres.py` (7).
- Open (phase 2): health report and alarms, S5 seam, timer/runbook behind F1, I3 skew proof; I4 race proof at review. S3 cutoff and matcher `now` still app clock; one-off CLIs bypass the schedule Site claim.

## S4-02d phase 2 - health, install gate and S5 currentness seam (built, review pending)

Branch `task/S4-02d-analytic-finding-worker-schedule`, `8cf2d147`..HEAD. Handoff `archive/agent-history/S4-02d-phase-2-handoff.md`; probes `archive/agent-history/S4-02d-phase-2-probes.py`.

- Phase-1 review fixes: F1 rule-8 schedule-writer rules case-insensitive with strict one-line SET-list parse (phase-1 guard probes 20/20 incl. seven bypass lines); F2 Site back-off test; F3 `CLAIM_LOST` stops a Site on a lost claim; `requeue` usage error.
- `scheduling/health.py` read-only report (`run health`): environment and per-Site `STOPPED|FAILED|RETRY_DUE|BACKLOG|RUNNING|IDLE`, typed alarms (heartbeat/claim/skip/failure/fence-moved streaks, `S3_JOB_FAILED` with requeue, consequence attempt growth, `STALE_NO_WORK` IDs, S4 backlog outside the active set), all in DB time.
- `scheduling/upstream.py` S5 seam (`UpstreamCurrentnessRead` port, `run upstream`): per-day S3 read status/limits/basis/watermark (selection seq), bracketed live jobs, `match_state`, latest Finding revisions with consequence reads, pending work, schedule state; eligibility CURRENT only with a healthy heartbeat AND Site head (Q1); before/after `match_state` comparison reports `SELECTION_MOVED_DURING_READ`.
- I3: DB clock for discover reconcile, S3 worker, matcher `now` and drain; one-off `recompute_consequences run` defaults to DB time, `--now` override, `now_source` reported. `SKIPPED_UNCHANGED_FENCE` clears `fence_moved_streak`.
- Gated install: `backend/deploy/schedule/assetops-schedule-tick@.service|.timer`, `tools/schedule-install-gate.py` (demo CLOSED until `I-late-reading-series-and-money-limit` resolved); `backend/README-db.md` runbook retires the per-Site consequence timer, covers `CONSEQUENCE_CLAIMED`, stop-the-tick before manual Leg B. Nothing installed.
- Tests: `test_s4_schedule_health_postgres.py` (10, incl. I3 skew and I4 two-chunk race), `test_s4_schedule_upstream_unit.py` (5), `test_s4_schedule_install_gate.py` (3). Tick cost: ~4-5 s per Site-visit tick on Windows (child start ~1 s x3), 4 Sites 12.6 s.
- Checks: full backend pytest 2115 passed; `tools/check-all.ps1` 9/9; phase-2 probes 21/21, phase-1 guard probes 20/20.
- Open: phase 3 walkthrough; I4 still needs the independent review's own race; one-off S3/S4 CLIs remain app clock and bypass the Site claim (runbook); health `STALE_NO_WORK` scan cost grows with Findings.

## S4-02d phase 3 - tick-only late-power walkthrough and slice wrap-up (built, review pending)

Branch `task/S4-02d-analytic-finding-worker-schedule`, `62581ecd`..HEAD. Handoff `archive/agent-history/S4-02d-phase-3-handoff.md`; slice packet `archive/agent-history/S4-02d-review-packet.md`.

- Phase-2 review fixes: F-A health alarm `S3_STALE_NO_JOB` (selected UTC day `STALE_PROJECTION` with no live S3 job; Site `FAILED`) and `assess_dispatch requeue --day` (refused unless STALE with no live job); F-C service `TimeoutStartSec=900`; F-D install-gate dedupe; phase-1 probes usage.
- I3 residual (open, evidence owner): scheduled S3 cutoff is DB time, `ingestion_disposition.decided_at` is the ingestion app clock; documented in `backend/README-db.md`; ingestion unchanged.
- `tools/s402d_tick_walkthrough.py` (reuses `s402c_late_power_walkthrough.LateWalk`; DB `assetops_s402d3walk*`, environment `walkthrough`): five schedule ticks only, command-log grep for hand-run Leg B (mutation caught). Evidence `archive/agent-history/S4-02d-walkthrough-evidence.md`: 23/23; tick 3 rebuilt S3, appended r2 citing the late ID, r1's EVIDENCE_ACCEPTED attempt typed `FINDING_REVISION_SUPERSEDED` no-op, r2 CURRENT PRICED; seam CURRENT only after the tick; stopped worker blocks the seam.
- I4: proved by the independent phase-2 review race (0 false CURRENT).
- Open: F-B statement-level guard; evidence-owner `decided_at` packet; health scan cost; S5-01 seam carries; demo-host tick cost; no owner-visible install before F1.

## S4-06 - equal-start future price succession (built, review pending)

Branch `task/S4-06-price-succession` from main `7c72c6b3`; packet `archive/agent-history/S4-06-review-packet.md`.

- `financials/assumptions.py` `plan_assignments`: a SUCCESSION whose `valid_from` equals the sole open-ended current assignment's start closes it and inserts only the new `[valid_from, inf)` row (Architect S4-02 Q1); no zero-length remainder. Later-start SUCCESSION, INITIAL, CORRECTION, `SUCCESSION_NOT_FUTURE` and `SUCCESSION_OVERLAP_NOT_PERMITTED` (bounded / >1 overlap) unchanged.
- No writer, migration or rule-8 change: `postgres_assumption_store.publish` already applies any plan under the Site/key advisory lock; earlier recorded cutoffs keep the scheduled assignment through the existing `snapshot` history read.
- Proofs: `test_s4_assumptions_postgres.py` `TestEqualStartSuccession` (cutoff history, retry, key reuse, stale prior, 2-publisher race, bounded/multiple refusal, CORRECTION tail on an older revision, unchanged earlier-price window selection); planner unit tests in `test_s4_assumption_publication.py`.
- Open: registry `I-price-equal-start-succession` stays `open` until merge.

## S4-04 - Site Finding index and list (phases 1-2 built, slice review pending)

Branch `task/S4-04-site-finding-index` (base main `f8a131e3`, unmerged); handoffs `archive/agent-history/S4-04-phase-1-handoff.md`, `archive/agent-history/S4-04-phase-2-handoff.md`; packet `archive/agent-history/S4-04-review-packet.md`; owner steps `archive/agent-history/S4-04-owner-walkthrough.md`.

- Read: `GET /api/sites/{site_code}/finding-index` (`finding_index_api.py`, service `analytics/finding_index.py`, SELECT-only store reads `index_snapshot`/`index_lineage` in `postgres_finding_store.py`). No snapshot table, so only `CURRENT` carries rows and `total_count`; refusals 422/409 carry neither.
- Discovery: fixed point over UTC days via stored canonical episodes within 20 min of an edge AND (phase-1 review H1) selected S3 Candidate segments within 20 min of the edge day's edge (`candidate_reach`); cap 62 -> 409 `INDEX_CONTINUITY_LIMIT`. The H1 root cause (matcher pass marking a deferred window matched) is fixed separately on `fix/S4-deferred-match`.
- UI: `sites/findingIndexClient.ts` (typed result union incl. `not_imported`, `closed`, `continuity_limit`, `basis_changed`, `invalid`), `sites/SiteFindingIndex.tsx`; `shell/SiteAnalyticsFrames.tsx` `SiteFindingsFrame` keeps scope in the URL (`domain/from/to/limit/cursor`, default today's UTC day) and falls back to the T028 `SiteFindings` on a 404. `App` prop `siteFindingIndex`. Row link text is the lifecycle title (stored titles fail the product-vocabulary scan).
- Walkthrough: `tools/s404_finding_index_walkthrough.py` (`assetops_s404_owner*`, `var/s404_owner*`, API 8934/web 5434, TLS 8935/HTTP 8936): prepare/serve/late/settle/gate/drop; browser claims `tools/s404-finding-index-evidence.mjs <base> <initial|late|settled|closed> <out> <manifest>`.
- Open: owner record; `mini:3#a/b` (S5-02 consumes this order); money stays unavailable until S4-05 provenance + LR-01 both reviewed in baseline; S5-01 Overview `finding_list` still says unavailable; plain-language copy for the W1 task; merge main after the deferred-match fix and rerun the focused index tests.
## S4-08 - Site assumption and consequence history (built, in_review; slice review gates merge)

Branch `task/S4-08-assumption-history` (base main `e46bbd7c`, unmerged); packet `archive/agent-history/S4-08-review-packet.md`. No migration; read-only (no new writer).

- Read: `financials/consequence_history.py` (`ConsequenceHistoryService`, cursor/fence, `classify`), store method `PostgresConsequenceStore.site_history` (one REPEATABLE READ snapshot: DB-clock default cutoff, fence count + max `(recorded_at, id)`, keyset page, FindingRevisions with latest consequence at cutoff, price links joined to assignments, prior digests). Route `consequence_history_api.py` `GET /api/sites/{site}/financial-assumptions/consequences?recorded_at=&after=&limit=`, included in `main.py` before the price-revision route; composed by `financials/composition.build_consequence_history_service`.
- Row contract: exact Finding/FindingRevision/consequence/price IDs, `at_cutoff` CURRENT/HISTORICAL, price state `LINKED|NO_PRICE_LINK|NOT_EVALUATED|LINEAGE_INCONSISTENT`, `change_from_prior` (`PRICE_ONLY` drives the plain sentence), `recorded_amount.disposition` `SHOWN|SOURCE_CLOSED|MIXED_OR_UNKNOWN_SOURCE|UNPRICED|QUANTITY_UNAVAILABLE|MINOR_UNIT_UNKNOWN|LINEAGE_INCONSISTENT`, per-row S4-05b block; `current_amount_shown` is always false. Cutoff string is `isoformat()` UTC (`+00:00`, microseconds), equal to the price read's echo.
- Refusals: 400 `INVALID_CURSOR`, 409 `CONSEQUENCE_HISTORY_BASIS_CHANGED` (`SCOPE_CHANGED|FENCE_CHANGED`), 422 `INSTANT_NOT_ZONED|INVALID_CUTOFF|INVALID_LIMIT|CUTOFF_REQUIRED_WITH_CURSOR`, 503 `CONSEQUENCE_HISTORY_UNAVAILABLE`; closed S3 gate lists rows with `SOURCE_CLOSED`.
- UI: `frontend/src/sites/ConsequenceHistory.tsx` ("Interpretation history" panel), `SiteAssumptions` reads history first and passes its cutoff string to the price read (default URL unchanged; `data-price-cutoff` now RECORDED_CUTOFF on default; history failure = plain price refusal `data-financials-read="no-cutoff"`); URL params `history_after`, `history_limit`; client `getConsequenceHistory` (`basis_changed` result reloads page one).
- Tests: `backend/tests/test_s4_consequence_history.py` (25), `test_s4_consequence_history_postgres.py` (7, incl. interleaved late commit), `frontend/src/sites/__tests__/siteFinancials.test.tsx` (+8).
- Walkthrough: `tools/s408_assumption_history_walkthrough.py` (wraps s405 owner+mixed under `assetops_s408*`; adds v2-v6 incl. S4-06 equal-start v5 and part-way v6); evidence `tools/s408-assumption-history-evidence.mjs` (owner/closed/mixed modes); S4-02a evidence asserts the unchanged default URL and one cutoff.
- Open: recorded amount display does not apply LR-01 eligibility (history is audit, as pinned versions on Finding Financials); Finding links pin exact IDs, not the cutoff; `assumptions:3#a` promotion waits for review; wording to W1-UX-02.
## IDX-GAPS - Site Finding index finding-index/2 (built, in_review)
Branch `task/IDX-GAPS-finding-index-v2` (from main ca6d7d61b). Contract `AssetOpsV1-plan2/specs/IDX-GAPS/spec.md` + Addenda 1-3; packet
`archive/agent-history/IDX-GAPS-packet.md`; decision `D-2026-10-31-finding-index-v2`.
- `analytics/finding_index.py`: `POLICY_VERSION` "finding-index/2", schema `site-finding-index-2`, token `sfi2-`. `gap_days` (G: non-CURRENT
  day -> NOT_CURRENT; CURRENT day whose Candidate segment reaches a non-CURRENT neighbour -> EDGE_NEXT_TO_GAP), `touched` (inclusive 20-min
  bounds, as `reaches`/`margin_ok`). When some requested day is not in G and the fence did not move: PARTIAL, rows whose touched days miss G,
  `withheld`, WITHHELD_FINDING host days. All requested days in G, or a moved fence: v1 status, no rows. v1 CURRENT bodies unchanged.
- `site_outcomes/mini.py`: `index_settled(body, board_day)` (CURRENT, or PARTIAL whose gaps do not name the board day), `finding_gap_line`
  (requested non-CURRENT days only; GAPS_NO_READINGS / GAPS_NOT_ASSESSED / GAPS_WITHHELD), `Reads.first`, `UNSETTLED_INDEX_STATUS`,
  `FINDING_TITLE` by lifecycle (Addendum 3). `board.SiteFacts.finding_gaps`; wire `finding_gaps` + `policy_versions.finding_index`.
- Frontend: `findingIndexClient` (`listsRows`, `gapDays`, PARTIAL), `productWords` PARTIAL, `SiteFindingIndex` `Partial` view,
  `OverviewFindingList` PARTIAL note and `partial-empty`, `OutcomeBoard` `data-outcome-finding-gaps` line.
- Real-data proofs `backend/tests/test_idx_gaps_postgres.py` P1-P5 + probe. R595 resolved (400d1096b); R610-R612 standing.
- Left open: R613 (estate Findings keep the all-days rule). Residual risk (probe, v1-identical): an unmatched cross-midnight Candidate block
  whose start day is a gap leaves the end day reading CURRENT 0 alone. b4 `two_board_days` Day A Cost NEEDS_ATTENTION, Day B Must-not-harm,
  ACT-048 checks stay with DEMO-SPARSE CO-1.

## FIX-S4-DOMAIN - mini matcher reads only mini_grid / dispatch Findings (built, in_review)
Branch `task/FIX-S4-domain-filter` (from main ee678cbe5). Ruling: `AssetOpsV1-plan2/specs/DEMO-SPARSE/spec.md` Addendum 3 ruling 1;
packet `archive/agent-history/FIX-S4-DOMAIN-packet.md`.
- `analytics/adapters/postgres_finding_store.py` `episodes(tenant_id, site_id, domain=DOMAIN, analytic_id=DISPATCH_ANALYTIC_ID)`
  ("mini_grid" / "dispatch"); WHERE gains `f.domain = :d AND f.analytic_id = :a` (the `_index_snapshot` predicate). `FindingMatcher.match`
  and the s4 test `stale_plan` call it with the defaults; no other implementer of `episodes` exists. `plan_pass` unchanged: a NULL
  `episode_end` on a mini episode still fails loudly.
- Tests: `test_s4_finding_domain_filter.py` (pure, recording connection: default and explicit params) and
  `test_s4_finding_domain_filter_postgres.py` (open cold excursion Finding beside the F01 mini window; pass plans only the mini OPENED;
  on the old store it failed with TypeError at `finding_episode.py:287`). The fixture disables the cold-consequence enqueue trigger inside
  its own insert transaction (the mini Site has no COLD_ROOM).
- Left open: the `_fence` revision count still spans every domain on the Site (a cold revision moves the mini fence; harmless re-plan).
