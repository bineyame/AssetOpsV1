# W2 technical designs re-review - amended 87428eb0

Reviewer: fresh Claude reviewer (independent, not the author). Inputs: cold review c8405733, EV review d5ca77b9, amend request 7927df76, amended designs at 87428eb0 (diffed against 5f7eb279). Read-only code spot checks; no suites run.

## Verdicts
- **Cold (`.agent/W2-technical-design-cold.md`): RETURN.** Two Medium findings remain, both narrow and fixable in place.
- **EV (`.agent/W2-technical-design-ev.md`): ACCEPT.** EV M1-M6 are resolved. EV inherits the W2-00 ledger insert from cold, so the fix for cold R-M1 flows into EV with no EV text change.

## Prior Mediums
- Cold M1 is resolved. Line 36 and the table at lines 40-47 map every NOT NULL dispatch column of `finding`, `finding_revision` and `analytic_run` (0009:80-84,102; 0007:48-50). CHECKs are keyed on `'mini_grid'`, which matches `finding_episode.py:78`. One literal per domain (`mini_grid`, `cold_chain`, `ev_charging`) is used for Finding, revision, recompute job and episode. Adding `finding_revision.domain` with a composite FK is concrete.
- Cold M2 is resolved, apart from R-M1 below. `MESSAGE_CONFLICT` is kept. `EVENT_ID_CONFLICT` and `SESSION_ID_CONFLICT` are `CONFLICT` with the first-accepted reference, and the replacement for `evidence_rejection_conflict_kind` (0005:239-241) is exact. Both receipt locations (`ledger_reads.py:232-233,376`) are named. The four `EV_*` codes are `REJECTED`. v4 has its own `V4_MEASUREMENTS` list, all keys explicit-null, and `INTERVAL_DELTA` is in W2-00.
- Cold M3 is resolved. The `$assessTables` (ps1:645), `$consequenceTables` (664) and `$ledgerConflictAllowed` (700) edits, the new `$consequenceWorkTables`, the probes and the transaction owner all exist as named.
- Cold M4 is resolved. There are forcing tables, one mechanism per case, the probe-disagreement rule is deleted, and the pack is standalone. Arithmetic is spot-checked below.
- Cold M5 is resolved. Every field is shaped (lines 142-155).
- EV M1-M5 are resolved, consistently with cold. The shared 0020 and W2-00 are used, numbering is 0024-0026, the domain literal is `ev_charging`, and writers are placed in the same rule-8 arrays.
- EV M6 is resolved. The vendor-adapter recommendation is clear for the owner: "defer `vendor-format-ev-peer/1` to the pilot gate". The cost is stated, and the OCPP 1.6J format, Wh units, owning module and refusal codes are all named.

## Arithmetic spot check (cold, Euler per minute, r = 1 - 0.08/72)
- `excursion` checks out. From 3.80 degC, T(19:15) = 20 - 16.2*r^15 = 4.068, publishing 4.1. T(19:20) = 4.156, publishing 4.2. T(19:10) = 3.979, publishing 4.0, which is in band. So the start is bounded [19:10,19:15], the latest start is 19:15, and the open episode lower bound at 20:00 is 45 min, which is at least 15. The failed result at 19:05 matches the 5-minute timeout.
- `missing-probe`: 7/13 is about 0.54. `late-reading`: 12/13 is about 0.92 at the 20:05 cutoff. When 19:20 arrives late, the degree-minute bounds change (10-minute vs 5-minute rectangles). Start bounds stay the same, so the anchor holds.
- `normal` holds numerically, but the rationale given is wrong (L1).
- The EV numbers also hold: 30.000, 15.000, 10.000 and 25.000 kWh, and 300 s.

## New Medium findings (cold; both block cold only)

**R-M1 - The event INSERT's conflict target breaks message dedup for EVENT rows.** (W2-00; cold lines 38, 134, 136)
- Today, message dedup relies only on `ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING` (`postgres_evidence_ledger.py:482`). `ledger_service.py` has no message precheck.
- The design gives EVENT inserts the event-identity partial target instead. It also says "a unique violation on another constraint is not converted". So a retransmitted event message (same message ID, in a different batch) raises a message-unique violation rather than returning `DUPLICATE` or `MESSAGE_CONFLICT`, which the design itself promises at line 22.
- Precedence is also unspecified when a record collides on both the message key and the event identity.
- Fix: keep the message arbiter on every INSERT. Detect event-identity and session-START collisions with a savepoint and reread, with a fixed order: message, then event, then session. Alternatively, precheck under a named advisory lock. Then restate the exact `$ledgerConflictAllowed` regex and the probes to match.

**R-M2 - The cold vendor peer's raw format is unnamed.** (cold line 157, W2-02 proof at line 163)
- `vendor-format-cold-peer/1` "maps an independent raw-format fixture" but names no raw format, units, module, fixture path or refusal codes. This is the same implementer-chosen contract that EV M6 returned.
- Fix: name the format, units, module, path and codes, or defer the peer to the pilot gate as EV does. Deferring is consistent with demo speed, and the line-163 proof would need updating.

## Low (non-blocking)
- L1 `normal` (line 82): the "three powerless minutes" rationale misses the thermostat cycle. Passive warming takes T to 4.008 at 19:55, which publishes 4.0. The compressor runs from 19:56, so 20:00 publishes 3.9. The no-Finding claim holds only by a 0.008 degC margin and strict `>`. State this, and also state the transfer and generator behaviour after `GRID_RESTORE` at 19:35, which is unspecified.
- L2 Range notation differs between the designs. Cold `19:15-19:40` is inclusive on point times (6 points dropped). EV `08:10-08:15` is one slot. The cold window is `[19:00,20:00)` yet counts the 20:00 point among its 13. Pick one convention.
- L3 EV names `consequence_worker.py` (line 105), but the existing worker is `financials/recompute.py:216`.
- L4 Cold and EV work rows use `UPDATE status`. The fuel path instead uses append-only `financial_consequence_work_attempt`. This is concrete but a divergence, so confirm it is intended.
- L5 Cold line 36 says 0025 widens "both" domain CHECKs. EV line 12 widens only `finding.domain`. Name the `finding_revision` widening in EV.
- L6 Cold roles still say "ONE per attempt" (lines 60, 63), and the cold `fault`/CLEAR plugged state is unspecified in EV. Hold/drop/fault are new to `observation/transform.py`, which today only has bias and dropout. Name the module.

## Not verified
I ran no suites and no architecture or registry checkers. I did not trace `assessment_worker.py` transaction plumbing or the composite-FK swap on `finding_revision` against live data.
