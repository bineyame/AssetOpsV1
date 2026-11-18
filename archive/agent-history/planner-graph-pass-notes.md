# Graph pass notes for checker Implementer and independent Reviewer (2026-10-11)

The Planner changed the registry, panel contract, packets and queue. No product code or delivery-report script was edited. The current report is non-authoritative until the changed paths and score behavior receive independent review.
The `recommendation:3` panel contract was also corrected from CapabilityReadiness to the frozen VerificationPlanVersion and accepted-evidence requirement, matching the existing S6-02 read path.

## Scoring fixtures to update in the checker lane

- Discover the new real packet links `S4-04`, `S5-02`, `S6-03` and renamed `S4-03-finding-evidence-history.md` from `tasks/README.md`; keep active/in-review and unknown-status refusal for every linked packet, including labeled V-01a/b and S2-02r (C9).
- Prove `A-finding-index` reaches the Site Finding list and both `mini:3` variants through S4-04/S5-02, but does not reach Finding Evidence/History or `mini:1/2/4`. S4-03 and S5-01 must be technically closable while the Site index remains open.
- Prove `A-action-index` reaches `sitework:1` through S6-03 only. Action detail/recommendation/change/plan/verification paths should remain reachable without that architecture node. `I-S6-01` must require the closed `I-S4-01` Finding task; `I-S6-02` follows S6-01, not S6-03.
- Recompute scores and top-two margin on the new graph. Open task nodes now use effort S for **incremental final integration/review/owner closeout** after independently sized subnodes; their technical AND paths and subnode efforts remain. The old 3.018/2.679 scores and 11.2% gap are stale.
- Review packet statuses for S4-04, S5-02 and S6-03 as not started, then test each as active and in review for global stop. Do not treat the current next-work result as selection authorization before the changed paths are reviewed.

## Review boundary

Changed effective paths are `finding-evidence:1-2`, `finding-history:1`, `sitefindings:1`, `mini:1-4`, the Action/Recommendation/Changes/Verification panels, `sitework:1` and Action child panels. Those panel rows are `reviewed_mapping:false` pending fresh independent review. Unchanged reviewed S1/S2 and S3/S4 money/health paths retain their citations. No node became resolved and no panel became Real.
The live report refuses on exactly 22 changed approved core panels with `[unmapped_approved_panel]`; this is the intended review gate. It reports no queue or structural mapping error.
