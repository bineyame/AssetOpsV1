# Architect request: W4-02 spec-review closure

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W4-02-build-spec.md` and `tasks/W4-02-mini-grid-depth.md`;
- `.agent/W4-02-spec-review.md`, which has 33 questions: 10 Blocker, 19 Should, 4 Nit;
- `.agent/W4-02-mock-measurements.md`;
- `.agent/W4-01-build-spec.md`, all rulings, because the W4-01 case model freezes at merge;
- `.agent/W3-01-build-spec.md` q1–q4;
- `.agent/post-W2-sequence.md`.

Close all 33 items with exact artifacts checked against merged code. Some items expose architecture gaps rather than wording:
- Q1: the missing mini-grid binding roles;
- Q2: W4-01 records never becoming accepted evidence;
- Q3: the worker, job domain and enqueue ownership.

For each gap, either specify the exact new contract or rule the honest limitation, keeping the mock slot with gap copy.
- If a contract is new, say which slice owns it.
- If it changes W4-01's frozen contract, record a versioned amendment in `.agent/W4-01-build-spec.md`, with its migration and compatibility effect, per the sequence's freeze rule.
- Rule the local-day versus UTC-day conflict explicitly.

Append the result as "Review closure (2026-10-20)" to `.agent/W4-02-build-spec.md`, amending `D-2026-10-20-w4-02-buildspec`. Update the task packet if scope changes. Write nothing else. Do not commit.
