# Architect request: W3-02 c2-q5, c2-q6 and the missing Evidence eyebrow

Read `.agent/W3-02-build-spec.md` (all rulings including c2), `.agent/W3-02-pending-rulings.md` (c2-q5 and c2-q6), and the v69 `globalevidence` mock.

Code: `b9612338` on `task/W3-02-estate-evidence-money-basis`.

Rule with exact artifacts:
1. c2-q5: the registry prerequisites chosen from the W3-01 Actions precedent: area `estate-aggregation`, `I-capability-read` and `D-estate-comparable-sites`. Confirm or replace them.
2. c2-q6: the captures do not follow the cold/EV links into the Site pages, so c2-q3 (the link-following tests) is still open. Name the exact test or capture that proves those links.
3. The mock shows an "Evidence" eyebrow above the page title. Estate roots have no breadcrumb, and `PageHeader` has no eyebrow slot, so it is currently missing. A mock element is never dropped. Give the exact placement and component change, say who owns it (Lane A for shell or shared components), and give the test.

Append the result as "Commit-2 rulings (c2b)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
