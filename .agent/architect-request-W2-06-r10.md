# Architect request: W2-06 N1–N3 (r10)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide" and "Token Efficiency";
- `.agent/W2-06-build-spec.md`, with all rulings through r9;
- on branch `task/W2-06-ev-assessment` at `dcc43b64`: the N1–N3 section of `.agent/W2-06-pending-rulings.md` (`git show task/W2-06-ev-assessment:.agent/W2-06-pending-rulings.md`), plus the code.

**N1.** When a job window has no accepted records, the build currently writes nothing and the job completes. Confirm that, or give the exact stored outcome: the row, status, read result and test name.

**N2.** The S4-05 reasons appear only in the job error, because the wire has no reasons field. Confirm that, or give the exact wire key, type, values, copy and test.

**N3.** No UI view shows session-detail evidence yet, so the per-record M1-c sentence has nowhere to appear. Confirm that it is deferred, and name the later slice or backlog entry that owns it. Alternatively, give the exact UI placement in an existing W2-06 route.

Keep the W2-05b manifests and the R12 vectors byte-identical. Where an item is a deferral, state that it is not a W2-06 merge blocker.

Append the result to `.agent/W2-06-build-spec.md` as "Closing rulings (r10)", amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
