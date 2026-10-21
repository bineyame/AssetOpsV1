# W3-02 pending rulings (Lane B, commit 1)

Recorded, not decided. Commit 1 code (`8d1e6325`, `c9e19695`) applies the reading named in each item; a ruling may change it.

## c1-q1 - EV `historical_label` vs "explicit earlier cutoff" (affects commit 3)
0c `EvSiteReads.money_on` (`ev_site_reads.py:349`) sets `historical_label` only when the pinned snapshot `state == "HISTORICAL"`. That state is `known_at < watermark` in `EvReadService._snapshot` (`postgres_assessment_store.py` "historical = known_at is not None and watermark is not None and known_at < watermark"), where `known_at` is the row-local Site evidence cutoff (max disposition by the estate `k`). The 0c H1 ruling says `Historical as of {known_at}` applies "for an explicit earlier cutoff", and closure 1 Q1 / 0b M3 define HISTORICAL as estate `known_at` earlier than the captured DB time.
They differ: an explicit earlier estate cutoff with no disposition after it gives `known == watermark`, so the state is not HISTORICAL and `historical_label` is null, while the estate rule says the row is historical. Question: should commit 3 derive the label from the estate cutoff (`snap.basis_historical`), ignoring `historical_label`, or should Lane A change the facade? Commit 1 Evidence does not use this field. It applies the estate rule itself through `snap.basis_historical`.

## c1-q2 - EV `METER_GAP` input not exposed by the pinned facade
Closure 1 Q4 takes EV gaps from the complete `_next_candidates(missing, power_missing, unknown_meter)`. The 0c `EvSiteReads.capabilities_on` returns capabilities but not the selected sessions' `unknown_meter_seconds`. Interim: `EvidenceMoneySnapshot.ev_capabilities` (`estate/adapters/postgres_evidence_money_read.py`) calls `ev_site._sessions(ev_site._pinned_ctx(c, pin))` on the same connection. This is a private call, and the pinned context is built twice. Question: should Lane A add `unknown_meter` (or the session list) to `capabilities_on`?

## c1-q3 - readings applied where the spec is silent (confirm or amend)
1. EV gap codes that affect only supporting claims (`INDEPENDENT_POWER_GAP`, `SITE_IMPORT_GAP`, `TARIFF_GAP`) still form a group with `unlocks: []`. A code affects a display row only through that row's claim's missing roles.
2. Current gaps come from CURRENT (and W1 CURRENT-day) rows only. They do not come from pending, stale, unknown or historical rows. A pending or stale row keeps its prior readiness and limitation in `disclosure.prior_selection`.
3. `summary.capability_count` is the display-row count (equal to `total_count`) even under partial coverage. `full/limited/none/unknown_count` are non-null only when `status == CURRENT` and coverage is COMPLETE, and are zeros for EMPTY_SCOPE. `limited_site_count` is also null when any row is CONTRADICTORY ("null affected count").
4. Under an explicit historical cutoff the cold/EV rows are `raw_state: HISTORICAL`, with readiness CONTRADICTORY if a constituent is CONTRADICTORY and UNKNOWN otherwise. This is 0b M3 applied to cold/EV.
5. The token `sites[]` arrays for Evidence are: `selected_assessment_revision_ids` (W1 interval IDs plus window revision; cold, both analytic IDs per window; EV, the selected assessment) and `cited_accepted_evidence_ids`. Finding, Action, consequence and assumption arrays are `[]`. EV session revision IDs are not included.
6. Row link query times use `analytics.cold.plain` (six-digit `Z`), the same format the W2 Site links use.
7. On a live read's page two, the cursor cutoff is earlier than the read time, so W1 `claim_limit_on` labels the day HISTORICAL (it compares `known_at < transaction_time`). Cold/EV rows follow page one's basis mode. The selection token is unaffected because it holds IDs, not states.

# W3-02 pending rulings (Lane B, commit 2)

Recorded, not decided. Commit 2 (`d9f898e7`) applies the reading named in each item.

## c2-q1 - gap `Sites` cell names
Closure 1 says the gaps `Sites` cell shows sorted stored Site names with codes in disclosure. The accepted commit-1
wire `gaps[]` carries `site_ids` and `site_codes` only, and `rows` is paged, so a gap's Site may not be on the page.
Interim: the page maps code -> name from the loaded rows and falls back to the stored code; codes are in the gap's
disclosure. Question: should commit-1's `_groups` add `site_names` (Lane B `estate/evidence_money.py`), or is the
code fallback acceptable?

## c2-q2 - refusal copy for codes the W3-02 state table does not name
The table names copy for 401/403/404/503, `ESTATE_BASIS_CHANGED`, `INVALID_WINDOW`, `ESTATE_PARAMETER_UNKNOWN`/
`ESTATE_CURSOR_INVALID`. The endpoint actually sends W3-01 codes, including `ESTATE_SELECTION_INCONSISTENT`,
`INVALID_KNOWN_AT`, `INVALID_LIMIT`, `INVALID_CURSOR`, `ESTATE_STORE_UNAVAILABLE`. Interim (`EVIDENCE_REFUSAL_COPY`):
503 store -> the 503 sentence; `ESTATE_SELECTION_INCONSISTENT` -> the 409 sentence; `INVALID_KNOWN_AT`, `INVALID_LIMIT`,
`INVALID_CURSOR` -> `This selection cannot be read. Reset the filters.` (the W3-01 `INVALID_KNOWN_AT` copy says
"cutoff", which the plain-language rule excludes). Confirm or amend.

## c2-q3 - closure-5 B5 route-read tests for commit 2
B5 asks commit 2 route-read tests to follow generated cold/EV Evidence links into the Site read and assert the exact
window/cutoff, no 422 and base-route fallback. Commit 1's Postgres tests assert the link shape
(`test_w302_evidence_cold_scope_windows_and_citations`, `test_w302_evidence_ev_window_rows_links_and_gaps`) but do
not call the W2 Site read with it. This run built only the page/client and UI tests. Question: is following the link
into the W2 cold/EV Site API a Lane B Postgres test for this commit (new `test_w302_evidence_links_postgres.py`), or
part of Lane A's mounted-route captures?

## c2-q4 - row context words
The ledger says pending amber / historical blue context is shown separately from the readiness chip. The page uses
`New evidence is being assessed` (PENDING_RECOMPUTE), `May miss newer readings` (STALE_SOURCE), `Not yet assessed`
(UNASSESSED/UNKNOWN placeholder) and `Historical as of {estate known_at}`; the server's row
`disclosure.historical.label` stays in the row disclosure. Confirm the words.

## c2-q5 - registry prerequisites for `I-estate-evidence-root` (Lane A, commit 2)
Closure 5 S13 names the node, title and paths but not prerequisites or area. The checker forces the panel area to the
subject-area brief's owner of `globalevidence` (`estate-aggregation`), and needs a UI, a projection and a data gate.
Lane A recorded, by the W3-01 `I-estate-action-root` precedent: node `requires` `A-estate-index-scope`,
`I-capability-read`; panels `globalevidence:1-2` `requires` `I-capability-read`, `I-estate-evidence-root`,
`D-estate-comparable-sites`, status `gap` (awaiting independent review, no owner acceptance); ledger product node
`P-estate-area`; the brief's `implementation_nodes` lists the new node. Confirm or name the intended nodes.

## c2-q6 - B5 route-read follow tests and capture copy (Lane A observation, commit 2)
c2-q3 is unchanged by the captures: Lane A's captures do not follow generated cold/EV links into the W2 Site read.

## c2-q7 - raw role code in the Current ceiling cell (Lane B, commit 2 fixes)
The cold `backup` row's `Current ceiling` shows `Not observed: TRANSFER.` That text is the stored cold analytic
limitation (`analytics/cold.py:645`, `"Not observed: " + ", ".join(missing) + "."`, where `missing` holds start-chain
step names such as `TRANSFER`), carried verbatim into `current_ceiling` by `_shape_window_row` (limitations joined).
The build spec only says `current_ceiling` displays the selected claim field (ledger `Current ceiling`); no ruling maps
cold start-chain step names to plain words, and the page does not rewrite server prose. Unchanged in this fix round.
Question: (a) map on the Evidence wire (estate `current_ceiling` gets a plain sentence, e.g. per-step words, with the
stored limitation kept in `Record details`), (b) map on the page from a closed step dictionary, or (c) leave the stored
limitation verbatim and accept it? If (a)/(b), name the step words (the cold chain's steps: which codes and labels).

## c2-q8 - Evidence tests do not settle on the store read (Lane A observation, commit 2 c2b)
`frontend/src/test/settled.ts` `LOADING` does not list `EstateEvidence.tsx`'s loading copy `Loading evidence across the
estate.`, so `settledScreen()` returns immediately in `estateEvidence.test.tsx` and the assertions race the fake read.
Under full-suite load it flaked twice on `39afe950` (`rendersEvidenceEmptyPendingAndRefusals` line 323, panels `[]`;
once `namesGapSitesFromTheWireNotThePage`), and the file passes alone (4/4 runs). Not changed: `settled.ts` is shared
test infra outside c2b's assignment. Question: who adds `evidence across the estate` to `LOADING` (Lane A shared test
helper, or Lane B with its page), and in which commit?

## c3-q1 - closure 2 N3 STOP: two-EV-Site persisted COMPARABLE fixture unavailable through reviewed producers (Lane B, commit 3)
Built: Financials read/API (`estate/financials.py`, `estate_evidence_money_api.py` `/api/estate/financials`,
`postgres_evidence_money_read.py` `cold_money`/`ev_money`, `evidence_money.py:group_key_for_partition`), pure tests
and one persisted single-EV-Site proof (`test_w302_money_comparability_postgres.py::test_w302_money_persisted_ev_single_site_line`:
real replay `complete` + golden tariff + W2-07 worker -> one ELIGIBLE `GROSS_TARIFF_SCENARIO` line equal to the
stored head, its session revision and accepted evidence IDs, `SINGLE_LINE`).
Failing setup step: a second EV Site in the same tenant/database. The reviewed EV producers support exactly one:
`sites/ev_lab.py:install_ev_lab` imports only `EV-LAB-001` (`EV_LAB_SITE_CODE`, fixture `tests/fixtures/w2/ev-lab-001.yaml`,
binding conversion `conversions/ev-lab-001-bindings.json`); the W2-05b `Chain.open()` calls `pg_harness.fresh_database()`
per chain (a second chain wipes the first) and its scenario request/gateway provisioning/replay route are keyed to
`EV = "EV-LAB-001"` (`test_w205b_ev_replay_postgres.py:102,176,308,369`). A second Site would need a new Site import
fixture, binding conversion, gateway provisioning and Host run on a second code - new producer/fixture scope, not a
reuse. Not built: `test_w302_money_persisted_ev_comparable_same_values` and `test_w302_money_persisted_ev_different_currency`
(the same two-Site precondition). Per N3, commit 3 is NOT declared done. Question: (a) authorize a second EV Lab Site
fixture (code, import YAML, bindings, gateway) and a same-DB two-chain harness, owned by which lane; (b) a revised
proof contract (e.g. two disjoint EV windows on EV-LAB-001 with the same tariff, which differ in `window_start/end`
and so can never share a partition); or (c) another fixture you name.

## c3-q2 - interpretations taken in commit 3 (confirm or correct)
1. `RECORDED_REPAIR` lines are listed/partitioned when a stored head exists but the category gets no `NO_LINES`
   sentinel (outside the three-category mock enum). Sentinel categories: mini-grid operating cost, cold product
   exposure, EV gross tariff.
2. An EV `STALE_BASIS` or pending guard (or a stale/pending cold/EV window) makes that category's coverage unknown
   (`UNKNOWN_COVERAGE`), as Q19 rule 1's stale/pending selection.
3. Group `reason_codes` for missing disjointness proof is `BASIS_NOT_PROVEN` (state `OVERLAPPING_BASIS`); each involved
   line is `CONFLICT` with line reason `OVERLAPPING_BASIS` (Q6 table).
4. Two or more eligible lines with a null `assumption_fingerprint` give `INELIGIBLE` + `ASSUMPTION_UNKNOWN`.
5. W1 fingerprint `price_kind` = selected price `state`; W1 `limit` = stored `limitations` if the selector exposes
   them (it does not today, so null). W1 line citations = Finding citations plus power evidence IDs.
6. The Financials token's `selected_assessment_revision_ids` reuse the W3-01 Site coverage's selected assessments;
   cited IDs are the lines' basis evidence union; Finding/consequence/assumption arrays come from the lines.
7. `test_w302_money_unknown_coverage_precedes_no_lines` runs over the fake snapshot (pure) in the named Postgres file.

## c3-q3 - c3-q1 fixture: the second registered draft run is refused (Lane B, commit 3; N3 still holds)
Built per c3-q1 at `fefa5ab4`: `backend/tests/fixtures/w3/ev-lab-002.yaml`, `backend/conversions/ev-lab-002-bindings.json`,
`install_second_ev_site` and `two_ev_sites` in `test_w302_money_comparability_postgres.py`, and the W2-05b harness
parameters (`ev_request(case, *, site_code, seed)`, `Chain.open(*, fresh, install)`, Site-coded `_gateway/scope/replay`).
In one `w302p_test` database the first chain (EV-LAB-001, seed 20517) ran; `install_second_ev_site` then imported
EV-LAB-002 into the same tenant and published its `ev-roles-1` bindings without error.
Failing call: `RunSetupService.create_draft_run(ev_request("complete", site_code="EV-LAB-002", seed=20518))`
(`assetops_backend/runs/service.py:601` `_create_ev_draft`). Returned error: `RunSetupRefused VERSION_UNAVAILABLE:
Scenario ev-complete is a ev-scenario/1 document for the registered Site EV-LAB-001; site EV-LAB-002 is not that
registered Site.` Every shipped EV scenario (`config/scenarios/ev-*.yaml`) names `site_code: EV-LAB-001`, and the Host
re-reads the shipped scenario through `StoreEvInputs(..., cached_scenario_repository())` and verifies its digest, so no
draft, gateway upload, replay, assessment or money head exists for EV-LAB-002 (no public IDs to report).
Device IDs stay the `ev-publication/1` profile channels (`runs/profiles.py` pins them); EV-LAB-002 has its own gateway
`edge-ev-lab-002` and its own source rows (source external IDs are unique per gateway).
Not done: `test_w302_money_persisted_ev_comparable_same_values` and `::test_w302_money_persisted_ev_different_currency`
are built with the ruled assertions and skipped under `blocked_c3q3`. Question: authorize an EV scenario document for
EV-LAB-002 (e.g. a test-only `ev-complete` copy with `site_code: EV-LAB-002`, where it lives and how the Host
scenario repository finds it), or name another route.

## c3b-q1 - RESOLVED (Lane A parser item landed, commit 3) - c3b Lane A parser item not on the branch

Lane B c3b items landed in `6f065647`: test-only `backend/tests/fixtures/w3/scenarios/ev-complete-lab-002.yaml`
(shipped `ev-complete` with only `scenario_id`/`site_code`/`seed` changed), `second_scenario_repository` (temp root:
six shipped EV docs + the fixture, one `CachedScenarioRepository(ReadOnlyYamlScenarioStore(root))`), injected into the
second chain's `RunSetupService` and `StoreEvInputs` via `Chain.open(..., scenarios=, scenario_id=)`, and
`test_w302_second_ev_scenario_differs_from_shipped_only_in_three_fields` (mutation `seed: 20519`: failed, reverted).
Blocker: c3b assigns the `ev_parsing.py` change to Lane A; after merging main, `ev_parsing.py:174/181` still pin
`EV_SITE_CODE`/`EV_SEED`. Failing call: `second_scenario_repository(root).list_scenarios()` ->
`ScenarioConfigurationInvalid: EV scenario shipped:ev-complete-lab-002.yaml: site_code must be 'EV-LAB-001'`. No
Draft, upload or money head exists for EV-LAB-002 (no public IDs). Both comparability tests keep `blocked_c3q3`
(reason updated) with the c3b assertions. Question: dispatch Lane A's parser item; Lane B then removes the skip.

Resolution (Lane A, commit 3): `ev_parsing.py` admits `(EV-LAB-002, 20518)` only for `ev-complete-lab-002` and returns the
validated Site/seed in `EvScenarioDefinition`; `(EV-LAB-001, 20517)` unchanged for every other ID. Parser test
`test_w205b_ev_scenarios.py::test_the_second_site_pair_parses_only_for_its_one_scenario_id`. The fixture now parses.

## c3b-q2 - two readings needed to run the two-Site tests; COMPARABLE test still skipped on its traversal assertion (Lane A, commit 3)

1. Applied, please confirm: c3b's `CachedScenarioRepository(ReadOnlyYamlScenarioStore(root))` cannot work - the shipped
   store has only `list_scenarios`, and the cache calls `get_scenario` (`AttributeError` in `scenario_cache.py:32`).
   `second_scenario_repository` now wraps `CompositeScenarioRepository(shipped=ReadOnlyYamlScenarioStore(root),
   user=UserYamlScenarioStore(<empty temp dir>))`, the same composition as `build_scenario_repository()` over the test
   root. With it `test_w302_money_persisted_ev_different_currency` passes un-skipped (end-to-end two-Site path runs).
2. Needs a ruling: `test_w302_money_persisted_ev_comparable_same_values` passes every assertion up to the `limit=1`
   traversal, where page one's `selection_token` differs from the full read's. Page groups equal the full read's
   groups; only the token differs. Cause: a live read's cutoff (`token_k`) is that read's own wall-clock time
   (`estate/index.py:85`, `k = read_at`), and `known_at` is in the token, so two separate live reads never share a token.
   Re-reading both at one explicit `known_at` makes the read HISTORICAL, and the group then goes `INELIGIBLE`
   (`reason_codes: ['HISTORICAL']`) and the `CURRENT` assertion fails, so that is not a fix either. Options: (a) compare
   page one's token with page two's (cursor-carried) and groups with the full read, not the token across live reads;
   (b) change the token or cutoff semantics (product change, outside this run). The test carries a `c3b-q2` skip until ruled.
