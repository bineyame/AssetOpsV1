# Design appendix: baseline reconciliation, self-check and research basis

**Companion to `layer4-transformation-design.md` (rev 16)** · AssetOps Architect (Claude) · 19 Nov 2026.

These sections were §11, §12 and Appendix B of the design document up to rev 15. §1 is unchanged, and §2 is re-pointed to the rev 16 sections.

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

| The executive must understand… | Where in the design (rev 16) |
|---|---|
| which business outcome is underperforming | §2.1 and §2.2: outcomes read through their factors, against plan |
| which researched lever is relevant | §2.4: a lever is declared on the factor it changes |
| whether AssetEcon can meaningfully improve the choice | §2.4: option dispositions; Conditional where influence is conditional |
| which alternatives win or lose and why | §2.4: decision with no action and the rule that rejected an option |
| how the value is calculated | §2.4: the valuation rule; every figure opens to its source |
| who bears the cost given contract rights | §2.4 and `worked-portfolios.md` §1.4: residual cost per remedy path |
| what is observed versus modelled | §0 rules and §2.3: evidence classes in words on every figure |
| what intervention can be undertaken | §2.4 and §2.5: the proposed plan, approved by a named person |
| how it will be verified | §2.6: three verdicts |
| what pilot data and engagement is needed | §2.3: the pilot asks per vertical |

**What this design does not establish:** that any prospect's figures resemble the manifest; that the forward replay is calibrated on a real site; that a tariff or contract clause applies to a given operator; that any supplier will accept a claim; or that AssetEcon's differentiation holds. Those are pilot questions (`design-questions-and-decisions.md`).

## 3. Research basis

Industry claims rest on the brief's ledger [R1]–[R12] (AMDA benchmarking; ESMAP productive use; World Bank mini-grids; Efficiency for Access / IIR cold rooms; three EV depot scheduling papers; NREL O&M; DOE FEMP; Solar Best Practices; ABB E-mobility SLAs). They support the existence and materiality of lever families. They do not support any site-specific magnitude, conversion rate or AssetEcon's differentiation, which remains a hypothesis to validate with prospects and pilots.
