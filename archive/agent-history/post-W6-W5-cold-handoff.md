# Handoff: post-W6 W5-cold-Work (COMPLETE: all steps done, see packet "Completion")

Branch `task/post-W6-W5-cold-work`, last build commit 363008e1. Packet: `.agent/post-W6-W5-cold-packet.md`.

## What remains
1. **After W2-cold merges, merge main in, then build R339.**
   - Import `coldTabSearch` from `shell/coldSiteRoutes.tsx`. It is W2-cold's helper.
   - Add `search={coldTabSearch(site, params)}` (a `useSearchParams` param) to these mounts:
     - The SAF Financials > Scenarios `<OperatorSiteTabs current="Financials" />`, main ~:1301 (W4 also edits this line; re-anchor).
     - The SAF Work mounts for Actions (main ~:2002 and the domain Actions frame tab row) and cases (~:2250).
     - Cold-health is already done by W2-cold (`SiteHealthFrames.tsx:71`); verify only.
     - Cooling uses `ColdPerformanceFrame`'s `coldWindowSearch(window)` (W2-cold SAF:292); verify only.
   - Tests go in `coldRoutes.test.tsx` or `operatorSiteTabs.test.tsx`:
     - Each of the four screens' tab hrefs carries `from`/`to`/`known_at`.
     - A bare Work URL gives bare tabs.
     - Mini and EV are unchanged.
   - Revert-prove each test, then mark R339 in the register.
2. **After W4 merges**, confirm the `status-tone--*` CSS styles the B14-04 classes in `ColdCooling.tsx`. `coldDepth.test.tsx` already asserts the classes.
3. **Unit 5, when the coordinator clears captures:**
   - All 116 pairs for cold-work, cooling, cold-health, cold-scenarios and cold-action at 1440 and 390.
   - R338 regression pairs: cold-work-incidents/maintenance defaults, ev-work and ev-work-*, and the mini sitework-incidents/maintenance defaults.
   - After W4, one 390 cold Site tab row.
   - Caps: apply as in pre-flight C9.
   - Update `tools/w502-cold-work-evidence.mjs` claims if any expect Retry on a cold 403/422.
   - Record the SHA, producer, pinned clock and gaps. The gaps are R344's VERIFICATION_WINDOW (unreachable) and linked CANCELLED (no producer mode).
4. Then run the full vitest, build and guards on the final SHA, and set the register rows to closed with the capture refs.

## Open risks
- The R338 shared default changes EV and mini defaults (ruling 1). Regression captures are required.
- B15-04: the EV refusal path is untouched because `refusal` is optional and absent in `EV_ACTION_PRESENTATION`. W5-EV follows in this file.
