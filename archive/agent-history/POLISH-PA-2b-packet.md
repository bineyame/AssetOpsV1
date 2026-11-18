# POLISH PA-2b review packet: plan due state and asset labels

Task: `tasks/POLISH-PA-2b-plan-due-assets.md`. Branch `task/POLISH-PA-2b-plan-due-assets` from main `816448bec`.
Contract: `.agent/build-sheet-POLISH.md` §1.4 (backend), §3 asset labels, §5 PA-2, §7 R640/R641, Addendum 3 and
Addendum 6 (Q2, Q4). USER_REVIEW_REQUIRED: no (merge on review ACCEPT).
Captures: deferred to PA-3 (Addendum 3). The read-level tests below are the screen proof until then.

## Outcome delivered

| Item | Change |
|---|---|
| Plan due rule (§1.4) | New `outcomes/plan_due.py` `plan_due_state(trigger_kind, next_due_at, to)`. Only CALENDAR with a due instant is assessed: `< to` OVERDUE, `< to + 14 d` DUE_SOON, else NOT_DUE; anything else NOT_ASSESSED. `soon_until(to)` builds the horizon without importing `datetime` (`test_out_a1_outcome_map` keeps `outcomes/` import-pure). `warnings._plans` and `_overdue` call it, and `visits.warning_facts` filters cues with it (`soon_until=soon_until(to)`). The existing warning tests pass unchanged (`test_out_c_rules`, `test_out_c1_never_money`). |
| Preventive read (Q2) | `work/global_index.py`: each preventive row gets `due_state` at the request `to`. On the preventive root only, the envelope gets `summary` counted over the full selection before paging, so every page carries the same counts. `state_counts` stays null. Incidents, maintenance and operational records are unchanged (no `summary`). Frontend validator: not changed, because `isEnvelope`/`isRow` check named keys only and accept extra keys. |
| Asset labels (Q4) | New `outcomes/asset_words.py` (`asset_word`, `asset_label`). `work/site_index.asset_fields(row, site_type)` gives `(asset_label, asset_type)` for W4 site rows, global incident/maintenance rows and preventive plans. `_ELIGIBLE` (W4 work read) and `_PLANS` (global read) add `asset_type_count` (non-retired assets of the same type at the Site, scalar subquery); `_ELIGIBLE` also adds `site_type`. Preventive plans use the Site row's `site_type`. `asset_type` joins the preventive plan basis next to `asset_label`; case bases did not hold `asset_label` and are unchanged. |
| Consumers | `site_outcomes/cold.py` matches Protect plans by the wire `asset_type` (`PLAN_TYPE_TOKENS`); its label parser `_asset_type` was removed. `site_outcomes/visits.asset_name` uses the plain label as it is, so the repeat warning reads "Backup generator visited 3 times in 60 days (…)". |

## Wire shape for PB-3

`GET /api/work/preventive` (schema `global-work-index-1`, unchanged version):

```json
{
  "schema_version": "global-work-index-1", "scope": {}, "window": {}, "known_at": "…", "status": "…",
  "coverage": {}, "total_count": 5, "state_counts": null,
  "summary": {"overdue_count": 2, "due_soon_count": 1, "not_assessed_count": 2},
  "rows": [{"…existing keys…": "…",
            "trigger_kind": "CALENDAR", "next_due_at": "2026-10-25T00:00:00Z", "next_due_hours": null,
            "due_state": "OVERDUE",
            "asset_id": "…", "asset_label": "Backup generator", "asset_type": "GENERATOR"}],
  "next_cursor": null, "selection_token": "…"
}
```

- `due_state` is one of `"OVERDUE" | "DUE_SOON" | "NOT_DUE" | "NOT_ASSESSED"`. The counts cover OVERDUE, DUE_SOON
  and NOT_ASSESSED; NOT_DUE is not counted. The cut-offs are `window.to` and `window.to` + 14 days, so the card notes
  use `day(to)` and `day(to + 14 d)`.
- `asset_label` is `string | null`: "Backup generator" (GENERATOR on COLDCHAIN), "Generator" (GENERATOR on MINIGRID or
  EV_CHARGING), "Compressor", "Battery", "Connector" (CONNECTOR or EV_CONNECTOR), "Charger" (EV_CHARGER), or the
  capitalised type word ("Power conversion system"). When the Site has more than one non-retired asset of that type it
  is "{word} {asset_code}", for example "Connector c2".
- `asset_type` is `string | null`: the stored type, for example `"GENERATOR"`, `"EV_CONNECTOR"`. Null exactly when
  `asset_label` is null.
- The same `asset_label`/`asset_type` pair is on `GET /api/work/incidents` and `/api/work/maintenance` rows, and on the
  W4 Site work index rows (`/api/sites/{code}/work/...`). Those roots have no `summary` or `due_state`.
- The old composite form `"{asset_code} · {ASSET_TYPE}"` is gone everywhere. The frontend `assetLabelWords` and
  `coldAssetLabel` see no " · " and show the plain label unchanged until PB-3 replaces them with `asset_type`/`assetWords`.

## Files materially changed

- Backend: `outcomes/plan_due.py` (new), `outcomes/asset_words.py` (new), `outcomes/warnings.py`,
  `site_outcomes/{visits,cold}.py`, `work/{site_index,global_index}.py`,
  `work/adapters/postgres_{work_read,global_read}.py`.
- Tests: new `backend/tests/test_polish_pa2b_plan_due_assets.py` (9 pure tests); new
  `test_w601b_global_maintenance.py::test_preventive_due_summary_over_all_pages` (Postgres read across pages);
  key-set and asset-label pins in `test_w601b`, `test_w601a`, `test_w401_site_indexes_postgres`; fake rows moved to
  the new wire shape in `test_out_b2_mini`, `test_out_b3_cold_ev`, `test_out_c2_board`, `test_out_c3_cold_cost`.
- PA-2a leftovers (6-digit code pins missed in PA-2a, failing on main): `test_w601c_request_detail.py:653` and
  `test_w601e_operational_index.py:325,329,352` now expect `display_code(...)`.
- Records: task file, `.agent/mock-departure-register.md` (R641 added; R640 asset part filled), `.ai/CODE_STATE.md`.

## Acceptance criteria

1. Shared due rule, warnings unchanged: **met** (`test_due_boundaries` covers `due == to` and the 14-day edge;
   `test_not_assessed_cases` covers hours of use; `test_board_warnings_use_the_helper_with_unchanged_behaviour`;
   `test_out_c_rules` and `test_out_c1_never_money` are unchanged and pass).
2. Preventive `summary` and `due_state`; `state_counts` null; other roots unchanged: **met**
   (`test_preventive_due_summary_over_all_pages`: limit 2 over 5 plans, three pages, each `summary ==
   {2, 1, 2}`, exact `due_state` per title; the default window gives `{0, 3, 2}`; no `summary` on maintenance or
   incidents). Frontend: no change needed.
3. Plain `asset_label` in place, wire `asset_type`, code appended only when ambiguous, consumers read the fields:
   **met** (`test_asset_words_by_type_and_site`, `test_asset_label_appends_the_code_only_when_ambiguous`,
   `test_work_rows_carry_label_and_type`, `test_repeat_warning_names_the_plain_asset`; Postgres `test_plan_asset_label`
   computes the expected label from the stored type, the Site type and the same-type count; cold Protect plan
   matching passes in `test_out_b3_cold_ev`/`test_out_c3_cold_cost`).
4. Read-level tests: **met** (above).
5. Captures deferred; R641 and R640; guards: **met** (see Checks).

## Checks run

- PYTHONPATH pointed at this worktree (`AssetOpsV1-polA2b`) for every direct run; the host wrapper sets it itself.
- Every backend test file without a DB, at `f400b179f`: before the fake-row updates, 6 failures, of which 3 were
  Postgres modules with no URL and 3 were fake rows in the old shape. After the updates the affected unit files pass
  (`test_out_b2_mini`, `test_out_c2_board`: 46 passed; `test_out_b3_cold_ev`, `test_out_c3_cold_cost`, PA-2b pure,
  `test_out_c_rules`, `test_out_a1_outcome_map`: 58 passed).
- Host wrapper, Postgres, `-n 4`: `test_w601a/b/c/e`, `test_w401_site_indexes_postgres`,
  `test_out_c3_repeat_visits_postgres`, `test_out_c4_ev_warnings_postgres`, `test_out_b4_board_postgres` and the PA-2b
  pure file: 84 passed, 3 failed (5.9 min).
  - `test_w601c` `:653` and `test_w601e` `:325`: PA-2a's 6-digit pins, fixed in `ed1939238`. Rerun of both files:
    30 passed.
  - `test_out_b4_board_postgres::test_kobo_guardrail_two_board_days` gave `SITE_NOT_FOUND` "No Site KOBO-001 is
    configured" under `-n 4` and passed alone (1 passed). It is order- or parallel-dependent, not this slice. It
    passed in PA-2a's scoped run.
- `tools\check-all.ps1 -Python …plan2\.venv\Scripts\python.exe` at `ed1939238`: All 12 guards passed. `tools\check-agent-workflow.ps1` was rerun after the records commit: passed.
- Not run: the full suites.

## Known deviations

- **Extra asset words.** The §3 map names COMPRESSOR, BATTERY, GENERATOR and CONNECTOR. The EV foundation stores
  connectors as `EV_CONNECTOR` and chargers as `EV_CHARGER`, so those map to "Connector" and "Charger" rather than the
  fallback "Ev connector"/"Ev charger". Builder latitude, listed for review.
- **Retired assets.** "Non-retired" means `retired_at IS NULL`. If the row's own asset is retired, the count can be 0
  and the label is the bare word.
- **Shared files.** `work/site_index.py` also serves the W4 Site work index, so Site work rows gain `asset_type` and the
  plain label too, as Addendum 6 Q4 intends ("Rewrite `asset_label` in place").
- **Untouched.** `global_detail` `work_asset` (raw `{asset_code, asset_type}` on the request detail) was not in Q4 and is
  unchanged.
- **PA-2a leftovers.** Two Postgres test files on main still pinned 6-digit labels (`test_w601c`, `test_w601e`). They
  are fixed here because they fail on main.

## Residual risk

- Two scalar subqueries per work row. They use the `asset_site_type` index; the row counts are small.
- The PA-3 rebuild captures (`maintenance-preventive`, `wr-overview`, `portfolio-week`) are where the plain labels and
  the "Backup generator visited …" warning are first seen on screen.

## Review focus

The `due == to` boundary, counts before paging, the plan basis gaining `asset_type`, the PB-3 wire shape above, and
the extra EV words.
