# Architect request: W3-03 final review items (rF)

Read:
- `.agent/W3-03-build-spec.md`, closure 1's footer disclosure and r1b's cursor signing;
- `.agent/W3-03-final-review.md`;
- the v69 `portfolio` mock.

Code: `85efbea7` on `task/W3-03-portfolio-composition`.

Rule with literals and tests:
- **M1.** Give the exact footer source and window disclosure literal, and its placement in `ContextFooter`.
- **M2.** `/portfolio` returns 503 on any server started without `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX`. Choose one, and give exact literals:
  - docs only: say exactly which docs and dev or run scripts set the key, and how;
  - a local-dev default key, with its source and a guard that production can never use it.

  The owner walkthrough must not see a broken page.
- **L1–L5.** For each, give the literal fix or confirm it is acceptable as-is:
  - L1: "coverage incomplete" shown on an empty scope;
  - L2: identical short Finding IDs;
  - L3: raw codes in the drawers;
  - L4: a footnote about linked cells when none exist;
  - L5: missing mock icons.

Append the result as "Final review rulings (rF)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
