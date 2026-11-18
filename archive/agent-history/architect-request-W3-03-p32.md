# Architect request: W3-03 P-3-2 (empty-state 390 card cap) (r3b)

Read:
- `.agent/W3-03-build-spec.md`, through r3;
- `.agent/W3-03-pending-rulings.md`, P-3-2, with the three options;
- `.agent/W3-03-mock-measurements.md`;
- the v69 `portfolio` mock cards.

Code: `e055b841` on `task/W3-03-portfolio-composition`.

Two problems with the empty state:
1. **Card height at 390.** The empty state fails `card0 218>207` and `card1 218>207` at 390. The long operating-cost "no value" text wraps to three lines and stretches its row partner. Choose one, with literals and a test:
   - accept it as a limitation;
   - a CSS-only fix;
   - shorter wording.

   Prefer faithfulness to the mock and honest copy. Do not raise a cap unless the mock's own measurement justifies it.
2. **Matrix scroll with zero Sites.** The matrix-scroll check fails because there are zero Site columns. Should the check apply with zero Sites? Give the exact predicate.

Append the result as "Run-3 empty-state ruling (r3b)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
