# Walkthroughs: the owner's guided tour of the mock-up

**AssetEcon Layer 4 mock-up · recreated from the design (`rev 16.12`) and the mock-up as it is built today · AssetOps Architect (Claude) · 19 Nov 2026**

**Status.** Not approved: awaits the owner's inspection. **The visual check is not yet done:** this server has no browser, so no screenshot, layout or phone-width check was made for this text. Every step below was checked against the screen text the mock-up renders (`tools/render_text.cjs`), not against how it looks. All figures are illustrative demonstration data.

## 1. What the mock-up shows, and how to open it
<!--derives: Part 1; §2.0; §2.8; §2.9; WP §1.5-->

**What exists, and stays.** The mock-up keeps today's product frame: the left menu, the six Portfolio tabs, the site pages and their earlier views, Findings with their threads, Actions and verification. An executive who knows today's product finds everything where it was.

**What is added on top.** Every money figure is now computed upward from a Site's factors, sits under one of the four executive headings, and is compared with a target. Decisions compare their options with doing nothing. The plan shows what the portfolio commits to, and who approved it. *Serves the objective:* an operator executive sees what the month did to their money, what is worth doing about it, and who acts, which a monitoring tool does not show.

**How to open it.**
- Open `index.html` in a browser; no server is needed. Or, from this folder, run `python3 -m http.server 8790 --bind 127.0.0.1` and open the local address.
- Choose the operator in the blue review bar at the top (**Demo operator**). The review bar is review tooling, not part of the product. Its screen selector lists every screen.
- The top bar of every screen shows the period and the snapshot's date: "October 2026 · Figures as of 06:00, 6 Nov".
- Main routes: `#/plan` with its four tabs (Items, `/left-out`, `/review`, `/history`; IA-2a: the stepper, the spend, crew and value tiles, the release line and Approve or Send back on every tab) and `#/portfolio` with its three tabs (Overview, `/outcomes`, `/demand-and-capacity`; IA-1b, the empty address opens `#/portfolio`); `#/site/<site>`; `#/decision/<id>` (IA-1c: every decision of the operator, its crumbs Decisions › its Site). "Waiting for you" in the top bar opens the inbox in place: For you (the plan version awaiting approval and the decisions the executive chooses; the badge counts these), In your portfolio, and Since you last looked (the choices and approvals made in this tab). The old `#/portfolio/outcomes-by-site` opens `#/portfolio/outcomes`; `/act-first`, `/what-changed` and `/scope` are kept for the review select until their units land (IA-2b, IA-2d).

**Who appears on screen.** People are shown by role title, with the Site for a Site manager, and a fictional first name, labelled illustrative. The roles are the design's five: the operator executive, the finance and commercial lead, the Site manager, the field technician and the analyst. The system recommends; a person chooses, creates the Actions and approves.

**How to read the four headings.** *Grow revenue* and *Optimize cost and efficiency* carry the money that explains the contribution gap; cash collected sits under Optimize, outside that gap. *Protect asset and capital* shows measures in their own units, with values at stake listed and never added. *Assure performance and returns* shows the evidence behind every heading and adds no money of its own.

## 2. Lakeside Power: Kobo first (mini-grid)
<!--derives: §2.0; §2.1; §2.2; §2.4; §2.5; §2.6; Figure 1b; WP §1.1; WP §1.5-->

**Step 1. The month in one line.** Route `#/portfolio`, operator Lakeside Power.
- *Sees:* October contribution of $1,443.00<!--fig:portfolio.lakeside-power.actual.sums.contribution--> against a target of $2,295.00<!--fig:portfolio.lakeside-power.plan.sums.contribution-->, $852<!--figx:{portfolio.lakeside-power.plan.sums.contribution}-{portfolio.lakeside-power.actual.sums.contribution}--> short, composed from the three Sites' factors, and the first three moves of the period's proposed plan.
- *Why it matters:* it answers the money question for the whole portfolio at once, before anyone opens a Site.
- *Who:* Amina, the operator executive, reads it.

**Step 2. Where the money went: Grow and Optimize.** Same screen, the first two heading cards.
- *Sees:* under Grow, Kobo's customer consumption above target, +38.00<!--figx:({sites.lakeside-power/Kobo.actual.nodes.billed_kwh}-{sites.lakeside-power/Kobo.plan.nodes.billed_kwh})*{sites.lakeside-power/Kobo.actual.nodes.tariff}-->. Under Optimize, three Kobo fuel lines, the largest −412.50<!--figx:-({sites.lakeside-power/Kobo.actual.nodes.candidate_l}-{sites.lakeside-power/Kobo.plan.nodes.candidate_l})*{sites.lakeside-power/Kobo.actual.nodes.diesel_price}--> for generator running while solar could carry the load; together they are the −600.00<!--figx:-({sites.lakeside-power/Kobo.actual.nodes.candidate_l}-{sites.lakeside-power/Kobo.plan.nodes.candidate_l})*{sites.lakeside-power/Kobo.actual.nodes.diesel_price}-({sites.lakeside-power/Kobo.actual.nodes.unexplained_l}-{sites.lakeside-power/Kobo.plan.nodes.unexplained_l})*{sites.lakeside-power/Kobo.actual.nodes.diesel_price}-({sites.lakeside-power/Kobo.actual.nodes.necessary_l}-{sites.lakeside-power/Kobo.plan.nodes.necessary_l})*{sites.lakeside-power/Kobo.actual.nodes.diesel_price}--> that Kobo's row of the bridge shows under Assure. Below it, "Cash collected, outside the contribution gap": Kobo collected 3,180.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.collected--> of 3,458.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.revenue--> billed, with 278.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.outstanding--> outstanding.
- *Why it matters:* the two money headings add to Kobo's gap of −562.00<!--figx:{sites.lakeside-power/Kobo.actual.nodes.contribution}-{sites.lakeside-power/Kobo.plan.nodes.contribution}-->, so every dollar is explained once. Cash is shown apart, because collecting a bill does not change what the month earned.
- *Who:* Peter, Site manager at Kobo, owns the litres; Joseph, the finance and commercial lead, owns collection.

**Step 3. What is at risk, and how sure we are: Protect and Assure.** Same screen, the last two cards.
- *Sees:* Protect lists measures in their own units, such as 30<!--fig:portfolio.lakeside-power.actual.sums.obligation_hours_without_redundancy--> obligation hours without redundancy in October (by Site under "Service and assets" on each `#/site/<site>` page: 10<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.obligation_hours_without_redundancy--> evening hours at Kisiwa, 20<!--fig:sites.lakeside-power/Mto.actual.nodes.obligation_hours_without_redundancy--> daytime hours at Mto), and lists the warranty values at stake beside them, never added. Assure opens "Contribution's bridge by heading", shows how much of the cost rests on records, the decisions compared with doing nothing, the Actions and their three verdicts (none reached yet), and the contract deadlines, such as Mto's inverter warranty notice due 27 Nov.
- *Why it matters:* Protect is the limit a decision must respect, not a saving. Assure is why an executive can trust the money figures above it.
- *Who:* Amina tracks; Joseph files the notice.

**Step 4. Kobo's factors, read upward.** Route `#/site/kobo`.
- *Sees:* contribution $883.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.contribution--> against $1,445.00<!--fig:sites.lakeside-power/Kobo.plan.nodes.contribution-->, then the breakdown, each row with its target, October value, effect on contribution, evidence and heading. Litres used are 1,180<!--fig:sites.lakeside-power/Kobo.actual.nodes.diesel_l--> against 700<!--fig:sites.lakeside-power/Kobo.plan.nodes.diesel_l-->. Any underlined figure opens a drawer with its definition, formula, source records and coverage.
- *Why it matters:* the driver behind the gap is a quantity at its factor, not a flag, and today's Findings sit on the factor they observe.
- *Who:* Peter reads it; the analyst, Wanjiru, maps the sources behind it.

**Step 5. The choice, valued against doing nothing.** Route `#/decision/kobo-generator`.
- *Sees:* both settings, lowering the generator stop setting from 90 to 70 per cent battery charge and lowering the reserve, pass the operating checks on the simulated days (chip "Simulated"). Their litres and value read "Not available yet: needs a simulation of Kobo's own October", so neither is recommended or valued. The dawn margin is shown beside each as information, not a limit. Kobo's 330 L of candidate running reads as October's records classify it, to be re-checked against Kobo's own 5-minute readings. The "Who decides" panel shows no option recommended and nothing chosen yet; the stop setting's one-off cost is 90.00<!--fig:options.KOB-STOPSOC.operator_one_off-->, within the 250.00<!--rec:demo_workflow.tenants[lakeside-power].spend_threshold--> spend threshold, with no crew visit.
- *Why it matters:* this is economic judgement a monitoring tool cannot give: the fuel saving net of its cost, under Optimize, with the service limit kept.
- *Who:* Peter chooses and creates the Actions; Musa, the field technician, supervises the 14-day trial.

**Step 6. The executive approves the plan.** Routes `#/portfolio/act-first`, then `#/plan`.
- *Sees:* first the issues needing a decision, each with who decides. Then the plan, proposed by the system for November and December: version 1, awaiting Amina's approval; $3,660.00<!--fig:plans.lakeside-power.default.spend--> of the $5,000.00<!--rec:plans.lakeside-power.budget--> budget; a modelled +$2,213.33<!--fig:plans.lakeside-power.default.value--> from the valued options only (the rice huller, Simulated). Each item names its owner, its state and an "Effect under each heading": the Kisiwa repair under Protect, the Mto huller under Grow and Optimize. The huller is a capital item, so its Action is created only after approval.
- *Why it matters:* the plan trades Sites against one budget and one crew, which no single Site can do, and nothing spends above the threshold until the executive approves.
- *Who:* Amina approves or sends back the version; each item's owner (Halima, David, Peter) creates its operational Actions, and Joseph creates the notice and claim Actions.
- *Try:* under "What if", switch the budget to $6,500.00<!--rec:plans.lakeside-power.switches.budget[1]--> and the letter of intent to "No"; the plan shows its new spend and value, and the four-case table shows each result. The line "Showing the case you chose" then stays on every tab, and Left out lists the Actions that return to their creator. Approve: the dialog, the toast with Undo, the stepper on Approved, the badge down by one and a new first row under History.

**Step 7. Who is doing what.** Route `#/portfolio/what-changed`.
- *Sees:* every Action with its creator, owner, due date and whether it is released or waiting; the plan's review; and the three verdicts on each chosen change, all "not yet".
- *Why it matters:* the executive sees accountability by name, and later sees whether the money followed.
- *Who:* the Action owners act; Amina tracks.

## 3. Harvest Cold Network: Thika (cold rooms)
<!--derives: §2.0; §2.4; §2.6; WP §1.2; WP §1.5-->

**Step 1. Three rooms that look alike.** Route `#/portfolio`, operator Harvest Cold Network.
- *Sees:* contribution $946.00<!--fig:portfolio.harvest-cold.actual.sums.contribution--> against $1,716.00<!--fig:portfolio.harvest-cold.plan.sums.contribution-->. Under Grow, Mwea's empty space; under Optimize, Kirinyaga's electricity above what its occupancy explains and Thika's customer compensation of 108.00<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.liability-->. Under Protect, one batch exposed above its limit and 26<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.nights_without_backup_cover--> nights without backup cover at Thika, with the stock value at stake listed, not added.
- *Why it matters:* similar rooms need different moves: a customer at Mwea, a repair at Kirinyaga, cover at Thika.
- *Who:* Esther, the operator executive, reads it.

**Step 2. Protecting stock until the repair.** Route `#/decision/thika-backup`.
- *Sees:* night cover until the contractor replaces the backup generator's controller on 8 Nov, for 100.00<!--fig:options.THIKA-EPC-STOPGAP.operator_one_off-->, brings nights without backup cover to zero. Waiting with no cover is rejected. Fitting a controller ourselves is rejected because it voids 710.00<!--fig:options.THIKA-SELF.rights.cover_lost--> of cover held under the installation contract.
- *Why it matters:* the decision sits under Protect because it restores backup cover; no saving is claimed for it.
- *Who:* Brian, Site manager at Thika, chose it and created the Action, released when created because it is within the threshold and needs no visit by a technician.

**Step 3. The portfolio's plan.** Route `#/plan`.
- *Sees:* $720.00<!--fig:plans.harvest-cold.default.spend--> of the budget and a modelled +$3,182.40<!--fig:plans.harvest-cold.default.value--> from the valued options. Switch "aggregator signs" to "No" and the Mwea contract drops out.
- *Who:* Esther approves the version.

## 4. Metro Bus Depots: Kasarani (EV depots)
<!--derives: §2.0; §2.1; §2.4; §2.6; WP §1.3; WP §1.5-->

**Step 1. A cost centre judged on service.** Route `#/portfolio`, operator Metro Bus Depots.
- *Sees:* charging and depot cost of $41,705.12<!--fig:portfolio.metro-bus.actual.sums.cost_to_serve--> against $38,520.80<!--fig:portfolio.metro-bus.plan.sums.outcome_total_with_stated_totals-->; revenue is "not applicable". Under Protect, required departures missed: none in October, 7<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed--> since charger 2 failed at Kasarani on 1 Nov, shown separately from October; those cost 840.00<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.penalties--> in penalties, which the Optimize card counts as cost.
- *Why it matters:* the structure shows the risk at the factor, before any invoice arrives.
- *Who:* Daniel, the operator executive, reads it.

**Step 2. Keeping every departure.** Route `#/decision/kasarani-charger`.
- *Sees:* waiting for the manufacturer's repair would likely miss 5<!--fig:options.KAS-OEM-WAIT.protect.departures_missed--> more departures in the 3 nights to 9 Nov, 600.00<!--fig:-options.KAS-OEM-WAIT.monthly_or_horizon_change--> more in penalties, and is rejected because it breaks the departures limit. Charging the short buses at Ruiru on the nights the spare bus cannot cover is worth +$375.00<!--fig:options.KAS-OEM-STOPGAP.value--> to the restore on 9 Nov, against the reference of waiting. Repairing locally is rejected because it voids 380.00<!--fig:options.KAS-LOCAL.rights.cover_lost--> of cover.
- *Why it matters:* the decision sits under Protect because it restores departures; the penalties it avoids are money, a cost under Optimize.
- *Who:* Mercy, Site manager at Kasarani, chose it and created the Action, released when created.

**Step 3. Growth on the chargers already in place.** Routes `#/portfolio/demand-and-capacity`, then `#/plan`.
- *Sees:* Ruiru can take 6 more buses on its chargers, shown as potential beside Grow, never counted as revenue. The plan holds a spend of $1,725.00<!--fig:plans.metro-bus.default.spend--> for a modelled +$95,859.00<!--fig:plans.metro-bus.default.value-->, almost all from Embakasi's charging schedule; its per-bus departure timing reads "Not available yet: needs a simulation of the charging schedule".
- *Who:* Daniel approves; Ibrahim, Site manager at Embakasi, owns the schedule.

## 5. The owner's checklist
<!--derives: Decisions; §2.0; §2.8; WP §1.0; WP §1.5-->

**Check on screen** (about 30 minutes):

| Screen | What to check |
|---|---|
| `#/portfolio`, each operator | The four cards read as the executive's headings; Grow and Optimize explain the gap; cash stands apart; Protect shows no money of its own |
| `#/site/kobo`, `#/site/thika`, `#/site/kasarani` | Each factor row names one heading, and the same structure serves all three Site types |
| `#/decision/kobo-generator`, `#/decision/thika-backup`, `#/decision/kasarani-charger` | Options against doing nothing; who recommends, who chooses, who creates the Actions; each option's "Effect under each heading" |
| `#/plan`, each operator | Version, owner, item states; the thresholds open from "Release thresholds"; each switch re-evaluates the plan |
| `#/plan/left-out`, `#/plan/review`, `#/plan/history`, each operator | The same header as Items; what is left out and why; the plan's review ("Not yet" while the period is open); versions and approvals, newest first |
| `#/decisions`, `#/findings`, `#/actions`, `#/sites`, each operator (§6) | One list per object from the menu; the tiles equal the rows; Sort is the only control at this size; each row opens one thing; the Outcomes tab shows the same Site rows |

**Decisions for the owner** (with their defaults, in `../decisions-register.md`):

| Where to look | Question, and the default that applies now |
|---|---|
| `#/portfolio`, the decision links on each card | OD-25 (owner, 19 Nov): a decision sits under the heading of its Finding's factor, or its lever's with no Finding; register call 18 now says how a Finding is pinned. In the data all fourteen agree with the screens' headings |
| `#/portfolio`, the Protect card | Register call 17: Protect shows no money; compensation and penalties are Optimize costs. Default: applied in the data |
| `#/decision/kobo-generator` | Register item D6: simulated figures are shown to clients with their Simulated chip, gaps as "Not available yet", and said aloud. Default: shown, labelled |
| `#/decision/kisiwa-genset` | Register item Q14: keep Kisiwa's battery fuel saving as a flagged assumption. Default: kept, flagged |
| `#/decision/mto-inverter` | Register item Q15: when losing a unit breaches redundancy. Default: it follows the capacity computed from records |

## 6. The four home lists (IA-2b1)
<!--derives: spec-IA-2b §1, §4, §5; D-IA.63, D-IA.67, D-IA.70, D-IA.76-->

**What exists, and what changes.** Decisions, Findings, Actions and Sites were separate screens, each drawn its own way. They are now one list shape, opened from the left menu: count tiles on top, then the rows, at most ten, then "Show all". The address holds the view, so Back and a shared link bring back the same sort and filters. *Serves the executive: every object is found the same way.*

**At the demo's size the lists stay quiet.** Controls grow with the list: none under 3 rows, Sort only up to 10, filters and search above 10. Every operator has 3 Sites and at most 9 rows per list, so each list shows Sort only, and Metro's Actions (2 rows) show none. The filters still exist: an old link such as Cost Findings lands on Findings with a chip "Optimize cost and efficiency · All headings", and the chip is the way out. The full toolbar, group heads and "Show all" appear only on a 30-Site test fixture (shown in the review's screenshots).

| List | Lakeside | Harvest | Metro | A row opens |
|---|---|---|---|---|
| Decisions | 8, 3 waiting for a choice | 3, none waiting | 4, 2 waiting | the decision |
| Findings | 9 | 4 | 7 | its decision (two Kobo Findings open the generator decision; at Metro three open the Embakasi schedule and two the Ruiru expansion) |
| Actions | 6: 2 released, 4 waiting | 3: 1 released, 2 waiting | 2: 1 released, 1 waiting | the decision whose option it carries out, or the plan |
| Sites | 3, gap to target −$852 | 3, gap −$770 | 3, gap −$3,184 | the Site |

**Several rows, one target.** A Finding or an Action has no page of its own yet, so its row opens its decision (or the plan). Several rows can therefore lead to the same page; the page is the right one, and each object gets its own page later (IA-2d).

**Where the Outcomes explanations went.** The Portfolio's Outcomes tab now shows the Sites list's rows, without its controls. A row is one link to its Site, so the in-cell "show how this is worked out" buttons left the table: each figure's explanation is one click away on the Site's page, beside the same figure.

**Three things the lists do not do, on purpose.** Decisions, Findings and Actions have no "at stake" total and no stake sort: stakes are valued on different bases and horizons, and some are alternatives, so neither a sum nor an order would be a true figure. The Sites gap tile stays, because Site gaps are one measure in one month and add up to the Overview's own gap (−$852, −$770, −$3,184). Hub queues keep their "Decide" buttons until the next part (IA-2b2), after your walkthrough of the plan.

**Check on screen:** `#/decisions` (Sort to "Due date", then Back), `#/findings-cost` (lands on Findings with the heading chip), a decision's "Decisions" crumb and a Site's "Sites" crumb (both now links), `#/portfolio/outcomes` (the Site rows, no buttons).

