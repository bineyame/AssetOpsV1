# S2-01b fix round 1 re-review

Produced by a fresh Claude reviewer (did not author the slice or the fix).

**Target:** `task/S2-01b-durable-simulated-gateway`, fix commits `ed0e397` and `d050540` (diff `dd69470..d050540`).
**Against:** Codex first review `.agent/S2-01b-codex-review.md` (F1 block), task `tasks/S2-01b-durable-simulated-gateway.md` AC4, packet "Fix round 1", questions `.agent/S2-01b-questions-5.md` (open to the Architect, not decided here).

## Verdict: ACCEPT (F1 resolved). No block findings. One new carry (R1) and one layout note folded into existing F3. F2 and F3 remain carried as before.

## F1 resolution, verified

Each part of the Codex direction is met:

- **Fit by count and bytes.** `gateway/assetops_gateway/service.py:214-239` (`_fit`) tries the count-bounded prefix first, then binary-searches on `BatchRejected(field="batch")`, which in `contracts/assetops_contracts/ingestion_batch_v2.py:238-239` is only the 1 MiB check. Batch text grows monotonically with each envelope (fixed-width id and digest, each envelope adds its escaped text), so the search is sound. Any other rejection kind re-raises instead of being treated as size. A group that already fit seals the same bytes and batch IDs as before, and the existing seal, replay and wire-vector tests pass without edits.
- **Refuse an individually unbatchable report before sequencing.** `_check_batchable` (`service.py:490`, `535-550`) runs after the envelope is built and before the `envelope_outbox` insert and the `sequence_state` upsert (`service.py:491-513`). `_Held` is caught at `service.py:521`, so the hold is written and no sequence is used. The only unbounded envelope field is the canonical decimal `value`. `unavailable_reason` is enumerated (`source_envelope_v3.py:259`), and IDs and ENUM labels are bounded by the snapshot, so the field label `value` is accurate. Because every admitted envelope fits a batch on its own, `_fit` always finds a prefix of at least 1. The refusal path cannot be reached from valid input, as the packet says.
- **Durable, honest Stage.** Ledger schema v2 adds `seal_refusal` (`ledger.py:142-158`), with an incremental migration loop (`ledger.py:306-318`). `seal()` commits partial batches and the refusal row, then raises `SEAL_REFUSED` after commit (`service.py:664-684`). IPC maps `GatewayRefused` to a typed error (`ipc.py:217`), and the host converts it to `PublicationRefused("SEAL_REFUSED")` (`host/gateway_publication.py:141-149`). `registered_stage_status` (`contracts/assetops_contracts/gateway_stage.py:89-98`) returns `STAGED` only when every envelope has a `batch_id`, and the status comes from the ledger alone, so a read after a restart gives the same answer. The session note no longer claims that "nothing was staged" (`host/lab_execution.py:2435-2437`).
- **Lab.** The parser requires `seal_refusals` (`runSetupClient.ts:1701-1703`). The refusal table and the headings changed from "sealed" to "stored"/"outbox" are honest, because those panels list unbatched envelopes too. No consumer branches on the old three-value status: `RunFrame.tsx:1216` and `RunHeader.tsx:164` show it raw, and the backend payload passes it through.

## Findings

### R1 - Carry (low): seal-refusal key omits outbox state, so a sibling state group can erase a refusal

`service.py:661-663` groups unbatched envelopes by `(source, epoch, snapshot, state)`. The `seal_refusal` primary key (`ledger.py:154`), the success-path `DELETE` (`service.py:678-680`) and the reader lookup (`service.py:910-920`) all use `(source, epoch, snapshot)` and leave out `state`. `admit`/`admit_texts` accept `initial_state` `READY` as well as `STAGED` (`service.py:370, 385`). Groups are processed in `ORDER BY ... o.state`, so `READY` comes before `STAGED`. A refused `READY` group therefore records its row, and the `STAGED` group for the same source, epoch and snapshot then seals and deletes it in the same transaction. The run's Stage then reads `SEALING_PENDING` rather than `SEALING_REFUSED`, and the durable reason is lost. This fails safe, since the Stage never claims `STAGED`, and it needs mixed-state admission plus a refusal that valid input cannot produce. That is why it is a carry and not a block. Fix: add `state` to the refusal key, the `DELETE` and the lookup, or delete only when no sibling group for the same key was refused in the same call. Confirmed by code reading. I did not reproduce it.

### Layout note - fold into existing F3 (carry)

The new "Sealing refused" table (`GatewayLedgerView.tsx:145-179`, 6 columns, free-text `detail`) is a dense table. The packet records layout evidence as **not run**, names the precondition (a live run cannot reach the refusal state from valid input) and does not claim a pass. That is the correct form. Add a fixture-driven narrow-width check of this table to the F3 layout carry. It is not a reason to return.

### F2, F3 - still carried

These are unchanged by this round. They stay in `.ai/MILESTONE_REVIEW_BACKLOG.md` as the Codex review classified them.

## Checks I ran (results as observed)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `pytest gateway/tests -q` | 80 passed |
| `pytest host/tests/test_registered_gateway_publication.py -q` | 15 passed |
| `pytest backend/tests/test_s2_registered_basis.py -q` | 33 passed |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run src/shell/__tests__/gatewayLedgerStage.test.tsx` | 9 passed (it ran in this session, against the usual sandbox expectation) |

**Not rerun:** the full host (644), backend with Postgres (1631), simulator (265) and full frontend vitest (1213) suites, `npm run build`, and the five mutation checks. These are the Implementer's numbers, not mine. Layout evidence was not run (see above).

## Residual risk not already in the packet

- R1 above.
- `_check_batchable` labels any `BatchRejected` as `UNBATCHABLE` at `value`. That includes a batch-configuration rejection such as an invalid `foundation_valid_from`, which snapshot verification should already rule out. The detail string carries the real kind and field, so nothing is hidden. Note only, not a finding.
- The status vocabulary (`SEALING_PENDING`, `SEALING_REFUSED`, `HELD`) and the questions-5 defaults are with the Architect. If the words change, the change touches `gateway_stage.py` statements and the frontend test copy only, not sealed bytes.

No files were changed by this review apart from this report. The pre-existing modification to `.agent/coordinator-handoff.md` was left untouched.
