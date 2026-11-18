# W1-UX-05 review: Foundation, Readiness, SLD, Health and battery presentation

Reviewer: a fresh, independent Claude reviewer. I did not author this slice and did not edit it.
Revision: `35c1adf1` (detached, worktree `AssetOpsV1-gap-planning`), base `815888f0`.
Diff: `git diff 815888f0..35c1adf1 -- ':!.agent'` (26 files). The changes after `af9b6406` are docs only, so the implementer's full-suite run at `af9b6406` covers the code under review.

## Verdict: ACCEPT

I found no High or Medium findings. The eight Lows below do not block the merge. Finding 1 must be fixed before anyone relies on 390 px measurements in the combined W1 walkthrough.

## Honest state: what I checked

- **Unknown, stale, refused and not configured never read as positive.**
  - No new `ProductWords` uses `positive`. Foundation period words are `neutral`, `waiting` or `limited`. Set-up readiness, Health contact and battery condition are the same.
  - Codes the screen does not recognise fall back to `limited` with `UNRECOGNISED_SENTENCE`.
  - See `foundationHeadlines.tsx:39-127` and `healthHeadlines.tsx:31-126,243-262`.
- **Commissioning confirmed.** It is always `not-known` ("Not recorded here", `foundationHeadlines.tsx:294-298`). The headline always adds "commissioning is not yet confirmed".
- **Set up to report.** It is `neutral` and says it "does not mean any device is connected, reporting or healthy" (`foundationHeadlines.tsx:91-99`). The test asserts the tone (`siteFoundationRevision.test.tsx:2121`).
- **Reporting now.** It is passed as `value: null` (`foundationHeadlines.tsx:394`). `ValueBars` draws that as a hatched "not known" mark, never a fill. Tested at `siteFoundationRevision.test.tsx:2172-2175`.
- **Fresh contact with old facts.** It is in the attention list: `contact !== CURRENT || factAgeUnknown || reported_facts.status !== CURRENT` (`healthHeadlines.tsx:162-164`). Tested with `s7-delayed-old` showing "in contact; its latest report is old".
- **Battery condition is never judged.**
  - The headline is fixed: "Battery condition: cannot yet be judged".
  - `isBatteryDetail` now refuses any condition other than UNKNOWN (`healthClient.ts:211-213`), so a "GOOD" value becomes a refusal panel, not a card. This is tested.
  - No remaining life, warranty or replacement wording appears.
- **The state line stays outside the closed panel.**
  - `ProductStatus` renders in the card's status slot, before the visual and outside `ExactReferences`.
  - `expectStateLineVisible` runs on every card state tested.
  - Refusals and the unreadable store have no read instant. They use a local equivalent that checks the same visibility (`siteHealthBoundary.test.tsx:410-421`).

**Changed test assertions.** I diffed every removed line in the four test files. All are wording-only renames with the same selector, role and count:

- binding → channel link
- PV array / Load → Solar array / Supplied users
- Minimum generator runtime → Shortest generator operation
- Critical-load priority → Critical service order
- claim readiness → what the readings can support
- claims → says
- firmware "runs" → "has installed": same gap ID and placement

One assertion changed source as well as wording. `siteFoundationRevision.test.tsx:327` used to check the backend sentence and now checks the frontend constant that replaces it. That is still an exact full-sentence match, and the next two assertions (`data-readiness-state` UNKNOWN, registration-is-not-contact) are unchanged.

`siteHealthBoundary.test.tsx` is purely additive apart from one import. No fail-closed assertion was removed or loosened: "Not bound", "Unknown until bound", not-current, refusal, pending-gateway and no-healthy all remain. I confirm the packet's claim.

## Findings

1. **Low (blocks the combined walkthrough evidence): the 390 px measurements in `w1-ux-01-evidence.mjs` and `w1-ux-05-evidence.mjs` cannot fail. Treat every "narrow" measured claim as not established.**
   - **Where.** `tools/w1-ux-05-evidence.mjs:98-101,130,141,186`, which is identical to `tools/w1-ux-01-evidence.mjs:98-101,130,141,186`. I diffed lines 90-145 of both and they match.
   - **What is wrong.**
     - The claim is `scrollWidth <= clientWidth && wide.length === 0`. It never checks that `clientWidth` is near the requested width.
     - The UX-05 run recorded `clientWidth` 1425 at both widths. That is 1440 minus a 15 px classic scrollbar, so the page was laid out at desktop width when measured.
     - A mobile 390 override would show about 390 with no scrollbar. So the measurement ran without the override in effect.
     - `shot()` reapplies the override immediately before capture, which explains why the PNGs are 390 px wide.
   - **Consequence.**
     - Every measured "narrow" claim was effectively taken at desktop width: no sideways scroll, state and as-of boxes drawn, and Tab reach.
     - UX-01's packet records "390 scrollWidth = clientWidth" as met but gives no value. It ran the same code, so that pass is unproven: not shown false, but not evidence.
     - UX-05 records this honestly ("not established by measurement", visual check only), so it is not a packet-integrity finding against this slice.
   - **Fix, in the shared script pattern (UX-01 owner or coordinator):**
     - After `size(width, height)` and `go(...)`, wait with `waitFor(\`window.innerWidth === ${width} && document.documentElement.clientWidth <= ${width}\`)`.
     - Add a claim that records `innerWidth` and `clientWidth` and fails unless `clientWidth` is within `[width - 20, width]`. Measure only after that claim passes.
     - If the override still does not hold for the measurement, run each width in its own Chrome launched with `--window-size=<width>,<height>`, or use `Browser.getWindowForTarget` with `Browser.setWindowBounds`. Then capture with the override kept equal to that window size.
     - Rerun the narrow pass for UX-01 and UX-05, or have the coordinator's combined-walkthrough captures replace both.
     - `tools/v01a-foundation-evidence.mjs` uses the same `size()` pattern. Check its narrow `vw` readings too.

2. **Low: the shared helper `expectStateLineVisible` rejects the honest missing bound.**
   - **Where.** `frontend/src/test/productPresentation.ts` (`toMatch(/^As of /)`) against `frontend/src/ui/productWords.ts:399-402`. `asOfText(null)` returns "As of: time not recorded".
   - **Which side changes: the helper.** "As of: time not recorded" is the honest output for a read with no instant (refusals, an unreadable store) and must not become a time or "now".
   - **Fix.**
     - Change the helper to `/^As of (?:\d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2} UTC|: time not recorded)$/`.
     - Make the same change to the regex in the evidence scripts (`w1-ux-0x-evidence.mjs:184`).
     - Then replace UX-05's local `expectRefusedStateLine` (`siteHealthBoundary.test.tsx:410-421`) with the shared helper.
   - **Owner.** This is a UX-01 shared file, so the UX-01 owner or a W1 cleanup slice makes the change, not this branch.

3. **Low: the S1 "Ready to report" green badge under the neutral card.**
   - **Where.** `FoundationBindingsPanel.tsx:31-47,163`: `READINESS_WORD.READY_TO_REPORT = "Ready to report"`, tone `configured`, a green tint with a check mark.
   - **No semantic contradiction.**
     - The panel description says it is distinct from contact and from what the readings can support.
     - The verdict sentence is configuration-only.
     - The card directly above says "Set up to report … does not mean any device is connected, reporting or healthy".
   - **Where it is weak.** The same state carries two names a few lines apart, and one of them, "Ready to report" with a green check, reads more positively than the card allows.
   - **Recommendation.** Rename the badge to "Set up to report" in the W1 plain-language batch. That changes an S1-owned test, so route it through the Architect. The configured tone can stay.

4. **Low: Readiness shows "Gateway registered: Done" while contact is stale.**
   - **Where.** `foundationHeadlines.tsx:289-293`.
   - **Not misleading as worded.** The step is labelled "Gateway registered" with the detail "Registered; contact is reported below". The meaning block points contact and reporting to Health. The Gateway status panel below shows the stale contact.
   - **The gap.** The strip title "From configuration to confirmed reporting" invites reading the strip as progress toward reporting, and the card itself never surfaces stale contact.
   - **Recommendation for the owner walkthrough.** Either retitle the strip so it does not promise reporting (for example "Set-up steps"), or add a contact line when the gateway-health read is available. The card currently has no gateway-health input. This is not an acceptance gap: the packet asked for set-up, not contact.

5. **Low: two fallback headlines can sound positive when the code is not recognised.**
   - **Readiness.** When `readiness.state` is not recognised and no roles, gaps or gateways are missing, the headline reads "Nothing is missing from the set-up…" and "Readings linked" is `done` (`foundationHeadlines.tsx:286,312-317`). The state line beside it does say "Set-up state not recognised".
   - **Health.** When `summary.status` is not recognised and no gateway is enabled, the headline reads "All 0 enabled gateways are in contact and their latest reports are recent" (`healthHeadlines.tsx:165-169`).
   - **How likely.** Both are defensive edges the backend should not produce.
   - **Fix.** Branch the headline on `words.unrecognised`, and on `enabled.length === 0`, to a non-positive sentence.

6. **Low: the selected gateway's own state line says "In contact" for a gateway with old facts.**
   - **Where.** `SiteHealth.tsx:476-480`, using `gatewayContactWords`.
   - **What is wrong.** The scope says "contact" and the fact list beside it says the report is old. The panel's state line, though, does not carry the "needs attention" the headline list gives this gateway.
   - **Recommendation.** Have the line say "In contact; its latest report is old", or add a `next` that does.

7. **Low: S7-01b L2 is deferred correctly but must be tracked.**
   - **Where.** `backend/assetops_backend/evidence/source_health.py:258` sends `_seconds(d.received_at - d.observed_at)`, which goes negative under an untrusted clock.
   - **No frontend exposure.**
     - `SiteHealth.tsx:107` shows a lag only when it is 60 s or more.
     - An untrusted clock or an `OBSERVED_AFTER_RECEIPT` reason returns "Unknown age" before the lag is reached (`SiteHealth.tsx:104`).
     - No other frontend site renders the field.
   - **Fix.** A backend task nulls a negative `receipt_lag_seconds` (or nulls it whenever `trust == "UNTRUSTED"`) and adds a contract-fixture test. It is listed only in CODE_STATE "Open", so put it in the queue.

8. **Low: the backend "binding" sentences replaced on screen.**
   - **Where.** `FoundationBindingsPanel.tsx:96-101,196,271,372-374`.
   - **I checked the three replacements against the backend.**
     - `foundation_api.py:340-343` (NONE state)
     - `binding_service.py:773-775` (readiness statement)
     - `binding_service.py:935-939` (snapshot reason)
   - **Each is meaning-preserving.** It keeps "every role is unbound", "readiness is Unknown" and "operational status is not assessed". Each is keyed on the same condition the backend uses: no binding set, or `binding_set_revision_id === null`.
   - **Residual risk.** If the backend changes what it says in that condition, the UI will mask it.
   - **Fix.** Reword the backend sentences into product words, then remove the frontend overrides. Not needed for this merge.

No wording-preference findings are raised.

## Checks I ran (worktree `35c1adf1`, PowerShell)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run` on the seven focused files below | 7 files, **273 passed**, 0 failed, 57 s |
| `tools/check-agent-workflow.ps1` | passed |
| `tools/check-architecture.ps1` | First run failed, for the environment only: Rule 8 found no `.venv` in this worktree. Rerun with `ASSETOPS_GUARD_PYTHON` set to the main repo `.venv` python: **passed**. |
| `node frontend/docs/architecture/check_v69_dependency_registry.cjs` | exit 0 |

The seven files in the focused run:
- `siteFoundationRevision.test.tsx`
- `foundationScreen.test.tsx`
- `siteConfiguration.test.tsx`
- `siteHealthBoundary.test.tsx`
- `w1Vocabulary.test.tsx`
- `sharedVisualVocabulary.test.tsx`
- `t028Vocabulary.test.tsx`

Vitest ran under this sandbox, unlike the known esbuild denial.

## Not verified by me

- **The full frontend suite.** The implementer reported 1755 passed in 154 s at `af9b6406`. I cite it because the code there is identical to the code under review.
- **`npm.cmd run build`.**
- **`tools/check-all.ps1` guards beyond the architecture and workflow checks.**
- **The served 1440/390 captures and keyboard reach.** These need Chrome, the walkthrough DBs and a dev server, so I did not run them. As finding 1 shows, the recorded "narrow" measurements are desktop-width measurements.
- **The 390 px layout.** Only the implementer's visual inspection of the 390 px PNGs supports it.
- **Backend.** No backend code changed, so I ran nothing.

## Residual risk not named in the packet

- The narrow-width claims for keyboard reach and for state-line boxes being drawn are as unproven as the overflow claim (finding 1), not just the overflow claim the packet names.
- The `aria-labelledby` targets for SLD parts are `<text display="none">` elements (`SiteSingleLineDiagram.tsx` `SldNodeName`). Directly referenced hidden nodes do count toward the accessible name, and jsdom tests pass. Real screen-reader output was not checked.
