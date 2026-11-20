# 3A3 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **1** (reset at spec rev 2, 2026-11-20; Q1 recorded by the Architect after review r1).

## Q1 (§2.5 budget lines; raised by review r1 F3, not by the builder)

§2.5 read `tariff_usd_per_kwh` and `diesel_usd_per_l` from the plan, which holds neither. The builder took them from
`tenant.prices` (packet D2) without asking. Ruled in `rulings.md` D-3A3.13: they come from plan money ÷ plan quantity,
exact, or `EMU_PLAN_PRICE`.
