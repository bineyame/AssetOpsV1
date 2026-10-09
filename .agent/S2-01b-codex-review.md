# S2-01b Codex first review

**Target:** `task/S2-01b-durable-simulated-gateway` at `bb09554`, diff from `85a11c4`.

**Verdict: RETURN.** The normal registered Kobo path is supported by the implementation packet and its recorded green suites, but one valid admission path cannot produce a bounded sealed batch and is reported in Lab as sealed. This violates S2-01b AC4 and makes the Stage claim false. No code was changed in this review.

## Findings

### F1 — Block: a valid admitted series can permanently fail batch sealing

`gateway/assetops_gateway/service.py:579-641` splits each homogeneous group by **count** only (`max_envelopes`, default 256). `seal_batch_v2` also enforces a 1 MiB serialized-byte limit (`contracts/assetops_contracts/ingestion_batch_v2.py:213-258`). V3 permits canonical decimal strings without a length bound. Thus a set of individually valid reports can be durably sequenced, then exceed the batch byte limit. `seal()` raises and rolls back its entire transaction, leaving every row unbatched; retrying the IPC `seal` operation uses the same count and fails again. The host's earlier admission is already committed, so this is not a recoverable all-or-nothing refusal of acquisition.

Focused reproduction on the reviewed tree: with the gateway test snapshot and fixed clock, admit 256 `battery-bms/soc` reports whose value is a 4,096-digit canonical integer. All 256 return `ADMITTED`; `gateway.seal()` raises `BatchRejected(TOO_LARGE, batch)`; SQLite then has 256 `envelope_outbox` rows and zero `upload_batch` rows. The reports fit the IPC frame bound. A single sufficiently long valid value has the same problem even if the count is lowered. No green suite needs repeating to establish this case.

The visible claim compounds the failure. `host/gateway_publication.py:154-160` calls the ledger Stage `STAGED` whenever it contains an envelope or hold. `contracts/assetops_contracts/gateway_stage.py:21-28` then states that the gateway **sealed this run's public reports**, although this reproduction has zero batches. `host/lab_execution.py:2434` keeps the sealing refusal only in a live session note, which disappears after a host restart. AC4 requires bounded immutable batches and an honest pending/failed Stage after acquisition failure. Fit batches by both count and serialized bytes, refuse an individually unbatchable report before sequence allocation, and keep the publication/sealing state durable enough for a restart read to describe it accurately.

### F2 — Carry: the F1 release guard is absent until Stage has loaded

`frontend/src/shell/RunCommitPanel.tsx:154-188` computes `releaseBasisBlock(stage)` for an already committed artifact, but `releaseBasisBlock(null)` returns null. The Commit read and Stage read are independent. If Commit finishes first, an old pre-import artifact whose Site was later registered briefly shows an enabled **Resume release** or **Retry release** button; it remains enabled if Stage fails to load. The server still refuses, so this is a presentation and actionability gap rather than a new Evidence write. Carry it to the next Lab UI correction: keep release controls unavailable while the basis is unknown, then show the existing basis block when Stage resolves.

### F3 — Carry: narrow full-run layout remains unverified

The packet records a 640 px page scroll width of 780 px in the registered run layout check, including a READY-draft case without the new gateway ledger. It also records that the full layout run stopped after 215 passes on stored-run state and did not reach later sections. The gateway-specific assertions passed at 640 px. Carry the narrow page overflow and clean-state later-section check as layout evidence work; this is not a reason to reopen the gateway contract.

## Review scope and checks

I read the task, review packet, workflow and role criteria, S2 decisions, current S1-S7 architecture and execution references, and traced the host adapter, authenticated IPC, snapshot verification, ledger admission/sealing, registered Stage read and Lab release guard. I relied on the packet's recorded full suites (frontend 1212, backend 1630, host 638, simulator 265, gateway 76, architecture/workflow guards) and did not rerun them. My focused byte-limit reproduction used a temporary SQLite ledger; it changed no repository files. The working tree already had an unrelated modification to `.agent/coordinator-handoff.md` when review began; I left it untouched.
