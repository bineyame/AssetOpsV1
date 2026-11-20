# Review r1: Portfolio drill-down (e7f5566ac) and one shell model (d458c13f0)

Reviewer: fresh Claude reviewer (did not author). Branch `task/uiux-design-model`; this reviews a snapshot of d458c13f0
(`git archive`, built `index.html` byte-identical to a rebuild from the snapshot's sources). Screenshots:
`/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/review-shell/` (SS/ below).

## Round 1 summary

- **Verdict: REVISE.** Every gate passes, and every gate fails when a violation is planted. But the gates miss four content-truth or scope defects that an executive would hit in the demo.
- What works: one drawer grammar. Steps, headings and tiles open in place and nothing navigates. The new Findings and Actions lists read the plan's store and are good. There is one period chip and one Site name. The stub tabs and "(earlier view)" are gone, and there is a real not-found page.
- H1: a driver drawer says "No Finding names this driver yet / No decision yet" when the chosen option moves that driver. Metro "Monthly peak import −$600" is the clearest case. The join uses only the Finding's factor.
- H2: Harvest shows two shares for the same $620 on one screen: the Grow tile and drawer say 81%, while its only step says 67%. Heading shares use net subtotals; step shares use gross widening.
- H3: C3 is not fixed on Assets › Warranty & vendors. Every operator still sees the cold-room, generator and charger assets of the other operators. `shell_check` S3 cannot see this, because it uses the same name match as the fix.
- H4: the kept v7.0 lists now say "None at Lakeside Power's Sites" (Incidents, Maintenance) and list one Site's assets. They do this while the Portfolio and the plan show generator 1 and inverter 2 failing at Kisiwa and Mto. A second record universe (F-104, ACT-048, WR-019, INC-203) is still in the navigable product.
- Item 3: removing the v7.0 operating views from the navigation is right as an interim step, not as the end state. Recommendation below.
- Item 4: removing the cross-operator count tiles is right. Tiles come back only when they are computed from the scoped list.

## Findings

### H1 · "No decision yet" is not always true (acceptance gap, content truth)
- **Where:** `loop-ux.js` `uxGapModel`, `finds`/`decs` (the `(st.hkeys || []).includes(f.factor)` join) and `uxDriverBody`. Route `#/portfolio`; drawers `uxdrv-metro-optimize-1` and `uxdrv-harvest-optimize-2`.
- **What:**
  - **Metro "Monthly peak import −$600" (SS/drawer-uxdrv-metro-optimize-1-metro-390x844-east-africa-dark.png):** the drawer says "No Finding names this driver yet. No decision yet." But:
    - the Finding `embakasi-import-limit` reads "Monthly peak import 500 kW: at the 500 kW limit". It shows on the Findings page as "Chosen · awaiting approval" (SS/findings-metro-390x844-east-africa-dark.png);
    - its decision `embakasi-schedule` chose EMB-DEADLINE, and the manifest's `option_money_factors` lists `max_kw` among that option's money factors (EMB-DEADLINE: [peak_kwh, kwh_0000_0500, kwh_2200_2400, max_kw]).

    The decision that is under way moves this $600, and the drawer says nothing is being done.
  - **Harvest "Customer compensation −$108":** "No Finding names this driver yet". The Thika excursion Finding is its cause, and the Optimize card itself says the compensation is linked to "batches exposed".
- **Why it matters:** the owner's brief asks that every number be honest. This dispatch names "No decision yet is honest" as a check, and it is false on the largest no-decision step in Metro.
- **Fix (a class rule, not an instance):**
  - A step's decisions are those whose Finding factor is the driver, **or** whose chosen or considered option lists the driver's factor in `option_money_factors`.
  - A step's Findings include Findings on the linked Protect measure, as the Optimize card already does.
  - Add a gate assertion: for each driver drawer, the set of decisions equals the set derived from `option_money_factors` plus the Finding factor.

### H2 · Two shares for one amount on one screen (content truth)
- **Where:** `loop-ux.js` `uxGapModel`. `gShare` uses net heading subtotals; `share` uses each step's gross widening amount. Both are worded "% of what widens the gap". Route `#/portfolio` (Harvest).
- **What:**
  - The Harvest Grow tile and the Grow drawer say "−$620 · 81% of what widens the gap".
  - Its only step, "Occupied crate-days −$620", says 67% in the chart and in its own drawer. SS/drawer-uxd-harvest-grow-harvest-1280x720-neutral-dark.png shows both at once: 81% in the drawer, 67% in the chart behind it.
  - Optimize reads 19% at the heading, but its steps read 21% + 12% plus an offset.
  - Lakeside is unaffected only because it has no offsets.
- **Why it matters:** a finance reader finds this in seconds (the same failure as audit C2). The gate passes because it checks only that the drawers open, not that the figures agree.
- **Fix:**
  - Use one denominator. Either the heading share is the sum of its widening steps' shares (Grow 67%, Optimize 33%, with "+$155 offsets" stated), or both use net figures and the word changes.
  - Extend `ux_interaction_check` to assert that a heading's share equals the sum of its steps' shares, and that the tile, the drawer and the chart agree.

### H3 · C3 is not fixed: Warranty & vendors shows every operator's assets (acceptance gap)
- **Where:** `loop-ux.js` `uxShell`. The scope filter removes a row only if its text names another operator's Site. Route `#/assets-warranty`, all three operators.
- **What:**
  - **Lakeside** sees 17 rows, including "CMP-003 · Cold-room compressor", "the backup generator · Backup generator", "BAT-CR-01 · Cold-room battery", "CHG-002 · Connector 2 charger" (Ampere Charge Co, "Diagnostics first · ACT-061") and "Vendor performance · Across all sites".
  - **Harvest and Metro** each see 14 rows with the same leak.
  - Any v7.0 record that names an asset and no Site passes the filter.
  - `shell_check` S3 uses the same name heuristic, so it is blind to the class it claims to gate.
- **Why it matters:** C3 is one of the three classes this commit claims to fix, and showing another tenant's data is the worst version of it.
- **Fix:**
  - Scope by data, not by rendered text. Tag kept v7.0 rows with their Site key at rebase time, or take the asset tables out of the navigation until they are converted.
  - Make S3 check a data attribute (every row's `data-site` is in `OPS[op].sites`) instead of the text match.

### H4 · The kept v7.0 lists contradict the plan (C1.4 leftover; content truth)
- **Where:** `#/incidents`, `#/maintenance`, `#/assets`, `#/oprecords` and `#/globalevidence`, all scoped by `uxShell`. SS/assets-lakeside-1440x900-east-africa-light.png, SS/assets-metro-390x844-east-africa-dark.png.
- **What:**
  - **Lakeside Incidents and Maintenance:** "None at Lakeside Power's Sites in this demo". The Portfolio, the Findings and the plan say generator 1 failed at Kisiwa on 30 Oct, inverter 2 failed at Mto on 28 Oct, and "Repair the Kisiwa alternator" is planned (Musa, 9 Nov).
  - **Metro Incidents:** "None", while Kasarani charger 2 has been down since 1 Nov.
  - **Asset inventories:** Lakeside lists only Kobo's three assets; Harvest lists only Thika's; Metro lists one Ruiru charger. Embakasi and Kasarani, and Kirinyaga's condenser, are missing.
  - **Old record ids:** rows still carry v7.0 ids that exist in neither new list ("1 · F-104", "2 · ACT-048", "F-118", "WR-019", "ACT-061", "INC-203").
  - **Vocab gate exemption:** a scan of these now-navigable routes with the vocab_check rules gives 30 hits (record and asset codes, "Tenant", "feature switches"). `vocab_check` still files these routes as "earlier-view body" and does not fail them.
- **Why it matters:** this is the "two Action universes" instance, moved from Actions to the lists next to it. An empty "None" that contradicts the Portfolio is worse than the old cross-operator banner.
- **Fix:** each list either:
  - reads the plan's store (Findings with a Protect heading become Incidents; plan Actions with a repair become Maintenance; the assets named in decisions are listed for all 9 Sites); or
  - leaves the navigation like the other review-only screens.

  Also make vocab_check's "fails" flag follow `uxInProduct`, not `r.loop`.

### M1 · Evidence-by-Site signs are not explained in a "widens" drawer
- **Where:** `loop-ux.js` `uxDriverBody`, the Evidence list. SS/drawer-uxdrv-lakeside-grow-0-lakeside-1440x900-east-africa-light.png.
- **What:** "kWh sold −$25 · 3% of what widens the gap" is followed by "Kobo: +$38 · Kisiwa: −$55 · Mto: −$8" with no words. A plus sign under a "widens" headline reads as an error.
- **Fix:** label each mixed-sign row with its direction ("Kobo +$38, offsets"), or group the rows under "Widens" and "Offsets", as the chart already does for steps. Add a sum line that reconciles to the step.

### M2 · The heading drawer says everything twice, in two vocabularies
- **Where:** `uxd-*-grow` and `uxd-*-optimize`. `uxHeadingTop` is placed above the unchanged `categoryCard`.
- **What:**
  - **Driver names:** "kWh sold" appears again as "Customer consumption against target"; "Fuel not explained" as "Fuel used beyond what the generator model explains".
  - **Precision:** "−$412" appears again as "−$412.50".
  - **Link labels:** "Open decision →" sits next to "Decision →".
  - **Rounding:** the "Generator needed" drawer lists −$37, −$104 and −$25 (sum −$166) under −$167, because `Math.round(−37.5)` gives −37.
- **Why it matters:** the owner's complaint was repetition, and the brief asks for one grammar.
- **Fix:**
  - The heading drawer keeps the new top only. Drop "Driver effects on contribution" from `categoryCard` when it is opened from the gap.
  - Use one driver label (`GAP_SHORT`) and one link label.
  - Round step evidence with `uxRoundTo` to the step's displayed value.

### M3 · Findings list: "Show all" does nothing, and a new status word
- **Where:** `ux.css` `.ux-flist>li{display:grid}` overrides `[hidden]`; `uxFindingRows` falls back to `'Linked'`. SS/findings-lakeside-1440x900-east-africa-light.png.
- **What:**
  - **Show all:** Lakeside shows all 8 rows and a "Show all 8" button that does nothing visible.
  - **Status word:** two rows carry the status "? Linked" with the decision's title as the issue text ("Kobo battery warranty evidence", "Kisiwa late repair response and service credit"). "Linked" is not a status in either vocabulary, which is the C1.3 class.
- **Fix:**
  - Add `.ux-flist>li[hidden]{display:none}`.
  - Give these Findings their real status and issue text (they are in `HC.findings` and the manifest).
  - Add an S6 sub-check that every status label comes from the one enum.

### M4 · Dead affordances left after unlinking
- **Where:** `#/assets` (all operators).
- **What:**
  - The copy says "Opening an asset moves you to its own pages" and "Detailed asset pages are shown for the battery in this mock-up". The rows are now plain text.
  - Harvest and Metro have no battery in the list.
  - "the battery · Kobo battery" and "the backup generator · Backup generator" are rebase naming artefacts.
  - "in this mock-up" is C4 wording, and S4's pattern does not match it.
- **Fix:** when `uxShell` unlinks a list's rows, remove the copy that describes the navigation. Add "in this mock-up" (outside the plan's Approve note) to the S4 pattern.

### L1 · Two Site switchers on Site pages
- `#/site/*`: the scope menu ("Kisiwa ▾") sits beside the "Kisiwa · Mini-grid" select (SS/site_kisiwa-lakeside-390x844-neutral-light.png, SS/site_thika-harvest-1280x720-neutral-dark.png).
- The audit flagged this under C1/C15. Keep one.

### L2 · Not-found page details
- The rail highlights Portfolio on the not-found page, and "About these figures" shows on a page with no figures (SS/no-such-page-lakeside-1440x900-east-africa-light.png).

### L3 · Possessive of "Metro Bus Depots"
- "Metro Bus Depots’s Sites" appears in the Findings heading and in the "None at …" rows.

### L4 · Grow and Optimize tiles drop their status word
- The Grow and Optimize tiles lost their status word ("Off target") while Protect and Assure keep theirs ("↘ Limits broken"). The four tiles no longer read as one set.

### L5 · `SHELL_PLANT` covers only S2, S3, S4 and S7
- S1, S5, S6 and S8 have no plant of their own. I planted each of them and each fails (gate table below); add them to the tool's plant.

### L6 · Stub routes still answer by URL
- `#/site/kisiwa/health` and the other stub routes still render "Not built in this mock-up … see Kobo, Thika or Ruiru". They are reachable only from the review bar's Screen index; the product search lists only the scoped screens (SS/topbar-search-harvest-1440-neutral-light.png).
- Route them to not-found, or to the Site Overview.

## Item 3: the v7.0 operating views (owner-level recommendation)

**Recommendation: keep them out of the navigation for the walkthrough, and queue one converted "Operations" tab for all 9 Sites as demo-critical work. Do not treat the current state as the end state.**

Removing them was right as it stands:
- the views exist only for Kobo, Thika and Ruiru;
- they run on a 6 Oct one-hour event window, with other names and other status words;
- for six Sites the tab was a stub;
- putting them back as they are brings back C1 and C4 on every Site.

The cost is real, though. With only Overview and Financials, a Site has no operating view at all: no dispatch, no temperature, no sessions, no asset health. An operator executive judges "value beyond monitoring tools" against the monitoring they already have. The owner's own frame is "a solid core" with Layer 4 as boosters on top, and a product that shows the boosters with the core hidden reads as a finance overlay.

The fix is structural, not a link:
- one "Operations" tab, the same for every Site type: its measures against target for the period chip, plus the Site's assets with their state;
- converted from v7.0 for the three Sites that have data;
- with an honest "not available yet" inside the same structure for the six that do not (owner rule: missing data stated in the UI, the same on every Site).

The Site Overview's "Operations measures at this site" section is the seed of that tab.

## Item 4: the count tiles removed from the kept v7.0 lists

Removing them is right. They counted three operators together, so for any one operator they were wrong numbers. On lists of 1 to 3 rows a count tile adds nothing.

The mechanism is blunt, though: `uxShell` removes any `.cards` or `.statusbar` block that holds a digit. Under the audit's C2 rule ("count tiles and the lists under them read from one source"), tiles should come back only where the list is long enough to need a summary, and only computed from the scoped list. The page is not weaker today; it would be on a 300-Site operator, where those summaries matter.

## Gate table

All runs used `tools/heavy-slot.sh --` on the snapshot.

| Gate | Clean run | Planted violation | Plant result |
|---|---|---|---|
| render_text | 206 renders, 0 script errors | n/a | n/a |
| vocab_check | 0 hits (287 "earlier-view" body hits not failing; see H4) | n/a (existing VOCAB_PLANT not rerun) | n/a |
| copy_check | 0 hits over 13,044 segments | n/a | n/a |
| hand_typed_scan | count 0, manifest 0, allow 46/46 used, 0 unused | n/a | n/a |
| plan_switch_check | 777 passed, 0 failed | n/a | n/a |
| design_lint | 0 fails (residual colour-literal notes only) | n/a | n/a |
| shell_check | 0 fails; routes crawled: Lakeside 38, Harvest 34, Metro 35 | SHELL_PLANT=1 | FAIL 164 (S2 3, S3 31, S4 3, S7 127) |
| shell_check S1 | pass | period chip replaced by the range picker on Findings | FAIL 3 (S1, one per operator) |
| shell_check S5 | pass | stub "Health" tab put back into the navigation | FAIL 12 (S4/S5 "Not built in this mock-up", S3) |
| shell_check S6 | pass | Findings `data-count` set one higher | FAIL 3 (S6 "count 9 but 8 listed", …) |
| shell_check S8 | pass | unknown route falls back to the Portfolio | FAIL 3 (S8) |
| ux_interaction_check | 176 PASS, 0 FAIL; drill-down: Lakeside 12, Harvest 10, Metro 8 marks, all in place | driver drawer without "No decision yet" (DD); a chart step that navigates (DD2) | see below |

Drill-down plants (both runs exit 1):
- **DD** ("No decision yet." replaced by "Nothing recorded."): the drill-down check fails for all three operators, for example "uxdrv-lakeside-grow-0 does not say what is being done" and "uxdrv-metro-optimize-1 …".
- **DD2** (a step with a decision has no drawer and navigates to its decision): the check fails for all three operators, for example "mark 3 opens no drawer" (Lakeside) and "mark 1 opens no drawer" (Harvest, Metro).

**What the gates cannot see:**
- H1: the decision join;
- H2: shares across tile, drawer and chart;
- H3: rows scoped by text instead of data;
- H4: kept lists that contradict the plan's store.

Each needs the assertion named in its fix.

## Could not verify / residual risk

- I did not run full suites or the 1,414-pair recapture (UI mock only; out of scope).
- I did not open the decision pages behind each "Open decision →"; I trusted `decById` and the plan check's 777 passes.
- Residual risk:
  - `uxShell` rewrites the DOM after render: it removes rows, rewrites "A · B" text nodes and strips trailing separators in every `td`. On any kept page it can silently drop or change legitimate content, and no gate compares the content before and after.
  - The Kisiwa headline "1 decision is waiting" beside "2 decisions open" (audit C2) is still present; it is out of this slice's scope.
