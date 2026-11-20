# 3C1 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **2** (builder, 2026-11-20). Neither case occurs in the fixture view or the pack manifest (checked: no
October `liability` coverage is ESTIMATED, and no October written field is a float whose text has an exponent), so no
written byte, golden or count depends on the answer. The code carries a provisional behaviour, named below, for the
Architect to confirm or change. Nothing else is stopped.

## Q1 (§2.1, §2.3): the reason for an October actual `liability` that is both ESTIMATED and 0

- **Stopped:** only the choice of reason. Either way nothing is written.
- **Built (provisional):** the ESTIMATED test runs first, so the field is listed `ESTIMATED_NOT_RECEIVED`
  (`records.py` `_actual`).
- **Ask:** is that the reason, or is it `ZERO_NO_ROW`?

## Q2 (§3 "Other numbers", P9): is exponent text "decimal text"?

- **Stopped:** only the treatment of exponent text such as `"1e-05"`. The view turns a binary float into its `repr`,
  which can have an exponent.
- **Built (provisional):** an October written field is accepted when it is an int or matches
  `-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?`, and it is written as `format(Decimal(text), "f")`. Anything else is
  refused `DS1B_NUMBER` (`"abc"` is refused, as T7 checks).
- **Ask:** accept the exponent form (as built), or refuse it as `DS1B_NUMBER`?
