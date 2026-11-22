# IA-2b1 review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer (did not author the work). Branch `task/IA-2b1-lists`, head `549e4f8fa`, worktree
`/opt/assetecon/AssetOpsV1-ia2b1`. IA-2a is not on `main`, so `main...HEAD` carries IA-2a too; the IA-2b1 code was read as
`task/IA-2a-plan` (`f9430112e`, an ancestor of the head) `..HEAD` on `vNEXT/` (18 files), and the docs as `main...HEAD`.
Read against `spec-IA-2b.md` §1 to §5 and §7 to §10, `packet-IA-2b1.md`, `mid-build-questions.md` Q1 to Q8,
`owner/owner-ia2b-defaults-2026-11-21.md`, `owner/owner-ui-ux-guidance-2026-10-25.md` and register rows R761 to R765.

## Summary (round 1)

- **Verdict: READY FOR WALKTHROUGH**, with one Medium (M1) to fix on the branch before merge; it can be fixed before the walk.
  Merge stays held for the owner's walkthrough (`USER_REVIEW_REQUIRED: true`).
- **The lists are as specified at 1440 and 1280.** Four lists from one def table and one component; tiles equal the rows;
  Sort only at the live size; aliases land with their queries; crumbs link; Outcomes is the Sites rows with no button.
- **M1 (Medium, new class on three lists).** At 390, a cell's second line (`<small>`) drops into the label column of the stacked
  card: "over 12 months, against doing nothing" sits under "At stake", "in 3 days" under "Due", "Optimize cost and efficiency"
  under "Largest driver". 17 cells on Lakeside (Decisions 8, Actions 6, Sites 3). `ia_shots` does not measure it.
- **L1 to L3 (Low):** the palette's "Act first · Portfolio" is new in this slice, not left over; the Outcomes fold obeys a typed
  list query with nothing on screen to show it; the after-Approve sweep in `ux_interaction_check` no longer measures what users see.
- **Architect items:** recommend accepting both the `resolveScreen` line (Q1) and the aliases pulled into unit 3 (Q5).
- **Gate at the head:** `ia_gates: 108 runs, landed IA-1a, IA-1b, IA-1c, IA-2a, IA-2b1, all as expected (5169.4 s)`. Fast check-all: `All 42 guards passed (blocking; 0 advisory, 0 warned).`
- **My plant** (no-date-first due sort, scratch copy) fails `list_shape_check` B on all three operators.

## Findings

### M1 (Medium, acceptance gap: spec-IA-2b §8 `ia_shots` "stacked at 390"; owner UI brief "right control per content")

- **Where:** `ia-shapes.js:305` (`iaListBody` writes each cell's HTML straight into `<td data-label>`) with `ia.css:99`
  (`.ia-list td small{display:block}`). Under `max-width:760px`, `table.ux-stack td` is a two-column grid (`index.html:1045`),
  so every child of the `td` is its own grid item. The text goes into column 2, and the `<small>` that follows wraps into column 1,
  under the label.
- **Seen:** `lists-S1-lakeside-decisions-390-light.png` (At stake, Who decides "†"), `lists-S1-lakeside-actions-390-light.png`
  (Due), and `lists-S1-lakeside-sites-390-light.png` (Largest driver: "Optimize cost and efficiency" reads as a field with no
  value). Measured in Chromium at 390 (Lakeside): cell children whose left edge is in the label column: Decisions 8 of 40,
  Actions 6 of 18, Sites 3 of 15, Findings 0, Outcomes 3. The IA-2a base has the same 3 on Outcomes (the deleted
  `iaOutcomeTable` had the same rule), so the class is inherited from IA-1b, but this slice spreads it to three new lists.
- **Why it matters:** the phone is part of the walkthrough. A value shown as a label misreads (an executive sees "Optimize cost
  and efficiency" as a field name). `ia_shots`' fit check passes because nothing overflows.
- **Fix:** wrap each `td`'s content in `<span class="ux-cell">`. That is the reviewed pattern: `index.html:1087`
  `table.ux-stack td>.ux-cell{grid-column:2}`, used by `loop-site.js`. Outcomes is fixed by the same line. Add an S1 measure to
  `ia_shots` (no `td` child starts in the label column at 390) with a plant that drops the wrapper, so the class stays closed.

### L1 (Low, preference with a new cause): the palette's "Act first · Portfolio" is new in this slice

- **Where:** `ia-routes.js:63` (the alias) via `ia-routes.js:182` `iaPaletteFilter`, from the reviewed `PTABS` entry
  (`loop-ux.js:456`).
- **Seen (jsdom, Lakeside):** at head the palette has `["Act first","Portfolio","decisions"]` beside `["Decisions","Go to","decisions"]`.
  At the IA-2a base the "Act first" entry is absent (0 of 15 commands), because `portfolio/act-first` was not live. The packet
  and Q5's note say the palette "still lists" it. It does not: the alias made it live.
- **Why it matters:** the palette names a screen the product no longer has, under the wrong home, two entries to one place. It
  goes against one name per thing in the owner's UI brief. It is not a blocker.
- **Fix (cheap, on the branch):** in `iaPaletteFilter`, drop an entry whose source path is a list alias (or keep only the first
  entry per canonical target). Recommend fixing it with M1 rather than putting it on the backlog, since this slice caused it.

### L2 (Low, acceptance edge: D-IA.70 "a chip for each view state no control shows")

- **Where:** `ia-shapes.js:165` `shapeHubOutcomes` passes the Outcomes route's own `ctx.query` to `iaListBody('sites', …)`.
- **Seen (jsdom):** `#/portfolio/outcomes?sort=name` reorders the rows (kisiwa, kobo, mto, against kobo, kisiwa, mto), and
  `?target=on` empties Lakeside's table ("Nothing matches these filters", with "Clear filters" leading to `#/sites`) under a
  headline "3 of 3 Sites are below target". Nothing on screen shows the state. The fold has no tools and no chips by design (§5).
- **Why it matters:** it is reachable only by a typed or shared address, so the risk is low. But a shared link can show a table that
  contradicts its own headline.
- **Fix:** the fold builds its model from the scope alone (`{ ...ctx, query: {} }` for the list part); "Show all" then still
  carries the scope.

### L3 (Low): the `ux_interaction_check` change (8b7bf29ee) is honest, but the after-Approve sweep lost its live page

- **Where:** `tools/ux_interaction_check.cjs:36` (`actFirst`) and `:613` (the routes after Approve).
- **Judgement:** it is honest, and it does not weaken any assertion it keeps.
  - The reviewed act-first screen is still registered for the review select, and the check says so and removes the alias only
    in its own window, the same as `plan_switch_check` (Q6).
  - The "findings" expectation is the true new state: the Findings list is live and is the first hit.
- **But:** before the flip, `portfolio/act-first` in the after-Approve sweep measured the page a user saw at that address. Now it
  measures a screen users cannot reach, and the Decisions and Actions lists that replaced it are not in that sweep. Block B of
  `list_shape_check` covers Actions after Approve through its own classifier, which is not the same "no WAITING after Approve"
  contract. I checked by hand: after Approve, the Actions list shows only `RELEASED` pills on all three operators (Lakeside 6,
  Harvest 3, Metro 2) and "Waiting 0". Adding `actions` and `decisions` to the sweep would pass today.
- The `/^Findings/` match does not assert the target. That is a nit.
- **Fix:** add `'decisions'` and `'actions'` to the routes at `:613`. Optionally assert that the "findings" hit's `data-go` is
  `findings`.

### Not findings (judged as asked)

- **The 760 px wrap rule (`ia.css`, last line; Q8).** It is sound: it is scoped to `.ia-list`, at the same breakpoint as `ux-stack`.
  It undoes only the global `th` nowrap and the pill's nowrap inside the stacked card. The packet's no-CSS run shows the 51 fit
  failures it removes, and `listwrap` proves the shots bite. A two-line pill ("Released: Actions under way") is readable in the
  shots. No change asked.
- **"Portfolio · Portfolio" in the phone screen menu.** It is the review bar's chooser (a review tool, not the product), and it
  exists on `main` for `#/plan` and `#/portfolio/outcomes`. Backlog it, not a blocker for this slice.
- **The duplicate "Act first" in the palette** is L1: it does not block, but fix it on the branch.

## For the Architect

1. **`resolveScreen` (`loop-core.js:341`, Q1). Recommend accepting it.**
   - The line it replaces already rewrote the address for a live alias. The new line only routes that same write through
     `iaCanon`, the one merger D-IA.78 names. The default would have added hidden state to `iaLiveAlias` and a second address
     write in `iaScreen`.
   - The ALIAS, landing, foreign and landed branches are byte-identical.
   - For a non-list alias without a query, `iaCanon` returns `#/{path}{typed query}`, the old output.
   - Probed: `findings-cost` lands on `#/findings?heading=optimize`. `findings-cost?sort=site` lands on
     `…?heading=optimize&sort=site`. `portfolio/act-first?state=waiting&foo=1` lands on `#/decisions?state=waiting`: an
     unknown parameter is dropped for a list target, which is new but harmless. `findings-risks?heading=grow` lands on
     `heading=protect`: the alias's own query wins, as §5 says.
2. **The aliases pulled into unit 3 (Q5). Recommend accepting it.** They were dormant until the flip, because `iaLiveAlias` tests
   `iaLanded` on the target path. The only effect before 4(b) was that `aliasq` could be proved under force, which is the W2
   order. Note the one product effect they bring at the flip: L1.

## Mid-build questions checked against commits

- Q5: the four aliases are in `8b0543c7e` (unit 3). Matches.
- Q6: `plan_switch_check` removes the alias in `c80539d53`, and `ux_interaction_check` does in `8b7bf29ee`. Matches.
- Q7: `3ec99d53f` changes one line of the `notarget` plant. Matches.
- Q8: `b4ea6c7c9` adds the 760 px rule to `ia.css` and the bundle. Matches.
- Q5's coordinator note is inaccurate on one point (see L1).

## Checks run (at `549e4f8fa`)

- `node tools/ia_gates.cjs` (heavy slot, unforced): **`ia_gates: 108 runs, landed IA-1a, IA-1b, IA-1c, IA-2a, IA-2b1, all as expected (5169.4 s)`** (log: `/opt/assetecon/evidence/IA-2b1/review1/gates.log`)

- `pwsh -NoProfile -File tools/check-all.ps1` (fast): `All 42 guards passed (blocking; 0 advisory, 0 warned).` (142 s).
- `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = repo venv): `Architecture check passed.` Without it, the chain
  guard refuses with "no Python interpreter", as the packet noted.
- `tools/check-agent-workflow.ps1`: `Agent workflow check passed.`
- **My plant:** on a scratch copy of the head, the Decisions/Actions due comparator `iaByDue` was changed to put "no date" first
  (Q3's rule inverted), in `ia-shapes.js` and the bundle. `list_shape_check`: `3 FAIL`, one per operator, on
  `decisions · sort=due` ("rows kobo-generator,… B computes mto-inverter,mto-demand,…"). Actions did not bite, because every live
  Action has a due date; the fixture's no-date rows are Sites, not Actions. It is caught.
- **Probes (jsdom and Chromium, scratch):**
  - the palette at head against the IA-2a base;
  - the alias landings;
  - the Outcomes fold with a typed query;
  - the Actions list after Approve on all three operators;
  - stacked-cell positions at 390 on the five list surfaces, head against base.
- **Shots read:** S1 Lakeside Decisions 1440 and 390, Actions 390, Sites 390; S8 sites30 two filters, 1440 dark. Tiles fill,
  groups 14 · 3 · 5 sum to 22, "Not shown: 12 Sites, gap to target −$1,276.80. Show all 22" and a cents tile are consistent.

## Gate

108 of 108 runs as expected, 0 BAD, no "dormant" line: 11 checks pass unplanted (including `ux_interaction_check`, the BAD of the packet's run at `b4ea6c7c9`, now passing at the head after `8b7bf29ee`), and 97 of 97 plants fail. Reviewer logs and probe scripts: `/opt/assetecon/evidence/IA-2b1/review1/`.

## Not verified

- I did not rerun `ia_shots` (the packet's run is at `b4ea6c7c9`; `8b7bf29ee` and `549e4f8fa` touch no product file, which I
  checked with `git show --stat`).
- I did not run `tools/layout-evidence.mjs` (the packet explains why: `file://`). `ia_shots` is the layout gate, and M1 shows a gap in it.
- I did not do the S9 keep-place by hand. I relied on `listkeep` and the S9 log.

## Residual risk

- The Findings and Actions rows open a decision or the plan (R764, D5) until IA-2d. Several rows lead to one page (Lakeside
  Findings: kobo-generator ×2). Say this at the walkthrough.
- A palette query with 12 or more hits cuts at 12 (the reviewed `uxPaletteFill`). The new Finding and Action entries are appended
  last, so an empty query never shows them. Typing finds them.
- Register row R761's last column ("raised in") is empty where R762 to R765 say IA-2b1 (`.agent/mock-departure-register.md:725`).
  This is a nit.
