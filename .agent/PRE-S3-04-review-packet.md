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

## Fix round 1 (review B1)
- Reworded to configuration-only scope: `READINESS_STATEMENT` and the no-binding-set text in `backend/assetops_backend/sites/binding_service.py` (dropped "Nothing is reporting."; now "...operational status is not assessed here."), and `bindings.statement` in `backend/assetops_backend/foundation_api.py` ("Whether any channel is reporting is not assessed here.").
- Tests: `_assert_configuration_only_copy` in `backend/tests/test_s1_bindings.py` (readiness + bindings statements; old phrases absent, "not assessed here" present). Proven failing before the fix (2 failures), passing after. Frontend `siteFoundationRevision.test.tsx` fixtures updated to the new wording and the Readiness view asserts the old phrases absent and the new scope present (fixture-driven, so the backend test is the real guard).
- Search of Foundation/Readiness views for other evidence/reporting claims: none remaining in `frontend/src/sites` or foundation/binding backend copy. Out of scope and untouched: `SiteOverview.tsx:241` (C2) and run-setup/simulator "no accepted evidence" copy (Lab surfaces, correct there).
- Checks: test_s1_bindings 35 passed; foundation/binding/readiness subset 358 passed (`test_s2_site_evidence_postgres.py` has a pre-existing collection NameError, ignored); vitest siteFoundationRevision 42 passed; tsc clean; check-all.ps1 6/6 guards passed.
