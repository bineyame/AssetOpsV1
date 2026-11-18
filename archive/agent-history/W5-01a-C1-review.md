# W5-01a C1 per-unit review — Cooling part only

Reviewer: independent Claude reviewer, 2026-10-22. Branch `task/W5-01a-cold-selected-depth`, head `4400491c`, code commit `703807cf`, diff `git merge-base main HEAD` (`68b88dae`)..`703807cf`. Scope: `GET /cold/cooling`, the extracted gate, `main.py` mount and the two C1 test files. The Health read (`/cold/health`, `test_health_not_configured`) is held for an Architect ruling and is not reviewed as missing.

## Verdict: ACCEPT (Cooling part)

No High or Medium findings. The four Lows below are non-blocking and can be folded into the follow-up C1 Health run. C1 as a whole cannot close until Health lands, because `links.health` currently points at a route that does not exist yet (see I1).

## Checks run (by me, on `4400491c`)

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- I created the private DB `assetops_w501c1rv_test` on 127.0.0.1:55432 and ran `pytest tests/test_w501_cold_depth_router.py tests/test_w501_cold_depth_postgres.py tests/test_w204_cold_reads.py tests/test_w203_cold_reads_postgres.py tests/test_w202_cold_replay_postgres.py -q`: **51 passed**, 0 failed, 0 skipped, 426 s. Afterwards I dropped every `assetops_w501c1rv%` database (0 remain).
- No frontend was touched, so I ran no tsc, npm or layout evidence. Layout evidence does not apply to this backend unit.
- I did not run `check-all.ps1` or the full backend suite. The builder reports 11/11 guards passing on the same build commit.

## What was verified against the card

- **Gate extraction (`cold_site_api.py`).** The `opened` body moved verbatim into `build_cold_gate`, and `served` moved into `cold_served`. Refusal order, codes, statuses and messages are byte-identical. `build_cold_site_router` uses both. The W2-04 tests (`test_w204_cold_reads.py`) and the W3-02 link tests share them, and they pass. Existing routes show no behaviour change.
- **Route.** `/api/sites/{site_code}/cold/cooling` takes `WINDOW_KEYS` only. `cursor` and `limit` give 422 `COLD_PARAMETER_UNKNOWN`. There is no 409. All nine shared refusal codes and statuses are exercised in `test_cold_depth_gate_and_links`.
- **Snapshot and clocks.** One `ColdReadService.within` connection serves `selection_on`, `envelope_on` and `accepted_on`. Omitting `known_at` gives `known_at == committed_watermark`, which is wall-clock `decided_at` and is asserted against `max(ingestion_disposition.decided_at)`. A future `known_at` gives 422 `COLD_TIME_INVALID`, the same check as W2-04 `_selected`. The historical read passes the `before["window"]["known_at"]` saved before `advance_late()`. The PENDING, LEASED and FAILED job states each give `PENDING_RECOMPUTE`. The final cutoff is CURRENT and its cited set is a strict superset of the first. The stale-probe window gives `STALE_SOURCE`, and the empty window gives `UNKNOWN`.
- **Scope.** A wrong Site code gives 404. A foreign tenant yields an empty selection. A disclosure refusal gives 403, and a down store gives 503.
- **Provenance.** `envelope_on(...)["source_provenance"]` is used with revision-ID selection. No evidence ID is passed to `public_provenance` as a revision token.
- **Derivation table.** The mapping LIMITED/CONTRADICTORY/UNAVAILABLE-or-no-START maps to LIMITED/CONTRADICTORY/UNKNOWN. Restart, return and both durations are null, and `comparison_state=CONTEXT_MISSING` holds on all six W2 cases. Points come only from OBSERVED `COMPRESSOR`/`PROBE` first steps whose IDs are accepted. The context rows are the five literal labels in order. Ambient, Loading and Defrost are always Unknown. Power is Observed only from an accepted selected `grid_power_event`. Door is Observed only from an accepted OPEN/CLOSE pair with positive elapsed time, read from the Site-scoped ledger on the same connection. The backup-failed producer gives door Observed at 60 s.
- **Links.** The keys are `temperature`, `backup` (which maps to `/cold/backup-chain`), `evidence` and `health`. They are built from the URL-quoted Site code, never the UUID, and they preserve `from`, `to` and `known_at`.
- **Would the tests fail on the old code?** Yes. Both test files import modules and symbols that do not exist on `main` (`cold_depth`, `cold_depth_api`, `build_cold_gate`). Beyond that, the assertions would catch each regression the card names: a filled restart or duration, a missing door pair, a non-accepted point, a wrong state per cutoff, and a changed refusal code.

## Findings

- **L1 (Low, correctness edge).** `backend/assetops_backend/analytics/cold_depth.py:53,59`, `door_pairs`. The docstring says each OPEN pairs with "the next CLOSE strictly later than it". The code instead clears `opened` on any CLOSE, including one with zero elapsed time. So the sequence OPEN 19:10, CLOSE 19:10, CLOSE 19:11 yields Unknown, although the docstring and the card's "matched pair with positive elapsed time" read as Observed at 60 s. A same-instant OPEN/CLOSE is also ordered by UUID, so the result depends on the ID. **Fix:** skip a non-positive CLOSE without resetting `opened`, or change the docstring to match the code. Either way, add that case to `test_door_pairs`. The W2 producers do not reach this case.
- **L2 (Low, weak test).** `backend/tests/test_w501_cold_depth_postgres.py:133` asserts `state in STATES` for the positive backup-failed replay. This passes for any state, including UNKNOWN. **Fix:** assert the exact expected state, presumably `CURRENT`.
- **L3 (Low, test coverage).** The card lists "missing selected ID" among the cases the tests must prove. It is proved only in memory (`test_w501_cold_depth_router.py:178`), where `envelope_on` is stubbed to `REGISTERED_SIMULATION`. That shows the point is dropped. It does not show that the real envelope classifies a selection with a missing ID as `UNKNOWN` ("empty/broken/foreign is UNKNOWN"). It is also not exercised on Postgres. **Fix:** add a Postgres case that deletes or invents one cited `accepted_evidence` ID, then assert the point is dropped and `source_provenance.classification == "UNKNOWN"`. The other option is to state in the spec that the W2-03 envelope tests already cover the provenance half.
- **L4 (Low, coupling; preference).** `cold_depth.py:119` constructs `ColdSiteReadService(self._reads, None)` and calls its private `_capabilities`. This computes all six capabilities, which costs extra `basis_revisions_on` and observed-role queries, only to read `COOLING_RESPONSE`. It is correct today on the same connection, but a change to the W2-04 private method can silently change Cooling. **Suggestion:** expose a small public `cooling_response_on(c, snap)` in `cold_site_reads` (Lane A shared file, so an Architect call), or accept the coupling as it stands.
- **I1 (Info).** `links.health` is `/api/sites/{code}/cold/health`, which returns 404 until the held Health read is built. This is expected inside C1, but C1 must not be handed to C2 with Health unbuilt.
- **I2 (Info).** `test_w501_cold_depth_postgres.py:264`: the `"36" not in json.dumps([nulls])` assertion is vacuous because the nulls are already asserted. It is harmless.

## Builder's six shape choices: decided by spec or Architect ruling?

1. **Page payload key `cooling`.** Spec line 17 says only "page payload and `links`" and names no key. **Needs an Architect ruling.** Confirming `cooling` is trivial, and Health would follow with `health`.
2. **Context row keys `label/state/evidence_ids/duration_seconds`, with state `Observed`/`Unknown`.** The labels, their order and the `Observed`/`Unknown` values are decided by line 53 (the derivation table) and the ledger "Context normalization" row. The **key names are not literal**, so they **need an Architect ruling**. That includes whether `duration_seconds` exists on every row or only on the door row.
3. **Several door pairs sum to one `duration_seconds`.** The spec is silent: line 53 speaks of "a matched ... pair" and the producer has one pair. **Needs an Architect ruling**, choosing between a sum, the first pair, the longest pair, or one row per pair.
4. **A point is dropped when its step ID is not an accepted ledger record.** **Decided by the spec.** Line 19 says "selected *accepted* compressor/probe points and IDs", and line 53 says points come from the selected start chain's steps, "No unselected ... row may fill them". Dropping the point is the only reading consistent with "accepted". L3 still applies to the test proof.
5. **`accepted_evidence_ids` is the union of the selected revisions' stored `evidence_ids`.** **Decided by the spec.** Line 17 says "Exact accepted IDs are deduplicated cited IDs from the selected W2-03 assessment, episode/Finding and W2-04 read, never a page or cursor subset". This matches the merged W2 `_pinned_ids`. Note the consequence: the field can list a cited ID that is absent from the ledger, as the in-memory test asserts with `COMPRESSOR_MISSING`. **Architect to confirm** that "cited" rather than "ledger-present" is intended, given the field name. I raise this as a confirmation, not a defect.
6. **"`cooling_recovery.state`" read as the W2 `COOLING_RESPONSE` capability.** No field named `cooling_recovery` exists in code. The W2-04 overview `cooling.state` is exactly the `COOLING_RESPONSE` capability (`cold_site_reads.py:363-369`), with the identical LIMITED/CONTRADICTORY/UNAVAILABLE set and UNAVAILABLE when nothing is selected. Line 53 effectively decides this by its value set and its "no selected assessment" clause, and the builder's reading is the only one that fits. **The Architect should correct the spec wording** so it names `COOLING_RESPONSE`. A one-line amendment is enough, and no code change is expected.

## Items needing an Architect ruling

- R1: the page payload key (`cooling`) (choice 1).
- R2: the context row key names, and whether `duration_seconds` appears on every row (choice 2).
- R3: how several matched door pairs are reported (choice 3).
- R4: confirm that `accepted_evidence_ids` means cited IDs even when one is absent from the ledger (choice 5).
- R5: amend the spec wording from `cooling_recovery.state` to the `COOLING_RESPONSE` capability (choice 6).
- R6 (optional, from L4): whether to add a public `cooling_response_on` to `cold_site_reads`.
- Held, not reviewed here: the builder's Health questions (source read, per-row asset, edge cases, payload keys).
