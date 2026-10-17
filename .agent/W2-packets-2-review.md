# W2-02 / W2-03 packet review (plan) - 2026-10-17

Reviewer: fresh Claude, independent of the Planner. Reviewed at `b531d9d6` (planning head). Read-only and no suites run.
Sources: `.agent/W2-technical-design-cold.md` sections 2 and 4-7, `.agent/architect-W2-design.md`, `.agent/architect-W1-fidelity.md`, `.agent/W2-00-review.md`.

## Verdicts
- **W2-02: ACCEPT.** No High or Medium findings.
- **W2-03: RETURN.** One Medium finding (M1), a one-paragraph fix.

## Checks
- Registry checker: `Registry valid: 241 nodes, 11 linked pilot panels`, exit 0. The planning diff only adds `task` to A/I-cold-world (W2-02) and A-cold-excursion-rules, I-cold-assessment-store and D-cold-domain (W2-03). No status changed. The peer and adapter nodes stay unassigned, which matches the section 7 deferral.
- `v69-rendered-panels.json` matches the packet's counts and titles: temperature 3, coldbackup 4, cold-finding 3, cold-finding-excursion 3.
- Spot-checked code:
  - Rule-8 `$assessTables` / `$assessInserts` are at `tools/checks/configuration-persistence.ps1:645-647`, so "add before derivation" is correct.
  - `V4_CHANNEL_MAPPINGS` is at `contracts/.../source_envelope_v4.py:635`. The ledger lookup at `ledger.py:407` has no role, which confirms that W2-00 Low 2 is still open.
  - The conflict split in `ledger_reads.py:238-239` is real (W2-00 Low 1).
  - `finding.split_from_finding_id` already exists (`0009_finding_store.py:47`), so `split_from` needs no new column.
  - 0020 already refuses its downgrade on `recompute_job.domain='cold_chain'`.
  - `expectV69Panels` exists, so the W1-F1 guard is present.
- Physics check of the forcing table:
  - normal: about 0.47 C rise over 60 min, so it stays below 3.5 C.
  - excursion: T(19:15) is about 4.07 and T(19:20) about 4.16, consistent with the section 4 thresholds.
  - backup-failed: the door adds 0.0167 C.
  - missing-probe: 7 of 13 points.

## Coverage against the design
- W2-02:
  - Both phases cover section 4 in full: the closed registries for host, Lab and kernel, the thermal law and defaults, the guards, EVENT/IDENTITY, the six fixtures with the frozen window and seed, the closed tuple table, and the 3 s latency with half-even rounding.
  - They also cover the section 6 replay fields, the section 7 manifests, twice-replay idempotency, the late source time and the private-key scan.
  - W2-00 Low 1 is closed in Phase 2 and Low 2 in Phase 1. Low 3 needs no action.
  - The vendor peer is deferred in line with section 7.
  - Dependencies are stated: W2-00, W2-01, S2 and outbox.
- W2-03:
  - Section 2's 0022 delta is covered: scoped FKs, domain widening, `finding_revision.domain`, the composite FK and the guarded downgrade.
  - Section 5's rules are covered.
  - Section 6's four reads and panel map are covered.
  - Section 7's rule-8 writers and probes are covered.
  - The UI phase requires `expectV69Panels` for all four routes against `v69-rendered-panels.json`, in stocked and empty/refused states.
  - It also requires 1440/390 side-by-side captures, and a structure mismatch counts as High.
  - Dependencies are stated: W2-02, W2-01, W2-00, S4-05 and W1-F1.

## Findings
**M1 (Medium, acceptance gap) - `tasks/W2-03-cold-assessment.md:19`.**
- Problem: Phase 1 lists abstract case categories, but it never requires the six W2-02 manifests to produce their section 4 claims through S2 and assessment. `backup-failed` is not named at all.
- Why it matters: these six cases are the W2 demo story. A build could pass on hand-made fixtures while the real replays give different bounds or claims.
- Fix: add one assertion per manifest, run on its accepted replay:
  - normal: `NO_EXCURSION_OBSERVED`, and start and transfer observed.
  - excursion: exposure Finding, latest start 19:15, open episode, duration low 45 min and high null.
  - backup-failed: `OBSERVED_FAILURE`, the door is CONTEXT only, and the exposure Finding still holds.
  - missing-probe: coverage 7/13, temperature `UNKNOWN`, no exposure Finding, start failure still observed.
  - late-reading: 12/13 points and first highs at 19:15/19:25 at the 20:05 cutoff; at 20:10, a new revision with old history intact.
  - contradictory: `CONTRADICTORY`, never `OBSERVED_FAILURE`.

**L1 (Low) - `W2-03:19`.**
- Problem: the missing-transfer, clock-skew, SUSPECT, unbound-role and equal-event-ID cases have no source in the six replays.
- Fix: say that they are built through authenticated Batch V2 and S2 intake in tests, not by inserting rows directly into `accepted_evidence`.

**L2 (Low) - `W2-03:21`.**
- Problem: the section 6 common read contract is not tested explicitly. It covers the 31-day maximum, the `(time,id)` cursor with limit 50/200, the refusal codes 401/403/404/409/422/503, and a missing claim returning 200 `UNKNOWN`, not 404.
- Fix: add one test line.

**L3 (Low) - `W2-03:17`.**
- Problem: the section 5 split rule has no test. It splits only after two stable in-band points (excursion) or a new start request (backup).

**L4 (Low) - `W2-02:13`.**
- Problem: the section 4 probe-failure `UNAVAILABLE`/`SENSOR_FAILURE` reading is "if the profile publishes it". The packet neither says whether `cold-publication/1` publishes it nor tests it. None of the six scenarios exercises it.
- Fix: state "not published in /1", or add a unit test.

## Residual risk
- The design's code-line citations have drifted. For example, `kernel/execute.py:90-105` now points at imports. The Implementer should locate the registry seams by symbol, not by line.
- W2-01 is not merged yet, so W2-02 cannot start until it is.
