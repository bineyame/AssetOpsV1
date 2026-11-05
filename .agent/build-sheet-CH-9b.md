# Build sheet CH-9b: verifying "run the mill at midday" with `midday-productive-shift-1`

- Architect: Claude (Architect 5), 2026-11-04. Owner-agreed (OWN-1104, D-AW-7 reversed): an Action is verified against the outcome it was designed for. Rulings are logged in the plan as **CH9b-R**.
- Lane 2: CH-9 → **CH-9b (2.5 units)** → DD-1. Branch `task/CH-9b-midday-verification`, cut after CH-9 merges. CH-6a (the MG-5 `kpi` record, `judge`) must be on main; if it is not, stop and report.
- Design: `implementation-logic-design-proposal.html` §5b.1 levers `productive-load-midday@1` (`must_not_harm: [MG-5, MG-4]`, `verification: midday-productive-shift-1`) and `verification_plans.midday-productive-shift-1` (`measure: productive_kwh[midday]`, `compare: before/after, Complete days`, `min_days: 3`, …).
- Paths: `B/` = `backend/assetops_backend/`. The existing family is `reserve-trial-1` (`B/actions/verification.py`, `B/actions/verification_rules.py`).

## 0. Result and boundary

**Observable result.**
- The Kobo "run the mill at midday" Action gets a frozen verification plan at apply. Once 3 fully checked days exist on each side, it gets a stored outcome: VERIFIED, NOT_VERIFIED, or an honest "not judged yet: {n} of 3 fully checked days after the change".
- On VERIFIED the headroom thread moves to "Checked and working, monitoring" (RESOLVED_MONITORING), through the existing lifecycle.
- The verification page shows the plan's metric (midday productive use before and after, with its days) and the guardrails (MG-5, MG-4) in a generic metric table.

**Not in this slice.** A general lever catalogue loader (CH-8); other levers; any change to `reserve-trial-1` behaviour (its outcomes stay byte-equal).

## 1. Rulings (CH9b-R)

| # | Ruling |
|---|---|
| R1 | **A family registry, minimal.** `B/actions/verification_families.py`: `{"reserve-trial-1": <today's code path>, "midday-productive-shift-1": MiddayShift}`. Plan freeze, outcome write and reads dispatch on the plan's family. `reserve-trial-1` is moved behind the registry unchanged; an L2 test proves its outcomes are byte-equal before and after. Whether a family column exists on `verification_plan` is pre-flight P2. If not, migration `0047_verification_family` adds `family text NOT NULL DEFAULT 'reserve-trial-1'` (append-only rules unchanged). |
| R2 | **Plan (frozen at apply).** The baseline is the last 3 COMPLETE `productive_kwh` days (daylight period, CH-9 R5/§9) before the effective day. The later window is the first 3 COMPLETE days on or after it, looking at most 14 days ahead. The plan stores the candidate day ranges, `min_days = 3` and the rule version. Days are chosen by grade only, never by value. |
| R3 | **Pass rule from the catalogue, never fitted.** The rule is the catalogue entry's own comparison (P1 reads the full entry). If the entry has a margin or target, use it. **If it gives none, stop: the owner declares the margin** (for example "later mean above baseline mean"), recorded verbatim as an OD item. No value is chosen from the data. |
| R4 | **Guardrails (`must_not_harm`).** MG-5 (`critical_served`, CH-9 R9) and MG-4 over the same later days must not be worse than baseline by the KPI's own `judge` rule (CH6-R R5-R6). A guardrail breach is NOT_VERIFIED with reason `GUARDRAIL_<KPI>`. A guardrail day that is not COMPLETE makes the outcome `NOT_JUDGED` (counted as missing), never a pass. |
| R5 | **Evaluator.** `MiddayShift.evaluate(plan, rows)` is pure, over `SnapshotReader` rows at the evaluation cutoff. It writes the outcome and its metrics (`metric_key`, `window_name` BASELINE/LATER, `value_text`, `threshold_text`, `unit`) through the existing verification store, and triggers from the CH-1b `snapshots` consumer when a later day becomes COMPLETE. Its outcome states are the existing set. The lifecycle needs no change, because it already maps a VERIFIED `verification_outcome` to RESOLVED_MONITORING (`B/chain/lifecycle_run.py`). |
| R6 | **Recurrence (D-AW-3, OWN-1104).** A headroom-thread occurrence during the later window is recorded by CH-6b's `RECURRED_DURING_CHECK` (if CH-6b has not merged, the packet notes the occurrence is still skipped) and counts against the change. For this family "occurrence" is not a failure signal by itself; the R3 metric decides. The packet states this. |
| R7 | **Reads and UI.** `VerificationService.summary` returns `metrics[]` for any family. `cost_check` and `trial_hours` stay reserve-trial-only (null otherwise). The verification page renders `metrics[]` as one table: label, before, after, days, rule. That is a MOCK DEVIATION candidate (MD-CH9b-1) against the verification mock. CH-9's before/after text becomes this outcome's line, "Midday use before and after the change: {b} → {a} kWh a day on {n} fully checked days each", plus the outcome words. |
| R8 | **DD-1.** The `mill-midday` story day (CH-9 R7) must leave 3 COMPLETE days on each side within the baseline. DD-1 places it so, by day placement only, never by values. |

## 2. Pre-flight (batch the answers, then stop)

- **P1.** The full `midday-productive-shift-1` and `productive-load-midday@1` catalogue text (design §5b.1), quoted: is there a margin or target? (R3)
- **P2.** The `verification_plan` / `verification_outcome` columns (migration 0019+) and every place that assumes the reserve-trial shape (`verification.py`, `verification_rules.py`, `verification_read`, the frontend verification page). List them with `path:line`.
- **P3.** How the reserve trial is triggered (synchronous evaluate today; MD-0 P1), and the cleanest trigger for R5.
- **P4.** MG-4's measure and its `judge` inputs (CH-6a), for the R4 guardrail.

## 3. Tests

1. **L0:** R2 day choice (gaps, LOW days, fewer than 3); R3 pass/fail with the declared rule; R4 guardrail breach and non-COMPLETE guardrail day; the metric text.
2. **L2:** `pg_harness.fresh_database()` + `setup_cache`:
   - freeze at apply;
   - evaluate after 3 COMPLETE later days;
   - the lifecycle reaches RESOLVED_MONITORING;
   - `reserve-trial-1` outcomes byte-equal (R1);
   - 0047 upgrade and downgrade if added.
3. **L2m (Kobo MD-0):** if MD-0's Kobo story carries the mill Action, the outcome on the states day set. Otherwise an L2 fixture only, and the packet says so.
4. **Existing, scoped:** `test_s6_*verification*`, `test_out_e*`, `test_ch3_*`, `test_ch9_*`, `test_ch6a_*`, the verification-page vitest.
5. **Guards:** A, W, N, V, M, and the outcome-id ratchet.

## 4. DS-R1 and OL-1

| Item | Touched how | Resolution |
|---|---|---|
| `reserve-trial-1` as the only verification family (CH-9 §4 keep) | Replaced by the registry | **Fixed** |
| Before/after shown as "measured, not verified" (old CH-9 R6) | Replaced | **Fixed** (verified by plan) |

**OL-1:** MG-5 and MG-4 are read through `outcome_map` `CONTRIBUTIONS` (CH-6a), never as literals. The ratchet does not grow.

## 5. Size: 2.5 units

| Unit | Content |
|---|---|
| u1 (1) | R1 registry (+ 0047), R2 plan freeze, the byte-equality proof |
| u2 (1) | R3–R5 evaluator, guardrails, trigger, lifecycle L2 |
| u3 (0.5) | R7 reads and the verification page |

## 6. Review focus

- The pass rule is the catalogue's or the owner's, never fitted.
- Days are chosen by grade, not value.
- Guardrails can fail the change.
- Reserve-trial outcomes are unchanged.

## Revision CH9-R3 (Architect 9, Claude, 2026-11-05)

**Size goes from 2.5 to 4.5 units.** A new first part **R0, "Actions from an opportunity" (2 units)**, comes before R1. Its full text is in `.agent/build-sheet-CH-9.md` §11.
- **Migration:** an exactly-one-of Finding or opportunity origin on `action` and `chain_action_thread`, with the trigger updated.
- **Port:** one `link_action(kind, action_id, origin)`.
- **Readers:** a listed reader audit, plus a guard test against new unlisted readers.
- **L2 proofs:**
  - Finding-origin bodies are byte-equal before and after;
  - CH-4 R6 runs with a linked Action;
  - the mill Action goes ACTION_ACCEPTED → ACTION_APPLIED on the headroom thread. This proof moves here from CH-9 u5.

**Pre-flight adds:**
- the migration number (after 0046);
- the study revision table for `origin_opportunity_revision_id`;
- the full reader list.

Split at R0 / R1 only if the pre-flight measures more than 6 units.

## Build units (split 2026-11-05)

- Architect: Claude (Architect 13), 2026-11-05, under the owner's efficiency rule (`.ai/ROLE_CONFIG.md` "Token Efficiency", demo-sprint additions). Plan row **SPLIT-1**. No ruling above changes. **Total unchanged: 4.5** (2 + 1 + 1.5).
- **Common rules** as in `build-sheet-CH-5b.md` "Build units".
- **Pre-flight P1 moves to CH-9b1.** P1 (is there a margin in the `midday-productive-shift-1` catalogue entry?) is a design-text read with a possible owner OD stop (R3). Asking it in the first unit gives the owner the whole of CH-9b1 and CH-9b2 to answer, so CH-9b3 never waits on it.
- **Only CH-9b3 needs CH-6a on main** (R4 guardrails use the CH-6a `kpi` records and `judge`). CH-9b1 and CH-9b2 do not, so they start straight after CH-5b1 on lane 2.

| Unit | Size | Scope | Depends on | Review |
|---|---|---|---|---|
| **CH-9b1** Actions from an opportunity (R0) | 2 | Revision CH9-R3 and `build-sheet-CH-9.md` §11 Q1 "The contract change" | CH-9 merged | Own review (contract migration and reader audit) |
| **CH-9b2** family registry and plan freeze | 1 | old u1: R1, R2, P2, P3 | CH-9b1 merged | **Batched with CH-6b0** (lane 2; both small, both on the verification/lifecycle path) |
| **CH-9b3** evaluator, guardrails, trigger, reads and page | 1.5 | old u2 + u3: R3–R7, P4 | CH-9b2 and **CH-6a3** merged; CH-6b0 merged (else R6 fallback) | Own review |

**CH-9b1 (2).**
- **Reading budget:** this sheet's header, §0, the Revision CH9-R3; `.agent/build-sheet-CH-9.md` §11, the Q1 block only (`:173-200`); design §5b.1, the `productive-load-midday@1` lever and `verification_plans.midday-productive-shift-1` entry only (for P1). Code: `0016_action_store.py:50-80`, `0042_chain_threads.py:75-110`, `postgres_thread_store.py:40-60`, `lifecycle_run.py` (grep the ACTION_* mapping), and the reader list from `grep -rn "origin_finding_id\|origin_finding_revision_id" backend/assetops_backend`.
- **Pre-flight:** the migration number (next free head after CH-5c2's 0048; whichever merges second re-points); the study revision table for `origin_opportunity_revision_id`; the full reader list with `path:line`; and **P1** quoted.
- **Acceptance:** the migration upgrades and downgrades on `pg_harness.fresh_database()`; exactly one origin pair per row (CHECK tested both ways); `link_action` with a Finding origin is byte-unchanged; the reader-audit guard test fails on an unlisted new reader; L2: Finding-origin board, Actions-list, thread and verification bodies byte-equal before and after; CH-4 R6 with a linked Action (the opportunity is not withdrawn); the mill Action ACTION_ACCEPTED → ACTION_APPLIED at L0 and L2; scoped `test_ch2_*`, `test_ch3_*`, `test_ch4_*`, `test_ch9_*`, `test_s6_*verification*`; guards A, W, N, V, M and the outcome-id ratchet.

**CH-9b2 (1).**
- **Reading budget:** this sheet §1 R1, R2; §2 P2, P3; §3 item 2 bullets 1 and 4–5. Code: `B/actions/verification.py`, `B/actions/verification_rules.py` (the dispatch and freeze paths, by grep), `0019_verification_core.py`, the snapshot reader for `productive_kwh` (grep `SnapshotReader`).
- **Acceptance:** L0 R2 day choice (gaps, LOW days, fewer than 3 days, the 14-day look-ahead, grade-only choice); L2 freeze at apply; `reserve-trial-1` outcomes byte-equal before and after the registry; the family column migration (if P2 needs it) upgrades and downgrades; scoped `test_s6_*verification*`, `test_out_e*`; guards A, W, N, V, M.

**CH-9b3 (1.5).**
- **Reading budget:** this sheet §1 R3–R7; §2 P4; §3 items 1 (R3, R4, metric text), 2 bullets 2–3, 3, 4, 5; §6. The CH-9b1 P1 answer and any owner OD. Code: the CH-6a `kpi` records for MG-5 and MG-4 (`records_for` / `kpi_record`, grep), `judge` in `B/outcomes/objectives.py`, the CH-1b `snapshots` consumer (grep), `VerificationService.summary`, the frontend verification page (grep `cost_check`).
- **Acceptance:** L0 pass/fail with the declared rule; guardrail breach → NOT_VERIFIED `GUARDRAIL_<KPI>`; a non-COMPLETE guardrail day → NOT_JUDGED; the R7 line text; L2 evaluate after 3 COMPLETE later days → stored outcome and RESOLVED_MONITORING through the existing lifecycle; L2m on MD-0 if the Kobo story carries the mill Action, else L2 only (packet says which); R6 stated in the packet (with CH-6b0 merged, the during-check occurrence is recorded); the `metrics[]` table rendered (vitest), MD-CH9b-1 labelled; scoped `test_s6_*verification*`, `test_out_e*`, `test_ch3_*`, `test_ch9_*`, `test_ch6_*`; guards A, W, N, V, M and the outcome-id ratchet.
