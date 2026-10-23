# W5-03b E5 independent review: authored EV scenario store (migration 0034)

- Branch `task/W5-03b-e5-backend`, head `50b43246`, base `29d7539c` (`git diff 29d7539c..HEAD`, 31 files, +1829/-26).
- Reviewer: fresh Claude reviewer (not the author). This review fixed nothing and touched no file in the review5 working tree.
- Judged against: `.agent/W5-03-build-spec.md` (Unit E5, "E5 exact persisted schema and wire contract", the refusal table, "E5 guard and composition ownership", P-34-2/3, "E5 consolidated correction" P-E5-1..10, the K2 lane override), `.agent/W5-02b-K2-rulings.md` "Lane 2 ruling", `tasks/W5-03-ev-depth.md`, `.agent/W5-04-build-spec.md` and `.agent/W5-04-preflight-rulings.md`.

## Verdict: REVISE

The schema, store, service, API, mount, guards and head pins conform to the spec, and the persisted producer works: I reran the E5 file myself and got 9 passed. The one blocking item is test strength, M1 below. Two refusal rows of the metered-energy baseline table have no test, although the spec assigns that table to `test_complete_session_baseline`. Those rows are absent or foreign Foundation, and foreign meter evidence. The code for both exists (and judgment call 6 rests on it), but nothing exercises it. The fix is tests only. Once M1 is closed and the Architect has answered the items below, I expect ACCEPT.

Counts: **0 High, 1 Medium, 4 Low.**

## Findings

### M1 (Medium, acceptance gap: test strength). Baseline-table refusals for Foundation and foreign meter evidence are untested.
- Code: `backend/assetops_backend/ev_scenarios/service.py:76-80` (the `foreign_meter_evidence` and `foundation_revision_id is None` refusals); `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:3100-3106,3114` (the foreign-Foundation nulling and the `foreign_meter_evidence` computation).
- Tests: `backend/tests/test_w503_ev_scenarios_postgres.py:418` (`test_complete_session_baseline`) and `:509` (`test_command_refusals_and_replay`).
- What is wrong: the spec's metered-energy baseline table is titled "(test `test_w503_ev_scenarios_postgres.py::test_complete_session_baseline`)". It requires `accepted_evidence_ids` empty or foreign to give 422, and `foundation_revision_id` absent or foreign to give 422. The tests cover the empty session and meter case (`missing-meter`) and the absent assessment (the `EMPTY_W` UNKNOWN selection). No test reaches the absent Foundation, the foreign Foundation (judgment call 6) or the foreign meter evidence branch, and no test asserts that nothing was written on those paths.
- Why it matters: these are the guards that stop an authored basis citing a Foundation or meter evidence outside the selected read. They are the provenance promise E6 and W5-04 build on, and a regression in `scenario_basis_on` would pass the suite unseen.
- Fix: add focused cases that assert 422 `EV_SCENARIO_INVALID` and `counts == [0, 0]`. Monkeypatching `foundation_revision_on` and `accepted_on` (as `test_selected_provenance_on_sets` already patches links) is sufficient. The cases are: (a) `foundation_revision_on` returns None; (b) the selected head has more than one `foundation_ids` entry and the fallback revision is outside them; (c) a cited meter evidence ID is outside `accepted_on`.

### L1 (Low, test strength). The malformed persisted-basis 503 paths are untested.
- `backend/assetops_backend/ev_scenarios/service.py:256-264,283` and `backend/assetops_backend/ev_scenarios/store.py` (`_MALFORMED`, `_MALFORMED_ROOT`).
- These paths were copied from C4, where `test_w501_cold_scenarios_postgres.py::test_list_malformed_stored_basis_is_503` and `::test_list_malformed_root_window_is_503` cover them. E5 has no equivalent test, so the 503 rather than a partial 200 is unproven for EV.
- Fix: port the two C4 malformed-row tests, inserting through the replica role the way `test_schema_constraints` already does.

### L2 (Low, test strength). The default page size of 50 is never exercised.
- `backend/assetops_backend/ev_scenarios/service.py:246`; tests at `test_w503_ev_scenarios_postgres.py:594-614` use only `limit=1` and `limit=100` over 3 rows.
- The spec says "default 50/max 100". C4 proved the default with a 51-row page. A default-size regression would pass.
- Fix: one 51-root case without `limit`, asserting 50 items plus a `next_cursor`, then 1 item.

### L3 (Low, test strength). The write-race retry and the second-race 503 are untested.
- `backend/assetops_backend/ev_scenarios/service.py:179-191`, `store.py:266-282`.
- The P-E5-6 mapping (one retry, then `DECISION_STORE_UNAVAILABLE`) is reached only by reading the code. C4 has no race test either, so this is parity rather than a regression. Fix this optionally: patch `insert_scenario` to raise `IntegrityError` once and then twice.

### L4 (Low, defensive correctness). Meter evidence is checked against `accepted_on` but not intersected with the selected head's cited set.
- `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:3100,3114`, with `selected_provenance_on` at `:3054-3063`.
- `authored_basis.accepted_evidence_ids` takes `meter_ids` as-is. `authored_basis.source_provenance` is computed after intersecting with `sel["evidence_ids"]`. If a cited meter ID were accepted but not in the selected head's evidence set, the stored list and the provenance block would silently disagree. They do not disagree in the fixture: the test asserts `provenance.evidence_ids == meters`. The spec phrase "empty/foreign" does not say which set "foreign" is relative to.
- Fix, if the Architect wants "foreign" to include "outside the selected head": add `e not in {selected evidence_ids}` to `foreign_meter_evidence` and add a test. Otherwise no change.

## Unit-by-unit conformance (verified against the spec text)

- **Migration** `backend/migrations/versions/0034_w5_ev_scenarios.py`:
  - `revision="0034_w5_ev_scenarios"` and `down_revision="0033_w5_cold_work"` exactly.
  - The sequence is created first, then `ev_scenario`, then `ev_scenario_revision`.
  - Every column, nullability and default matches the E5 schema paragraph. All four root constraint names, the three root checks, the nine named revision checks, both composite scoped FKs and the four revision UKs match by name and columns.
  - It also adds the two JSON-object checks (`..._assumptions_check`, `..._authored_basis_check`), which the "SQL checks require assumptions/basis to be JSON objects" sentence requires.
  - The index is `ev_scenario_site_order(tenant_id,site_id,recorded_at DESC,id)`, literal to the spec.
  - It adds the two `_immutable` append-only triggers and the C4 lock-and-refuse downgrade. Downgrade order: triggers, index, revision, root, sequence. The structure is byte-for-byte C4 apart from the names.
  - The test catalog pins it all (`test_schema_constraints`), including a refused nonempty downgrade, an empty downgrade to 0033 and re-upgrade.
- **Head pins (P-E5-1):** exactly the 18 named files changed, and each changes only current-head assertions. The `test_w501` parent assertion now names `0033_w5_cold_work` literally, which preserves its intent. The remaining `0033_w5_cold_work` mentions in `backend/tests` are parent or refusal-message literals, not head pins.
- **Rules:** closed root and correction bodies, the `GROSS_TARIFF_CONTEXT` kind, the `{tariff_per_kwh,currency}` assumptions with the C4 decimal and ISO grammar imported (not copied), and the C4 P-C4-22 create and correction hash inputs. `ESCN-` plus six digits.
- **Store:** the sole writer; INSERT-only on the two tables. Writes are REPEATABLE READ, the list is REPEATABLE READ READ ONLY, and `clock_timestamp()` supplies the defaults. Every query is scoped by tenant and Site (`_CANDIDATES`, the `latest_no` subquery, `lock_scenario`, `scenario_revisions`, `scenario_by_create_key`). It imports no analytics or financials module.
- **Service:**
  - Order: admit, then authorize, then the closed body, then one write transaction. Replay is answered from the stored hash and prior cutoff before any basis is resolved.
  - P-E5-5 allows only a CURRENT selection with an assessment, complete sessions, meter evidence and a Foundation.
  - The correction window must equal revision 1 before append. Stale prior returns 409. The list follows the spec's HISTORICAL rule (superseded, or `scenario_at` before the latest stored revision, or `known_at` before the watermark).
  - The cursor binds tenant, Site, route, window, `known_at` and whether it was explicit, the watermark, `scenario_at`, limit, the selection digest and the last `(recorded_at,id)`.
- **Read methods for W5-04:** `EvReadService.scenario_basis_on(c,t,s,code,lo,hi,known_at)`, `EvReadService.selected_provenance_on(c,snap,ids)` and `EvSiteReads.scenario_money_on(c,snap,cutoff=None)`. All are public, take the caller's connection and are read-only. `selected_provenance_on` lowercases both sets before intersecting, then calls `cited_set`. That matches P-E5-3/4 and W5-04 pre-flight ruling 14.
- **API:**
  - Paths `/api/sites/{code}/ev/financials/scenarios`, `POST` on the same path, and `POST .../{scenario_id}/revisions`.
  - Uses the unchanged `ev_gate`. POST needs both `from,to`. Command access 401 and 403 map to `UNAUTHENTICATED` and `DECISION_WRITE_FORBIDDEN`. The principal is resolved before the body is read.
  - None of the A1Q W5S-9 HTTP-scan tokens is present (grep returned nothing).
- **`main.py`:**
  - The mount sits directly after the E1b `build_ev_depth_router` mount, with imports and the decision injections exactly as in the spec snippet.
  - It passes `ev_site_reads` as the third service argument. P-E5-2 requires that, although the older snippet omits it.
  - `ev_site_reads` and `ev_reads` share the same `database_url()` condition.
- **Rule-8 guards and probes:** every E5 block sits directly after its C4 peer: declaration, writer list, both resets, forbidden DML, INSERT-only, unseen, probe names, doc, constant, probes and controls. The substitution table is applied. `$pgReaders` is untouched. The two displaced C4 closing braces are restored in `0042653f`; the C4 blocks read intact, and `check-architecture.ps1` passes on this head.

## The 10 judgment calls

| # | Call | Does the spec decide it? | Reviewer view |
| --- | --- | --- | --- |
| 1 | Money uses the current head (`cutoff=None`) | **Not clearly.** P-E5-2 lists "as-of head recorded by cutoff" among the reused `_select`/`_select_as_of` policies but does not say which branch E5 passes. | Architect item A1. I support the builder. Only a CURRENT selection can be authored, and CURRENT means `known_at` equals the committed watermark, so the current head *is* the head as of the selected cutoff. `_select_as_of` filters `recorded_at` (DB wall time) by an evidence-clock instant, which the spec says is an independent clock. The E1b depth and W2-07 overview also use the default `_select(ctx)` even with an explicit `known_at` (`ev_site_reads.py:308-312`), so the persisted IDs equal what the overview shows. |
| 2 | Limit refusal reuses `EV_LIMIT_INVALID` | **No.** The E5 refusal table lists no limit code. C4 minted `COLD_LIMIT_INVALID`, and `EV_LIMIT_INVALID` already exists in `ev_assessment_api.py:139`. | Architect item A2. Reuse looks right ("existing EV ... codes remain"), but the table is presented as closed. |
| 3 | Correction codes: unknown or invalid root gives 404 `DECISION_NOT_FOUND`; predecessor not in root gives 422 `DECISION_LINK_SCOPE_INVALID` | **No.** Neither code is in the E5 table. They are C4's codes (`cold_scenarios/service.py:107,115,129`). | Architect item A3. The other choice for a foreign predecessor is 422 `EV_SCENARIO_INVALID` ("foreign ID"). Both are tested. |
| 4 | Index `(…,recorded_at DESC,id)` rather than C4's `id DESC` | **Yes, literally.** The builder conformed. | Not a finding. Architect FYI A4: the list orders `id DESC` (`store.py:102`, C4 parity), so the index direction differs from the query order. Inside the `DISTINCT ON` subquery that has no functional or measurable effect. |
| 5 | No service gives `EV_READ_UNAVAILABLE`; store failure gives `DECISION_STORE_UNAVAILABLE` | **Yes.** The table allows either 503 code. | Conforms; tested. |
| 6 | Foundation outside the selected head's `foundation_ids` counts as foreign and gives 422 | **Partly.** The table says absent or foreign gives 422, but does not define "foreign". | The reading is coherent. With one cited ID, `foundation_revision_on` returns that ID. With none, nothing can be foreign. With more than one, the fallback is checked for membership. **Untested (M1).** |
| 7 | `selection.accepted_evidence_ids` is the union of session and meter evidence; `authored_basis` holds meter evidence only; meter evidence outside `accepted_on` gives 422 | **Yes**, P-E5-3/4. | Conforms. The foreign branch is untested (M1). See L4 on which set "foreign" is relative to. |
| 8 | Pending and historical test: the `complete` chain plus a test-local `late_import` with ACCEPTED `decided_at` 09:05 | **Yes, within P-E5-7's limits.** No scenario row is seeded and `energy_complete` is not bypassed. | Acceptable. `late_import` (`test_w503_ev_scenarios_postgres.py:352`) is a line-for-line clone of the merged and reviewed `ev_depth_cases.add_import` (W5-03a fix ruling 2). Its only change is `decided_at`, and it does not alter value, quality or unit. The test asserts that the watermark moved and the state became `PENDING_RECOMPUTE`, so the fixture is not vacuous. The 09:05 is a fixture value, not a source literal (P-34-2 holds). Cleaner later: parameterize `add_import` with `decided_at` rather than cloning it, which is a preference. |
| 9 | Write path: `store.reading` wraps the selection; one retry, then 503 | **Yes**, P-E5-6 and C4. | Conforms (untested race, L3). |
| 10 | No `total_pages`; imports `_instant` and `_Refused` from `ev_assessment_api` | **Yes** for the DTO: the literal `ev-scenarios-1` has no `total_pages`. The import is not decided. | Conforms. Importing private names across modules is a preference only, so it is not a finding. |

## Items for the Architect

- **A1.** Confirm judgment call 1: the money IDs come from the current head (`scenario_money_on(c, snap)` with no cutoff). The reasoning is in the table above. The alternative is a one-argument change in `service._basis`, and it would give null IDs in the E1 fixture.
- **A2.** Confirm that `EV_LIMIT_INVALID` (422) is the E5 list limit refusal, and add it to the E5 refusal table. The alternative is to mint `EV_SCENARIO_LIMIT_INVALID`, the C4 analogue.
- **A3.** Confirm the correction codes: 404 `DECISION_NOT_FOUND` for an unknown, malformed or foreign root, and 422 `DECISION_LINK_SCOPE_INVALID` for a predecessor outside the root. The alternative is `EV_SCENARIO_INVALID`. Add the chosen codes to the E5 table.
- **A4.** FYI: the index `id` (spec-literal) differs from the query and C4's `id DESC`. Keep it, or amend the spec to `id DESC` for parity. There is no functional impact either way.
- **A5.** Not listed by the builder: "currency conversion ... refused as `EV_SCENARIO_INVALID`" has no trigger in the code. An authored `currency` that differs from the selected tariff revision's currency (for example `USD` against a KES priced consequence) is stored without refusal. C4's P-C4 ruling made the sentence trigger-free because the cold Site currency is undeclared, but E5 does have a selected tariff currency. Decide whether a mismatch with a non-null `tariff_revision_id` refuses or is allowed as an authored what-if.
- **A6.** L4: should "foreign" meter evidence also mean "outside the selected head's `evidence_ids`", not only "outside `accepted_on`"?

## Checks I ran (actual output)

- `tools/check-architecture.ps1` gave "Architecture check passed." `tools/check-agent-workflow.ps1` gave "Agent workflow check passed." Both ran on head `50b43246`.
- `tests/test_w503_ev_scenarios_postgres.py -q -n 2` on a private `assetops_w503e5rev_test` gave **9 passed in 235.5 s**.
- Adjacent: `tests/test_w503_ev_depth_postgres.py tests/test_w207_ev_site_reads_postgres.py -n 2 --dist loadfile` gave **33 passed in 923 s** (the machine was contended). The private DB has been dropped.
- Not run, on the coordinator's instruction: the full backend suite (the coordinator is running it on this branch) and `tools/writer_guard_probes.py`, which mutates files in the working tree. I did not reverify the builder's probe result of 11 CAUGHT and 2 ALLOWED. The probe corpus reads correctly as C4 with the substitutions, and the non-vacuity rests on the builder's run.
- No frontend file changed, so there is no frontend or layout evidence to check.

## Residual risks the packet does not name

- **The review5 venv imports the wrong checkout.** `pip list --editable` in `AssetOpsV1-review5\.venv` shows `assetops-backend`, `-contracts`, `-gateway` and `-simulator` all installed editable from `C:\Users\assef\Bineyame\AssetOpsV1\…`, the main checkout, not review5.
  - Run without a `PYTHONPATH` override, the E5 file fails at collection (`ImportError: V4_EV_MAPPING_PROFILE_ID` from the main checkout's contracts).
  - With only contracts and simulator overridden, the Lab-run producer subprocesses ran the main checkout's backend and gateway and failed (`LabProjection status FAILED`).
  - It passed only with `PYTHONPATH=<review5>\backend;contracts;simulator;gateway;host`.
  - Any suite run in review5, the coordinator's included, must set that path. Otherwise it is either a collection failure or, worse, a partial run of main-checkout code.
- The handoff's focused run had 1 failure, a known timing bound in `test_s405` that passed when rerun alone. That leaves the full suite as the coordinator's same-revision proof, which the handoff already lists as still needed.
