# S7-01b review packet - Site Health and battery boundary UI

Task `tasks/S7-01b-health-ui.md`; branch `task/S7-01b-health-ui` from main `f3de235a`, which already contains S7-01a. USER_REVIEW_REQUIRED: true. The slice goes to review first, then the owner walkthrough `.agent/S7-01b-owner-walkthrough.md`, then merge. Reviewer diff: `git diff f3de235a..HEAD -- ':!.agent'`.

## Outcome

- **Site Health** at `/sites/{site}/health`. The Health tab is now enabled.
  - The status strip is labelled "Gateway contact" and gives the enabled-gateway count. Disabled gateways are shown as "N disabled, not counted".
  - Separately qualified sections follow, in v69 `#/health` order: Battery condition; Gateway contact (server receipt against the declared interval); Queue and storage, as last reported; Device contact reported by gateways.
  - A closing notice says that contact is not equipment condition.
  - Technical details are closed by default and hold the IDs, rule, snapshot, watermark digest and reason codes.
  - `?gateway=<gateway id>` selects one gateway. The selection shows its latest report ID and sequence, and it survives reload.
- **Battery** pages:
  - `/sites/{site}/assets` is the entry. It lists the configured battery, or shows "No battery configured" with no asset ID.
  - `/sites/{site}/assets/{asset id}` is the detail page. Condition is Unknown, with the three named missing inputs. The declared rating is labelled "not a measurement". State of charge is "Not shown". Signal channels show as connected, none, or not set up. Withheld items are listed. Asset, Foundation, channel-set and channel revision IDs are in disclosures.
  - An asset ID outside the effective basis returns a typed refusal (404) and no condition row. An invalid ID returns 422. A 401, 403, 409 or 503 is a typed refusal that keeps its HTTP status and code.
- **S7-01a backend follow-up** (`D-2026-10-16-s701-clock`):
  - Separate constants `CLOCK_OFFSET_LIMIT_MS` and `OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS`, both 5000 ms and inclusive. The second is now disclosed in the read as `clock.observed_after_receipt_allowance_ms`.
  - `summary.reason` is `NO_ENABLED_GATEWAY` or `NO_REGISTERED_GATEWAY`.
  - Ages are null under an UNTRUSTED clock, and for any time later than `read_at`.
  - Review L6 is done: a binding set that names another Foundation revision returns 409 `FOUNDATION_BASIS_UNAVAILABLE`.
- **Walkthrough** `tools/s701_health_walkthrough.py prepare|serve|links|deliver|attest|drop` (review L1 and L4):
  - It uses a private DB.
  - It creates the KOBO-001 bindings before registering the case gateways.
  - `deliver` refreshes all six cases meant to read CURRENT.
  - `attest` asserts the stale-cadence case only after 60 s.
  - KOBO-002 is a second Site built from the Kobo file without its battery.
  - `serve` prints the exact URLs.

## Files materially changed

- Backend:
  - `backend/assetops_backend/evidence/source_health.py`
  - `backend/assetops_backend/sites/battery_boundary.py`
  - `backend/assetops_backend/asset_boundary_api.py`
  - `backend/tests/s7_health_cases.py`
- Backend tests:
  - `test_s7_source_health_rules.py` (new, pure)
  - `test_s7_source_health_postgres.py`
  - `test_s7_asset_boundary_postgres.py`
  - `test_s7_health_contract_postgres.py` (new) plus the fixture `backend/tests/fixtures/s7_health_api_contract.json` (new; the committed wire contract the UI tests read)
- Frontend (new):
  - `src/sites/healthClient.ts`
  - `src/sites/SiteHealth.tsx`
  - `src/sites/SiteBattery.tsx`
  - `src/shell/SiteHealthFrames.tsx`
  - `src/sites/__tests__/siteHealthBoundary.test.tsx`
- Frontend (changed):
  - `src/shell/operatorSiteRoutes.ts`
  - `operatorSiteTabs.tsx` (Health enabled)
  - `App.tsx`
  - `SiteAnalyticsFrames.tsx` (`SiteScoped` exported)
  - `src/test/settled.ts` (two loading sentences)
  - `src/ui/primitives.css`
  - the tab inventories in `operatorSiteTabs.test.tsx`, `siteDetailRoute.test.tsx` and `overflowContainment.test.tsx`
- Tools:
  - `tools/s701_health_walkthrough.py` (new)
  - `tools/s701-health-evidence.mjs` (new)
  - `tools/layout-evidence.mjs` (the tab claims now include Health)

## Acceptance criteria

| Criterion (task / rulings) | Status |
| --- | --- |
| Six central cases, never received, no source, wrong Site/asset, store failure in the UI | Met: recorded contract cases in `siteHealthBoundary.test.tsx`; 401, 403 and 409 are derived and named in the test |
| Stale projection only if S7-01a has a derived projection | Met by absence: the read has `stale_projection.applicable=false`, and a test asserts no "projection" text |
| Contact beside reported-fact time/age; source contact only if supplied; queue, clock and disk as last reported; IDs, receipt, `read_at`, watermark | Met. The default view keeps plain language; exact values are in Technical details and the selected-gateway panel |
| Summary labelled "Gateway contact" with enabled count; never Site/equipment health; DISABLED shown and not counted | Met (tests and evidence) |
| Unknown age plus clock reason, never a signed age | Met: backend nulls the ages; UI and evidence assert there is no `-N s` text |
| Battery UNKNOWN with named missing inputs, or NOT_CONFIGURED; SOC and rating kept separate; no replacement/warranty/life claim | Met |
| Asset route by configured asset ID; out-of-basis ID refused | Met: 404 KOBO-001 asset under KOBO-NB/KOBO-002; 422 invalid |
| Reload, exact links, keyboard, Back preserve selection | Met: jsdom tests plus browser evidence (Enter key on Details, reload, `history.back`) |
| 1440/390 | Met: `s701-health-evidence.mjs` 40/40 (no sideways scroll measured over 66-512 elements per page) |
| Backend follow-up: constants, `summary.reason`, nulled ages, L6 | Met; each guard proven non-vacuous (below) |
| Walkthrough `prepare|serve|deliver|attest|drop`, own DB, bindings before gateways, deliver all CURRENT cases, attest stale after 60 s, second Site with printed URLs | Met: run end to end, `attest: ok` |

## Checks run

- **Focused backend tests** on the private `s701b_impl_test` DB:
  - `test_s7_source_health_rules.py`, `test_s7_source_health_postgres.py` and `test_s7_asset_boundary_postgres.py`: 21 passed.
  - `test_s7_health_contract_postgres.py`: 1 passed, and identical across two regenerations.
- **Non-vacuous proofs**, each on a committed tree and reverted with `git checkout`:
  - Removing the L6 check fails `test_binding_set_of_another_foundation_revision_is_refused`.
  - Removing the UNTRUSTED/future guard in `reported_age` and the `summary.reason` fails two rule tests.
- **Frontend**: `npx.cmd tsc --noEmit` is clean. The focused files pass: `siteHealthBoundary.test.tsx` 13/13, plus the tab tests.
- **Full `npm.cmd test`**: 1623 passed, 1 failed (1624).
  - The failure was `siteFoundationChange.test.tsx`: "Unable to find ... heading 'Battery reserve change'" after 2978 ms. That is a load timeout in an S6 file this slice did not touch.
  - Rerun alone: 8/8 passed.
  - The earlier full run, before the tab-inventory fix, had failed only on the two Health tab lists, which are now updated.
- **Guards**: `tools/check-all.ps1` passes 9/9, with `ASSETOPS_GUARD_PYTHON` set to the main venv. The dependency registry checker (`check_v69_dependency_registry.cjs`) passes.
  - A first run caught `site-substrate` (src/sites importing shell routes). It was fixed by having the frames supply `HealthLinksContext`.
- **Full backend suite** (one run, at revision `e1294d16`; code is unchanged since then, and later commits touch only the evidence script and docs):
  - Command: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q -p no:cacheprovider --junitxml=<abs>`, on the private `s701b_impl_test` DB, with keep-awake running and no other pytest process.
  - Result: **2540 passed** in 1303.99 s (21:43; cap 30 min).
  - JUnit: tests 2540, failures 0, errors 0, skipped 0.
- **Browser evidence** `node tools/s701-health-evidence.mjs http://127.0.0.1:5447`, run right after `deliver`: 40/40 claims at 1440 and 390, with 8 app and 4 mock screenshots and `comparison.md`. It was found and fixed in this slice that a visually hidden column header widened the 390 page to 632 px.
- **`tools/layout-evidence.mjs`** against the walkthrough store: 206 PASS and 28 FAIL.
  - Every failure is a store precondition of that generic tool: no legacy file Kobo, no configured-diagram Site, no fuel-tank Lab Site, and Site tab rows that do not render for the sites it picks on this private store.
  - The tool's tab claims were updated for Health. They remain **unverified** by this tool on its intended store; the Health tab itself is measured by the S7 evidence.
- **Owner walkthrough**: run end to end once (prepare, serve, dev server on 5447, deliver, attest, evidence, drop). The final rerun at `5a56e1b7`..`c3e0c542` used code identical to `e1294d16`:
  - `attest: ok`, with stale-cadence STALE asserted 78 s after its receipt.
  - Evidence: 40/40 claims.
  - The evidence script gained two fixes in that rerun. It asserts the stale-cadence case only after 60 s (as `attest` does), and it waits for the battery link after Back (a race).
  - The fixture DB, work folder, copied `var/sites` and the test DB were all dropped afterwards.

## Known deviations

1. **Mockup fidelity.** v69 `#/asset` shows illustrative reserve and power-stress counts, a weekly chart, a capacity-test action and a warranty date. None of these has an accepted source in W1, so they are deliberately not rendered (the task withholds them).
   - v69 `#/health`'s three-asset table becomes one battery row, because the read is battery-only.
   - The mock's "Data sources" table becomes the gateway contact, queue and device sections.
   - The plain-language and visual pass is carried to the W1-conclusion fidelity task, per the owner direction.
2. **The KOBO-002 test case.** The recorded contract's KOBO-002 has a configured battery whose channels are not set up (`NO_BINDING_SET`; an unconverted import). The walkthrough's KOBO-002 has no battery (`NOT_CONFIGURED`).
   - The UI tests cover NOT_CONFIGURED with the recorded `KOBO-NB`, and UNBOUND with a derived case.
3. **The 409 shape.** The read's 409 for an inconsistent selection is derived in the UI test rather than recorded, because S7-01a builds it only through a patched store.

## Residual risk

- Code has not changed since the frontend full suite and `check-all` ran (`1e71ddeb`). The later commits change only the evidence script and docs.

- Contact ages on screen are computed at read time, while the page itself does not refresh. A reload gives current ages.
- On the real clock, cases go stale about 120 s after `deliver`. The owner steps say so.
- The vite dev server started through Git Bash exited (code 127) twice during evidence runs. Run from PowerShell, as the owner steps say, it stayed up.

## User-review focus

Check that the wording reads as gateway contact, not equipment health. Check that "Unknown" is shown with its reasons on both screens. Check that the mock's illustrative numbers are acceptable to omit until real sources exist.

## Carried to W1-UX-05 (from S7-01b review, 2026-10-16)

- L1: an `OBSERVED_AFTER_RECEIPT` gateway still shows "observed N s ago"; show Unknown age with the reason in the default reading (`SiteHealth.tsx:111,386-388`).
- L2: the read sends a negative `receipt_lag_seconds` from an untrusted clock (`source_health.py:258`); null it.
- L3: gateway/report IDs in the selected-gateway panel move to technical details (`SiteHealth.tsx:474-490`).
- L4: add a UI test for the battery 409 `FOUNDATION_BASIS_UNAVAILABLE`; `isBatteryDetail` should check condition is UNKNOWN.
