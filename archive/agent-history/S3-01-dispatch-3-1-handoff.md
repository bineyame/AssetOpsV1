# S3-01 dispatch-3.1 handoff (complete; phase 3b UI is next after the fresh Claude review)

Branch `task/S3-01-dispatch-assessment`. The dispatch-3.1 commits start at `05f9b4d`. Ruling: `D-2026-10-11-s3-phase-3a-version-and-cutover` (`.agent/architect-S3-answers-3.md`). Packet: the "dispatch-3.1" section in `.agent/S3-01-phase-3a-review-packet.md`. Questions: `.agent/S3-01-questions-4.md` (Q14-Q16, with fail-closed defaults). Status stays `active`. The phase-3a handoff `.agent/S3-01-phase-3a-handoff.md` still holds the 3b anchors (client calls, `DispatchView`, fixture days).

## What landed

- `analytics/dispatch_v3.py`: `MODEL_VERSION = "dispatch-3.1"`. It covers Q9 (the multi-epoch default is AMBIGUOUS) and Q13 (`INTERVAL_LIMITED` is lifted into the window). The version is in every `input_sha256` and `basis_sha256`, so the bump appends new revisions under the same keys.
- Reassessment needed no new code. `DispatchAssessmentWorker.reconcile` already enqueues any head whose `model_version` differs from the current one. `run_pending()` (CLI `assess_dispatch process-jobs`) reassesses those windows. Explicit selections are not remapped.
- `dispatch_read.py`:
  - `run` and `revision` carry `model_note`. It is `null` for the current model; for any other model it reads "OLDER_RULE_RESULT: produced by dispatch-3; the current model is dispatch-3.1 ...".
  - The window `calendar` names the model.
  - A dispatch-3 head reads `STALE_PROJECTION`, with `MODEL_VERSION_CHANGED` and `INPUT_BASIS_CHANGED`.
- `postgres_assessment_store.py`:
  - `lineage_breaks(..., model_version)` adds `selected_heads_other_model`.
  - `accepted_evidence(...)` maps a message ID to an evidence ID. It replaces `accepted_message_ids`.
  - `selected_intervals(..., domain, bracket)` adds `window_jobs`.
- `performance_comparison.py` (schema `s3-performance-comparison-v2`, which records `model_version`):
  - **Classes:**
    - `STALE_MODEL` and `STALE_PROJECTION` (a PENDING, LEASED or FAILED job) are `UNPROVEN`.
    - `MATCH` and `INTENTIONAL_DELTA` need the cited records inside the selected interval's evidence.
    - `INTENTIONAL_DELTA` applies only through `DOCUMENTED_DELTAS` (`CAPABILITY_CHANNELS_REQUIRED`, rows 5a/5b). It needs the interval's own limitation.
    - `MISSING_SOURCE` closes the gate, as `EXCEPTIONS`.
  - **Gate refusals:** a report made under another model version; any window still selected under another model.
- Decision table `backend/tests/dispatch_3_decision_table.md` gains "Model versions" and "Comparison" sections.

## Phase 3b UI must show (from the ruling)

1. The selected model version and revision. A pinned `dispatch-3` run or revision is labelled with its `model_note` (an older rule result), never as current.
2. Window status and every reason. These include `MODEL_VERSION_CHANGED`, `RECOMPUTE_OUTSTANDING` (Q12: the prior result is kept visibly stale, with the job state and reason) and `FAILED`, with the prior revision still open to inspection.
3. Ambiguity (`AMBIGUOUS_COHORT`) and the named window limitations, including `INTERVAL_LIMITED: interval from ...`, with their spans.
4. Comparison and gate state from `/performance/dispatch/cutover`.
   - Show the outcome, the statement and the counts.
   - Show `MISSING_SOURCE` exceptions with the missing message IDs and the closed gate. Route these to remediation or to a separate migration decision; never call them parity.
   - Show an `INTENTIONAL_DELTA` only with its `rule`, `rule_change`, `interval_limitations` and `compared_evidence_ids`.
   - Show an explicit unproven or closed state.
5. The empty-set caveat. KOBO-001's comparison is a zero-inventory statement, not claim parity. The walkthrough must not call it parity.
6. No fuel, money or saving implication. Fixture provenance and the demo annotations stay separate.
7. The walkthrough covers Necessary (10-09), bounded Candidate (10-02) and Indeterminate (10-03 or 10-01). It also covers the stale and failed states, pinned history, and the desktop/narrow mock comparison.

## Open risks

- `GET .../performance/dispatch/cutover` returns only `{site_code, read: POSTGRES_DISPATCH_3_1|CLOSED, permitted, reason}`. It does not expose the report's counts, claims, missing IDs, deltas or `model_version`. Phase 3b must add a report summary (the newest report from `build_performance_comparison_reports().latest`) to that route or a sibling route before the UI can show item 4.
- Q14-Q16 are open, with fail-closed defaults.
