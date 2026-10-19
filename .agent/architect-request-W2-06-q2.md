# Architect request: W2-06 q2 (Q1–Q15). Give concrete artifacts, not prose.

You are the AssetOps Architect. Read:
- the `.ai/ROLE_CONFIG.md` sections "Mockup drives the design; implementers never decide" and "Architect full technical design";
- `.agent/W2-06-build-spec.md` (all rulings);
- the W2-05b spec "Run 6 rulings (q6), manifest table";
- the W2-05b manifests and their Postgres replay test;
- the W2-03 cold assessment writer, enqueue, worker wiring and pure vectors, which are the analogue.

The code is on `task/W2-06-ev-assessment` at head `1b2677aa`. Read it with `git show task/W2-06-ev-assessment:<path>`. The open questions are in `.agent/W2-06-pending-rulings.md`, section "run 2 (q2)", and the anchors are in `.agent/W2-06-phase-handoff.md`.

Two prose closures still left 15 questions open. This time, answer with concrete artifacts the builder copies:

1. **R12 vectors.** Write the exact pure vector fixture content for all six cases, ready to copy into the vector file you name. Include:
   - the input records: accepted evidence IDs paired to reports (Q1), times, kWh and states;
   - the expected outputs: every column value;
   - an explicit rule for each of Q2–Q9:
     - record use;
     - 30-second rule scope;
     - span intersection;
     - kWh scale and representation: manifest `"30.000"` versus an exact sum of `30`;
     - seconds rounding;
     - mapping-profile source;
     - file names.
2. **Enqueue and worker.** Answer Q10–Q15 with exact function signatures and pseudocode that mirror the cold W2-03 code path:
   - how EV assessment work is enqueued without changing the S2 ledger, which the spec forbids. If the cold path is a separate trigger or outbox, name the exact EV equivalent;
   - the work window;
   - config-change enqueue;
   - worker wiring: file, function and registration;
   - every assessment and Finding column value, as a table.
3. **Gap check.** Check commits 4 and 5 for any remaining gap of this kind, and answer it the same concrete way.

Append the result to `.agent/W2-06-build-spec.md` as "Run 2 rulings (q2): concrete vectors and writer pseudocode". Write nothing else. Do not commit.
