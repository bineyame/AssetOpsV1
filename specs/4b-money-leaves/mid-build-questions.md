# 4b mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
unit (`4b1` or `4b2`), the section, what is stopped, what is built, and what you ask. The Architect rules in
`rulings.md`. Record the count in each packet; a count above zero is a spec-template defect to fix.

Count: **1** (reset at spec rev 2, after handshake round 1; Q1 raised in the 4b1 build).

## Q1 (4b1, spec §2.1 and §2.7 S8; D-4B.17; plant V18)

- **What the spec fixes.** `STRUCTURE_STATED` runs right after `STRUCTURE_COMPOSES` and refuses `stated_by` on a row
  whose unit is not exactly money. S8 asks `check` to raise `STRUCTURE_STATED` on "a planted copy of `revenue` with
  `tariff`'s unit `MONEY / KWH`", and V18 (allow any MONEY exponent) must fail that assertion.
- **Why it cannot.** `check` runs code-major. A row with unit `MONEY / KWH` and `composes="SUM"` is refused first by
  `STRUCTURE_COMPOSES` (a unit with a denominator is never summed, D-3B3.14); with `composes="NONE"` it reaches
  `STRUCTURE_STATED` but is refused there for `composes != "SUM"`, so the unit rule is never the deciding condition
  and V18 passes. (Planting the unit on `revenue` itself is refused earlier still, by `STRUCTURE_UNIT`.) Any
  `MONEY / KWH` plant therefore cannot isolate D-4B.17.
- **Stopped.** Only that S8 assertion (and so the V18 proof). The `_stated` check itself refuses non-money units as
  written (`not row.unit.is_money`), and the `diesel_l` plant (unit L, SUM) shows the unit condition refusing.
- **Built.** Everything else in 4b1, S1 to S10 otherwise as written.
- **Asked.** Which plant should carry D-4B.17? A unit with a MONEY exponent other than 1 and no denominator passes
  `STRUCTURE_COMPOSES` with `SUM` and isolates the rule, for example a planted node `x = tariff * delivered_kwh * om`
  (unit `MONEY^2`, `composes="SUM"`, `stated_by` CHARGE); V18 fails it. Or the check order could change, which the
  spec fixes and I have not touched.

