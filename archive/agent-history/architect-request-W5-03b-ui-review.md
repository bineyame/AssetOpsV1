# Architect request: W5-03b E4/E6 review items (final)

Read:
- .ai/ROLE_CONFIG.md ("Mock fidelity", D1-D6, lesson 15)
- .agent/W5-03-build-spec.md (E4/E6)
- .agent/W5-03b-ui-preflight-rulings.md (1-16 plus build rulings 17+)
- .agent/W5-03b-ui-review.md (E4 REVISE, E6 REVISE, items 1-5)
- the backlog entry about the shared DataTable stickyFirstColumn white header in .ai/MILESTONE_REVIEW_BACKLOG.md
- the v69 mock (EV health, EV scenarios)

The code is on task/W5-03b-ev-health-ui; read it with `git show task/W5-03b-ev-health-ui:<path>`.

Rule items 1-5 exactly. Cite the mock for each.
- Item 2: the sticky-header white cell in the shared primitive (primitives.css:5406-5415). It affects every user of the primitive (W5-03a EV Availability/Energy, E4, possibly cold). Rule whether this fix round corrects the primitive now to match the mock's grey header, with a test, and name the file ownership. Recommended: fix it once here.
- Items 1, 4 and 5: give exact CSS values.

Confirm that E6-H1 and the Lows (E4-L3, E6-L2, S-L1, S-L2) are to be fixed as the review states, or amend them.

Append rulings to .agent/W5-03b-ui-preflight-rulings.md, numbered after the last one. Apply them to .agent/W5-03-build-spec.md. Add register rows after the register's last row only for real departures. Close the backlog line if item 2 is fixed here. Do not touch product code. Do not commit.
