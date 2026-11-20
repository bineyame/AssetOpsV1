# Review r2: RECON-1 UI (1b630d9f5) and shell/drill-down r1 fixes (0d73eca32)

Reviewer: fresh Claude reviewer (did not author either commit). Branch `task/uiux-design-model`, snapshot of 0d73eca32
(`git archive`; the built `index.html` is byte-identical to a rebuild from the snapshot's sources). (A) is a discovery
review of 1b630d9f5; (B) is a verification of the r1 findings (`.agent/REVIEW-shell-drilldown-r1.md`) and their sweeps.
Screenshots: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/review-recon-ui/`
(SS/ below; 30 shots, 1440 and 390, East Africa and Neutral, light and dark).

## Round 2 summary

- **Verdict: REVISE.** The reconciliation itself is right: every tie line, the Financials table and the plan groups
  match `derived-values.json` and the RECON table to the dollar, and X1 to X6 each fail when planted. But two classes
  that the commits claim to close are still open on screen.
- H1 (new, A): the typed comparator survives outside the cards. Every decision page's "Who decides" says "Each option
  valued against no action", including the inverter and Ruiru pages, and the plan total's evidence drawer says
  "Plan value = Σ of the valued options' changes against no action" over a sum that holds the inverter claim. This is
  the D-RECON.6 defect (two bases under one name) one click from the headline.
- H2 (B, r1 H3 not fixed as a class): Lakeside and Harvest still see Ruiru's EV connector repair-or-claim table and a
  cross-operator "Not recorded · 2" vendor row; Lakeside Incidents carries Thika's "power-to-cooling chain" copy. Rows with
  no declared key are tagged `data-site="all"`, and S9 accepts "all".
- M: the queue drops Ruiru's "6 more buses offered; all departures met" and shows the meter audit as "Not available yet";
  the plan formula's whole-dollar parts do not add (6,456 − 368 ≠ 6,089); Financials explains "metered but not billed" to a
  cold-chain and a bus-depot executive with no labelled cell; record-id stripping writes "its record" into headings; X7
  misses the original lowercase "revenue explains"; the Overview queue says "6 of 6" under a badge of 8.
- B verified: H1 (driver decisions) and H2 (one share basis) are fixed as classes, with gates that fail when planted;
  H4 has no "None" that contradicts the plan; M1 to M4 and L1 to L6 are fixed, M4 with a new artefact (M5 below).
- The author's deviation from UI item 2 (Grow tile shows its share, not a revenue bullet) is acceptable; reasoning below.

## (A) RECON-1 UI: hand checks against `derived-values.json` and the RECON table

| Check | Lakeside | Harvest | Metro |
|---|---|---|---|
| Overview tie lines (Grow and Optimize drawers) | "Revenue −$97: Grow revenue −$25, and −$72 metered but not billed, counted under Optimize (meters not yet mapped to a customer −$56, authorised adjustments −$16)"; "Optimize −$827: cost to serve −$755, and −$72 …". Correct (−97 = −25 − 72; −827 = −755 − 72). SS/drawer-grow-tie-lakeside-1440-ea-light.png, SS/drawer-optimize-tie-lakeside-390-neutral-dark.png | No tie line, no crossing figure. Correct | No revenue or Grow figure; Grow tile "Revenue: not applicable · charging is a cost centre". Correct |
| Financials "From the statement to the headings" | Revenue: Grow −$25, crossing −$72 (Mto: −$56; −$16), total −$97. Cost: $0, −$755, −$755. Total −$25, −$827, −$852. Correct. SS/financials-lakeside-1440-ea-dark.png | Revenue −$620, "none this month", −$620; cost $0, −$150; total −$770. Correct (see M3). SS/financials-harvest-390-neutral-light.png | Revenue "Not applicable at a captive depot"; cost −$3,184; residual "+$20 not attributed yet". Correct (see M3). SS/financials-metro-1440-neutral-light.png |
| Mto Site economics | "Revenue −$80: Grow revenue −$8, and −$72 metered but not billed …". Correct (D-RECON.1 Site line). SS/mto-economics-1440-ea-light.png | n/a | n/a |
| Tagged figures (`data-figure`) | gap −852, grow −25, optimize −827, revenue_change −97, cost_change −755, metered_not_billed −72, identical on every route | gap −770, grow −620, optimize −150, crossing 0 | gap and optimize −3,184.32 |
| Headline vocabulary | "cost and efficiency explain $827" | "Grow revenue explains $620" | n/a |
| Plan total | "Against doing nothing: Kobo stop setting +$2,916 …; Mto rice huller +$3,540 … (+$6,456). Cost of restoring what failed: Mto inverter claim −$368, to the restore on 28 Nov; nothing after. Net +$6,089." Groups right; rounding see M2. KPI "Change within the next 12 months +$6,089 · Includes the cost of restoring what failed: Mto inverter claim". SS/plan-total-lakeside-1440-ea-light.png | One group: Kirinyaga +$1,512, Mwea +$1,670 over the 4-month contract (+$3,182). SS/plan-total-harvest-390-neutral-dark.png | One group: Kasarani +$150 to the restore on 9 Nov, Embakasi +$95,484 (+$95,634); Ruiru listed beside. SS/metro-plan-1440-neutral-light.png |

- **Ruiru** (SS/ruiru-expansion-1440-ea-light.png, -390-neutral-dark.png): headline "Not valued: an expansion is listed
  beside the plan"; the three context lines read exactly as D-RECON.5 ("2,800 of 3,200 kWh a night, no departure missed";
  "$60,000 and add no capacity: the import limit binds"; "$3,124.80 a month"). Listed beside the plan: "Install 4 more
  chargers: not needed · $60,000 · The rejected alternative; never a saving". The queue's at-stake column reads only
  "Not valued: expansion" (M1).
- **Inverter** (SS/mto-inverter-1440-ea-light.png, -390-neutral-dark.png): column and card heading "Cost to restore,
  against an immediate restore at no cost"; recommended "−$368 to the restore on 28 Nov, against an immediate restore at no
  cost"; no baseline card; the no-action card reads "Never restored: the warranty lapses on 27 Nov, $2,600 of cover lost,
  extra fuel runs on", Rejected. Correct. The "Who decides" panel on the same page contradicts it (H1).
- **mto-losses** (SS/mto-losses-1440-ea-light.png, -390-neutral-dark.png): title, options (meter check Recommended, $60,
  routine maintenance budget, "Not valued: losses are not priced"; no action as the baseline), chooser Site manager Mto
  · David. Correct. **mto-billing**: options MTO-BILLING and no action only; "Choose this", no "Choose another option".
  Correct.
- **C2 counts**: Kobo "2 decisions open" (data-count 2, 2 rows: one under review, one awaiting approval, so none "waiting
  for a choice"); Kisiwa "2 decisions open, 1 waiting for a choice"; Mto "4 decisions open, 2 waiting for a choice"; Thika
  1/1. The dispatch's "2 open, 1 waiting" for Kobo is Kisiwa's line; Kobo's own line is right for its data.
  Thika "Where value leaks": bars neutral, title "No leak against target" (SS/site-thika-1440-neutral-dark.png; see L3).
- **Period menu**: lists the loaded history months; not re-shot.

**The author's deviation from item 2 (Grow tile shows a share, not "Revenue $9,688 against a target of $9,785").**
Acceptable. Item 2 was written against the tile before the drill-down commit; the tile now shows the heading figure only
(Grow −$25 · 3%), so no statement-line figure sits beside it and rule 3 does not call for a tie on the tile. The tie
appears where both figures meet: the Grow drawer opens with "Revenue $9,688 against $9,785" and the tie line, and the
Optimize drawer with its own tie. The Overview surface (SS/overview-lakeside-1440-ea-light.png) shows no revenue figure
an executive could set against Grow −$25. It should be recorded as a MOCK DEVIATION (D2) against item 2 with the ruling's
author informed, since the ruling text still asks for the bullet.

## (B) r1 findings: verification

| r1 | Verdict | Evidence |
|---|---|---|
| H1 driver decisions | Fixed as a class | Metro "Monthly peak import −$600 · Open decision →" (embakasi-schedule via EMB-DEADLINE's `max_kw`); Harvest compensation links thika-backup. The gate's want-set is computed in the check from `DEC`, `option_money_factors`, `service_cost_lines` and `HC.findings`, not from `uxGapModel`'s `decs`. Plant H1b (option-money-factor join removed) fails; see gate table. Note: the service-cost-line rule takes every Protect Finding at the Site, not the line's `protect_measure`; it is right for today's data and the gate mirrors it (L4). |
| H2 one share basis | Fixed as a class | Harvest Grow 67%, Optimize 33% "; +$155 offsets", same on tile, drawer and chart. Plant H2b fails. |
| H3 scope by data | **Not fixed as a class** (H2 below) | `V70_KEYS` scopes keyed rows; unkeyed rows become `data-site="all"` and stay. |
| H4 no "None" contradicting the plan | Fixed | Lakeside Incidents lists Kobo battery, Kisiwa generator 1, Mto inverter 2 from the Findings; Maintenance lists the plan's repairs (Musa 9 Nov, Joseph 13 Nov, David 28 Nov); Metro Incidents lists Kasarani charger 2. A scope note names uncovered Sites. vocab_check now holds the kept lists (they render as in-product). |
| M1 evidence signs | Fixed | "Kobo +$38, offsets", with a Total line. |
| M2 heading drawer twice | Fixed | `categoryCard(…, {fromGap})` drops the driver list; one link label. |
| M3 Show all, status words | Fixed | `[hidden]{display:none}`; S6 status vocabulary. |
| M4 dead affordances | Fixed, with a new artefact | Navigation copy removed; record-id replacement writes "its record" (M5). |
| L1–L6 | Fixed | One switcher (scope menu); not-found without figures note; "Metro Bus Depots’ Sites"; status chips on Grow and Optimize tiles; SHELL_PLANT fails S1 to S10; stub routes go to not-found. |
| S10 before/after | Works for additions | Plant (scope note without `data-ux-added`) fails 34 times. It compares word sets only, so it cannot see removals or changed digits (residual risk). |

## Findings

### H1 · The typed comparator survives outside the cards (acceptance gap, D-RECON.6 item 14 and the plan-total rule)
- **Where:**
  - `loop-site.js:47` (`whoDecides`): "Each option valued against no action. AssetOps recommends …" on every decision page,
    including `#/decision/mto-inverter` (RESTORE_REFERENCE) and `#/decision/ruiru-expansion` (NOT_VALUED).
  - `loop-portfolio.js:296` (`planValueRecord.formula`): "Plan value = Σ of the valued options’ changes against no action … =
    +$6,088.50", in the evidence drawer of the plan total (`port:lakeside:m12`), a sum that includes MTO-INV-CLAIM.
  - Same class: `loop-site.js:17` ("the decision page compares every option against no action", every Site Overview),
    `loop-site.js:31` (Site economics notice), `loop-init.js:47` (decision subtitle), `loop-portfolio.js:211` (Assure
    "Options against doing nothing, with their limits"), `loop-ux.js:662` (no-recommendation heading).
- **Why it matters:** D-RECON.6 rejects exactly this: "it leaves the plan total mixing two bases under one name". The cards
  were fixed, but the sentence explaining the page and the drawer explaining the headline still state one basis. A finance
  reader who opens "how this is worked out" on +$6,089 reads the wrong comparator. The ruling's item 14 requires the typed
  comparator dropped "wherever the basis names itself".
- **Fix (class):** every comparator sentence reads `decBasis(d)` / `optBasis(id)` (BASIS_WORDS); the plan formula uses the
  two groups of `valueNote`. Add a gate: on each decision page and the plan-total drawer, no "against no action / doing
  nothing" phrase where the decision's (or a summed option's) basis is not NO_ACTION.

### H2 · r1 H3 is not fixed as a class: unkeyed v7.0 rows of other operators stay (acceptance gap, C3)
- **Where:** `loop-ux.js` `uxRowSites` / `uxShell`: a row with no key in `V70_KEYS`, no vendor in `V70_VENDORS` and no Site
  name gets `data-site="all"` and is kept; `shell_check` S9 accepts "all". Routes `#/assets-warranty` (all operators),
  `#/incidents` (Lakeside).
- **What:**
  - Lakeside and Harvest see Ruiru's "Repair or claim · its record connector fault" table: "Claim under warranty $0 parts ·
    $120 site labour … ≈5 sessions a day move to connector 1", "Unauthorised repair voids connector cover"
    (SS/warranty-lakeside-1440-ea-light.png, SS/warranty-harvest-1440-neutral-light.png).
  - Vendor performance on every operator shows "Not recorded · 2" (a count from the shared v7.0 table) while Lakeside's
    own vendors (Northwind, Kestrel) are removed because they also serve Thika: the page's warranty table names two vendors
    and its vendor table names none.
  - Lakeside Incidents: "Case boundaries: A correlated power-to-cooling chain supports this incident" (Thika's cold-chain
    copy, about an incident the page does not show; SS/incidents-lakeside-1440-ea-light.png).
- **Why it matters:** the r1 finding was "any v7.0 record that names an asset and no Site passes the filter"; the fix
  moved the hole from "no Site name" to "no declared key", and the gate certifies it. Another operator's data on a tenant
  page is the worst form of C3.
- **Fix:** default-deny: a kept v7.0 row or panel without a key is removed (or the panel is declared per Site in the key
  table, panels included). S9 then fails on `data-site="all"` outside `[data-ux-added]` elements.

### M1 · Queue at-stake: Ruiru loses its unit, and the meter audit reads "Not available yet" (acceptance gap, items 12 and 17)
- **Where:** `loop-ux.js:139` (`uxQueue` builds the stake cell itself and drops `P.wnote`); `uxStakeParts` returns `{num:0}`
  for an INVESTIGATION option.
- **What:** Metro queue: "Not valued: expansion" with no "6 more buses offered; all departures met" (the data has
  `params.added_buses: 6`, `departures_missed: 0`). Mto Site queue: mto-losses "At stake: Not available yet".
- **Why:** item 12 requires the opportunity in its own unit; "Not available yet" is the owner's word for missing data,
  and here nothing is missing: the audit is not valued because losses are not priced.
- **Fix:** render `wnote` in `uxQueue` (one stake renderer, not two); a not-valued option says "Not valued: losses are not
  priced".

### M2 · The plan formula's parts do not add in whole dollars
- **Where:** `loop-portfolio.js` `valueNote` (`usd()` per term). SS/plan-total-lakeside-1440-ea-light.png.
- **What:** "+$6,456 … Mto inverter claim −$368 … Net +$6,089": 6,456 − 368 = 6,088. The data is +6,456.00, −367.50,
  +6,088.50.
- **Why:** this formula exists to show the parts of the headline; a finance reader checks it first. Same class as r1 M2
  (rounding of parts against their total). The headline's own evidence drawer prints the same text in cents
  (−$367.50, +$6,088.50), so the two renderings of one formula also disagree.
- **Fix:** show cents where a term has them (−$367.50, +$6,088.50), or round the terms to their displayed total (`uxRoundTo`).

### M3 · Financials explains a crossing that does not apply, and the zero cell is unlabelled
- **Where:** `loop-portfolio.js` `reconTable`. SS/financials-harvest-390-neutral-light.png, SS/financials-metro-1440-neutral-light.png.
- **What:** Harvest (cold rooms) and Metro (captive depot) both get "Metered but not billed: energy customers used and
  their meters recorded, not yet billed; it lowers revenue on the statement …". Harvest's crossing cell reads only "none
  this month" under "Optimize cost and efficiency", so the defined term appears nowhere in its table. Metro has no
  revenue line at all.
- **Why:** D-RECON.2 rule 4 labels the crossing cell "Metered but not billed" and shows "none this month" for a zero; an
  executive reads an unlabelled "none this month" as Optimize being nil. A definition for a term that cannot occur in the
  operator's vertical is noise.
- **Fix:** label the cell "Metered but not billed: none this month"; at a captive depot replace the note with the residual
  line only. (Also: the cost row's Optimize cell has a dead ternary, `…?'':''`.)

### M4 · X7 misses the defect it was written for
- **Where:** `tools/ux_interaction_check.cjs` X7, `/(^|[.;]\s)Revenue explains/` (case-sensitive, sentence start).
- **What:** planting the pre-fix wording ("…; revenue explains $620 of it.", lowercase, as the audit found it) passes;
  only "Revenue explains" with a capital fails (gate table).
- **Fix:** match case-insensitively wherever a Grow figure is labelled, e.g. `/(^|[^w] )revenue explains/i` excluding
  "Grow revenue explains".

### M5 · Record-id stripping writes "its record" into product copy
- **Where:** `loop-ux.js` `uxShell` (`V70_RECORD` → 'its record' in prose). SS/warranty-metro-390-ea-dark.png.
- **What:** heading "Repair or claim · its record connector fault"; "run diagnostics first (its record)"; "(scenario, its
  record)"; vendor row "1 · stop"; Harvest Incidents "Maintenance lead · /".
- **Why:** C4-class copy produced by the fix; `copy_check` does not see it.
- **Fix:** remove the parenthetical or clause that holds a record id, not just the id; add "its record" and dangling
  "· /" to copy_check.

### M6 · The Overview queue says "6 of 6" under a badge of 8
- **Where:** `#/portfolio` (Lakeside), the queue filter counter. SS/overview-lakeside-1440-ea-light.png.
- **What:** "Needs a decision 8" and "View all 8 in Act first", while the filter bar reads "6 of 6".
- **Why:** C2 class (counts read one source); X5 covers only `[data-count]`.
- **Fix:** "6 of 8", or the counter carries `data-count`/`data-count-of` so X5 checks it.

### L1 · The Lakeside Assets pages list Kobo only
- `#/assets`, `#/assets-warranty`: Kisiwa's generators and Mto's inverters, the two failed assets of the demo, are not
  listed; the scope note points to Findings. Honest, not finished; the owner's call on the five v7.0 lists is pending.

### L2 · "+$20 offsets" and "+$20 not attributed yet" name one figure two ways (Metro)
- The Optimize tile and drawer call Ruiru's residual an offset; the KPI and Financials call it not attributed. Use the one
  word "not attributed yet" (SS/drawer-optimize-metro-1440-neutral-light.png).

### L3 · Thika leak amounts stay red when the bar is neutral
- "No leak against target", grey bars, but "3,720 crate-days" and "$86" in the loss colour (SS/site-thika-1440-neutral-dark.png).
  X6 checks the bar only.

### L4 · The service-cost-line join is broader than the data's link
- `uxGapModel` and the H1 gate take every Protect Finding at the Site for a service-cost-line step; the data names the link
  (`service_cost_lines[].protect_measure`). Right today (one Protect Finding per affected Site); a second Protect Finding at
  Thika or Kasarani would be linked wrongly, and the gate would agree.

### L5 · Small copy
- Queue "$70," with a trailing comma (Kisiwa service credit). Ruiru card "$0 · We pay". The Ruiru recommendation repeats
  "listed beside the plan" twice. "These records cover Kobo. For Kisiwa, Mto, see …" (list joiner differs from "Kisiwa and Mto").

## Gate table

All runs used `tools/heavy-slot.sh --` on the snapshot.

| Gate | Clean run | Planted violation | Plant result |
|---|---|---|---|
| render_text | 207 renders, 0 script errors | n/a | n/a |
| vocab_check | 0 hits; 257 hits on 64 review-only routes, not failing (the kept lists now count as product) | n/a | n/a |
| copy_check | 0 hits | n/a | n/a |
| hand_typed_scan | count 0, manifest 0, allow 46/46 used, 0 unused | n/a | n/a |
| plan_switch_check | 778 passed, 0 failed | n/a | n/a |
| design_lint | 0 fails (colour-literal residual notes only) | n/a | n/a |
| shell_check | 0 fails; Lakeside 38, Harvest 34, Metro 35 routes | SHELL_PLANT=1 | FAIL 137: S1 108, S2 3, S3 3, S4 3, S5 3, S6 6, S7 3, S8 3, S9 2, S10 3 |
| shell_check S9 | pass (accepts `data-site="all"`, see H2) | reviewer plant: `uxShell` keeps rows of other operators | FAIL 57 (S9 29, e.g. "lakeside #/assets: S9 4 row(s) … (thika)") |
| shell_check S10 | pass | reviewer plant: scope note without `data-ux-added` | FAIL 34 (S10 34, "text not in the v7.0 page and not marked as added: records, cover, kisiwa, mto …") |
| ux_interaction_check | 188 PASS, 0 FAIL (incl. X1-X7 "79 tagged figures on 21 routes", H1 and H2 for all three operators) | below, run through the gate's own X and H1/H2 blocks, extracted verbatim | below |
| X1 | pass | gap `data-v` +1 on the Overview only | FAIL "X1 gap\|lakeside differs: portfolio −851, … globalfinancials −852" |
| X2 | pass | the tie line's crossing figure renamed (tie dropped) | FAIL "X2 portfolio lakeside: revenue_change −97 and grow −25 differ, with no labelled Metered but not billed line" |
| X3 | pass | every gap figure +1, consistently | FAIL "X3 lakeside: grow −25 + optimize −827 is not the gap −851" (all three) |
| X4 | pass | Harvest zero cell reads "nil" | FAIL "X4 Harvest Financials: the crossing cell reads 'none this month'" |
| X5 | pass | Site headline `data-count` +1 | FAIL "X5 site/kobo: count 3 but 2 …" (and kisiwa, mto, mwea) |
| X6 | pass | every target-bearing leak bar marked `.is-bad` | FAIL "X6 site/kobo, site/thika, site/kirinyaga: a bar marked as a loss is at or above its target" |
| X7 | pass | "Grow revenue explains" → "Revenue explains" | FAIL "X7 portfolio" |
| X7 | pass | "Grow revenue explains" → "revenue explains" (the audit's wording) | **PASS: not caught** (M4) |
| H1 | pass | option-money-factor join removed from `uxGapModel` (decisions and the Findings it brings) | FAIL "Necessary running: wants kisiwa-genset, shows none"; "Monthly peak import: wants embakasi-schedule, shows none" |
| H2 | pass | heading share +5 where the heading has offsets | FAIL "harvest optimize: steps 33%, tile 38%, drawer 38%"; "metro optimize: steps 100%, tile 105%, drawer 105%" |
| check_manifest.py | 7510 passed, 1 failed (H9, see residual risk) | n/a | n/a |
| check_alignment.py | 102 passed, 0 failed (60 C4 words listed for the reviewer) | n/a | n/a |

Two of my first plants did not bite and are not counted: removing only `...moved` from the decision set is masked by the
Findings that `moved` also brings in (the product's output is unchanged), and a share plant that read `g.offset` before it
is assigned changed nothing. The stronger plants above replace them.

## Could not verify / residual risk

- `check_manifest.py`: 7510 passed, 1 failed, "H9 baseline: 4458 checks passed before the history checks == 4503". Neither
  commit touches the pack (`git diff --stat 7c0f075bb 0d73eca32` outside the mock-up is empty), so this comes from the
  merge 7c0f075bb or the environment; the first run also needed the untracked owner brief copied into the snapshot's
  `.agent/`. Route to the data lane to confirm on the author's checkout.
- S10 compares word sets: it cannot see a removed row of this operator, a changed number, or reordering.
- `render_text` renders the kept lists for Lakeside only; Harvest and Metro kept lists were checked by my own crawl, not
  by vocab_check.
- I did not run full suites or the recapture (UI mock only).
