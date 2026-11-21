# IA-1 and IA-2 rulings, continued (rulings-2.md is at the 15k cap)

## IA-2a handshake answers

Architect (Claude), 2026-11-21. Answers R1 to R18 and P1 to P14 of `handshake.md`; spec §5.1 rev 5. Every gate below has
a plant that can fail it, and each plant names the state or host where it fails.

### D-IA.49 Unit 2 checks run forced; no check may stay dormant after the flip (R1, R2, R11a, R18, P8, P9)

- **The flag.** `IA_FORCE_LANDED=IA-2a` (read in `ia_crawl.cjs` `boot`, after the scripts load and before the first
  render) adds the unit to `IA_LANDED` in the booted window only. No product-file change. With it, `plan` and
  `plan/<tab>` render through `shapePlan`, and G1's graph includes the three tab edges (R11a).
- **What unit 2 proves.** Unit 2 has no builder, so under the flag its assertions run against `shapePlanInterim` and a
  stub (`tools/fixtures/plan_stub.js`, one function per tab returning the §5.1.2 placement with fingerprints). Evidence for unit 2
  is "written and mutation-tested": each assertion passes on the stub and fails on a one-line mutation of it. It is not
  "plants failing on the real shape"; the packet says so in those words.
- **Plants run at 3(a).** The builders land with the flag still needed (routes not live). At 3(a) `ia_gates --force IA-2a`
  runs every IA-2a plant, including the three `PSW_PLANT`s on `plan_switch_check` (R2), against the real builders. That
  run is the "shown failing before the flip commit".
- **After the flip.** `ia_gates` fails any IA-2a check whose output contains `dormant`. The plant table is the proof it ran.
- **The stop moves.** The recommended stop is the end of 3(a), not of unit 2. Unit 2 never merges alone (R18). A stop line
  names the next-resume sha, and states that `IA_LANDED` has no IA-2a at that point.
- **Runner rows (P9).** `ia_gates.cjs` gains rows `PLAN_PLANT`, `COUNT_PLANT=planstep|planhist`, `SHAPE_PLANT=doctitle`,
  `G1_PLANT=plantabs`, `PSW_PLANT` and `UXI_PLANT` (so `plan_switch_check` and `ux_interaction_check` join the runner).
  `ia_shots` needs the heavy slot: `SHOTS_PLANT=approvefold` runs by hand in the slot, output in the packet.
- **Plants must be able to fail (R11d).** `G1_PLANT=plantabs` returns Items only and runs on `portfolio` → `plan`, where
  the group is shown; the surfaces `plan tab: Left out|Review|History` are unreachable under it, so G1 must report them.

### D-IA.50 Identity covers states; counts agree on every route and case (R3, R4, R6, R12, R15, R17, P2, P4 to P6, P10)

- **R3.** `parts_identity.cjs` sets the plan state with one literal `PLAN_STATES` defined in the script and passed to
  both windows (`uxMockSet`: `plan[op]` = `{state, by, version, ids}`; "sent back" adds `reason`, `giveWay`).
  "Approved" runs the default case and every non-default case (`version` + 1, that case's `ids`). Counts to print per
  function: `planScreen` = operators (3) × cases (the script's own per-operator count, listed) × 3 states × 2 previews;
  `whatChangedScreen` = 3 × 3 × 2 = 18; the four splits join the job list. Plant `PI_PLANT=planparts|approval|band|whatchanged`
  changes one byte in that split's output in the new window; each must report DIFFERS. The script also fails if both
  windows were booted from the same file path (a window compared with itself).
- **R4.** `whatChangedScreen` calls `whatChangedParts(LS.op)`; Review calls it with `ctx.op`. `plan_shape_check` asserts
  `ctx.op === LS.op` on every render (an operator in the address included) and fails otherwise. Building all six parts
  for Review is accepted (cost and `UX_QN` advance as today; the check resets `UX_QN` per render).
- **R6.** Copy: "Version {n} proposed" is `PSTATE().version` (the proposal); the History sub is `S.version` (the plan's
  current version). The count check acts (Approve, Undo, Send back) on each of the four routes and compares with
  the manifest and `sessionStorage['l4-mock']` after each act; the packet's count table says so.
- **R12.** Boots: 4 routes × 4 states (as proposed, Approve, Undo, Send back) × 3 operators = 48, plus Approve of a
  non-default case on Lakeside 6500/No, Harvest No, Metro No × 4 routes = 12 more: 60 boots. After Approve of a
  non-default case History's first row, the stepper and the toast say the new version (`S.version`, not
  `PSTATE().version`). The badge is down by one only when the starting state was PROPOSED; at DRAFT it is unchanged.
  Plant `COUNT_PLANT=planver` (History's first row reads `PSTATE().version`) fails on that case.
- **R15.** `plan_shape_check` asserts focus after Approve is on `[data-plan-state]` (the chip) on all four tabs, and
  after Undo is on the act button (`uxFocusAction`). The chip lives in L1's act row, so it exists on every tab.
- **R17.** Keep `REVISED` (= Proposed, D-IA.44). `plan_shape_check` unit-tests `iaPlanSteps` directly on DRAFT,
  PROPOSED, REVISED, APPROVED, CLOSED (cur 0, 1, 1, 2, 3) and the thrown error on `BOGUS`; plant `PLAN_PLANT=revised`
  (REVISED → 0) fails it.
- **P2, P4, P5.** Confirmed as the implementer states: `crew` and `listed` become `const`s with identical strings, the
  `grid2` wrapper and whitespace stay in `l3`; `B.crew` is the fallback; `whatChangedParts` returns six strings in
  today's order. Only the byte compare decides.

### D-IA.51 Approve of another case is never unseen (R5)

L1 gains, on all four tabs and only when the case differs from the proposal (so L1 stays identical across tabs), one line
after the release line: `<p class="ia-plan-case">Showing the case you chose: {label}. <a href="#/plan">Change the case</a></p>`.
`{label}` is the case wording the Approve dialog already uses (the builder reuses that function and names it in the
packet). `.ia-plan-case{margin:var(--s2,8px) 0 0}` joins `ia.css`. Approve stays in the band on every tab. The check is
the R12 one above plus: the line is present on all four tabs after a non-default pick, absent on the default case.

### D-IA.52 Plants and fingerprints (R7 to R10, R13, R14, R16)

- **R7.** `PLAN_PLANT=cap` fails on History: the check asserts History's row count equals the log entries for the
  operator plus 2 (proposed, opened), and at least 3 after one Approve. `[data-ux-over]` is asserted on all four tabs;
  if Items, Left out or Review hold no capped list, the plant may only fail on History, and the packet says so.
- **R8.** Selectors: `section.approval` absent; `.meter, .metertrack, .meterhead` absent; `.ux-meterbar` is the only bar.
  `[data-ux-sticky]` once per tab; the sticky's Approve and the band's carry the same `data-act` (D-IA.23). Plant
  `PLAN_PLANT=sticky` (sticky carries a different act) fails it.
- **R9.** The check holds its own constants: the `<h2>` or `aria-label` of every placed fragment ("Left out of the plan,
  and why", "Listed beside", the returned Actions heading, "Try another case", "Where this plan is", "The plan at a glance",
  "The plan's review", "Versions and approvals"), plus the release line (`.approval-releases`), the version notice
  (`.notice`) and the case line (`.ia-plan-case`), each counted exactly once per route. Headed-when-non-empty fragments
  are asserted only where they exist: returned Actions on Lakeside 6500/No, Harvest No, Metro No; Listed beside on the
  hosts the check lists by name. `PLAN_PLANT=place` fails on a count of 2.
- **R10.** Tiles are computed from the manifest period; a period of three or more months makes the check fail ("L1 cap
  of 4 exceeded, spec stop"), for all three operators, not only Lakeside.
- **R13.** Yes: `screens.js` line 1004 is the one reviewed line, `s.docTitle || s.title`. Item 10 compares titles within
  each tab group; the Site group per Site (`ctx.site`) across every Site fixture.
- **R14.** The metric is the band's own Approve: `getBoundingClientRect().bottom <= innerHeight` at scroll 0, for
  `plan`, `plan/left-out`, `plan/review`, `plan/history` at 1440 × 900 and 1280 × 720; elements inside `[data-ux-sticky]`
  do not count. `SHOTS_PLANT=approvefold` (a 900 px block before the band) fails on it.
- **R16.** New check: every string rendered on the four routes and not on the reviewed pages is in the §5.1.6 list
  (`copy_check.cjs` list extended; plant `COPY_PLANT=plan` adds a stray word). "Opened within the executive’s limits" is
  sourced from `PSTATE().opened`; "The system · {date}" from `PSTATE().proposed`; the packet states both.

### D-IA.53 G1 and layout (R11, P3, P7, P11 to P14)

- **R11b, c.** Origin is `portfolio`. Measured: `plan` = 1 (Overview tile and inbox row both land on Items); each
  tab = 2 (the tab strip is on the plan page); a plan item's decision = 3 (plan 1, the closed item `details` 2, the
  decision 3, D-IA.32). The done clause "every plan item's decision (≤ 2)" is wrong and is replaced: the decision row is
  reported at 3 and is not a new bar; the decision's existing G1 row (reached from the inbox) is unchanged.
- **P3.** `crew` (Items) and `listed` (Left out) are placed full width, no `grid2` wrapper. Confirmed.
- **P7.** Confirmed: `docTitle` is set in `iaScreen` (read it before coding); one line in `render()`.
- **P11, P12.** Count and list every changed assertion of `plan_switch_check` and every changed line of the uxi plan block
  in the packet; no change beyond D-IA.48 and this ruling.
- **P13.** All six answered above. **P14.** Commit plan: (1) splits, `parts_identity` states and plants; (2) checks with
  `IA_FORCE_LANDED`, stub and mutation runs; (3a) builders, routes, `docTitle`, `ia.css`, forced plant runs (stop point);
  (3b) the flip, retargeting, walkthroughs, R757 to R760, screenshots, packet. Files: `vNEXT/` and this folder only.
