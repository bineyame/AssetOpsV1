# IA-1b review, round 1 (discovery): the hub shape

Branch `task/IA-1b-hub`, head `aa9eb82f7` (worktree `/opt/assetecon/AssetOpsV1-ia1b`, base `eb11251e9`). Read-only review by a fresh
Claude Reviewer. Read against spec rev 3 §2.8, §3 and §6, rulings D-IA.21 to D-IA.30, reviewer guide rev 3, packet-IA-1b, owner G1
(journeys in 2-3 clicks) and the owner's UI standing brief. Note: `rulings-2.md` does not exist yet; the IA-1b/IA-1c handshake answers sit
at the end of `rulings.md`.

## Summary (round 1)

**Verdict: accept with findings fixed on the branch** (M1 and M2 before merge; M3 needs an Architect call; Lows may ride along).
- Every gate I reran matches the packet: ia_gates 34 runs, all as expected; uxi 359 PASS / 1 FAIL (Q1); hub shots 108 / 0 bad;
  parts_identity 40/40 identical before the fix, 37 + 3 "sticky only" after; build in sync with sources; scope clean.
- P4 one source holds on all 9 Sites in both states (Outcomes gap = Site gap tile; column 6 = Site pill = split).
- Overview budget: 5 blocks; 1,944 / 1,521 / 1,587 px at 1440. Aliases, landing, foreign addresses and the D-IA.30 popover behave.
- M1: uxi is not green (§6 item 4): the Assure drawer's focus trap is broken by this unit (Q1). My view: fix it here.
- M2: G1 cannot see closed `<details>`. A planted extra disclosure click passes; the largest-driver drawer is 4 real clicks, printed 3.
- M3: Lakeside's `mto-losses` (waiting for a choice) is hidden on both the Overview (6 of 8) and Mto (3 of 4), and nothing leads to it.
  The Site cap has no deviation row.
- Lows: two retargets now assert screens nobody sees; three text-accepting retargets have no IA-1c expiry; column 5 and the scoped
  headline are unguarded (my plants pass every gate); the Outcomes table at 390 hides the gap and driver columns.

## Checks I ran (heavy ones through `tools/heavy-slot.sh`, env.sh sourced)

| Check | Result |
|---|---|
| `node tools/ia_gates.cjs` (worktree) | 34 runs, landed IA-1a, IA-1b, all as expected, 302.2 s; first failing lines identical to the packet's table |
| `ux_interaction_check.cjs` (scratch copy) | 359 PASS, 1 FAIL: "overview drawer assure … Tab stays inside" |
| `ia_shots.cjs` (`SHOTS_ONLY=hub`) | 108 measured, 0 bad; headlines 1-2 lines at 1440/1280; 3 lines only at 390 (Overviews and Sites, not gated) |
| own probe (`probe.cjs`): 36 full-page shots (12 routes × 1440 light, 1280 dark, 390 light, all 3 operators), P4, budget, addresses, Q1 | no sideways scroll anywhere; findings below |
| `parts_identity.cjs` vs `eb11251e9` | split commit `772bcf002`: 40/40 identical; head: 37 identical, 3 sticky only (Kisiwa, Mto, Ruiru, no-recommendation), 0 differ |
| `node build.mjs` in a copy, `cmp index.html` | in sync |
| `check-architecture.ps1` | passes (with `ASSETOPS_GUARD_PYTHON` pointing at main's `.venv`; the worktree has none) |
| `check-agent-workflow.ps1` | passes |
| Scope | only `vNEXT/`, `specs/`, `.ai/state/`, the register; no `frontend/src`, manifest or evaluator change |

Cited, not rerun: G3 36/36 with clip/root plants, shell_check, plan_switch 781/0, vocab, copy, design_lint, hand_typed, render_text (79
of 237 differ, all routing). `check_manifest` H9 4502 vs 4501 fails on main too, so it is not counted here.

### My plants (scratch copies `rev-ia1b-r1/p-*`, each rebuilt)

| Plant | What it breaks | Result |
|---|---|---|
| `details` | the plan tile's link wrapped in a closed `<details>` (one more click) | **click_depth_check PASS**, plan still depth 1 (M2) |
| `adverse` | `iaLargestAdverse` picks the *smallest* adverse driver | **count, outcomes_table and click_depth all PASS** (L3) |
| `headline` | Outcomes headline counted over all Sites, not the scoped rows | **all PASS** (L4) |
| `pill` | the Site sticky pill's predicate drops `none` | count_check FAILS (kisiwa, mto, ruiru under no-recommendation): this gate works |

## Findings

### M1 (Medium; acceptance gap, spec §6 item 4): the Assure drawer's focus trap is broken on `#/portfolio`
- `loop-ux.js`, the drawer keydown trap; the cause is `iaUnlink` turning "Open Scope & coverage" into text.
- **What I saw.** All three operators: one Tab after Close lands on "Contribution's bridge…"; the next Tab leaves the open modal
  dialog for the review bar.
- **Why it matters.** It is a keyboard and accessibility regression on the first screen the owner sees, and uxi is not green.
- **Q1, my view.** Fix it in IA-1b; do not wait for IA-2d.
  - This unit caused the regression.
  - The bug is a class, not one link: the trap treats elements inside a closed `<details>` as focusable. Any drawer whose last
    focusable sits in a closed disclosure has the same hole.
  - The fix is one filter: skip elements inside a closed `details`, other than its `summary`. Add a uxi plant that puts a closed
    `details` with a link at the end of a drawer.
  - Waiting for IA-2d leaves a known failing gate merged on `main` for several units.
- **Process.** It needs the Architect's word, because the trap is reviewed code that D-IA.22/24/28 do not list. Nothing else in this
  review blocks on Q1.

### M2 (Medium): G1 counts links inside a closed `<details>` as zero extra clicks, so the largest-driver depth is understated
- `tools/click_depth_check.cjs` `readEdges`: only `.ux-drawer` content is excluded.
- **Proof.** Plant `details` puts the plan link behind a closed disclosure; G1 still prints `portfolio › plan` at depth 1 and passes.
- **Live effect.** Every driver opener on a Site page sits in the "What is driving the gap" section, a `uxSecA`. All seven sections
  are closed at load on every Site (probe: `sections open 0000000`). So the owner's real path is four clicks: Outcomes tab, Site row,
  open the section, open the driver. The packet prints 3.
- **Why it matters.** This is the hidden-content class that D-IA.21 closed for drawers. The owner judges G1 ("2-3 clicks") by
  clicking, not by the gate.
- **Fix (measurement).** The reader treats a `summary` as an opener edge to a `details` node and reads the details' contents from that
  node. Extend the fixture test with a closed details and add a plant.
- **Then an Architect call on the outcome.** Either "What is driving the gap" opens by default (it carries the Site's answer), or the
  driver surface's limit changes. Do not adjust the numbers to fit.
- **The answer is already visible.** The section's summary line already reads "X −$N is the largest", so "why is this Site off target"
  is answered at depth 2. Only the drawer is at depth 4.

### M3 (Medium; owner-facing, partly unregistered): a waiting decision is not shown on any hub screen
- `loop-ux.js` `uxSiteParts` (`qMax` 3) with `shapeHubOverview` (top 6, no View all).
- **What I saw.** Lakeside has 3 waiting decisions. `mto-losses` (state `choose`) is 7th of 8 in the Overview queue ("6 of 8") and
  4th of 4 at Mto ("3 of 4"). The Mto lead and sticky say "2 waiting for a choice", but only one waiting row shows. The two rows
  shown above it are "Awaiting approval". Nothing on the hub leads to it until the IA-1c inbox; IA-2b adds "View all".
- **Why it matters.** "What needs me" undercounts on screen on the operator the walkthrough opens with. It is also the honesty class:
  a count says 2 and the list shows 1.
- **Fix.**
  1. Add a register row for the Site queue cap: R749 names only `portfolio`, but the Site's top 3 removes content that the reviewed
     Site page showed (D5, resolving IA-2b).
  2. Ask the Architect whether the capped queues should keep every waiting decision, or rank waiting before approval inside the cap.
     That is a rule, not a re-sort by hand.

### L1 (Low): two retargets assert screens that no live route shows, so they can no longer fail for the product
- `plan_switch_check.cjs` (the residual column, read from `outcomesBySiteScreen()`) and `ux_interaction_check.cjs` "EV board" (read
  from `SCREENS…'ev'.render()`).
- **Live equivalents exist.**
  - Ruiru's "+$20 not attributed yet" is in the Site board answer on `site/ruiru`.
  - Metro's Demand & capacity shows "Revenue · charging is a cost centre · Not applicable", but not the exact string the check wants.
- **Fix.** Retarget each to its live route, shown failing on a plant first (P16), or retire it with a stated reason.

### L2 (Low): the three text-accepting uxi retargets have no expiry
- drill-down `done`, drivers `got`, queue `firstPrim`.
- They accept `.ia-unlinked[data-ia-to^="decision/"]` unconditionally. After IA-1c they would keep passing if a decision link stayed
  unlinked.
- **Fix.** Accept the text form only while `!IA_LANDED.has('IA-1c')`, or IA-1c's card removes them.

### L3 (Low; honest numbers): Outcomes column 5 has no check on the real data
- Plant `adverse` passes every gate. `outcomes_table_check` feeds `driverHtml` synthetically.
- On the demo data, all 9 Sites' column 5 equals the Site board's "… is the largest" answer, which I checked by probe.
- **Fix.** Add a one-source assertion, column 5 against the board's first non-residual row, to `count_check` or a sibling check.

### L4 (Low): the Outcomes headline's scope is guarded nowhere
- `ia-shapes.js` `shapeHubOutcomes`: the scope filter is written twice, once in the shape (which drives the headline) and once in
  the builder (which drives the table). The OUT `scope` plant reaches only the builder; plant `headline` passes everything.
- **Also.** A typed `?scope=group:cold` on Lakeside renders 0 rows under "Every Site is on or above target in October".
- **Fix.** Derive the headline from the builder's in-scope rows. A scope with no Sites should not state "Every Site …".

### L5 (Low; owner-facing polish): the Outcomes table at 390
- The six columns scroll inside the table. "Gap to target" is cut mid-figure ("−$46…"), and the driver and waiting columns are off
  screen.
- The options table already stacks into cards on the phone. The same pattern here would honour the standing brief ("the right
  control per content"). The spec is silent, so this is a preference unless the Architect rules otherwise.

## Judged as asked

- **Retargets with no plant of their own.**
  - The uxi drill-down, drivers and queue-primary changes are sound for IA-1b; they need an expiry (L2).
  - The EV board and the plan_switch residual changes keep green checks on dead builders (L1).
  - render_text's "loop" change (it judges the rendered screen) is correct and explains the `#/cold` case.
- **R748-R750.** They match spec §7's decided deviations and categories (D2; D5 resolving IA-2b). Missing: a row for the Site queue's
  top-3 cap (M3).
- **Gates that can't fail.**
  - The closed-`details` blind spot (M2).
  - The two dead-builder retargets (L1).
  - Column 5 and the headline scope (L3, L4).
  - Every packet plant bites, and I confirmed each first line.
- **Live links to unbuilt screens.** None found: the crawl is clean, `#/portfolio/act-first` has no IA alias, and the decision links
  are text.
  - Owner-visible consequence until IA-1c: "Decide" in the Site sticky, the queue's "Decide"/"Review", and the Insight's "Open …
    decision" read as dead text.
- **No regressions on Decision, Site or plan.**
  - The plan and decision byte identity holds.
  - The one Site diff is the named sticky fix.
  - The legacy Site screen's own "Decide" now also follows the queue primary, as D-IA.22 intends.

## Residual risk not in the packet

- The scope switch changes nothing on the Overview (packet item 5). Every demo operator has one group, so "All sites" and the group
  are the same today, but the owner may read the switch as broken.
- A typed `#/cold` under Lakeside still lands on the legacy board outside the frame and switches the operator (D-IA.28, packet
  item 7). Only a typed address reaches it.
- Demand & capacity's L1 has no `.ux-headline`, so the 2-line headline rule never measures that tab.
- `check-architecture.ps1` needs a `.venv` in the worktree, or `ASSETOPS_GUARD_PYTHON`; the packet's "passes" presumably used one.

Evidence: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/rev-ia1b-r1/`
(`shots/`, `iashots/`, `probe.cjs`, `p-*` plants, `uxi.txt`, `iashots.txt`; scratch, may be cleared).
