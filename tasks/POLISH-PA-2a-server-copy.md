# POLISH PA-2a - Server copy, codes and titles (Lane A, about 4.5 units)

Status: in_review

USER_REVIEW_REQUIRED: no (merges on review ACCEPT; walkthroughs deferred to the owner walkthrough after this round).

Contract: `.agent/build-sheet-POLISH.md` §3 (record codes, ids, Finding titles), §3.1 "BE" rows, §5 Lane A PA-2,
Addendum 4 (titles) and Addendum 6 (PA-2 split and pre-flight rulings Q1, Q3, Q5, Q6, Q8, Q9, Q10). Branch
`task/POLISH-PA-2a-server-copy`. PA-2b (Q2 preventive counts, Q4 asset labels, §1.4 backend) is a separate slice.

## Acceptance

1. `outcomes/display_code.py` `display_code()` (prefix plus the number zero-padded to at least 3 digits) is used in
   every visible server label and sentence that embeds a record code (Addendum 6 Q8 list and the work link labels);
   stored and wire `code`/`action_code`/`public_code` fields are unchanged.
2. `Finding {id[:8]}` labels become the stored revision title, else "Finding" (estate index, work site/global index,
   global detail, domain Action index), through the Q3 reads. RECURRED reads "Happened again after an earlier
   occurrence ({earlier title})", without the parenthesis when no title is held.
3. `Action {id[:8]}` labels become the Action's display code, else "Action" (Q9).
4. Finding `TITLES` per Addendum 4 (MERGED unchanged); the golden manifest's titles edited directly (Q1).
5. §3.1 BE strings: "Current view", "No end time yet", "No action agreed yet" (with both keyed maps), "Can't be
   compared across these sites yet", "Backup generator did not start on its own", TRANSFER "No record of switching
   to backup power." at read time (Q5), trial cost lines and `VERIFIED_WITH_COST` (Q6). `UTC_SUFFIX` unchanged (Q7).
6. Pure tests pin each changed output; tests pinning the old strings are updated mechanically.
7. Captures: deferred to PA-3 (Addendum 3). Register row R640 (display codes part). Guards: check-all.
