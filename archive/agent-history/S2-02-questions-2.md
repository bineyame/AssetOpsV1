# S2-02 questions 2 (phase 2)

Raised while building S2-02 phase 2 (credential, diagnostics, gateway transport, Lab Commit). Each is built on the fail-closed default named; none blocks phase 3. Batch with questions-1 for the next Architect round.

**Q8. Rotation revokes the previous credential at issue.** `provision_gateway issue` revokes every earlier active credential of the gateway in the same transaction that stores the new verifier, so there is no overlap window; the gateway must pick up the new secret file before its next request. Options: (a) immediate revoke (built); (b) a bounded overlap (old valid until an explicit `revoke`). *Default:* (a) — fail-closed; sealed bytes, batch IDs and receipts are unchanged across rotation (tested).

**Q9. Central freshness threshold.** `CURRENT` while the last diagnostic was received within **2 × declared cadence** (120 s for the 60 s demo), else `STALE`; no diagnostic ever is `UNKNOWN`. The gateway emits at most one diagnostic per cadence slot at any point within the slot, so consecutive receipts can legitimately be up to two cadences apart; a 1 × threshold would flicker. *Default:* 2 ×. The declared cadence is a registered column `gateway.diagnostic_cadence_seconds` (default 60, set by provisioning), not a field of the V1 wire.

**Q10. TLS enforcement point.** Credentialed gateway requests (`/api/ingestion/batches*` with `Authorization`, `POST /api/gateways/*/diagnostics`) are refused with **426 `GATEWAY_TLS_REQUIRED`** unless the ASGI request scheme is `https`, before authentication. `python -m assetops_backend.serve_tls --cert --key` serves uvicorn with TLS. A TLS-terminating reverse proxy (`X-Forwarded-Proto`) is **not** trusted; supporting one needs an explicit decision. *Default:* direct TLS only.

**Q11. Diagnostic refusal shape.** Malformed bodies (422) and same-identity changed bytes (409) leave an append-only `gateway_diagnostic_refusal` row (audit, technical design "refused and audited"). Scope failures (path/claimed gateway or Site mismatch, unregistered or foreign source) are 403 with **no** row, matching the Batch V2 claim rule (questions-1 Q3). *Default:* as built.

**Q12. Provisioning tenant and actor.** The CLI accepts only the configured development tenant (`demo`), like the S1 converters; `actor` defaults to the OS user name. A real operator identity awaits the S1 tenant/user model. *Default:* as built.
