# IA-1a packet: the frame and gates

Branch `task/IA-1a-frame` (worktree `/opt/assetecon/AssetOpsV1-ia1a`), off main `e0aedb86b`, main `f4b8923a7` merged in.
Module path: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/` (`ia-routes.js`, `ia-shapes.js`,
`ia.css`, `tools/ia_crawl.cjs`, `shape_check.cjs`, `click_depth_check.cjs`, `after_render_check.cjs`, `ia_gates.cjs`).
Evidence: `/opt/assetecon/evidence/IA-1/IA-1a/`. Mid-build questions: **0**. Packet named per spec §8 (`packet-IA-1a.md`), not `packet.md`, so the later units do not overwrite it. `USER_REVIEW_REQUIRED: true` (G2 stop is after IA-1c).

## Commits
- `1072bde12` frame, registry, render path, plan interim, the three checks and runner, retargets, r5 G1 and L-a gates.
- `ec8aa722c` merge of main (`f4b8923a7`: the three OD-6/A5 alignment fixes; without it `check_manifest.py` shows 4 baseline fails).
- branch head (this commit): `shape_check.cjs` (left out of the first commit by mistake), the L-a fix, the review-bar popover with its height held, the packet, spec status, built state.

## Done criteria
| Criterion (reviewer guide) | Result |
|---|---|
| 1 `plan` and `not-found` live in `IA_ROUTES`, rendered by `iaRender` | yes; `render()` goes through `iaRender` only for landed routes |
| 2 `ia_gates.cjs` passes, every plant fails | 13 runs, all as expected (table below) |
| 3 earned gates pass | see Checks |
| 4 copy §2.7 word for word | group, item, status, search, scope and footer labels as written; "Still to be rebuilt: …" sits in a review-bar popover (deviation 3) |
| 5 no unlanded destination reachable | rail items are unavailable roots; `iaUnlink` turns the plan's `decision/*`, `site/*` and the scope menu's Sites into text |
| 6 `planParts` byte-identical; Lab gate; Portfolio unavailable | 8 of 8 cases byte-identical; shape_check item 5; Portfolio is `IA-1b` |

## Gates and plants (`node tools/ia_gates.cjs`, 84.8 s)
| check · plant | expected | got | first line |
|---|---|---|---|
| shape_check · - | pass | pass | |
| click_depth_check · - | pass | pass | "G1: origin lands in IA-1b; 0 live surfaces" |
| after_render_check · - | pass | pass | 0 mutations on plan and not-found, 3 operators |
| shape · unlink | fail | fail | `#/plan links #/site/kobo (legacy or unknown)` |
| shape · stub | fail | fail | `#/plan links #/site/kisiwa/health` |
| shape · rail | fail | fail | `rail item "Portfolio" is not an unavailable root` |
| shape · palette | fail | fail | `#/plan links #/portfolio` |
| shape · primary | fail | fail | `2 primary buttons in one L1 region` |
| shape · lab | fail | fail | `the workspace footer shows with the switch off` |
| G1 · engine | fail | fail | `self-test: Plan at depth 2, expected 1` |
| AR · text | fail | fail | 17 mutations, `text "the calculation"` |
| AR · attr | fail | fail | `data-ar-plant on div` |
| AR · late | fail | fail | `children of h1` |
| r5 G1: uxi · `UXI_PLANT=container` | fail | fail | all 3 operators at 1440 and 1280; e.g. `row 830 px wide in a 646 px box; last cell ends at 1043, past its card at 883` |
| r5 L-a: uxi L6 clipping (real violation, before the fix) | fail | fail | `embakasi clipped "Monthly cost up $1,246 against Sep"` |
| plan_switch (changed assertion), plant: `iaUnlink` drops links | fail | fail | `the frame names every chosen item's decision (0)` ×3 |
| shell_check (S5 accepts a landed IA route), `SHELL_PLANT=1` | fail | fail | 138 fails, S5 among them |
| design_lint `LINT_PLANT=1` | fail | fail | |

G1 self-test (op · surface · depth): Outcomes 1, Plan 1, Decision A 1, Inbox 1, Decision B 2, Site 2, Driver drawer 3.

## Checks
Final build, branch head plus the last commit; logs in the evidence folder.
- `node tools/ia_gates.cjs`: 13 runs, all as expected, 81.6 s (`ia_gates.txt`).
- `ux_interaction_check.cjs` (heavy slot): 324 PASS, 0 FAIL, 398 s. Earlier runs on this branch failed L6 clipping (Embakasi) and, with the rebuild line shown in full, the first queue row at 1280 (harvest 724 px against a 720 px fold). Both are fixed (deviations 3 and 4).
- `shell_check` 0 fails (22 s); `plan_switch_check` 781 passed, 0 failed (135 s); `render_text` 0, `vocab_check` 0, `copy_check` 0, `hand_typed_scan.py` 0.
- `design_lint` exit 0; `LINT_PLANT=1` exit 1. `python3 ../check_manifest.py`: 7571 passed, 0 failed (after the merge of main).
- `planParts` byte-identity: 8 of 8 (Lakeside budget 5000/6500 × letter yes/no, Harvest aggregator yes/no, Metro tariff yes/no), `plan_parts_identity.txt`.
- Screenshots: 36 (plan and not-found × 3 operators × 1440/1280/390 × light/dark), 0 bad: frame present, top bar on one line at 1280 and 1440, no sideways scroll (`screenshots/`, `shots.txt`).
- `tools/check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON` set to main's `.venv`); `tools/check-agent-workflow.ps1` passed.
- layout evidence (`tools/layout-evidence.mjs`): not run. It needs a served base URL, and ports 5490 and 8990 are off limits. The screenshot script above measures the frame instead.

## Known deviations
1. `MOCK DEVIATION` (implementation, IA-1a): `uxStickyTick` writes its measured offsets to `--ux-sticky-left/top` on `<html>`, not inline on the bar. Inline styles would be a mutation inside the frame (D-IA.17). Same layout.
2. The primary rule compares `data-ux-act` (the reviewed buttons' attribute); the spec says `data-act`. The check reads either.
3. "Still to be rebuilt: …" is inside a review-bar popover (summary "Still to be rebuilt (12)"). Shown as a line, it wrapped the review bar and pushed the first queue row below the fold at 1280 on 5 legacy pages (uxi FAIL, then fixed).
4. r5 L-a: at 1280 the tile trend now wraps instead of an ellipsis. No copy changed; a shorter string would be new copy (spec §7).
5. The plan's H1 and subtitle are the reviewed plan screen's own (`The plan for November and December`); the spec names no title.
6. Branch name is `task/IA-1a-frame` as the dispatch says (the spec writes `task/ia-1a-frame`).
7. An empty hash still opens the legacy Portfolio. `iaStart()` is used by the gates only; the spec does not say otherwise.

## Not verified
- G1 live surfaces: none until IA-1b. `IA_G1_SURFACES` and the hub tab groups are IA-1b's.
- `audit.mjs` and `rendered_strings.cjs` were retargeted to `plan` but not run (the full audit was not scheduled).
- The reviewer's manual P3 (devtools observer) and P9 brand-pack sweep.
