# Design appendix: baseline reconciliation, self-check and research basis

**Companion to `layer4-transformation-design.md` (rev 16.12)** · AssetOps Architect (Claude) · 19 Nov 2026.

These sections were §11, §12 and Appendix B of the design document up to rev 15. §1 is unchanged, and §2 is re-pointed to the rev 16.12 sections.

## 1. Reconciling the brief's reported baseline (C2)

| Reported behaviour | Validated? | Transformation |
|---|---|---|
| Readings, dispatch classes, episodes, fuel exposure and the generator trial path operate | yes [test-confirmed, baseline §3.11] | kept as factor observers; value comes from forward replay and the valuation identity, not gross Candidate exposure |
| MOVES affects state; CHECKED is text/counts; 10 CONTRIBUTIONS are MOVES | yes [code-observed `outcome_map.py:149-180`] | MOVES rows become structure definitions (factor relations); CHECKED becomes obligation bounds |
| Portfolio Grow = estimated income; Optimize = last-day lead Finding exposure; Protect/Assure = counts | yes [implementation-report §5.2–5.3; code-observed `chain/read.py:190`] | outcomes computed through the structure read; slice 1 relabels meanwhile |
| `recorded_amount@1` has no billing source | yes [code-observed] | commercial records + `@2` |
| Alternatives/scenarios without a comparison bridge; reserve trial fixed −5 | yes [code-observed] | options on the valuation identity; the reserve trial becomes one generator |
| Verification selective, simulated/authored; mill lacks guardrails | yes [code-observed `verification_rules.py:688`, `verification_families.py:175` `"guardrails": {}`] | guardrails generated from obligation bounds; verification triple; field sources admitted |
| Cold lacks paid occupancy/finance; EV lacks roster and utility cost | yes [implementation-report §7] | occupancy ledger; roster, tariff pricing, deadline feasibility |
| No warranty/EPC/O&M/SLA/insurance evaluation | yes; warranty exists only in the v7.0 mock and as withheld fields [code-observed] | rights register + supplier-claim case; no contract lifecycle management |
| ~62 s/site-day partial, ~147 s whole build | historical [implementation-report §8.9] | scoped regeneration; re-benchmark |
| Portfolio API computes fields the UI does not render | yes [implementation-report §5.6] | exposed in slice 1 |

## 2. Self-check against the brief's final acceptance test

| The executive must understand… | Where in the design (rev 16.6) |
|---|---|
| which business outcome is underperforming | §2.1 and §2.2: outcomes read through their factors, against target |
| which researched lever is relevant | §2.4: a lever is declared on the factor it changes |
| whether AssetEcon can meaningfully improve the choice | §2.4: option dispositions; Conditional where influence is conditional |
| which alternatives win or lose and why | §2.4: decision with no action and the rule that rejected an option |
| how the value is calculated | §2.4: the valuation rule; every figure opens to its source |
| who bears the cost given contract rights | §2.4 and `worked-portfolios.md` §1.4: residual cost per remedy path |
| what is observed versus modelled | "Rules every figure follows" and §2.3: evidence classes in words on every figure |
| what intervention can be undertaken | §2.4–§2.6: the Actions the accountable role creates against a Finding or a plan item, released by the plan the executive approves |
| how it will be verified | §2.7: three verdicts |
| what pilot data and engagement is needed | §2.3 (sources) and §5 below (the pilot asks per vertical) |

**What this design does not establish:** that any prospect's figures resemble the manifest; that the forward replay is calibrated on a real site; that a tariff or contract clause applies to a given operator; that any supplier will accept a claim; or that AssetEcon's differentiation holds. Those are pilot questions (`design-questions-and-decisions.md`).

## 3. Research basis

Industry claims rest on the brief's ledger [R1]–[R12] (AMDA benchmarking; ESMAP productive use; World Bank mini-grids; Efficiency for Access / IIR cold rooms; three EV depot scheduling papers; NREL O&M; DOE FEMP; Solar Best Practices; ABB E-mobility SLAs). They support the existence and materiality of lever families. They do not support any site-specific magnitude, conversion rate or AssetEcon's differentiation, which remains a hypothesis to validate with prospects and pilots.

## 4. Change log

- **Rev 16 (19 Nov).** Regenerated at the owner's order, in the structure the owner set: today's architecture first, then what is added on top (`.agent/owner-design-regeneration-request-2026-11-19.md`). It was written from the Phase A audit (`regeneration/A-current-mechanics-and-design-audit.md`), which found 50 errors in rev 15 in five classes:
  - a Finding treated as a condition rather than the living result it is;
  - the person who decides, acts and tracks left implicit;
  - today's mechanics understated;
  - replacement framing;
  - the owner's boosters not recognised.
- **Rev 16.1 (19 Nov).** Fixes for review B (`regeneration/B-review.md`). The system evaluates and proposes, and a named person chooses and creates the Actions. Today's opportunity path was added to Part 1. The Mermaid hazards and the wrong citations were fixed.
- **Rev 16.2 (19 Nov).** Fixes for review C (`regeneration/C-rereview.md`, N1–N4 and the Lows), plus the owner's three decisions of 19 Nov:
  - the plan is a first-class construct (§2.5);
  - the spend threshold is a Site or portfolio setting;
  - a configurable tolerance applies per factor.

  The document was also trimmed to about 12 pages:
  - the three-vertical table moved to `worked-portfolios.md` §1.0;
  - the pilot asks moved to §5 below;
  - the revision history moved here;
  - restated prose was cut.
- **Rev 16.3 (19 Nov).** The owner's answers ("Q-B1 yes, agree with the architect's pushbacks") are recorded as OD-4 to OD-6. The standing owner brief (`.ai/RULES.md` §10) is applied, and every section now states how it serves the overall objective.
- **Rev 16.4 (19 Nov).** Fixes for review D (`regeneration/D-review-rev16.3.md`). "Plan" now means only the new construct, everywhere:
  - targets and budget lines replace it in the worked portfolios;
  - "verification baseline" replaces it for verification;
  - "maintenance schedule" replaces it for maintenance;
  - the on-screen "Actual against plan" is renamed.

  Other changes:
  - the spend threshold applies to the whole chosen change;
  - a released Action whose item the plan drops is covered;
  - the pushbacks the owner agreed are recorded as OD-7 and OD-8.
- **Rev 16.5 (19 Nov).** OD-7 and OD-8 confirmed explicitly ("OD-7 and OD-8 yes"). Figure 10 redrawn to the delivery order the owner approved (OD-9): canonical format and leaf factor IDs first, then sources (lane A) and factor structure (lane B) in parallel, joining at the money leaves.
  Architect's note on the order: lanes agreed; refinement applied (cost-side decisions start before the join); caution (the canonical format is version 1).
- **Rev 16.6 (19 Nov).** Fixes for review E (`regeneration/E-review-rev16.5.md`) and the design gaps G-F1 to G-F5 from the pack recreation (`regeneration/F-pack-recreation-plan.md`):
  - the decisions table renders whole;
  - a naming lint guards OD-6;
  - the Figure 10 caption follows the step order;
  - "Action" is defined, and the schema's origin constraints are credited and changed by name;
  - the documented limits moved here (§6).
- **Rev 16.7 (19 Nov).** The pack recreation plan is approved (`.agent/owner-recreate-document-packs-2026-11-19.md`). Fixes for verification review G (`regeneration/G-verify-rev16.6.md`, N1 to N9), and the design-first additions the plan and Action workflow document needs:
  - the owner's OD-10 (the system opens the period's draft plan) and OD-11 (a change above a threshold makes a new version for approval) are added to §2.5 and Decisions, with Figure 6b, the plan's states;
  - the plan's life in a period is defined: its period, carry-over, versions, the crew-visit threshold, the three spend steps counted once, item and Action ownership, and where approval requests appear;
  - the spend threshold rule is stated for proactive items too;
  - the naming lint judges each "plan" in its own sentence and is now rule A3 of `check_alignment.py`, with the review's 12 planted sentences as permanent fixtures;
  - stale file pointers are re-pointed, the limit IDs below are renamed DL1 to DL6, and the diagram classes carry a text colour for the dark theme.
- **Rev 16.8 (19 Nov).** The owner took the default on all ten pack questions ("defaults for all 10, go ahead", `.agent/owner-pack-questions-defaults-2026-11-19.md`):
  - answers 1 to 8 are OD-13 to OD-20: sign-in, who grants roles, the executive as the finance lead's backup for imports, the item owner as the person who chose, new connections as capital, the threshold precedence, no lender evidence pack, and structure approval of steps 1 and 3C with the pack;
  - answers 9 and 10 are commercial (C2, C12 to C15) and go to the register and `commercial-plan.md`, not here (P4);
  - the approved housekeeping: the backup-start Finding is pinned to nights without backup cover (§2.1); the both-thresholds rule is listed as an Architect's call; the deep-dive safeguard and pilot onboarding are tied to steps 3A, 4, 5 and 9 (§2.3, §2.9); plan items have their own states (§2.5, Figure 6c); Lakeside has a proactive item, the Kisiwa generator service, and a December crew-visit limit (`worked-portfolios.md` §1.1, §1.5);
  - the demonstration workflow names each item's chooser and owner, and `check_manifest.py` checks it against OD-5, OD-16, OD-17 and the release rule.
- **Rev 16.9 (19 Nov).** The owner's summary confirmations (`.agent/owner-summary-confirmations-2026-11-19.md`) add OD-21 to OD-24:
  - OD-21: the four outcome categories are the executive's headings over the structure. Each node has one home category, and Findings, decisions, plan items and verdicts tie back through it (§2.0, Figure 1b). Three named changes on merit: contribution sits above the money headings, unexplained litres move to Optimize, and collections stay under Grow rather than Assure;
  - OD-22: the integration order, EMS upload and API first, then the edge gateway over Modbus, proven first on the Modbus emulator and then on a BeagleBone Black (§2.3, §2.9);
  - OD-23: a calculated daily snapshot that the UI reads, with six recalculation triggers, rebuildable and checked (§2.8);
  - OD-24: the evidence words replace the old claim ladder (Rules).
- **Rev 16.10 (19 Nov).** OD-21 corrected to the brief's own terms, with the owner's approval (`.agent/owner-assure-per-brief-2026-11-19.md`): Assure carries no money and presents A1 to A5; collection of billed value moves from Grow to Optimize (O3), correcting rev 16.9; A4 stays an Assure objective met by the evidence kept, beside OD-19; each heading is checked against the brief's G1 to G3, O1 to O3 and P1 to P4. Kobo's split is unchanged (+38.00 Grow, the fuel cost as it stood at that revision (restated since by M rev 16.20, DD3b3) Optimize): collection is cash, outside contribution.
- **Rev 16.11 (19 Nov).** The mock-up's data gaps closed in the design first (coordinator's request after the mock-up packet `specs/mockup-vnext-categories-snapshot/packet.md`). Every node's home category is named, never inherited; the manifest gains the registry (`home_categories`) and `check_manifest.py` checks it is complete. Kasarani's charging energy deliverable per night and Ruiru's charger 7, connector 2 are Protect (P1, P2). Technical losses (O2) and losses beyond expected (O3) move from inherited Grow to Optimize; the others the mock-up inherited are confirmed and named. A decision sits under its lever factor's home, by a stated rule. Operations measures are Optimize (O2). Customer compensation and penalties leave the Protect measures: money a failure has cost is an Optimize cost line, and Protect shows the failure in its own unit. Each portfolio's daily snapshot records its as-of time and any pending recalculation; Harvest Cold carries the pending demonstration case. No figure changed. The same day the owner approved a vertical factor map (`vertical-factor-map.md`, #13): the brief's 28 levers mapped to registry factors, with no factor added; it joins the appendix table.
- **Rev 16.12 (19 Nov).** The final fix round after review H (`regeneration/H-whole-pack-review.md`). A decision takes the heading of its Finding's factor (owner, `.agent/owner-decision-heading-rule-2026-11-19.md`), or its lever's with no Finding; a Finding is pinned to the most specific factor it observes, never a parent total; every Finding-backed decision's Finding factor and lever share a heading, checked (register call 18 replaced). The role accountable for what a decision concerns chooses its option, and the finance and commercial lead creates every notice and claim Action (the Architect's ruling on OD-16, M3; Kobo's battery evidence is now Peter's item). One Action release machine, Figure 6d (M4). Figure 10 loses the edge from step 1 to step 3C, which had no reason, and the OD-20 sentence states what the schedule computes (M5). Each valued option names its money factors, and Ruiru's stated-total residual has a registry row (known gaps).
- **Rev 16.14 (20 Nov).** UX audit C2 and the Decision page re-review (M1, (b), plan totals), rulings D-RECON.1 to D-RECON.7 (`specs/RECON-1/rulings.md`): §2.0 "How the statement and the headings reconcile" (one table, line by heading; the crossing "metered but not billed" shown as a labelled line; `check_manifest.py` `reconciliation()`); §2.0 Ruiru's expansion not valued, the chargers as context; §2.4 the reference when no action never ends (cost to restore) and plan totals by basis. Data changes for D-RECON.5 to D-RECON.7 go to the data lane.
- **Rev 16.15 (20 Nov).** Figure 1c in §2.0: one chain from target to verdict at Kobo, answering the owner's question (owner: "yes, add the figure", `owner/owner-add-figure-merge-pack-2026-11-20.md`). §2.4: the cost-to-restore reference only in a decision valued in money (D-RECON.8).
- **Rev 16.16 (20 Nov).** The owner's answers of 20 Nov (`owner/owner-answers-eight-open-questions-2026-11-20.md`) add OD-26 to OD-28. §2.10 and Figure 11: assets, rights, incidents with their repeats, maintenance and records integrated into the structure (OD-26); §2.8 and §2.9 gain their rows; §2.6 records who creates an approved expansion's Actions as a role setting (OD-27); the crossing's screen words become "unbilled energy" (OD-28). The manifest gains `operations` for all 9 Sites, checked by `check_manifest.py` `operations()` (OP1 to OP9); derived values unchanged. Rulings D-L4OPS.1 to D-L4OPS.9 (`specs/L4-OPS/rulings.md`).

## 5. Minimum pilot asks per vertical

Moved from design §2.3 in rev 16.2.
- **Mini-grid:** EMS export, meter register, billing export, settlement statements, fuel records, budget, and one asset's contract set.
- **Cold:** storage ledger, energy bills, chamber log, invoices and receipts, QA notes, budget, and the refrigeration contract.
- **EV:** CPMS log, roster, utility invoice, service tickets, budget, and the charger warranty or SLA.

## 6. Documented limits of the illustration

Moved from `derivation-register.md` §9 in rev 16.6 (G-F3). These are kept as limits, not fixed. The section references (§3.1, §7) point to `evidence/derivation-register.md`, where the pack recreation moves that file. The IDs are local to this section: DL1 to DL6 are not the design's gaps L1 to L7.

- **H2.** Violations of different bounds add when two decisions are on their fallback at once.
- **H3.** There is no holiday calendar.
- **H4.** The horizon must be whole years.
- **H6.** A missing record falls back silently to its declared alternative.
- **H13.** Small figures (below 50) in companion documents are checked only where anchored.
- **H14.** The influence scan's sensitivity is bounded by its perturbation sizes and five worlds.
- **Typed text on screen.** The remaining typed figures on screen are the builder's allow-listed literals (§7), each with its reason. "406 kW" stays as a spike-E design-value basis.
- **L-RS.** Records restated in screen code (§7) are not checked against the record.
- **L-UB.** Typed narrative facts on screen (§7) have no record behind them and are labelled as narrative.
- **F3 (final review).** Rendered typed copies are unchecked. Numeric manifest leaves the screen renders directly are not compared with anything: `listed_not_summed`; MTO-BILLING charges; the huller's revenue and fuel; the `forward_replay` copies of the K and M parameters; `portfolio_constraints.budget_usd_nov_dec` beside `plans.*.budget`; the coverage shares; KAS-OEM-STOPGAP `nights`; site variances and bridge amounts, checked only against each other; the `excluded`, `recommended` and `switches[].cases` labels. They are correct today, and they can drift unseen.
- **F4.** The plan-facing option fields `value` and `valued_in_money` are not defined in the specification and are not compared by the checker (`NOT_COMPARED`), although the screens read them. Planting a wrong value there passes (EV1).
- **F6.** Typed narrative counts that restate evaluated figures, e.g. "the spare bus on one night" on the Kasarani page, §7 rows 170 and 175, and "6 more buses". The label L-RS ("records restated") understates them: these restate evaluated figures.
- **DL1.** The influence scan covered 2,438 of 2,613 manifest leaves. The 175 left out include `oracle`, 32 leaves of illustration expectations that nothing enforces, which are (b) illustration expectations, unenforced. They also include `checks`, 8 statements of identities, some of which no code checks; these are (c) text.
- **DL2.** H2 above: summing violations across bounds is reachable (G20).
- **DL3.** Fallback eligibility is static: a decision falls back only when none of its options can meet the bound at all. A plan with crews 1 or budget 600 is therefore infeasible, although declared fallbacks exist. This is put to the owner as Q16.
- **DL4.** The specification's authority over the independent model rests on review. The checker never reads the specification, so an edit to the specification alone passes (SP1). The specification-first order cannot be shown from the repository, because the files were committed together.
- **DL5.** A wrong untagged figure that equals no key figure, outside the scanned documents (the design's Parts 1–2, `worked-portfolios.md` and the walkthroughs), is not caught (Dr4); see also H13.
- **DL6 (presentation).** "inverter inverter 2" on Act first (the huller condition), and "spare bus free on 0 night" under a changed roster. The evaluator docstring is corrected.
