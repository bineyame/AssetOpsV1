# Implementer effort and approach view on commercial-capability iteration 6 (2026-10-27)

Read-only, at main 1a746769. Focused rules check: test_w403_scenario_rules.py + test_s6_verification_rules.py, 72 passed. Effort is relative: "card" = one post-W6 fix card (~6 commits, 10-15 files, one scoped Postgres run, one recapture, one fix round). Plan 2 review cycles per slice.

| Candidate | Size | Key finding |
|---|---|---|
| 1 Links + claim labels + Portfolio triage | M (~1.5-2 cards), no migration | New pure `estate/triage.py`; fill `estate/index.py:124` priority/confidence placeholders and `portfolio_row` `next_move`; recurrence exists for mini only (`finding_episode._recurrence`); no shared claim-label component exists; changing server order touches `PORTFOLIO_ORDER`, cursor and `estate-selection/2` token; the multi-site "producer" is a one-day pytest fixture with documented gaps (post-W6-W3-estate-packet.md:147) |
| 2 Mini productive-use working decision | M (~1.5 cards), no migration | Extend `mini_decisions/scenario_rules.py` PRODUCTIVE_LOAD keys (collection fraction, marginal cost, enablement, other cost); jsonb columns so no DDL; reserve/service gates already enforced in `calculate` and `mini_depth/rules.py:assess_renewable_hour`; lower risk than the Architect states; recommended first working decision |
| 3a Generator trial links | S | Fold into 1 |
| 3b Post-trial modelled comparison | M (~1-1.5 cards, +0.5 if persisted) | `fuel-cost-1` is a containment bound (low = 0), so before-minus-after always contains zero: it cannot show an improvement. Needs a new versioned window model (generator kWh x SFC x window price over the frozen 60-min windows); comparability bands already exist in `verification_rules.comparability`; amounts will be small (60-min windows, no annualisation) |
| 4 EV bus departure decision | L (3+ cards), migration + new decision family | No vehicle identity, SoC, capacity or departure exists anywhere; `0034` kind CHECK allows only GROSS_TARIFF_CONTEXT; displaced-vehicle modelling would invent session behaviour; keep as declared illustrative context this sprint |
| 5 Cold lot review set + value | M-L (~2-2.5 cards), migration | No lot entity; new lot revision table, pure lot-episode join rule, API, view, producer variant; cheaper if product rule = chamber threshold; intervention = truncation on observed chronology only (no thermal model) |
| 6 Comparable Portfolio placement | M (~1 card), after inputs exist | `estate/financials.compare` + `_overlaps` already partition and refuse overlapping sums; `estate_total` is always None; the no-double-counting rule is largely enforced already (add a guard test); fold into 1 + 2 |

Shared: reuse the existing declared-input revision pattern (mini scenarios, cold C4, EV E5); one migration if lots/bus are ruled in; one label component; one extended demo producer (biggest single shared cost); batched validation (pure tests while building, one scoped Postgres batch, one capture run, one full suite). Validation is serial on this machine, and that, not coding speed, is the throughput limit.

Recommended order: (0) one batched Architect ruling pass (triage order seam and label vocabulary; marginal-cost basis; window model; cold rule/threshold), (A) candidates 1 + 3a + label component + producer extension, (B) candidate 2 with 6 folded in, (C) 3b only if the window model is ruled, else "inconclusive/unavailable", (optional) 5 if its rule is simple; EV stays illustrative. Close-out: one capture run, one Postgres batch, one full suite.

Rulings needed before coding (from the implementer):
- C1: does triage change server order or only annotate/group? the closed placement groups and reason codes and their precedence; cold/EV recurrence = unknown?; closed claim-label vocabulary, server- or client-derived.
- C2: marginal cost declared or derived; decision scoped to the noon 1-h eligible window, no annualisation; collection sensitivity points; old revisions keep frozen calculations.
- C3b: new point-estimate window model under a new version; restrict to candidate-avoidable seconds?; derived or persisted and price pinning; which outcome states yield a figure; where intervention cost is declared.
- C4: bus-session binding; taper/efficiency; displaced sessions; alternative set; cost scope.
- C5: product rule = chamber threshold?; duration semantics vs episode bounds and open episodes; partial lot presence; intervention counterfactual = truncation only.
- C6: within-group display order; productive-use contribution as a new `compare()` category?
