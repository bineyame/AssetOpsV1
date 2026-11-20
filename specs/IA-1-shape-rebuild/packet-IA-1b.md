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

## Fix round r1 (D-IA.31 to D-IA.35; review `review-IA-1b.md`; commit `e1b222ee9` and this one)
Merged `task/IA-1b-midbuild-answers` (rulings-2.md). Mid-build question Q1 is closed by D-IA.31. `index.html` rebuilt.
Built: `uxTabbable` and the Tab branch (D-IA.31); `iaQueueCap`/`iaCapMore`, `uxOverviewParts(op, rank)`, `uxSiteParts` (D-IA.34);
`uxSecA(open)` and `uxSiteParts(..., openFirst)` (D-IA.33); G1 reader `<owner>#details=<k>` (D-IA.32); `iaOutcomeScope`, scope
parser, "No Site in this scope has a target" (D-IA.35 L4); `ux-stack` class on the options and Outcomes tables (L5); register
R749 amended, R751, R752 (`.agent/mock-departure-register.md`).

### Results (final head)
- `ia_gates.cjs`: 42 runs, all as expected, 471 s (jsdom checks plus 27 plants).
- uxi (heavy slot, 484 s): **384 PASS, 0 FAIL** (was 359/1). New: every Overview drawer on all three operators, each press asserted;
  drawer trap sweep (lakeside 15, harvest 12, metro 10+ drawers across the four routes; Outcomes and Demand & capacity hold none,
  the per-operator total proves the set non-empty); drawer trap unlinked last; EV board on `#/portfolio/demand-and-capacity`.
- ia_shots 234 measured, 0 bad (184 s). G3 36 of 36. plan_switch 785/0. shell_check, design_lint, vocab, copy, hand_typed,
  render_text: 0 findings, script errors 0. `check_manifest.py`: 7571 passed, 1 failed (H9 baseline 4502; fixed on main by
  `d5af18b80`, not on this branch). `check-agent-workflow` passes; `check-architecture` fails here only on its environment
  (no `.venv`/ASSETOPS_GUARD_PYTHON for the chain-structure guard; rule 8 vacuity text), as on a worktree without a venv.
- Layout evidence: not run (needs a served URL; ports off limits). `ia_shots` measures.

### New plants (each fails; first failing line)
| plant | first failing line |
|---|---|
| UXI_PLANT=trap | `FAIL plant trap: drawer trap unlinked last: Tab press 3 left the drawer for button.` and `... overview drawer assure walk: Tab press 2 left the drawer for button.` (exit 1; 3 if either passed) |
| G1_PLANT=details | `edge reader: missing page -> page#details=0` |
| G1_PLANT=closed | `Lakeside Power · the plan: depth 2 > 1` |
| G1_PLANT=siteclosed | `Lakeside Power · Kobo largest driver against target (Candidate running): depth 4 > 3` |
| COUNT_PLANT=capsel | `Overview queue: waiting decision mto-losses is hidden by the cap` |
| COUNT_PLANT=capmore | `Overview queue: 6 rows shown + 0 on the line = 6, the heading counts 8` |
| COUNT_PLANT=adverse | `Outcomes: kobo column 5 reads "Generator needed −$38 ...", expected "Candidate running" and −$412` (demo Sites have two adverse drivers, so it bites) |
| PS_PLANT=resid | `metro ruiru Site page: "What is driving the gap" says "+$20 not attributed yet" (No measured driver moved the result)` |
| UXI_PLANT=evrev | `FAIL EV board: Metro ... has 0 Revenue row reading "charging is a cost centre" and "Not applicable"` |
| UXI_PLANT=expiry | drill-down, drivers and queue-primary FAIL on all three operators that have them (8 FAIL lines) |
| OUT_PLANT=headline | `live: the headline "3 of 3 Sites are below target in October" counts Sites outside the 1 rendered row(s)` |
| OUT_PLANT=scope | now rewrites `iaOutcomeScope`: `C: 12 rows at group:cold, expected the 7 cold Sites` |
| SHAPE_PLANT=foreignscope | `foreign scope: #/portfolio/outcomes?scope=group:cold renders 0 rows, expected 3` |
| SHOTS_PLANT=stack | `lakeside #/portfolio/outcomes 390x844 light: ... stacked table does not fit: table wider than its container` (6 bad) |
The jsdom plants are in `ia_gates.cjs`; trap, evrev, expiry, stack and resid are browser or heavy and were run by hand.

### G1 before D-IA.33 (the new reader, `G1_PLANT=siteclosed`)
Plan 1, every Site Overview 2, only the largest-driver surfaces moved (4, all Sites with a driver); nothing else past a limit.
After D-IA.33: plan 1, Site Overviews 2, every driver surface 3 (Kobo, Kisiwa, Mto, Mwea, Thika, Kirinyaga, Embakasi).

### Seen (own screenshots, scratchpad `own/`, 1440 and 390)
Mto Site Overview: "What is driving the gap" open with its board, six sections closed, queue shows 3 rows and "And 1 more: 1 awaiting
approval." Lakeside Overview: "And 2 more: 2 awaiting approval." Both read cleanly at 390. Note: at 390 the Overview's existing
phone CSS shows 3 queue rows of 6 (R749 phone rule), so the line's count refers to the rows beyond the six, not beyond the three seen.

### Known deviations (added)
- D-IA.34's line says "And N more" against the cap (6 or 3); the phone's CSS cut to 3 rows on the Overview is IA-2b's list work.
- D-IA.34's inbox opener on the line applies from IA-1c (coded behind `IA_LANDED.has('IA-1c')`, not exercised yet).
- The sweep's Outcomes and Demand & capacity routes have no drawer openers; the sweep asserts the per-operator total instead.
- Queued to IA-2b by D-IA.35 L5: the other wide data tables take `ux-stack`.


## Fix round r2 (M4: the phone queue cap)
- `ux.css`: the phone `nth-child(n+4)` rule on the Overview queue is dropped; the 6-row cap and "And N more" stand at every width (D-IA.34).
- `count_check` gains a 390 Chromium pass (3 operators x default and no-recommendation x Overview and each Site): rows on screen = capped rows,
  every waiting decision on screen or counted on a visible inbox line, "And N more" = what is off screen; non-empty set asserted
  (4 routes per run). Plant `COUNT_PLANT=phone` restores the rule: fails (Lakeside 3 of 6 on screen, "And 2" vs 5 off screen, mto-billing hidden;
  Metro 3 of 4, ruiru-connector hidden). It is added to `ia_gates` (43 runs). `count_check` now needs PW/CHROME (env.sh).
- `ux_interaction_check` phone line retargeted from "top 3, no View all" to "every capped row on screen, no View all"; plant `viewall` fails (3).
- Seen at 390: Lakeside Overview 6 rows + "And 2 more: 2 awaiting approval"; Metro 4 of 4 rows, 2 waiting visible.
- Main merged (d5af18b80). Results: ia_gates 43 runs all as expected (541 s); uxi 384 PASS 0 FAIL (534 s); ia_shots 234 / 0 bad;
  G3 36 of 36; check_manifest 7572 passed, 0 failed.
