# Architect request: W2-05b q3 (Q15–Q17, N9–N12)

You are the AssetOps Architect. Read the `.ai/ROLE_CONFIG.md` section "Mockup drives the design; implementers never decide", then the whole of `.agent/W2-05b-build-spec.md` (including q1, the commits 3–5 closure and q2) and the W2-05a build spec. The code is on `task/W2-05b-ev-producer` at head `5c5c809e`. Read these with `git show task/W2-05b-ev-producer:<path>`:
- `.agent/W2-05b-pending-rulings.md` (Q15–Q17, N9–N12);
- `.agent/W2-05b-phase-handoff.md`.

Commit 3 is built. Commit 4 is blocked on these items:
- **Q15.** The merged 05a connector-state enum has no `UNPLUGGED`, so the gateway holds it as `INVALID_ENUM` and every real Stage refuses at 08:00. Rule the exact fix and where it lives. If it is the 05a vocabulary in the 05b branch, give the exact enum values and labels. Also say whether any migration or contract change is needed, given that 05b adds no migration.
- **Q17.** The gateway and ledger reject the 05a energy conversion `IDENTITY_KWH`, so the EV snapshot cannot activate. Rule the exact fix: either accept `IDENTITY_KWH` in the gateway and ledger, or have the binding use `IDENTITY`. Name the files and the tests.
- **Q16.** No correlation ID is ruled for a fault without a session. Rule it, or confirm that refusing it is correct.
- **N9–N12.** Ratify each one, or correct it exactly.

Check that these do not conflict with the q2 corrections to commits 1 and 2.

Append the result to `.agent/W2-05b-build-spec.md` as "Run 3 rulings (q3)". Write nothing else. Do not commit.
