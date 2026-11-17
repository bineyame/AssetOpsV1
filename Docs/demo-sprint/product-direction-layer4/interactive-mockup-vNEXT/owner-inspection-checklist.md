# Owner inspection checklist

**Not approved: awaits owner inspection.** Open `index.html`; use the **Demo operator** selector in the blue review bar.

## Owner review in 30 minutes

**1. The five mechanics (5 minutes; main document §2).**
- *Define:* every outcome — contribution, cost to serve, Protect, operations, Assure — is a declared structure of factors down to source facts.
- *Observe:* factors are observed from sources and each outcome is computed upward through its structure; a shortfall is what that computation shows.
- *Evaluate:* an option changes factors; the same structure, re-run, gives its money and Protect effect against no action.
- *Choose:* a plan under budget, crews and deadlines, with switches for the assumptions that change it.
- *Prove:* the same factors are observed after the change; three separate verdicts.

**2. One operator walk (10 minutes; Lakeside Power).** Overview (headline, four figures, the plan's first three moves) → *Outcomes by site* (each outcome to its factors, plan against actual) → *Act first* (switch the budget to $6,500 and the letter of intent to No; watch the plan change) → `#/decision/kobo-generator` (options against no action, design-value labels, Protect under each option) → *What changed* (commitments, three verdicts, rights).

**3. One cross-vertical contrast (5 minutes).** Metro: *Demand and capacity* (Ruiru: 61% of deliverable energy used — the import limit binds — so +6 buses fit and +10 do not) and `#/decision/kasarani-charger` (departures missed 2 under waiting, 0 under the stopgap, which therefore avoids $240 of penalties for $90). Harvest: `#/site/thika` (batch exposed, damage confirmed, liability — three different things).

**4. The decisions only you can take (10 minutes; `../design-questions-and-decisions.md`).**

| Decision | Open this screen |
|---|---|
| Q1 the five mechanics | main document §2 |
| Q2 Portfolio frame: (a) six parallel tabs, (b) one sequential page, (c) staged Overview + tabs in loop order (recommended) | `#/portfolio` |
| Q3 *Act first* is the plan, not ranked Findings | `#/portfolio/act-first` |
| Q5 demo operators: separate logins for client demos | review bar selector |
| Q7 Embakasi's tariff assumption (largest figure) | `#/decision/embakasi-schedule` |
| Q9 delivery order, with the calibration lane first | main document §9 |
| Q13 may early prospects see replay-derived figures if labelled and said aloud? | `#/decision/kobo-generator` |
| Q14 keep Kisiwa's battery fuel saving as a flagged assumption? | `#/decision/kisiwa-genset` |
| Item 11 below: rebuild Ruiru's preserved deep views? | `#/ev-health` |

**Everything else** still open is listed, with the Architect's recommendation, in `../design-questions-and-decisions.md` (Q4, Q6, Q8, Q10–Q12, Q14 and residual risks RR1–RR3); none needs a screen.

The numbered rows below are the full inspection log by revision.

| # | Decision for the owner | What to click | Default in the mock-up |
|---:|---|---|---|
| 1 | Is the Portfolio frame right (Q2: staged Overview + tabs in loop order, against the alternatives in main §6.2) (no role filters, no new menu items)? | `#/portfolio` and each tab, for each operator | As built |
| 2 | Overview: outcome cards show each outcome with the factors that define it (not "gap then causes"). Right reading? | Overview → the four cards | As built |
| 3 | "Factors needing attention" (off plan, at or near a limit, new factor, not observed) on Overview and site pages | Overview (Metro: Kasarani) ; `#/site/kasarani` | As built |
| 4 | Outcomes by site: factor structure per site with plan against October at every factor; waterfall as one view | `#/portfolio/outcomes-by-site` | As built |
| 5 | Demo operator selector placed in the review bar, not the product top bar | Review bar | Review bar |
| 6 | Act-first lens chips retired with the Findings ranking; the brief's D6 "filters, role emphasis" deliberately not added | `#/portfolio/act-first`; Findings root keeps its tabs | Retired / not added |
| 7 | Switches on Act first re-compute the plan (Lakeside budget and letter of intent; Harvest aggregator; Metro tariff) | Act first, each operator | Defaults: $5,000, Yes; Yes; Yes |
| 8 | Site page shows how each site type fills the shared structure (factors, levers, limits) | `#/site/kobo`, `#/site/thika`, `#/site/embakasi` | As built |
| 9 | v7.0 site Financials, Assumptions and Scenarios merged into site economics | `#/financials` (redirects to `#/site/kobo/economics`) | Merged |
| 10 | v7.0 site overviews kept as "Operating outcomes (earlier view)" | `#/site/kobo` → sub-tab | Kept |
| 11 | Ruiru's preserved deep views keep the earlier 2-connector, 80 kW example under a banner (conflict with the 12-charger, 400 kW depot) — accept, or rebuild them? | `#/ev-health` | Banner |
| 12 | Decisions without option rows in the scenario file (Kisiwa service credit, Ruiru connector) shown from the design's rights table | `#/decision/kisiwa-om`, `#/decision/ruiru-connector` | As built |
| 13 | Harvest's modelled change from the valued options: +$3,182.40 (Kirinyaga repair over 12 months + Mwea contract, whose 4 months fall inside the horizon) | Harvest Overview, Act first | Totalled (rev 5) |
| 14 | Visual direction: keep v7.0 styling here; apply v7.2 in the product build (Q4) | — | v7.0 |
| 15 | Evidence drawer content (definition, formula, source-shaped rows, clocks, coverage, provenance) | Any underlined number, e.g. Kobo litres on Outcomes by site | As built |
| 16 | Rev 5: Protect as measured factors against a target of 0 (units, period, Σ over sites; EV October and November to 6 Nov separately; liability and penalties marked as the same factor as their cost line; at-stake values listed, never summed) | `#/portfolio/outcomes-by-site` (each operator); any site page; Overview Protect card | As built |
| 17 | Rev 5: Kobo's observed fuel = needed + candidate running (330 L) + not explained by the model (120 L); 210 L only as the option's effect | `#/portfolio/outcomes-by-site`, `#/decision/kobo-generator` | As built |
| 18 | Rev 5: plan figure "from the valued options", with spend not valued in money named (Lakeside $2,230; Harvest $100; Metro $90) | Overview figure; Act first, every switch case | As built |
| 19 | Rev 5: no executive question or role on screen; decision titles and headings name the content; identifiers only as plain name (TAG) | Any decision page; audit result in `browser-audit.md` | As built |
| 20 | Rev 6: tab order Overview, Outcomes by site, Demand and capacity (renamed from Opportunity), Act first, What changed, Scope & coverage; same order and rename for the live product (Q2) | `#/portfolio` tab row; `#/portfolio/opportunity` redirects | As built |
| 21 | Rev 6: Overview first fold = headline, four figures, the plan's first three moves; value chain behind a disclosure on phones | `#/portfolio` at 1440 and 390 px | As built |
| 22 | Rev 6: "Design value" labels on replay-based figures (Kobo, Mto demand, Embakasi, Kirinyaga, plan value) | `#/decision/kobo-generator`; click the Overview plan figure | As built |
| 23 | Rev 6: operations measures (O2), cold realisation stages, plan downside, rights measures by contract and period | Outcomes by site; Thika site page; Act first; What changed | As built |
| 24 | Rev 7: every replay figure tagged "Design value: the replay has not yet been run on site data" (all routes and drawers); Kirinyaga tagged as an assumption | Act first (Lakeside), `#/decision/kobo-generator`, any drawer on those figures | As built |
| 25 | Rev 7: EV operations measure is deliverable energy used (import-limited), with the binding limit per depot; Ruiru 34% shown as nameplate charger-hours beside 61% of deliverable energy | Metro: Outcomes by site; Demand and capacity | As built |

