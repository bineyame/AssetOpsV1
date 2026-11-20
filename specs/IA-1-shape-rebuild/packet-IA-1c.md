# IA-1c packet: the decision shape and the "Waiting for you" inbox

Branch `task/IA-1c-decision` (worktree `/opt/assetecon/AssetOpsV1-ia1c`), off main `b817f9370`. Module path:
`Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/` (`ia-routes.js`, `ia-shapes.js`, `ia.css`, `loop-ux.js`,
`loop-site.js`, `tools/`). Evidence: `/opt/assetecon/evidence/IA-1/IA-1c/`. Mid-build questions: **1** (Q2, open, below).
Owner defaults applied: OQ-IA.1 (Choose on every decision, recorded under the decider), OQ-IA.2 (badge = "For you"), OQ-IA.3.
`USER_REVIEW_REQUIRED: true`: the G2 stop (the owner sees the hub and decision shapes before IA-2).

Commits: `a58b79f39` split (byte-identical, before any edit) · `70064f7cf` shape, inbox, act log, G1 surfaces, plants · `097d79ce6`
shots, uxi retargets, register R753, walkthrough · `b3dc66a0b` `6084674a9` `b5739046d` top bar at 390, 1280, 761-1199 · `1dc1762de` Q2 ·
`cb7f8454a` state, spec status, index · this commit: packet. Gates ran at `cb7f8454a`; `b5739046d` is CSS only (761-1199) and was reshot.

## Built
- `decision/:dec` (unit IA-1c, shape `decision`) for every `DEC` entry of the operator's Sites (15). `decisionParts(id)` and
  `uxDecisionSlots(id, parts)` split the reviewed page; `shapeDecisionPage` places sticky, L1 head + recommendation, L2 option cards,
  L3 the six sections, `[data-ia-drawers]` dialogs/Evidence/Actions/How. H1 question while waiting, subject once chosen; crumbs
  Decisions (text) › Site › subject; `home: 'Decisions'`, no rail item lights. `IA_LANDED` gains IA-1c, so decision links are live.
- Inbox: `iaForYou`, `iaInPortfolio`, `iaInboxControl` (top bar, between period chip and theme toggle), `iaInboxDrawer` (closed, after
  `.canvas`, opens in place). Badge on demo data: Lakeside 1, Harvest 1, Metro 2. "And N more" lines now carry "Open Waiting for you".
- `uxActDo` appends `{ key, op, by, at, toast }` to `uxMock().log` (newest first; Undo restores the state before, removing it).

## Gates (final head `cb7f8454a`; CSS-only commit `b5739046d` after it)
- `ia_gates.cjs`: **47 runs, landed IA-1a, IA-1b, IA-1c, all as expected (699.2 s)**. IA-1c plants, first failing lines:

| plant | first failing line |
|---|---|
| SHAPE decprimary | `Lakeside Power · #/decision/kisiwa-om: 2 primaries in one L1 region` (Harvest has no waiting decision: skipped) |
| SHAPE stickyact | `#/decision/kisiwa-om: a primary outside every level that is not the sticky repeat of the page primary` |
| G1 inbox | `Lakeside Power · waiting: Kisiwa late repair response and service credit: depth ∞ > 2` |
| COUNT foryou | `Lakeside Power (default) · the badge reads 0, expected 1` |

- `parts_identity.cjs` (base = main's build): **70 cases, 70 byte-identical** (planScreen 16, uxOverview 6, siteOverview 18,
  decisionScreen 30 = 15 decisions × default and no-recommendation). No sticky diff in this unit.
- uxi (heavy, 536 s): **384 PASS, 0 FAIL**. Retargets (P16): palette now expects "kobo gen" to find the live decision and "findings"
  (IA-2b) to find nothing; `UXI_PLANT=palette` fails (`"findings" finds "FindingsGo to"`). D-IA.35 L2: with IA-1c landed `TEXT_OK` is
  false; drill-down, drivers and queue-primary pass on the real links; plant `expiry` retired (it can no longer differ).
- count_check (in gates; also alone): PASS, the badge and both inbox row sets in 3 states × 3 operators; synthetic line now expects the
  opener (D-IA.34). G3 36 of 36 (clip, root fail). plan_switch 785/0. shell_check 0 (SHELL_PLANT fails). design_lint 0 (LINT_PLANT
  fails). vocab 0 (plant fails), copy 0, hand_typed 0. `check_manifest.py` 7572 passed, 0 failed. check-agent-workflow passes;
  check-architecture passes with `ASSETOPS_GUARD_PYTHON` = main's `.venv` (the worktree has none).
- ia_shots (final, at `b5739046d`): **342 measured, 0 bad** (hub, 15 decisions, inbox open, plan, not-found, width sweep). SHOTS_PLANT=headline: 54 bad of 108.
- P7 probe (`p7/`, script in scratch): **25 assertions, 0 failed**: Metro Ruiru expansion (stepper Recommended → Awaiting approval, badge
  2 → 1, row leaves For you, log row "… chosen Daniel · hh:mm", queue row choose → approval, Overview waiting 2 → 1); Lakeside Kisiwa
  late repair (badge stays 1, leaves In your portfolio, waiting 3 → 2); the plan approved on `#/plan` (badge 1 → 0); Undo restores each.
- Layout evidence (`tools/layout-evidence.mjs`): not run, needs a served URL and ports 5490/8990 are off limits; ia_shots measures.

## G1 (click_depth_check; all within limits)
| op | queue decisions (≤1, via queue) | waiting + plan (≤2, via inbox) | plan items' decisions (≤2) |
|---|---|---|---|
| Lakeside | 6 shown rows, all 1 | kisiwa-om, mto-billing, mto-losses, plan: 2 | 1 (3), 2 (kobo-battery, mto-inverter via the Protect drawer) |
| Harvest | 3, all 1 | plan: 2 (no waiting decision) | 3, all 1 |
| Metro | 4, all 1 | ruiru-expansion, ruiru-connector, plan: 2 | 2, all 1 |
Unchanged from IA-1b: plan 1, Site Overviews 2, largest-driver drawers 3 (Kasarani, Ruiru n/a). Plan-version Actions: unmeasured until IA-2b.

## render_text (P15)
89 of 237 renders differ from main: 74 gain the inbox control and drawer in the frame; the 15 decisions now render in the frame.
Demand & capacity keeps its two red marks (D-IA.29).

## Shots
`screenshots/` (decisions 90, inbox 18, hub 108, plan/not-found), `p7/` before and after Choose. Seen by me: decisions on three
operators at 1440, 1280×720 and 390, light and dark; the page body matches main to the pixel at 1440 (frame aside).

## Known deviations and findings
1. MOCK DEVIATION D5 → IA-2d: the inbox and every drawer have no address (R753). R750 note updated (links live).
2. Q2 (open): the decision's Site crumb, its only way to the Site (D-IA.26), is hidden at 390 and 1280×720 by the reviewed `ux.css`
   rule. Built as spec'd.
3. Pre-existing on main, not changed (reviewed code): under `?state=no-recommendation`, "See the options" (`#uxcards-<id>`) is routed
   as an address and shows not-found. Needs a ruling before the owner uses that preview.
4. Top bar: at 1280 the search box gives way (ellipsis); 761-1199 the right group may take a second row; below 1024 the inbox label is
   visually hidden as at 390 (spec names 390 only).
5. A decision's scope label reads "All sites" (spec silent; a Site page reads its Site).
6. `IA_G1_SURFACES` "plan items" are `planCase(op).ids` mapped through `DEC_SEE_ALSO`/`decOf`.


## Review fix round r1 (D-IA.36 to D-IA.40; review `review-IA-1c.md`, answers in `rulings-2.md`)
Merged `task/IA-1c-review-answers` and main (index-rulings-12 and INDEX.md conflicts resolved by keeping both sides). Built as ruled:
- **D-IA.36** `iaInPage(a)` plus one capture-phase click listener (`ia-routes.js`); `.ux-ocards{scroll-margin-top:var(--ia-sticky-h)}`, the var set
  by `iaInPage` from the sticky bar's measured height (the bar is only shown after the scroll, so it is measured by showing it briefly). shape_check
  item 11 (every `#<id>` link names an element, all states); uxi "in-page link" (Metro Ruiru connector, `?state=no-recommendation`, 1440 and 390).
- **D-IA.37** `iaFitTopbar` (`data-fit` 0..3, called at the end of `iaRender` after insertion and before the after-render guard observes, on resize and
  `fonts.ready`); the four width patches removed from `ia.css`; ia_shots sweep (761 to 1920, portfolio, plan, x-unknown, longest-Site decision) with
  one-row, past-window and truncation measures and `data-fit="0"` at 1440; register **R754** (`.agent/mock-departure-register.md`).
- **D-IA.38** `data-ia-crumbs="keep"` on `.canvas` for decision, record, asset shapes; CSS only; shape_check item 12; ia_shots Site-crumb measure.
- **D-IA.39** count_check acts through `uxActDo`, reads the act log after Choose and after Undo (the toast is read before navigation).
- **D-IA.40** `iaParamSite`; shape_check item 13 (scope text and lit entry on every `site/*` and `decision/*`).

### New plants (each run, first failing line)
| plant | first failing line |
|---|---|
| SHAPE anchor | `Lakeside Power · #/decision/kisiwa-om: in-page link "#nowhere" names no element on the page` |
| SHAPE sitecrumb | `#/decision/kisiwa-om: the crumbs are not "Decisions" (text), a link #/site/kisiwa reading "Kisiwa", then the subject (text text text)` |
| SHAPE decscope | `#/decision/kisiwa-om: the scope reads "Lakeside Power · All sites", not "Lakeside Power · Kisiwa"` |
| COUNT nolog | `Lakeside Power (after one act) · act log after Choose: 0 rows (none), expected one log:0 to #/decision/kisiwa-om` |
| UXI anchor | `FAIL in-page link at 1440: ... H1 "Page not found", focus on nothing ... not-found true` |
| SHOTS fit (sweep) | `BAD lakeside #/portfolio 761x800: ... top bar runs past the window (right)` |
| SHOTS truncate (sweep) | `BAD lakeside #/portfolio 1366x800: ... truncated control (ia-search-t 219 > 29)` (alone, at a width where the bar fits) |
| SHOTS crumbs (decision) | `BAD lakeside #/decision/kobo-generator 1280x720: ... the Site crumb is not shown` |
Final run at head, all through `tools/heavy-slot.sh`: uxi **386 PASS, 0 FAIL (530 s)**; count_check PASS (desktop jsdom and 390 Chromium); G3 36 of 36; plan_switch 785/0; shell_check, design_lint, vocab, copy, hand_typed 0 findings; render_text 237 renders, 0 script errors; check_manifest 7572 passed, 0 failed; after_render_check PASS (the fit runs before the guard observes).
`ia_gates.cjs` now lists anchor, sitecrumb, decscope and nolog under IA-1c: **51 runs, all as expected (764.8 s)**.

### Known deviation (superseded by the fix-round answer below): D-IA.37's own stop condition is hit
The ruled collapse (level 3, avatar hidden) does not fit below about 950 to 1000 px: the bar needs 760 px beside a 174 to 204 px rail and the
period chip alone is about 298 px, the scope switch about 200 px. Measured `data-fit` / overflow (X), lakeside portfolio: 761 to 934 3X,
960 3, 1000 2, 1024 1; Harvest needs about 1000; Metro and decisions about 934. `ia_shots` therefore reports **456 measured, 48 bad**, all
"top bar runs past the window" at 761, 800 and 900 (nothing else is bad: 1023 and up pass the sweep, the decisions, the crumbs). I did not tune a
width, gap or label (the ruling forbids it): **the round stops here for a ruling** (for example the period chip as an icon at level 3, or the
rail narrower, or the two-row bar below 1000). Looked at: the top bar at 761 (period chip clipped, inbox and theme off screen), 1024, 1280, 1440 (full
search); a decision at 390 and 1280x720 with its Site crumb visible (both fine).

## Fix-round answer (D-IA.41, D-IA.42; `rulings-2.md` "IA-1c fix-round answer")
Merged `task/IA-1c-topbar-answer`. Built as ruled: `data-fit` 4 (period as "October 2026"; ` · Figures as of ...` clipped in `.ia-period-asof`) and 5
(two rows, the phone's arrangement, used at every width below 761; the measure steps 0 to 4 and sets 5 without a test); `iaPeriodChip` and `iaPeriodHtml`
in `ia-shapes.js` (render_text unchanged; the period menu's current item reads "current period · Figures as of ...", at every level); search an icon at every
width (`data-fit` 5 overrides the ux.css hide at 600); R755 and R756 in the register; `--ia-sticky-h` from the shown bar's `bottom`, gap `var(--s2)`
(`ia.css`). `ia_gates.cjs` lists `AR_PLANT=fitlate` and `UXI_PLANT=stickyh` under IA-1c.
Measured changes beyond the ruled text (each needed for the ruled `rows` and `reach` clauses to hold; no width, gap or label tuned):
- Level 5: the period gets `flex:0 0 100%` (its own row, so "exactly two bands" holds at 600 to 760 and 761 up, where everything else would fit one row);
  its open menu is anchored `left:0` (it was right-anchored to a now left-hand chip and opened off the window); the "Ctrl K" hint hidden at 5 (it pushed the
  search to a row of its own at 390); the scope switch is `flex:1 1 0; min-width:0; max-width:max-content` instead of `flex:0 1 auto` (with `auto` the
  flex line wraps the theme toggle to a third row instead of shrinking the scope label, which wraps between words).
- `ia_shots` `tall` measure no longer applies to the scope switch at level 5 (its label wraps by ruling); `past` ignores the closed period menu's box and
  checks the left edge; `SHOTS_W=390,761` narrows the sweep for debugging.
- `SHOTS_PLANT=midword` uses `!important` on `overflow-wrap:anywhere` (the sheet's `[data-fit="5"]` rule outranks the ruled plain selector, so the plant would not bite).
- **`SHOTS_PLANT=longname` control departs from the ruled padding**: 240 px of padding alone leaves no form that fits at 390 (the padding is not breakable;
  it fails reach and tall at 390 to 800). The control sets the scope label to a long name made of words ("Lakeside Power · Kisiwa Generator and Fuel Depot,
  Northern Shore Extension") and skips `order` and `full` (content-dependent by design); `wrap`, `phonesearch`, `midword` use the ruled padding.

### Plants (first failing line)
| plant | first failing line |
|---|---|
| SHOTS wrap (sweep) | `BAD lakeside #/portfolio 390x800: ... top bar runs past the window (ux-pop ux-scope-sw); scope not reachable (reach); data-fit 5 but ... 3 row band(s)` (120 bad of 216) |
| SHOTS phonesearch | `BAD lakeside #/portfolio 390x800: ... search not reachable (reach)` (24 bad) |
| SHOTS midword | `BAD lakeside #/portfolio 390x800: ... the scope label breaks inside a word ... (anywhere/normal/clip) (midword)` |
| SHOTS asof | `BAD lakeside #/portfolio 390x800: ... the period menu's current item lacks "Figures as of 06:00, 6 Nov" (asof)` (12 bad: 3 operators x 1440 and 390 x 4 rows) |
| SHOTS longname (control) | pass: `ia_shots` sweep 216 measured, 0 bad (exit 0) |
| AR fitlate, UXI stickyh | AR fitlate: `Lakeside Power · #/plan: 1 mutation(s) after insertion: data-fit on header` (ia_gates); UXI stickyh: `FAIL in-page link at 1440: ... options heading at 8 px (sticky bar bottom 39)` (run with its path arguments, outside ia_gates: the check needs the page path) |

### Final run at head (all through `tools/heavy-slot.sh`, light machine)
`node build.mjs` ok; `ia_gates` **52 runs, all as expected, 0 BAD (797 s)** (incl. `after_render_check` fitlate; the uxi stickyh plant was dropped from `ia_gates`
because `ux_interaction_check` needs the page path argument and crashed with exit 1, a false "fail"); `ia_shots` full **504 measured, 0 bad (422 s)**
(the inbox-open runs skip `reach`: the drawer's scrim covers the bar by design); uxi **386 PASS, 0 FAIL (532 s)**; count_check PASS; G3 36 of 36 (clip 24 of 36
and root fail); plan_switch 785/0; shell_check 0; design_lint 0; render_text ok; vocab 0; copy 0; hand_typed 0; check_manifest ok.
Looked at the top bar myself at 390, 761, 800, 900, 1024, 1280, 1440 (Metro; 390 and 761 re-looked for Harvest after the scope fix): level 5 two rows at 390 and 761,
level 4 (period "October 2026", search icon with its hint) at 800 and 900, level 1 at 1024 and 1280, level 0 at 1440. The "Figures as of" sentence shows in the bar from 1024 up and in the period menu at every width.
