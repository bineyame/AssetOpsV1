# DS1m packet: the mock-up's trend lines from the history

Branch `task/DS1-mockup-trends` (worktree `/opt/assetecon/AssetOpsV1/.claude/worktrees/ds1m`), base `main` `54808af06`
(the pack, with DS1p, merged). Not merged. `USER_REVIEW_REQUIRED: true` (spec header).
Head used for the call sites (P15): `uxOverview` and `uxHistory` in `interactive-mockup-vNEXT/loop-ux.js` at `54808af06`
(`uxHistory` line 370; tile calls lines 290-293). No screen code changed.

**Mid-build questions: 2** (MB7, MB8 in `mid-build-questions.md`), both ruled on `main` (`a74b40fe8`, `rulings.md`
"DS1m mid-build answers"). MB7: G3 amended. MB8: the Lakeside sentence is accepted with DS1m. Each was a spec gap, not
an implementer defect.

**Round 4 status: all gates green, 9 plants fail their clauses; R742 closed (see "Round 4").**

**Round 3 status (superseded): plan_switch_check green; ux_interaction_check and G3 red from `main`'s UI change (see "Round 3").**

**Round 2 status: one gate is red, caused by `main`'s data and not by DS1m; stopped and reported.** After merging `main`
and regenerating, `plan_switch_check` gives 777 passed and 1 failed. The failure is `mto-losses: chosen by David
(SITE_MANAGER) ()`. `main`'s own regenerated output fails identically (see "Round 2" below).

## Round 4: D-DS1.15 built (merge of `main` `f4b8923a7`, then the amended gates)

`main` merged (`df428ae17`, clean). `gen_fixtures.py` and `build.mjs` rerun: `fixtures.js` and `index.html` byte-identical
(no diff). No screen code changed. Evidence: `/opt/assetecon/evidence/DS1/m-r4/` (green runs) and `m-r4-plant/` (plants).

| Gate | Result |
| --- | --- |
| DS1 generator tests (`.venv/bin/python -m pytest simulator/tests/world`) | 125 passed |
| render_text | 237 renders, script errors 0 |
| plan_switch_check | 778 passed, 0 failed, script errors 0 |
| ux_interaction_check (G1 + G1+ block 8 on 3 overviews and 9 Sites: 8a, 8b, 8c each x 12) | 360 PASS, 0 FAIL |
| check_manifest.py | 7571 checks passed (2869 history), 0 failed (main's fix) |
| G3 (`tools/g3_trends.cjs`, 36 shots) | 36 of 36 pass |

Built: block 8 in `tools/ux_interaction_check.cjs` (sweep from `OPS[op].sites`, nothing skipped; 8a form by `kind`, 8b
series last points = headline, 8c stated change from `last - Sep`); `tools/g3_trends.cjs` (36 shots, per-width clauses,
figure measured with a `Range`). Decision for the reviewer: the signed form accepts an unsigned `$0` (Metro Kasarani's gap
is unchanged, `usdW(0, true)` = "$0"); the ruling says "signed change", and a sign on zero would be invented.
The G3 script now lives in the repo (it was outside it in rounds 1-3).

**Plants** (each a copy of `index.html`, made by `scratchpad/ds1m_r4_plants.py`; generated file never edited; all reverted
by being copies; logs `m-r4-plant/P*-ux.txt`, `P*-g3.txt`):
| Plant | Result |
| --- | --- |
| P1 no `DERIVED.history` | 8a FAIL on all 12 pages (plus 8b, 8c as a consequence); G3 0 of 36 pass, form fails on all 36 |
| P2 Oct +100 on Ruiru cost, Kobo gap | 8b FAIL on Ruiru and Kobo only (2 lines); nothing else |
| P3 compare against first point | 8c FAIL on all 12 pages; nothing else |
| P4 no `data-measure` | 8a FAIL on the 4 Metro pages; nothing else |
| P5 trend `visibility:hidden` | G3 24 of 36: 12 fail, all 1440 |
| P6 `max-width:40px` | 24 of 36: 12 fail, all 1280 |
| P7 `.ux-kpi-s+.ux-kpi-s` hidden at 1280 | 24 of 36: 12 fail, all 1280 |
| P8 sparkline shown at 390 | 24 of 36: 12 fail, all 390 |
| P9 `.has-trend` hidden at 390 | 24 of 36: 12 fail, all 390 |

**R742 closed** (`.agent/mock-departure-register.md`: status closed, D5 open count 2 to 1). `check_manifest.py` is now green
on this branch after the merge.

## Round 3: after merging `main` at `e0aedb86b` (UI branch `25b3ae88b`)

Merge conflicts: `.ai/state/index-2.md` (renumbered DS1m to line 150), `specs/INDEX.md` (main's rows, DS1 row kept), and
`fixtures.js`, `index.html` (regenerated from the merged sources with `python3 tools/gen_fixtures.py` then
`node build.mjs`, never hand-edited; sha `77fbcc841cd4`). A second regeneration is byte-identical to the first.
Evidence: `/opt/assetecon/evidence/DS1/m-r3/` (ux, g3). Gate expectations were not changed.

| Gate | Result |
| --- | --- |
| DS1 generator tests (`pytest simulator/tests/world`) | 125 passed |
| render_text | 237 renders, script errors 0 |
| **plan_switch_check** | **778 passed, 0 failed, script errors 0.** The round 2 red is gone: `main`'s check now expects the case on screen |
| **ux_interaction_check** | **red**: `metro overview trends: 1 sparklines, 2 "against Sep"` (DS1m's G1+ check, block 8). Lakeside and Harvest pass |
| **G3 (amended, MB7)** | **red, 4 of 30 pass** (the 1440 Portfolio Lakeside and Harvest shots) |
| check_manifest.py | 3 FAIL: alignment A3 and A5 on `website-content.md`, and the H9 baseline (4498 before history == 4501). The same fails occur on a clean `main` checkout (which also has an A3 hit in `layer4-transformation-design.md`) |

**Cause of the ux and G3 reds: `main`'s screen code, not the DS1 data.** The history data reaches every tile (series
and last points match the headlines). The UI branch (`786e1f905` "a trend is its tile's measure", `a090e1220` "Site
subtitle and trends shortened not hidden") changed what is drawn:
- A cost operator's (Metro's) first KPI tile is now text only ("Monthly cost up $1,684 against Sep", `uxTrendCost`,
  no `svg.ux-spark`). G1+ and G3 require two sparklines.
- At 1280x720 and 390x844 the trends are no longer hidden by the compact rule (`compactHidden=false`, sparkline visible).
  The MB7-amended G3 requires them hidden there.
- Site pages now draw real trends (Kobo -$8 / -$90, Thika -$54 / -$86, Ruiru "Monthly cost up $259" / +$148). The
  amended G3 requires "Trend not available yet" (D5, R742).
The mock-up's register row R742 (Site trends "not available yet") is therefore stale against `main`.
Needed from the Architect: a ruling on the expectations (G1+ block 8 for cost tiles; G3 compact and Site clauses; R742).

## Commits

| Commit | What |
| --- | --- |
| `51dae6c24` | **Check first (W2).** G1+ (R20): block 8 of `tools/ux_interaction_check.cjs`. On the pre-history fixtures: 95 PASS, 3 FAIL, one per operator ("0 sparklines, 0 against Sep; last points null = 1443 …"). |
| `160fed3b6` | `fixtures.js` and `index.html` regenerated (`python3 tools/gen_fixtures.py`, `node build.mjs`). |
| `622535c16` | Register row R742 (`MOCK DEVIATION D5`, Site trend tiles); MB7 and MB8. |
| (this) | Packet; built-state entry (`.ai/state/demo.md`, `index-2.md` line 143); spec and `specs/INDEX.md` status. |

## Done criteria

| Criterion (spec §9, reviewer guide) | Result |
| --- | --- |
| §9.1 `git diff --exit-code -- ../derived-values.json ../history.json ../missing-records.json` after regenerating | exit 0 |
| §9.2 KPI tiles 1 and 2 show the 64×16 sparkline and "<change> against Sep", all three operators | Yes. Lakeside −$151 / −$330; Harvest −$157 / −$253; Metro +$1,684 / −$661 (all "against Sep") |
| Last point equals the tile's headline | Yes: 1443 / −852; 946 / −770; 41705.12 / −3184.32 (`T.actual`, `T.variance`) |
| No screen code changed | Yes: the diff touches only `fixtures.js`, `index.html` and the gate file |
| No figure other than the trends changes | Yes. In jsdom, 205 renders before and after: only the three Portfolio overviews change, and only in their trend slots and sparkline names. One non-figure sentence also changes (MB8). No drawer text changes. |
| §9.2 period menu keeps "not available yet" (R21) | Kept. `ux_interaction_check` "period menu: … earlier periods 'not available yet'" PASS. **Choosing September as the period is still not available**, although its trend point is shown. |
| §9.3 Site tiles keep "Trend not available yet"; one D5 register row | Yes: all 12 Site shots say so, with no sparkline. Row R742 is in `.agent/mock-departure-register.md` (D5 table). |
| G1, G1+, G2: 0 hits; G1+ fails on a plant | Yes (gate table) |
| G3: 18 states pass | **6 of 18 pass.** The 12 that fail are at 1280×720 and 390×844, where the trend line is `display:none` by existing compact CSS. Stopped: MB7 |
| Files touched = §3's DS1m row | Yes, plus `mid-build-questions.md` and the closeout files the standing brief requires (state entry, spec status line, `specs/INDEX.md` row) |

## Gates (all at `160fed3b6` or later; evidence `/opt/assetecon/evidence/DS1/m-after/`)

| Gate | Command | Result |
| --- | --- | --- |
| render_text | `node tools/render_text.cjs` | 205 renders, script errors 0 (~90 s) |
| vocab_check | `node tools/vocab_check.cjs` | exit 0, hits 0 (368 earlier-view body hits are reported as not failing, as at base) |
| copy_check | `node tools/copy_check.cjs` | exit 0, no hits |
| plan_switch_check | `node tools/plan_switch_check.cjs` | 777 passed, 0 failed, script errors 0 (same as base) |
| hand_typed_scan | `python3 tools/hand_typed_scan.py` | exit 0. Count 2: both in a `loop-core.js:401` comment ("$883 +", "−$250"). That file and `derived-values.json` are unchanged from base. Manifest hits 0; allow list 46/46 used |
| ux_interaction_check (G1, G1+) | `$HS -- node tools/ux_interaction_check.cjs "$PWD/index.html" <ev>` | 98 PASS, 0 FAIL, 74 s. Before the regeneration: 95/3 |
| G1+ plant | the same, on a copy of `index.html` with `DERIVED.history` deleted (`/opt/assetecon/evidence/DS1/m-plant/`) | exit 1, the 3 trend FAILs, 95 PASS |
| design_lint (G2) | `$HS -- node tools/design_lint.cjs` | exit 0, `fails: []` (CSS colour residuals reported as not failing, as before) |
| check_manifest.py | `PY check_manifest.py` | 7436 passed (2869 history checks), 0 failed |
| check_alignment.py | `PY check_alignment.py` | 114 passed, 0 failed |
| check-agent-workflow | `pwsh tools/check-agent-workflow.ps1` | passed |
| check-architecture | `pwsh tools/check-architecture.ps1` | passed with `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`. Without it, it fails only because the worktree has no `.venv` (environment) |

`HS=/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh`, after `source /opt/assetecon/tools/pw/env.sh; export LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH`.

## G3 (layout evidence for DS1m)

`tools/run-audit.sh --shots` covers neither 1280×720 nor dark, so G3 used a capture script run through the slot:
`$HS -- node /opt/assetecon/evidence/DS1/m-tools/ds1m_shots.cjs "$PWD/index.html" <out>`.
- Operator: `sessionStorage l4-op`.
- Theme: the mock-up's own attribute, `localStorage l4-theme` → `html[data-theme]`. Each shot asserts that the attribute
  equals the theme.
- Each trend's box is measured against its `.ux-kpi` and the viewport.
- Run `/opt/assetecon/evidence/DS1/m-g3-160fed3b6/` (`results.json`, log `/opt/assetecon/evidence/DS1/m-g3.txt`), 35 s:
  - Page errors: 0 in all 30 shots.
  - Portfolio at 1440×900: all 6 pass (visible, inside the tile, inside the first viewport).
  - Portfolio at 1280×720 and 390×844: 12 fail on "visible". `ux.css:360` (`min-width:1024px and max-height:820px`) and
    `ux.css:246` (`max-width:600px`) set `.ux-kpi-s+.ux-kpi-s{display:none}`, which hides the trend sub-line (MB7).
  - Site at 1440×900: 6 pass. Site at 390×844: 6 hidden by the same rule. Their "Trend not available yet" slot was
    already hidden there before DS1m.

**Trend screenshots** (`/opt/assetecon/evidence/DS1/m-g3-160fed3b6/`):
- **Portfolio:** `portfolio-{lakeside,harvest,metro}-{1440x900,390x844,1280x720}-{light,dark}.png`. The trend is visible
  in the 1440 shots and absent in the 390 and 1280 shots (MB7).
- **Site:** `site-lakeside-*` (Kobo), `site-harvest-*` (Thika) and `site-metro-*` (Ruiru), at
  `{1440x900,390x844}-{light,dark}.png`.
- "Both packs" in the dispatch is read as both themes, light and dark. If it meant the pack before and after DS1p, the
  "before" state is the 95/3 run at `/opt/assetecon/evidence/DS1/m-w2-fail/`, which has no shots.

## Known deviations

- **The dispatch differs from the spec, and the spec was built.**
  - The dispatch's check list asks for the Site tiles to fill and for the period menu to list Jul–Oct.
  - Spec §9.3 (D5) and §9.2 / R21, with the reviewer guide's DS1m items, require the opposite: the Site tiles stay
    "Trend not available yet", and the period menu keeps earlier months "not available yet".
  - No gate asserts the old state except the period-menu check, which stays valid under R21 and was not weakened.
- **The register header counts** ("Register rows: 405", D5 6/1) were not updated, because only one row was in scope.
  They were already stale (IDs run to R741).

## Not verified

- G3's pass at 1280×720 and 390×844 (MB7, stopped).
- A visual check of every shot: the 1440 Portfolio and the 1280 Lakeside shots were viewed by eye. The rest are
  measured only.
- No full suites were run, and none was scheduled.

## Round 2: after merging `main` (rulings `a74b40fe8`)

**Commits:** `d8b610b16` (merge of `main` at `e3052032d`, no conflict); `f6830f091` (regenerated `fixtures.js` and
`index.html`, manifest sha `357a7b6f6cff`). The §9.1 pack-output diff exits 0. Evidence: `/opt/assetecon/evidence/DS1/m-r2/`.

| Gate | Result at `f6830f091` |
| --- | --- |
| render_text | 205 renders, 0 script errors |
| vocab_check / copy_check | exit 0, 0 hits / exit 0, no hits |
| **plan_switch_check** | **777 passed, 1 failed**: `mto-losses: chosen by David (SITE_MANAGER) ()`. The decision page's "who decides" step is empty |
| hand_typed_scan | exit 0. Count 2, the same `loop-core.js:401` comment as before; manifest hits 0 |
| ux_interaction_check (G1, G1+) | 98 PASS, 0 FAIL (70 s); the three overview-trend checks pass |
| G1+ plant (`DERIVED.history` removed; `/opt/assetecon/evidence/DS1/m-plant2/`) | exit 1: 95 PASS, 3 FAIL (the trend checks) |
| design_lint (G2) | exit 0, `fails: []` |
| G3, amended by MB7 | **30 of 30 pass** (below) |
| check_manifest.py | 7556 passed (2869 history checks), 0 failed |
| check_alignment.py | 114 passed, 0 failed |

**Where the `plan_switch_check` failure comes from.** The decision `mto-losses` (`chooser: SITE_MANAGER`, manifest line
1617) was added on `main` by the RECON-1 data lane (`6448fd67b`, D-RECON.5-7). `main`'s committed `fixtures.js` predates
it.
- `main`, files as committed: 777 passed, 0 failed.
- `main`, regenerated in a scratch worktree (`/opt/assetecon/evidence/DS1/m-mainwt`): 777 passed, 1 failed, the same
  line.
- Any branch that regenerates from today's `main` turns this gate red. DS1m did not fix it: the fix is screen code or
  data owned by another lane.

**rendered-text.json diff**
- **Against `main`'s own regenerated output:** byte-identical. `fixtures.js` and `index.html` are byte-identical to
  `main`'s regeneration, and so is `rendered-text.json`. No difference at all.
- **Against `main`'s committed (stale) files**
  (`/opt/assetecon/evidence/DS1/m-r2/textdiff-vs-main-committed.txt`), 11 fields differ:
  - DS1m's trend slots and sparkline names on the three Portfolio overviews;
  - the MB8 Lakeside sentence;
  - **RECON-1's own change:** Ruiru's "$60,000 capital avoided (Modelled)" becomes "Not modelled" / "not available
    yet". It appears on 6 renders: Lakeside `decision/ruiru-expansion` and `site/ruiru`; Metro `portfolio`,
    `portfolio/act-first`, `portfolio/act-first/plan` and `portfolio/demand-and-capacity`, text and drawers.
  - This figure change comes from `main`'s manifest (`capex_not_needed`), not from DS1m. It reaches the committed mock-up
    with whichever branch regenerates first.

**G3, amended by MB7** (`/opt/assetecon/evidence/DS1/m-g3-f6830f091/`, `results.json`; log
`/opt/assetecon/evidence/DS1/m-r2/g3.txt`; 36 s through the slot):
- 30 of 30 pass, with 0 page errors, 0 elements clipped by their tile, and no sideways scroll in every shot.
- Portfolio at 1440×900 (6): both trends visible, inside the tile, inside the first viewport.
- Portfolio at 1280×720 and 390×844 (12): both trend slots are present with their series (`svg.ux-spark` and
  "against Sep"). Each sits in a `.ux-kpi-s` that is `display:none` and matches `.ux-kpi-s+.ux-kpi-s`, with nothing
  else hiding it (`compactHidden`).
- The `compactHidden` test is not vacuous: it is false for all 12 trends in the 1440 shots.
- Site at 1440×900 and 390×844 (12): "Trend not available yet", no sparkline (D5, R742).
- Screenshot names are as in round 1, in the new folder.

## Merge note (round 1; done in round 2)

`main` moved after the base. From `54808af06` to `56300a810` it changed `demo-site-scenario-manifest.yaml` (the RECON-1
data lane, D-RECON.5-7) and `check_manifest.py`. `derived-values.json`, `fixtures.js` and `index.html` did not change on
`main`.
- The merge is textually clean, but this branch's `fixtures.js` embeds the manifest at `54808af06` (sha `0800a0478f1f`).
- Whoever merges must `git merge main` here and rerun `gen_fixtures.py` and `build.mjs` (spec §3: the branch that merges
  last regenerates), then rerun the gates.
- DS1m did not do that merge. A regeneration then would mix RECON-1's manifest changes into DS1m's "only the trends
  change" diff.

## Review focus

- MB7's choice: amend G3, or have the UI lane relax the compact rule. MB8: accept the carried wording.
- The sign convention on the first tile's sparkline name ("Jul +$1,311 …" on a level series). It comes from the screen
  code's `usdW(v, true)` and is unchanged by DS1m.
