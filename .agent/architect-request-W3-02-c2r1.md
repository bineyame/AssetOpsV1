# Architect request: W3-02 commit-2 review (r1) — two copy points

Read `.agent/W3-02-build-spec.md` (c2, c2b, c2c), `.agent/W3-02-commit2-review.md`, and the v69 `globalevidence` mock.

Rule with literal artifacts:
1. "Record details" contains a raw JSON dump. The owner's rule is plain text, with no system vocabulary on client screens. Give the exact plain rendering: the fields, their labels and their order. Alternatively, rule that the disclosure is removed only if the mock has no such element.
2. The eyebrow is uppercase, as ruled in c2b, but the mock shows sentence case. The mock is the layout and copy authority. Give the exact casing and the CSS rule.
3. Confirm the remaining Lows: add the missing named test `meetsMeasuredNarrowLayoutWithoutDocumentOverflow`, and correct the stale ledger `data_owner`. The Notice icon predates this slice, so carry it as backlog.

Append the result as "Commit-2 review r1 rulings" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
