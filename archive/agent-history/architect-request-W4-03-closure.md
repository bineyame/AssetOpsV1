# Architect request: W4-03 spec-review closure

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W4-03-build-spec.md` and `tasks/W4-03-mini-decisions-work.md`;
- `.agent/W4-03-spec-review.md`, which has 36 questions: 11 Blocker, 19 Should, 6 Nit;
- `.agent/W4-03-mock-measurements.md`;
- `.agent/W4-01-build-spec.md` (all rulings; the case contract is frozen), `.agent/W4-02-build-spec.md` (closures 1–3), and `.agent/W3-01-build-spec.md` (all rulings and amendments; the Finding-row contract is frozen);
- `.agent/post-W2-sequence.md`.

Close all 36 with exact artifacts, verified against merged code and the frozen contracts. The architecture-level items:
- Q1–Q3, the write path. Specify an executable actor, grant and authorization path in development and in the fixture, using the existing W4-01 mechanisms, or rule the exact new grant with its owner. Give the literal POST bodies and the idempotency and actor columns.
- Q4–Q6, the opportunity producer and links. Give the producer and enqueue, the study windows, and the opportunity-to-scenario link table. Adding opportunities to the estate lens must either be recorded as a versioned W3-01 amendment, or deferred with honest-gap copy.
- Q7, Q9, Q11. Align with W4-02: keep claim and currentness as separate fields, and use the authored AUTHORED_DEMONSTRATION source. Map the Alternatives tab on the canonical Site Finding exactly.

Never trim a mock slot. Include a supersession index for any replaced text.

Append the result as "Review closure (2026-10-20)" to `.agent/W4-03-build-spec.md`, amending `D-2026-10-20-w4-03-buildspec`, plus any versioned amendment to the W3-01 or W4-01 specs. Update the packet if scope changes. Write nothing else. Do not commit.
