# S4-01 questions 4 (phase-2 fix round 1)

Raised by the Implementer while fixing the phase-2 review (B1, B2, C3) and applying Q17-Q20
(`D-2026-10-12-s4-finding-phase-2-read-boundaries`). Each one has a default that is already built. None of them
blocks phase 3.

## Q21 - Does the recurrence link use the same stop proof?
The default is yes. A LINKED recurrence now also requires that both stops around the separation are CONFIRMED by
the Q17 report proof: the stop after the earlier run and the stop before the new run (one record when the runs
are consecutive). Otherwise the result is `NOT_ESTABLISHED` with
`SEPARATION_STOP_NOT_CONFIRMED: <reason>`. Without this, a stop bridge that Q17 refused would come back as a
LINKED recurrence over the same contrary report. The consequence is that one non-GOOD or contrary generator
report inside either stop leaves the two Findings unlinked. Intermediate Necessary runs between the two episodes
are still allowed. Confirm, or rule that recurrence keeps only the OFF-bound checks.

## Q22 - A completed match is recorded in the unmerged migration 0009
Q18 requires "a Finding match at that exact selection" before `NO_FINDING`. Nothing recorded a matcher pass, so
the default adds an append-only `finding_match_pass` table to the unmerged `0009_finding_store`, holding the
selection sequence the pass fenced and the matcher version. The window read says `NO_FINDING` only when a
`finding-episode-2` pass covers the window's current selection sequence; until then it says
`FINDING_MATCH_PENDING`. 0009 has reached only disposable fixture/test databases: the isolated test and producer
databases are dropped and recreated on every run. Confirm that editing 0009 is acceptable, or require a 0010.

## Q23 - The operator `finding-reads` CLI is not gated
`assess_dispatch.py finding-reads`, which the producer's verify step uses, calls `FindingReadService` directly.
It does not go through the Performance cutover gate, because it is a labelled operator/fixture tool and not a
product route. The product routes are gated. Confirm that this stays outside Q19.

## Q24 - What "exact source lineage available" means for a pinned read while the gate is closed
The default serves a pinned `revision_id` while the gate is closed. It uses the Finding store's own immutable
citations (runs, assessment revisions, cited evidence). It does not read the S3 selection: currentness is
`SOURCE_CLOSED` and the S3 drill-down links are withheld, with the reason given. The body carries
`audit_only.non_current = true`. A default read is a 409 `PERFORMANCE_CUTOVER_CLOSED`. Confirm.
