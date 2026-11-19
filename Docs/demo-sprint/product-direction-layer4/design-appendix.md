# Design appendix: baseline reconciliation, self-check and research basis

**Companion to `layer4-transformation-design.md` (rev 16.5)** · AssetOps Architect (Claude) · 19 Nov 2026.

These sections were §11, §12 and Appendix B of the design document up to rev 15. §1 is unchanged, and §2 is re-pointed to the rev 16.5 sections.

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

| The executive must understand… | Where in the design (rev 16.5) |
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

## 5. Minimum pilot asks per vertical

Moved from design §2.3 in rev 16.2.
- **Mini-grid:** EMS export, meter register, billing export, settlement statements, fuel records, budget, and one asset's contract set.
- **Cold:** storage ledger, energy bills, chamber log, invoices and receipts, QA notes, budget, and the refrigeration contract.
- **EV:** CPMS log, roster, utility invoice, service tickets, budget, and the charger warranty or SLA.
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
