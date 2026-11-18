# W5-01a C2 rebuild delta: independent re-review (C2b)

Reviewer: fresh Claude reviewer (did not author). Branch `task/W5-01a-cold-selected-depth`, worktree `AssetOpsV1-review2`, HEAD `e6ac07dd`.
Scope: commits `b84b9373`, `f6350739`, `e6ac07dd`, reviewed against "Codex retrospective of Claude Architect rulings (2026-10-22)" in `.agent/W5-01-build-spec.md` (Q-C2-2, Q-C2-3) and the ROLE_CONFIG rule "Both Architects ... against the v69 mock".

## Verdict: ACCEPT

There are no High or Medium findings. Two Low items should be fixed on the branch when C3 resumes; neither blocks this delta.

## Ruling-by-ruling check

**Q-C2-2 `Match` heading.** This matches the ruling. `ColdCooling.tsx` renders the third heading as the literal `Match`. Every cell shows a neutral `Not established` badge whatever the factor's Observed or Unknown state, and the Evidence column is unchanged. The page renders no `Matched`. `cooling_panels` asserts the heading, all five cells (in both the backup-failed fixture and the second fixture) and that no `\bMatched\b` appears.

**Q-C2-3 Recovery curves graphic.** This matches the ruling.
- File list. The delta touches `coldDepthGraphics.tsx` (new), `primitives.css`, `shell-overflow.ps1`, `ColdCooling.tsx` and `coldDepth.test.tsx`. These are the ruled additions plus existing C2 files. No C3 file is touched.
- Rule 5 registration. The diff adds `$coldDepthModule` as an svg owner, adds check 1f (the region selector must declare `overflow-x: auto|scroll`), requires the module to render the region (`$coldDepthRegionSeen`) and adds a non-vacuity check (`$coldDepthSvgSeen`). It mirrors the assessment-graphic pattern, and all existing allowlist checks are kept (the diff only adds lines). The packet records three mutation probes that each produced exactly one failure. I did not rerun those probes. The guard passes on the clean tree.
- Marks and labels. Marks are unconnected `<circle>` elements on the categorical lanes `Compressor running` and `Chamber temperature`. Each has an `HH:MM:SS` label and a `<title>`. The x axis is the selected window in 15-minute UTC ticks. There is no °C axis, no path, polyline or polygon, and no 36/42/+17% value; tests assert each of these. With no points, an empty frame is drawn and the selected-point table is omitted. `No accepted recovery sequence in this window.` is always shown, as the ruling requires for the W2 producer. No curve is invented.
- Against the v69 `cooling` mock. The panel slot, title, order and pairing with Context normalization are the same as the mock. The graphic sits at the top of the panel as the mock's line chart does, and the source table follows below it. The mock's two °C series and its legend are absent, as the selected-data limit requires (no numeric series). This is the closest form the selected data allows. The panel subtitle is still the earlier C2 copy, which is a prior ruling and not part of this delta.

**Recaptures (`evidence.json` at revision `f6350739`).** All eight recaptured pairs are within their caps, with `over_cap: []`, no overflow, no ellipsis and titles equal to the mock.

| Viewport | Measured | Cap |
| --- | --- | --- |
| 1440 | Recovery curves 402-417, Context normalization 402-417 | 470 |
| 1440 | Page 1217-1278 | 1600 |
| 390 | Recovery curves 251-464, Context normalization 466-490 | 500 |
| 390 | Page 2002-2222 | 2350 |
| 390 | Cards 261 | 360 |
| 390 | Status 99 | 140 |
| 390 | Notice 80 | 150 |
| 390 | State notice 43-61 | 150 |

I viewed limited 1440/390 and empty 390 alongside the mock 1440/390. At 390 the graphic's 480 px minimum width scrolls inside its region; the 20:00 tick is past the visible edge.

## The two implementer decisions

**(a) The `Match` badge wraps at 390 (`f6350739`). In spec, so there is no finding.** The C2 card says: "At 390, use actual `Not established` ... in the two-column cap test; wrap values/notes without ellipsis". The cap table fixes each panel at ≤500 at 390. Without the wrap the panel measured 513, which breaches the cap. The fix applies the card's own wrapping instruction. It is scoped to `.cold-cooling-context` under a 480 px media query, and it changes no copy, column or heading. It does make the badge render on two lines (`Not / established`) where the mock's shorter badges stay on one line. That follows from the ruled copy being longer than the mock's, not from an implementer redesign.

**(b) The "stale `coldDepth` test" fix. The assertion is in spec. The test name is not, which is a Low finding.** Q-C3-3 (on `main` as `998c5b75`, not yet merged into this branch) adds `coldDepth.test.tsx` to C3's Lane A list and rules the following.
- The last assertion, which the ruling gives literally as:
  `` expect(coldUiHref(`/api/sites/${SITE_CODE}/cold/health?${Q}`, routes)).toBe(`/sites/${SITE_CODE}/health?${Q}`); ``
  The branch has this line character-for-character, and the Cooling assertions are kept.
- The test name `coldUiHref maps the cooling and Health API links with their exact queries`. The branch has a different name.

The edit was also needed for this delta's own focused run to pass, because C3 (`a374e2d8`) had already mapped `health` on this branch.

## Findings

1. **Low: test name deviates from the Q-C3-3 literal.**
   - Where: `frontend/src/sites/__tests__/coldDepth.test.tsx:471`.
   - What: the branch reads `"coldUiHref maps the cooling API link with its exact query (and health, which C3 mapped)"`.
   - Fix: rename it to `"coldUiHref maps the cooling and Health API links with their exact queries"` after merging `main` (C3 rulings) into the branch. This is an acceptance gap against a literal ruling, not a preference.
2. **Low: the handoff misstates a measurement.**
   - Where: `.agent/W5-01a-phase-handoff.md`, C2 rebuild run entry.
   - What: it says "Context normalization is at most 478 at 390", but `evidence.json` records 490 for `cooling-empty` at 390. That is still under the 500 cap.
   - Fix: correct the number. This is packet accuracy only.

Residual items, not findings on this delta:
- The C3 registry reason for `cooling:1` is still `W5-01a selected first steps do not establish an ordered recovery curve.` (`v69-dependency-registry-pilot.json:469`). The retrospective asks C3 to describe the selected marks and the absent comparable curve. The C3-owned `cooling:2` reason still says the context rows "show Unknown", but the Match cells now read `Not established`. Both belong to the C3 builder.
- `.cold-depth-graphic__mark` hard-codes `#3d6fb0` and `#ffffff`, which are the same values as `--graphic-needed` and `--graphic-paper`. Using the tokens would be cleaner. This is a preference, not a defect.

## Checks I ran (worktree `AssetOpsV1-review2`, HEAD `e6ac07dd`)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | Passed. This includes shell-overflow with the new registration. |
| `tools/check-agent-workflow.ps1` | Passed. |
| `tools/check-all.ps1` | All 11 guards passed. |
| `npx.cmd tsc --noEmit` (frontend) | Exit 0. |
| `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` on `coldDepth.test.tsx` and `coldRoutes.test.tsx` | 2 files, 73 tests passed. |

Not verified by me:
- The wider adjacent set. The implementer reports 62 files and 1416 tests.
- The production build.
- Live recapture. Chrome, backend and Vite were not run; I judged the captures from `evidence.json` and the PNGs.
- The guard mutation probes.

I started no persistent processes.
