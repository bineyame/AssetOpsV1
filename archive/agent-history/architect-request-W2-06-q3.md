# Architect request: W2-06 q3 (P1–P8)

You are the AssetOps Architect. Read:
- the `.ai/ROLE_CONFIG.md` section "Mockup drives the design; implementers never decide";
- `.agent/W2-06-build-spec.md`, all rulings including q1 and q2;
- the W2-05b build spec, all q1–q6 rulings;
- on main, the merged W2-05b code: `ev_lab`, the EV replay, the gateway v4 mapping and S2 intake;
- on main, the cold analogue: how W2-02 and W2-03 establish clock attestation for cold replay records.

The code is on `task/W2-06-ev-assessment` at head `83268ef4`. Read it with `git show task/W2-06-ev-assessment:<path>`. The open points are in `.agent/W2-06-pending-rulings.md`, section "run 3"; the anchors are in `.agent/W2-06-phase-handoff.md`.

P1 blocks the build. The merged EV replay records no clock attestation, so every EV record reads as unattested, and the spec selects only clock-attested records. Find exactly how cold records become clock-attested on main, and rule the EV equivalent. Give the exact file, function and change. If it requires changing merged W2-05b code inside the W2-06 branch, say so, and list the tests and any manifest impact. Also confirm that the six W2-05b manifests stay unchanged, or give their exact new values.

Answer P2–P8 exactly, with concrete artifacts:
- P2, the binding ID check: give the rule.
- P3, use and reason for unlinked rows in the run hash: give the literal values.
- P4, policy key names: give the literal key names.
- P5, P6 and P8: ratify each one or correct it.
- P7, publish-path wiring against the guards: name the exact path and the guard allowance, mirroring cold.

Check commit 3b (the writer, worker and Finding) and commits 4–5 for any other dependency on merged-slice behaviour that the q1/q2 rulings assumed but the code lacks, and answer each one now.

Append the result to `.agent/W2-06-build-spec.md` as "Run 3 rulings (q3)". Write nothing else. Do not commit.
