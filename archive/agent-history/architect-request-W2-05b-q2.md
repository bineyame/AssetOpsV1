# Architect request: W2-05b notes N1–N8 (q2)

You are the AssetOps Architect. Read the `.ai/ROLE_CONFIG.md` section "Mockup drives the design; implementers never decide", the whole of `.agent/W2-05b-build-spec.md` (including q1 and the commits 3–5 closure), `.agent/W2-05b-pending-rulings.md` (notes N1–N8), and `.agent/W2-05b-phase-handoff.md`. The code is on `task/W2-05b-ev-producer`; read it with `git show task/W2-05b-ev-producer:<path>`. The v69 mock is authoritative for the Lab layout.

Commits 1 and 2 are built. Rule every note N1–N8 exactly.
- **N3.** The EV Lab link currently sits inside the cold-chain panel. Placing it there was an implementer decision, so it is a defect. Rule its exact placement against the v69 Lab mock, with the panel heading and description copy.
- **N1.** Rule how the owner walkthrough will list EV runs, given that the 403 copies cold replay: keep it as is, with a reason, or give the exact change.
- **N8.** Fix the private digest shape before commit 5 pins manifests. Cover the closing boundary, the partial last quantum, the `p/q` kWh text and `forcing_ordinal`.
- **Every other note.** Ratify it, or correct it with the exact change.

Say which existing commit, 1 or 2, needs a correction; that fix will be folded into the next builder run.

Append the result to `.agent/W2-05b-build-spec.md` as "Run 2 rulings (q2)". Write nothing else. Do not commit.
