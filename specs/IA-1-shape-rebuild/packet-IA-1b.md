# IA-1b packet: the hub shape

Branch `task/IA-1b-hub` (worktree `/opt/assetecon/AssetOpsV1-ia1b`), off main `eb11251e9`. Module path:
`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/` (`ia-routes.js`, `ia-shapes.js`, `ia.css`, `loop-ux.js`,
`loop-site.js`, `loop-core.js`, `tools/`). Evidence: `/opt/assetecon/evidence/IA-1/IA-1b/`. Mid-build questions: **1** (Q1).
Owner defaults OQ-IA.1/OQ-IA.2 touch IA-1c only. `USER_REVIEW_REQUIRED: true` (G2 stop after IA-1c).

Commits: `772bcf002` parts splits (byte-identical, before the fix) · `8e833ac72` hub, sticky fix, IA-1b gates and plants ·
`0ce2745cc` earned-gate retargets, walkthrough, register R748-R750 · `76e86ac84` Site scope label, `data-ia-to`, uxi
retargets, Q1 · this commit: packet, state, spec status.

## Gates (`node tools/ia_gates.cjs`: 34 runs, landed IA-1a, IA-1b, all as expected, 321.6 s)
Unplanted pass: shape_check, click_depth_check, after_render_check, count_check, outcomes_table_check. Every plant fails:
IA-1a's 15 (unlink, stub, rail, palette, primary [now two distinct acts], lab, tabstop, notfound, noact [host `plan`],
lablegacy, G1 engine, AR text/attr/late/replace) and IA-1b's 15, first lines:
| plant | first failing line |
|---|---|
| shape selflink / aliaskey / crossop | `a self-link in L2` / `alias key "portfolio/outcomes" matches the route` / `#/site/mwea shows site/mwea, not not-found` |
| shape linkprimary / landing | `2 primaries in one L2 region` / `the empty hash renders portfolio (the legacy screen, outside the frame)` |
| G1 tile / driver / hidden | `the plan: depth ∞ > 1` / `Kobo largest driver …: depth ∞` / `a link inside a closed drawer read as a step (page -> fixture-b)` |
| count choose | `(no-recommendation) Outcomes: kisiwa "Waiting for a choice" reads 0, expected 1` |
| outcomes cap / group / scope / sort / notarget | `12 rows shown` / `group heads ""` / `12 rows at group:cold` / order unsorted / `no-target Site not last` |

## Other checks (final build)
- `parts_identity.cjs`: 40 cases (planScreen 16, uxOverview 6, siteOverview 18; default and `?state=no-recommendation`):
  before the fix 40 byte-identical (`parts_identity_split.txt`); after it 37 identical, 3 "sticky only", 0 differ. The one diff
  (no-recommendation, Kisiwa; Mto and Ruiru likewise): the sticky's `<a class="button primary" href="#/decision/kisiwa-om">Decide</a>`
  is gone, since no `choose` row is shown.
- uxi (heavy slot, 444 s): **359 PASS, 1 FAIL**: "overview drawer assure" (Q1). Plants fail: block7 (7 blocks), tall (2,525 px),
  viewall (`3 / link`), palette ("kobo gen" finds the decision), x5 (`uxi_plant_x5.txt`).
- Overview budget at 1440: Lakeside 5 blocks, 1,944 px; Harvest 5, 1,521 px; Metro 5, 1,587 px.
- G3 36 of 36; G3_PLANT=clip 24 of 36, root 0 of 36. ia_shots (hub) 108 measured, 0 bad; SHOTS_PLANT=headline 54 bad.
- shell_check (on `ia_crawl`) 0 fails, SHELL_PLANT=1 fails (S1-S4) · plan_switch 781/0 · vocab 0 (a planted hit fails) · copy 0 ·
  design_lint 0, LINT_PLANT=1 fails · hand_typed 0 · check-architecture and check-agent-workflow pass.
- `check_manifest.py`: 7571 passed, **1 failed** (H9 baseline 4502 against 4501). main `eb11251e9` fails identically; not this unit's.
- layout evidence (`tools/layout-evidence.mjs`): not run; it needs a served URL and ports 5490/8990 are off limits. ia_shots measures.

## G1 (click_depth_check; all within limits)
| op | plan | Site Overviews | largest-driver drawer |
|---|---|---|---|
| Lakeside | 1 (portfolio › plan) | Kobo, Kisiwa, Mto 2 (› Outcomes › Site) | Kobo, Kisiwa ("Necessary running"), Mto 3 (› opener) |
| Harvest | 1 | Mwea, Thika, Kirinyaga 2 | Mwea, Thika, Kirinyaga 3 |
| Metro | 1 | Embakasi, Kasarani, Ruiru 2 | Embakasi 3; Kasarani, Ruiru n/a (no driver against target) |
The plan-version Actions surface is unmeasured until IA-2b (D-IA.29).

## render_text differences (P15)
79 of 237 renders differ, all from routing: the four hub routes render in the frame; other operators' `site/*` and their stubs
show not-found under Lakeside (D-IA.28); `mini` and `outcomes-by-site` resolve to their aliases. `render_text.cjs` now judges
"loop" on the rendered screen (`#/cold` under Lakeside switched the operator first). Demand & capacity keeps its two red marks
(welding hour bar `bad`, `capBars` `over`; D-IA.29).

## Screenshots
`screenshots/` (108: 6 hub routes × 3 operators × 1440/1280/390 × light/dark), `compare-main-1440/` (main against the branch).
Seen: layout identical; Site pages are about 80 px shorter (top-3 queue); decision links read as text until IA-1c.

## Known deviations
1. MOCK DEVIATION D2: "More in the tabs" dropped (R748). D5 → IA-2b: no "Act first ›" or "View all" (R749); rows keep "Why"
   and the action link (R750).
2. Q1 open: the Assure drawer's focus trap fails once "Open Scope & coverage" is unlinked; the trap is reviewed code.
3. Retargets with no plant of their own: uxi drill-down/drivers/queue-primary accept `iaUnlink`'s text form (`data-ia-to`) until
   IA-1c; uxi EV board and plan_switch residual read their legacy builders (`#/ev`, `outcomes-by-site` are now aliases).
4. The old Outcomes-by-site residual column is on no live route; Ruiru's unattributed amount stays on the Overview gap tile.
5. Scope filters Outcomes only; the Overview is unchanged by it (spec silent). A Site page's scope label reads that Site.
6. Portfolio and Site subtitles are the legacy screens' own; Outcomes and Demand & capacity have none.
7. `#/mini|cold|ev` with no such group stays legacy (D-IA.28); the legacy page switches the operator.
