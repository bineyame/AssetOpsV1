# S2-01a review packet: registered Kobo Lab basis

**Task:** `tasks/S2-01a-registered-lab-basis.md`.
**Branch:** `task/S2-01a-registered-lab-basis`.
**USER_REVIEW_REQUIRED:** false. An independent review is required before S2-01b.

**Controlling decisions:**
- `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary`, with its phase-1 amendment (commit `684aa91`);
- `D-2026-10-08-s1-bindings-roles-and-snapshot`;
- `D-2026-10-07-s2-edge-split-and-demo-source`.

The Architect answers are in `.agent/architect-S2-answers-2026-10-08.md` and `.agent/architect-S2-01a-answers-2.md`.

**Commits:**

| Phase | Commit | What it holds |
|---|---|---|
| 1 | `ce65b8d` | Selection and freeze |
| 1 | `fabbfc2` | Tests, and the typed refusal for an invalid Site row |
| 1 | `f1b78bd` | The run read reports the basis |
| 1 | `ad0b210` | Site-type / role-set guard (from the amendment) |
| 2 | `8d0e1d3` | Execution and Commit guards, Stage basis, name frozen at setup, rule 8, host tests |
| 2 | `7c2b271` | Lab frontend |
| 2 | `d0042fb` | Layout-evidence mode and questions Q4-Q5 |
| 2 | closeout commit | This packet and the context records |

## Outcome delivered

An imported KOBO-001 Draft is set up only from one selected, registered Postgres Foundation and binding snapshot. Selection is at the run's source start, as known at `knowledge_at`.

The Draft freezes:
- the exact revisions;
- the snapshot schema, hash and bytes;
- both selecting instants;
- the binding-derived component links.

It survives a restart and verifies its bytes against its hash on every reload.

The Draft runs (start, step, run-to-end) through the unchanged kernel. Its readings are identical to a legacy Draft of the same scenario. Commit refuses every imported run on the server, and the UI disables Commit. The Lab shows the basis and labels the Site name and time zone as current-row metadata frozen at setup. Pre-import YAML Drafts stay read-only and labelled `LEGACY_FILE`.

## Files materially changed

**Backend**
- `sites/registered_basis.py`: new; selection.
- `sites/binding_service.py`: the CURRENT/HISTORICAL classification, `pinned_identity_problems`, and `acquisition_snapshot(now=)`.
- `foundation_api.py`: the selection header and fields.
- `runs/registered_basis.py`: new adapter; `site_display_name` was added in phase 2.
- `runs/models.py`: `RegisteredBasis`.
- `runs/parsing.py`: strict render/parse.
- `runs/service.py`, `runs/ports.py`, `runs/refusals.py`.
- `simulator_lab_api.py`:
  - `configuration_basis_payload`, which adds `site_metadata`;
  - `_refuse_if_imported(record, *, commit=False)`;
  - `REFUSAL_REGISTERED_COMMIT_UNAVAILABLE`;
  - the `_frozen_basis` REGISTERED branch.
- `main.py`: wiring.

**Guard**
- `tools/checks/configuration-persistence.ps1`: rule 8 is amended, not loosened.

**Host test**
- `host/tests/test_registered_kobo_execution.py`: new.

**Frontend**
- `shell/runSetupClient.ts`:
  - the `RunConfigurationBasis` type, guard and `configuration_basis`;
  - `reasonCode`;
  - the Stage `frozenBasis`, where absent means not reported and null means unreadable.
- `shell/RunSetupFrame.tsx`: store labels on picker rows, the registered-basis read at the start, and the refusal reason.
- `shell/RunFrame.tsx`: `ConfigurationBasisPanel`, the Stage basis line, and the refusal code fallback.
- `shell/RunCommitPanel.tsx`: `commitBasisBlock`.
- `shell/simulatorLabRoutes.tsx`, `App.tsx`: wiring.
- `sites/siteReadModel.ts`: optional `configuration_store`.

**Tests**
- `backend/tests/test_s2_registered_basis.py`: 31 tests.
- `test_s2_registered_basis_postgres.py`: 5 tests.
- `test_run_setup.py` and `test_s1_cutover.py`: adjusted.
- Frontend: `runSetup.test.tsx` (+4), `runCommitPanel.test.tsx` (+5) and `runSetupClient.test.ts` (+5).

**Tool**
- `tools/layout-evidence.mjs`: `ASSETOPS_LAYOUT_S2_01A_RUN` mode.

## Acceptance criteria

1. **Registered selection: met.**
   - The Lab picker lists KOBO-001 labelled "Registered configuration".
   - For the entered start, setup reads `GET /api/sites/{id}/foundation?at=` and shows:
     - the Foundation revision and version;
     - the binding version;
     - the snapshot hash and schema.
   - Setup sends the Foundation version that the start selects, not today's. When no complete snapshot applies, Create is blocked with its code.
   - The server selects again and verifies the hash and schema. It validates the original valid periods, including `end_time`. It refuses with `REGISTERED_BASIS_UNAVAILABLE` or `REGISTERED_BASIS_BOUNDARY` plus a `reason_code`, and allocates no Draft.
   - Tests: `TestRegisteredSelection`, `TestBoundary`, `TestOverHttp`, and the frontend "a registered Site (S2-01a)" tests.
2. **Kernel input: met, with Q4 and Q5 noted.**
   - Links are frozen only from binding rows. There are ten, including `generator-controller/status`, and the legacy-only capability pairs are absent.
   - The host resolves each link exactly as frozen.
   - Registered and legacy daytime runs give identical projections, apart from run identity and the inputs digest.
   - Public signals, observations and recent reports contain no cause, oracle, intent or private keys.
   - The Site-type / role-set mismatch is refused (`SITE_TYPE_ROLE_SET_MISMATCH`).
   - Name and time zone are labelled `CURRENT_SITE_ROW_AT_SETUP`, both on the run read and on screen.
   - Tests: `host/tests/test_registered_kobo_execution.py`, and `test_site_name_and_time_zone_are_labelled_current_row_metadata`.
3. **Frozen run: met.** These are persisted on the record and verified on reload:
   - revision IDs and versions;
   - the snapshot schema, hash and bytes;
   - `source_start` and `knowledge_at`.

   A reload after restart (a fresh `YamlRunStore`) returns the same basis on the run read and the Stage read. A later publication leaves the old Draft unchanged. Default knowledge selects the correction; an earlier `knowledge_at` recovers the original. Tests: `TestFrozenAcrossPublication`, `test_stage_is_labelled_registered_with_no_evidence_claim_after_reload`, and the reload-tamper test.
4. **Controls and history: met.**
   - Start, step and run-to-end reach the port for a registered Draft (test, plus a live run on the branch host: 200, 200).
   - A pre-import YAML Draft of an imported code still refuses `SITE_AWAITING_MIGRATION`, with its Stage readable and labelled `LEGACY_FILE` (`TestLabRefusesImportedSites`).
   - The Stage for a registered run is labelled `REGISTERED`, with `can_release: false` and `accepted_evidence: false`.
   - A server Commit on a registered run returns 409 `REGISTERED_COMMIT_UNAVAILABLE` before the port or the commit store is touched. This held live for a COMPLETED, STAGED run.
   - The UI Commit is disabled with the reason for a registered run, a legacy Draft of a since-registered Site, and an unreadable basis.
5. **Failure integrity: met (phase 1).**
   - An outage, unsupported schema, missing bytes or digest mismatch fails closed, with no Draft created.
   - A historical basis survives a current registration edit, while a current basis still refuses on a current gap.
   - There is no YAML substitute.
   - Tests: `TestFailureIntegrity`, `TestHistoricalAvailability`, and the Postgres file.

## Reviewer path, as run here

1. Phase 1, in-memory and real Postgres: import and convert KOBO-001, select, freeze and reload, publish a later reserve, compare the two Drafts, then historical knowledge, the boundary refusals and the gap or hash failures. These are the tests above.
2. Live on the branch build (host `lab_app` on :8091 over the dev DB, vite on :5291):
   - setup `POST` with KOBO-001 v10 for 2026-10-09: 201, REGISTERED, snapshot hash `36b9d5e5…b16d`;
   - start: 200; run-to-end: 200;
   - Stage: `REGISTERED`, `can_release` false, STAGED, COMPLETED;
   - `POST /commit`: 409 `REGISTERED_COMMIT_UNAVAILABLE`.
3. Not repeated live: the publish-then-second-Draft comparison and the KOBO-GAP-001 case. They are covered by the in-memory and Postgres tests.

## Checks run (actual)

**Suites**

| Check | Result |
|---|---|
| Backend, `pytest backend/tests` with `ASSETOPS_TEST_DATABASE_URL=…/assetops_test` | 1614 passed, 0 skipped |
| Host, `pytest host/tests` | 624 passed |
| Simulator, `pytest` | 244 passed |
| Frontend vitest | 1196 passed (49 files) |
| `npm run build` | ok |
| `tsc --noEmit` | clean |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |

**Non-vacuity proofs.** Each check below was broken on purpose, failed as expected, and was then restored with `git checkout`.

| Change made | What failed |
|---|---|
| Commit route calls the boundary without `commit=True` | Rule 8 fails, and the Commit test fails |
| Registered Commit refusal disabled | The rule 8 boundary regex fails |
| Registered pass-through removed | The start/step test fails |
| `commitBasisBlock` forced to return null | 2 frontend tests fail |
| Setup sends the current version instead of the selected one | The setup test fails |

Phase 1 proofs: boundary `<`, every snapshot forced to current, reload hash check disabled, and identity check skipped.

**Layout evidence**
- The new S2-01a mode was measured on a registered run at 1280x800 and 640x700, and all claims hold:
  - there is no horizontal scroll;
  - the basis is drawn as REGISTERED;
  - a 64-hex-character hash is drawn inside the viewport, so the measured set is not empty;
  - the metadata label is drawn;
  - the Stage is REGISTERED;
  - Commit is disabled with the basis block.
- The full `layout-evidence.mjs` run reported 132 PASS and 0 FAIL, then stopped. After the run-setup sections it reported "CDP Runtime.evaluate got no reply within 60000ms" (the browser stopped answering). The later run, cockpit and site sections were **not measured** in that run. The local store holds about 270 runs, which may be the cause; this is not diagnosed.

## Known deviations

- The run page's Site name is frozen on `RegisteredBasis.site_display_name`, not on `FrozenSiteBinding`. Legacy runs still freeze no name, as before.
- The setup preview reads the configuration effective at the start with server-now knowledge. `knowledge_at` stays API-only, as specified. The interval-end boundary is checked only at setup, and its refusal shows the reason code.

## Residual risk and carries

- **Q4** (`.agent/S2-01a-questions-2.md`): the KOBO-001 bindings bind 10 of the 12 legacy links. The two capability signals are unconfigured for a registered Draft.
- **Q5**: the imported Foundation lacks generator parameters, so mini-grid models are BLOCKED for a registered Draft. Generator status is therefore proven at link resolution, not as a staged report.
- Backlog, from the Architect's Q1 and Q3: Site metadata is current-row and not historically versioned. Asset-code identity is mutable before S2-02 accepts evidence.
- No gateway authentication, outbox, Evidence or receipt was built; those belong to S2-01b and S2-02.

## User-review focus

None is required (`USER_REVIEW_REQUIRED: false`). For the independent reviewer:
- the boundary in `simulator_lab_api.py::_refuse_if_imported`;
- the rule-8 regexes;
- `RunSetupFrame`'s use of the registered version;
- the Q4 and Q5 defaults.
