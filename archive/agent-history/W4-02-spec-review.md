# Independent spec dry-read: W4-02 mini-grid depth (2026-10-20)

Reviewer: a fresh Claude spec reviewer, read-only, worktree `AssetOpsV1-plan2` on main `3e5c8a6f`. This follows the ROLE_CONFIG rule, with `.agent/W4-01-W3-01-spec-review.md` and `.agent/W3-02-spec-review.md` as precedents.

Inputs:
- `.agent/W4-02-build-spec.md` (cited as `S:Lnn`) and `tasks/W4-02-mini-grid-depth.md`;
- `.agent/W4-02-mock-measurements.md`;
- `.agent/post-W2-sequence.md`;
- `.agent/W4-01-build-spec.md` (`W4-01:Lnn`) and `.agent/W3-01-build-spec.md` (`W3-01:Lnn`), q1–q4;
- `.ai/ROLE_CONFIG.md:449-455`;
- v69 `screens.js:297-303` (renewable), `:468-474` (service), `:476-483` (fuel) and `:485-492` (backup), plus `:102` (`backupChainTable`), `:32` (`claim`), `:132` (`conf`), `:952` (tab row) and `:1013-1014` (renewable drawer);
- the merged code.

Method: I read the spec commit by commit, as a mid-level implementer would, and checked every named path, symbol, table, column, route, guard and component against the merged tree.

**State of main.** W4-01 and W3-01 are **not merged**. The newest migration is `0026_w2_ev_money.py`. There is no `0027`, no `work/` module, no `OperationalRecord`, and no `evidence/public_provenance.py`. W3-02 records `0028` as **unused** (`W3-02-build-spec.md:16`). So the spec's `down_revision` is `0027_w4_work_cases`, but that revision does not exist yet, and the W4-01 and W3-01 seams cannot be verified.

**Verified correct**, so not listed below:
- `assessment_inputs.py`: `EvidenceQuery` (`:82`), `AcceptedReading` (`:105`, including `interval_start/end`, `quality`, `foundation/binding*_revision_id`), `build_input_set` (`:347`) and `sha256_json` (`:323`);
- `PostgresAssessmentStore`: `query_evidence` (`:229`), `_configuration` (`:254`), `_persist` (`:474`), `_select` (`:539`), `window_snapshot` (`:602`) and `selected_intervals` (`:759`);
- `SourceProvenanceResolver.resolve` (`source_provenance.py:250`);
- in the DDL: `site(tenant_id,id)` is unique (`0001:78`), `accepted_evidence(tenant_id,site_id,id)` is unique (`0005:211`), `ledger_append_only()` exists (`0005:310`), and `analytic_run_selection` has a nullable `job_id` and no `known_at` (`0008:28-40`);
- the W1 overview strings (`SiteWindowOverview.tsx:371,380,381`);
- the registry nodes (`v69-dependency-registry-pilot.json:130-133`);
- all 48 layout budgets. I recomputed each one as `mock + max(24, 10%)`, rounded up, from the measurements file, and every value matches.

## Questions

### Blockers

1. **(Blocker) Role vocabulary for the four domains does not exist.** S:L24-27 and S:L132 require accepted observations for:
   - storage charge acceptance/obligation;
   - requested service for non-critical loads (residential, grain mill);
   - mini-grid supply loss (the `Grid` column);
   - generator start request/result;
   - power path;
   - load response.

   The merged `MINIGRID_ROLES_3` (`sites/binding_roles.py:82-114`) has only `generator_state/power`, `feeder_demand`, `battery_soc/power`, `pv_power`, `pv_irradiance`, `fuel_level`, `pv_available_power`, `pcs_discharge_capability` and `critical_load_requested/delivered_power`. `grid_state` and `backup_bus_state` exist only in `COLD_ROLES_1` (`:136,145`). The implementer would have to decide:
   - whether there is a `minigrid-roles-4`;
   - the role names, units, ENUM sets and cardinality;
   - which role means "supply loss" on an islanded mini-grid;
   - whether passive feeders need a request role or an authored demand model (and if a model, its shape).

   The fixture (S:L132) cannot be built without these answers.
2. **(Blocker) Authored records cannot be cited.** The spec uses attested deliveries, a witnessed dip and witnessed test history (S:L26-27, S:L59, S:L61, S:L63), but neither its schema nor W4-01's can carry them.
   - In W4-01, `OperationalRecord` kinds are `OPERATOR_LOG|MANUAL_READING|SHIFT_NOTE|SITE_VISIT` (`W4-01:216`). There is no delivery or test kind and no completeness-attestation field. The record stays `SUBMITTED`, `ACCEPTED` is unreached in W4, and it is never `accepted_evidence` (`W4-01:23,37-40`).
   - `mini_depth_revision_evidence` only has an FK to `accepted_evidence` (S:L100).

   Decide whether W4-02 consumes `SUBMITTED` W4-01 records, which kind and payload key carries delivery volume and completeness, and how a revision cites them (a second junction table? a jsonb field?). Otherwise, state that fuel residual and `last_witnessed_test_at` are always null in W4, and that the positive fixture can only prove the partial claims.
3. **(Blocker) Computation trigger and job model are missing.** S:L20 says "a worker may reuse an identical input digest", and S:L41 keys currentness on "overlapping pending/leased/failed job". The spec does not say:
   - who computes and persists `mini-*/1` revisions (a worker? a CLI? an ingestion hook?);
   - which `recompute_job.domain` value is used. The column is unconstrained text (`0025:17`). Cold and EV enqueue through acceptance triggers (`0020:104`, `0025:229-285`). Reusing the mini-grid dispatch domain would make the dispatch worker lease these jobs.
   - how a job is enqueued on a late accepted row or a binding change;
   - how the `FAILED`-clearing predicate works. `_LIVE_JOBS` (`postgres_assessment_store.py:187-191`) checks `analytic_run_selection`, and `mini_depth_selection` has no `job_id` (S:L102-108).

   No commit in S:L127-130 owns `inputs.py`, `projection.py`, `composition.py` or the worker.
4. **(Blocker) Persisted window granularity per domain is undefined.**
   - S:L33 allows service, fuel and backup reads of "one Site local day or one exact hour". The writer must know which windows it persists (per day? per hour? both?), and an hour request against day revisions finds no selection. The mock answers for the selected hour (`screens.js:470-473`, "selected hour").
   - For renewable, "the designated hour" (S:L24) has no definition: an authored Foundation property? a scan of all hours? the mock's fixed 12:00-13:00?
   - The aggregation of `capability_kw`, `used_kw` and `headroom_kw` across 1-5 days and the eligible hours is also unspecified (S:L39).
5. **(Blocker) Site-local days conflict with the shipped UTC day.** S:L16, S:L33 and S:L54 want Site-local days, defaulting to "the selected Site day from the shell". The shipped shell and overview select **one UTC day** (`site_overview/route.py:11-12,47-67`, `NOT_ONE_UTC_DAY`). W3-01 windows are whole UTC days (`W3-01:129`), and Dispatch windows are UTC-day windows (`postgres_assessment_store.py:134-136`). Decide:
   - how a UTC-day shell selection maps to a Nairobi local day;
   - which day the `Compare with Dispatch evidence` and fuel dispatch-output joins use when they straddle two UTC days;
   - the URL parameter set (`date=` or `from/to/known_at`; cold uses `coldWindowFromParams`, `coldAssessmentClient.ts:202`).
6. **(Blocker) The envelope's `currentness` cannot represent 1-5 selections, and `selection_id` has no stated type.**
   - S:L36 shows a single `selection_id`/`assessment_revision_id`/`input_sha256`/`committed_watermark`. Renewable has up to five separately selected days (S:L33).
   - The example types `selection_id` as `"<selection-uuid>"`, but S:L80 says it is `mini_depth_selection.seq`, "not a UUID".

   Give the multi-day currentness shape (per-day array? aggregate state precedence?), the `selection_id` JSON type, and `basis_sha256`'s `selected_revision_ids` for 5 days (`W3-01:196`).
7. **(Blocker) The `status` enum mixes currentness with claim state, and the UI copy covers only three values.** S:L41 yields `UNKNOWN|PENDING_RECOMPUTE|STALE_SOURCE|HISTORICAL|LIMITED|SUPPORTED`. A historical supported read therefore loses `SUPPORTED`. The copy (S:L55, S:L58, S:L61) renders only Supported/Limited/Unknown. The spec does not say:
   - which of `PENDING_RECOMPUTE` or `STALE_SOURCE` a "changed watermark" yields (S:L41 writes "/");
   - the `currentness.state` and `job_state` enums (W3-01 uses `NONE|PENDING|LEASED|SETTLED|FAILED`, `W3-01:129`);
   - the source-staleness input (there is no `source_freshness` field, unlike W3-01);
   - the page copy for `PENDING_RECOMPUTE`, `STALE_SOURCE` and `HISTORICAL`.
8. **(Blocker) Domain row and card sub-shapes are not frozen** (S:L39). Missing:
   - service `requested_evidence_state` enum, the row `coverage` shape and the `assessment` enum;
   - renewable `constraints[]` code list, with a code-to-copy table for the mock's four constraint texts (`screens.js:301`);
   - fuel row `basis`, `treatment` and `value` types (scalar or `{low,high}`?) and the treatment code-to-copy table;
   - backup `steps[]` element (code, state, at, evidence_ids?), `critical_recovery` type, and `service_outcome`/`result` enums (`INCOMPLETE|FAIL|PASS|NO_EVENT`? the mock's empty row shows a `No event` badge, `screens.js:102`);
   - the limitation `code` list beyond `REQUEST_BASELINE_MISSING` and `SITE_ROLE_UNSUPPORTED`, with copy for the "What unlocks…" and "Next evidence" text derived "from missing role codes" (S:L57).
9. **(Blocker) The PV capability source contradicts merged code.**
   - S:L24 says capability is an "authored, in-force Foundation property with unit and uncertainty". No such property key exists. `_configuration` extracts only `reserve-state-of-charge` and `minimum-runtime` (`postgres_assessment_store.py:262-279`). Foundation properties have no uncertainty field.
   - The mock card reads "Reported capability; ±1 kW model allowance" (`screens.js:299`). The merged `pv_available_power` channel ("Solar available power", `binding_roles.py:98`) is a reported capability.

   Decide channel or Foundation property. If a property: the component type, key, unit, uncertainty representation and writer. Retained margin (S:L24) and backup recovery target (S:L27) have the same problem: no property key exists.
10. **(Blocker) The navigation mechanism is mis-stated.** S:L14 says to update the guard's closed unavailable multiset. Service, Fuel, Renewable and Backup are **not** in it (`navigation-truthfulness.ps1:745-746`), because the mini Performance subtab row is derived from the backend `/analytics` served-capability declaration (`SitePerformance.tsx:55-56` `RENDERABLE={"dispatch"}`, `presentationProfile.ts:143-150`). Decide:
    - whether the analytics declaration serves four new capability IDs;
    - the subtab order (mock: Service, Dispatch, Fuel, Renewable, Backup, `screens.js:952`);
    - whether a capability tab shows when the store is down or the role is unsupported.

    Also, `/sites/:id/performance/backup` is already the **cold** backup view (`SiteAnalyticsFrames.tsx:141,171`). Specify dispatch by `site_type`, and the result for a COLDCHAIN or EV Site on `/performance/mini/*` (S:L43 says UNKNOWN 200).

### Should

11. **(Should) Error codes diverge from the frozen tables and merged code.**
    - S:L43 uses `AUTHENTICATION_REQUIRED`, but merged code and W3-01/W4-01 use `UNAUTHENTICATED` (`action_index_api.py:41-42`, `W3-01:57`, `W4-01:304`).
    - S:L43 uses `INVALID_CUTOFF`, but both frozen tables use `INVALID_KNOWN_AT` (`W3-01:60`, `W4-01:390`).
    - The 404 UI copy is `This site could not be found.` against W4-01's `This site was not found.` (`W4-01:308`).
    - No exact server `message` strings are given for any code.
    - Should the detail carry `rows/total_count:null` like other reads?
12. **(Should) Does the Performance cutover gate apply?** The sibling router refuses with 409 `PERFORMANCE_CUTOVER_CLOSED` via `gate` (`performance_api.py:51-61`), and S:L43 has no 409. Also: is the router a new `mini_depth_api.py` builder or added to `build_performance_router` (S:L14 vs S:L20)? What is the exact `main.py` mount, and which `access()` 401/403 helper does it reuse (`action_index_api.py:38-45` pattern)?
13. **(Should) The knowledge filter is incomplete.** S:L16 requires `received_at <= known_at`. The merged `_EVIDENCE` filters only `d.decided_at <= :k` (`postgres_assessment_store.py:100-108`). Decide whether to add a filter, accept the shared query as is, or post-filter, without changing dispatch.
14. **(Should) The historical selection rule is unstated.** The dispatch head query ignores cutoff (`postgres_assessment_store.py:633-636`, `ORDER BY seq DESC LIMIT 1`). For `known_at` in the past, which predicate selects the head: `selected_at <= known_at`? `revision.knowledge_cutoff <= known_at`? Both? Also, `mini_depth_basis_uq` (S:L94) excludes `knowledge_cutoff`, so a reused digest keeps the first cutoff. Is that intended?
15. **(Should) Watermark, role coverage and dispatch lineage have no column.** S:L10 says `analytic_run` stores watermarks and role coverage, and S:L41 compares a "changed committed watermark". `mini_depth_revision` has neither (S:L83-95), and fuel's dispatch-derived output (S:L26) has no link to the dispatch run/revision it used. Name the `result` jsonb keys, or add columns.
16. **(Should) The fuel expected-use basis is ambiguous.**
    - S:L26 says "dispatch-derived generator output". The mock says "Measured output × configured coefficient" (`screens.js:480`), and `generator_power` is a measured role. Which one?
    - `selected_intervals` has no `known_at` parameter (`postgres_assessment_store.py:759`), so it cannot serve a historical cutoff.
    - Should the existing `specific-fuel-consumption` selection and bound rule (`financials/fuel_cost.py:48-71`) be reused for the "±10%" band?
    - `opening_l` and `closing_l` are scalars, but the bridge needs "bounded" terms (S:L26, S:L39). Scalar or `{low,high}`?
17. **(Should) The service computation is undefined.** For a one-hour or one-day window, is `delivered_load_kw` the sum of per-feeder means over covered intervals (S:L55)? What defines an interruption for `interruptions_seen` (feeder at zero? generator state?), and what is its JSON type? Where does the load classification "General service / Critical service / Productive use" come from? Only critical is identifiable, via `critical-load-priority` (`binding_service.py:246-248`). S:L56 says "pinned Foundation role", but `feeder_demand` is the binding role for all three.
18. **(Should) The pending dual provenance DTO is omitted.** W3-01 q1 #5 (`W3-01:199`) gives selected reads `selected_source_provenance` and `pending_source_provenance` siblings. S:L36 has only `source_provenance`. On `PENDING_RECOMPUTE`, which set does it describe? Is `detail` included or omitted (q1 #6, `W3-01:200`; S:L12 says "optional")? Give the no-selection envelope literal: `basis_sha256:null`, `selection_id:null`. Who adds the mini-depth adapter to the shared `public_provenance.py`, and is it Lane B's file?
19. **(Should) The renewable status bar is mis-mapped against the mock.** In the mock, `Compare with Dispatch evidence →` is the status bar's **right-hand action** (`screens.js:298`), not part of the window table (S:L54). The spec does not decide:
    - the status-bar secondary text ("Solar left unused on 3 of 5…") versus the S:L51 sentence placement;
    - whether `Watch` is ever reachable before W4-03, given there is no "productive-use decision" record (S:L51);
    - whether the confidence chip renders as the mock's popover button (`conf()`, `screens.js:132`) or as plain text `Not assessed`.
20. **(Should) Panel subtitles and card notes are unmapped** (the `panel(...,'subtitle')` and `metric(...,note)` arguments).
    - Panel subtitles: renewable `Actual one-minute means cover…` and `Electrical feasibility does not establish customer demand`. S:L53 gives a different literal, "Electrical capacity…". Is it a subtitle or body text? Also service `Delivered is measured · needed is not`, fuel `Opening + deliveries − use − closing`, and backup `Same chain as the cold-room Backup view: …`.
    - Card notes: all four renewable notes; fuel's four notes, including the dynamic `Modelled: {kW} for {min} × {L/kWh} ± {pct}`; backup's four notes. Service notes are partly covered.
    - Status secondary text for fuel (`Illustrates the minimum balance terms…`) and backup (`Generator operation alone is not a witnessed…`).
    - Page descriptions: the four `SITE_SCREEN_DESCRIPTIONS` entries are a shared Lane A file (`V69Layout.tsx:254-288`).
21. **(Should) The disabled CTA conflicts with the unavailable rule, and its copy leaks planning vocabulary.** S:L53 says "CTA is disabled with `Opportunity decisions are planned for W4-03`". S:L47 says null destinations render a noninteractive `Unavailable` control, and the shared guard forbids `disabled` on the unavailable component (`navigation-truthfulness.ps1:760`). "W4-03" is internal vocabulary on a client screen. In the mock, this CTA is a drawer opener (`claim('…','renewable')`, `screens.js:300`, `:1013-1014`), and the drawer ("Eligible-window basis" table, "Bounded translation") is not mapped at all. Is it in or out? The same question applies to `Inspect fuel basis` (`claim()` drawer, `screens.js:482`).
22. **(Should) The backup readiness-table mapping is underspecified.** S:L63 has four fixed rows, while the chain has six steps (S:L33). Say which steps feed `Supply interruption`, `Start command and state` and `Power restored to critical service`, and the source of `Witnessed outcome` (no test record exists; see Q2). Also say the empty-chain row's `Result` cell (mock badge `No event`, `screens.js:102`). The mock's empty text is "selected **hour**" against the spec's "selected period". Should the shipped cold chain table component be reused, given "same chain as the cold-room Backup view"?
23. **(Should) `Open Actions` destination differs from the mock.** The mock targets `actions` (the estate root, owned by W3-01, `screens.js:491`). S:L63 says W1 Site Work Actions. Confirm the deviation and the exact route.
24. **(Should) The W1 overview delta is under-specified** (S:L13). Decide:
    - whether `SiteOverviewRead` composes the mini reads (`dependency-direction.ps1:402-427` restricts `site_overview/composition.py`) or the frontend makes extra calls;
    - the card value and note per status;
    - the link text (mock `View detail →`, `screens.js:34,265`);
    - which `known_at` and day mapping applies (UTC day, Q5);
    - what a one-day renewable card shows (recurrence cannot be established in one day);
    - which existing overview tests change (`siteOverviewScreen.test.tsx`, `overviewDispatchAssessment.test.tsx`).
25. **(Should) Guard and registration edits are not named.** S:L123 says "0029 guard allowlist", but the spec does not name:
    - the rule-8 writer registration in `tools/checks/configuration-persistence.ps1` (the pattern at `:683-742`);
    - the SQLAlchemy/dependency-direction allowlist and module-root entries for `mini_depth/`;
    - the `tools/writer_guard_probes.py` probes;
    - the upgraded-head literals to change from `0027` to `0029` (W2 tests `test_w203…:30`, `test_w204…:38`, `test_w205a…:27`, `test_w206…:29`, plus W4-01's head assertions);
    - the catalog count deltas (W4-01 gave exact +tables/+triggers/+indexes; S:L80 gives none).
26. **(Should) The migration header is incomplete.** State the literal `revision = "0029_w4_mini_depth"` and `down_revision = "0027_w4_work_cases"`; `0028` is already recorded unused (`W3-02-build-spec.md:16`), so "expected … if 0028 unused" (S:L80) can be definite. Give the jsonb shape of `foundation_revision_ids` and `binding_set_revision_ids` (sorted UUID arrays?). Say whether downgrade runs its refusal check under a lock.
27. **(Should) The positive fixture source is undefined.** S:L132 requires role-compatible request evidence, attested deliveries and a correlated backup chain "through normal ingestion". The merged KOBO publication supplies only critical requested/delivered power (`demo_configuration.py:17-20`, roles-3). Is a new `registered-kobo-publication` version, binding conversion file (`backend/conversions/kobo-001-…json`) or Lab profile change in scope? Who owns it? What are the exact file names and dates of the five local days?
28. **(Should) Commit sizing exceeds one builder run.**
    - Commit 1 carries the migration plus four domains' pure rules and the writer.
    - Commit 3 carries four pages of six panels each, plus the overview, navigation, descriptions and guard fixtures.
    - The worker, input and projection code (Q3) and the fixture publication (Q27) have no commit.

    Propose splitting rules into two commits (renewable/service, then fuel/backup), adding a worker/enqueue commit, and splitting the UI into two pages per commit.
29. **(Should) The panel-structure test and registry edits are not named.** S:L129 names `miniDepth.test.tsx` cases but no assertion through `frontend/src/test/panelStructure.ts` / `v69PanelTitles.ts`, which other slices use (`coldRoutes.test.tsx`). Post-W2 requires reviewed per-screen panel paths in the registry before activation (`post-W2-sequence.md:9`). Which nodes close, and does `G-asset-battery-exposure`, owned by `A-mini-breadth-projections` (`registry:388`), stay open?

### Nits

30. **(Nit) Two-column split widths are not stated.** The 1440 pairs measure 735/408 px (renewable headroom/evaluation, service supported/unlock, backup operating/next), and the cards are 4-up at 1440 and 2×2 at 390. Only heights are budgeted (S:L69-74). Name the `pair` component or grid.
31. **(Nit) "Explicit past cutoff ⇒ HISTORICAL" needs a threshold.** Use DB snapshot time, as in W4-01:21, and say how an explicit `known_at` equal to read time is treated.
32. **(Nit) Focused test-count deltas are not stated.** W4-01 gave exact backend and frontend node counts (`W4-01:325`). S:L127-129 lists 9 + 7 backend and 4 frontend nodes without a stated expectation. Confirm the count, and whether `test_401_403_404_422_503` is one node or parametrized.
33. **(Nit) Some time conventions are missing.** Give the `known_at` microsecond format and the URL parameter names of the page route `/sites/{site_code}/performance/{domain}`. Frontend routes are keyed by `site_id` (`operatorSiteRoutes.ts:143-146`). Say whether the API's `{site_code}` and the route's `:siteId` are the same token.
