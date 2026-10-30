# OUT-B handoff (partial, 2026-10-30): resume inside B1 at `site_outcomes/board.py`

Branch `task/OUT-B-site-outcome-board`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outB`, head `8b2aaf1c`. It is cut from OUT-A head `7b826e97`, with no main merge yet; merge main in only when the coordinator says A has merged.

Contract: spec rev 3, `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md`.
- **"Pre-flight rulings B" (:672-737) wins** over older Slice B text.
- Slice B is at :741.
- §B.1 wire is at :763, §B.2 board rules at :844, §B.3 at :950, §B.4 at :984 and §B.5 at :1087.
- Pre-flight with all current anchors: `.agent/OUT-B-preflight.md`. Q-numbers there match the rulings table.

## Landed
- `cdc1618d`: `tasks/OUT-B-site-outcome-board.md` (in_progress), the `.ai/ACTIVE_CONTEXT.md` line 8 pointer, and the pre-flight.
- `8b2aaf1c`, B1 part 1:
  - `backend/assetops_backend/outcomes/status.py`: `Signal`, `outcome_state`, `roll_up`, `STATE_LABEL`, `STATE_TONE`, `PRECEDENCE`, and kind constants including the issue-only `EVIDENCE_GAP`.
  - `backend/tests/test_out_b1_status.py`: every rule with a negative control, every pairwise precedence, the lead tie-break, and the mock grid B column.
  - `test_out_b1_status.py` and `test_out_a1_outcome_map.py` together: 46 passed (the A1 purity test still passes).
- Deviation to note in the packet: `roll_up` takes `(outcome_key, state)` pairs in catalogue order, not `(state, reason)`. The spec's signature cannot return a lead key.
- `.venv` junction to `AssetOpsV1-plan2\.venv` is present (coordinator).

## Next
1. **B1 part 2: `backend/assetops_backend/site_outcomes/__init__.py` and `board.py`** (pure; it may import only `outcomes/`).
   - Inputs: `SiteFacts`, `FindingFact`, `ActionFact`, `CaseFact`, `PlanFact`, `Contributor` and `Option` (§B.2 :846-871).
   - `assemble(facts) -> rows` in canonical order, using `categories_for`/`outcome_roles` from `outcomes/outcome_map.py:73/:95` and `status.py`.
   - Issue ordering and the safeguard suffix (signals never get it, B-Q20).
   - In hand, per B-Q18: an open Action goes to In hand only. It moves to Earlier once it is applied and verification is not NO_PLAN. Domain Actions are in hand only.
   - The `earlier_result` table (:895-906), and the two empty texts, set only on measured rows (:908-910).
   - Must not harm per B-Q19 (:914-919): only with a mini Action verification, names from other categories, excluding NOT_MEASURED.
   - The evidence-link table (:930-936), the confidence chips (:940-948), and `headline_money` passthrough (B-Q14).
   - Not-measured rows: lists `[]`, `earlier_empty_text` null, `not_measured_text` from `catalogue.row_not_measured` (`catalogue.py:80`).
   - Tests: add the board cases to `backend/tests/test_out_b1_status.py` or a new `test_out_b1_board.py`. Both Earlier sentences (addendum 2), "Did not fix it" from a later request on the same asset (B.7 #4), and must-not-harm present and absent.
   - Then tell the coordinator B1 is ready for its per-unit review, and continue to B2.
2. B2 (mini composer, with a per-unit review), B3 (cold and EV), B4 (read/composition/route/main.py/estate summary/`EstateEvidenceService.site_readiness`/import test, per-unit review), then B5 and B6. Use the pre-flight answers for source keys. A spec that does not work means stop and ask.

## Rules carried
- **Heavy jobs need the coordinator's go first:** `measure-mock-panels` (B5, B-Q1 command), full vitest, `-Tier all`, captures.
- Test DBs `assetops_out_b_…_test` only. PID-only kills. No execution-policy override. `check-all.ps1` is safe to run directly.
- Focused pytest command: PowerShell, with PYTHONPATH from the task file, then `python -m pytest -q -p no:cacheprovider <file>` from `backend/`.
