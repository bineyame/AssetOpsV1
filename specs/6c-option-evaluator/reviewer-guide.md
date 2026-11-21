# 6c reviewer guide

**DRAFT, awaiting owner P6.** Architect (Claude), 2026-11-21, rev 0. Discovery review (W5): a money figure and a new
mechanism. Read `spec.md`, the P6 proposal, 0K4d's `packet.md` §2 and `review.md` item 3 (the residual risk), 6a
`spec.md` §2 to §3, then the diff. The unit is done when every question in spec §7 is answered yes with evidence,
and every plant in spec §6 fails its named test.

## What to check, and how

1. **Hand values (W2).** Tests 1 and 4 write spec §5's literals. An expected value computed by calling the evaluator,
   `difference` or `evaluate` is High. Recompute by hand:
   - F1b's `stop-70-reserve-30` row: (400 / 2) × 1.25 − (100 / 2) × 0.05 = 247.50; × 12 = 2970.00; − 90.00 = 2880.00;
   - the near-set threshold 3012.00 × 0.9 = 2710.80;
   - C1's and E1's values.
2. **The difference rule.** Read `structure/difference.py` against spec §2 operator by operator. Check that:
   - the product uses `val1(b)` with `d(a)`, and `val0(a)` with `d(b)`;
   - the zero short cut applies only to an exactly-zero change;
   - a needed `None` value names its leaves.

   The parity test covers every node of the three registries.
3. **Missing is never zero (owner rule).**
   - In F1a, every option with a battery-use change has value `None`, naming `wear_rate`.
   - `stop-90-reserve-25` is valued, because its battery-use change is exactly 0. Confirm that this follows from the
     rule and is not a special case.
4. **No design value, no vertical code.** Test 8's two AST scans and the R5 regex pass. Grep `decisions/` and
   `structure/difference.py` for 2,916, 262.50, 12.00 and 210, and for every structure key. The only constants are
   `TIE`, `DAYS_PER_MONTH` and `OUTCOME_FACTOR`.
5. **The admission is 0K4d's rule.**
   - `judge` is the body `admit` now calls.
   - 0K4d's two test files pass unchanged: run them.
   - The evaluator recomputes every case's admission and refuses a mismatch.
   - The dawn readings appear in no disposition rule. Read §3.4 R1 to R4 and the run outcome against the code.
6. **Ranking.**
   - A REJECTED option never ranks.
   - `RANKING_INCOMPLETE` withholds every rank when any admitted value is missing.
   - The near set and distance pick `stop-70-reserve-30` over the higher `stop-70-reserve-25`.
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

## Open for the handshake

- Pre-flight items 1 to 3 (spec §0). The negative `extra_l` is the one that can stop the build (§11 Q7).
- Whether K1's trimmed copy of the 0K4d file may live under `backend/tests/fixtures/`. The default is yes: it is a
  SIMULATED model output, it holds no operator data, and it is about 30 KB.
