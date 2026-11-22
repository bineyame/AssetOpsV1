# Review: DD4a cold operating reality (discovery, all runs)

Branch `task/DD4-cold-ev-reality`, head c55c8dbe6; diff `main...HEAD` (merge base after 34928040d). Reviewer: fresh
Claude reviewer, not the author. Judged against `packet-DD4a.md` (runs 1-3, deviations 1-17), spec §4.4 and §7 DD4,
rulings D-DD.81-91, D-DD.103, D-DD.119-122.

## Round 1 summary

- **Verdict: accept with findings fixed on the branch** (one Medium, three Low; no High).
- The model and writer work: D-DD.83/85/86/87 in `packs/cold.py`, the D-DD.81/91 join, D-DD.103 span, D-DD.90 scope
  restriction, D-DD.119/120 in-process cold books with the `TEL_BOOKS` byte check, D-DD.121 judge. All are built as ruled.
- B-1031 recomputed from the writer run's 6 Oct readings (`/opt/assetecon/worlds/DD4a-0c5d5fab7b90/`). The peak
  reading is 5.422 °C at 20:25. Five readings are above 5 °C (20:10-20:30), which bounds the excursion at 20-30 min.
  Interpolating the readings (warming about 0.0286 °C/min, cooling about 0.055 °C/min) gives a crossing just after 20:07
  and a return just before 20:33: 20:08-20:32, 25 min. Back-extrapolating one cooled minute from 5.422 gives a peak of
  about 5.477 at 20:24. The bus is UNPOWERED from 19:11 and POWERED at 20:23 (72 min). Event rows: FAILED (CONTROLLER)
  19:11, SUCCEEDED (OPERATOR) 20:22, TRANSFER_RESULT 20:23. All of this matches D-DD.89 and the builder.
- **Medium F1:** the branch introduces a `check_manifest.py` K8 failure (history.json sha) and the packet reports it
  as one that predates the slice.
- Questions for the Architect: two model questions (Q1 Mwea `f_m`; Q2 metered room energy against `M`'s cold kWh).

## Findings

### F1 Medium: K8 fails on the branch only, and the packet calls it pre-existing (acceptance gap, D-DD.90)
- `Docs/demo-sprint/product-direction-layer4/check_manifest.py:2126` (`K8_HISTORY_SHA` 6fd610899336...) and
  `specs/DD-demo-data/packet-DD4a.md` run 3 §"D-DD.89", the sentence "it exits 1 with 7 failures that failed before
  this change too (H9, K8, ...)".
- What is wrong: on main 12e618be3, `check_manifest.py` reports 6 failures (walkthroughs, A1, A2, A3, A5, H9) and
  K8 passes. On the branch it reports 7; the new one is `K8 sha256(history.json) d2498a9c5a0e == the 0K4m base
  6fd610899336`. Run 2's D-DD.90 commit moved `history.json`'s `view_digest` line (deviation 7), and the commit re-pinned
  `simulator/tests/world/golden/history_v1.json`. It did not re-pin K8. "Before this change" means before the run 3 `M`
  commit, not before the slice.
- Why it matters: D-DD.90 asks that sha256(history.json) (K8) equal main's, and that the packet list every pin that
  moves. Merging as is turns main's K8 red, and the packet's account would hide it.
- Fix: re-base `K8_HISTORY_SHA` to d2498a9c5a0e... with a dated note, as H8, H10 and K13 were re-based. The note
  should cite D-DD.90 and deviation 7 (only `view_digest` moved; the scope blocks are asserted by
  `test_scope_seasons_parity`). Also correct the packet line to "6 failures, the same as main". Rerun
  `check_manifest.py` and record the count.

### F2 Low: the D-DD.89 sweep leaves the mock's one-hour window and its in-policy share stale (class sweep, W6)
- `interactive-mockup-vNEXT/screens.js:51` (`window:'6 Oct 2026 · 19:00–20:00 EAT'`); `screens.js:399` ("in policy
  42–58% of the hour", "Coverage: 13 / 13 readings"); `screens.js:627` (`pct(35)–pct(25)` and `'42–58%'`, still
  computed from the old 25-35 minutes); `portfolio.js:18,21` (`window:'6 Oct · 19:00–20:00'`); `screens.js:1072`.
- What is wrong: the cards now say 75-85 minutes above 4 °C inside a window that is 60 minutes long, and the in-policy
  share still derives from 25-35. Deviation 17 lists the chart series and "Exposure size" as left for a content pass.
  It does not list these.
- Why it matters: this is content only, with no layout move, and the mock is not proof of data. But it is the same
  class D-DD.89's sweep names (a story figure typed beside the world's), and the screen now contradicts itself.
- Fix: either extend the window to 19:00-21:00 (25 readings) and compute the share from 75-85, or add these lines to
  deviation 17's list for the content pass, so it is recorded.

### F3 Low: the narrative states a mechanism the readings do not show
- `Docs/demo-sprint/product-direction-layer4/domain-and-decision-models.md:260` (Thika narrative): "The peak came
  two minutes after cooling resumed: the air keeps warming while the coil pulls down."
- What is wrong: in the readings, the compressor is STARTING at 20:23 and RUNNING at 20:24. The per-minute peak is at
  20:24, the minute before the first cooled minute. The pack has no coil lag. "Two minutes" compares the 20:25
  *reading* with the 20:23 bus. The cause is the 1-minute compressor start delay (`cold-compressor-start-delay` 1.0)
  plus the 5-minute reading grid.
- Why it matters: owner rule "one figure, loyal to the operating world" and honest numbers. A walkthrough reader would
  learn a physics claim the world does not contain.
- Fix: "The highest reading, 5.4 °C at 20:25, came two minutes after power returned; the compressor restarts one
  minute after power reaches it." Or drop the clause.

### F4 Low: C-DD6 is listed in both `STUBS` and `LIVE`
- `tools/dd_check.py:44` and `:776`.
- What is wrong: `STUBS["C-DD6"]` now holds the pending tuple, so `test_dd1_check::test_stubs_fail_naming_their_unit`
  still counts C-DD6 as a stub. It passes only because `run` prefers `LIVE` and the clone fetch is empty. If DD5 makes
  the clone fetch real, that test fails for a reason unrelated to stubs.
- Fix: rename the pending table (for example `PENDING = {"C-DD6": (...)}`) and drop C-DD6 from `STUBS`. Add `C-DD6`
  to the live set in `test_dd1_check.py:101`. This is a preference-level tidy, not an acceptance gap.

## Builder defaults 13-17 (confirmed or not)

- 13 (above 4 °C: 79-minute excursion against D-DD.89's "82"). **Confirmed.** The per-minute excursion is
  19:33-20:51. 82 counts the 18:00-23:30 window. `M` now says "75-85 (bounded by 5-minute readings)", which both
  satisfy. The test asserts both figures and that the 3 extra minutes fall after 20:52.
- 14 (Mwea gets no `f_m`). **Followed the ruling's test, but the ruling contradicts itself.** D-DD.119 says "a Site
  with no `kwh` rule **and** no `kwh_model` has no entry". Mwea has `kwh_model` 2635 against `kwh` 2650, so by that text
  it gets 2650/2635. By the ruling's own test it gets none. See Q1.
- 15 (C-DD6 fails on the clone until DD5). **Confirmed** (D-DD.121: "On the clone it fails until DD5 loads").
- 16 (order of test and `M` commit). **Confirmed.** The writer-run rows I read equal the test's figures.
- 17 (sweep wording). **Partly confirmed.** "From about 19:35" and "19:30-19:35 / 20:50-20:55" match the readings. The
  `source_time` 17:25Z is 20:25 EAT and correct. The "two minutes after cooling resumed" sentence and the stale
  window are F2 and F3.

## Checks run (this review)

- `ASSETOPS_GUARD_PYTHON=... tools/heavy-slot.sh -- pwsh -NoProfile -File tools/check-architecture.ps1`:
  "Architecture check passed."
- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- `tools/checks/statement_catalogue.py`: exit 0 ("OK statement catalogue: load, coverage, legacy, scan (9 adopted),
  keys, imports").
- `check_manifest.py`: branch 7794 passed, 7 failed; main 12e618be3 7795 passed, 6 failed. K8 is the difference (F1).
- Join greps (D-DD.81, D-DD.91): one `class TelemetryRefused` (frame), and `QUANTUM` and `readings_bytes` appear only
  in `telemetry.py`. No `record_kind} {r.outcome` remains.
- Read-only scripts over the writer run:
  - Thika 6 Oct events and readings 18:50-21:05 (above).
  - All three rooms end at `2026-11-06T06:00:00+03:00`, with `span.to` equal to that instant; pack `cold-thermal` 2.
  - Kirinyaga `efficiency` is 21/20, 11/10, 117/100, 500/403, 500/403. Mwea and Thika are 1.
  - Per room-month `rounding_total_kwh` is written.
- Tests not rerun. I cite the builder's same-revision reach set (0707ce3c1/0c5d5fab7; c55c8dbe6 changes docs only):
  - simulator 207 passed;
  - backend checks 24 passed;
  - rehearsal (Postgres) 12 passed;
  - 13 M-reading files: 678 passed, 2 failed (the same two as main).
- Not verified: the Kobo W1 byte parity and the mini/EV book pins. I read the tests but did not rerun them. No layout
  evidence applies (no UI code).

## Residual risk the packet does not name

- **Ordinary cycling leaves the 2-4 °C band every day at every room.** These are counts from the writer run.
  - Readings above 4 °C: Mwea 812, Thika 1015, Kirinyaga 1058, on all 129 days.
  - Run lengths above 4 °C: at most 2 readings at Mwea and 3 at Kirinyaga. Thika's longest outside 6 Oct is 3; on
    6 Oct it is 16.
  - About 340-420 single readings fall below 2 °C (minimum 1.945).
  - The product's `cold-excursion/1` uses `cold-min-excursion` 15 and second-reading confirmation. A 3-reading run
    (lower bound 10 min) should not become an excursion.
  - But DD5/DD6 must show Mwea and Kirinyaga with 0 excursions, Thika with 1, and no daily "unconfirmed out-of-band"
    limitation lines on cold pages. Today nothing checks this.
- **Metered room energy against `M`'s cold kWh.** October Σ compressor-meter (5-minute means × 5/60):
  - Mwea about 1576 kWh against `M` 2650;
  - Thika about 1771 against 3720;
  - Kirinyaga about 2114 against 5000.
  - Effect on the bill: D-DD.20 bills the meter, so DD4b's cold bill and energy-cost leaves fall to roughly 40-60 % of
    the generated figures.
  - Effect on Kirinyaga's ratio: with `f_m` applying to the compressor only (not the 1 kW auxiliary), Kirinyaga's
    meter ratio to its f=1 room is about +14 %, not +24 %. OR-CC-1 ("Kirinyaga +24 %") and Mwea's "+0.6 %" may not
    reproduce from readings. See Q2.
- The CLI's `telemetry` now always builds records and re-renders the cold ledger. A `--books` directory without the
  cold ledger refuses `TEL_BOOKS` even for a Kobo-only run. This is acceptable for the world pipeline, but a partial
  books directory no longer works.

## Questions for the Architect

- **Q1 (model; deviation 14).** D-DD.119's text gives a Site with `kwh_model` an accounting-period `f_m`, but its test
  gives Mwea none. Which holds?
  - The builder's default: Mwea f = 1.
  - The alternative: Mwea October/November at 2650/2635, which moves Mwea's readings and the parity pins.
- **Q2 (model, owner-visible in DD4b).** The declared room meters about 1576, 1771 and 2114 kWh in October, against
  `M`'s 2650, 3720 and 5000. By D-DD.20 the bill follows the meter. Which story figures follow the room, and which
  are restated: the cold energy cost, Kirinyaga's +24 % (diluted to about +14 % at the meter by the auxiliary) and
  Mwea's +0.6 %? Or are the room's declared figures (leak, COP, auxiliary) revisited? Nothing in DD4a should be tuned.
  This needs a ruling before DD4.4 writes the cold bill.
