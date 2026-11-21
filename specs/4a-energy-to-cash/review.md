# 4a review: energy to cash (discovery review, W5)

## Round 1 (2026-11-21, fresh Claude reviewer; branch `task/4a-energy-to-cash` at `f0b864eb9`, base `aa3ebefe8`)

**Summary (verdict: ACCEPT).**
- I judged against spec rev 2 §2 to §8, rulings D-4A.1 to D-4A.26 and reviewer guide rev 2. All eight done questions of §8 answer yes on the evidence below.
- I reproduced the figures myself. PG1b from real readings: clinic 2x24x31 = 1488, res 4x24x31 = 2976, mill (23x2+4)x30 + 1.5x24 = 1536, so delivered 6000. Technical is 5 % per feeder: 74.4 + 148.8 + 76.8 = 300. Unexplained is 6000 - 300 - 5580 = 120. Kobo: billed gap 8645 - 8550 = 95 at 0.40, giving +38.00; price gap 0 over 8645 kWh, giving 0.00. My Postgres rerun of these passed: 4 tests.
- Honesty: every step of §2.4 is reached by its named variant, and test 2b's map equals `STEPS`. On the evaluated structure, PG3(a) and PG1(e) give None and NOT_AVAILABLE, never 0. Stored v3 snapshots read REBUILD_NEEDED (`structure_snapshot/read.py:93`, version-relative test `test_3b7a_structure_snapshot.py:440`).
- W6 sweep: every changed pinned literal traces to registry v4, the stated kWh nodes, the new property, `MAIN_OF` or the fifth builder. None hides a regression.
- My plants: 5 of 8 caught. The 3 that survive are Low test gaps (F1 to F3). The code is correct on each path, but no test holds it.
- Q1 and Q2 defaults: both sound (see below). The Architect can confirm each in one line.
- Merge with main: only the bookkeeping files conflict (`.ai/state/data.md`, `index-2.md`). 3B6 and 3B4 are sequenced after 4a.

### Checks run (this review, at `f0b864eb9`; code identical to `1052af7e8`)

| Check | Result |
|---|---|
| `pwsh tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`) | Architecture check passed |
| `pwsh tools/check-agent-workflow.ps1` | passed |
| heavy-slot pytest, no DB: test_4a, 3b1, 3b3 evaluate, 4b1, 4b money leaves, 5a, 3b7a seam, 3b7a snapshot, w402, 5b, 4d litre split | 556 passed, 1 skipped |
| `heavy-slot --db` with `run-host-tests.ps1 -- test_4a_energy_to_cash_postgres.py` (PG1+PG1b, PG2, PG3a, PG3b) | 4 passed (33 s) |
| Implementer's Postgres regression (7 files) at `59ea84aa9` | cited, not rerun. `59ea84aa9..1052af7e8` changes only the new PG test, the fixture and the questions file, so the source is the same |
| Implementer's check-all at `1052af7e8` | cited, not rerun. `1052af7e8..f0b864eb9` is docs only |

Layout evidence: not applicable (no screen, no served text).

### My plants (scratch copy of HEAD, deleted after the run)

| # | Plant | Result |
|---|---|---|
| Q1 | unmapped takes metered's absence only at steps 4 to 7, so with no reads it gives **0** | caught, V23 |
| Q2 | unmapped's step for the missing read kind is dropped, giving **0** | caught, V22 and 2b |
| Q3 | adjustments' step for a month with no charge is dropped, giving **0** | caught, V24 and 2b |
| Q4 | the band ignores a Foundation revision that lacks it | caught, test 3 |
| Q14 | the account route also matches charges whose subject is a METER | caught, test 1 Mto, V10 and others (8 failed) |
| Q5 | the first of several assignments is taken as the read's customer | **survives** (F1) |
| Q6 | the largest band is applied to total delivered, instead of each feeder's own | **survives** (F2) |
| Q11 | the `METER_REF_CONFLICT` check on an assignment is dropped (only reads checked) | **survives** (F3) |

### Findings

- **F1 (Low; test gap; `tests/test_4a_energy_to_cash.py` §5.4 variants; rule at `structure/energy/rules.py` `_customer`).**
  - **What is wrong:** §2.4 "Charged" says a read whose meter has more than one assignment containing it has no customer (REGISTER_GAP). No vector has two such assignments, so `found[0]` would pass every test.
  - **Why it matters:** the plant can charge a read through the wrong customer, which hides unmapped kWh (a leak reads as smaller).
  - **Fix:** add one variant to V9b: a second `M-2204` assignment to another customer over the same span. Expected unmapped 140, billed 5425.
- **F2 (Low; test gap; `rules.py` `technical`).**
  - **What is wrong:** every DECLARED vector, PG1b included, has all bands equal (5). Per-feeder Σ_f (Σ_d) × band_f is therefore never told apart from "one band × total".
  - **Fix:** add one no-DB vector with two DECLARED feeders at different bands, for example Kobo's three feeders at 4, 5 and 6: 62 + 145 + 279 = 486.
- **F3 (Low; test gap; `rules.py` `metered` step 4, D-4A.24).**
  - **What is wrong:** V18 plants the conflict on a read only. The assignment half of step 4 (`a.meter_ref != a.body_meter_ref`) is untested.
  - **Fix:** add V18b, where the `M-0099` assignment's `body_meter_ref` is `M-0098`. Expected: metered, unmapped and unexplained NOT_CALCULATED_YET `METER_REF_CONFLICT`.

None of these is an acceptance gap of §8, and none blocks. Each is a one-line variant and can go on the branch before merge or into the next 4a touch.

**Not findings, checked:**
- The private import of `commercial.months._parse` (spec §4.2 names 3A4's rule; the guard passes).
- Billed 0 when every charge is FIXED. The contract (`records_v1.py:164`) forbids a quantity on FIXED and requires kWh on USAGE, so this 0 is a recorded zero and not a missing kWh.
- Money-only ADJUSTMENTs are not counted (D-4A.8).
- The second `latest_revisions` call per Site-month (performance only, see residual risk).

### The two defaults (for the Architect, one line each)

- **Q1: the world dates moved and the gateway is enabled.** This does not weaken PG1b. What PG1b proves still holds:
  - the roles-4 set starts at install + 27 min (2026-09-30T06:27Z), before October's first local midnight (2026-09-30T21:00Z), so it is in force all month;
  - the band is effective before the month and recorded on 10-04T01:00Z, after day 3, so PG1(d) and PG1b(c) still test the cutoff (P24 caught);
  - every batch is asserted ACCEPTED, so the readings are real accepted evidence.
  - Enabling the gateway and sources is a harness prerequisite (`demo_combined_kobo.py` does the same), not a change of what is measured.
  - **Recommend confirming.**
- **Q2: PG1(e)'s note on unexplained.** §2.4 binds and the test follows it correctly. Both reasons are true and neither is 0, so the honesty rule holds either way.
  - The order is defensible: unexplained reads its operands in chain order, and the delivered gap is upstream.
  - One inconsistency remains: `technical` checks the band **before** delivered's absence, while `unexplained` checks delivered first. After days 1 to 3, sibling cells name different records (band against readings gap).
  - Since technical is absent whenever delivered is, unexplained could take technical's absence first and always match it (band first, then delivered).
  - This is a preference for 5c's coherence, not an acceptance gap. **Recommend:** confirm §2.4 as written and amend D-4A.17's PG1(e) wording to `FEEDER_READINGS_GAP` for unexplained. If the Architect prefers sibling-consistent reasons, swap unexplained steps 1 and 2 (a one-line rules change plus V3's expected note).
  - The band reason for unexplained stays held by test 1 (Kobo) and V20/V21. The evaluator passes leaf absences through unchanged (`evaluate.py` `_leaf`), so the pure coverage carries to the structure.

### Merge risk with main (`12a0c6356`)

- `git merge-tree` conflicts only in `.ai/state/data.md` and `.ai/state/index-2.md`; both are append-style bookkeeping. `specs/INDEX.md` auto-merges.
- Main's code changes since the base (0K1 replay files) do not touch 4a's files.
- 3B6 (D-3B6.19, D-3B6.20) is ordered after 4a's merge and relies on `EnergyLeafSource._state` keying by `SITE_TYPE_TO_STRUCTURE`. It does, so a cold or EV Site falls through to the fallback.
- 3B4's `check.py` edit is also after 4a. Neither needs a 4a change.

### Residual risk not in the packet

- **Demo database.** After merge, every stored v3 snapshot serves REBUILD_NEEDED until 3B7a's build runs. The demo or walkthrough database needs that rebuild scheduled, or the deep-dive serves "rebuild needed" everywhere.
- **Duplicate commercial scans.** A structure read now makes two `latest_revisions` scans per Site-month (commercial source and energy source). That is fine at demo scale, but grows with portfolio size.
- **`money.py` stated branch.** It returns NOT_CONNECTED for `metered_kwh` and `billed_kwh` without checking the Site type. This is harmless today (no cold or EV row states, D-3B6), but must be revisited if a later structure reuses those factor IDs.
- **Feeder readings not in kW.** A feeder whose readings are not in kW (an energy counter) reads FEEDER_READINGS_GAP rather than a unit-specific note. That is honest (no figure) but names the wrong cause.
