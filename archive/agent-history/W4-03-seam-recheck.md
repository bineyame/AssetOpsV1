# W4-03 pre-build seam re-check (after W4-01, W3-01 and W4-02 merge)

Base checked: `C:\Users\assef\Bineyame\AssetOpsV1-plan2`, main `fea7d378` (W4-02 merged `ce098e5c`, W3-01 `b5d0a7d6`,
W4-01 `d76809dd`). This is a read-only check of `.agent/W4-03-build-spec.md` (main body plus closures 1-3) and
`.agent/W4-03-mock-measurements.md` against the merged code. Nothing was run apart from greps and reads. Line refs are
`file:line` on that revision. The spec's own lines are cited as `spec:N`.

**Result: 35 open questions. 5 Blocker, 21 Should, 9 Nit.**

## Verified as specified (no action)

- Single Alembic head `0029_w4_mini_depth`, which sets `down_revision = "0027_w4_work_cases"` (`0029_w4_mini_depth.py:40-41`). No `0028` file exists. `0030` with parent `0029_w4_mini_depth` (spec:73) is correct.
- The tick stage CHECK is `('IDLE','S3','MINI','S4','CONSEQUENCE')` (`0029:154-156`). `0030` does not need to touch it unless S1 below is ruled toward a tick stage.
- `recompute_job.domain` is text with no CHECK (`0005_evidence_ledger.py:289-305`), so `mini_opportunity` needs no DDL. W4-02 leases only its four literal domains (`postgres_assessment_store.py:158-159,367-391`), and the W4-02 read filters `j.domain = :jd` (`mini_depth/read.py:149-154`). Neither will see `mini_opportunity`.
- All scoped FK targets exist:
  - `site(tenant_id,id)`
  - `accepted_evidence(tenant_id,site_id,id)` (`0005:211`)
  - `finding(tenant_id,site_id,id)` and `finding_revision(tenant_id,site_id,id)` (`0009_finding_store.py:54,105`)
  - `work_case(tenant_id,site_id,id)` (`0027_w4_work_cases.py:28`)

  `finding_revision` has `finding_id`, `episode_start` and `episode_end` (`0009:64-105`). It has no `(…,finding_id,id)` composite, as closure 1 says (spec:308).
- Catalog arithmetic: the base DDL has 18 UNIQUE and 17 FK. The amended delta is 22 UNIQUE, 20 FK, 5 explicit indexes and 10 `<table>_immutable` triggers, and it recomputes (spec:310). The downgrade lock order is a valid child-to-parent order.
- W4-02 head rule is `selected_at <= K AND r.knowledge_cutoff <= K`, ordered `(selected_at DESC, seq DESC)` (`read.py:138-147`). This matches spec:14 and spec:284. The closure-2 scan SQL (spec:349-353) uses the correct `mini_depth_selection.domain='renewable'` value (`0029:114-127`).
- W3-01 shared provenance helpers:
  - `PublicProvenance.cited_set`, `dual_blocks` (the six-key empty alias) and `basis_sha256` (`evidence/public_provenance.py:63-72,204-221,271-277`).
  - W4-02 wraps them as `mini_blocks` (`mini_depth/provenance.py:22-36`).
- The W3-01 estate All page `/findings` is live (`frontend/src/shell/operatorSiteRoutes.ts:337`, `OperatorShellLayout.tsx:54`), so closure 3's bare `href="/findings"` resolves. The `estate-selection/2` token is `estate/scope.py:23`.
- The W4-02 positive authored renewable study exists: 06–10 Oct, 4 of 5 eligible, 18–20 kW, `AUTHORED_DEMONSTRATION` (`.agent/W4-02-review-packet.md:85-89`). A 10 kW × 1 h × USD 0.25 test scenario is therefore physically supportable by its lower bound (but see B1 for which Site).
- Mock measurements: all 26 height caps were recomputed (`mock + max(24,10%)`, rounded up) and all match spec:216-224.
  - Scenarios: 348/66 and 391/102.
  - Alternatives: 268/66 and 365/84.
  - Opportunity: 69/137/232/295/295 and 96/273/339/217/295.
  - Superseded Site Work caps: 61/348/66, 115/370/102, 326 and 348.

  The card widths (4×281; narrow 174 wide, `HxW` format), the 735/408 pair and the 1161/360 panel widths also match. Alternatives columns 459/360/302 and 115/104/101 match. W4-01's binding Site Work caps (410/460 Incidents, 384/410 Maintenance) are in `.agent/W4-01-build-spec.md:334-337`.
- `SITE_SCREEN_DESCRIPTIONS` exists (`frontend/src/ui/V69Layout.tsx:257`). The legacy CTA `Other possible explanations (Alternatives)` exists (`frontend/src/sites/assessmentAnalysis.tsx:276-279`).

## Blockers

**B1. The positive opportunity data lives on MG-W402-001, but every W4-03 fixture, principal and walkthrough is bound to KOBO-001.**
- W4-02's authored conversion and fixture Site is `MG-W402-001`, "never KOBO-001" (`backend/conversions/w4-mini-depth-cases-v1.json` `site_code`; `backend/tests/fixtures/w4/mg-w402-001.yaml:1-5`).
- W4-03 resolves "KOBO-001/Foundation/bindings" (spec:230). The fixture principal admits only "the resolved KOBO-001 tenant/Site" (spec:340).
- The Alternatives branch needs a W1 *dispatch* Finding revision on the same Site (spec:24,290). The W4-01 case fixture is KOBO-001 only (`backend/tests/fixtures/w4/w401-work.json` `site_codes`).
- A KOBO-001 replay therefore has no five-day noon selection, so no positive opportunity. An MG-W402-001 replay likely has no dispatch Finding.

**Fix:** the Architect names the Site per branch: opportunity and scenario on MG-W402-001, Alternatives and cases on KOBO-001, or both on one Site with the missing data authored. State what the principal admits per Site and where the work-link case comes from. A case and an opportunity must share a Site (spec:28).

**B2. W4-01 work commands cannot be injected through `create_app`, so the walkthrough cannot create cases "through frozen public case APIs".**
- `create_app` has no work principal or command-access parameter (`backend/assetops_backend/main.py:177-199`).
- The work router is built with the default `no_service_principal`, so every work write returns 403 (`main.py:489-495`; `work_api.py:53-56`).
- W4-01's own captures seeded cases through the service, not the served API (`.agent/W4-01-review-packet.md:42-44`).
- Spec:340 requires `serve` to inject `service:w401-fixture` for W4-01 commands, but adds only `mini_decision_*` arguments.

**Fix:** decide one of two routes:
- (a) add `work_command_access` and `work_principal` arguments to `create_app` (a W4-01 composition change; say whether that breaks "frozen");
- (b) the walkthrough seeds cases through `WorkService` in-process, as W4-01 did, and calls only W4-03 routes over HTTP.

**B3. A new `mini_opportunity` job domain leaks into W1 readers that exclude jobs by a four-domain literal.**
- The S4 Finding matcher fence counts every `recompute_job` with `domain NOT IN ('mini_renewable','mini_service','mini_fuel','mini_backup')` (`analytics/adapters/postgres_finding_store.py:112-115`).
  - Each opportunity enqueue, coalesce, lease and settle therefore moves the W1 fence. Every tick then re-plans S4 matching for the Site instead of `SKIPPED_UNCHANGED_FENCE` (`scheduling/tick.py:42,316-324`).
- The Site Evidence pending-job projection uses the same `NOT IN` literal (`evidence/adapters/postgres_evidence_ledger.py:810-818`). Opportunity jobs would show as pending recompute work on Site Evidence.
- The spec never mentions either reader.

**Fix:** have W4-03 add `mini_opportunity` to both exclusions, or switch them to positive domain lists. In either case add a regression test that an opportunity job does not move the fence or the Evidence projection.

**B4. The Q24 navigation multiset literal cannot pass the guard.**
- Spec:387-390 lists `Scenarios, Scenarios, Incidents, Maintenance, Cooling, Recommendation×2, Availability, Energy / site power`.
- W4-01 removed Incidents and Maintenance because both are live routes. The current literal is `Alternatives, Scenarios, Cooling, Recommendation, Recommendation, Availability, Energy / site power` (`tools/checks/navigation-truthfulness.ps1:742-749`).
- The second `Scenarios` assumes an EV unavailable occurrence that does not exist:
  - EV Financials renders its own `Subtabs` with only Overview and Assumptions (`frontend/src/sites/EvSiteViews.tsx:353-365`).
  - The one `<UnavailableTab label="Scenarios" />` is shared by the mini and cold Financials frames (`shell/SiteAnalyticsFrames.tsx:730-748,784,820`).
  - EV Scenarios is added only by W2-F M12, which is planned and also Lane A (`.agent/W2-F-build-spec.md:36`).

**Fix:** the literal after W4-03 is `Scenarios, Cooling, Recommendation, Recommendation, Availability, Energy / site power` if W4-03 lands before W2-F. It is the same plus a second `Scenarios` if after. Name the order.

**B5. Closure 2 gives the Opportunity page six context tabs, but the mock renders Overview only.**
- `screens.js:948` returns `tabRow([['Overview',s.id]])` for `opportunity-finding`. The measurement file records `tabs : Overview` at both widths (`.agent/W4-03-mock-measurements.md`, opportunity rows).
- Closure 1 matched this ("tab row contains only selected Overview", spec:296).
- Closure 2 "Mock fidelity correction" cites `screens.js:959` (the mini Finding tab row, which is correct for `alternatives` only) and then requires five extra disabled slots on Opportunity (spec:404,408). That is a layout mismatch, which the owner's mockup-is-the-layout-spec rule rates High.

**Fix:** restore Overview-only for Opportunity and keep the six slots for Alternatives.

## Should

**S1. The spec runs opportunity work on a separate schedule, while W4-02 put mini work into the one environment tick.**
- The tick (`scheduling/tick.py:1-25,306-313`; `stages.py:128-150`) is the single per-environment timer. `tools/schedule-install-gate.py:1-12` gates only that tick, and its `walkthrough` host class allows no timers.
- Spec:266 adds `tools/install-mini-decisions-schedule.ps1` plus a separate `run-pending`.
- The tick's Site selection keeps a Site scheduled only for Dispatch or four-domain mini work (`tick.py:160-176`; `stages.py:96-100`), so an opportunity job never keeps a Site scheduled.

**Decide:** a tick stage (which needs a `schedule_site_head_stage_check` change and counters in `0030`, so the spec's catalog delta grows) or a second timer. If a second timer, give its gate semantics per host class.

**S2. Who writes `recompute_job` is unresolved.**
- W4-02 precedent: the mini worker issues no job SQL and goes through `PostgresAssessmentStore` methods with a literal domain predicate (`mini_depth/worker.py:6`; `postgres_assessment_store.py:362-470`).
- Rule 8 permits only `UPDATE recompute_job SET status =` and the window widen, and only from the assessment store or ledger (`tools/checks/configuration-persistence.ps1:648-680`).
- Spec:308 registers `mini_decisions/worker.py` as a direct job writer. Spec:363 uses `UPDATE recompute_job SET available_at=greatest(...)`, which no guard pattern allows.
- The generic `lease_job` would accept `mini_opportunity`, because it refuses only the four W4-02 domains (`postgres_assessment_store.py:334-335`).

**Decide:** new assessment-store `*_opportunity_job` methods (the W4-02 pattern) or a direct writer plus a new guard allowance and its probes.

**S3. The opportunity selection's job FK cannot be "scoped".**
- `recompute_job` has no `UNIQUE(tenant_id,site_id,id)` (`0005:289-305`).
- W4-02 used an unscoped `mini_depth_selection_job_fk` plus a service match check (`0029:128-130`; `mini_depth/store.py:201-210`).
- Spec:262 and spec:308 say "scoped/validated" while forbidding `recompute_job` DDL (spec:344).
- The revision's `source_job_id` is not in the 20-FK count. Is it a plain column?

**S4. The `0030` DDL is split across spec:75-172, spec:262 and spec:308, with no consolidated column list.**
- The split covers:
  - root `create_key`/`create_payload_sha256`;
  - which tables gain `actor_kind`;
  - the work link's missing `authorization_basis`/`idempotency_key`/`payload_sha256`;
  - producer, job and version columns on revision versus selection;
  - the length CHECKs;
  - the full `mini_opportunity_scenario_link` table.
- Unit 1 must assert "exact constraint/index/trigger names from `pg_catalog`" (spec:310), but only the trigger names and one index name are given.

**Fix:** one consolidated `0030` DDL with constraint names.

**S5. W4-02 appends a new selection seq even when it reuses a revision.**
- `append_selection` always INSERTs a selection and reuses an identical-digest revision (`mini_depth/store.py:213-246`). Every renewable rerun of an unchanged noon hour therefore yields a new `seq`.
- W4-03's vector and pins are keyed by `(local_day, selection_seq, mini_revision_id)` (spec:278,346). Each such rerun would:
  - make every scenario pin "non-head", so the calculation is `WITHHELD` (spec:278);
  - queue a new opportunity job;
  - append a selection.
- The opportunity `input_sha256` contents are never defined (spec:141,262).

**Decide:** whether headness and staleness compare `mini_revision_id` only, and the exact digest input.

**S6. Retention does not reach the fixture dates.**
- 0029 retention is rolling `p_at - interval '5 days'` (`0029:286-287`), not Site-local days. Spec:346 binds `:retention_start` as "earliest retained Site-local noon".
- The fixture days (06–10 Oct 2026) are outside a 5-day retention at build time, so the scan never enqueues them.
- The walkthrough `replay` step (spec:340) never calls `reconcile`.
- The scan's clock is not injectable for tests.

**Fix:** define the retention bound, add `reconcile --site ... --from ... --to ...` to replay, and add a test clock seam.

**S7. Missing-day status semantics conflict.**
- W4-02 `compose_renewable` returns `UNKNOWN` when any requested day lacks a selection (`mini_depth/read.py:217-233`).
- The W4-03 table maps "one or more missing/conflicting days" to Evidence limited (spec:35). Closure says "absent selected revision → UNKNOWN" (spec:276) without saying per day or all days.
- W4-02's decision set is `ELIGIBLE|EXCLUDED|LIMITED|CONFLICT`, and assessed means `ELIGIBLE|EXCLUDED` (`rules.py:312-319,395-411`). W4-03 should name this mapping for "complete assessed day".

**S8. The decimal-string wire conflicts with W4-02's stored floats.**
- W4-02 stores bounds as JSON int or float (`mini_depth/projection.py:29-38`) and serves numbers (`read.py:196-204`).
- Spec:298 requires base-10 decimal strings for physical ranges, but the spec:50 example uses numbers.
- Undefined: the conversion and normalization (for example `Decimal(str(x))`, `"18"` vs `"18.0"`), and whether `mini_opportunity_revision.result` stores strings.

**S9. Reuse or reimplement W4-02 currentness?**
- `MiniDepthRead.read(domain='renewable', lo=first midnight, hi=midnight after last)` already returns, per noon hour, the head, job state, stale-digest state, rows and dual provenance blocks (`read.py:337-432`).
- The head, job and stale-digest pieces are private helpers (`_HEAD`, `_JOBS`, `_cutoff_sha`, `read.py:138-166`).
- The spec does not say whether the opportunity and scenario reads call `MiniDepthRead`, import the helpers, or reimplement the input-digest staleness rule. Reimplementing it is non-trivial and risks drift.

**S10. Performance gate and scope helper.**
- The W4-02 mini router has no performance gate (`mini_depth_api.py:98-150`; `main.py:454`).
- Spec:306 adds 409 `PERFORMANCE_CUTOVER_CLOSED` "for a cutover-closed Finding/physical read" without naming which W4-03 routes take `performance_gate`, or its order relative to `SITE_ROLE_UNSUPPORTED`.
- Site type and timezone come from `ImportedSiteRegistry` (W4-02 `mini_depth_api.py:102-115`), not from W4-01's `ledger_scope` tuple (`work_api.py:71-84`). Name the one to use.

**S11. The guarded unavailable components cannot carry the bespoke copy the spec requires.**
- `UnavailableTab`, `UnavailableChip` and `UnavailableLinkEntry` render a fixed `Not available yet` (`frontend/src/ui/UnavailableEntry.tsx`). The guard counts them as a closed multiset.
- The spec requires custom sentences in those slots:
  - the Analysis tab (spec:406);
  - the five Opportunity tabs (spec:408, but see B5);
  - the Site Findings chip `Opportunity index unavailable; ...` (spec:268,381), while `Opportunities` stays in `$expectedChips`;
  - `Scenario detail unavailable` and `Scenario creation unavailable` (spec:300).

**Decide:** extend the guarded component, or use plain text outside it. Also decide whether these new slots enter the multiset; the Q24 literal excludes them.

**S12. The canonical Finding frame shape conflicts with the closure-2 Alternatives view.**
- One frame renders every child view with `Finding | Evidence | Alternatives | Recommendation | History` and a Site-rooted trail (`SiteAnalyticsFrames.tsx:603-628`).
- Spec:406 gives only the Alternatives view `Overview | Analysis | …` and a global trail, so the tab row would differ between views of one Finding.
- Cold and EV Findings enter this same frame for any child view (`SiteAnalyticsFrames.tsx:563-599` branches only when `findingView` is undefined). A live Alternatives entry would therefore appear for cold and EV Findings, whose Alternatives GET returns 404 (spec:290).

**Decide:** scope the tab by Site type, and keep the tab/trail consistent across views.

**S13. The Financials split assumes cold and EV occurrences that do not exist.**
- The generic `SiteFinancialsFrame` branch serves MINIGRID and every non-cold Site (`SiteAnalyticsFrames.tsx:790-826`). EV uses its own subtabs (see B4).
- Spec:302 assumes cold and EV "retain their existing unavailable occurrences in their own frames".
- This overlaps W2-F M12 (Lane A). Name the build order and the owner of the EV slot.

**S14. The Opportunity CTA lookup is undefined.**
- The W4-02 renewable page must resolve the exact five-day study (`frontend/src/sites/MiniPerformance.tsx:549`).
- The opportunity row shape has no `first_day`/`last_day` (spec:50,53), and the list returns every intersecting study (spec:286).
- Define the query, the matching field, and the rule for a renewable window that is not five days.

**S15. The scenario list window is undefined in practice.**
- The list filters by root `created_at` in `[from,to)` (spec:286), but the mini Financials frame has no window control (`SiteAnalyticsFrames.tsx:790-826`).
- The authoring DB time is unrelated to the renewable dates. What `from`/`to` does the page send?

**S16. The example scenario pin would fail the positive fixture.**
- The example pins one tuple, `2026-10-06` (spec:253-254). That is the EXCLUDED day of the positive study (`.agent/W4-02-review-packet.md:97`).
- An opportunity link needs the exact five-tuple pin (spec:260).

**Fix:** confirm the fixture pins all five days.

**S17. Two head rules for alternatives conflict.**
- One rule: the head per `(finding_id, alternative_key)` at cutoff (spec:284).
- The other: "a selected old Finding revision displays its exact alternative rows" (spec:24,284).
- After a carry-forward to R2, reading R1 needs a head per `(finding_revision_id, key)` and a `review_state`. Define the query.

**S18. The commit plan is ambiguous and breaks tests in unit 1.**
- The spec has two incompatible plans: five commits (spec:232-238) and nine units (spec:310).
- The named tests belong to the old five commits. Nothing maps them to the nine units.
- 15 test files hard-code the head `0029_w4_mini_depth`. Examples: `test_s1_bindings_postgres.py:118`, `test_w401_migration_postgres.py:28`, `test_w207_ev_money_postgres.py:38`, `mini_depth_probe.py:22`.
  - They fail as soon as unit 1 adds `0030`, but spec:240 places the update at closeout.

See the sizing section below.

**S19. 0030 downgrade does not address opportunity jobs.**
- The 0029 refusal checks only the four mini job domains (`0029:310-326`). The 0030 downgrade checks only its ten tables (spec:310).
- A downgrade therefore leaves `mini_opportunity` jobs that no worker leases.

**Decide:** refuse on those jobs, or tolerate them.

**S20. Provenance inputs for the authored lists are undefined.**
- The list envelope needs selected and pending blocks (spec:286), but nothing says which revision IDs and accepted IDs feed `cited_set`:
  - for scenarios: the pinned mini revisions?
  - for alternatives: the cited accepted IDs plus the Finding revision?
- For opportunity, does the basis use the five mini revision IDs (spec:15) or the opportunity revision ID (spec:276)?

**S21. The W3 estate Opportunities lens is not "unavailable".**
- W3-01 shipped a live `/findings/opportunities` route with honest empty copy, `No supported opportunity Finding in this selection.` (`frontend/src/estate/findingIndex.tsx:35-62`).
- The replacement test asserts the lens "retains its unavailable state" (spec:381).

**Fix:** assert the live-empty lens with no opportunity rows and an unchanged token.

## Nits

- **N1.** "Dispatch Finding" should be a named predicate: `finding.domain='mini_grid'` (`0022_w2_cold_assessment.py:56`) and/or the analytic ID (spec:290).
- **N2.** The RULED_OUT interval rule has two edge cases:
  - `finding_revision` allows `episode_start = episode_end` (`0009:102`), so the half-open interval is empty;
  - the interval of a point reading is undefined (W4-02 uses `coalesce(interval_*, source_time[+1µs])`, `0029:249-250`).
- **N3.** The registry targets named in the spec are not registry nodes:
  - `A-alternative-comparison` is only a proposed gate on `analysis:3#b` (`v69-dependency-registry-pilot.json:314`);
  - `FinancialScenario` and `RenewableOpportunityWindow` are mock entity names (`screens.js:584`), not nodes (spec:310).
  - No `panels[]` entries exist yet for the five W4-03 keys, which is correct, since unit 9 adds them.
- **N4.** Spec:294's "390 cap from W4-01's measured 354 px" is ambiguous: W4-01 gives `354 → 460` (`W4-01-build-spec.md:334`). The decision-context lines also grow rows beyond W4-01's stocked measurement.
- **N5.** The spec does not name the test clock seams. W4-02 has `MiniDepthRead.test_read_clock_override` (`read.py:324-352`) and the store has `test_clock_override` (`store.py:105`). They are needed for `INVALID_KNOWN_AT` and the scan tests.
- **N6.** `DecisionPrincipal` is an object, but W4-01's `Principal` returns a `str` (`work_api.py:47-56`). Should W4-03 import `work.model.ATTESTATION`, `canonical_json` and `idempotency_key` (`model.py:33-34`), or copy them?
- **N7.** The `currentness.windows` keys differ: W4-02 uses `selection_id` and `assessment_revision_id` (`read.py:385-391`), while W4-03 uses `selection_seq` and `mini_revision_id`. Confirm this is intended.
- **N8.** `DECISION_USER_AUTH_REQUIRED` and `DECISION_ATTESTATION_INVALID` appear only in prose (spec:248), not in the error table.
- **N9.** The supersession row at spec:327 ("Site-rooted breadcrumb" for Opportunity) is not expressly revoked by closure 2, which revokes only the "last row".

## Already delivered by W4-01, W4-02 or W3-01 (W4-03 must reuse, not rebuild)

**W4-01**

- Command gate and refusal order: `build_work_router(..., command_access, principal)` (`work_api.py:63-95`).
- `ATTESTATION` regex, `SERVICE_GRANT_PREFIX`, the canonical actor, idempotency and the path/body hash (`work/model.py:33-34`; `work/service.py:99-203`).
- Site Work list wire (`work/site_index.py:241-258,325-336`):
  - `case_id`, top-level `known_at`, and `total_count` before paging;
  - `url:null`, `finding_links` and `action_links`;
  - maintenance `outcome_state:"UNVERIFIED"`, `outcome_note` and `next_evidence_copy`.
- The frozen Site Work copy is already shipped (`frontend/src/sites/siteWorkCases.tsx:105-107,246,440-446`):
  - `Count unknown · work source unavailable`;
  - static `Manage in … · Not available yet`;
  - the notice;
  - `No outcome recorded`, the `Unverified` badge and `No next evidence recorded`.

  The W4-03 ledger rows for Site Work (spec:196-198) are delivered apart from the decision-context lines.
- The `WORK_CASE_NOT_FOUND` message (`model.py:42`). The `work_case` scoped UNIQUE used by the FK (`0027:28`). The registry `panels` entries `sitework-incidents:1` and `sitework-maintenance:1`, status `gap`.

**W4-02**

- The noon-hour head at cutoff, overlapping-job state and input-digest staleness (`mini_depth/read.py:138-166,408-432`).
- Validation of 1–5 consecutive full local days (`read.py:96-116`) and `local_noon`.
- The five-day eligible/assessed denominator and `recurrence_established` (`rules.py:395-411`). `opportunity_kwh = headroom`, but only for ELIGIBLE (`rules.py:378-383`; `projection.py:125-133`).
- The dual provenance adapter `mini_blocks` (`provenance.py:22-36`). The non-MINIGRID `SITE_ROLE_UNSUPPORTED` envelope pattern (`mini_depth_api.py:78-96,131-135`). Six-digit `iso` (`read.py:82-84`).
- The renewable Productive-use panel (`MiniPerformance.tsx:534-562`):
  - the `No productive-use scenario has been assessed.` sentence;
  - the `Opportunity decision` unavailable slot;
  - the constraints drawer.
- Noon-only renewable selections, the head index (`0029:131-132`), and the MINI tick stage.
- The positive authored five-day study on MG-W402-001 (see B1).

**W3-01**

- The live `/findings` root (the closure 3 link target). The `estate-selection/2` token (`scope.py:23`).
- The live, empty estate Opportunities lens (see S21). `dual_blocks`, `cited_set` and `basis_sha256`.

## Commit sizing: one builder run per unit, with a "read only these sections" index

Closure 1's nine units (spec:310) control. Measured against the merged code, units 2, 6 and 9 are each too large for one run. Proposed: 12 units. Every unit also reads its Blocker or Should rulings once they are answered.

| Unit | Output | Read only |
| --- | --- | --- |
| 1 | `0030`, consolidated DDL (S4), catalog/name test, downgrade, the 15 head-pinned tests (S18), rule-8 table registration, store INSERT skeletons per table (anti-vacuity) | spec:71-174, 262, 308, 310 (catalog and lock order); 0029 file; `configuration-persistence.ps1:780-830` |
| 2a | Scenario rules (closed keys, decimals, currency) + pure vectors | spec:22, 278, 280, 298, 394-396 |
| 2b | Shared pinned-noon currentness helper (S9) + scenario write/read API, `create_app` injection | spec:43-69, 246-262, 282-286, 336-338; `mini_depth/read.py`; `work_api.py` |
| 3 | Alternatives API, exact Finding revision, RULED_OUT | spec:24, 250-262, 284, 290; `0009_finding_store.py:33-105` |
| 4 | Opportunity scan/enqueue/worker/projection/reconcile, B3 reader fixes, job ownership (S2) | spec:26, 264-266, 342-368, 308 (`selected_hours`/`result`); `postgres_assessment_store.py:326-470`; `mini_depth/store.py:179-246` |
| 5 | Opportunity list/detail/currentness/provenance, opportunity-scenario link | spec:26-41, 260, 276, 282-288, 304 |
| 6a | Scenarios page + Financials split + nav guard/fixtures | spec:182-185, 300-302, 383-392, 216-220; `SiteAnalyticsFrames.tsx:720-830` |
| 6b | Canonical Alternatives tab, breadcrumb, CTA retarget | spec:186-190, 272, 312, 402-406, 410-421; `SiteAnalyticsFrames.tsx:515-640` |
| 7 | Opportunity page + W4-02 CTA | spec:191-195, 296-298, 304, 408, 414; `MiniPerformance.tsx:534-562`; measurements (opportunity) |
| 8 | Work decision-context overlay (API + UI) | spec:28, 274, 294; `work/site_index.py:199-336`; `siteWorkCases.tsx` |
| 9a | `tools/w403_mini_decisions_walkthrough.py` + fixture JSON | spec:228-230, 280, 336-340, 375-376 |
| 9b | Registry panels, captures, check-all, full suite, packet | spec:226, 238-240, 398-400 |
