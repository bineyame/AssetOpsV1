# PRE-S3-03 questions (batched; fail-closed defaults in effect)

For the Architect/Planner. Each default is the more restrictive reading and is already what the checker enforces; changing one is a registry/checker edit plus fixture.

| ID | Question | Default applied |
| --- | --- | --- |
| Q1 | V-01 has no effort size in its packet. What is it (S/M/L, or XL to split)? | `delivery_plan.visual_gates.V-01.effort = null`; V-01 is listed with visual reach but blocked `effort` and never scored. |
| Q2 | `evidence-analysis:2` core: is the positive rule-backed claim-limit part of the owner core, or only the S2 explanation already delivered? | Treated as core and `unmapped` (proposed `R-capability`/`R-claim-lineage` only), so the panel stays unreviewed and blocks ranking. |
| Q3 | `mini:3` and `sitefindings:1`: are both the honest-empty/Unknown and the positive Finding-row portions core? | Both core (AND); Unknown never completes the positive portion. |
| Q4 | `analysis:3#b` alternatives and `asset:3#b` positive physical condition are non-core per the proposal table. Confirm. | Non-core; visible in the mapping, never W1 work. |
| Q5 | Tie-break "fewer unresolved technical gates": measured as distinct open gates (other than the candidate) on its reached technical paths. Acceptable? | As stated; then lower effort, then node ID. |
| Q6 | `outside_ranking` holds `A-finding-index` and `A-money-comparability` as mandatory shared contracts (strategy, Shared-contract priority). Any others? | Those two; listed with reach but never eligible. |
| Q7 | Any packet in `in_review` or `active` stops selection globally (active-task exclusivity). Should an `in_review` packet without `USER_REVIEW_REQUIRED` allow parallel selection? | Global stop for both. |
| Q8 | Readiness shows stale S1 text after S2-02: `readiness:1` scope note "No accepted evidence is linked" (foundation_api.py:295-298) and `readiness:2/3` "awaiting credentials" per gateway/source (FoundationRevisionPanel.tsx:318-353; foundation_api.py:270,286). Which slice owns the correction (V-01, S7-01 or a carry)? | `readiness:1#a` recorded delivered with a caveat (the configuration claim is correct); the `readiness:2#a`/`3#a` registered-configuration portions are **not** recorded delivered. |
| Q9 | The 14 `reviewed_mapping:true` S1/S2 panels were verified by this implementer against merged code. Who records the independent mapping review? | `mapping_review.by` says independent review pending; the report header stays non-authoritative. |
