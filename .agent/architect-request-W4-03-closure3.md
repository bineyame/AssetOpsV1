# Architect request: W4-03 closure round 3 (breadcrumb root)

Read `.agent/W4-03-build-spec.md` (all closures), `.agent/W4-03-closure-check2.md` and `.agent/W3-01-build-spec.md` (the global `/findings` route and its query keys).

Close the remaining item and N3 with literal rules:
- On canonical Alternatives, the breadcrumb `Findings` root links to W3-01's `/findings`, which is a W4-03 prerequisite. Give the exact href, and say whether it carries `from`/`to`/`known_at` or is bare, consistent with W3-01's link conventions. Give the test assertion.
- On opportunity detail, say whether the root stays disabled, and give its copy.
- Remove the "until a reviewed global index exists" condition, with a supersession-index entry.

Append the result as "Review closure 3 (2026-10-20)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
