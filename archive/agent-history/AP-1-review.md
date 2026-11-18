# AP-1 review: stored-Site analytics readiness (`/api/sites/{id}/analytics`)

Reviewer: fresh Claude reviewer (did not author the work), 2026-11-13.
Branch `task/AP-1-analytics-port`, worktree `/opt/assetecon/AssetOpsV1-ap1`, HEAD `6df1ca25e` (merge `21da6e03e`).
AP-1's own commits: `f75c70cec`, `9f5b8e6f1`, `444c651ca`, `6df1ca25e`, plus the conflict resolution in `21da6e03e`.
(`5e93499e6` is a main commit brought in by the merge, not AP-1.)
Judged against: design `.agent/architect-analytics-port-and-db-choice-2026-11-13.html` Part A, D-SR.75/77/78, packet `.agent/AP-1-packet.md`.

## Verdict: REJECT (one High finding needing an Architect placement ruling; the backend is sound)

The backend port is correct and well tested. But on the real app the stored 200 is never shown: a stored Site's
Evidence page is `LedgerSiteEvidence`, which renders no readiness panel. The slice therefore has no observable
product behaviour on Kobo or Kisiwa, its one "renders the table" vitest proves it only with a fixture pairing that
cannot occur, and every stored Evidence page load now runs the stored read and discards it.

## Findings

### H1 (High, acceptance gap) The stored readiness 200 has no consumer on a stored Site's Evidence page
- `frontend/src/sites/SiteEvidence.tsx:118` fetches `/analytics` for every Site, but `SiteEvidence.tsx:189-201`
  returns `<LedgerSiteEvidence>` as soon as `/evidence` answers the ledger shape (`isLedgerEvidence`, store
  `POSTGRES`). `LedgerSiteEvidence` takes no declaration and renders neither `CapabilityReadinessTable` nor
  `CapabilityReadinessAnalysis` (grep: those components are used only at `SiteEvidence.tsx:253-254,304`, on the
  file-evidence path). A stored Site whose S2 comparison has not passed gets 409 on `/evidence` and the
  `EvidenceRefused` page instead (`evidence_api.py:236-251`). So no stored Site reaches the table.
- The design premise (A1: "panel shows 'not available yet'" on Kobo/Kisiwa) is not what the code does today either;
  that line also renders only on the file path. This is a design gap the implementer followed, not an implementer
  error, but the acceptance outcome "stored mini Site Evidence shows readiness" is not met.
- `frontend/src/sites/__tests__/ap1StoredAnalytics.test.tsx:57-63,90-93` pass a `POSTGRES` Site with
  `POPULATED_EVIDENCE` (the file-shaped evidence). That combination is impossible in production, so the test passes
  without proving the user-visible behaviour (the packet's "SiteEvidence/CapabilityReadiness render the stored 200"
  is true only of the component, not of the page).
- Cost side effect: before AP-1 the call was a cheap 409; now each stored Evidence load runs `role_presence` plus
  `selected_intervals_on` and the dispatch-3.2 adapter over the range (site-wide with no range: every selected
  window) and discards the result. Unwarmed latency is still unmeasured (parity probe pending).
- Fix (needs an Architect ruling on placement, about 0.2-0.3 units): either render the existing
  `CapabilityReadinessTable`/`CapabilityReadinessAnalysis` inside `LedgerSiteEvidence` (Overview "What we can conclude
  now" / Analysis "How each limit is set", matching v69 `SITE_EVIDENCE.mini.caps`, which is a capability table on the
  mini Evidence page), passing `loaded.declaration` through; or, if the panel stays off the ledger page, skip the
  `/analytics` call when `/evidence` is the ledger shape. Replace the vitest fixture with the ledger evidence shape
  (`LedgerEvidence`, store `POSTGRES`) so the test exercises the real branch.

### L1 (Low) `LookupError` catch masks programming errors as "Site not found"
- `backend/assetops_backend/analytics_api.py` stored branch: `except LookupError` maps to 404 `SITE_NOT_FOUND`.
  `KeyError`/`IndexError` are `LookupError` subclasses, so a missing key in a stored row or result
  (`revision["model_version"]`, `s["start"]`, `p["role"]` in `stored_declaration.py`) would tell the user the Site
  does not exist. Fix: raise a dedicated exception (e.g. `StoredSiteNotFound`) from `stored_site_declaration` when
  `site_type_on` is None and catch only that.

### L2 (Low) The 422 refusal text is technical once the panel is reachable
- `stored_declaration.py:v3_assessment_view` raises "Readiness maps dispatch-3.2 results only; revision <uuid> is
  <model>." and `CapabilityReadiness.tsx` `Unavailable` renders a non-409 message verbatim. D-SR.78 Q3 asks for the
  page's existing refusal sentence; with a revision UUID and model id it is not plain words. Moot until H1 is fixed;
  fix with H1 (plain sentence in the message or render the generic line for `UNSUPPORTED_RULE_VERSION`).

### L3 (Low) Parity probe is not strictly read-only and its pass key will flag expected differences
- `tools/ap1_parity_probe.py:35`: `build_assessment_store(persistent=True)` plus `service.dispatch` runs
  `assess_site`, which appends revisions to the shared JSON `var/assessments` when evidence changed
  (`service.py:145 save_history`). A probe should not write; use `persistent=False` (the in-memory store recomputes
  the same latest assessments).
- The `available` key is `role|device_id|signal_id`; file-era ids vs stored binding ids (and the D-SR.78 null ids for
  unbound roles) will appear as one-sided keys in `available_mismatch`, so "mismatch empty" cannot be the literal pass
  rule; compare by role (and by feeder for Load) and list id differences separately.
- D-SR.78 Q3 asks the probe to record whether selected revisions trip the 422; today an `UnsupportedModel` aborts the
  probe with a traceback. Catch it and emit it in the JSON.

### N1 (Note, wording) "(reference Not bound)"
- `CapabilityReadiness.tsx` `referenceSuffix`: D-SR.78 Q2 says "Not bound" where the reference sits. The builder puts
  it inside the existing "(reference ...)" slot, which satisfies the ruling literally; "(Not bound)" would read more
  plainly. Preference, not an acceptance gap.

## Checked and found correct
- Role map fail-closed: unmapped labels and `NOT_STORED` kinds are never available; controls only from an unsuperseded
  Foundation revision with a value; configured capability never counted as observed (`segment_roles(s, {})` takes no
  configuration; test `test_configured_capability_is_never_an_observed_reading` is real).
- Role presence: one query, all bindings returned with a NULL latest time when no GOOD accepted reading exists, so
  bound-but-silent reads "No usable record" with its ids and only a truly unbound role reads "Not bound"; presence,
  controls, site type and selected intervals all run on one REPEATABLE READ connection (`read_snapshot` ->
  `_snapshot`).
- Consistency: the no-DB test derives the claim-limit roles from `role_coverage` + `_reasons` and compares with the
  panel over 5 revisions (covered, PCS gap, unobserved, unknown text, poor/conflict); the Postgres test compares
  against the real claim-limit route over 3 fixture days (one is trivially empty, two are not). Not vacuous.
- `in_window` unchanged (`declaration.py:186-202`); the SQL prefilter `window_start < hi AND window_end > lo` is a
  superset and the per-assessment rule still applies.
- Legacy codes keep the file path; closed gate -> existing 409 `AWAITING_EVIDENCE_MIGRATION`; cold/EV -> `analytics: []`
  without the gate or any reading query; other model -> 422 `UNSUPPORTED_RULE_VERSION`; store down / no DB -> 503.
- Sibling routes (`/dispatch`, `/findings`, `/assessments/...`, `/api/findings`) unchanged, still on `LegacySiteGate`
  (only `get_declaration` branches). No AP-1 test asserts a sibling stays 409 for a stored code; low risk, unchanged code.
- D-SR.77: `SitePerformance` branches on `configuration_store === "POSTGRES"` and never calls `/analytics` for a stored
  Site; the only caller (`SiteAnalyticsFrames.tsx:426`) passes it. `FindingsIndexes`/`FindingDetail` do not call
  `/analytics` (grep: `getDeclaration` only in `SiteEvidence.tsx` and `SitePerformance.tsx`).
- Merge `21da6e03e`: `SiteEvidence.tsx` keeps the SR-12a ranged rejections read and the SR-12b ranged `/analytics`
  read; the all-dates line is on neither panel; the merged test covers both.
- No stray files in AP-1's commits (packet force-added by name only).

## Checks run (by this reviewer, on HEAD `6df1ca25e`)
- `pytest tests/test_ap1_stored_declaration.py`: 28 passed.
- `pytest test_sr12b_analytics_readiness_range.py test_t028_dispatch_analytic.py test_t028_fix_round_1.py
  test_s3_claim_limit_vocabulary.py`: 61 passed.
- `ASSETOPS_TEST_DATABASE_URL=.../assetops_ap1_test pytest tests/test_ap1_stored_declaration_postgres.py`: 6 passed
  (12.6 s).
- vitest `ap1StoredAnalytics`, `siteEvidenceScreen`, `t028EvidenceCapability`, `miniDecisions` (the other file that
  mounts `SitePerformance`): 4 files, 91 passed. No file named `SitePerformance*.test.tsx` exists; Performance
  coverage is in `ap1StoredAnalytics` and `miniDecisions`.
- `npx tsc --noEmit`: clean (exit 0).

## Not verified
- Kobo parity, Kisiwa live read and unwarmed timing (probe pending a DB slot; code reviewed only, see L3).
- check-all (coordinator), full suites (policy), layout evidence (not layout-sensitive as built; becomes relevant if
  H1 adds the table to the ledger page).

## Residual risk not in the packet
- H1's discarded read on every stored Evidence load, unmeasured, on the demo's main page.
- `ledger_scope` (backend branch) and `configuration_store` (frontend branch) are two signals for "stored"; they agree
  today (both derive from `sites/cutover.py`), but nothing asserts it.

## Re-review (fix round cc6d153be + 67021409a) - ACCEPT
- H1 closed: `LedgerSiteEvidence` Overview shows the readiness table only when declaration is `loaded` with rows (`capabilityTableShown`), badge "Evidence · Overview"; 409/422/`[]` keep the old line and badge; Analysis view untouched. Vitest uses `LEDGER_EVIDENCE` + `ledgerClient` through `App`/`SiteEvidence` (the `isLedgerEvidence` branch) with a POSTGRES Site; the 200 test fails on the old `LedgerSiteEvidence` (verified by swapping it in), 409/422/[] tests assert today's line, no UUID/model id.
- L1 `StoredSiteNotFound` -> 404, KeyError -> 500 (tested). L3 probe: `persistent=False`, role/feeder keyed compare with `id_differences`, 422 recorded (code read; probe not run, needs DB). N1 "(Not bound)" done.
- Checks: AP-1 + sr12b + t028 pytest 71 passed; vitest ap1StoredAnalytics (8), s2LedgerEvidence, siteEvidenceScreen, v01bEvidenceVisual (68) passed; tsc clean. No stray files; worktree clean.
