# IA-2a review, round 1 (discovery, W5): the plan shape

Reviewer: fresh Claude reviewer (did not author the work). Branch `task/IA-2a-plan`, head `242303a11`, diff `main...242303a11`
(main at `2ef8e9769`; its vNEXT `index.html` is byte-identical to the builder's `main-index.html`). Evidence and logs:
`/opt/assetecon/evidence/IA-2a/review/`.

## Summary (round 1)

- **Verdict: ACCEPT WITH FIXES.** Two Medium findings, both against the owner's standing UI brief rather than against
  spec §5.1's wording. Each needs an Architect ruling before the fix (new copy, or a layout rule §5.1.7 does not allow).
  Merge stays held for the owner's IA-2 walkthrough (`USER_REVIEW_REQUIRED: true`).
- The build matches spec §5.1: four live routes from one shape, L1 identical on the tabs, placement as in §5.1.2, approval panel
  gone (R757), History as in §5.1.4, `docTitle`, a single state source (`PSTATE()` only in `iaPlanHistory` for
  version/proposed/opened). `loop-ux.js`/`loop-portfolio.js` hunks are the four splits only.
- Gates rerun: `parts_identity` 282/282 byte-identical; `plan_shape`, `plan_switch` (793/0), `count`, `shape`, G1, `copy` pass
  unforced (no "dormant"); all 14 plants I ran fail with the packet's first lines.
- **M1** Spend tile and release line show two figures with no reason given. Cause found: one item per operator is released when its
  Action is created (under the spend threshold), so the line leaves it out.
- **M2** At 390, switching tabs changes nothing on the first screen: the tab body starts 920 to 1086 px down on an 844 px screen.
  At 1280 × 720 the body's heading is visible (570 to 653 px), so not a finding there.
- Low: an empty fourth tile column (already on `main`); a new hand_typed hit (the packet calls it pre-existing on `main`, which it
  is not); the case link departs from D-IA.51 without saying so; `.ai/state/index-2.md` conflicts with current `main`.

## Findings

### M1 (Medium, honest numbers; not an acceptance gap of §5.1): two spend figures for one plan, no reason given

**Where.** `ia-shapes.js:85` `iaPlanHead` places `p.ap.releases` (`loop-portfolio.js:470`, `approvalParts`) directly under the
band's spend tile (`loop-ux.js:396`, `uxPlanBandParts`), on every tab and every operator.

**What.** Tile "Plan spend $3,750 of $5,000" against "Approving releases … $3,660 of one-off spend" (Lakeside); $720 vs $620
(Harvest); $1,590 vs $1,500 (Metro). Neither line says why they differ. The same gap shows after Approve ("Released with the
approval: … $3,660").

**Cause** (`spendgap.cjs` / `spendgap.log`). The tile is `planCase(op).spend`, the sum of every item in the case. The line is
`waitingSummary(op, ids).spend`, which sums only `waitItems`: items with no `releaseOf(op,id).at`. One item per operator has
`releaseOf().code === 'AT_CREATION'`, meaning its Action was released when created because it was within the spend and crew
thresholds:
- Lakeside: KOB-STOPSOC, $90 (3,750 − 90 = 3,660; also "5 items" of 6).
- Harvest: THIKA-EPC-STOPGAP, $100 (720 − 100 = 620).
- Metro: KAS-OEM-STOPGAP, $90 (1,590 − 90 = 1,500).

Both numbers are correct, and both are reviewed copy reused byte for byte. On the reviewed page, though, the line sat in a side
panel titled "Approval". IA-2a puts it in the header, one line under the tile, so a reader sees two totals for one plan with
nothing to reconcile them. The owner's brief ("honest numbers"; wrong-looking numbers on a clean page are worse than clutter)
makes this a Medium.

**Fix** (Architect copy ruling; §5.1.6 says nothing else is new). Add one IA-only clause in `iaPlanHead`, after `p.ap.releases`,
so `planScreen` stays byte-identical. Build it from the same one-source helpers: items in `planCaseIds(op)` that are not in
`waitingSummary(...).waitItems`, their `releaseOf().spend` summed. For example: "{$90} more was released when its Action was
created ({item}), within the spend threshold." Hide it when there are none. Gate: `plan_shape_check` asserts tile spend =
release-line spend + the clause's spend in the three states, with a plant that drops the clause.

### M2 (Medium at 390; not a finding at 1280 × 720 or 1440): tabs switch nothing visible on a phone

**Measured** (`tabfold.cjs` / `tabfold.log`, all 36 operator × width × tab combinations). The top of the tab body (`[data-level=L2]`):

| width | Lakeside | Harvest | Metro | viewport |
|---|---|---|---|---|
| 1440 × 900 | 694 | 718 | 674 | in view |
| 1280 × 720 | 590 to 620 | 622 to 653 | 570 to 601 | heading in view (the bottom 70 to 150 px; about 88 px of that window is review chrome, not product) |
| 390 × 844 | 1026 | 1086 | 920 | **below the fold on every tab** |

At 390 the first screen on all four tabs is the same: H1, the tab strip, the stepper, the tiles and the act row. Only the tab
underline moves (`harvest-plan-review-390.png`, `lakeside-plan-history-390-light.png`). The spec built exactly what §5.1.2 says
("L1 identical on the four"), so the builder made no mistake. But a tab whose effect cannot be seen breaks the brief's "one
interaction grammar" (a tab switches content) and "right control per content" on the phone. This is not High: the primary demo
width (1440) and the laptop width work, and the Approve journey is intact everywhere.

**Fix** (Architect ruling). One rule for every tabbed shape, not a plan-only patch. Below the 760 px breakpoint, on a tab
switch, scroll the tab strip to the top of the viewport (L1 stays identical; one grammar), **or** show a compact L1 on
non-default tabs at phone width (stepper, chip and Approve only). Gate: an `ia_shots` clause that fails when, after a tab
switch at 390, the tab body's first heading is outside the first viewport; plant: no scroll on switch.

### L1 (Low, mock fidelity; already on `main`): three tiles leave an empty fourth column

`.heroes.ux-kpis` is a 4-track grid (`ux.css:55`, and `:213`/`:214` below 1440). Harvest and Metro have one crew limit, so
they get three tiles: the last tile ends at 1116 of 1416 px at 1440, 994 of 1256 at 1280, and at 390 the value tile sits
alone in the left half (`tabfold.log`: `kpis 3 last 191 grid 374`). The mock's L1 row has three meters filling the row.
**Not High.** The order and content match the mock, and the track count comes from the reviewed band on `main`, where all
three operators had three tiles in four tracks. IA-2a only filled Lakeside's row. **Fix (cheap; same round if the Architect
allows a fourth `ia.css` rule):** `.ia-frame [data-shape="plan"] .ux-planband .heroes.ux-kpis:not(:has(> :nth-child(4)))
{grid-template-columns:repeat(3,minmax(0,1fr))}` with a phone rule to match. Otherwise take it to the walkthrough.

### L2 (Low, packet claim incorrect): the hand_typed hit is new in this diff, not pre-existing on `main`

I ran `hand_typed_scan.py` on the branch: count 1, `loop-portfolio.js:590` "Rights measures by contract and period (as of 6 Nov)".
On a `git archive` of `main` it reports **count 0** (`hand_typed-main.log`). The string is on `main` at line 589, but inside a
backtick template, and the scanner blanks templates before it scans quoted literals. The `whatChangedParts` split moves it into
a top-level quoted literal (`rightsM:sec('…')`), where the scanner sees it. So the hit is in this diff, and the packet's
"pre-existing on `main` … not in this diff" is wrong. The rendered text is unchanged, and the scan still exits 0. **Fix:**
correct the packet line. Optionally write the literal as `` `Rights measures by contract and period (as of ${fdate(AS_OF)})` ``,
which renders the same string, so `parts_identity` holds. Residual risk: the scanner never scans quoted literals inside
templates, so other typed dates may be hiding (backlog).

### L3 (Low, undeclared deviation from D-IA.51): the case link target

`ia-shapes.js:84` uses `href="#sw-h"` on Items and Left out and `#/plan` on Review and History. D-IA.51 says `#/plan` on all four,
"so L1 stays identical", and `plan_shape_check` rewrites `#sw-h` before comparing (its header says so). The choice is better
(probe: on Items and Left out the hash stays on the route and the switches scroll into view, at 1440 and, once settled, at
390). But it is not in the packet's notes or the register. **Fix:** a packet line, and the Architect ratifies it in
`rulings-3.md`.

### L4 (Low, merge mechanics): `.ai/state/index-2.md` conflicts with current `main`

`git merge-tree --write-tree main 242303a11` reports a conflict in `.ai/state/index-2.md` (DS3 merged after `af7847ac2`). Keep
both sides at merge, as at `af7847ac2`.

### Builder's note 4 (walkthrough polish, no finding)

These are confirmed as described, and none conflicts with §5.1. Review shows "Not yet" once as plain text and once as a chip
(reviewed copy; R759). History rows run the actor into the label because the `<small>` has no separator. The Items L2 heading
repeats the H1.

## Checks run (by me, head `242303a11`, heavy slot, pw env)

- `parts_identity.cjs main-index.html`: **282 cases, 282 byte-identical, 0 sticky only, 0 differ** (planScreen 48, planParts 48,
  approvalParts 48, uxPlanBandParts 48, whatChangedScreen 18, whatChangedParts 18, earlier jobs 54).
- Unforced, base runs: `plan_shape_check` PASS; `plan_switch_check` **793 passed, 0 failed**; `count_check` PASS; `shape_check`
  PASS; `click_depth_check` PASS (plan 1, each tab 2, inbox 2, plan items reported against 3); `copy_check` IA-2a block 4802
  strings, 0 stray. No output says "dormant".
- Plants, each rc=1 with the packet's first line: PLAN `place`, `cap` (History only, per D-IA.52 R7), `l1`; COUNT `planstep`,
  `planhist`; PS `crewtile`, `release`, `leftout`; SHAPE `doctitle`; G1 `plantabs`; COPY `plan` (`subset.log`, `run-*.log`).
  Not rerun by me: PLAN `tabs`, `approval`, `thr`, `stepdone`, `revised`, `sticky`; COUNT `planver`; UXI `planans`, `planwait`. These
  rest on the builder's after-flip `gates.log` (76 runs, 0 BAD, 3575.6 s at `a4737f102`). `git diff a4737f102 242303a11 -- <vNEXT>` is empty:
  the merge of `main` and the packet commit touch no vNEXT file.
- Browser (`tabfold.cjs`, `probes.cjs`, `probe390.cjs`): the 4 tabs × 3 operators × 1440/1280×720/390. No sideways scroll, 0
  page errors, document titles distinct ("Left out · …", "Review · …", "History · …"). L1 tiles: Lakeside 4, Harvest 3, Metro 3.
  Back from History returns to Left out. My shots and logs are in the review folder. I also looked at the builder's shots
  (`3b/shots/`, Lakeside 1440/1280/390, Harvest 1440, Metro 1280).
- `check-architecture.ps1`: passed. It needs `ASSETOPS_GUARD_PYTHON` because the worktree has no `.venv`; without it the chain
  guard refuses to run. `check-agent-workflow.ps1`: passed.
- Diff scope: vNEXT, its tools, `walkthroughs.md`, this folder, `.ai/state`, `specs/INDEX.md` and the register only. No
  manifest, backend or `frontend/src` change.

## Not verified by me

The full forced and unforced `ia_gates` runs (about 1 hour each; I cite the builder's at `a4737f102`). The full `ia_shots`
(601/0), uxi (386/0), G3, render_text, check_manifest and the fast check-all. Dark mode, which I did not look at. The dialog,
toast and Undo journey by hand: I rely on `count_check` and uxi, which assert it. `tools/layout-evidence.mjs` was not run
(needs a served URL); the packet records it as not run, not as a pass, and `ia_shots` measures the layout.

## Residual risk not named in the packet

- The hand_typed scanner's blind spot (L2): quoted literals inside templates are never scanned.
- M1's class goes beyond the plan. Any L1 that puts a total beside a subset of the same total needs its reconciling clause.
  Sweep the Overview's plan tile ("Spend and crew visits against their limits") when the fix lands.
- M2's class: every tabbed shape with a tall L1 (the Portfolio group at 390 too) has the same phone behaviour. The ruling
  should be general (W6).
