# W4-02 pre-build seam re-check (after W4-01 merge)

Base checked: `C:\Users\assef\Bineyame\AssetOpsV1-plan2`, main `4049a72c` (W4-01 merged at `d76809dd`). Read-only check of `.agent/W4-02-build-spec.md` (main body plus closures 1-3) and `.agent/W4-02-mock-measurements.md` against the merged code. Line refs are `file:line` on that revision. Nothing was run apart from greps and reads. The spec's own line numbers appear as `spec:N`.

**Result: 20 open questions. 3 Blocker, 9 Should, 8 Nit.**

## Verified as specified (no action)

- Single Alembic head `0027_w4_work_cases` (`0027_w4_work_cases.py:5-6`, down `0026_w2_ev_money`). No `0028` file exists, so `0029` with `down_revision = "0027_w4_work_cases"` (spec:192) is correct.
- `recompute_job` (`0005_evidence_ledger.py:289-308`): `domain text` has no CHECK, so `mini_*` values need no DDL. Lease is filtered by domain (`postgres_assessment_store.py:333-334`). The mutation trigger lets `available_at` change on a PENDING row (`0005:349-367`). `0027` does not touch `recompute_job`.
- `ingestion_disposition(batch_id, ordinal, tenant_id, site_id, decision, accepted_evidence_id, decided_at)` (`0005:246-266`). `decide_chunk` writes the accepted row and its disposition in one `_run(write=True)` transaction (`postgres_evidence_ledger.py:430-510`), which confirms closure 3 item 2.
- The W3-01 shared helpers are on main through W4-01's cherry-picks: `PublicProvenance.cited_set`, `LinkRowsReads`, `dual_blocks` and `basis_sha256` (it returns null when nothing is selected) are in `public_provenance.py:63-72,204-277`, and `link_rows_on` is at `postgres_evidence_ledger.py:1105`. The W3-01 *estate* `actions` route is **not** merged (`tasks/README.md:106` "planned"; App.tsx has no estate actions route), so the Q23 fallback `Actions unavailable` applies.
- `assessment_inputs.py:82,105,323,347`. `postgres_assessment_store.py:243,268,488,553,616,870`. `assessment_worker.py:60-61` is the `ROLES_BY_SET` tuple. `fuel_cost.py:59-81` has `fuel-cost-1/sfc-upper-multiplier/v1` set to 1.10.
- Navigation multiset after W4-01: tabs `Alternatives, Scenarios, Cooling, Recommendation×2, Availability, Energy / site power`; chips `Cost, Risks, Opportunities` (`navigation-truthfulness.ps1:747-749`). The mini tabs are not in it, which matches Q10.
- `INVERTER` and `AC_BUS` component types exist (`sites/models.py:32-35`, `foundation_content.py:43`). `authored_fixture_specs.py:17-18` has the registration pattern. `UnavailableLinkEntry` exists (`ui/UnavailableEntry.tsx:46`).
- Mock measurements: I recomputed all 48 height budgets (`mock + max(24, 10%)`, rounded up), the 390 inner-scroll widths (379/511/719/326), the row budgets and the 735/408 pair widths. Every one matches spec:71-76 and Q30.
- W4-01 read clock: `clock_timestamp()` as the first statement of a REPEATABLE READ snapshot, with a private `test_read_clock_override` (`work/adapters/postgres_work_read.py:5-6,287-297`). Q31 is compatible with it (see N6).

## Blockers

**B1. The domain to role map in the enqueue trigger is never written down.** Closure 2 (spec:229) queues an hour "only for roles used by that domain". Closure 3 (spec:274) says that exactly three of the 17 gate roles (`pv_irradiance`, `battery_power`, `pcs_discharge_capability`) have no mapping. That implies a map for the other 14, but the spec never gives it. Open cases a mid-level implementer would have to settle alone:
- Does `pv_power` or `pv_available_power` feed renewable "observed PV"?
- Which domain do `battery_soc` and `fuel_level` belong to?
- Is `generator_state` used by fuel, by backup, or by both?
- Do `critical_load_*` belong to service, renewable or backup?

This ends up as a frozen SQL literal in `0029` and decides which jobs every MINIGRID accepted row creates (see S4). **Fix:** a closed table `domain -> roles[]`, plus a migration-test assertion of that table.

**B2. The roles-4 EVENT and STATE channels cannot be accepted as specified. If they are made acceptable, they enqueue cold work.**
- v4 acceptance requires the closed `V4_CHANNEL_MAPPINGS` entry and pinned `v4_metadata` (`evidence/ledger.py:418-431`). The v4 tables exist only for cold and EV (`binding_service.py:222-225,391`).
- Closure 2 (spec:262) forbids mapping roles-4 to a v4 Lab profile, but does not say whether W4-02 adds an authored roles-4 v4 mapping profile.
- Without one, every `backup_start_event` EVENT is `MAPPING_INCOMPATIBLE`. The positive observed backup chain and the start-request cards are then unreachable, leaving only the spec:264 fallback.
- With one, `decide_chunk` enqueues `cold_chain` work for any v4 record whose role is in `COLD_ROLE_NAMES`, and that check does not look at Site type (`postgres_evidence_ledger.py:67,466-468`).
- `backup_start_event` and `backup_bus_state` already exist in `cold-roles-1` (`binding_roles.py:137-145`). The bus role there uses `BUS_STATES = POWERED|UNPOWERED` (`binding_roles.py:41`), whereas Q1 uses `ENERGIZED|DEENERGIZED|UNKNOWN` (spec:140).

**Fix:** the Architect decides between (a) an authored roles-4 v4 mapping profile, with the cold enqueue gated on `site_type='COLDCHAIN'`, and (b) declaring positive backup replay out of scope up front. If (a), also choose distinct role names or confirm that per-set enums are intended.

**B3. The Overview backup card has no slot.** Q24 (spec:188, 258) adds a backup mini read and a card ("Observed chain …"). The shipped W1 Overview has exactly five objective cards: Service, Dispatch, Battery, Fuel, Renewable (`frontend/src/sites/SiteWindowOverview.tsx:370-382`). The v69 mini Overview mock is the same five (`frontend/mockups/v69/screens.js:265`). The mock's Backup row is in the separate capability table (`screens.js:198`). Under the "mockup is the layout spec" rule, a sixth card is a layout mismatch. **Fix:** drop the Overview backup read, or place it on the existing capability-table row, and state which.

## Should

**S1. Reusing the Dispatch cutover gate conflicts with Q10.**
- Q12 (spec:164) reuses `performance_gate`. That gate is closed unless a file-backed **Dispatch** comparison report for the Site PASSED and the Dispatch lineage is intact (`main.py:346-355`, `analytics/performance_comparison.py:184-214`).
- Consequences:
  - Every mini read returns 409 on test and replay databases with no comparison report.
  - Every mini read returns 409 for COLDCHAIN and EV Sites, which contradicts Q10's "authorized non-MINIGRID returns 200 UNKNOWN `SITE_ROLE_UNSUPPORTED`" (spec:158).
  - The Overview card rules (spec:258) do not say what a 409 renders.
  - Republishing KOBO bindings under roles-4 can move the Dispatch-classified revisions and close the gate until the comparison is rerun. Neither the replay steps nor the API tests mention this.
- **Fix:** decide the gate (Dispatch gate vs. none), its order relative to the non-MINIGRID UNKNOWN, and how 409 renders on the Overview.

**S2. The `recompute_job` writer guard has no place for the mini worker or the publication enqueue.**
- Rule 8 lets only the ledger and `postgres_assessment_store.py` write `recompute_job`. That includes `UPDATE … SET status` (`configuration-persistence.ps1:641-670`).
- Calls to an enqueue SQL function count as job writes. They are allowed only from the assessment store, plus the Foundation store's single `ev_enqueue_configuration` allowance (`configuration-persistence.ps1:738-748,864-871`).
- Q25 (spec:190) registers only the three mini tables. Two things are left open:
  - whether `mini_depth/worker.py` leases jobs and marks them DONE itself (a new allowance) or through `PostgresAssessmentStore`, which is the cold/EV precedent;
  - which writers may `SELECT mini_enqueue_configuration(...)`.

**S3. Shared `recompute_job` readers have no domain filter.**
- The S4 matcher fence counts every job for the Site (`analytics/adapters/postgres_finding_store.py:112-115`), so every mini enqueue moves the W1 Finding fence.
- The Site Evidence `site_window` pending-job projection groups all domains (`postgres_evidence_ledger.py:796-803`).
- `dispatch_jobs` returns every domain, despite its name and docstring (`postgres_evidence_ledger.py:955-963`).
- Hourly mini jobs will change W1 Evidence and Finding behaviour. **Fix:** decide whether W4-02 adds domain filters to these shared W1 reads.

**S4. Existing tests on the MINIGRID KOBO kit break, and Q25's update list misses them.**
- `test_w200_source_events_postgres.py:176-181` asserts that only `dispatch` jobs exist outside the cold and EV domains.
- `:568` and `:633-634` insert accepted rows directly with no disposition (`raw_copy`, `:472-482`) for roles in the closure-3 gate list. That now raises `23514` at commit.
- `test_s2_evidence_ledger_postgres.py:171,179` asserts `len(job)==1 and domain=='dispatch'` (whether it breaks depends on B1).
- The Q25 head-literal list (spec:190) also omits 8 files that pin `0027_w4_work_cases`: `test_s1_bindings_postgres`, `test_s2_evidence_ledger_postgres`, `test_s405_publication_postgres`, `test_s4_consequence_store_postgres`, `test_s4_evidence_consequence_work_postgres`, `test_w200_source_events_postgres`, `test_w201_cold_foundation_postgres`, `test_w207_ev_money_postgres`.

**S5. Moving KOBO-001 to roles-4 drops S6 verification and fights the demo config.**
- `VERIFICATION_ROLE_SETS = {minigrid-roles-3}` (`binding_roles.py:233`) gates `verification_readiness` (`binding_service.py:846`).
- `demo_configuration.py:178` republishes whenever `current.role_set != spec["role_set"]`, and `kobo-001-s6-verification-demo-config.json:19` pins roles-3.
- The authored W4-02 fixture targets KOBO-001 (spec:264), as the S4 authored cases already do (`s4-power-demo-cases-v1.json:7`).
- **Fix:** add roles-4 to `VERIFICATION_ROLE_SETS`, or use a separate fixture Site, and state what happens on a demo-config re-run.

**S6. Q10's "/analytics capability declarations" has no defined shape for the mini domains.**
- A declaration is an `AnalyticDeclaration` that requires `finding_type`, `claim_levels`, `thresholds` and a readiness basis (`analytics/declaration.py:343-373`), and `tools/checks/analytic-declaration.ps1` enforces those fields. Mini-depth has no Finding type.
- The predicate "a MINIGRID Site with an installed W4-02 reader" is undefined.
- The frontend renders only `RENDERABLE = {"dispatch"}` (`SitePerformance.tsx:56,196`), and subtabs come from `performanceSubtabs(profile, served)` (`presentationProfile.ts:143-150`).
- **Fix:** name the declaration source for the four tabs (a declaration entry vs. a separate served list) and the order mechanism.

**S7. The schedule installer conflicts with the repository convention.**
- Workers run as stages of one environment tick (`scheduling/stages.py:1-20`), and per-worker timers were retired (`backend/README-db.md:95-123`).
- `tools/schedule-install-gate.py` requires `--host-class` and installs nothing itself.
- Closure 2 (spec:233) asks for a separate `tools/install-mini-depth-schedule.ps1` periodic job.
- **Fix:** decide whether this is a new tick stage or a separate timer, and which host class it is gated for.

**S8. The time zone source is the mutable Site row, not the Foundation.** The spec says "selected Foundation time zone" (spec:16, 229). The only zone is `site.timezone` (`0001_foundation_identity.py:67`, served at `sites_api.py:216`), which is a current mutable row. It is not pinned in the `result.basis` of Q15 (spec:170), so local-hour boundaries can change under existing revisions. **Fix:** decide whether to read the zone from `site.timezone` and whether to pin it in the basis or digest.

**S9. Q33's route-token rule contradicts the code.**
- Q33 (spec:208) says the frontend route is keyed by the Site **UUID** and must never be substituted for `site_code`.
- `sites_api.py:212` serves `"site_id": site.site_code`, and existing Performance clients pass that value to `/api/sites/{code}/…` (`coldAssessmentClient.ts:5-8`, `SiteAnalyticsFrames.tsx:197-211`). The spec's own example link is `/sites/KOBO-001/performance/dispatch` (spec:36).
- **Fix:** restate Q33 to match the shipped token.

## Nits

- **N1.** Q24 names `siteOverviewScreen.test.tsx` and `overviewDispatchAssessment.test.tsx`; neither exists. The Overview card tests are in `frontend/src/shell/__tests__/s5SiteWindowOverview.test.tsx`.
- **N2.** Q9's three typed properties need a `kind` (`PHYSICAL|CONTROL`, `sites/models.py:90,119`) and a carrier-map placement, following the `EV_`/`COLD_PROPERTY_CARRIERS` precedent (`models.py:254-292`). Neither is given.
- **N3.** `UnavailableLinkEntry` renders `"{label} · Not available yet"` (`UnavailableEntry.tsx:46-54`). Passing the spec's literal copy ("Actions unavailable", "Opportunity decision unavailable", "Fuel basis unavailable") would produce doubled wording. State the exact label for each one.
- **N4.** Unit ordering: unit 3's replay "records … selection seqs" (spec:264), but the worker arrives in unit 4. The calls to `mini_enqueue_configuration` from the Foundation and binding writers (spec:233) are not assigned to a unit.
- **N5.** Downgrade precedent: `0020` and `0025` also refuse while jobs of their own domain exist (`0020_w2_source_event.py:104`, `0025_w2_ev_session.py:229`). `0029` refuses only on rows in the mini tables, so it leaves orphan `mini_*` jobs. Confirm that this is intended.
- **N6.** Clock hooks are not named. Say whether to reuse W4-01's `test_read_clock_override` for reads (`postgres_work_read.py:267-297`) and `test_decision_clock_override` for enqueue tests (`postgres_evidence_ledger.py:510-513`). Also say which clock the worker's `selected_at` and `created_at` use.
- **N7.** Site-scope outage: W4-01 maps a failed scope lookup to 503 before 404 (`work_api.py:76-80`). Q11 does not cover that case for the mini router.
- **N8.** Registry and ledger precedent:
  - The W4-01 merge left its registry nodes `open` with `"task":"W4-01"` instead of closing them, whereas Q29 says close them.
  - W4-01 also updated `v69-screen-ledger.json` (coverage, task, `registry_dependencies`), which `check_v69_ledger.py` checks in check-all (`tools/check-all.ps1:72`). The renewable, service, fuel and backup ledger rows are still `coverage: deferred, task: null`, and Q29 does not mention them.

## Commit sizing

Seven units is workable. Unit 1 is the heaviest: the migration with 3 tables, 3 functions and a deferred trigger, plus roles-4, 3 Foundation properties, the writer, and the catalog and closure-3 proofs. It cannot be written until B1 is closed, and its test-update load grows with S4. Unit 3's scope depends on the B2 decision. Unit 6 depends on B3 and S1 for the Overview cards.
