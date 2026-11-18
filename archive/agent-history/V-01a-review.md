# V-01a review: Site and Foundation visual fidelity (fresh Claude reviewer)

This review was produced by a fresh Claude reviewer that did not author V-01a.

**Scope:** branch `task/V-01a-foundation-visual`, diff `575430f..caf2077` (`1c6c4d1`, `b5a3979`, `caf2077`), against `tasks/V-01a-foundation-visual-fidelity.md`, the V-01 umbrella, and the W1 panels `sites:1`, `foundation:1-3`, `readiness:1` and `sld:1-2`.

## Verdict

**Accept with findings fixed on the branch.** The product changes are small, correct and truthful:

- The `?at=` address-instant option.
- The devices caption.
- The panel sub-lines and the bus rating.
- The Readiness separation sentence.

One finding blocks the owner's visual check. The walkthrough and packet call a scheduled period "current", so the owner's links and the evidence screenshots never show the configuration that is actually in effect. Fixing it is a labelling change. Three carries follow.

**Ready for the owner's visual check:** not yet. It will be once B1 is fixed (relabel, and add the in-effect-now route and screenshot). With B1 fixed, the screens themselves are fit for the owner to judge.

## Checks I ran (results as observed)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `tools/check-all.ps1` | all 6 guards passed (ledger: 110 screens, 258 panels) |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npm.cmd test` (frontend) | **ran in this session**: 55 files, 1326 tests passed |
| `pytest backend/tests -q -x` | 1771 passed, 127 skipped (the slice does not touch the backend) |
| `v01a_foundation_walkthrough.py prepare` / `serve`, plus two dev servers on 5360/5361 | worked; isolated trees from `caf2077` |
| `node tools/v01a-foundation-evidence.mjs http://localhost:5360 <scratch> http://localhost:5361` | **50/50**, exit 0 |
| `node tools/layout-evidence.mjs http://localhost:5360 KOBO-001` | 200 PASS, 0 FAIL, then stopped at the known Lab precondition (`fuel-loss-event/run-setup` submit disabled). The packet records this honestly as stopped, not as a pass. |
| Own CDP probe (scratchpad, not in the repo) | period selector at no `?at=`, at a period start, at an inside instant and at a malformed `?at=`; narrow parts-table geometry; Tab order on the SLD |

**Not run:** `npm.cmd run build`. I did not rerun the production build. `tsc` and vitest are verified; vite bundling is not.

**Not re-verified:** the non-vacuity revert proofs (42/50 and 1 failed of 43). I did not repeat the reverts. The test and the evidence claims read as discriminating, because they assert the absence of "In effect now" and of "none has reported".

**Cleanup:** I compared the screenshots myself (app and mock, 1440 and 390, sites, foundation, readiness and sld). All my processes are stopped, and ports 8860, 8861, 5360, 5361, 9361 and 9377 are free. The owner's listeners (5183, 5199, 5213, 5291) were not touched, and nothing was written to `var/`.

## What I confirmed

- **Period-selector fix.** With no `?at=`, the selector shows "In effect now" and the strip shows "This is the configuration in effect now." (v10).
  - At a period start (`?at=2026-10-21T00:00:00Z`), the matching v13 option is selected.
  - At an inside instant (`?at=2026-09-30T00:00:00Z`), the selector shows "At 2026-09-30 00:00 UTC (from the address)". The strip says "Historical period … v3". The page never falls back to "In effect now".
  - Reload and the Enter subtab switch keep the instant (evidence tool).
  - A malformed `?at=garbage` renders "No stored version for this period". That handling is pre-existing and upstream, as the packet says.
- **Devices caption.** It is now consistent: configured assets, and reporting is not assessed here. The test asserts that "none has reported" is absent.
- **Readiness (PRE-S3-04).** The sub-line separates configuration readiness from claim readiness and operational status.
  - The page footer still says that operational status (contact, credentials, data received, accepted evidence) is not assessed here.
  - The gateway copy is "registered… whether it has made contact or sent data is not assessed here".
  - The badges stay neutral. No health word appears.
- **No mock values used as data.** The app shows stored values: 45 % reserve, 400 V bus, 60/50 kW, v13/v12. The mock's 30 % SOC, 35 %/90 % thresholds, MG-DEMO-01, Online/100 %/95 % and the KPI tiles do not appear.
- **Per-panel table.** The rows for `sites:1`, `foundation:1-3`, `readiness:1` and `sld:2` match what renders, including the identity rows, the topology bus label and the "No channel declared" row for the AC bus.
- **Keyboard.** Tab order on the SLD runs from the top bar to the breadcrumb, the view tabs, the subtabs, "Configuration readiness →" and then the period select. The subtab focus is visible, and Enter keeps `?at=`.
- **`Panel.description`.** It is additive: it renders only when the prop is given. Vitest (1326) covers the S1-S4 screens and shows no regression, and layout evidence covers the Site and Foundation views before the Lab stop.

## Findings

### B1 (block for the owner check): the "current period" walkthrough and evidence show a scheduled period, never the period in effect

- **Where:**
  - `tools/v01a_foundation_walkthrough.py:47-53`: `PERIODS`, labelled "Current period (21 Oct 2026 onward)" → `2026-10-22T00:00:00Z`. The comment says each value is the "valid_from of each stored period".
  - `.agent/V-01a-owner-walkthrough.md` steps 2, 4 and 5.
  - `.agent/V-01a-review-packet.md`, "States covered: … Foundation current".
  - `tools/v01a-foundation-evidence.mjs`, which uses the same instant for every populated screenshot.
- **What is wrong:**
  - Today is 2026-10-12. At `?at=2026-10-22`, the app correctly shows Foundation v13 with "Scheduled period: … This is not the configuration in effect now." The period actually in effect is v10 (2026-10-03 to 2026-10-21), which the no-`?at=` route shows.
  - None of the five instants is a stored `valid_from` (v3 starts 2026-09-29T11:57:49Z, v13 starts 2026-10-21T00:00:00Z, and so on). Each one exercises the "from the address" option.
- **Why it matters:**
  - The owner would open a link labelled "Current period" and see a page that says it is not current.
  - Every populated app screenshot, and the readiness and SLD pairs, is of a scheduled period. The default in-effect-now state, which is the route a user lands on, has no app/mock pair.
  - The packet's claim that "Foundation current" is covered is therefore inaccurate.
  - The labels are also time-dependent: after 21 Oct, v13 does become current.
- **Fix:**
  - Relabel the instant as the scheduled v13 period, or derive the labels from `/foundation/versions`.
  - Add the no-`?at=` route ("In effect now", v10) as the first walkthrough link and as an evidence-tool screenshot state at both widths.
  - Correct the comment, the guide steps and the packet's "States covered".
- **Class:** acceptance-record and owner-guide accuracy, not product behaviour.

### C1 (carry): the SLD introduction still says "no reading has arrived"

- **Where:** `frontend/src/sites/SiteSingleLineDiagram.tsx:91-96` (`SITE_SLD_INTRODUCTION`), on `sld:1`.
- **What is wrong:** it is unconditional copy, "a picture of the configuration … - no reading has arrived, and every value slot on it is empty." On the same page, V-01a's new panel sub-line ("not reporting status") and the fixed devices caption ("whether any of them is reporting is not assessed here") decline to make that claim.
- **Why it matters:** it is the same class of statement the Architect sent to V-01a for the devices caption, and the view does not read Evidence to back it. In this walkthrough DB it happens to be harmless, because Evidence is `AWAITING_EVIDENCE_MIGRATION`. On a Site with central evidence it would be false.
- **Why carry, not block:** it is pre-existing T016 copy. The "Awaiting runtime/evidence" slot vocabulary was accepted under T016. The Architect's V-01a mandate named only the devices caption.
- **Fix:** change "no reading has arrived" to "whether any reading has arrived is not assessed here". Optionally have the Architect rule on the slot label. Route to the Architect or the truthfulness sweep.

### C2 (carry): at 390 px the `sld:2` Channels column and its caption sit off-screen in a horizontal scroll region

- **Measured:** the table is 433 px wide inside a 309 px `overflow-x: auto` region. The Channels header starts at x≈370 px. The caption scrolls with the table, so its text is clipped mid-sentence in the 390 screenshot.
- **Why it matters:** the column carries `sld:2`'s supported claim (bound channels per part). The packet's accepted differences mention only that the drawing scrolls at 390.
- **Fix:** record it as an accepted narrow-width difference in the per-panel table. Alternatively, move the caption outside the scroll region, or stack the rows at narrow width (a layout change, so layout evidence must be rerun).

### C3 (carry, minor): the packet's screenshot list overstates the evidence

- **What is wrong:** the packet lists "SLD current and imported period" as captured states. The tool writes only one SLD pair per width, at the scheduled 22 Oct instant. The imported-period SLD is measured as a binding-set difference but is not screenshotted.
- **Fix:** say "measured" rather than "captured", or add the screenshot. This can be folded into the B1 fix.

## Q1-Q5 defaults (honest and safe?)

| Question | Judgement |
| --- | --- |
| Q1: keep the grid SLD | Honest. It draws the same declared parts and connections. A redraw would be a separate intrinsic-geometry task. |
| Q2: view as h1 | Honest and consistent with S2-S4. |
| Q3: neutral readiness tones | Safe. Green/amber would read as operational status, against PRE-S3-04. |
| Q4: channels-per-part stability | A reasonable reading. It is measured, and it discriminates between periods. It adds no unsupported selection state. |
| Q5: text-only cards | Cosmetic and honest. |

## Residual risk not named in the packet

- The walkthrough and evidence instants are tied to the calendar. After 2026-10-21 the "scheduled" period becomes current, and the strip wording the owner sees will change.
- A `?at=` that names a period start in a different format (for example `+00:00` instead of `Z`) misses `selectable.has` and shows the "from the address" option instead of the period row. This is truthful but redundant, and cosmetic.
- `npm.cmd run build` was not rerun by this reviewer.
