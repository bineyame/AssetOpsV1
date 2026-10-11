# PRE-S3-04 review (fresh Claude reviewer)

Target: plan/pre-S3-startup, 75dd4d8 product files + packet commit.

## Verdict: reject (one block finding; small fix)

## Checks run
- `npx.cmd vitest run src/shell/__tests__/siteFoundationRevision.test.tsx`: 42 passed (ran here, not inferred).
- Searched the repo (excluding node_modules/.venv/.git/.agent) for the old phrases ("awaiting credentials", "not sending data", "no accepted evidence is linked", "no live source is claimed", `evidence.state`). The three C4 sites are gone; the only remaining hits are tests asserting absence, the task file and the backlog note.
- Other consumers of the removed `evidence.state`: none. `FoundationReadModel.evidence` is read only as `.statement` (StoredFoundationViews.tsx:435). The `state: "NONE"` hits elsewhere belong to `bindings.state`, a different field. Not run: full backend suite, full frontend suite/build (not requested; unverified by me).
- Nothing new infers contact/credentials from registration; the gateway and source copy now says "Registered" and "not assessed here". No new status value. The new Link only renders when `evidenceHref` is supplied. Wording is plain.

## Findings

### B1 (block): same stale claim remains on the same Readiness view, in two other API statements
- `backend/assetops_backend/sites/binding_service.py:82-87` `READINESS_STATEMENT` ends "...no evidence has been accepted for this Site." Rendered by `ReadinessVerdictPanel` (`FoundationBindingsPanel.tsx:150`, `<p>{readiness.statement}</p>`), which is on the Readiness view.
- Same file, ~line 730: the no-binding-set text ends "Nothing is reporting." (also rendered at :150). Same class of unqualified operational claim.
- `backend/assetops_backend/foundation_api.py:375-378` `bindings.statement` ("No evidence has been accepted against them.") rendered by `SignalBindingsPanel` (`FoundationBindingsPanel.tsx:201,207`).
- Why it matters: the task acceptance and Q8 require removing or qualifying hardcoded "no accepted evidence" copy; this is the identical hardcoded claim (the C4 finding named three locations, but the criterion is the claim, not the lines). Post-S2 it contradicts Site Evidence, and the page now says "not assessed here" in one panel and "no evidence has been accepted" in the next. The new tests only inspect the `evidence` block and the gateway text, so they cannot catch it; the new `document.body` negative check passes only because the real phrases differ in case/wording ("no evidence has been accepted" does not match /no accepted evidence/).
- Fix: reword the three strings to configuration-only scope (e.g. "It does not mean any device is connected, reporting or healthy; operational status is not assessed here." and "...what a registered channel will mean once it reports."; drop "Nothing is reporting."), and extend the backend/frontend assertions to cover `readiness.statement` and `bindings.statement` (e.g. no "no evidence has been accepted", no "nothing is reporting"). Check existing tests that pin the old strings (backend test_s1_bindings/test_s1_cutover, siteConfiguration.test.tsx:648 style assertions).

### C1 (carry): test limit is acceptable
Packet's stated limit (API has no evidence input, so output identical pre/post-S2) is honest and acceptable once B1 is fixed; the copy is state-independent by construction.

### C2 (carry, minor)
`SiteOverview.tsx:241` "No window: no evidence has been accepted for this site." is outside this task's Foundation Readiness scope; flag for a later truthfulness sweep. Layout evidence not required (copy-only).
