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
