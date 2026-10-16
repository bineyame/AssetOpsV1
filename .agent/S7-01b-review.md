# S7-01b review - Site Health and battery boundary UI (+ S7-01a follow-up)

Reviewer: a fresh, independent Claude reviewer who did not author the slice. Reviewed `09501a67` (head of
`task/S7-01b-health-ui`), diff `git diff f3de235a..09501a67 -- ':!.agent'`, in worktree `AssetOpsV1-review2`.

## Verdict: ACCEPT

No High or Medium finding. There are four Low findings below, and none of them blocks merge.

## Checks run (by this reviewer)

- **Focused backend tests.** Private DB `s701b_rev2_test` (created and dropped), worktree `PYTHONPATH`, main venv:
  `pytest test_s7_source_health_rules.py test_s7_source_health_postgres.py test_s7_asset_boundary_postgres.py
  test_s7_health_contract_postgres.py` -> **22 passed** (192.9 s). The contract test passes, so the committed
  `backend/tests/fixtures/s7_health_api_contract.json` equals the normalised persisted responses at this revision.
- `npx.cmd tsc --noEmit` (frontend) -> clean, no output.
- `npx.cmd vitest run siteHealthBoundary.test.tsx operatorSiteTabs.test.tsx siteDetailRoute.test.tsx
  overflowContainment.test.tsx` -> **4 files, 78 passed**. Vitest ran in this environment.
- `tools/check-architecture.ps1` -> "Architecture check passed.", exit 0. It includes the statement-level rule 8 guard.
- `tools/check-agent-workflow.ps1` -> "Agent workflow check passed.", exit 0.
- **`tools/writer_guard_probes.py`: not run to completion.** I started it and then stopped it: it takes about 70 s a
  probe and mutates backend modules. The slice adds no SQL writer, so the probes are not required. I restored the one
  module the probe had mutated with `git checkout --`, and the tree was clean afterwards. This is not a claim that it
  passed.
- **Not run by me:**
  - The full backend suite. I cite the implementer's run instead: 2540 passed, 0 failed, 0 skipped at `e1294d16`,
    1303.99 s. Backend code is identical at `09501a67`.
  - Full `npm.cmd test` and the build.
  - `tools/s701-health-evidence.mjs` and `tools/layout-evidence.mjs`.
  - The walkthrough end to end, which needs servers on ports 5447 and 8947.

  The packet records layout-evidence honestly: 206 PASS and 28 FAIL, each failure a store precondition, and the
  tool's claims for Health marked "unverified". The Health tab's layout rests on the S7 evidence script (40/40),
  which I did not rerun.

## Focus points verified

- **Clock ruling `D-2026-10-16-s701-clock`.**
  - `CLOCK_OFFSET_LIMIT_MS` and `OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS` are separate constants
    (`source_health.py:40-42`). Both are inclusive (`:165`, `:177`), and the second is disclosed as
    `clock.observed_after_receipt_allowance_ms`.
  - `reported_age` (`:184-189`) returns null when there is no time, when the clock is UNTRUSTED, or when the time is
    later than `read_at`. It is used for both `fact_age_seconds` and `reported_contact_age_seconds`.
  - `summary.reason` is `NO_ENABLED_GATEWAY`, `NO_REGISTERED_GATEWAY` or null (`:281`).
  - Pure tests cover the inclusive edges and both reasons. The Postgres test asserts that every age is null or >= 0.
- **Gateway contact label** (`SiteHealth.tsx:263-275`).
  - The badge reads "Gateway contact: ...", followed by "N enabled gateways: x current, y stale, z unknown" and
    "N disabled, not counted".
  - Disabled rows are listed with a Disabled badge and left out of the device-contact rows.
  - The tone is neutral throughout, with no green.
- **Contact and reported facts kept apart.**
  - `contactText` uses only `row.contact`, which comes from server receipt.
  - Queue and storage, and device contact, each have their own section headed "as last reported".
  - A closing notice says that none of this is a statement about equipment condition.
- **Battery.**
  - The detail page always shows "Unknown" with the named missing inputs. The NOT_CONFIGURED entry shows no asset ID.
  - The contract records 404 `ASSET_NOT_IN_EFFECTIVE_BASIS` (a foreign asset under KOBO-NB) and 422
    `INVALID_ASSET_ID`.
  - L6: `battery_boundary.py:109-113` raises on a mismatched binding set, and the API returns 409
    `FOUNDATION_BASIS_UNAVAILABLE` with `physical_condition: null`. The implementer showed the test is not vacuous,
    and it passes here.
- **Refusals carry no rows.** `healthClient.read` turns every non-200 answer into a typed refusal that keeps its status
  and code. A malformed 200 becomes a 502 refusal. The UI test asserts zero gateway rows and no summary for 404, 503,
  409, 401 and 403.
- **`?gateway=`.** The selection is in the URL, drives the selected panel and survives a remount. An unknown ID shows
  "No such gateway".
- **Rule 8.** There is no new SQL writer in `backend/assetops_backend`. The walkthrough's only SQL is admin
  `CREATE/DROP DATABASE` on a guarded `assetops_s701_owner*` name. It publishes through the S7-01a `HealthCases`
  authenticated path.
- **Deviations: all three judged acceptable.**
  - Leaving out the mock's reserve and stress counts, weekly chart, capacity-test action and warranty date is what
    the task requires: none has an accepted source, and the claims are withheld.
  - KOBO-NB is the recorded NOT_CONFIGURED Site, while the walkthrough uses KOBO-002 without a battery. All the states
    are covered: NO_BINDING_SET and NOT_CONFIGURED are recorded, and UNBOUND is derived.
  - The derived 409 body matches the shape the real handler returns in `source_health_api.py:68-71` (code, message,
    `gateways: null`). The UI maps it by code.
- **Walkthrough reachability.**
  - `prepare` builds the bindings before the case gateways (L1).
  - `deliver` refreshes all six `CURRENT_CONTACT_KEYS` (L4).
  - `attest` checks the stale-cadence case only after 60 s.
  - `serve` prints the exact URLs.
  - The owner steps state the window of about 2 minutes after `deliver`, and say to rerun `deliver` and reload if it
    is exceeded.

## Findings

1. **Low: an age computed from an implausible gateway time is shown in the default view without its reason.**
   - Where: `frontend/src/sites/SiteHealth.tsx:111`, and the queue table at `:386-388`.
   - When it happens: `reported_facts.status` is UNKNOWN with `OBSERVED_AFTER_RECEIPT`, but `observed_at <= read_at`.
     This is a later read of a gateway whose clock ran ahead without a measured offset.
   - What the user sees: the backend still states `fact_age_seconds`, and the UI renders
     "Unknown: observed N s ago" (the queue table shows "N s ago"). The reason appears only in Technical details.
   - The ruling only requires nulling for UNTRUSTED or for a time later than `read_at`, so this conforms. But the age
     comes from a time the read itself judges implausible.
   - **Fix:** when `status === "UNKNOWN"`, render `Unknown age: <reason>` whatever the age, or have `reported_age` also
     return None for `OBSERVED_AFTER_RECEIPT`. No recorded case covers this.
2. **Low: a signed `receipt_lag_seconds` is still emitted from an untrusted clock.**
   - Where: `backend/assetops_backend/evidence/source_health.py:258`. It is -90 for `s7-clock-offset` in the
     committed fixture.
   - The UI renders the lag only for OLD facts with a lag of 60 s or more, so nothing negative reaches the screen
     today. But the wire field goes against the intent of ruling L5 for any later consumer.
   - **Fix:** null it under UNTRUSTED or when it is negative, or mark the field diagnostic-only in the DTO.
3. **Low (presentation): exact IDs appear outside Technical details.**
   - The selected-gateway panel shows the Gateway ID, the Latest report ID and the report sequence epoch in the
     default view (`SiteHealth.tsx:474-490`).
   - Gateway external IDs head every table row and the panel heading.
   - The task asks the selection to show its report ID, so this follows the packet. Flag it for the W1-conclusion
     presentation pass, which could move the UUIDs into a disclosure.
4. **Low (test gap): the battery 409 `FOUNDATION_BASIS_UNAVAILABLE` is not exercised in the UI.**
   - `frontend/src/sites/__tests__/siteHealthBoundary.test.tsx` covers 404 and 422 on the detail page, but not the
     new L6 409.
   - `BATTERY_TEXTS` maps the code and the generic refusal path is tested, so the risk is small.
   - **Fix:** add a derived 409 case to the asset refusal table.

## Residual risk not named in the packet

- `isBatteryDetail` does not check that `physical_condition.status === "UNKNOWN"`. The UI hard-codes "Unknown", so a
  future status would fail closed, but silently. Revisit this when a condition other than Unknown becomes possible.
- I did not rerun the full frontend suite, the build, the layout evidence or the walkthrough (see Checks run).
