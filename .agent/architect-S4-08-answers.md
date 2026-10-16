# Architect answers - S4-08 (2026-10-16)

Decision: `D-2026-10-16-s408`. Authority: `tasks/S4-08-assumption-consequence-history.md`, `D-2026-10-14-s402-post-review-follow-ons`, `.agent/architect-S4-02-batch-answers.md`, `D-2026-10-15-s405-stored-demo-provenance`, `D-2026-10-16-s405b-label`, and `D-2026-10-16-w1-ux`.

## Q1 - Unpriced versions

**Accept.** Include every stored, in-scope consequence revision at the selected recorded cutoff, including `UNPRICED` versions with no assumption link. Return a typed missing-price state and null amount. Keep the exact Finding and consequence lineage available for audit; never attach a later or current Site price, infer zero, or omit the version from paging.

## Q2 - Current at cutoff

**Accept.** `CURRENT_AT_CUTOFF` applies only to the latest consequence revision recorded by the cutoff *within the latest FindingRevision of that Finding recorded by the same cutoff*. If that FindingRevision has no consequence by the cutoff, no consequence row for that Finding is current at cutoff. Every earlier FindingRevision's consequences are `HISTORICAL_AT_CUTOFF`, even when one heads its own consequence chain. Determine this from the same scoped, cutoff-fenced read; later revisions cannot change an earlier cutoff's classification.

## Q3 - Money at a past cutoff

**Accept with an explicit display rule.** A selected past cutoff is an audit view. Even its `CURRENT_AT_CUTOFF` row may show an eligible recorded priced amount only as **historical, assumption-conditioned audit history**, never as a current amount or today's exposure. An amount appears only when that exact version's existing source and money gates permit historical display; a closed source hides it, and missing or withheld amounts stay null. Apply the S4-05b exact-version source label and limitation beside any displayed amount. Only the separate today's exact-head read may make a current-money claim after all existing currentness, LR-01, source, quantity and price gates pass. Keep the selected cutoff visible and preserve it through links and paging.

These rulings do not promote `assumptions:3#a` or record owner acceptance. The S4-08 read and UI still need implementation and independent review; visible wording remains subject to the combined W1 walkthrough.
