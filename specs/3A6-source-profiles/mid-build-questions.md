# 3A6 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **1** (reset at spec rev 2, 2026-11-20).

## Q1 (2026-11-21, commit 2): A9 (a)'s map is not one to one

- **Section.** §6 A9 (a) gives the kobo `State` map `{"Invoiced": "INVOICED", "Paid": "PAID", "Quote": "INVOICED"}`.
  `check_layout` (3A3, D-3A3.2; unchanged by §2.2) refuses a map that is not one to one, and `compile_profile` runs
  `check_layout`, so that profile is `PROFILE_INVALID columns.8.paths.0.map` before step 4b is reached.
- **Stopped.** Only A9 (a)'s literal map. **Built.** Step 4b as specified; A9 (a) is tested with the one-to-one map
  `{"Invoiced": "INVOICED", "Paid": "PAID", "Quote": "DRAFT"}` (same uncovered key `Quote`, same expected refusal
  `ADMIT_MAP_UNCOVERED {header: "State", value: "Quote"}`); plant V22 fails it.
- **Asked.** May a profile's map be many to one (profiles are never rendered, so one-to-one guards nothing for
  them), or does A9 (a) take the one-to-one literal? Default kept: maps stay one to one for every layout.

