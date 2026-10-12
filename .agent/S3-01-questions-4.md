# S3-01 dispatch-3.1 questions (batched; each has its fail-closed default built)

Context: `D-2026-10-11-s3-phase-3a-version-and-cutover`, `.agent/architect-S3-answers-3.md`. None of these blocks phase 3b.

1. **Q14: only one documented `INTENTIONAL_DELTA` rule.** `performance_comparison.DOCUMENTED_DELTAS` holds a single entry. `CAPABILITY_CHANNELS_REQUIRED` (table rows 5a/5b) covers a legacy `CANDIDATE_AVOIDABLE` that becomes `INDETERMINATE` when the selected interval's own segments name a missing `PV available power` or `PCS discharge capability`. Other `dispatch-2` to `dispatch-3.1` differences are not registered:
   - row 1, operator override unavailable;
   - row 2, minimum runtime without a policy Necessary;
   - the multi-epoch default `AMBIGUOUS` (no interval is produced, so there is nothing to match);
   - open bounds.

   A claim affected by any of these is `UNPROVEN` and keeps the gate closed.
   - *Default built:* the single entry; no catch-all.
   - *Ask:* should any of these become a claim-specific entry? If so, name the claim change and the interval-level limitation text that proves it.
2. **Q15: `MATCH` also requires a comparable basis.** The ruling (Q11) requires a delta to match the claim to one selected interval with comparable accepted public records. The same check now applies to `MATCH`: every record the legacy claim cites must be accepted and in the selected interval's `evidence_ids`. Otherwise the claim is `UNPROVEN` ("claim levels agree, but ..."). Before this change, phase 3a accepted equal claim levels over an overlapping span.
   - *Default built:* the stricter `MATCH`. KOBO-001's legacy set is empty, so this has no live effect.
   - *Ask:* confirm, or allow a `MATCH` on level and span alone.
3. **Q16: freshness range for comparison jobs.** A selected interval is `STALE_PROJECTION` in the comparison when a PENDING, LEASED or FAILED `recompute_job` overlaps its window's read range, which is the window widened by the 6-hour `BRACKET`. This is the same overlap rule the window read uses (`window_snapshot`), so a neighbour window's outstanding job also makes the interval stale.
   - *Default built:* the read's rule.
   - *Ask:* none, unless the Architect wants the window bounds only.
