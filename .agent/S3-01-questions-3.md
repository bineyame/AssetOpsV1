# S3-01 phase 3a questions (batched; each has its fail-closed default built)

1. **Q9: F3 fix changes the `dispatch-3` cohort rule without a model-version bump.** The default cohort is now `AMBIGUOUS` whenever one source reports under two or more sequence epochs inside a UTC window, whether or not their spans overlap. Before, successive epochs were treated as one stream. The reason is that central evidence cannot tell a reprovisioned gateway from a labelled fixture placed beside ordinary evidence. Explicit selection still works. The model version stays `dispatch-3` because nothing has been released or cut over (table amended: `backend/tests/dispatch_3_decision_table.md`, "Successive epochs").
   - *Default built:* the stricter rule, with no version bump.
   - *Ask:* does the Architect want `dispatch-3.1` instead?
2. **Q10: Performance cutover with documented migration exceptions.** The gate (`analytics/performance_comparison.py`) opens only on outcome `PASSED`. A file-backed claim whose cited records are not accepted centrally (`MISSING_SOURCE`) gives `EXCEPTIONS`, and that keeps the gate closed.
   - *Default built:* closed on any exception.
   - *Ask:* may documented `MISSING_SOURCE` exceptions open the gate (as S2 configuration exceptions did not)? KOBO-001's file baseline holds no dispatch claim, so its comparison is an explicit empty set.
3. **Q11: `INTENTIONAL_DELTA` rule.** A legacy claim is an intentional delta only when the selected `dispatch-3` interval is `INDETERMINATE` and the window names limitations. Any other difference is `UNPROVEN`, which gives `FAILED` and keeps the gate closed.
   - *Default built:* this rule.
   - *Ask:* confirm the rule, or name further `dispatch-3` deltas that may count.
4. **Q12: outstanding job over a matching basis.** When the selected run matches the current basis but an overlapping job is PENDING or LEASED, the read is `STALE_PROJECTION` with `RECOMPUTE_OUTSTANDING`. It is not `CURRENT`, per Q7. `PENDING` is used only when no run has been selected yet.
   - *Default built:* this mapping.
   - *Ask:* confirm the mapping.
