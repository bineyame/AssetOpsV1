# IA-2b1 packet: the list shape (in review)

**Complete: units 1 to 4 built; the flip at `c80539d53` (`IA_LANDED` gains IA-2b1). No stop line.** Branch `task/IA-2b1-lists`
(worktree `/opt/assetecon/AssetOpsV1-ia2b1`), not merged. Module path: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/`.
Spec: `spec-IA-2b.md` (rev 2; `spec.md` §0, §6 to §8 apply). Evidence: `/opt/assetecon/evidence/IA-2b1/` (`unit3/`, `unit4/`, `fin/`).
Mid-build questions: **8** (`mid-build-questions.md` § IA-2b1), plus one recorded existing issue. `USER_REVIEW_REQUIRED: true` (UI).

Commits: `7f785dab8`, `51dbb41bb` unit 1 (checks, dormant) · `c5480c05b` unit 2 (`qty_check` modes) · `8b0543c7e` unit 3 (component, not
live) · `21de38a42` 4(a) defs, routes, Outcomes fold, crumbs, search, register R775-R779, walkthroughs §6 · `c80539d53` 4(b) the flip ·
`3ec99d53f` `notarget` plant · `b4ea6c7c9` `ia_shots` S1-S9 and the 760 px wrap rule · `8b7bf29ee` the `ux_interaction_check` retarget (see Gates).

## Built
- Four home lists (Decisions, Findings, Actions, Sites) from one def table (`IA_LIST_DEFS`) and one component (`shapeList`,
  `iaListModel`, tiers, chips, tools). `iaListRestore`, registered after the router, keeps the control's place. The Outcomes tab draws the
  Sites list's rows (`iaOutcomeTable` deleted). act-first and the Findings aliases resolve to the lists with their queries. The Decisions
  and Sites crumbs link. The rail units are renamed and the search index has the lists.
- **Layout fixes in `ia_shots` (b4ea6c7c9), two rules at `max-width:760px`, scoped to `.ia-list`:** the stacked row title wraps
  (the global `th{white-space:nowrap}`), and the state pill wraps (its `nowrap`). Without them, 51 of 255 list shots fail the
  390 stacked-fit check, e.g. `cell "Litres used 1,180 agains" 679 > 332` (`fin/shots-nocss.log`, run on a scratch build without the rule).

## Live list counts (jsdom, `fin/list-counts.txt`; no list is over 10, so no live "Show all")
| Operator | List | Tiles | Rows | Controls | Targets (several rows to one) |
|---|---|---|---|---|---|
| Lakeside | Decisions | 8 · Waiting for a choice 3 | 8 | sort | 8 |
| Lakeside | Findings | 9 · Decision waiting 3 | 9 | sort | 8 (kobo-generator ×2) |
| Lakeside | Actions | 6 · Released 2 · Waiting 4 | 6 | sort | 4 (kobo-generator ×2, mto-inverter ×2) |
| Lakeside | Sites | 3 · Below target 3 · Gap −$852 | 3 | sort | 3 |
| Harvest | Decisions / Findings / Actions / Sites | 3·0 / 4·0 / 3·1·2 / 3·3·−$770 | 3/4/3/3 | sort | 3/3 (mwea-occupancy ×2)/3/3 |
| Metro | Decisions / Findings / Actions / Sites | 4·2 / 7·3 / 2·1·1 / 3·Over 1·−$3,184 | 4/7/2/3 | sort; Actions none | 4/4 (embakasi-schedule ×3, ruiru-expansion ×2)/2/3 |

Tiers live: 1 (sort) everywhere except Metro Actions (2 rows, tier 0). The 30-Site and 25-decision fixtures cover tier 2 and "Show all".
`qty_check`: count keys 7 (`decisions:n:`, `decisions:waiting:`, `findings:n:`, `findings:waiting:`, `actions:n:`, `sites:n:`,
`sites:below:`); format key 1 (`sites:gap:`); deferred to IA-2e: 1 key (`plan-spend`, 72 screens). `EQUAL` sites gap = Overview gap
on 18 scenarios. Live cents fallbacks: **0** (expected 0).

## Gates
- **Full gate** `node tools/ia_gates.cjs` (heavy slot) at `b4ea6c7c9`, 5545 s: `ia_gates: 108 runs, landed IA-1a, IA-1b, IA-1c, IA-2a,
  IA-2b1, 1 BAD (5544.2 s)` (`fin/ia_gates.log`). 97 of 97 plants fail; 10 of 11 checks pass. The BAD: `ux_interaction_check` failed
  unplanted. It measured the reviewed act-first screen, which is now an alias of `#/decisions`, and it expected "findings" to find nothing
  live. Fixed in the next commit with the same in-window alias removal as `plan_switch_check` (Q6). The rerun of its rows is in
  `fin/ia_gates-uxi.log` (`GATES_ONLY=ux_interaction_check` at `8b7bf29ee`, a partial run of its 3 rows, 1889 s with a slot wait): the check passes, and `planans` and `planwait` fail; the runner printed `all as expected`.
- Every 2b1 plant fails in the gate, with a line only the plant produces (baseline 0). The unit 4 table is in
  `/opt/assetecon/evidence/IA-2b1/unit4/plants/SUMMARY.txt`; the counts are planted-only failure lines:
  `list_shape_check` tile 1 · restore 189 · scopemenu 15 · remainder 2 · rowctl 111 · own 37 · stakesort 40 · cap 5 · keep 4 · scope 2 ·
  search 1 · sort 7 · invalid 1 · group 6 · canon 1 · tier 5. **notarget: 21** (`list_notarget_v2.txt`, after `3ec99d53f`; the
  SUMMARY's "proved no" row is the earlier plant, which threw before the target assertion). `shape_check` deccrumb 2 · aliasq 9;
  `click_depth_check` listrail 6; `copy_check` list 15; `qty_check` counts 9 · tilecount 15 · sitegap 18 · listcents 24 · gapnet 12.
- Real violations, each made, failing, then reverted (patches in `plants/viol_*`): item 15 self link (12) · copy "Due day" (15) · qty
  Released +1 (18) · Outcomes button in a row (42) · Outcomes sort=name (12).
- **`ia_shots` list set (`SHOTS_ONLY=lists`, b4ea6c7c9; not part of `ia_gates`, which never runs `ia_shots`):** 255 shots + 9 class
  lines, 0 bad (`unit4/shots/shots.log`): S1 72 · S2 72 · S3 24 · S4 24 · S5 24 · S6 14 · S7 2 · S8 20 · S9 3; 255 tile rows
  measured. S9 Lakeside `#/decisions` sort: place skipped (the control's top is 352 px at scroll 0, above half the viewport), focus
  asserted; the two sites30 cases measure place (422 → 422). Plants (`shots-plant-*.log`): **listkeep** S9 3 of 3 bad (top 422 → 436,
  focus lost) · **listwrap** S8 10 of 20 bad at 390 (`select[name=target] 88 px, its own width 144`), S9 2 · **emptytools** S4 24 of 24 bad.
- Other checks: fast check-all `All 42 guards passed (blocking; 0 advisory, 0 warned).` (275 s, `fin/check-all.log`); `tools/check-architecture.ps1` (venv python) `Architecture check passed.`;
  `tools/check-agent-workflow.ps1` `Agent workflow check passed.`; `python3 tools/check-decision-index.py` OK (1316 IDs).

## For the Architect's check
1. **`loop-core.js` `resolveScreen`, one line (unit 3, `8b0543c7e`), overriding Q1's default.** Before: a live alias wrote
   `'#/' + target + typed query`, which dropped the alias's own query (`findings-cost` landed on `findings`). After: it writes
   `iaCanon('#/' + id + typed query)`, so `findings-cost` lands on `findings?heading=optimize`. Why: `resolveScreen` already rewrites the
   address, and `iaCanon` (D-IA.78) is the one merger of alias and typed queries. The default would have given `iaLiveAlias`, a lookup,
   hidden state, and made `iaScreen` write the address a second time. The ALIAS, landing, foreign and landed branches are unchanged.
2. **The aliases pulled forward from unit 4 (Q5).** Spec §9 puts "the aliases" in 4(a). Unit 3 added the four, dormant, so `aliasq`
   could be proved under force. Correction (review round 1, L1): the palette did not "still list" "Act first (Portfolio)"; the alias made it live, a second entry beside "Decisions · Go to". Fixed: `iaPaletteFilter` drops list-alias entries (the alias stays an address).

## Known deviations (register R775-R779)
- `MOCK DEVIATION` D2: no "at stake" tile and no stake sort on three lists (R775).
- `MOCK DEVIATION` D2: Search drawn from 11 items with the filters (R776).
- `MOCK DEVIATION` D2: the Sites "Not shown" remainder beside "Show all" (R777).
- `MOCK DEVIATION` D5, resolving in IA-2d: Finding and Action rows open their decision or the plan (R778).
- `MOCK DEVIATION` D5, resolving in IA-2c: no Assets, Incidents and Maintenance lists (R779).
R749 to R751 close in IA-2b2.

## Residual risk and review focus
- **Existing issue (recorded, not fixed).** At 390 the review bar's screen chooser reads "Portfolio · Portfolio" on `#/decisions`
  from any arrival page. It lists only `SCREENS`, and a landed IA route without an entry falls back to the first option. `main` does the
  same on `#/plan` and `#/portfolio/outcomes`; IA-2b1 adds `#/decisions` to the class (`fin/screen-select.txt`).
- `plan_switch_check` and `ux_interaction_check` read the reviewed act-first screen by deleting the alias in their own window (Q6).
- Layout evidence: the `ia_shots` list set above (390, 1280, 1440; light and dark). `tools/layout-evidence.mjs`: not run (the
  mock-up is a `file://` page with no base URL; `ia_shots` is its layout gate).
- Focus: one target per row; tiers at the live sizes; restore and keep-place; the Outcomes fold; several rows to one decision.
