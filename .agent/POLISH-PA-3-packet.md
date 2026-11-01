# POLISH PA-3 review packet: producers, links and rebuild

Task: `tasks/POLISH-PA-3-producers-rebuild.md`. Branch `task/POLISH-PA-3-producers-rebuild` from main `c4a39b1dc`.
Contract: `.agent/build-sheet-POLISH.md` §1.3, §3 (Lab names, narratives), §3.1 PA-3 rows, §4, §5 PA-3, §6, §7,
Addenda 3, 5 and 9. USER_REVIEW_REQUIRED: no (merge on review ACCEPT).

## Outcome delivered

| Item | Change |
|---|---|
| P-01/P-02 (§4, Addendum 9 Q3) | `tools/demo_combined.py` `story_links(story, days, kobo, web)` (pure) + `LINK_FORMS`; `links()`/`serve` print it. Cold/EV boards on the `days.json` event window; a day with null `start`/`end` links the whole calendar day, label "…, no event: whole day". No `/outcomes` or `/overview`. |
| Guards (Addendum 9 Q1) | `DB_RE` `^assetops_(demo3\|polish)_[a-z0-9]{1,20}_test$`; work `var/demo3*` or `var/polish*` (`WORK_PREFIXES`). Marker and drop guard unchanged. |
| P-08 slip (§1.3) | `demo_combined_ev.declare_and_work` records `action.action_code`, `intent.intent_id` and the Action's posted `raised_at` (the create response carries no `raised_at`; the posted body is the stored value). R645. |
| Narratives (§3, Addendum 9 Q2) | Kobo and EV requests pass `narrative=f"{title}."`. w502 BUILD `narrated(title)` adds it to the fixture WR and the earlier visits only when `demo_combined_cold` sets `ns["DEMO_NARRATIVES"]`; standalone w502 and the worst-case path are unchanged. |
| Lab names (§3, D-5) | `install_cold_lab`/`install_ev_lab` `display_name=None` overrides the record's name (`dataclasses.replace`; source bytes and sha256 unchanged, so later installs stay idempotent). `demo_combined_cold.DISPLAY_NAME` "GreenHarvest Cold Room" (first install); `demo_combined_ev._install` passes "Depot Charging Hub" to every EV day's chain. R646; R111 closed for the demo build. |
| CO-1 (DEMO-A L1/L2, Addendum 9 Q4) | L1 assertion "Reliable service and battery and generator life" in the Must-not-harm text is back. "Action on the Cost row" reads `issues` + `in_hand` only and matches `k["action"]` in href or `display_code(k["action_code"])` in text (imported from `outcomes/display_code.py`). |
| DEMO-A L3 | R535/R552 descriptions marked historical; `.ai/CODE_STATE.md` DEMO-A heading/main/addenda text current (`4f57261d3`, Addenda 1-4). |

## Files materially changed

- `tools/demo_combined.py`, `tools/demo_combined_ev.py`, `tools/demo_combined_kobo.py`, `tools/demo_combined_cold.py`,
  `tools/demo_combined_finish.py`, `tools/w502_cold_work_walkthrough.py` (passthrough only).
- `backend/assetops_backend/sites/cold_lab.py`, `backend/assetops_backend/sites/ev_lab.py`.
- Tests: new `backend/tests/test_demo_combined_links.py` (5 pure); 2 new tests each in
  `test_w202_cold_lab_bindings_postgres.py` and `test_w205a_ev_foundation_postgres.py`.
- Records: `.agent/mock-departure-register.md` (R645, R646, R111 note, R535/R552 L3), `.ai/CODE_STATE.md`, task file.

## Acceptance criteria

TBD after the heavy jobs.

## Checks run

- `tools\run-host-tests.ps1 -- test_w202_cold_lab_bindings_postgres.py test_w205a_ev_foundation_postgres.py test_demo_combined_links.py`: 32 passed.
