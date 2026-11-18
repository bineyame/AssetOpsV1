# S4-02d questions 1 (phase 1 implementer)

Conservative choices taken and built; none blocks phase 1. Architect or reviewer may overturn any of them.

1. **Heartbeat on a tick with Site failures.** Packet item 3: "Only a completed zero-work tick advances heartbeat;
   claimed/skipped, failed and timed-out ticks do not." Built: a tick that completes discovery and visits its
   bounded Sites advances `heartbeat_at`, even when a Site stage failed or timed out; that failure is recorded on
   the Site head (`last_failure_*`, `retry_due_at`). A tick that fails or times out in discovery, loses its claim,
   is skipped (claimed) or is inside back-off does not. Reason: one permanently failing Site would otherwise
   stop the environment heartbeat and mark every Site STOPPED. Phase 2's S5 seam must therefore read the Site
   head's failure/`last_completed_at` as well as the tick heartbeat. Question: confirm that a Site-stage failure
   is a Site-level, not environment-level, health signal.
2. **Later stages after an earlier failure.** Built: S4 and the drain still run after an S3 failure/timeout on the
   same Site (S4 leaves non-CURRENT windows unchanged; the drain is independent), and the Site claim is released
   with the first failure. A DB stall can therefore cost a Site up to three stage bounds in one tick.
3. **Consequence Site claim held by someone else.** The drain's own advisory claim being held (e.g. a legacy
   per-Site timer still installed) is reported as stage code `CONSEQUENCE_CLAIMED` and recorded as a Site failure
   with back-off, so it alarms instead of passing silently. Phase 2 retires the per-Site timer.
4. **Clocks.** Schedule claims, leases, retry and heartbeat are DB time; the consequence stage gets
   `clock_timestamp()` as its `now`. The S3 worker's lease and knowledge cutoff and the matcher's `now` still use
   the application clock (unchanged S3/S4 behaviour). Phase 2 owns the skew proof (I3).
5. **One-off CLIs bypass the schedule's Site claim.** `process-jobs`, `match-findings` and
   `recompute_consequences run` do not take `schedule_site_head`'s claim, so S3/S4 serialisation is guaranteed
   between scheduled stages only. Phase 2's runbook should say an operator stops the tick before a manual Leg B run
   (the matcher fence still protects Finding writes).
