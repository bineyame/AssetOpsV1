# 4a reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new observer on the structure read, a change to the
stated-node rule (D-4A.1), kWh under a money heading. Read `spec.md`, `rulings.md`, then the diff. Done means every
question of spec §8 answers yes with evidence and every plant below fails its named test. Run nothing heavy yourself
unless a finding needs it; cite the builder's gate run at the same commit (`.ai/ROLE_CONFIG.md`).

## What to check, and how

1. **The fixtures are hand literals (W2).** Tests 1, 2 and PG2/PG3 write spec §5's numbers; none computes an expected
   value with `month_energy`, `feeder_month` or the evaluator.
2. **Unknown is never zero.** For every step of spec §2.4's table, a missing input gives `value None`,
   `NOT_AVAILABLE`, the stated cause and note; the only zeros are `adjustments_kwh`, `unmapped_kwh` and `billed_kwh`
   with the month's billing held (ZERO_WHEN_HELD, and its sources named).
3. **Leaks keep their names.** Unmapped kWh is a join (D-4A.7), never `metered − adjustments − billed`; V12 is the
   check. Unexplained losses are not clamped (V12) and carry MODELLED.
4. **Evidence and origins.** Delivered MEASURED with `demo-simulated` for SIMULATED readings; technical and
   unexplained MODELLED; metered, billed, adjustments RECORDED; unmapped and tariff DERIVED. 5c's word follows from
   these (5c §2.4); nothing here reads "Verified" or "Recorded" for a reading.
5. **The stated-node change is minimal.** `check._stated` gains exactly `or row.unit == KWH`; `evaluate.py` and
   `bridge.py` have no diff; 4b's S8 plants still refuse.
6. **The W6 sweep.** Every changed literal in an existing test is in the packet's table with its reason (stated kWh
   nodes, derived tariff, registry v4, new property). A literal changed for any other reason is a finding.
7. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files; no migration; no change under `tools/`;
   check-all and `check-architecture.ps1` pass; `structure/energy/rules.py` is pure (test 8).
8. **No served text.** No new user-facing string anywhere except, if 5c has merged, the 5c record keys of D-4A.12 as
   SC-1 statements in the last commit, after SC-1a's merge.

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | the band applied to metered kWh instead of delivered | test 1 (Mto technical 279) |
| P2 | unexplained clamped at 0 | test 2 V12 |
| P3 | technical 0 when no band is declared | test 1 (Kobo) |
| P4 | a month with an uncovered day summed anyway | test 2 V3 |
| P5 | unmapped computed as metered − adjustments − billed | test 2 V12 (310, not 140) |
| P6 | charges matched by meter subject only | test 1 (Kobo unmapped 8690) |
| P7 | a read with no register assignment left out of unmapped | test 2 V9 (118, not 140) |
| P8 | productive-class kWh counted in billed kWh | test 2 V13 |
| P9 | tariff over every CHARGE line | test 2 V13 |
| P10 | a straddling read prorated | test 2 V6 |
| P11 | metered valued with no register held | test 2 V5 |
| P12 | `_stated` accepts any unit | test 4 (the `diesel_l` plant) |
| P13 | `CommercialLeafSource.stated` keeps refusing `metered_kwh` | test 5; `test_4b*` regression |
| P14 | the per-context memo removed | test 6 |
| P15 | `MAIN_OF` left as `"revenue"` | test 7; PG3(a) |
| P16 | a LIVE reading labelled `demo-simulated` | test 3 |
| P17 | `technical-loss-band` 100 accepted | test 9 |
| P18 | `feeder_month` drops the `known_at` cutoff | PG1 |

## Not findings

Billed kWh's disagreement at a Site with productive-class usage (D-4A.10). The tariff as one average (D-4A.6). Mto's
metered gap split below the meter (D-4A.5, pack divergence). No tariff-sheet reader, no tolerance on the band, no
Finding (spec §9). No figure for a partial feeder month (D-4A.2).
