# V-01a registry closeout review

Reviewer: fresh Claude reviewer (independent of author). Branch closeout/V-01a-registry @ f02e83f vs d81d265.

## Verdict: ACCEPT. No block findings. Two minor carries.

## Verified
- Structured JSON diff of registry and ledger (not just the text diff): only V-01a gate, visual_acceptance/caveat on w1_panel_mapping rows 0,2,3,4,5,9,10 (sites:1, foundation:1-3, readiness:1, sld:1-2), caveat rewrites on readiness:1#a, 2#a, 3#a, and four ledger unknown_or_empty appends. No status, panel_status, core_panels or owner_inputs change; nothing marked real; readiness:2#a/2#b/3#a/3#b remain unmapped, panel_status gap; panel_status stays partial elsewhere.
- Gate: status accepted, accepted_on 2026-10-12, 8 evidence paths all exist; note states conditional, layout/copy only, not technical closure, no W1 core change, carries C1-C4. Matches owner verbatim and D-2026-10-12 addendum.
- readiness:1#a caveat matches foundation_api.py:295-298 ("Operational status (...) is not assessed here."). Caveats for 2#a/3#a match current UI (RegisteredSourcesPanel shows "Registered", caption "not assessed here"; no "awaiting credentials" remains in src/backend; a regression test asserts its absence).
- Checks: check_v69_dependency_registry.cjs pass; tools/check-all.ps1 all 6 guards passed; --verify-report .agent/next-work-2026-10-12b.json exit 0 (fingerprints current).
- Next work: report decision select V-01b 2.47 vs A-S4-financial 2.215 (gap 0.103, above 10%, top score, user_review_required true). Consistent with inputs; the <=5% story-path rule does not apply. Note the report's second-ranked candidate list shows D-financial-basis after V-01b (A-S4-financial is the second-best score per decision block; I did not recompute scores).

## Carry (non-blocking)
1. Registry caveat for 2#a cites FoundationRevisionPanel.tsx:353-370 and LedgerSiteEvidence GatewayContact; line numbers will drift. Low.
2. The "Round 3 conditional-acceptance rows" in the packet are referenced by name only; if V-01a packet is later edited, the condition pointer could rot. Low.

## Not verified
Frontend vitest/build not run (not touched; metadata-only diff). Scoring algorithm not recomputed.
