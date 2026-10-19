# Architect request: W2-05b q4 (Q18–Q25) and the final closure of commits 4–5

You are the AssetOps Architect. Read:
- the `.ai/ROLE_CONFIG.md` sections "Mockup drives the design; implementers never decide" and the implementer dry-read;
- the whole of `.agent/W2-05b-build-spec.md`, including q1, the commits 3–5 closure, q2 and q3.

The code is on `task/W2-05b-ev-producer` at head `888bc259`. Read these files from that branch with `git show task/W2-05b-ev-producer:<path>`:
- `.agent/W2-05b-pending-rulings.md`, which holds Q18–Q25;
- `.agent/W2-05b-phase-handoff.md`.

The builder stopped before commit 4 with eight unruled questions, even though the commits 3–5 closure ran earlier. That closure was not concrete enough. This time, read the actual cold W2-02 code that commit 4 mirrors: the persisted cold artifact (schema version and keys), the cold delayed schedule and restart path, the Foundation-to-parameters mapping, the binding-row source, the notes/history text and the delay-ID prefix. Specify the EV version by exact analogy, naming each key, file and function.

1. Answer Q18–Q25 exactly. Q19 asks how an already-installed EV-LAB-001 gets the corrected state map. State whether this needs a re-publish path, a fixture reinstall, or nothing, and give the exact operator and test steps.
2. Do a line-level implementer dry-read of commit 5 against the actual code and its cold counterpart. Commit 5 owes:
   - the EV replay router access (N1);
   - the manifests;
   - the full suites.

   Pre-answer every remaining question, so that commits 4 and 5 need no further rounds.

Append the result to `.agent/W2-05b-build-spec.md` as "Run 4 rulings (q4) and final commits 4–5 closure". Write nothing else. Do not commit.
