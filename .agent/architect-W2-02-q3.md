# Architect request - W2-02 commit (2)/(3) points (2026-10-17). Brief; edit `.agent/W2-02-build-spec.md` in place; amend `D-2026-10-17-w2-02-buildspec`. No code.

From the implementer (handoff `.agent/W2-02-phase-2-handoff.md` on branch task/W2-02-cold-producer):
1. Unspecified: what `observation_sha256` hashes. Proposal: SHA-256 of the canonical JSON of the document's `observations` rows plus `cold-observation`/1. Decide.
2. Confirm: frozen run identity carries only ids/digests (not the 13 Foundation values or the cold document contents); the host re-reads both at execution and checks them against the frozen revision id, content SHA and `scenario_sha256`.
3. Confirm or correct these physics readings (spec silent):
   a. GENERATOR_FAILURE forcing is a hidden fault: the start request moves the generator to STARTING; at the 5-min timeout it becomes FAILED with START_RESULT/FAILED.
   b. On restore, the transfer switch returns to GRID immediately and emits a transfer result.
   c. Compressor power = cooling capacity while running on a powered bus.
   d. Grid and transfer events share the outage correlation.
   e. Ambient temperature is published every 5 minutes.
Print a 3-line summary.
