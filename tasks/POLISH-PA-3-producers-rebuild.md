# POLISH PA-3 - Producers, links and rebuild (Lane A, about 5 units)

Status: in_progress

USER_REVIEW_REQUIRED: no (merges on review ACCEPT; walkthroughs deferred to the owner walkthrough after this round).

Contract: `.agent/build-sheet-POLISH.md` §1.3 (P-08), §3 "Lab Site names" and "Request narratives", §3.1 PA-3 rows,
§4 (P-01/P-02), §5 Lane A PA-3, §6 D-3/D-5, §7 (R645, R646), Addendum 3 (rebuild DB and screen check), Addendum 5
(Lab names are data, never exempt) and Addendum 9 (Q1-Q4). Branch `task/POLISH-PA-3-producers-rebuild` from main
`c4a39b1dc`.

## Acceptance

1. `tools/demo_combined.py` `story_links(story, days, kobo, web)` is pure; `links()` and `serve` print it. Rows: portfolio
   and findings week, preventive and maintenance month, one board per story day (Kobo `?date=`, cold/EV on the
   `days.json` event window, or the whole calendar day labelled "no event: whole day"), Kobo Overview day S,
   verification, Finding. No `/outcomes` or `/overview` form. Pinned by `backend/tests/test_demo_combined_links.py`.
2. Guards accept `assetops_polish_<name>_test` and `var/polish*`, and still refuse other names (pure test).
3. `demo_combined_ev` records `action_code`, `intent_id` and the Action's posted `raised_at` in `ev.json` (P-08 slip).
4. Narratives: Kobo and EV requests pass `"{title}."`; w502's fixture WR and earlier visits do so only when
   `demo_combined_cold` sets `DEMO_NARRATIVES` (standalone w502 unchanged; worst case unchanged).
5. `install_cold_lab`/`install_ev_lab` take `display_name`; the demo producers pass "GreenHarvest Cold Room" and
   "Depot Charging Hub". Postgres tests cover with and without it.
6. CO-1: DEMO-A L1 assertion back; L2 reads `issues` + `in_hand` only, matching href or `display_code(action_code)`.
   L3 stale register/CODE_STATE text fixed.
7. Rebuild into `assetops_polish_full_test` / `var/polish_full` (`check.json` all rows pass); the slow build test passes
   every row. `assetops_demo3_full_test` is not written.
8. Strict capture of all 14 keys from the rebuild; the packet lists the PA-1/PA-2 screen check, capture counts per
   owner, and the runbook (links, timings, the Depot Action line). Register R645, R646. Guards: check-all.
