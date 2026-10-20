# Architect request: W4-01 review findings (r1)

Read:
- `.agent/W4-01-build-spec.md`, all rulings including "Run 8 rulings (q8)", which already rules the 13 commit-5 readings and the two guard/registry points;
- `.agent/W4-01-review.md`: H1–H3, M1–M5. The reviewer wrote it without seeing q8;
- the v69 `sitework-incidents` and `sitework-maintenance` mocks.

Code: branch `task/W4-01-work-case-core` at `afa35e79`.

For each finding, either point to the q8 ruling that already settles it, or give the exact replacement (literal copy, component, data source and test), so a Sonnet fixer decides nothing. Cover:
- H1: the subtab counts `Actions (n) · Incidents (n) · Maintenance (n)`. Give the count source and the null/unknown display.
- H2: the empty-block `evidence` icon.
- H3: remove the extra `Read in full` strip item, or rule its copy.
- M1: the page-two `known_at` strip behaviour.
- M2: the missing `w401-work.json` fixture. Build it, or amend the spec.
- M3: every unruled visible string.
- M4: run-9 readings 1–5, 8 and 11.
- M5: the cherry-picked W3 money prerequisites that W4 does not call. State whether this deviates from q3 ruling 6, and whether it is harmless at merge.

Append the result as "Review r1 rulings" to `.agent/W4-01-build-spec.md`. Write nothing else. Do not commit.
