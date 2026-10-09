# S2-01b review packet: durable simulated gateway

- **Task:** `tasks/S2-01b-durable-simulated-gateway.md` (amended through `ec0f77a`). USER_REVIEW_REQUIRED: false.
- **Branch:** `task/S2-01b-durable-simulated-gateway`, built in phases 1, 2, 3a and 3b on S2-01a `85a11c4`. Not merged.
- **Decisions:** `D-2026-10-08-s2-local-gateway-snapshot-transfer`, `D-2026-10-08-s2-v3-source-payload-and-period-reference`, `D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary` (with the Q1-Q4 amendment of `.agent/architect-S2-01b-answers-4.md`).
- **Phase records:** `.agent/S2-01b-phase-1-handoff.md`, `-phase-2-handoff.md`, `-phase-3a-handoff.md`; questions `S2-01b-questions-1..3.md`, all answered.

## Outcome

A registered Kobo Lab run's public device reports leave the host through an authenticated local channel into a **separate gateway process**. That process holds the run's verified snapshot, sequences each admitted report into a canonical SourceEnvelope V3, and seals source-specific Batch V2 objects in a WAL SQLite ledger. Envelopes and batches stay `STAGED` with upload pending and no receipt. The Lab Stage for a registered run is read back from that ledger and shows its exact bytes. The new `registered-kobo-publication` v1 profile rounds numeric readings to 0.000001 in each signal's source unit, so all 293 public reports are admitted; under v3, 41 ratio readings were held. Pre-import YAML runs keep their file Stage, and registered Commit still refuses. S2-01a carry F1 is closed.

## Commits (phase order)

| Phase | Commits |
| --- | --- |
| 1 | `775f8f9` wire contracts and ledger, `c4cf878` handoff |
| 2 | `79fbbf2` gateway process and IPC, `a8bd895` registered Stage through the gateway, `1f0d25b` boundary guard, `77736f9` questions, `1d98fa1` port inventory, `692296d` handoff |
| 3a | `aca557a` device resolution profile, `a205bb0` handoff |
| 3b | `d3a98e8` F1, `896a8f9` Lab gateway Stage, resolution UI and Q4 wording, `939ced0` layout mode, plus this closeout commit |

## Files materially changed

- **Contracts.** `contracts/assetops_contracts/source_envelope_v3.py`, `ingestion_batch_v2.py`, `gateway_report.py`, `gateway_stage.py`, `observation.py` (resolution and `quantize_half_even`), `lab_projection.py` (Q4 docstring). Vectors are in `contract-fixtures/source-envelope-v3-vectors.json`.
- **Gateway package.** `gateway/assetops_gateway/` (`ledger.py`, `snapshot.py`, `service.py`, `ipc.py`, `__main__.py`).
- **Host.** `host/gateway_publication.py`, `host/lab_execution.py` (registered `_stage`), `host/execution_adapter.py` (`frozen_resolutions`), `host/lab_app.py`.
- **Backend.**
  - `runs/profiles.py`, `models.py`, `parsing.py`, `provenance.py`, `service.py`, `refusals.py`, `registered_basis.py`.
  - `simulator_lab_api.py`: `registered_stage_payload`, signal `resolution`, and the profile summary.
- **Simulator.** `observation/transform.py`, which quantizes after the bias and before the public observation.
- **Frontend.**
  - `shell/runSetupClient.ts`: the `GatewayLedgerStage` type, the `isGatewayLedgerStage` guard, the `status: "gateway"` result, and the resolution fields.
  - `shell/GatewayLedgerView.tsx`, which is new.
  - `shell/RunFrame.tsx`, `RunCommitPanel.tsx` and `RunSetupFrame.tsx`.
- **Guards and tools.** `tools/checks/dependency-direction.ps1`, `analytic-declaration.ps1` and `run-setup.ps1`, plus the host-to-gateway IPC rule. `tools/layout-evidence.mjs` gains the `ASSETOPS_LAYOUT_S2_01B_RUN` mode.

## Acceptance criteria

**AC1 Process and basis transfer: met.**
- **The process.** `python -m assetops_gateway serve --config` runs a separate process. Its IPC is authenticated by a protected local credential file created `O_EXCL` with mode 0600, and it is bounded at 16 MiB per frame.
- **Provisioning.** Tenant, Site, gateway, `SIMULATED` mode and permitted sources are provisioned in config, independently of any request.
- **Snapshot checks.** `snapshot.py::verify_snapshot` checks the hash, schema, canonical text, exact keys, the provisioned scope, internal consistency and the claimed references. It also checks validity at each report time.
- **Refusals.** A wrong Site or source, changed bytes, an unsupported schema and an unavailable gateway are each refused, with no YAML fallback.
- **Tests.** `gateway/tests/test_gateway_process.py` covers this (a stranger credential, wrong-Site provisioning, typed activation refusals), and so do `host/tests/test_registered_gateway_publication.py` (wrong Site or no gateway, unavailable) and the activate request, which carries the exact snapshot bytes.

**AC2 Public adapter: met.**
- **What crosses.** Only `assetops.simulated-device-report` v1 texts cross the boundary, with exact keys and no run id or private words (host process-boundary tests).
- **Binding rows.** Selected binding rows drive device, signal, source, unit and role. V3 carries the device value in the binding `source_unit`.
- **ENUM.** ENUM must be a mapping key and an uppercase member. It is proved through a direct public `generator-controller/status` observation, including an invalid-label hold. It is not a status that the daytime run emits (see Deviations).
- **Holds.** Unknown channel, incompatible unit, invalid enum and missing binding each become a typed hold with field and detail, and no sequence is allocated. POLICY and OPERATIONAL_RECORD return `SCHEMA_UNSUPPORTED`.

**AC3 Durable V3 identity: met.**
- **Ledger setup.** WAL, foreign keys, busy timeout, synchronous FULL, a migration version, and a single writer behind an OS file lock.
- **Sequencing.** The per-`(gateway, source, epoch)` sequence and the envelope insert happen in one transaction. The epoch changes only on reprovisioning, and overflow at `2**63-1` refuses.
- **Message id.** It uses length-delimited framing, with vectors that include the unframed-collision pair.
- **Replay and restart.** A replay is `ALREADY_ADMITTED` with the same identity. A distinct report at the same source time gets a new id. Restart keeps the bytes.
- **Run link.** The run link lives only in the local admission row's `lab_run_ref`.

**AC4 Sealed queue: met.**
- **Batch V2.** Each batch is bounded (256 envelopes, 1 MiB), has ordered ordinals, and is homogeneous by source, binding and epoch. Its digest excludes `payload_sha256`.
- **Copied verbatim.** `foundation_valid_from` is copied verbatim. A new basis opens new batches, and the old bytes do not change.
- **Immutability.** Triggers forbid rewriting or deleting envelope and batch bytes.
- **Local state.** `STAGED`, `READY`, `IN_FLIGHT`, the receipt slot and retry metadata are persisted. An interrupted `IN_FLIGHT` batch returns to `READY` with identical bytes.
- **No delivery claim.** No `ACKED` state and no receipt exist.

**AC5 Lab inspection and carry: met.**

The Stage read:
- `GET /runs/{id}/stage` for a registered run returns `store: GATEWAY_LEDGER`, built from the ledger. The file Stage is never asked (`backend/tests/test_s2_registered_basis.py`). Pre-import runs keep `LEGACY_FILE`, and direct registered Commit returns 409.

The Lab view:
- **Parsing.** `isGatewayLedgerStage` accepts only a whole ledger with `upload_state: PENDING`, `receipts: []` and `release_eligible: false`. Anything else falls to "unavailable" rather than a delivery claim; the guard was proved non-vacuous by removing the receipts check.
- **Rendering.** `GatewayLedgerView` shows the snapshot SHA-256, Site and gateway, epoch, and queue depth by state. It shows each sealed batch with its full SHA-256 and exact text, and every envelope with source, sequence, state, batch item, SHA-256 and exact text. It also shows typed holds with field, reason and seen count, publication notes, an unreachable gateway, "Upload: PENDING" and "Receipts: None".
- **Commit.** Commit and release stay blocked for a gateway Stage, even when no frozen basis is reported.
- **Tests.** `frontend/src/shell/__tests__/gatewayLedgerStage.test.tsx`, 8 tests.

Exact bytes across restarts:
- Host plus gateway restart giving identical bytes is proved in `host/tests/test_registered_gateway_publication.py` and `test_registered_kobo_resolution.py`.

F1:
- **The change.** `RunCommitPanel.tsx::releaseBasisBlock` applies the frozen-basis block to the committed branch. A legacy artifact committed before its Site was imported shows the basis block instead of Resume or Retry.
- **Tests.** `runCommitPanel.test.tsx` covers unfinished, refused and missing releases, plus a never-imported control that still offers Resume.
- **Non-vacuity.** Disabling the block failed all 3 cases, and the change was reverted.

**Phase 3 device resolution: met** (phase 3a).
- **Profile and identity.** `registered-kobo-publication` v1 applies 0.000001 to every numeric signal and none to ENUM. The resolution is frozen in `signal_resolutions`. v3, v4 and v5 bytes are unchanged.
- **Rounding.** It rounds exactly, half to even, after the bias.
- **Results.** There are 293 reports and 0 holds, where v3 gave 252 and 41. Replay and restart are byte-stable.
- **Refusals.** `PUBLICATION_UNIT_MISMATCH` and `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE` are reachable.
- **Lab, in 3b.** Setup names the profile's resolution and the registered-Site need, and leads both refusals with a plain label (`runSetup.test.tsx`). The run view shows a "Published to the nearest" column and a note: subtracting the bias gives the true value at that reading's own time only to within half a step, and a retained reading says nothing exact about a gap-hidden value (Q4).
- **Q4 docstring.** The `ObservationView` docstring is corrected, with no reserialization.

## Checks run (3b closeout, after `939ced0`)

| Check | Result |
| --- | --- |
| Frontend `npx vitest run` | 50 files, 1212 passed |
| `npx tsc --noEmit` | exit 0 |
| `npm run build` | exit 0 (the existing chunk-size warning only) |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| Backend with `ASSETOPS_TEST_DATABASE_URL` (Postgres on) | 1630 passed |
| Host | 638 passed |
| Simulator (run from `simulator/`, since a repo-root run fails collection on `from tests...`) | 265 passed |
| Gateway | 76 passed |
| Layout evidence | S2-01b mode (`ASSETOPS_LAYOUT_S2_01B_RUN`, real gateway process, lab_app on 8010, vite 5320, registered KOBO-001 daytime run, 293 envelopes, 5 batches, 0 holds, PENDING): 1280x800 10/10 PASS. 640x700 9/10 PASS; FAIL `the page does not scroll horizontally` (scrollWidth 780 vs clientWidth 625). Every gateway-ledger claim passes at 640 (snapshot hash, batch table in its own scroller, exact text, 6 resolution cells, sets non-empty). Overflow cause is not the ledger: no descendant's right edge exceeds 625 and the contained tables are in scrollers; `.app-frame` itself reports sw780. The same 780 failure appears in the full run on the READY-draft 640 case (no gateway ledger), while the BLOCKED 640 case passes at 625, so it tracks pages with run-interval tables. Not confirmed pre-existing: no baseline run on S2-01a was taken. Open for review |

Earlier phase full runs are in each handoff. 3a: backend 1630, host 638, simulator 265, gateway 76.

## Reviewer path

1. **Commands.** `pytest gateway/tests host/tests/test_registered_gateway_publication.py host/tests/test_registered_kobo_resolution.py backend/tests/test_s2_registered_basis.py backend/tests/test_s2_registered_resolution.py`.
2. **Frontend.** `npx vitest run src/shell/__tests__/gatewayLedgerStage.test.tsx src/shell/__tests__/runCommitPanel.test.tsx src/shell/__tests__/runSetup.test.tsx`.
3. **Live.**
   1. Provision a gateway from KOBO-001's snapshot (`host/tests/gateway_process.py::provisioning_from_snapshot`) and start `python -m assetops_gateway serve --config <cfg>`.
   2. Start `lab_app` with `ASSETOPS_GATEWAY_ADDRESS` and `ASSETOPS_GATEWAY_CREDENTIAL` set.
   3. Create a registered daytime Draft with `registered-kobo-publication@1` and run it to the end.
   4. Open the run's Stage disclosure. Expect 293 envelopes, 0 holds and PENDING upload. Restart both processes and compare the batch SHA-256 values.
4. **Layout.** `ASSETOPS_LAYOUT_S2_01B_RUN=<run> node tools/layout-evidence.mjs <base>`.

## Known deviations

- **ENUM proof (Q2).** ENUM handling is proved by a direct public generator-status observation through the registered map. The daytime Lab run emits no generator status. S2-02 owns a selectable generator-status run.
- **Delay windows (Q3).** A registered run with a delay window is refused before activation, with nothing staged. This is proved by injecting a delay window into a real Draft, because no registered-selectable profile declares a delay. It is a refusal test only; S2-01c owns delayed admission.
- **Stage before run.** There is no product UI that creates a gateway config. It is operator provisioning through a config file, and the live path needs it done by hand.

## Residual risk

- **Credential.** Protection relies on the user-profile ACL on Windows, because 0600 is advisory there. There is no explicit ACL hardening.
- **IPC.** There is no idle timeout on IPC connections.
- **Republishing cost.** Whole-series republish is O(n) per step. That is fine for 48 boundaries; a week-long run needs a watermark.
- **`frozen_inputs` rows.** `frozen_inputs` now has a "Device resolution" row on every run. That is a read-model change; stored bytes are unchanged.
- **Profile drift.** Changing a published profile's resolution later strands its runs, because the host refuses the drift. This is intended.
- **Duplicate holds.** A replayed held report increments `seen_count`. Hold rows are not byte-fixed.

## Carries

- **F1:** closed (above).
- **F3:** full `tools/layout-evidence.mjs http://localhost:5320` run, bounded 600 s: 215 PASS, then a hard stop (exit 1) with 'found its submit still disabled after ten seconds' at line 550, not the earlier CDP no-reply stall. Cause: the full script drives an existing ready Draft from the stored runs (about 286 in `var/runs`, plus the executed run created for the S2-01b mode), and it picked the already-completed registered run, whose controls are disabled. That also produced 2 FAILs per width in the READY-draft cases ('three execution controls', 'optional-inputs panel') and the 640 scroll FAIL above. So the full run is polluted by stored-run state, not clean evidence; a clean-var full run was not done. Sections after the BLOCKED draft cases were not measured.
- **S2-01a current-row metadata / asset-code identity:** unchanged, still expiring before S2-02.

## User-review focus

None required (USER_REVIEW_REQUIRED false). The reviewer should check:
- the gateway Stage copy, which never claims sent, accepted or delivered;
- the half-step wording in the reporting-paths note;
- the F1 block text on a committed legacy artifact.

## Fix round 1 (Codex review F1, `.agent/S2-01b-codex-review.md`)

Code commit `ed0e397`. F2 and F3 stay carried in `.ai/MILESTONE_REVIEW_BACKLOG.md`; not touched. Choices the review did not name are in `.agent/S2-01b-questions-5.md` (fail-closed defaults).

**What changed**
- **Byte-aware sealing** (`gateway/assetops_gateway/service.py` `_fit`, `seal`): each (source, epoch, snapshot, state) group is cut in sequence order into the longest prefix that fits both `max_envelopes` and Batch V2's 1 MiB. The count-bounded prefix is tried first, so a group within both bounds seals exactly as before (normal-path bytes, batch IDs and vectors unchanged; existing sealing, replay, restart and wire-vector tests pass unedited). Only a byte refusal shortens it, by binary search.
- **Unbatchable report held before a sequence** (`_check_batchable`): after building the envelope and before the outbox insert and `sequence_state` write, a singleton seal is tried; failure is a typed hold `UNBATCHABLE` at `value`, no sequence consumed.
- **Durable seal refusal** (ledger schema 2, `seal_refusal` table, migration v1 to v2 in `ledger.py`): a group that still cannot be sealed keeps its envelopes unbatched from the first unsealable one, records one refusal row, does not stop other groups, and `seal` raises `SEAL_REFUSED` after commit. Sealing the group later deletes the row. `GatewayReader.run_stage` returns the refusals for groups holding the run's unbatched envelopes; `ipc.stage_document` carries them.
- **Honest Stage** (`contracts/.../gateway_stage.py` `registered_stage_status`): `STAGED` ("sealed this run's public reports") only when every envelope is in a batch; otherwise `SEALING_PENDING` or `SEALING_REFUSED`; holds only is `HELD`. Derived from the ledger, so a read after host restart says the same. Host maps a seal refusal to `PublicationRefused("SEAL_REFUSED")`, and the session note no longer claims "nothing was staged by this attempt" (`host/lab_execution.py`).
- **Lab** (`registered_stage_payload`, `GatewayLedgerView.tsx`, `runSetupClient.ts`): `seal_refusals` travel and are parsed (required); a "Sealing refused" table renders them. Headings "exactly as sealed" / "Every sealed envelope" became "exactly as stored" / "Every envelope in the outbox", since they list unbatched envelopes too. The test fixture with an unbatched envelope now carries `SEALING_PENDING`.

**New tests** (each first seen failing, or proven non-vacuous)
- `gateway/tests/test_gateway_ledger.py`: the reviewer's case (256 reports, 4,096-digit value: all admitted, at least 2 batches, each at most 1 MiB, sequences 1..256 all batched); a single over-limit value held `UNBATCHABLE` with no outbox row and no sequence, the next report gets sequence 1; a forced seal refusal is durable across close and fresh read, leaves only that source unbatched, and clears when the group seals; v1 ledger migrates to v2.
- `host/tests/test_registered_gateway_publication.py`: status per ledger shape (5 cases) and statement never says "sealed this run" unless `STAGED`; a seal refusal is a typed `PublicationRefused`.
- `backend/tests/test_s2_registered_basis.py`: refusal travels verbatim in the payload; the registered Stage carries `seal_refusals: []`.
- `frontend/.../gatewayLedgerStage.test.tsx`: refusal row renders, no "sealed" claim; parser rejects a body without `seal_refusals`.

Non-vacuity (each mutation on the committed tree, then `git checkout --`): count-only `_fit` fails the bytes test; removing `_check_batchable` fails the unbatchable test; not reading `seal_refusal` fails the durability test; the old "any envelope means STAGED" rule fails 2 host status cases; an optional `seal_refusals` in the parser fails the parse test.

**Checks (after `ed0e397`)**

| Check | Result |
| --- | --- |
| Gateway | 80 passed |
| Host | 644 passed |
| Backend with `ASSETOPS_TEST_DATABASE_URL` (Postgres on) | 1631 passed |
| Simulator (from `simulator/`) | 265 passed |
| Frontend `npx vitest run` | 50 files, 1213 passed |
| `npx tsc --noEmit` / `npm run build` | exit 0 / exit 0 |
| `tools/check-architecture.ps1` / `tools/check-agent-workflow.ps1` | passed / passed |
| Layout evidence | not run: the normal registered path still renders `STAGED` with unchanged tables; the new refusal table appears only for the refusal state, which a live run cannot reach from valid input. Its layout is unverified. |

**Residual risk:** a ledger already holding an unbatchable envelope admitted before this fix now records a refusal instead of raising forever; that group stays unbatched until an operator acts (no re-sequencing path exists, by design). The binary search re-seals up to about 9 trial prefixes per over-size chunk; bounded, and only on the over-size path.
