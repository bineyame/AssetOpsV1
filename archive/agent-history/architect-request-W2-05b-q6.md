# Architect request: W2-05b q6 (Q26–Q31), the manifest assertions

You are the AssetOps Architect. Read:
- the `.ai/ROLE_CONFIG.md` section "Mockup drives the design; implementers never decide";
- the whole of `.agent/W2-05b-build-spec.md` (q1–q5);
- `.agent/W2-technical-design-ev.md`, especially the six scenario cases and their expected outcomes.

The code is on `task/W2-05b-ev-producer` at head `b75dbb9c`. Read these from that branch with `git show task/W2-05b-ev-producer:<path>`:
- `.agent/W2-05b-pending-rulings.md` (Q26–Q31);
- `.agent/W2-05b-phase-handoff.md`;
- the W2-02 cold manifests and the replay test, which are the analogue to mirror.

The final part of commit 5 is blocked: the six EV manifests' `assertions` values, the Postgres replay test, the packet and the final suites.

Give an exact manifest table for all six cases. For each case, list:
- every `assertions` key with its literal value;
- how each value is derived, by exact rule;
- the per-connector values for the fault case;
- the contradictory case;
- `first_cutoff_outcome`;
- the 0-versus-null rule.

Answer Q26–Q31 explicitly. Make sure the values agree with the simulator totals already pinned in commit 2: 30, 15, 10, 30, 30 and 30 kWh. Also pre-answer anything else the Postgres replay test needs, so this is the last round.

Append the rulings to `.agent/W2-05b-build-spec.md` as "Run 6 rulings (q6), manifest table". Write nothing else. Do not commit.
