# Architect request: W2-06 fix-round questions (r9)

You are the AssetOps Architect. Read the following:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide" and "Token Efficiency".
- `.agent/W2-06-build-spec.md`: every ruling through "Review rulings (r8)".
- On branch `task/W2-06-ev-assessment` at `0c5cfb3d`, the section "fix round r7/r8" of `.agent/W2-06-pending-rulings.md`. Read it with `git show task/W2-06-ev-assessment:.agent/W2-06-pending-rulings.md`; the code is in the same commit.

The builder stopped on four open questions: M1-a, M1-b, M1-c and M3. Rule each one exactly, using concrete artifacts:
- the literal stored field or read-time derivation, with JSON key, type and example;
- persisted versus refused, with the status/reason/code table;
- the UI location, component and exact copy;
- for M3, the wire field that separates START from ABORT. Give its key, its type and its literal values, and say whether it is stored or derived.

Name the test for each ruling. State whether the six W2-05b manifests or the R12 vectors change; they must stay byte-identical unless you give the literal new values. Answer in advance any follow-on question a mid-level implementer would still ask.

Append the result to `.agent/W2-06-build-spec.md` as "Fix-round rulings (r9)", amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
