# Architect request: W3-03 closure round 2

You are the AssetOps Architect. Read:
- `.agent/W3-03-build-spec.md`, including "Review closure (2026-10-20)";
- `.agent/W3-03-closure-check.md`: 4 OPEN items (Q6, Q9, Q24, Q31) and 7 new questions (N1–N7);
- `.agent/W3-03-mock-measurements.md`, now re-measured with every top-level block: context, value cards, pulse, aside, footer and page height;
- `.agent/W3-01-build-spec.md` and `.agent/W3-02-build-spec.md`.

Close all 11 with exact artifacts:
- Q24: caps for every measured block, using max = mock + max(24px,10%).
- Q9: per-variant (a)–(e) expectations, and the named W1 priced-line producer.
- N1: rule one owner and one shared `group_key` function. If W3-02 owns it, record that in `.agent/W3-02-build-spec.md` as a versioned amendment.
- N2: a first-match-wins order.
- N3: a supersession index listing every superseded line in the body, with its replacement.
- N6: assign each test to a commit.

Append the result as "Review closure 2 (2026-10-20)" to `.agent/W3-03-build-spec.md`, plus any W3-02 amendment. Write nothing else. Do not commit.
