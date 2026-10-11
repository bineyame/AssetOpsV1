# PRE-S3-04 review packet

Task: Foundation Readiness truthfulness (Architect batch 5 Q8; PRE-S3-03 review C4).

## What changed
- `backend/assetops_backend/foundation_api.py`: `evidence` block no longer carries `state: "NONE"` (removed; no new status value) and its statement changed.
  - Before: "No accepted evidence is linked to this Foundation and no live source is claimed."
  - After: "Operational status (contact, credentials, data received, accepted evidence) is not assessed here."
- `frontend/src/sites/FoundationRevisionPanel.tsx` (`RegisteredSourcesPanel`): gateway line
  - Before: "Gateway X: registered, awaiting credentials, not sending data."
  - After: "Gateway X: registered. Whether it has made contact or sent data is not assessed here; see Site Evidence." (link via new optional `evidenceHref`, passed from `StoredFoundationViews`).
  - Source caption: "...none is sending data." -> "...whether data is arriving is not assessed here."; source State cell "Awaiting credentials" -> "Registered".
  - Leaf doc comment updated.
- `StoredFoundationViews.tsx`: scope note now says "Claim readiness, accepted evidence and diagnostics are on Site Evidence."
- `siteFoundationClient.ts`: `evidence` type is `{ statement }`.

## Tests
- `backend/tests/test_s1_bindings.py`: the missing state (no binding set) and the populated state (converted KOBO-001, ready to report) both assert no `state`, "not assessed here", no stale phrases; gateways stay PENDING registrations. Result: 35 passed.
- `frontend/src/shell/__tests__/siteFoundationRevision.test.tsx`: Readiness view asserts new wording, absence of "awaiting credentials / not sending data / no accepted evidence", and Site Evidence link. 42 passed.
- Honest limit: the read API has no Evidence/diagnostic input, so output is identical in post-S2 and pre-S2 states by design; that identity is what the tests pin (an accepted-evidence state cannot contradict the copy).

## Checks
tsc clean. tools/check-all.ps1: all 6 guards passed (architecture, navigation, workflow, registry, delivery fixtures, ledger).
