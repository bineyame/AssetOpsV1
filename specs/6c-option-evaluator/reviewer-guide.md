# 6c reviewer guide

**Rev 1, ready for the handshake** (P6 approved by the owner, 22 Nov 2026). Architect (Claude), 2026-11-21 rev 0,
2026-11-22 rev 1. Discovery review (W5): a money figure and a new mechanism. Read `spec.md`, the P6 proposal and its
rulings D-P6.1 to D-P6.19 (`specs/6-decision-valued/rulings.md`; D-P6.2 to D-P6.6 most), D-0K4.38, 0K4d's
`packet.md` §2 and `review.md` item 3 (the residual risk), 6a `spec.md` §2 to §3, then the diff. The unit is done when every question in spec §7 is answered yes with evidence,
and every plant in spec §6 fails its named test.

## What to check, and how

1. **Hand values (W2).** Tests 1 and 4 write spec §5's literals. An expected value computed by calling the evaluator,
   `difference` or `evaluate` is High. Recompute by hand:
   - F1b's `stop-70-reserve-30` row: 200 × 1.25 − 50 × 0.05 = 247.50; × 12 = 2970.00; − 90.00 = 2880.00;
   - F1i's delta: (100 + 200) / 2 = 150, August left out;
   - the near-set threshold 3012.00 × 0.9 = 2710.80;
   - C1's and E1's values.
2. **The difference rule.** Read `structure/difference.py` against spec §2 operator by operator. Check that:
   - a changed leaf's `d` is its delta, and `val1` of it is base + delta (D-P6.3); no `stated` map reaches
     `evaluate` (D-P6.4);
   - the product uses `val1(b)` with `d(a)`, and `val0(a)` with `d(b)`;
   - the zero short cut applies only to an exactly-zero change;
   - a needed `None` value names its leaves.

   The parity test covers every node of the three registries.
3. **Missing is never zero (owner rule).**
   - In F1a, every option with a battery-use change has value `None`, naming `wear_rate`.
   - `stop-90-reserve-25` is valued, because its battery-use change is exactly 0. Confirm that this follows from the
     rule and is not a special case.
4. **No design value, no vertical code.** Test 8's two AST scans and the R5 regex pass. Grep `decisions/` and
   `structure/difference.py` for 2,916, 262.50, 12.00, 210, 212.75 and 242.444, and for every structure key. The only
   constants are `TIE`, `OUTCOME_FACTOR` and the ±1 signs; there is no `30` and no division by `days`.
5a. **The world-month rule (D-P6.2).** A study without `frame` values nothing (F1h, K1) while its admission and dawn
   are stored; a SITE_RECORD study of another Site or missing the decision's full month is refused; the monthly
   change is the mean of full months (F1i). Run the K1 and F1h plants.
5. **The admission is 0K4d's rule.**
   - `judge` is the body `admit` now calls.
   - 0K4d's two test files pass unchanged: run them.
   - The evaluator recomputes every case's admission and refuses a mismatch.
   - The dawn readings appear in no disposition rule. Read §3.4 R1 to R4 and the run outcome against the code.
6. **Ranking.**
   - A REJECTED option never ranks.
   - `RANKING_INCOMPLETE` withholds every rank when any admitted value is missing.
   - The near set and distance pick `stop-70-reserve-30` over the higher `stop-70-reserve-25`.
   - An exact zero is `WORTH_THE_SAME_AS_NO_ACTION` and never ranks (F1f, D-P6.5).
   - `AT_GRID_EDGE` appears in F1g only.
7. **Labels.** The source class is computed from the origins actually used: F1 gives SIMULATED; C1 and E1 give
   RECORDED. `assumed` lists `diesel_price`. No label is hard-coded per fixture.
8. **The study's identity.** The run stores the sha256 and identity of the file. K1's provenance file names its
   source. `ignored_cases` lists `stop-90-reserve-30`.
9. **Seams.**
   - Test 9's import rules hold.
   - `runs/admission.py` changes only by adding `AdmissionMeasures` and `judge`, with `admit` delegating to `judge`.
   - Nothing imports `simulator` or `host`.
   - The evaluator never runs a replay.
10. **Writes.** Only 6a's adapter writes, through `add_run`. The deferred completeness check holds in test 6.
11. **Output.** The JSON line rounds once, money to cents and other quantities to 6 places; the stored rows are
    unrounded (D-P6.6). Refusals are variants of 6a's `decision.refused` and say "simulation", never "replay"
    (D-P6.7, D-0K4.50).

## Open for the handshake

- Pre-flight items 1 to 3 (spec §0), answered from `main` by D-P6.11; the packet confirms each.
- Whether K1's trimmed copy of the 0K4d file may live under `backend/tests/fixtures/`. The default is yes: it is a
  SIMULATED model output and holds no operator data.
- The owner's Q1 (Kobo's litres "Not available yet" until 0K4f) changes no rule here: 6c already values a
  Site-record study when one exists.
