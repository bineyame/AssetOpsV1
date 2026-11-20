# RECON-1 rulings: figures that reconcile, comparators that say their basis

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines are in `.ai/decisions/index-rulings-6.md`.
Sources: the independent UX audit, finding class C2 (`/opt/assetecon/AssetOpsV1/.agent/ux-audit-2026-11-20.md`), and
the Decision page re-review, M1, owner point (b) and plan totals (`/opt/assetecon/AssetOpsV1/.agent/REVIEW-decision-page-r2.md`).
Pack: `Docs/demo-sprint/product-direction-layer4/` (abbreviated `pack/`), design `rev 16.14`.
Amounts are the evaluator's (`derived-values.json`), checked by `check_manifest.py`; none is typed in a check.

## D-RECON.1 The two splits of the gap: why Grow and Optimize differ from revenue and cost

- **The mechanism.** The contribution gap is cut two ways. The statement cuts it by line: revenue against target, and
  cost to serve against target. The headings cut it by home category: Grow and Optimize. Each bridge row sits on one leaf.
  - Its **line** is the statement line its leaf sits under in the structure. A leaf under both lines (a cold room's
    crate-days drive both revenue and electricity) is read on the line of its own heading.
  - Its **heading** is its leaf's home: named on the row, never inherited (design §2.0, OD-21).
- **One table.** The two cuts are the rows and the columns of one table, line by heading, plus an explicit residual on its
  own row. They differ only by crossing rows. A **crossing row** sits on one line, but its heading is the other line's.
- **The rows that cross today.** Only the service-to-charge rows on revenue, homed under Optimize (O3), cross:
  - `METER_MAPPING_UNBILLED`: node `unmapped_kwh`, "meters not yet mapped to a customer";
  - `AUTHORISED_ADJUSTMENT`: node `adjustments_kwh`, "authorised adjustments".

  Losses before the meter (`technical_loss_kwh`, `unexplained_loss_kwh`) are on the revenue line too, but carry no price.
  They sit inside `DEMAND_VOLUME`'s metered-kWh effect, so they do not cross. No cost-line row sits under Grow.
  Collection is cash, outside both cuts.

| Operator | Revenue (row) | Grow (column) | Crossing: metered but not billed | Cost to serve (row, as effect) | Optimize (column) | Gap |
|---|---:|---:|---:|---:|---:|---:|
| Lakeside Power | −97.00 | −25.00 | −72.00 (Mto only: unmapped −56.00, adjustments −16.00; Kobo 0, Kisiwa 0) | −755.00 | −827.00 | −852.00 |
| Harvest Cold | −620.00 | −620.00 | 0 | −150.00 | −150.00 | −770.00 |
| Metro Bus | not applicable (captive depot) | not applicable | 0 (no revenue line) | −3,184.32 | −3,184.32, of which +19.68 is Ruiru's unattributed residual (a target stated as a bill total) | −3,184.32 |

  At Site level, Mto reads: revenue −80.00 = Grow −8.00 + crossing −72.00. Optimize −97.00 = cost to serve −25.00 +
  crossing −72.00. Gap −105.00.
- **Reason.** This follows from "named, never inherited" (design §2.0, `rev 16.11`): billed kWh is Grow, but the unmapped
  meters below it are Optimize (O3, `rev 16.10`, owner-approved). A heading is not a statement line, so its total cannot
  equal the line's whenever a part sits under a different heading from its whole.

## D-RECON.2 Both splits are correct; the screen shows the tie, in one set of words

- **Ruling.** Neither split is bent to match the other.
  - Moving the crossing rows under Grow would undo OD-21's O3 placement, which the owner approved ("yes, send it to the
    architect").
  - Taking them out of revenue would misstate the operator's own statement. A finance lead reconciles to that statement.
  - So the relationship is shown, not removed. Rules:
  1. **Vocabulary.** A heading figure is named by its heading, and a statement figure by its line. "Revenue explains"
     never labels a Grow figure. The heading's own name stays "Grow revenue", because the owner set it.
  2. **One figure, one value.** A headline figure shown on more than one screen reads one term of the table
     (manifest `home_categories.reconciliation.shared_figures`).
  3. **The tie line.** A screen may show a line's figure and its own heading's figure for one scope. If they differ, the
     difference is a labelled line on that screen, in the same words everywhere:
     "Revenue −$97: Grow revenue −$25, and −$72 metered but not billed, counted under Optimize". The crossing's rows are
     named in plain words: meters not yet mapped to a customer, authorised adjustments. When the crossing is zero, no line
     is added, because the two figures are equal.
  4. **Financials shows the table.** For every operator, Financials shows the table from the statement to the headings.
     A crossing cell of zero reads "none this month". At a captive depot, the revenue row reads "Not applicable".
- **The screen word.** "Metered but not billed", with a note: "energy customers used and their meters recorded, not yet
  billed; it lowers revenue on the statement and is counted under Optimize, because recovering it is a billing and
  settlement task, not selling more". The brief's "service-to-charge" is exact, but it is not an executive's word.
  **Owner view wanted** on this one phrase.
- **Rejected options.**
  - (a) One vocabulary only, statement or headings. This drops either the executive's levers (OD-21) or the finance
    lead's statement.
  - (b) A footnote in Assure only. The audit found the gap visible on the Overview itself, so a footnote there leaves
    the defect where the executive meets it.

## D-RECON.3 The cross-page figure check

- **`check_manifest.py` section 12, `reconciliation()`.** It runs after the history checks, so H9's count of the checks
  before them only grows by the design's new anchors (D-RECON.4). It builds the table from each Site's bridge and
  `derived-values.json`, then checks:
  - **RC1.** Each bridge row sits on exactly one statement line (ancestor walk over `structures`; the tie-break is its
    own heading).
  - **RC2.** For every Site with both sides evaluated, the rows on each line add to the evaluator's change in that line,
    as an effect on the outcome.
  - **RC3.** Only a side that is not decomposed leaves a residual. It sits in the vertical's one residual row, on its
    only line.
  - **RC4.** Every crossing row is declared in `reconciliation.crossing`, and every declaration crosses somewhere. Every
    crossing is revenue under Optimize; another direction needs its own label, ruled. No cost-line row sits under Grow.
  - **RC5.** Each portfolio's table adds to its gap. The gap equals the evaluator's outcome change summed over Sites, and
    the history's October gap (the trend's last point).
  - **RC6.** Every shared figure reads one term (`total`, `row:<line>`, `col:<heading>` or `cross`) and appears on two or
    more routes. The figure reading `cross` carries the crossing label.
  - **RC7.** A statement row and its line's heading shown on a common route are tied. Each tie (left = right + by) holds
    for every portfolio and Site where its terms apply.
  - **Self-test.** Planted copies must fail: an undeclared crossing, a stale declaration, a dropped tie, and a bridge row
    moved off its line's evaluator change.
  - **Result.** 91 checks: 87, plus 4 self-tests. 0 failed.
- **What `ux_interaction_check.cjs` asserts on screen.** The UI Architect adds this check. Each rendered shared figure
  carries `data-figure`, `data-scope` (operator key or Site key) and `data-v` (the effect, signed). The routes are
  `portfolio`, `portfolio/outcomes-by-site`, `globalfinancials`, `sites`, `site/<sk>` and `site/<sk>/economics`, for
  each of `lakeside`, `harvest` and `metro`.
  - **X1 (identical).** All elements with the same (`data-figure`, `data-scope`) have the same `data-v` across every route.
  - **X2 (tied).** On any route that shows `revenue_change` and `grow` for one scope with different values, a visible
    `[data-figure=metered_not_billed]` for that scope is present. Its `data-v` equals `revenue_change − grow`, and its
    text contains the manifest's `crossing_label`. The same holds for `optimize` against `cost_change`.
  - **X3 (adds up).** For every scope, grow + optimize = gap. Metro has no grow, and its residual is inside optimize.
  - **X4 (the demo cases).** Lakeside shows the tie on `portfolio` and on `globalfinancials`, and Mto on
    `site/mto/economics`. Harvest shows no crossing line, and its Financials crossing cell reads "none this month".
    Metro shows no `revenue_change` and no `grow` figure.
  - **X5 (counts, C2 instances 2 and 3).** Every `[data-count]` tile equals the number of items in the list it names
    (`data-count-of`).
  - **X6 (loss colour, C2 instance 4).** No bar marked as a loss (`.is-bad`) has its actual equal to its target.
  - **X7 (vocabulary).** No element whose `data-figure` is `grow` sits in text that begins "Revenue explains".

## D-RECON.4 Where the rule is recorded, and the bytes it moves

- **Where the rule is recorded.**
  - Manifest: `home_categories.reconciliation` (rule, crossing label and note, crossing drivers, shared figures, ties).
  - Design §2.0: the new paragraph "How the statement and the headings reconcile", with 11 checked figure anchors, plus
    one line in the Architect's-calls list. The design header moves to `rev 16.14`, and the HTML twin is re-rendered.
  - `decisions-register.md`: calls 25 to 28.
  - `derivation-register.md`: §3.4 and C14.
  - `design-appendix.md` change log.
- **Bytes.** Two constants of the frozen-base checks move:
  - **H10.** The manifest bytes before `history:` change by this one declaration block. No evaluator, model or generator
    reads the block, and it is outside `view_digest`, so it is not an October input. H10's constant is re-based in the
    same commit (R14 lifetime), and the old value is kept in the comment.
  - **H9.** The baseline rises from 4465 to 4476, for the 11 new design anchors.

  These do not change:
  - `derived-values.json`, so H8 still passes;
  - `missing-records.json`;
  - `history.json`, so H11 still passes;
  - the evaluator and the independent model.

## D-RECON.5 Ruiru expansion: headline, at-stake column, data

- **Headline.** "Not valued: an expansion is listed beside the plan". This is the reviewer's default, accepted. Against
  doing nothing (declining the buses), no capital is spent either. The $60,000 is the cost of RUI-4CHARGERS, which is
  rejected, so it is no result of RUI-ABSORB6. This agrees with `worked-portfolios.md` ("listed beside the plan, not
  valued"), and with design §2.0, reworded in `rev 16.14`.
- **Context, under the headline.** In words:
  - "Fits on the chargers in place: 2,800 of 3,200 kWh a night, no departure missed."
  - "Buying 4 chargers instead (rejected) would cost $60,000 and add no capacity: the import limit binds."
  - The energy bill rises by $3,124.80 a month for the added service. This is the factor change, shown as what it is,
    not as a result.
- **At-stake column (queue).** No money. The word "Not valued: expansion", with the opportunity in its own unit: "6 more
  buses offered; all departures met".
- **Data (for the data lane).** In `tenants[metro-bus].sites[Ruiru].decision.options[RUI-ABSORB6]`, replace
  `avoided_capex: 60000.00, avoided_capex_class: MODELLED` with
  `capex_not_needed: {amount: 60000.00, against: RUI-4CHARGERS, class: QUOTE}`. The amount is 4 quoted chargers, so it
  is a quote, not a model.
  - In `tenants[metro-bus].portfolio.allocation.listed_not_summed`, rename `RUI-ABSORB6_avoided_capex` to
    `RUI-4CHARGERS_capex_not_needed`.
  - `check_manifest.py` `stated()` (now at `:233`) compares `capex_not_needed.amount` with RUI-4CHARGERS'
    `operator_one_off`. It also checks that `against` names a REJECTED option of the same decision.
  - The evaluator does not read these keys; H8 must stay green. H10 is re-based in that diff.

## D-RECON.6 Mto inverter: the comparator in the data, and how plan totals label their terms

- **Ruling.** The inverter options keep their reference, an immediate restore at no operator cost. The figure is called
  the **cost to restore**, never "against doing nothing".
  - Here, no action never ends: no notice is filed, the warranty lapses on 27 Nov, and the inverter is never restored.
    Its loss runs to whatever horizon is chosen: −2,281.25 of extra fuel to 5 Nov 2027, plus 2,600.00 of cover lost.
  - Valuing the claim against it would show the claim as +1,913.75 (= −367.50 + 2,281.25). That would book a repair as
    a gain in the plan's headline, sized by an arbitrary horizon.
  - Kasarani is different. There, no action is waiting, and the supplier restores on its own date. So its options stay
    valued against no action, as the data has them.
  - The class rule (design §2.4, `rev 16.14`): value against no action, unless no action leaves a failed asset never
    restored. Then the reference is an immediate restore at no operator cost.
- **Rejected options.**
  - The reviewer's first default, valuing the options against MTO-INV-NOACT (`reference_option` in the evaluator). It
    inflates, for the reason above.
  - A footnote only. It leaves the plan total mixing two bases under one name.
- **Data (for the data lane).** Every `evaluation.options` entry gets `basis:`. It takes one of three values:
  - `NO_ACTION`: its reference is the decision's no-action path;
  - `RESTORE_REFERENCE`: MTO-INV-CLAIM, MTO-INV-BUYNOW, MTO-INV-LOCAL and MTO-INV-NOACT;
  - `NOT_VALUED`: RUI-ABSORB6, RUI-ABSORB10 and RUI-4CHARGERS, the comparator rows.

  The keep-it-honest rule for the check: `RESTORE_REFERENCE` only where the decision's no-action option has
  `restore: {date: none}`. The evaluator ignores the key, and `derived-values.json` must stay byte-identical (H8).
  `tools/gen_fixtures.py` must carry `basis` to the mock-up.
- **Plan totals.**
  - The headline is titled "Change within the next 12 months", not "12-month change".
  - The formula shows two groups. "Against doing nothing" holds each term with its period: "12 months", "to the restore
    on 9 Nov", or "over the 4-month contract". "Cost of restoring what failed" holds "inverter claim −$367.50, to the
    restore on 28 Nov; nothing after". The net follows.
  - Lakeside: +6,456.00 against doing nothing (stop setting +2,916.00, huller +3,540.00), −367.50 to restore, net
    +6,088.50. This is unchanged from today's total; only its parts are shown.
  - Harvest and Metro have one group each.
  - No figure in the data changes.

## D-RECON.7 Mto meter audit: its own decision on its own Finding

- **Ruling.** Option (ii): the audit becomes its own decision, on the unexplained-loss Finding. It is not an Action of
  the billing fix, and it is not ACCEPTABLE.
  - The audit observes a different factor: 120 kWh unexplained after expected losses (`unexplained_loss_kwh`, O3, not
    priced), against 140 kWh unmapped. A Finding is pinned to the most specific factor it observes (design §2.0,
    `rev 16.12`), so this deviation has its own Finding and its own heading row.
  - As an Action of MTO-BILLING, the audit would vanish if the billing fix were not chosen. It would also hide a
    deviation under another factor's decision. That is the instance-level fix W6 forbids.
  - ACCEPTABLE is the workaround the reviewer named: it offers the audit as a substitute.
  - `vertical-factor-map.md` already lists network-loss remediation (MG-L7) as its own lever, with the meter audit.
  - The cost: one more decision (Lakeside 7 to 8, the demo 14 to 15). Its options are the audit and no action. It is not valued in
    money, because losses are not priced. It still "goes ahead beside the plan" on the routine maintenance budget, so
    `worked-portfolios.md:275` stays true.
- **Manifest change (for the data lane).** All of it sits before `history:`, so H10 is re-based in that diff.
  1. `home_categories.findings`: add
     `- {id: mto-unexplained-loss, site: Mto, decision: mto-losses, origin: true, factor: unexplained_loss_kwh, heading: optimize}`.
  2. `home_categories.decisions`: add
     `- {id: mto-losses, site: Mto, finding: "Losses beyond expected: {fig:sites[lakeside-power/Mto].actual.nodes.unexplained_loss_kwh} kWh delivered but not explained after expected losses", finding_factor: unexplained_loss_kwh, lever: unexplained_loss_kwh, heading: optimize, chooser: SITE_MANAGER}`.
     Use the placeholder form if `narratives()` scans the block. Otherwise use the words without the figure; never a
     literal 120.
  3. `tenants[lakeside-power].sites[Mto].decision.options[MTO-METER-AUDIT]`: unchanged (RECOMMENDED, 60.00, crew 0). Add
     `decision: mto-losses` only if the data lane gives option rows a decision key everywhere; otherwise the grouping
     lives in the mock-up's decision list, as for every other decision.
  4. `plans`: no change. `recommended` keeps MTO-METER-AUDIT, now the one recommended option of its own decision, which
     satisfies "exactly one option per decision". `meter_audit_note` stays.
  5. `demo_workflow`: if the audit has an item or an Action, its chooser and owner is David (SITE_MANAGER).
- **Checks.** `homes()` then requires the following: one origin Finding row; Finding factor and lever under one heading
  (Optimize and Optimize); a chooser that is one of the three roles.
- **Design text, in the same data-lane diff.** §2.0 "all fourteen decisions" becomes "all fifteen". Add one example line
  under "How everything else ties back": the meter audit answers the unexplained-loss Finding, Optimize.
  `worked-portfolios.md` §1 lists the decision.

## UI change list, for the UI Architect (mock-up `interactive-mockup-vNEXT`; this commit edits no mock-up file)

**Reconciliation (D-RECON.1 to D-RECON.3).**
1. **Fixtures.** Regenerate the fixtures (`tools/gen_fixtures.py`) so `MANIFEST.home_categories.reconciliation` is
   present.
   - Add one function, `reconMatrix(scope)`, in `loop-portfolio.js`. It builds line × heading from `effectsOf` nodes, and
     a node's line comes from its ancestor (revenue or cost to serve).
   - Every shared figure below reads it. No screen computes its own split.
2. **Overview, By-outcome tiles (`loop-ux.js` `uxCatTile`).** Keep the Grow bullet "Revenue $9,688 against a target of
   $9,785". When the crossing is not zero, add a caption: "Revenue −$97: Grow revenue −$25, and −$72 metered but not
   billed, counted under Optimize". The Optimize tile gets "Optimize −$827: cost to serve −$755, and −$72 metered but not
   billed". The words come from `crossing_label` and `crossing_note`, and each figure carries `data-figure`.
3. **Overview headline and waterfall title** (`uxOverview` `hl`; `uxBridge` `title`). "revenue explains" becomes "Grow
   revenue explains". "cost and efficiency explain" stays.
4. **Financials (`financialsScreen`).** A new section after the statement: "From the statement to the headings".
   - Rows: Revenue against target, Cost to serve against target, Total. Columns: Grow revenue, Optimize cost and
     efficiency, Total.
   - The crossing cell is labelled "Metered but not billed", with its rows itemised (Mto: meters not yet mapped to a
     customer −$56, authorised adjustments −$16). A zero crossing cell reads "none this month".
   - Metro: the revenue row reads "Not applicable at a captive depot", with the residual line "not attributed yet".
   - The section appears for all three operators.
5. **Bridge tables** (the Assure card's `bridgeTable`; `gapSplit` "Show as table, by Site"). Under the Optimize
   subtotal, add a row "of which metered but not billed (in revenue on the statement)", per Site.
6. **Site economics (`site/<sk>/economics`).** On the revenue row of a Site with a crossing (Mto), add "of which −$72
   metered but not billed, counted under Optimize".
7. **Earlier views** (`loop-portfolio.js` `headline()`, `heroFigs()`). Read the same matrix, and add the tie wherever they
   print both revenue or cost and Grow or Optimize.
8. **Attributes.** Every rendered shared figure carries `data-figure`, `data-scope` and `data-v` (D-RECON.3).
9. **`tools/ux_interaction_check.cjs`.** Add X1 to X7 (D-RECON.3).
10. **C2 instances 2 to 4.**
    - Site `kobo`: "1 decision is waiting" and "2 decisions open" read one source, and each is labelled for what it
      counts.
    - `#/oprecords`: the "Records in window" tile equals its table's rows.
    - Thika "Where value leaks": a bar is coloured as a loss only when it deviates against its target.

**Ruiru expansion (D-RECON.5).**
11. **Decision dialog and card for RUI-ABSORB6.**
    - Result: "Not valued: an expansion is listed beside the plan".
    - Context lines as in D-RECON.5.
    - Remove the `avoided_capex` branch in `loop-decisions.js:147` and the `capAv` logic in `loop-ux.js:65`. Read
      `capex_not_needed` as context only, after the data lane's change.
12. **Queue at-stake (`uxStakeParts`) for `ruiru-expansion`.** The word "Not valued: expansion", plus "6 more buses
    offered; all departures met". No money.
13. **Metro plan, listed beside.** "4 chargers not needed: $60,000, the rejected alternative" (QUOTE), never "avoided"
    or "saving".

**Mto inverter and plan totals (D-RECON.6).**
14. **Inverter decision cards and dialog.** The result label is "Cost to restore, against an immediate restore at no
    cost". The no-action card reads: "Never restored: the warranty lapses on 27 Nov, $2,600 of cover lost, extra fuel
    runs on", Rejected, with figures from the data. This applies with the M1 fix: the typed "against doing nothing" is
    dropped wherever the basis names itself.
15. **Plan formula** (`loop-core.js` `spend` and value drawers; `planCase` rows). Two groups by `basis`, each term with its
    period words, then the net. Title: "Change within the next 12 months".
16. **Overview KPI.** "Options' value, 12 months" becomes "Change within the next 12 months". At Lakeside, its note
    reads "includes the cost of restoring the inverter".

**Mto meter audit (D-RECON.7).**
17. **New decision `decision/mto-losses`.**
    - Title: "Mto energy not explained after expected losses".
    - Origin Finding: unexplained loss (Optimize).
    - Options: Meter audit (Recommended; $60, routine maintenance budget; done on the inverter visit; not valued, because
      losses are not priced) and No action (the reference).
    - Chooser: David.
18. **`mto-billing`.**
    - Options: MTO-BILLING and No action only (`loop-decisions.js:232`).
    - Remove "Alongside the recommendation" and "Choose this instead" for the audit. M2 is resolved by structure.
19. **Lists.** Add the Finding to ATTN, the Optimize card's Findings and the Lakeside queue. The counts follow from the
    data. The plan row for the audit stays "beside the plan, routine maintenance budget".
