# POLISH PA-2b - Plan due state and asset labels (Lane A, about 3.5 units)

Status: in_review

USER_REVIEW_REQUIRED: no (merges on review ACCEPT; walkthroughs deferred to the owner walkthrough after this round).

Contract: `.agent/build-sheet-POLISH.md` §1.4 (backend), §3 "Asset labels", §5 Lane A PA-2, §7 (R640 asset part, R641),
Addendum 3 (captures) and Addendum 6 (Q2, Q4). Branch `task/POLISH-PA-2b-plan-due-assets` from main `816448bec`.

## Acceptance

1. `outcomes/plan_due.py` `plan_due_state(trigger_kind, next_due_at, to)` with a 14-day horizon: only CALENDAR plans
   with a due instant are assessed; `due == to` is not overdue. `warnings._plans` and `visits.py` call it, and the
   existing warning tests pass unchanged.
2. `GET /api/work/preventive` adds a top-level `summary: {overdue_count, due_soon_count, not_assessed_count}` over
   the whole selection before paging, and a per-row `due_state`, at the request `to`. `state_counts` stays null.
   Other roots are unchanged. Frontend validator: change only if it rejects the keys.
3. Work `asset_label` is rewritten in place to the plain word (GENERATOR is "Backup generator" on COLDCHAIN Sites,
   "Generator" elsewhere). `asset_code` is appended only when the Site has more than one non-retired asset of the
   type. Unmapped types use the capitalised type word. A wire `asset_type` is added. `cold.py` and `visits.py` read the
   fields and do not parse the label. The frontend parsers are untouched (PB-3).
4. Read-level tests pin the exact output: pure tests, plus a Postgres preventive read across pages.
5. Captures: deferred to PA-3 (Addendum 3). Register: R641, and the R640 asset-word part. Guards: check-all.
