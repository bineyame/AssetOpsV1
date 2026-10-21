# Architect request: W4-02 q10 (renewable page items)

Read:
- `.agent/W4-02-build-spec.md`, q1–q9 and the pages dry-read;
- `.agent/W4-02-pending-rulings.md`, q10;
- the v69 `renewable` mock.

Code: branch `task/W4-02-mini-grid-depth` at `54b955f9`.

Rule each q10 item with exact artifacts:
- Service, Fuel and Backup tabs are omitted from the row until their pages land, because the navigation guard rejects new "Not available yet" tabs. Confirm that is acceptable while the slice is in progress, given all four pages land before review, or give the exact guard update.
- The new registry nodes `I-mini-depth-read` and `I-mini-depth-ui`.
- The "Watch" status word.
- The Opportunity-decision CTA copy.

Append the result as "Run 10 rulings (q10)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
