# W2-05b review - EV causal producer and public replay

Reviewer: independent Claude reviewer (did not author the slice). Branch `task/W2-05b-ev-producer`, head `7859562d`,
final code revision `70a46d55`, diff `main...HEAD` (70 files). Judged against `tasks/W2-05b-ev-producer.md`,
`.agent/W2-05b-build-spec.md` (dry-read plus q1-q6), `.agent/W2-05b-pending-rulings.md` and the packet.

## Verdict: ACCEPT-with-followups

No High or Medium finding. Two Low items below; neither blocks merge.

## Ruling conformance (sampled against code)

- **Catalog and frozen identity (Q1-Q11):** six `config/scenarios/ev-*.yaml`; catalog labels, the ten-key row and the
  401 -> 422 -> 403 -> 404/200/503 order (N2) are in `simulator_lab_api.py:list_ev_scenarios`. The legacy catalog
  excludes `EvScenarioDefinition`. Legacy fingerprint pins are untouched. The test edits only exclude the new
  schema.
- **State table (Q13-Q14):** `test_ev_pack.py` passes. The pack is covered by the cell-by-cell tests.
- **v4 correlation (Run 8 handoff):** `transform.py:639-641` emits `session_id` only on energy `INTERVAL_DELTA`.
  Means and state default to null IDs (`host/ev_publication.py:166-177`). Events keep the v4 rules. Sessionless
  FAULT/CLEAR use the Q16 episode ID (`_correlation`, `:193-201`).
- **UNPLUGGED / IDENTITY_KWH (Q15/Q17):** the seven-label vocabulary and the identity maps are in place. `IDENTITY_KWH`
  is accepted only for `ev_connector_energy` with kWh->kWh and `{}` parameters, in `gateway/snapshot.py:302-308` and
  `evidence/ledger.py:317-323`. Every other combination still refuses. `gateway/service.py` needs no change: a
  non-ENUM, non-state binding is already a canonical-decimal passthrough (`:930-936`).
- **N13:** `_snapshot_rows` (`host/ev_publication.py:380-390`) requires a single declared device and signal in the
  frozen Foundation. The device's component must equal the mapped code. A consistent-swap refusal test and an
  unchanged-fixture-reaches-Stage test both exist (`test_ev_lab_execution.py:308-316,331-337`).
- **Artifact and restart (Q20-Q24), N14-N17:** host EV tests pass, including damaged schema-7 and schedule mismatch.
- **Manifests (q6):** I parsed all six. Each has 18 keys and is sorted compact JSON with a final newline. The window
  matches Q1, the profiles and seed are correct, and `assertions` equal the q6 table literally, nulls included.
  `test_w205b_ev_replay_postgres.py` regenerated them on my own clean DB and compared byte for byte; it passed.
- **Replay access (N1):** `main.create_app` passes the same injected `ev_access`/`ev_owner` to the catalog and to
  replay. The default is `no_owner_principal`, which gives 403. Tests cover 401, 403 (access and owner), 422
  (absent, empty, malformed, repeated), 404 Site and run, wrong-Site 403 and 503. Replay reads use REPEATABLE READ,
  READ ONLY on one connection and are SELECT-only.
- **Earlier behaviour:** `execution_path_for`, `gateway_mapping_for` and `_V4_ONLY_PUBLICATION_PROFILES` add EV
  without changing the cold or legacy branches. Cold keeps `cold-delay-` and schema 6. The Lab gate inventory now
  lists both EV routes, and the replay router is mounted inside the gate block.

## Findings

**L1 - EV setup copy renders smaller than its cold sibling** (`frontend/src/shell/SimulatorLabFrame.tsx:112-116`).
- The ruled sentence sits in `Panel description`. It renders at about 11 px; the sibling cold sentence (`:99`)
  renders as about 14 px body text (app-1440, app-390).
- This conforms to the q2 N3 wording ("description exactly ...").
- v69 has no setup panels. Its panel descriptions are also small sub-lines ("Exactly the source boundary..."), so
  this is not a mock mismatch.
- The fault is inconsistency between two sibling setup panels, plus small text on mobile.
- Follow-up: the Architect picks one slot for both panels in the W1-end UI/UX pass.

**L2 - no zero-failure full JUnit at the final revision.** This is a residual, not a defect.
- The `bd967b59` run (3096 tests, 1 failure, 0 skipped) ran code byte-identical to `70a46d55`; the fix changes only
  `test_simulator_lab_gate.py` (+3 lines).
- ROLE_CONFIG "Token Efficiency" says not to rerun full suites after test-only changes, only the touched file. I
  reran that file and it passes. This overrides the task's older "one full suite on final revision" sentence.
- Follow-up: the merge record should cite both the `bd967b59` run and the file rerun.

## Builder notes

- **N18 is not a finding.** The N1 composition seam exists and is tested. The isolated walkthrough ASGI app is
  walkthrough preparation, which the owner placed at W2 close (2026-10-19) and which does not gate this slice.
- **N19 is not a finding.** The spec reads "S2 delta/connector" as a single compound check, and
  `EV_CONNECTOR_MISMATCH` on a GOOD delta is that check. The envelope-level `EV_DELTA_*` refusals are unchanged
  W2-00 rules and are already proven at S2 intake (`backend/tests/test_w200_source_events_postgres.py:210-213`).

## Checks I ran (head `7859562d`, private DB `w205brev_test`, dropped)

| Check | Result |
| --- | --- |
| backend: lab gate, ev_replay_api, ev_scenarios, w205a_ev_roles, s2_evidence_ledger_postgres, scenario_fingerprints, run_binds_scenario_to_site | 234 passed |
| backend: `test_w205b_ev_replay_postgres.py` + `test_w205a_ev_foundation_postgres.py` | 32 passed, 401 s |
| simulator ev_pack, ev_public_transform, cold_pack + whole gateway suite | 354 passed |
| host test_ev_lab_execution, test_ev_publication + contracts | 78 passed |
| frontend `tsc --noEmit` | exit 0 |
| vitest: evRunSetup, evScenarioChoiceClient, simulatorLabGate, simulatorLabWorkspaceEntryPoint | 140 passed |
| `tools/check-all.ps1` | 10/10 passed |

Not rerun by me: the full backend, host and vitest suites, and the writer-guard `--seam` corpus. For those I rely on
the packet. Residual risk, already named by the packet: no concurrent-writer race test for replay snapshot isolation.
