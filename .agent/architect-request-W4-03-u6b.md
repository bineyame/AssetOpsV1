# Architect request: W4-03 unit-6b builder readings (u6b)

Read:
- `.agent/W4-03-build-spec.md`, through u6;
- the unit-6b section of `git show acff855f:.agent/W4-03-phase-handoff.md`, which lists 14 readings taken without a ruling;
- the v69 mocks for the mini Finding Alternatives page and the cold/EV Finding sections.

Code: `acff855f` on `task/W4-03-mini-decisions-work`. It adds:
- the Alternatives page;
- the six-tab row;
- the breadcrumb `Findings › Finding code unavailable › {section} · site:`;
- the "Finding section unavailable for this site." page;
- the Performance Alternatives link gating;
- the navigation guard list.

For each reading, confirm it or give the exact replacement (a literal copy string, route or predicate) and a test. Flag any reading that departs from the mock.

Unit 7 is being built in parallel. If a ruling changes anything unit 7 relies on, say so explicitly.

Append the result as "Unit-6b builder rulings (u6b)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
