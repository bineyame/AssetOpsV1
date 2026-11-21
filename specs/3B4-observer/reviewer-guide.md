# 3B4 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new mechanism on today's Finding store, a migration,
and a name added to a writer's table list. Read `spec.md`, `rulings.md`, then the diff. Done means every question of
spec §9 answers yes with evidence and every plant below fails its named test. Cite the builder's gate run at the same
commit; run nothing heavy unless a finding needs it (`.ai/ROLE_CONFIG.md`).

## What to check, and how

1. **Independent checks (W2).** Tests 1, 2, 4 and 5 write their expected tables and figures as literals from the pack
   (`derived-values.json`), never from `OBSERVED`, `signs` or `observe`.
2. **The rule.** `observe` follows spec §2.2's order exactly; strict `>`; band from the actual `of_factor`; the
   un-carried actual; no `Decimal` quantised; no float.
3. **Unknown is not zero.** No path turns a `None` side or band into 0 (grep `or Decimal(0)`, `or 0` in
   `structure/observe/`).
4. **The store.** The migration's CHECKs equal 0056's plus the arms (test 10); every INSERT is in the two stores; the
   lifecycle table of spec §4.3 is implemented first-match (test 11); the claim has no money field.
5. **The sweep (W6).** Re-run spec §4.4's grep on the branch; every reader is class A or in the table; the four
   predicates are present; `chain/threads.py` is unchanged.
6. **Seams.** `git diff main...HEAD --stat`: no `registry.py`, row file, `sources.py`, `i18n/` or `outcome_map.py`
   change; the guard diff is the one `$findingTables` name; check-all and `check-architecture.ps1` pass.
7. **Roles.** A Site manager's grant admits only on its own Site; money leaves need the finance lead (test 15).

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Must fail |
|---|---|---|
| P1 | `outstanding` declared `DOWN` | test 3 and start-up (`STRUCTURE_OBSERVE_DIRECTION`) |
| P2 | `billed_kwh` added to `OBSERVED` | start-up (`STRUCTURE_OBSERVE_LEAF`) |
| P3 | `technical_loss_kwh` moved to `OBSERVED` | start-up (`STRUCTURE_OBSERVE_SOURCE`) |
| P4 | `field_visits` moved to `OBSERVED` as UP | start-up (`STRUCTURE_OBSERVE_KIND`) |
| P5 | `dawn_days_below` removed from both tables | start-up (`STRUCTURE_OBSERVE_COVER`) |
| P6 | `abs(gap) < band` instead of `<=` for inside | test 5 (band equals gap) |
| P7 | band computed from the target's `of_factor` | test 4 (Kobo band 23.6 becomes 14.0) |
| P8 | a `None` band treated as 0 | test 5 (`TOLERANCE_NOT_AVAILABLE`) |
| P9 | the carried actual used (`site_bridge(...).actual`) | test 6 |
| P10 | `snapshot_as_of` in the basis | test 7 and test 11 (rebuilt snapshot writes) |
| P11 | `UNCONFIRMED` written for an `INSIDE_TOLERANCE` observation | test 11 |
| P12 | the thread-sources predicate removed | test 13 |
| P13 | `finding_detail` predicate removed | test 13 |
| P14 | a SITE_MANAGER grant on another Site admitted | test 15 |
| P15 | a money gap written into the claim | test 11 (claim keys) |
| P16 | `MONTH_OPEN` check removed | test 14 |

## Not findings

- Snapshots served with reason `RULES` after merge (the code digest moves when `check.py` changes).
- The fence still counting fuel, cold and EV revisions (`R-FENCE-FUEL`, D-3B4.9).
- No opportunity Findings (D-3B4.4); no words or screen (D-3B4.13); `liability` not observed (spec §11 Q6).
