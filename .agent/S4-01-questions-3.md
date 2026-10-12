# S4-01 phase 2 questions (Q16-Q20) - for the Architect

Raised by the phase-2 Implementer (`I-finding-read`), 2026-10-12. Each states the default built; none blocks the
phase-2 review. Packet: `.agent/S4-01-phase-2-review-packet.md`.

1. **Q16 - 401/403 with no human sign-in.** `D-2026-10-09-pre-s3-claim-routes-and-actor` requires 401/403, but
   no authenticated tenant-user principal exists; the S3 Performance read admits the configured development
   tenant. Built: `finding_api.build_finding_router(access=...)` seam returning 401 (with `WWW-Authenticate`) or
   403 before any lookup; tests inject both. The default composition admits the development tenant's operator
   context and every body carries `access_basis: DEVELOPMENT_TENANT_OPERATOR_CONTEXT...`. Fail-closed
   alternative: default 401 for everything until A-actor-identity sign-in exists (blocks the phase-3 UI and
   the owner walkthrough). Confirm the parity default.
2. **Q17 - contradictory report inside a bounded stop (Q11).** The matcher sees a stop through adjacent dispatch
   intervals (last ON, OFF after, OFF before next, first ON). An intervening ON is visible (it is its own run, so
   no single stop spans it; tested). A contradictory/UNOBSERVED generator-state report between the two OFFs is
   *not* visible: the `dispatch-3.1` interval result carries no state between runs. Built default: unchanged
   matcher, the risk recorded. Fail-closed option: refuse a stop bridge when the window has any generator-state
   limitation inside the stop, which needs either a window-result field (an S3 model change) or a matcher read
   of window evidence. Which?
3. **Q18 - honest window state route.** To distinguish assessed `NO_FINDING` from NOT_ASSESSED / PENDING / STALE /
   FAILED and "assessment newer than the Finding" without a Site list (S4-04), phase 2 adds
   `GET /api/sites/{site_code}/finding-windows/{day}` (UTC day, same scope/status matrix). Default: keep it as a
   bounded per-window read; S4-04 may supersede it. Alternative: fold it into the S3 window read.
4. **Q19 - Performance cutover gate.** The Finding read is not behind `PERFORMANCE_CUTOVER_CLOSED`: there is no
   file-backed Finding detail being cut over (T028 Findings are comparison history), and the read reports its own
   currentness per cited window. Default: ungated. Alternative: gate Finding detail on the same comparison gate.
5. **Q20 - relation records in the persisted claim.** The bridge (`claim.continuity`: bridging segments/reasons,
   observed stops with both OFF times, `candidate_minutes_added: "0"`) and recurrence (`claim.recurrence`: LINKED
   with both OFF bounds and covered window IDs, or NOT_ESTABLISHED with a reason) are recorded by the matcher at
   write time; OFF evidence IDs are resolved by the read from the cited (immutable) interval revision's evidence
   at the recorded time. They are not in the basis digest, so no basis changes; a Finding opened before this
   change reads `recurrence: NOT_RECORDED`. Default: accept (the unmerged fixture DB is rebuilt each run).
