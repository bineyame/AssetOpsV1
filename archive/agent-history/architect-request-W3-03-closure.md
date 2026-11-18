# Architect request: W3-03 spec-review closure

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W3-03-build-spec.md` and `tasks/W3-03-portfolio-composition.md`;
- `.agent/W3-03-spec-review.md`, which has 35 questions: 9 Blocker, 21 Should, 5 Nit;
- `.agent/W3-03-mock-measurements.md`;
- `.agent/W3-01-build-spec.md` (all rulings, and the estate selection token v2 amendment) and `.agent/W3-02-build-spec.md` (closures 1–3). These are frozen: W3-03 must reuse their wire exactly.

Close all 35 with exact artifacts, verified against merged code and the frozen W3-01/02 contracts:
- Q1–3: copy the W3-01/02 wire literally (coverage shape, domain enum, state vocabulary, cursor).
- Q4–7: map every mock element, including the drawers, the extra cell lines and the value-card detail lines and tones. Where data is unsupported, give honest-gap copy; never trim.
- Q9: freeze the clock and windows, choose every "or" fixture explicitly, and give literal assertions for the decline path.

Append the result as "Review closure (2026-10-20)" to `.agent/W3-03-build-spec.md`, amending `D-2026-10-20-w3-03-buildspec`, and update the packet if scope changes. Write nothing else. Do not commit.
