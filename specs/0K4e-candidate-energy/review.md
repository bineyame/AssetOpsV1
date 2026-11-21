# 0K4e review

## Round 1 (discovery, W5): Claude reviewer, 2026-11-21, head `aa2bc5595`, diff `b96d5e978..aa2bc5595`

**Summary (verdict: ACCEPT WITH FIXES on the branch).**
- The rule is right. I recomputed E1, E2, E3, E5, E5b and E9's planted night by hand, and every figure matches the code.
  The walk never counts a gap as zero load and never counts cover after the read range. The 15-minute fallback is
  `interval_start < s <= interval_end` and runs only on MISSING.
- Outside row 5b, 3.3 equals 3.2. Stored 3.2 history keeps the same md5. The reconcile pass enqueues exactly the windows
  whose head is 3.2 (E9-E11 green on my own run). Reading the 3.2 phase by patching `MODEL_VERSION` is sound.
- Served text comes from SC-1 statements over stored codes. `reasons` and `missing` are not extended, and the only
  baseline change is the one token swap.
- **M1 blocks merge:** `test_sc1_statements.py` fails on the branch. It is in the spec's regression list, and the packet
  does not cite it.
- Four Low findings: two untested rule clauses (both found by my plants), one served-text class with new instances,
  and one downstream effect the packet does not name.
- Q1: keep F05's extension. It is a fixture artefact, not a hidden 3.3 effect. Name the real effect, recency, in §5,
  and queue one Finding-level case for it.
- `USER_REVIEW_REQUIRED` stays true. Served candidate litres and Findings move when the coordinator runs the
  reconcile pass.

### Findings

**M1 (Medium, acceptance gap): the SC-1 catalogue test fails.** `backend/tests/test_sc1_statements.py:343` and `:352`.
`test_t8_shipped_catalogue_loads` pins the exact set of shipped statements and vocabularies. The branch adds
`dispatch.energy_cover`, `dispatch.energy_cover_cause`, `dispatch_input` and `reading_problem`, so the test fails with
"Extra items in the left set: 'dispatch.energy_cover_cause', 'dispatch.energy_cover'". The vocabulary assertion would
fail next. Spec §3 lists `test_sc1_statements.py` as regression, and neither the packet's check table nor its evidence
logs show it was run. Main's version passes. A merge would turn the fast tier red.
Fix: add the two statement keys and the two vocabulary names to the expected sets, with a 0K4e (D-0K4.24) comment as
the other adopters have. Then rerun the file.

**L1 (Low, missing test): nothing tests "the fallback runs only on MISSING".** `dispatch_v3.py:235` (`held_value`).
My plant changed `if found.problem != "MISSING"` to `if found.problem is None`, so a NOT_GOOD, CONFLICTING or
AMBIGUOUS_SERIES reading would be overridden by an overlapping GOOD mean. All 31 tests in `test_0k4e_energy_to_cover.py`
and `test_0k4e_readers.py` still passed. The code is correct today, but the clause is unguarded.
Fix: add one case: a NOT_GOOD 5-minute load reading ending at a slot inside a GOOD 15-minute mean should give `GAP`,
`problem "NOT_GOOD"`.

**L2 (Low, missing test): nothing tests the feeder re-read at each slot (D-0K4.23 R1).** `dispatch_v3.py:246`
(`_slot`). My plant read the feeders once, at the window start, instead of at each slot. All 31 tests still passed.
The ruling and the decision-table row both say that a feeder bound later counts from its binding on.
Fix: add one case with a second load feeder bound partway through the night. Its load should count from that slot on.

**L3 (Low, served text; spec-conformant, pre-existing class): energy-cover transitions read "records missing".**
`plain.py:306-320`. Two kinds of segment fall through to the legacy branch:
- a segment with one `SHORT` end and one `COVERED` end, for example E9's 22:30-22:35;
- a `COVERED` point withheld by minimum runtime.

Each carries a legacy `_NOT_EVIDENCE_GAPS` text. `missing_text` maps that text to "Detail not available ...", so the
segment reads "Records needed to decide are missing or conflicting: Detail not available for this part of the
assessment..". The double period is in the output. 3.2 already serves this for its own transitions, and D-0K4.24 says
legacy text wins, so this is not a defect of the slice. But 3.3 adds a new instance at every SHORT-to-COVERED
boundary, and the cause is the energy test, not a missing record. That is the false reason D-0K4.24's "Why" wants to
avoid.
Fix (queue, with Q9): have the plain reader render `_NOT_EVIDENCE_GAPS` texts as their modelling words, as
`finding_read` already does. The Findings side is correct: `portion_cause` adds the SHORT words beside the transition
words.

**L4 (Low, downstream not named): in-flight verification plans block after the reconcile.**
`actions/verification.py:151-152` and `:251`.
- After the reconcile, every in-flight reserve-trial verification plan's baseline pin reads `moved`. The reason is that
  `_baseline_facts` compares the full interval `result`, and that includes `model_version`. It fails closed, so the
  plan needs a superseding plan.
- A new freeze over 3.2 days that are still stale refuses with `VERIFICATION_BASELINE_NOT_CURRENT` before it reaches
  `VERIFICATION_MODEL_NOT_COMPARABLE`.

Neither is wrong, but spec §5 and the packet name only the mixed-baseline refusal.
Fix: add one line to the packet's Downstream section for the coordinator.

No High findings. No finding depends on preference, except the copy note under residual risk.

### The rule, by hand (judge item 1)

- **E1.** Slots 18:00 to 05:55 are 144 slots. 144 x 10 kW x 5/60 h = 120 kWh. Held = 0.5 x 200 x 0.95 = 95 kWh, which
  is less than 132. Result: SHORT.
  - **E2.** 0.7 x 200 x 0.95 = 133 kWh, and 133 >= 132. Result: COVERED, with 3.2's reason and the 20 kW margin.
- **E3.** 144 x 9.5 x 5/60 = 114 kWh, and 1.1 x 114 = 125.4.
  - SOC 96: 0.66 x 200 x 0.95 = 125.4 kWh, exactly the edge. Result: Candidate.
  - SOC 95: 123.5 kWh. Result: Indeterminate.
  - Without efficiency (P3), SOC 95 holds 130 kWh and turns Candidate. With `>=` dropped to `> need` (P2), it also
    turns Candidate. So both plants fail E3.
- **E5b.** At 18:00, 18:05 and 18:10, `lookup_asset` reads the 5-minute means. At 18:15 no reading ends at that slot,
  and 18:15 is not inside (18:15, 18:30], so the result is GAP `feeder_demand`/`MISSING` at 18:15.
  - Swapped convention: 3 x 10/12 + 4 x 20/12 = 110/12 = 55/6 kWh. The extra means ending 18:35 and 18:40 let the swap
    reach cover at 18:35, so P10 really fails. I confirmed this with a plant.
- **E9's planted night.** Held = 0.6 x 200 x 0.95 = 114 kWh.
  - From 22:00 there are 48 slots, giving 120 kWh and an edge of 132. Result: SHORT.
  - From 22:30 there are 42 slots, giving 105 kWh and an edge of 115.5. Result: SHORT.
  - From 22:35 there are 41 slots, giving 102.5 kWh and an edge of 112.75. Result: COVERED.
  - Five both-ends-COVERED segments give 25 minutes. 4d: 60 min x 30 kW x 0.3 = 9 L, and 25 min gives 3.75 L. The total
    is 24 h x 30 x 0.3 = 216 L.
- **The walk.**
  - The memo is keyed by slot. The backward fill accumulates only on REACHED and propagates GAP and END unchanged.
  - `s > read_range.end` ends the walk, so the slot at the range end itself is read. A plant of `>=` fails 5 tests.
  - An unbound feeder or PV gives `GAP UNBOUND`, and a missing value gives `GAP MISSING`. Nothing defaults to zero (P4
    plant fails E4).

### Judge items 2-8

2. **Outside the branch.**
   - `_evaluate`'s diff touches row 5b only. The withheld `Point` carries `cover`, and `payload()` adds the key only when
     it is non-empty.
   - `_control_changes` gains the two keys. `_configuration` emits capacity and efficiency per Foundation revision, with
     that revision's validity. Where a revision also carries a reserve, which every fixture and template does, the
     edges are the same as 3.2's.
   - The four S3 cases moved to PV 40 still test their own rule. Bounding is still asserted on portions and
     `candidate_bound`. Minimum runtime still withholds 30 minutes. The inverted SOC span still makes its segments
     Indeterminate through the cohort-limit rule. The capability-unbound case still needs PCS bound for the PV-alone
     branch.
   - Small loss: `test_two_capability_candidate_is_bounded_to_candidate_segments` no longer reaches the
     two-capability branch, and its name is now stale. The interval-level row-5b Candidate is covered by E2 (segment)
     and E9 (Postgres).
3. **History.**
   - E9 compares md5 of `row_to_json` for every 3.2 run and revision, before and after, and the two are equal. E11
     enqueues exactly the 3.2 heads, and a second reconcile enqueues nothing.
   - The `MODEL_VERSION` patch is sound. The worker takes the 3.2 module object loaded from git at `b96d5e978`, and the
     reads compare against `dispatch_v3.MODEL_VERSION` at call time.
   - The only import-time capture is `financials/money_eligibility.py:36`, which E9 does not touch.
   - Caveat (no effect on the assertions): the test's 3.2 input sets include the two new controls, because the 3.3
     store reads them. Their `input_sha256` therefore differs from what `main`'s store would have written.
4. **Downstream.**
   - 4d moves litres between candidate and necessary only (9 L to 3.75 L, total 216 L). Total invariance holds by
     construction, because `necessary_l` is the total less candidate, so E10 mainly proves the stored spans reach 4d.
   - `SUPPORTED_MODELS` has both versions. The claim-limit read answers for the 3.3 revision.
   - Verification refuses mixed models (`verification.py:258-262`; see L4 for the plans already in flight).
   - The 5c claim holds. On `task/5c-deep-dive-screen`, `test_4_h_kobo_litres` reads `test_4d_litre_split.LakesideInputs`
     stub spans and never calls the analytic, so no literal moves. The served Kobo figure moves only after the
     reconcile.
5. **Served text.**
   - `plain._segment` and `portion_cause` render the `dispatch.energy_cover*` statements. `reasons` and `missing` gain
     nothing (E1 and E7 assert `missing == []`).
   - `git diff b96d5e978 -- tools/checks/` is the one fingerprint pair (`3349d495df46` to `0bae2f18559a`), and the
     source diff is the token only.
   - Copy note (preference): "before the assessed records end at {at}" names the read range's end, not the end of the
     records. Records may continue past it.
6. **Q1, recommendation: keep the F05 extension.**
   - F05 tests limitation-and-closure, not the energy rule. Its readings stopped at the run's last report only because
     the fixture was written for 3.2. In an operating world, load and PV records continue after a run.
   - The extension makes the case physically trivial: a 1.58 kWh need against 57 kWh held. So it hides nothing about
     F05.
   - It does hide a real class effect that nothing tests at the Finding level: **recency.** A battery-support run whose
     post-run load and PV have not arrived yet reads `GAP`, so its portion is RECORD_GAP, until a later delivery
     reassesses the window. A Finding on the latest run therefore opens late, and does not open on the first pass.
   - Recommend: name recency in spec §5, and queue one Finding-level case in which the post-run records arrive in a
     second delivery and the Finding then opens. No Architect ruling is needed unless the Architect wants that case
     inside 0K4e.
7. **Deviations.**
   - E3 (one SOC point, 1.9 kWh): forced, since 200 x 0.95 makes held a multiple of 1.9. P2 and P3 still fail. Sound.
   - E5 (last quarter hour as 5-minute means): forced by E1's PV-at-06:00. A 15-minute PV mean ending 06:00 would move
     cover to 05:50. Sound.
   - E10 (planted day only): sound, see item 4.
   - Decision-table 3.2 row: correct, and it matches the code.
   - Branch name: immaterial.
8. **Plants.** Each was applied in a scratch copy of the backend, its test run, then reverted.
   - P1: E1 fails.
   - P4: E4 fails.
   - P6: E6 fails (`range_end` 00:00, not 06:00).
   - P10: E5b fails.
   - P13: 6 reader tests fail.
   - P14: E13 fails.
   - Mine:
     - `s >= end`: 5 tests fail.
     - Fallback on any problem: **survives** (L1).
     - Feeders read once: **survives** (L2).

### Checks run (this review, head `aa2bc5595`)

| Check | Result |
|---|---|
| `pytest test_0k4e_energy_to_cover.py test_0k4e_readers.py test_s3_dispatch_v3_analytic.py test_s3_claim_limit_vocabulary.py test_sc1_statements.py` (heavy-slot) | 443 passed, **1 failed** (`test_t8_shipped_catalogue_loads`, M1) |
| `heavy-slot.sh --db` with base `assetops_test`, run-owned clones: `test_0k4e_dispatch_33_postgres.py`, `test_s4_finding_store_postgres.py`, `test_s4_finding_read_postgres.py`, `test_s3_claim_limit_postgres.py`, `test_s3_dispatch_read_postgres.py`, `test_4d_litre_split_postgres.py` (`-n 4`) | 41 passed in 41.76 s |
| check-all (fast), once | `All 42 guards passed (blocking; 0 advisory, 0 warned).` 142.8 s wall |

**Not verified.**
- `test_md0_mechanism_postgres.py`: `TEMPLATE_STALE`, and the template is left for the coordinator. `mechanism-v1.json`'s
  generator runs are all PV 40 against a 30 kW load, so they take the PV-alone branch and I expect no movement. That is
  unproven until the template is rebuilt.
- The full suite. I cite the implementer's same-revision runs. Their w302 and k7 failures are explained as base drift
  and environment.
- `select-tests.py --base main`: not run.
- The frontend: not touched by the diff.

### Residual risk the packet does not name

- **The 6-hour bracket decides evening points.** Windows are UTC days, and the read range ends at 06:00 UTC the next
  day, which is 09:00 local at Kobo (UTC+3). An evening battery-support point is Candidate only if PV covers 1.1 x load
  by local 09:00. On overcast mornings it is `NOT_REACHED` whatever the battery holds. The spec accepts this as
  conservative, but the 4d candidate figure after the reconcile will partly measure the bracket, not the battery.
- **Data cadence.** The walk steps every 5 minutes. Instant readings at a 15-minute cadence, and 5-minute means stamped
  every 15 minutes (the S3 fixture shape), give `GAP` at the second slot. A real site with that cadence would read every
  battery-support point as GAP (RECORD_GAP in Findings). The 15-minute fallback rescues interval means only.
- **Off-grid points get their own walk.** A point not on the 5-minute grid of its neighbours starts a slot grid of its
  own, so memo sharing (E8b) holds only for aligned report times. Cost stays bounded by points x slots, which is fine at
  the cadences seen.
