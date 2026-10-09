# S2-01c questions 5 (fix round 1) - fail-closed defaults, batchable

Raised while implementing `.agent/architect-S2-01c-answers-4.md` "First-review ruling" and `D-2026-10-09-s2-ordered-publication-and-closing-boundary`. Each default is built; none blocks.

1. **Batch composition per boundary.** To make `run_to_end` and single steps give identical Batch V2 bytes, not only identical envelopes, the Lab seals after every reached boundary's admission. A run now seals many small batches (one per boundary group) instead of one per operator step. Already-sealed bytes are untouched. *Default built:* seal per boundary. Alternative: seal per step and pin only envelope identity/bytes (batch membership would then depend on step size).

2. **A passed boundary blocks the run's ordinary publication.** If the gateway clock has passed a boundary whose undelayed reports were never admitted, the gateway refuses `PUBLICATION_INSTANT_PASSED`, the Lab notes it, and the ordered pass stops there; every later step stops at the same boundary (nothing later is admitted, so no later reading gets a sequence ahead of the gap). There is no repair control. *Default built:* expose and stop; recovery is a new run. Alternative: admit later boundaries and leave a recorded gap.

3. **A delayed report whose release boundary was missed.** If a pass failed before a due delayed report was admitted, the next pass releases it at the first boundary that pass admits (or the explicit post-run instant): the actual later instant, never backdated, per the existing delayed-release rule. Only ordinary readings refuse when their boundary is passed. *Default built:* as described. Alternative: refuse a delayed report too once its first reachable boundary is passed.

4. **IPC body change.** `admit_at_run_clock` now requires `at_instant` (exact-key bodies); a host sending the phase-2 body is refused. Nothing merged sends the old body. *Default built:* required. Alternative: optional, with the old stamp-at-current-clock behaviour when absent (which is the behaviour B1 removed).

5. **SCHEDULE_MISSING with a live session.** The read returns `SCHEDULE_MISSING` under the same condition the advance refusal uses: executed, no stored schedule, and no live session. With a live session the next world step rewrites the schedule, so the read shows `NO_SCHEDULE` until then. *Default built:* match the advance condition. Alternative: also treat a live session without a schedule as missing.
