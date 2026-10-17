# W2-01 re-review - cold Foundation, readiness and SLD (after fix rounds 1-2)

Reviewer: a fresh, independent Claude reviewer who did not author the work. Revision `ae2d9686`. W2-01 fix diff `acea3bda..ae2d9686` without `.agent`, with the main-side files of merge `81f62703` set aside using `81f62703^2..81f62703`. Prior review: `.agent/W2-01-review.md` (RETURN).

## Verdict: ACCEPT

H1 and M2 are fixed. The contact mapping matches `D-2026-10-17-f5-subtabs-and-contact`. The merge kept both sides. No High or Medium finding remains. The three Lows below do not block.

## Prior findings

- **H1 (SLD), fixed.**
  - `cold-sld:1` is now the bus-bar SLD: a vertical "Backup AC bus" bar, with the grid meter and generator feeding the transfer switch and the switch feeding the bar. The compressor, cold room and chamber probe sit to the right of the bar. The drawing uses component icons.
  - Names wrap with no ellipsis ("Automatic transfer / switch", "Chamber temperature / probe").
  - The Monitoring strip has one box per binding, each with a hollow "Reporting not assessed here" marker and no reporting dot.
  - At 1440, panel 1 is 709 px against the mock's 702.
  - At 390 the drawing is scaled to fit, like the mock's, with no sideways scroll (`cold-sld-stocked-390-app.png`).
  - The missing breakers are honest (no protection is declared; deviation 7).
  - Tests: bar, icons, wrapped names, no "…", strip count and markers, plus a lane-layout unit test.
- **M2 (390 density), fixed.**
  - The parts table shows only the role, and "Function description not recorded" appears exactly once (asserted).
  - Readiness rows at 390 are about 2 lines.
  - Pages at 390 are 1.27-1.35x the mock (about 1.24x net of the shell rail). The mock's readiness table also scrolls sideways inside its panel at 390.
  - **The 9 readiness rows are honest data, not a cut.**
    - Each row is a real `cold-roles-1` area with its own declared state, such as the manual log "Needs a source / Optional".
    - The mock's 4 rows are illustrative. Collapsing to 4 would hide configured or missing facts.
    - Panel 1 is about 2.1x the mock at 1440, but each row is one line apart from the site row, and the page stays within budget. This is acceptable.
- **Low 3, fixed.** The manual log has its own row. The test asserts that no Configured row says "No source".
- **Low 5, fixed (deviation 9 accepted).** An empty track labelled "No history to draw" sits with the mock's legend plus "No history".
  - The text is a plain, true statement and claims nothing.
  - "Not available yet" would need a catalogued `MissingClaim` placement, and C5 pins `G-readiness-gateway-uptime` to exactly one placement. Withdrawing the registry edit was the right call.
  - The Architect may add a cold placement later.
- **Low 4, fixed by the ruling.** See finding 1.

## Contact ruling check

- Backend:
  - No health store maps to `NEVER`, `as_of:null`, "No gateway health read is configured".
  - A selected gateway with no matching fact maps to `NEVER` with "No diagnostic is recorded for the selected gateway".
  - No gateway selected or none registered gets its own limitation.
  - A health-read error stays a 503 `GATEWAY_ACCESS_UNAVAILABLE`.
  - This matches the design text. Both named cases (missing store and unmatched) are asserted at the API level: enum, null `as_of`, limitation.
- UI: the four wordings are distinct, and "Never contacted" is gone. Tests cover missing-store, unmatched, and the empty-health COLD-002 case.

## Findings (all Low, non-blocking)

1. **Low - the no-gateway-selected and no-gateway-registered backend branches have no test.** `backend/assetops_backend/cold_foundation_api.py:96-97`.
   - The branch is two lines, both outcomes are distinct constants, and the UI mapping for both is tested. It does not block.
   - **Fix:** in `test_w201_cold_foundation_postgres.py`, add one API case per branch: a Site with no binding set and two registered gateways (selected), and a Site with zero gateways (registered). It can be a test-local fixture variant. Assert `{"state":"NEVER","as_of":null,"limitations":[<constant>]}`.
2. **Low - the UI's no-gateway override can contradict the backend.** `frontend/src/sites/ColdFoundationViews.tsx:111` (with `gatewayName` at `:212-217`).
   - `gateway === NO_GATEWAY_SELECTED` is true whenever the frontend `/gateway-health` read is empty, refused or unavailable. In that case the status says "No gateway selected / No particular gateway is checked for contact", even when the cold read reports a selected gateway (limitation `No diagnostic...`, or `[]` for a registered gateway without a diagnostic).
   - This is the deviation 2 title fallback, now carried into the status card. In the seeded app every cold fixture has a registered gateway (the COLD-002 capture is titled `edge-cold-002`), so the packet's note "COLD-002 ... now reads 'No gateway selected'" holds only for the unit fixture (`healthOf([])`), not for the live app.
   - **Fix:** drive the status only from `contact.limitations`, and drop `|| gateway === NO_GATEWAY_SELECTED`. If the health read failed, have `gatewayName` return a distinct "Gateway not read" title rather than "No gateway selected". Then correct the packet note.
3. **Low - the COLD-002 and stocked readiness captures predate round 2.** `.agent/W2-01-evidence/cold-readiness-*-app.png` still show "Never contacted". With the current code, the live app shows "No contact received yet" for both fixtures, since the registered gateway has no diagnostic.
   - **Fix:** recapture the readiness pairs at the final revision before the owner walkthrough. The layout is unaffected.

## Regression checks

- The state line is said once: in the statusbar, with the table footnote explaining it.
- Each panel or nested panel has one "How this was worked out".
- No raw IDs or enums appear in default copy. The gateway external ID appears only through the approved `cold-readiness:2` title rule.
- No Configured/No source contradiction remains.
- Test diffs only add or tighten assertions. The two replaced assertions became stronger negative and positive checks.
- The mini-grid is unchanged:
  - The `SiteSingleLineDiagram`/`componentIcons` changes against main add the cold path and widen types only.
  - The mini-grid archetype table is untouched.
  - The registry and `gapCatalogue` net diff for the fix round is empty.
- **The merge is correct.** `81f62703^2..81f62703` touches only W2-01 files.
  - `v69PanelTitles.ts` keeps F2's `evidence-analysis:2` and adds the two cold rules.
  - `V69Layout.tsx` keeps all the F2 descriptions and adds the three cold ones.

## Checks I ran

The worktree was at `ae2d9686`, with the main venv python, `PYTHONPATH` set to the worktree roots and `ASSETOPS_GUARD_PYTHON` set.

- `pytest backend/tests/test_w201_cold_vocabulary.py backend/tests/test_w201_cold_foundation_postgres.py -q`, serially, on the private DB `w201rerev_test` at 127.0.0.1:55432 (created, then dropped): **44 passed** in 181 s.
- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run src/sites/__tests__/coldFoundation.test.tsx`: **23 passed**.

## Not verified

- The full frontend suite was not rerun. The implementer recorded 2010 passed at `9e892d7a`.
- The full backend suite was not rerun. The coordinator recorded 2649/2651 at `a4e4cb10`, with 2 load flakes that passed alone. Round 2's backend contact change is covered only by the focused run.
- The capture tool was not rerun. I judged the committed pairs.
