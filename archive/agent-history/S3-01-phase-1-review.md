# S3-01 phase 1 review - `I-sim-dispatch-cases` (1a + 1b)

Reviewer: a fresh Claude reviewer (independent of the Implementer), 2026-10-11.
Target: branch `task/S3-01-dispatch-assessment`, diff `b020bff..67b97d6`. Nothing was fixed, merged or committed by the reviewer.

## Verdict

**Accept with findings.** F1 and F2 are small and should be fixed on the branch before phase 2 starts. They do not block it. F3 to F6 are carries for phase 2/3 or for the Architect batch. I found no blocking correctness, contract or architecture violation.

Every phase-1 acceptance row in the task file is met, or is met with limits the packet names honestly:

- `minigrid-roles-2` vocabulary, with roles-1 still readable.
- A registered simulated binding and accepted report for both capability channels.
- A versioned manifest that keeps public IDs apart from the private oracle.
- Eight cases accepted through the gateway, sealed Batch V2 and central acceptance. The one exception is the labelled fixture, as Q1 says.
- Replay and verify in a fresh process.
- Candidate blocked before the channels exist and available after acceptance.
- No analytic cutover.

## Checks run by this reviewer

| Command | Result |
| --- | --- |
| `tools/check-architecture.ps1` | Architecture check passed |
| `tools/check-agent-workflow.ps1` | Agent workflow check passed |
| `tools/check-all.ps1` | All 6 guards passed (registry, ledger, navigation, delivery fixtures included) |
| `pytest backend/tests/test_s3_role_vocabulary.py test_s3_demo_configuration.py test_scenario_fingerprints.py test_run_binds_scenario_to_site.py` (no DB) | 58 passed, 1 skipped (Postgres test, URL unset) |
| same S3 two files with `ASSETOPS_TEST_DATABASE_URL=...:55432/assetops_test` | 10 passed (the Postgres demo-config test now runs) |
| `pytest host/tests/test_s3_registered_capability_publication.py` | 4 passed (real gateway process; roles-2 publishes both capabilities, roles-1 publishes none, the gap removes 4 readings) |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |

Not re-run, as the dispatch instructed:

- The full backend, host, simulator and gateway suites (1770/666/265/164).
- The end-to-end `tools/s3_dispatch_cases.py run`/`verify`.

I read those results from `.agent/S3-01-dispatch-cases-run.txt` and the committed manifest. I did not reproduce them.

`npm.cmd test` and `npm.cmd run build` were not run: the diff changes no frontend code, only the registry JSON, which the guard covers. The known esbuild sandbox denial would block them anyway, so the frontend suite and build are unverified by me.

Layout evidence does not apply because there is no UI change.

## Findings

### F1 - Low - fix on branch. The packet's contradiction values do not match the evidence

- **Where:** `.agent/S3-01-phase-1-review-packet.md:49` states the contradictory SOC values as "91.75 / 99.25".
- **What is wrong:** the committed manifest (`.agent/S3-01-dispatch-cases-v1.manifest.json`, case `contradiction-fault-fixture`, `precondition.values`) records `69.1875` / `76.6875`.
- **Why it matters:** the packet appears to quote an earlier run, and reviewers and phase 2 read the packet as a statement of the evidence.
- **Fix:** correct the row from the manifest. Also check the other packet numbers against the final run. I checked the rest of the case table and it matches.

### F2 - Low - fix on branch. `--steps bindings` alone is accepted, though the docstring says only the first step may be named alone

- **Where:** `backend/assetops_backend/sites/demo_configuration.py:319-320`. The check is only `set(steps) - set(STEPS)`.
- **What is wrong:** run `bindings` alone, then `properties`. The properties revision is then published only into the period that covers 2026-10-01, which the binding publication already split at 10-02. From 10-02 onward the generator values are missing, so `mini-grid` Drafts block.
- **Why it matters:** it fails closed, but it contradicts the module docstring ("`--steps` may name only the first") and gives an operator a surprising order dependency.
- **Fix:** refuse a step list that names `bindings` without `properties`, unless the properties are already in effect at `bindings_from`, and add a test.

### F3 - Medium - carry to phase 2. The "late" case is late by publication lag only, not at central acceptance

- **Where:** `tools/s3_dispatch_cases.py:317-334`. The manifest case is `late-out-of-order`.
- **What is wrong:** the 07:00 SOC is published 10 minutes late (`published_at` 07:10). The run, however, completes before delivery (`run_case`: run-to-end, then commit, then `deliver_all`). The late reading therefore reaches central in the same delivery, in source order (sequence 212, `same_source_later_readings_sequenced_before_it: 0`). No accepted record arrives after the rest of its window has been accepted.
- **Why it matters:** the case's expected ceiling reads "a new revision when it arrives after an assessment". Phase 2 must show that "a late accepted record yields a new revision and job", and this fixture cannot exercise that by itself. Out-of-order within a source is not produced either (Q5).
- **Fix (phase 2):** produce central lateness explicitly, for example by withholding the late reading's batch until after a first assessment, and record which accepted ID is the late one. Alternatively, have the Architect rule on Q5 to cover both.

  Separately, the scenario header comment says the held SOC "arrives after later readings" (`config/scenarios/kobo-s3-dispatch-degraded-reporting.yaml:9-10`). The Q5 probe shows that is false within its own source. Reword it when convenient.

### F4 - Medium - carry to phase 3 (and Q1 ruling). The fault-fixture label does not exist centrally

- **Where:** `tools/s3_dispatch_cases.py:372-421`.
- **What is wrong:** the contradiction batch is posted with the real gateway credential, gateway ID and battery `source_id`. The only marks that it is a fixture are the epoch string `s3-contradiction-fixture-epoch` and the manifest's `fault_fixture: true`. Central accepted evidence has no fault-fixture flag. It is isolated in its own window (10-06) and epoch, so nothing is blended today.
- **Why it matters:** the task says the fault fixture is "labelled and never blended". A phase-3 Evidence drill-down or UI would show these two readings as ordinary gateway evidence. Phase 2 must not read the manifest to recover the label, because the analytic sees only public evidence.
- **Is the Q1 default safe?** Yes for phase 1, because it follows the S2-02 step-8b precedent. Before phase 3, the Architect should decide how a reader sees that this epoch is a fixture.

### F5 - Low - carry. The precondition reserve lookup is unscoped and reads current knowledge, not the as-accepted revision

- **Where:** `tools/s3_dispatch_cases.py:162-182`.
- **What is wrong:** the query on `foundation_revision` has no tenant or site filter. It uses `superseded_at IS NULL`, which means today's selected revision and not the revision the evidence was accepted under. For the 10-01 case those are v5 and v4.
- **Why it matters:** it is safe in the isolated single-Site database, and the row-count guard fails closed, so this is a fixture precondition only. Still, phase 2 must not copy this pattern into `EvidenceQuery`, which has to use the as-accepted revision and the `knowledge_at` selection.
- **Fix:** filter by site and select by the evidence's `foundation_revision_id`. This is a preference for the fixture.

### F6 - Info - carry (risk acknowledged). Foundation-UI binding edits now record roles-2

- **Where:** `binding_roles.py:25` (`ROLE_SET_MINIGRID = ROLE_SET_MINIGRID_2`) and `binding_service.py:439-441`.
- **What changes:** any MINIGRID publication that does not name a role set, including a Foundation-UI edit of a period that is historically roles-1, is now recorded under roles-2.
- **Why I accept it:** the two new roles are optional, so readiness and required-role behaviour do not change. Readiness reads each selected set under its own recorded `role_set` (`binding_service.py:649`), and `registered_basis` serves both versions. The behaviour is tested in `test_s3_role_vocabulary.py`.
- **Residual risk:** a UI edit with no visible role-set change moves the set's version. Phase 3 or the UI should make the role set visible when it changes (`FoundationBindingsPanel.tsx` already shows `role_set`).

## Reviewer focus answers

1. **Fixture boundary.** `classify_public` checks dispatch-2 rows 3/4/5a/5b on accepted public GOOD values, using the same conditions as `backend/tests/dispatch_decision_table.md` (10-point SOC headroom, 1.1 capability headroom). It is not wired into any analytic path, and phase 2 must not import it as `dispatch-3`.
2. **Q1-Q6 defaults.** All six fail closed and none fabricates data, so none is unsafe for phase 1. Q1 and Q5 leave real gaps (F4, F3) that need an Architect ruling before the gates they affect: Q1 before phase 3, Q5 before phase 2's late-evidence acceptance.
3. **Private oracle separation.** `private_oracle` holds only the Lab store path and the Lab run IDs, under a statement that they are not public evidence. Per-case public fields come from `accepted_evidence` and `ingestion_batch` rows only.
4. **`registered-kobo-publication` v3.** It is built with `replace(...)` from v2. It adds generator status and both capability signals at `0.000001`, generator power at 15 min, and only the discharge-capability reporting state. `record_channels=()`. v1/v2 objects are untouched, and the host test asserts that v2 lacks the new signals.

## Residual risk not already in the packet

- The committed manifest's IDs exist only until the next `run` drops and recreates `assetops_s3cases`. A phase-2 test that depends on the committed copy goes stale silently, so phase 2 should regenerate or pin its own manifest. The packet names environment-specificity, but not the drop-on-run.
- `physical-necessary` and `two-capability-candidate` share one evidence set (10-02). Phase 2's interval and segment logic must produce both claims inside one interval, with bounded segments that do not overlap. The fixture shows Necessary instants from 03:45 to 05:00 and Candidate instants from 05:15 to 09:15.
