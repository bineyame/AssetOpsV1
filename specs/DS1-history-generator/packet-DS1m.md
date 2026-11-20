# DS1m packet: the mock-up's trend lines from the history

Branch `task/DS1-mockup-trends` (worktree `/opt/assetecon/AssetOpsV1/.claude/worktrees/ds1m`), base `main` `54808af06`
(the pack, with DS1p, merged). Not merged. `USER_REVIEW_REQUIRED: true` (spec header).
Head used for the call sites (P15): `uxOverview` and `uxHistory` in `interactive-mockup-vNEXT/loop-ux.js` at `54808af06`
(`uxHistory` line 370; tile calls lines 290-293). No screen code changed.

**Mid-build questions: 2** (MB7, MB8 in `mid-build-questions.md`). Each is a spec gap, not an implementer defect.

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

## Merge note

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
