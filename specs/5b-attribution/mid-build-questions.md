# 5b mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **1** (reset for spec rev 2, 2026-11-20; Q1 raised in unit 1).

## Q1 (unit 1): a RESIDUAL row's `split` and `reason`

- **Section.** Spec §2.2 (`split: str  # SPLITS`, `reason: None unless NOT_SPLIT`) and §2.3 step 6 (the RESIDUAL row's
  `effect` and `unobserved_*`). Neither fixes the RESIDUAL row's `split` or `reason`; `SPLITS` has no RESIDUAL value,
  and `lowest` lists "rows with split LEAF or NOT_SPLIT, and RESIDUALs" as if a RESIDUAL were neither.
- **Stopped.** Only the assertion of those two fields (test 3(a) leaves them unasserted, saying so). Everything else
  of the RESIDUAL row is built and tested (factor None, parent, AR1, home, effect, unobserved, evidence, currency).
- **Built, provisional.** `split` `NOT_SPLIT`, `reason` `DETAIL_NOT_AVAILABLE` (`bridge.py`, marked): the residual is
  the part not split for want of detail, and it names the same `detail_missing` tuples a `DETAIL_NOT_AVAILABLE` row
  names. The alternative is `LEAF` with reason None. `lowest` and `by_home` include a RESIDUAL either way.
- **Asked.** Which pair does a RESIDUAL carry? `5c` reads `reason` to word each stop (D-5B.10), so the choice is
  user-visible.
