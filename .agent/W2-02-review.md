# W2-02 review - cold producer, Lab scenarios, gateway v4, Lab cold setup route, replay

Reviewer: fresh independent Claude reviewer (not the author). Revision reviewed: `8668396f` (code `7b0c9f79`).
Diff: `7ea8d042..8668396f -- ':!.agent'`, W2-02 non-merge commits from `d9cdcb97`.

## Verdict: RETURN

There are two Medium findings. Both are small fixes on the branch. Deviation 1 is still the separate known
blocker with the Architect, so after the fixes the verdict becomes **ACCEPT-pending-deviation-1**. Everything
else matches the spec, and I verified it as listed below.

## Findings

1. **Medium (acceptance gap): a mismatched or half-cold profile pair still creates a Draft.**
   Location: `backend/assetops_backend/runs/service.py:429-430`, the legacy branch of `create_draft_run`.
   The spec says: "Unknown profile, pack, observation version or mismatch refuses before Draft". The packet marks
   this "Met", but it is not:
   - `GET /run-profiles` now offers `cold-thermal/1` and `cold-publication/1` to the legacy setup form.
   - I ran a probe through `RunSetupService` (fixtures from `test_w202_cold_run_identity`). A legacy scenario with
     the cold pair returned a persisted `BLOCKED` Draft (STATE_NOT_SUPPORTED). So did `cold-thermal/1` with a
     legacy publication profile. Neither was refused.
   - Neither run can execute: the host's `execution_path` and `verify_cold_inputs` refuse it. The failure is
     safe, but it breaks the contract and leaves an orphan Draft.

   Fix: in the legacy branch, after resolving the profiles, refuse `VERSION_UNAVAILABLE` when either
   `model.model_profile_id == "cold-thermal"` or `publication.publication_profile_id == "cold-publication"`.
   Suggested copy: "Cold-chain profiles run only from a cold-scenario/1 document. Profiles are not substituted."
   Add a test to `test_w202_cold_run_identity.py` for both pairs, asserting `store.written == []`.

2. **Medium: the Cold run setup screen states its state more than once.**
   Location: `frontend/src/shell/ColdRunSetupFrame.tsx:286/289/308` (Cold scenarios panel), `:406` (the reason
   beside **Create draft run**) and `:344` (the Foundation version fact).
   - With no Site chosen, "Choose a site to see its cold scenarios." renders twice: in the panel and beside the
     button.
   - The empty and unavailable copies also render twice.
   - Once a choice is made, the basis-loading or basis-problem reason renders both in the "Foundation version"
     fact and beside the button.

   The coldRunSetup tests only read the `data-cold-choice-state` node, so they do not catch this. It breaks the
   owner's say-it-once rule this dispatch asked me to check.

   Fix:
   - Render the button-side reason only when the Cold scenarios panel does not already show it. Suppress it for
     the choose-site, empty and unavailable states, and keep the button disabled.
   - Make the Foundation version fact show the version, or "Not available yet", never `blockedReason`.
   - Add a test asserting each of the three copies appears exactly once (`getAllByText(...).length === 1`).

3. **Low: a raw ID in the choice label and a raw enum in refusals.**
   Location: `ColdRunSetupFrame.tsx:443` renders `Normal (cold-normal)`, and `:368` shows `Reason code: X`.
   The spec requires the scenario ID and profile identities as read-only facts on this developer surface. Those
   facts are acceptable, but the label does not need the ID repeated.
   Fix: label with `choice.display_name` only. Optionally drop the reason-code line, since the refusal message
   already says what is wrong.

4. **Low: the generator's STARTING to STOPPED move on grid restore skips the transition guard.**
   Location: `simulator/assetops_simulator/packs/cold.py:307`. The restore branch sets `generator="STOPPED"` from
   `STARTING` without calling `check_move`, and `_GENERATOR_MOVES` does not contain `("STARTING","STOPPED")`.
   Fix: add that move and call `check_move("generator", s.generator, "STOPPED")`.

5. **Low: the cold replay reader is wider than SELECT-only.**
   Location: `backend/assetops_backend/evidence/composition.py:41`. `build_cold_replay_reader` returns the whole
   `PostgresEvidenceLedger`, writer methods included. The service only calls `cold_replay_*`, and the static rule-8
   guard holds.
   Fix: return the object typed as the `ColdReplayReader` protocol, or a two-method facade.

6. **Low: a cold execution error escapes as an HTTP 500.**
   Location: `host/lab_execution.py:2295`. `_start_cold` does not catch a `PhysicallyUnacceptable` raised during
   the window, for example valid Foundation values that drive T outside [-40,60]. It surfaces as a 500, not as a
   refusal. The spec does not name a kind for this.
   Fix: map it to `LabControlRefused` before any Stage output, or record it as a deliberate deferral.

## Spec conformance checked
- **Pack physics and the five confirmed readings: correct.**
  - Law, minute order and exact Fraction updates are correct. The residual check runs every step and nothing is
    clamped.
  - Generator failure is latent, so the start fails at 19:05.
  - Restore puts the transfer on GRID immediately and emits TRANSFER_RESULT; the generator stops.
  - Compressor power equals capacity while RUNNING on a powered bus. The published value is the slot mean.
  - Grid, start and transfer events share the outage correlation; door events have their own.
  - Ambient is published every 5 minutes, including 20:00.
  - The manifests show normal 19:07/19:08, failure 19:05, excursion 4.1/4.2, 13/7/13 points and late
    19:20 to 20:10.
- **Observation transform and digest: correct.** Zero bias, half-even 0.1, +3 s latency. DROP, HOLD and ADD are
  as specified, with ADD carrying a distinct ordinal and the same correlation. `observation_sha256` is computed
  over `{observation_profile, observations}` only. The probe-failure UNAVAILABLE point is unit-tested
  (`test_cold_pack.py:128`).
- **Legacy run identity unchanged: verified by me.** In a temporary worktree at `d9cdcb97` and on this branch,
  the legacy `run_identity_sha256` is `0db30ea9...0bd5` and the rendered run document hashes the same. The cold
  keys are omitted, never null. The legacy fingerprint tests only exclude cold documents; no pin changed.
- **`cold-` IDs are valid V4 identifiers.** Event and correlation IDs are `cold-` plus 64 hex characters (69),
  which fits `_IDENTIFIER`. Report keys keep `cold:`, and `source_envelope_v4.py` is unchanged.
- **DeviceReport v2 and gateway admission: correct.** The v1 parser and serializer are untouched, and the v2
  report is strict with every key present. `_admit_in` dispatches by schema. The v2 checks run before
  duplicate lookup and allocation: validity, future time, exact five metadata keys against
  `V4_CHANNEL_MAPPINGS`, family, measurement, kind, unit, value, and a provisional V4 parse. The gateway allocates
  the sequence and message ID, and the V3 branch is extracted unchanged.
- **Host frozen-input check: refuses before any Stage output.** `_start_cold` verifies the revision ID and SHA,
  recomputes the content digest, and checks the scenario version and SHA and the observation SHA before
  executing or staging. A store error is `FROZEN_RUN_NOT_RECONSTRUCTIBLE`.
- **Delayed reports staged as specified.** Held reports become `DelayedReport` at 20:10 with `cold-delay-<sha>`.
  The schedule records world reached, complete and 61 boundaries.
- **Replay reader: SELECT-only, 403 in production.** It issues only SELECTs. Production mounts the route only
  under the Lab gate with `no_owner_principal`, so it answers 403. `test_owner_and_tenant_gate` checks the real
  `create_app`: 403 with the Lab on, 404 with it off.
- **The six proofs run the real path.** The chain is real `install_cold_lab`, then `RegisteredLabBasis`, a real
  Host Lab start, a real `assetops_gateway serve` process, the gateway's TLS upload to the S2 batch route, the
  Postgres ledger, and the replay and Site Evidence routes.
  - Only the UUIDs, epoch and clocks are fixed, all in test fixtures.
  - The manifests are compared byte for byte (canonical file text). Writing them needs
    `ASSETOPS_W202_WRITE_MANIFESTS=1`.
  - Any change to an envelope, batch, disposition or assertion fails the compare. The packet records a one-byte
    seed edit failing it, which I did not re-run.
- **Deviation 1, the known blocker, is narrowly scoped.** `open_cold_snapshot_gate` patches only
  `binding_service.configuration_gaps`, through the per-test `monkeypatch`, and only for `site_type ==
  "COLDCHAIN"`. Snapshot bytes, hash and pinned-identity checks still run.
- **Deviation 2 is acceptable.** The event conflict goes through the real gateway. The session vector goes
  through the ordinary S2 batch route under the real gateway credential, with the channel bound test-only. That
  is the W2-00 precedent, and the spec forbids inventing a session channel in the manifests. The real Site
  Evidence and rejection-list routes are asserted.
- **Deviation 3 is acceptable.** `simulation_records` uses the same `uses_v4_header_path`/`read_envelope_header`
  dispatch as `seal_batch_v2`, and the S4-05 publication tests are unchanged.
- **Known Deviations 4-9 are acceptable** as recorded readings.

## Checks I ran (serially, main venv python, PYTHONPATH as dispatched, private DB `assetops_w202rev3_test`, now dropped)
- **Backend W2-02 tests: 52 passed, 0 failed, 206 s.** Files: `test_w202_cold_lab_bindings_postgres`,
  `_replay_api`, `_replay_postgres` (12 real-chain proofs), `_run_identity`, `_scenario`, `_scenarios_api`.
- **Host cold tests: 19 passed.** Files: `test_cold_dispatch`, `test_cold_lab_execution`,
  `test_cold_publication`.
- **Gateway `test_cold_v4_admission`: 5 passed.**
- **Simulator `test_cold_pack`: 6 passed.**
- **Contracts `test_gateway_report_v2`: 6 passed.**
- **Adjacent legacy tests: 157 passed.** Files: `test_scenario_fingerprints`, `test_run_binds_scenario_to_site`,
  `test_run_setup`, `test_simulator_lab_gate`.
- **`tools/check-architecture.ps1`: passed.** **`tools/check-agent-workflow.ps1`: passed.**
- **Rule-8 break test: caught, then reverted.** I appended an `INSERT INTO accepted_evidence` (with a SQLAlchemy
  import) to `cold_replay.py`. check-architecture **failed** with "A second product database writer ...
  cold_replay.py:176" and "Database driver imported outside ...". I restored the file with `git checkout`, and
  check-architecture passed again.
- **Frontend: `npx.cmd tsc --noEmit` exit 0.** `npx.cmd vitest run src/shell/__tests__/coldRunSetup.test.tsx`:
  9 passed.

## Not verified by me
- **Full suites:** I did not re-run them. I am citing the implementer's runs on `7b0c9f79`/`e2392288`: backend
  2705, simulator 271, gateway 233, host 706, contracts 6, frontend 2153, all with 0 failed.
- **Other guards:** I did not run `check-all.ps1` or the registry checker.
- **Rule-8 corpus:** I did not run `writer_guard_probes.py`. I ran one manual probe instead.
- **Manifest non-vacuity:** I did not re-run the implementer's one-byte manifest edit.
- **Production refusal of cold Drafts (deviation 1):** I did not observe it myself; it is the implementer's
  statement.

## Residual risk
- **Same-minute event order:** `assertions.event_kinds` orders same-minute events by publication recording
  order. For example, POWER_LOSS and START_REQUEST at 19:00 come in a different order in different cases. This
  is pinned and deterministic under the test UUID controls, but a later analytic must not read causality from
  that order.
- **Batch count:** there are about 90 Batch V2 batches per run for about 93 envelopes, roughly one per publish
  instant. That is correct, but heavy for any later replay-volume work.
