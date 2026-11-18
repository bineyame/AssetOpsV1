# T025g review packet - The run is the only join of scenario and site (S1)

Task: `tasks/T025g-run-binds-scenario-to-site.md` (`USER_REVIEW_REQUIRED: true`).
Branch `task/T025g-run-binds-scenario-to-site` from `2297b25`. Implementer:
Claude, two phases (phase 1 handoff `.agent/T025g-phase-1-handoff.md`).
Rule: `D-2026-10-01-run-binds-scenario-to-site`. Contract stays at 9 (owner
signed off 2026-10-01). First review: discovery review by a fresh Claude
reviewer, which also confirms the no-move contract reading; Codex reviews
retrospectively after its reset.

## Outcome delivered

- No shipped scenario names a site. All seven `config/scenarios` documents are
  `scenario_version: 2` (`supersedes: 1`, valid from 2026-10-01), with the old
  requirement prose moved unchanged into `site_contract.description`.
- Run setup opens with no site selected and never selects one. Create stays
  disabled until the user picks a site. Each picker row shows the Foundation
  version and the template lineage, with T025f's staleness note.
- In process and live, against an isolated `var/`, shipped prolonged v2 with
  mini-grid v2 behaves as follows:
  - **READY** on a site built from the current Kobo template (GONDAR-01);
  - **BLOCKED** on the pre-T025a Kobo content (KOBO-001), naming the four
    missing generator properties;
  - a v1 request is refused with `VERSION_UNAVAILABLE`.
- Scenario detail resolves no site.
  - It shows what the scenario needs of a site: the addresses it names, the
    devices it reads through, the `site_contract` and a Site Controls
    statement.
  - It labels a legacy `target_site` "Legacy site declaration; not used to
    bind runs".
  - `Open target Site` is gone.
- Run detail and the Lab run header show the frozen template lineage, or
  "Not recorded" for an older run.

## Commits

- Phase 1:
  - `d0b9bd9` parser: `target_site` optional (legacy), `site_contract`;
  - `4b371bd` run setup binds the chosen site, lineage frozen;
  - `86f5bc9` handoff.
- Phase 2:
  - `2ceb88b` AC7 and AC8: the detail resolves no site, run setup has a picker
    (payload and clients together);
  - `c7892cc` AC9: run readback lineage (payload and client together);
  - `0c1625d` AC5 and AC6b: shipped v2, scenario fingerprints and guard,
    join proof, fixtures;
  - closeout commit: packet, `CODE_STATE`, `ACTIVE_CONTEXT`, `START_HERE`,
    task status.

## Files materially changed (phase 2)

- `backend/assetops_backend/scenarios/service.py`
  - `ScenarioDetailService(repository)` has no Site port.
  - `scenario_site_needs()` derives the needs from the document.
  - The resolution code is removed.
- `scenarios/models.py`
  - The resolution state sets and dataclasses are gone.
  - Added `ScenarioAddressNeed` and `ScenarioSiteNeeds`.
  - The policy comment is rewritten as legacy.
- `simulator_lab_api.py`
  - The detail payload drops `target_resolution` and
    `observation_source_resolutions` and adds `scenario.site_needs`.
  - The summary gains a nullable `site_contract`.
  - `run_summary` gains `template_lineage` (top level and under
    `deterministic_identity.site`), with the states
    `RECORDED / NO_TEMPLATE / NOT_RECORDED`.
- `frontend/src/shell/scenarioCatalogClient.ts`: the new shape, a nullable
  `target_site` and `site_contract`, and `site_needs` validated.
- `ScenarioFrame.tsx`:
  - `SiteNeedsPanel` replaces the "Target site" panel and its
    `TargetSiteAction`;
  - Create Draft Run is always a link;
  - the `siteHref` prop is removed.
- `ScenariosFrame.tsx`: no site column.
- `RunSetupFrame.tsx`:
  - `SitePicker`/`SitePickerRow` read `siteDirectory.listSites`, plus one
    `getSite` per row for the Foundation version, plus T025f lineage;
  - the form waits for its derived defaults;
  - the setup summary shows the lineage.
- `runSetupClient.ts`: `RunTemplateLineage`, a strict validator and
  `templateLineageText`. `RunHeader.tsx` gains the "Site template lineage"
  fact.
- `simulatorLabRoutes.tsx` and `App.tsx`: pass `siteDirectory` and the gated
  lineage client to run setup.
- `test/settled.ts`: the picker's loading texts count as unsettled.
- `config/scenarios/*.yaml`: all seven are v2 with `site_contract`. Header
  comments no longer name KOBO-001 or MG-001 as the target.
- Tests:
  - new backend helper `backend/tests/content_fingerprint.py`, shared with
    T025f's guard;
  - new `backend/tests/test_scenario_fingerprints.py`;
  - new `host/tests/test_t025g_join.py`;
  - rewritten:
    - `test_scenarios_api.py` (no-site detail);
    - `test_run_binds_scenario_to_site.py` (AC8 guards, AC9 payload, AC10
      copy rebuilt from a frozen v1 sample);
    - the frontend `scenarioCatalog`, `runSetup` and `runSetupClient` tests
      and `scenarioFixtures.ts`;
  - fixtures moved off `target_site`: `host/tests/fixtures.py`,
    `second_site.py`, `backend/tests/addressed_fixtures.py`;
  - requests that named v1 now name v2 (`test_runs_api`,
    `test_execution_contract_alignment`, `test_model_owned_needs`,
    `test_scenario_repository`);
  - the 14 frontend run fixtures gain `template_lineage`.
- `tools/layout-evidence.mjs`: the run setup action picks a site.

## Acceptance criteria

1. **Parser (phase 1). Met.** `target_site` is optional and parsed only when
   present. A null or malformed one is refused. `site_contract` accepts
   `description` only.
2. **Run setup (phase 1). Met.** Only `_refuse_site_without_topology` remains.
   A legacy `target_site` is ignored (`TestRefusalsAllocateNoRun`).
3. **Lineage frozen (phase 1). Met.**
   - `FrozenSiteBinding.template_lineage`; an absent one reads back as not
     recorded.
   - It is not in `FrozenWorldInputs`, and the gate digests are unchanged.
4. **Contract stays at 9. Met.**
   - `contract9_gate`: 23 passed with no edit, run after the v2 documents
     landed and again in the full host suite.
   - `git status` is clean afterwards.
5. **Shipped v2. Met.**
   - Seven documents are v2, `supersedes: 1`, valid from
     2026-10-01T00:00:00Z.
   - `test_scenario_fingerprints.py`:
     - pins each `(scenario_id, 2)` through the shared `content_fingerprint`;
     - fails on `target_site`, `site_id` or `template_id` at the top level.
   - AC10's copy test is kept: it rebuilds the legacy block from
     `FROZEN_V1_SAMPLE`.
6. **Join proof. Met, with one deviation (see below).**
   - (a) Phase 1: met.
   - (b) `host/tests/test_t025g_join.py`:
     - READY on GONDAR-01 with the current template;
     - BLOCKED on the pre-T025a content, with exactly the four
       `INITIAL_VALUE_NOT_RESOLVED` generator addresses;
     - v1 is refused with `VERSION_UNAVAILABLE`.
   - The pre-T025a fixture is the current template minus exactly the
     `c0f49ce..0dc42c0` additions, and a test pins that difference.
7. **Picker. Met.**
   - Nothing is selected, even with one site.
   - Create is disabled with the reason "Choose the site this run binds to
     first".
   - Rows show "Foundation version N" and "Created from template: id vN",
     plus the staleness note.
   - No row is disabled. A row whose Foundation read failed is still
     selectable, and Create then stays disabled.
   - The submit sends the picked site. A legacy declaration does not
     preselect.
8. **Scenario detail. Met.**
   - Every symbol the task names is retired: `resolve_target_site`,
     `TARGET_RESOLUTION_STATES`, `resolve_observation_sources`,
     `OBSERVATION_SOURCE_RESOLUTION_STATES`, the `SiteRepository` dependency
     and both payloads.
   - The needs come from the document, with no compatibility list.
   - The legacy label is shown.
   - An AST guard allows the scenario package only `validate_site_id` and
     `SiteConfigurationInvalid` from `assetops_backend.sites`.
9. **Run readback. Met.**
   - The `RunHeader` fact `[data-header-template-lineage]` shows
     `kobo-mini-grid-60kw v2`, "Not created from a template" or "Not
     recorded".
   - The setup summary shows the same.
   - The identity classification moves the three lineage fields to
     `rendered`, backed by payload tests.
10. **Catalog alive. Met.**
    - Owner-shaped copies of all seven parse, and the composite catalog lists
      them.
    - Live check: a v1 legacy copy in the isolated store is listed and
      labelled.

## Checks run (serially, after the last code commit)

- `host` pytest: **528 passed** (includes `contract9_gate` 23 and the 6 new
  join tests).
- `backend` pytest: **1374 passed**.
- `simulator` pytest: **227 passed**.
- `frontend` vitest: **1021 passed** (39 files).
- `tsc --noEmit`: clean. `npm run build`: built.
- `check-architecture.ps1`: passed. `check-agent-workflow.ps1`: passed.
- **Live check after each payload commit.**
  - Setup: `host/lab_app` served by uvicorn on port 8765, with
    `RUN_STORE_ROOT`, `USER_SCENARIO_STORE_ROOT` and `USER_SITE_STORE_ROOT`
    patched to a scratch directory, and Vite on 5199 with
    `ASSETOPS_API_PORT=8765`.
  - Pages were rendered in headless Chrome. The catalog, detail, run setup and
    run detail loaded after `2ceb88b`, `c7892cc` and `0c1625d`.
  - The sites in the scratch store were created through the API from the
    shipped templates. KOBO-001 was then edited to the pre-T025a content.
  - The owner's `var/` was never read.
- **Mutation proofs.** Each mutation was applied to a committed file and
  reverted with `git checkout`, and the tree was clean afterwards. Each one
  failed its guard:
  - M1: a shipped `target_site` was added;
  - M2: an in-place edit at v2;
  - M3: a `SiteRepository` import in `scenarios/service.py`;
  - M4: `target_resolution` back on the detail payload;
  - M5: an absent lineage served as `NO_TEMPLATE`;
  - M6: the picker auto-selects a lone site;
  - M7: the picker follows a legacy `target_site`;
  - M8: the run client accepts any lineage;
  - M9: `Open target site` restored.
  - M9's first scripted run "survived" only because its `-t` filter matched
    no test. Rerun with a matching filter, 3 tests failed.
- **Layout evidence.** Isolated stack, with KOBO-001, GONDAR-01 and MG-001 in
  the scratch store.
  - A focused CDP measurement covered the picker and the scenario detail at
    1280, 1000, 640 and 375 px:
    - all passed at 1280, 1000 and 640: no page scroll, 3 picker rows (a
      non-empty set), all visible, unselected and enabled;
    - each row carries a Foundation version and its lineage, and KOBO-001
      carries the note "Created from v1; current template is v2";
    - Create toggles on pick;
    - on the detail screen, 6 of 8 tables overflow at 640 and every
      overflowing table scrolls in a named region;
    - the legacy label shows on the copy only.
  - At 375 px both screens scroll the page by 47 px (422 vs 375). The cause
    is the shared `FactList` terms and values and the long `PageHeader` h1,
    not the picker rows, which all sit inside the viewport. 375 px is below
    the measured set (1280, 1000, 640). Not fixed: it is a shared-primitive
    behaviour.
  - `node tools/layout-evidence.mjs http://localhost:5199 GONDAR-01` against
    the same stack:
    - Sites, Foundation, scenario detail (all three widths) and catalog
      passed.
    - In the run setup summary, all checks passed except "blocked table is
      at least two rows". That is data-dependent: the fuel-loss draft is not
      blocked on GONDAR-01.
    - The tool then aborts at its MG-006 user-scenario section, which exists
      only in the owner's `var/`. **The rest of the tool was not run.** Its
      later claims (run detail, cockpit) are unverified for this slice.

## Known deviations

- **AC6b status source.** The pre-T025a Draft blocks on the four generator
  properties only.
  - The missing status source is not a blocking reason in this build. The
    `status` reading is a publication-profile declaration that publishes
    nothing where the site maps no such signal.
  - Making it block would turn READY Drafts BLOCKED, which the no-move
    contract reading does not cover.
  - What the run does record is the absence: no `generator-status` mapping is
    frozen, which `test_the_missing_status_source_is_recorded_not_blocking`
    asserts.
- **AC8 Site Controls.** A scenario declares no Site Control; control needs
  are the model profile's. The detail screen says so instead of listing any.
- **AC7 Foundation version** is read with one `GET /api/sites/{id}` per listed
  site. The operator `/api/sites` summary was left unchanged rather than
  widened.
- **Phase 1, Lab API null-handling.** Phase 1 said no payload shape would
  change, but it made `scenario_public_summary` render `target_site: null`,
  and `resolve_target_site` answered NOT_APPLICABLE for a document without
  one. Neither was live then, because no document lacked the key. Both were
  replaced in `2ceb88b`.
- **Phase 1, renamed test case.** In `test_scenario_parsing.py`, the case
  `target_site=None` was renamed from `id="absent"` to `id="null"`. It now
  means present-but-null, which is still refused; absent is a separate,
  accepted case.
- `SCENARIO_DETAIL` in the frontend fixtures now represents a v2 document (no
  `target_site`). A separate `LEGACY_SCENARIO_DETAIL` covers the legacy label.

## Residual risk

- The shipped Kobo `site_contract.description` still says "created from the
  kobo-mini-grid-60kw template". This is prose, which the decision allows; it
  is never evaluated.
- The picker issues N+2 reads (list, lineage, one detail per site). This is
  fine for the handful of local sites and would need a summary field at scale.
- Superseded v1 scenario text survives only in git and in frozen runs
  (Architect section 3, carried to the backlog).
- The 375 px page scroll on scenario detail and run setup comes from shared
  primitives (see Layout evidence).

## User-review focus (`USER_REVIEW_REQUIRED: true`)

Hands-on, with the Lab enabled on the owner's own `var/`:
1. Open `kobo-mini-grid-prolonged` (v2) and check what the detail screen
   shows:
   - no site and no `Open target Site`;
   - the needs tables and the site contract.
2. Set up a run.
   - Check that no site is selected and Create is disabled.
   - Rows show the Foundation version and lineage. GONDAR-01 and KOBO-001
     both record v1, so both show "Created from v1; current template is v2".
     That is true of GONDAR-01's record, per the decision.
3. Pick **GONDAR-01**, choose `mini-grid` v2, 06:00-14:00 local and a 5-minute
   timestep. The result should be **READY**.
4. Pick **KOBO-001** with the same inputs. The result should be **BLOCKED**,
   naming `generator-rated-power`, `generator-start-delay`,
   `generator-start-soc-threshold` and `generator-stop-soc-threshold` at
   `@generator`.
5. The owner's untracked `var/scenarios` copies should still be listed and
   labelled "Legacy site declaration; not used to bind runs".
6. A run detail should show "Site template lineage". Runs created before this
   slice read "Not recorded".

## R1 (fix round after the first Claude review)

- **F1 fixed.** Option chosen: the backend serialises `site_contract` as null
  when the block has no description (`simulator_lab_api.py`, summary). Why: the
  parser keeps accepting `site_contract: {}`, the client check stays strict,
  and one such document can no longer blank the catalog. The detail screen
  already reads a null contract as "none".
- **Seam test.** `test_an_empty_site_contract_crosses_the_seam_as_no_contract`
  writes and compares `contract-fixtures/scenario-empty-site-contract.json`;
  `frontend/src/shell/__tests__/scenarioEmptyContractSeam.test.ts` runs
  `isScenarioSummary` on that file. Mutation-proved both ways (backend fix
  removed: backend test fails; fixture set to `{"description": null}`: frontend
  test fails); both reverted with `git checkout`.
- **F5 fixed** (`.agent/scenario-site-targeting-architect.md`).
- **Carried** to `.ai/MILESTONE_REVIEW_BACKLOG.md`: F2, F3, F4, F6 and the two
  residual risks. F2 awaits the owner or Planner on AC6b's wording.
