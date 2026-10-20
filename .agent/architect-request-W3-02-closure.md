# Architect request: W3-02 spec-review closure

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide" and "Token Efficiency";
- `.agent/W3-02-build-spec.md` and `tasks/W3-02-estate-evidence-money-basis.md`;
- `.agent/W3-02-spec-review.md`, which holds 48 questions: 19 Blocker, 22 Should, 7 Nit;
- `.agent/W3-02-mock-measurements.md`, measured mock panel heights and widths at 1440/390. Use these for every height budget. Do not attempt your own browser measurement; it fails in your sandbox;
- `.agent/W3-01-build-spec.md`, including the q1, q2 and q3 rulings, which freeze the provenance DTO, error table and ownership;
- `.agent/post-W2-sequence.md`.

Close every one of the 48 items with exact artifacts (literal JSON, predicates, tables, copy, test names), checked against merged code.
- Where the mock shows something the data cannot support, keep the mock slot and give the honest-gap copy. Q5's comparable total is one example. Never trim the mock.
- Where a read lacks `known_at` or multi-day selection (Q1/Q2), specify the exact new read contract, or rule the honest limitation.
- Align the error codes and cursor with W3-01's frozen table.
- Fix the 390 budgets against the measurements.

Append the result as "Review closure (2026-10-20)" to `.agent/W3-02-build-spec.md`, amending `D-2026-10-20-w3-02-buildspec`, and update the task packet if scope changes. Write nothing else. Do not commit.
