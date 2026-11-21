# 4a reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake answers D-4A.15 to D-4A.26). Discovery review (W5): a new observer on the structure read, a change to the
stated-node rule (D-4A.1), kWh under a money heading. Read `spec.md`, `rulings.md`, then the diff. Done means every
question of spec §8 answers yes with evidence and every plant below fails its named test. Run nothing heavy yourself
unless a finding needs it; cite the builder's gate run at the same commit (`.ai/ROLE_CONFIG.md`).

## What to check, and how

1. **The fixtures are hand literals (W2).** Tests 1, 2, 2b, PG1b and PG2/PG3 write spec §5's numbers (PG1b's readings
   and band, D-4A.15); none computes an expected
   value with `month_energy`, `feeder_month` or the evaluator.
2. **Unknown is never zero.** For every step of spec §2.4's table, a missing input gives `value None`,
   `NOT_AVAILABLE`, the stated cause and note; the only zeros are `adjustments_kwh`, `unmapped_kwh` and `billed_kwh`
   with the month's billing held (ZERO_WHEN_HELD, and its sources named). Evidence: each step of §2.4 is hit by the
   variant §5.4b names (test 2b, whose map keys equal its `STEPS` literal), and "never 0" holds on the evaluated
   structure (PG1(e), PG3(a); D-4A.17). The registry's `absent` for `unexplained_loss_kwh` is unchanged and unread
   by 4a (test 8); the packet carries `R-ABSENT-META`.
3. **Leaks keep their names.** Unmapped kWh is a join (D-4A.7), never `metered − adjustments − billed`; V12 is the
   check. Unexplained losses are not clamped (V12) and carry MODELLED.
4. **Evidence and origins.** Delivered MEASURED with `demo-simulated` for SIMULATED readings; technical and
   unexplained MODELLED (PG1b: from real readings and a Foundation band); metered, billed, adjustments RECORDED; unmapped and tariff DERIVED. 5c's word follows from
   these (5c §2.4); nothing here reads "Verified" or "Recorded" for a reading.
5. **The stated-node change is minimal.** `check._stated` gains exactly `or row.unit == KWH`; `evaluate.py` and
   `bridge.py` have no diff; 4b's S8 plants still refuse.
6. **The W6 sweep.** Every changed literal in an existing test is in the packet's table with its reason (stated kWh
   nodes, derived tariff, registry v4, new property), found by the class grep of spec §6.4, including
   `test_3b7a_site_inputs_seam.py:49` and `test_w402_roles_properties.py:91-109`. A literal changed for any other
   reason is a finding. The packet states that stored v3 snapshots read `REBUILD_NEEDED` until 3B7a rebuilds them
   and that 4a touches none (D-4A.25).
7. **Seams.** `git diff main...HEAD --stat` lists only spec §0's files; no migration; no change under `tools/`;
   check-all and `check-architecture.ps1` pass; `structure/energy/rules.py` is pure (test 8).
8. **No served text.** No new user-facing string anywhere except, if 5c has merged, the 5c record keys of D-4A.12
   (with D-4A.20's `adjustments_kwh` → BILLING and D-4A.24's `METER_REF_CONFLICT`) as SC-1 statements in the last
   commit, after SC-1a's merge.
9. **Live reads and failures.** A live read passes `known_at` None to `feeder_month` and `latest_revisions`; no
   `except` in `structure/energy/` (test 6b; D-4A.23).

## Planted violations (each must fail the named test; the builder shows each failing once, in a scratch copy)

| # | Plant | Fails |
|---|---|---|
| P1 | the band applied to metered kWh instead of delivered | test 1 (Mto technical 279) |
| P2 | unexplained clamped at 0 | test 2 V12 |
| P3 | technical 0 when no band is declared | test 1 (Kobo) |
| P4 | a month with an uncovered day summed anyway | test 2 V3 |
| P5 | unmapped computed as metered − adjustments − billed | test 2 V12 (310, not 140) |
| P6 | charges matched by meter subject only | test 1 (Kobo unmapped 8690); test 2 V9b (140, not 115) |
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
| P18 | `feeder_month` drops the `known_at` cutoff on readings | PG1(b) (216, not 144) |
| P19 | an absent `unexplained_loss_kwh` written as 0 (its ZERO_WHEN_HELD honoured) | test 1 (Kobo); PG3(a); test 8 if done by reading `absent` |
| P20 | the account route matches any customer the meter was ever assigned to | test 2 V9c (115, not 140) |
| P21 | the meter taken from `body.meter_ref`, or a conflict ignored | test 2 V18 |
| P22 | a live read passes `now()` as `known_at` to the reads | test 6b |
| P23 | `MiniReadUnavailable` caught and turned into an absence | test 6b |
| P24 | Foundation revisions taken as the current ones (`superseded_at IS NULL`) instead of those known at the cutoff | PG1b(c) (technical `MONTH_OPEN`, not `LOSS_BAND_NOT_DECLARED`) |
| P25 | billed 0 when the month has no charge (billed step 3 dropped) | test 2b V24 |
| P26 | `BINDINGS_CHANGED` feeders summed anyway | test 2b V19 |
| P27 | coverage given when the feeders are not `ONE_SET` | test 2b V26 |

## Not findings

Billed kWh's disagreement at a Site with productive-class usage (D-4A.10). The tariff as one average (D-4A.6). Mto's
metered gap split below the meter (D-4A.5, pack divergence). No tariff-sheet reader, no tolerance on the band, no
Finding (spec §9). No figure for a partial feeder month (D-4A.2). No band basis (D-4A.18). The registry's `absent` metadata of
`unexplained_loss_kwh` (D-4A.17, `R-ABSENT-META`). Stored v3 snapshots reading `REBUILD_NEEDED` (D-4A.25).
