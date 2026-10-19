# Architect request: W2-05b build questions (q1) and full pre-build closure

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide", the Architect readiness gate, and "Token Efficiency";
- `tasks/W2-05b-ev-producer.md`;
- `.agent/W2-05b-build-spec.md`;
- `.agent/W2-technical-design-ev.md`;
- `.agent/W2-05a-build-spec.md`: the Run 8 rulings and the r2 confirmations;
- the W2-02 cold producer code it reuses: the cold scenario catalog, the cold simulator pack, `cold_lab`, and the cold Lab setup frame.

The v69 mock (`frontend/mockups/v69/`) is authoritative for every Lab label.

The builder stopped before writing any code. It raised 14 unruled questions in `.agent/W2-05b-pending-rulings.md`; the anchors are in `.agent/W2-05b-phase-handoff.md`.

1. **Answer Q1–Q14 exactly.** Give:
   - the JSON shapes, key names and value types;
   - the ordering keys, as a full total order;
   - the times and the hash input row form;
   - the ID patterns and the version values;
   - the UI component choice, with every visible label and error string;
   - the HTTP status and error code triggers;
   - the list-row fields and the profile display values;
   - the simulator state-transition table for every (state, forcing) pair, including the unreached states in Q13 and Q14, naming the closed refusal or no-op for each.
2. **Then do a full implementer dry-read of spec commits 3, 4 and 5:** the public transform and v4 mapping, the gateway Stage, the persisted EV artifact, the delayed schedule, restart and Commit, and commit 5. Answer in advance every question a mid-level implementer would ask, so the remaining build runs need no further question rounds.
3. **Also do a copy dry-read:** every user-visible string and its source field.

Append everything to `.agent/W2-05b-build-spec.md` as "Run 1 rulings (q1) and commits 3–5 closure (D-2026-10-18-w2-05-buildspec)". Write nothing else. Do not commit.
