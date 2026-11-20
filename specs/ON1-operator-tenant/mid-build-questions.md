# ON1 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **1** (reset at spec rev 2, 2026-11-20).

## Q1 (spec §2): the code for a structural refusal (open; default built)

- **Section.** §2 says "an unknown or missing key is refused" at every level and gives `sites` 1 to 50, `people` 1 to
  50, `roles` 1 to 5, but names no code for an unknown or missing key, a container of the wrong JSON type, or a list
  outside its bounds. (Duplicate keys and unparsable JSON are `ONBOARD_FILE`, as built.)
- **Stopped.** Nothing: the default below is small and reversible (one code in `operator_file._strict`/`_list`).
- **Built (default).** `ONBOARD_FORMAT` ("This is not an onboarding file of version 1.") with `where` the path of
  the object or list concerned (`sites[0]`, `people[2].roles[0]`, `sites`; none at the top level). A Site field of the
  wrong type inside a well-formed Site entry is `ONBOARD_SITE_INVALID` (the Site parser judges it).
- **Ask.** Confirm `ONBOARD_FORMAT`, or name another code (for example a new `ONBOARD_STRUCTURE`).
