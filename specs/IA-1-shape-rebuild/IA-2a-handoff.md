# Done (fix round r1, 2026-11-21): commits 09a06c300, e5ccb0137, ab3746a44

- All gates green at ab3746a44; packet-IA-2a.md has "Fix round r1". Logs `/opt/assetecon/evidence/IA-2a/r1/`. Nothing left to resume; review r1 next. Do not merge (owner walkthrough).

# Done (builder 3, 2026-11-21): 3(b) complete

- Flip `a4737f102`; merge of `main` `af7847ac2`; packet-IA-2a.md finished (in review). Logs `/opt/assetecon/evidence/IA-2a/3b/`.
  Nothing left to resume; the notes below are history.

# Resume note (builder 2, 2026-11-21, 05:45 UTC)

- Unit 2 committed `c5af13ced`; 3(a) committed `ef7d098ad` (builders, routes, docTitle, ia.css; not live), `76b739121` (uxi page
  default and route order), `ce3d81d16` (ia_gates prints a crash's error line).
- Unit 2 proof (stub, forced): every plant failed: PLAN_PLANT 9 of 9, COUNT planstep/planhist/planver, SHAPE doctitle, G1 plantabs
  (after the rebuild), PS crewtile/release/leftout, COPY plan, SHOTS approvefold (48 of 72 bad). Logs `/opt/assetecon/evidence/IA-2a/unit2/`.
- uxi planans and planwait fail on the builders (forced). The forced uxi base run crashed twice ("Target crashed"), during the /tmp
  quota incident 05:30-05:40; rerun pending.
- Uncommitted: walkthroughs.md (plan tabs), register R757-R760, `.ai/state/demo.md` + index line 168. The flip is prepared in
  `<scratch>/ia2a-r2/flip/` (IA_LANDED + IA-2a, plan renders shapePlan, shapePlanInterim deleted).
- Forced ia_gates at 3(a): 76 runs, all as expected (3805 s). Clean stop taken here; packet-IA-2a.md has the stop line.
- 3(b) prep: `/opt/assetecon/evidence/IA-2a/3a/3b-prep.patch` (git apply) and `flip.py <vNEXT dir>`.
- Next: -> flip commit (copy flip files, build) -> normal ia_gates, ia_shots full, parts_identity,
  G3, shell, lint, render_text, vocab, copy, hand_typed, check_manifest -> packet-IA-2a.md, spec Status in_review.

# IA-2a handoff (partial: unit 1 done, unit 2 started)

Builder 1 (Claude Opus), 2026-11-21. Stopped at the context budget (standing brief), not on a coordinator stop.
Worktree `/opt/assetecon/AssetOpsV1-ia2a`, branch `task/IA-2a-plan`, off `main` `f74076f87`. No database, server or
Docker touched; no process left running. `frontend/node_modules` is a symlink to the main checkout's.
Base page for `parts_identity`: `main`'s `index.html`, copy at
`/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/ia2a/main-index.html`
(regenerate with `git show main:<vNEXT>/index.html > <scratch>/main-index.html` if the scratchpad is gone).

`IA_LANDED` has no IA-2a. Every screen is as on `main`.

## Done

- **Unit 1, commit `554863783`.** The four splits of spec §5.1.5:
  - `planParts(op)` (`loop-portfolio.js`) gains `P, budget, diff, paths, crew, listed, leftBody, leftAns, left, cases,
    returned, switches, ap`. Local names `listedS` and `swS` avoid clashing with the data array `listed` and the global
    `switches()`.
  - `approvalParts(op,P,budget)` is new. `approvalPanel(op,P,budget,a=approvalParts(...))` joins the parts; `planParts`
    passes its own `ap`, so the parts are built once.
  - `uxPlanBandParts` is new in `loop-ux.js`, and `uxPlanBand` joins it.
  - `whatChangedParts(op)` is new; its local `review` rows are renamed `reviewRows`, and `whatChangedScreen()` joins
    the parts.
- **`parts_identity.cjs`.**
  - Adds `PLAN_STATES` (one literal, filled per operator and case from the base window, and written to both windows as
    `{plan:{[op]:…}}`).
  - Jobs added: planScreen × case × {approved, sent back}; the four splits as jobs (the base function against the
    script's own join of the new parts); whatChangedScreen × 3 states.
  - Adds `PI_PLANT=planparts|approval|band|whatchanged` (flips one byte), and a same-file refusal.
  - Result: **282 cases byte-identical** (planScreen 48, planParts 48, approvalParts 48, uxPlanBandParts 48,
    whatChangedScreen 18, whatChangedParts 18, uxOverview 6, siteOverview 18, decisionScreen 30).
  - The plants fail: planparts 48 differ, approval 48, band 48, whatchanged 18. The same-file run prints FAIL and exits 1.
  - The states take effect: lakeside 6500/No reads 34562 bytes as proposed, 34206 approved and 34078 sent back.
  - Logs are in `<scratch>/pi*.log`.
- **Uncommitted, unit 2 infrastructure** (inert by default; commit it with the rest of unit 2):
  - `tools/ia_crawl.cjs` `boot`: `IA_FORCE_LANDED` adds the units to `IA_LANDED` after the scripts load, then calls
    `render()` again before any read. The bundle is one `<script>` ending in `render();`, so "before the first render"
    cannot be met without a product change; state this in the packet. `forced()` is exported.
  - `tools/ia_gates.cjs`:
    - adds `--force IA-2a` (passes `IA_FORCE_LANDED` to every child and strips it otherwise);
    - adds the IA-2a plant rows: `PLAN_PLANT` tabs, place, l1, approval, thr, stepdone, cap, revised, sticky;
      `COUNT_PLANT` planstep, planhist, planver; `SHAPE_PLANT` doctitle; `G1_PLANT` plantabs; `PSW_PLANT` crewtile,
      release, leftout; `UXI_PLANT` planans, planwait; `COPY_PLANT` plan;
    - adds the base runs of plan_shape, plan_switch, uxi and copy when IA-2a is landed or forced;
    - adds the `dormant` rule: an IA-2a check whose output says "dormant" while the unit is landed or forced is BAD;
    - the summary prints "forced".

## Next (in order; spec §5.1.8 and §5.1.9, D-IA.49 to D-IA.53)

1. **Unit 2 (checks first).**
   - Write `tools/plan_shape_check.cjs`:
     - Boot through `ia_crawl.boot`.
     - Dormant unless `IA_LANDED` has IA-2a; it prints `IA-2a not landed; dormant` and exits 0.
     - When forced but the window has no `shapePlan`, it loads `tools/fixtures/plan_stub.js` with `w.eval`. The stub
       defines `iaPlanSteps`, `shapePlan(ctx, tab)` (the §5.1.2 placement with fingerprints), pushes the three tab
       routes, sets `IA_TAB_GROUPS.Plan`, and points `plan`'s render at `shapePlan(ctx, 'items')`.
     - Assertions: §5.1.8, plus D-IA.50 (R4: `ctx.op === LS.op`; R15: focus; R17: `iaPlanSteps` table, including the
       throw on `BOGUS`) and D-IA.52 (R7: History row count; R8: selectors; R9: the fingerprints counted exactly once).
   - Implement every plant as a window patch applied after boot and before a `render()`. Global function declarations
     can be reassigned through `w.eval`; `IA_TAB_GROUPS` is a const object whose properties can be set.
     - tabs: filter out History.
     - place: add `planParts(op).left` to the Items L2.
     - l1: strip `.approval-releases` on History.
     - approval: add `approvalPanel(...)` to the Items aside.
     - thr: drop `[data-ia-drawers]`.
     - stepdone: remove ` is-done`.
     - cap: redefine `uxCapLists` with a cap of 1.
     - revised: map REVISED to 0.
     - sticky: change the sticky's `data-ux-act`.
   - The same patches applied to the stub are the "one-line mutations" of unit 2.
   - jsdom has no `offsetParent`. `uxFocusAction` therefore falls back to the H1, so the R15 Undo assertion needs a
     shim in the check; state it.
   - Then:
     - the `count_check` plan block (60 boots, D-IA.50 R12; plants planstep, planhist, planver);
     - `shape_check` item 10 (live now; the Portfolio group passes) and the `doctitle` plant;
     - the G1 surfaces `plan tab: Left out|Review|History` and `plantabs` (D-IA.49 R11d, D-IA.53);
     - the `ia_shots` approvefold clause;
     - `copy_check` `COPY_PLANT=plan`.
   - Run `node tools/ia_gates.cjs --force IA-2a` against the stub for the mutation runs. Unforced `ia_gates` must
     stay green.
2. **3(a).** The builders in `ia-shapes.js` (`iaPlanSteps`, `iaPlanStepper`, `iaPlanBand`, `iaCrewTiles`,
   `iaPlanHead` with the D-IA.51 case line, `iaPlanHistory`, `shapePlan`) and the three routes.
   - Set `tab: 'Items'` etc. on all four routes, because `iaTabsHtml` needs `route.tab` truthy, and
     `tabGroup: 'Plan'`.
   - Add `docTitle` in `iaScreen`, and in `screens.js` `render()` write `${s.docTitle||s.title}`. The current line is
     `document.title=\`${s.title} · ${OPS[LS.op].name}\``.
   - Add the three `ia.css` rules.
   - Run every plant under `--force IA-2a`. This is the recommended clean stop.
3. **3(b).** The flip, the `plan_switch_check` and uxi retargeting, `walkthroughs.md`, R757 to R760, the screenshots
   and `packet-IA-2a.md`.

## Anchors (from a read-only survey; lines in `vNEXT/tools/` unless named)

- The shell `grep` is a ugrep wrapper that rejects long bounded patterns; use `/usr/bin/grep -n -o -E '.{0,200}x.{0,200}'`.
- **uxi** (Chromium, file://).
  - :22 `UXI_PLANT`; plants are early-exit branches (:41 to :97).
  - The plan block is at :547 to :613: route `#/plan` × 3 operators × 1440/1280/390.
  - :612 holds the assertion `r.n >= 4 && …` (the retarget to `>= 2`), and :563 the sticky probe.
  - :586 to :590 is the M1 routes list (add the three tabs). Output is PASS/FAIL lines, exit at :691.
- **plan_switch_check** (jsdom).
  - Crew meters: `metersCheck` :55 to :58, reading `.approval .meter`.
  - Release line: :86 `.approval .approval-releases`.
  - Budget: :104 to :123 `.approval .meterhead strong`. Retarget to L1's spend tile and crew tiles.
  - Actions: :90 to :102. Plant: :349 `PS_PLANT` (see Q3).
- **ia_shots**: argv[2] is the index path and argv[3] the out dir. Plants are applied in `run()` after goto (:57 to
  :69); the clauses are at :75 to :85; the plan routes list is :102.
- **count_check**: plants are `w.eval` code strings (:14 to :18, applied :39). It never reads `l4-mock` directly
  today; the plan block must read `w.sessionStorage.getItem('l4-mock')` itself (independence).
- **shape_check**.
  - Item 4: :90 compares `currentScreen().title`. Make it read `docTitle` where set.
  - Items 10 to 13 already exist (:21, :24 to :25, code :164 and :76). The spec's "item 10" therefore needs a new
    number; it is not yet chosen.
  - Plants: :30 `PLANTS`, `ITEM` map :57, injected :104.
- **G1 surfaces**: `IA_G1_SURFACES()` is in `ia-routes.js` :119 to :134, a product file. The three tab surfaces
  (`plan tab: …`, limit 2, via any) and the plan item's decision (limit 3, reported) go there in 3(a).
  `click_depth_check` :65 to :87 holds `APP` plants (add `plantabs`).

## Gate state at this handoff

- Unforced `ia_gates` after unit 1 (heavy slot, pw env): `ia_gates: 52 runs, landed IA-1a, IA-1b, IA-1c, all as expected (768.7 s)`.
  `<scratch>/gates-u1.log`. That run started before the uncommitted edits.
- `count_check` needs `PW` set (`source /opt/assetecon/tools/pw/env.sh`), or it errors with code 2.

## Risks

- The `dormant` rule matches the word anywhere in an IA-2a check's stdout. Keep that word out of other messages.
- Mid-build questions: 2 open (Q3 `PS_PLANT` vs `PSW_PLANT`; Q4 copy_check has no list), in `mid-build-questions.md`.
- shape_check already has items 10 to 13; the spec's "item 10" numbering collides (note it in the packet; it is not a blocker).
