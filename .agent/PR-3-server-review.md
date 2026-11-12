# PR-3 server half: independent review (Claude reviewer, 2026-11-12)

Branch `task/PR-3-price-entry` head `99d4b6f24`, diff `946a02661...HEAD` (PR-1 already on main, so excluded).
Read-only; no Postgres, no parity. Spec: rev 5 §5.1-5.4, D-PRICE.1, owner defaults 2026-11-12, `PR-3-packet.md`.

**Verdict: ACCEPT WITH NOTES** (no High or Medium findings; the Lows do not block the server half).

## Findings

- **Low L1 - replay is only recognised against the series head** (`backend/assetops_backend/financials/price_entry.py:183`).
  If any other price on the same key is saved between a save and its retry, the retry re-derives against the new
  head, the digest differs and the store returns 409 `IDEMPOTENCY_KEY_REUSED` ("nothing was written") although the
  first save did persist. That contradicts the honest-state copy "Saving again is safe" / "Nothing was saved." Rare
  with one site admin; fix would be to look the key up across the series (the store already queries by
  idempotency key) rather than only the head. The 571d3e101 fix is otherwise correct: same body replays 200 with
  one row (unit `test_a_retry_of_the_head_save_rederives_that_save`, packet Postgres flow), a changed body is the
  store's 409.
- **Low L2 - two rev 5 Postgres items deferred** (`backend/tests/test_pr3_price_entry_postgres.py`): productive-use
  INITIAL making the mill value priced and its `price_action` disappearing, and "a stored Financials response is not
  served after a save". The second is the only proof of the response-store watermark claim in §5.3. Both are packet
  resume point 3; they must land before PR-3 closes, not with the form only.
- **Low L3 - AR-4 path unexercised** (packet deviation 5). Statically the event matches: the 0044 trigger
  (`0044_chain_events.py:57-61`) is channel-agnostic, keyed by `assumption_key`, `valid = [min(valid_from), NULL]`
  for an open entry; AR-4 (`task/ANY-2-AR4` `ba227df16`) registers `price.revised@1 {days: valid_local, measures:
  by_assumption_key}` and `money.lines` reads `productive_use_price_per_kwh` (`estate/money_rows.py:10-12, 33`).
  Whichever merges second reruns the flow test (rev 5 contract line).
- **Low L4 - second store engine** (`backend/assetops_backend/main.py:651`): `build_assumption_store` opens its own
  pool beside `assumption_reads`. Disposed on shutdown; a memory note on this machine, not a defect.

## Checked and found correct

- Only `STORED_KEYS` enterable: unknown key -> `PRICE_ENTRY_INVALID` (step 6), `PRICE_NOUN` future keys ->
  `PRICE_KEY_NOT_ENTERABLE` (step 7), `price_entry.py:103,139`; `STORED_KEYS == ASSUMPTION_KEYS`.
- Refusal order 1-10 matches §5.3 (`financial_api.py:99-177`); extra 401 branch and scope-outage 503 are packet
  deviation 3. Nothing is written before `store.publish`; dry run never publishes.
- Human route `POST /financial-assumptions` byte-unchanged in the diff, still built with default
  `no_verified_principal`; `test_human_route_still_refused` and the unchanged `test_s4_assumption_publication` pass.
- `read_access` default refuses all (401); `main.py:658` passes `development_access` only to this router's
  `read_access` keyword, which only the new route reads. It equals the price read's own access
  (`financial_read_api.py:30` default, `main.py:667`), so no other route is widened. Writes still need the
  `ASSETOPS_OPERATIONAL_ENTRY` principal (residual risk as for the dip form: with the switch on, any caller may save).
- Attribution: `SET_BY = "Entered by site admin"` equals `OPERATOR_ENTRY_LABEL` (`OperationalRecords.tsx:89-90`);
  publisher actor is the imported `ENTRY_PRINCIPAL`, kind SYSTEM, no author; provenance literals as specified.
- Correction-with-reason: CORRECTION stores the reason as `correction_reason`; INITIAL/SUCCESSION keep it as
  `provenance.entry_note`, never `correction_reason` (store refuses that, `assumptions.py:160`). Change kind and
  Site-local midnight `valid_from` match the table; SUCCESSION/CORRECTION overlap conflicts pass through from
  `plan_assignments` unchanged. `expected_prior` = series head agrees with the store's `ORDER BY revision_no DESC`.
- Migration 0060: `down_revision 0059_site_period_read`; main at review time (`ef9903d8e`, moved past the base) still
  tops out at 0059, AR-4 too, and no other local branch carries a 0060. Guarded on the installed CHECK name;
  downgrade refuses while a `SITE_ADMIN_ENTRY` row exists. Actor CHECK untouched.

## Not ruled (with the Architect)

Q1 (Site code vs display name in the INITIAL summary) and Q2 / deviation 1 (dry run reports `reason_required`
instead of refusing): noted only.

## Checks run by the reviewer

- No-DB pytest, worktree PYTHONPATH (`backend;backend\tests;contracts;simulator;gateway;field;host;tools`), plan2
  venv: `test_pr3_price_entry.py test_s4_assumption_publication.py test_s4_assumption_read_api.py` -> **139 passed**,
  0 failed, 22.7 s.
- GUARDS_PLACEHOLDER
- Not verified by me: the Postgres flow (2 passed per packet on `51da89871`), check-all 19/19, full backend suite
  (not run, demo-sprint policy). No frontend in this half; layout evidence not applicable.
