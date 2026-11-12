# DATA-17N coverage — lane B packet (2026-11-12)

Branch `task/DATA-17N-coverage`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-data`, from main `f4850ee2c`.
Scope: D-17N.4 / rev 7 §7.4; item specs in `architect-answer-non-kobo-sites-2026-11-10.md` (rows E7, E14, E16, K10,
K11, K14, K16, C17 and the DATA-5/10 cards). One commit per item; no DB was touched today (no-DB tests only).

## Per-item status

| Item | Commit | Status | What changed |
|---|---|---|---|
| DATA-5 | `b5f58bec3` | built, no-DB tested; **VPS proof pending** | `backend/tests/story_diagnostics.py` routes diagnostic posts to the product `DiagnosticIngestionService`. Replay harness `_publish_and_accept(..., diagnostics=True)` (Kisiwa nights); Cold `w202.DIAGNOSTIC_CLOCK` (story `received`); EV `w205b.FORWARD_DIAGNOSTICS` (chain decision clock), set by `demo_combined_cold/_ev`. Ordinary tests keep their centrals (flags off). Kobo unchanged (Q1). |
| DATA-10 | `5933243e1` | built, no-DB tested; **VPS proof pending** | Kisiwa story doc `service_plan` (written S-8d 09:00, CALENDAR, due S+5d 00:00, "Generator 250-hour service", asset `generator`); `build` posts it via `WorkService.post_plan` at its story instant (`write_service_plan`). |
| DATA-13 | `ecf2d153a` | built, no-DB tested; **VPS proof pending** | `demo_story_clock.STORY_ACTION_DUE` = 14 d. Cold w502 BUILD posts `DEMO_ACTION_DUE` from the demo namespace; EV `w504_ev_work_cases.DEMO_ACTION_DUE` (set/restored in `declare_and_work`; read-back compares the posted due); Kisiwa `record_action`. Standalone producers unchanged; Kobo mill/battery Actions unchanged (Q3). |
| DATA-4 | — | **not built: spec gap (Q5)** | Not configuration (see Q5). |
| DATA-8 | `0926c7ae9` | built, no-DB tested; **VPS proof pending** | `SUPPLY_USES`: load-clinic (cold store) and load-mill (water pump) `PRODUCTIVE`; `publish_price` adds Kobo's productive-price fixture v1 (0.25 USD/kWh) for KISIWA-001 at the diesel price instant. |

No item names a finish (self-check) row in its spec, so none was added; the Saturday rehearsal finish check is the gate.

## Checks run (this machine, no DB)

- New: `test_data5_story_diagnostics.py` (6), `test_data10_kisiwa_service_plan.py` (5), `test_data13_story_action_due.py` (6), `test_data8_kisiwa_productive.py` (4); updated fakes in `test_k1_kisiwa_fixtures.py`, `test_own_g1_add_dates.py`, `test_evhb_ev_window.py`.
- Every non-Postgres backend/host test file importing a changed module (22 files): **367 passed, 31 skipped** (skips are DB-gated).
- `tools\check-all.ps1`: see the result line at the end of this packet.
- Not run: Postgres files, prepare, finish check (lane rules: no DB jobs on this laptop before 16:00; VPS).

## VPS resume points (scratch prepare proves them)

1. `git merge main` in the worktree; PYTHONPATH incl. `gateway;field`.
2. Scratch prepare on a `<prefix>_audit*` DB (never the demo DBs), Kisiwa on. Then:
   - DATA-5: `SELECT s.site_code, count(*) FROM gateway_diagnostic d JOIN site s ON s.id = d.site_id GROUP BY 1` — Cold, EV and Kisiwa > 0; no `gateway_diagnostic_refusal` rows for them. Health tab on each Site: the 8 "Not in the gateway's latest report · Unknown" lines become values (K16, E14). If a post is refused, the harness returns the refusal to the gateway (it is not swallowed): check the refusal row's kind first.
   - DATA-10: `maintenance_plan` has one Kisiwa row "Generator 250-hour service" on the generator asset; Overview › Protect no longer reads "No preventive plan recorded" (K14).
   - DATA-13: `domain_action.due_at` is set for the Cold, EV and Kisiwa story Actions (= raised_at + 14 d); Work › Actions no longer reads "Due dates are not yet set" (C17).
   - DATA-8: Kisiwa `financial_assumption` `productive_use_price_per_kwh` 0.25 USD; Overview › Grow shows estimated productive-use sales, not "no productive-use equipment declared" (K10, K11).
   - Finish check green, especially KIS-6/KIS-7 (item 3 board earnings; DATA-8 gives Kisiwa a `productive_kwh` subject) and KIS-1.
3. Postgres files to run one at a time after the prepare: `test_w202_cold_replay_postgres.py`, `test_w205b_ev_replay_postgres.py` (flags off: unchanged), `test_k1_kisiwa_site_postgres.py`, `test_w504_ev_work_producer_postgres.py`, `test_walk1_productive_producer_postgres.py`.

## Questions (batched; not designed around)

- **Q1 (DATA-5, Kobo).** The card says "touches every story Site, Kobo included: recapture Kobo Health". Kobo already has `gateway_diagnostic` rows from another source, so Kobo forwarding is left off (`demo_combined_kobo` unchanged). Turn it on for Kobo too (one keyword at its `_publish_and_accept` calls)?
- **Q2 (DATA-5, clocks).** The gateway builds each diagnostic on its own wall clock (cadence slot, `observed_at`, device contacts); the harness stores it with the story `received_at`. If Health's freshness compares `received_at` with real now, a Sat-night prepare may read "stale" on Monday. Which "now" does the demo Health read use, and is stale acceptable?
- **Q3 (DATA-13).** No due rule is specified. Built: due = raised + 14 d (keeps Kisiwa's, raised S-5d, in the future through S+8d). Kobo's battery Action and the mill Action are left without a due date. Confirm the rule and the scope.
- **Q4 (DATA-10).** Dates chosen inside "due within the story month": written S-8d 09:00, CALENDAR due S+5d (due soon on the demo days). Confirm, or give RUN_HOURS 250 (which reads "not assessed").
- **Q5 (DATA-4) — blocked.** The EV Foundation already declares charger 60 kW, connectors c1/c2 60 kW, the site import meter and the 80 kW import limit (`backend/tests/fixtures/w2/ev-lab-001.yaml`). "Charger use · connector capacity not read" is a constant (`backend/assetops_backend/site_outcomes/ev.py:41,201`); no utilisation calculation exists. On the EV single-line diagram, Grid supply, Main CB, feeder meters and Load manager are hard-coded "Not declared" slots (`frontend/src/sites/SiteSingleLineDiagram.tsx` ~1619-1655, footnote 1718), and "Rating not declared · No connector declared" is the empty Charger 2 slot (one charger declared). So a configuration change removes nothing. It needs an Architect spec: the Charger-use rule (e.g. delivered kWh / (rating × declared open hours)), read-model fields for grid supply / main breaker / feeder meters, and the diagram change.
- **Q6 (DATA-8).** A load has one supply use, so the cold store moves from ESSENTIAL_SERVICE to PRODUCTIVE (no backend logic reads ESSENTIAL_SERVICE; the Foundation's displayed supply use changes). The price reuses Kobo's 0.25 USD/kWh fixture. Should Kisiwa also declare MG-1 (the answer file says "MG-1 waits for DATA-8")? It would change CO-6 `objective_site_count`.

## Residual risk

- DATA-8 gives Kisiwa a measured `productive_kwh` subject: KIS-7 item 3, the Grow/Optimize board rows and any PRODUCTIVE_USE_HEADROOM opportunity on Kisiwa may change. Only the rehearsal finish check proves it.
- DATA-5 adds work per gateway delivery pass (one diagnostic per cadence slot), so prepare time grows slightly. Not measured.
