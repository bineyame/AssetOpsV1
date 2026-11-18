# S2-01c phase-3b design questions (Implementer, 2026-10-09)

Each has a fail-closed default that is implemented and committed. None blocks review. Batch with `.agent/S2-01c-questions-3.md` (still unanswered).

## Q1. F2: does "basis unknown" include a Stage read that does not report a frozen basis?

`RunCommitPanel.tsx` `releaseBasisBlock` now blocks Resume/Retry release when the Stage read is pending (`stage === null`), unavailable or not found, and also when a loaded file Stage carries no `frozen_basis` at all (a backend older than S2-01a). Before, an absent basis left release enabled. Two existing T027 tests that relied on a basis-less Stage now use an explicit unimported `LEGACY_FILE` basis with `can_release: true`. Commit (not release) keeps its earlier behavior for an absent basis. Default: unknown means not offered; the server refusal remains. Architect: confirm, or say an absent basis should keep the pre-S2-01a behavior.

## Q2. Where the "Lab Gateway & Ingestion" view lives

The Lab has no separate Gateway & Ingestion page. The diagnostics and publication panels render inside a registered run's Stage disclosure, under the gateway ledger (`RunFrame.tsx` gateway branch). The diagnostics read is gateway-wide, not per-run, so it appears on every registered run's page. Default: keep it on the run page and add no route or navigation (v6.9 `lab` is reference only). A dedicated page would be a small follow-up.

## Q3. Freshness of the diagnostics read

The diagnostics panel reads once per page load and again whenever the Stage is re-read (after a step, run-to-end, playback stop or publication advance). It does not poll. It labels the instant it was read on the gateway's real UTC clock, so a stale read is visibly stale. Default: no timer; S2-02 owns freshness against server receive time.

## Q4. New client methods are optional on `RunSetupClient`

`getPublication`, `advancePublication` and `getGatewayDiagnostics` are optional members so the roughly twenty test fakes need no change; a client without them is shown as "not available", never as an empty queue or a healthy gateway. The production client implements all three. Default: keep optional.

## Q5. The advance input accepts free text

The advance input is pre-filled with the earliest waiting scheduled release, or the clock's current instant. The client does not validate the instant: the backend's 422 (shape) and `PUBLICATION_INSTANT_INVALID` (canonical UTC) refusals are shown verbatim with plain wording. Default: server-side validation only, so there is one definition of a valid instant.
