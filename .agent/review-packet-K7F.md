# K7-F second Kisiwa-only scratch prepare (record)

Branch `task/DIESEL-K7F-kisiwa-freeze`, code `f1f7dca2a`. Ruling DIESEL-1-R3n (§9o.4). Build-side packet sections are not in this file; this is the scratch-run evidence only.

## Gate
- Keep-awake running (powershell PID 23744, found, not started).
- Free RAM, 5 samples over 2 min at 30 s: 4.55, 4.66, 4.70, 4.69, 4.67 GB (all >= 2.5 GB).

## Run
- Command: `python tools/demo_combined.py --db assetops_demo3_kisiwa_test --work var/demo3_kisiwa prepare --sites kisiwa --cap-seconds 5400` (PYTHONUNBUFFERED=1, absolute PYTHONPATH under the k7f worktree, plan2 venv python).
- First attempt refused in 62 s (exit 1): `database ... exists and var\demo3_kisiwa\.demo3-combined-work does not record that this tool made it`. K7-D's database was made from the k7 worktree's work folder. The marker file (same two lines, `db=assetops_demo3_kisiwa_test`) was copied by hand into the k7f work folder; the second attempt then dropped and recreated the database as intended.
- Second attempt: **exit code 0**, wall time 4308 s (tool: "Prepared in 4262.9 s (cap 5400 s)"). Kisiwa build step 3554.0 s (tool `wall_seconds` 3539.8); freeze + evaluate 0.7 s; register 1.6 s.
- Lowest free RAM 3.04 GB (60 s samples; floor 1.0 GB never approached). Peak working set 0.28 GB for the prepare process tree (python only; the Postgres server is a separate container). No stall.
- Expected, listed per R3n §9o.2: `performance: Site 'KOBO-001' is not registered in tenant 'demo'.` and the prebuild `code: FAILED` line with KOBO-001 404s (`/api/sites/KOBO-001/outcome-board...`).

## Story reads (kisiwa.json)
- CLI raise, nights 1-10 (28 Oct - 6 Nov): night 4 (31 Oct) `UNCHANGED` (the Finding already opened earlier in the build; CLI re-run does not reopen), the other nine `NO_FINDING`. `cli_raise_check` passed (it ran inside the prepare). Assess states: night 4 UNEXPLAINED, others WITHIN_MARGIN.
- Action ACT-000001 recorded 2026-11-01T13:00Z; site visit REC-000014 recorded 2026-11-02T12:15Z; case WR-000013 link recorded 2026-11-02T12:20Z, COMPLETED (shown 2 Nov 15:05 local = 12:05Z).
- Plan frozen at recorded_at 2026-11-02T12:30Z (S-4d 12:30), `effective_from` 2026-11-02T12:05Z = COMPLETE; candidates from 2026-11-02 (night 6) to 2026-11-15; baseline window `bc4b350d...` = night 4 ("The night of the finding", 95.7 to 144.3 L, No readings for 105 min).
- Verdict evaluated 2026-11-05T13:00Z (S-1d 13:00): **VERIFIED**, reasons `TARGET_MET`, source class REGISTERED_SIMULATION.
- Rendered headline: "Fuel stayed accounted for". Sentence: "On 3 fully checked nights after the change, the fuel in the tank matched the generator's modelled use and the recorded deliveries within the stated margin, and the tank sensor sent readings all night." Rule text: "Rule fixed before the check: the first 3 fully checked nights after the change must each stay within the stated margin, with the tank sensor sending readings all night." Fixed line: "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented." Cards: Nights checked 3 of 3; Fuel accounted for 3 of 3 nights; Tank sensor readings all night on 3 of 3 nights. Later nights 2, 3, 4 Nov each -24.3 to 24.3 L, within the margin.

## Finish rows (`demo_combined_kisiwa.py check`, exit 1)
| Row | Result |
|---|---|
| KIS-3 | pass. nights 10, night 4 UNEXPLAINED, others WITHIN_MARGIN; `tolerance_l` "1/100000"; `max_diff_l` loaded_litres 0, use_low 0, use_high 0, residual_low 0, residual_high 0 |
| KIS-4 | pass (supported 1, priced 1, sums_checked 5, served_strings 124) |
| KIS-9 | pass (records 13, dips 11, placed 15; (e) is inside the row, no separate line) |
| KIS-5 | pass (VERIFIED, TARGET_MET, pins_checked 4, later nights 2, 3, 4 Nov) |
| KIS-10 | **FAIL**: `AssertionError: ('/api/estate/outcome-summary', {'from': '2026-10-30T21:00:00Z', 'to': '2026-11-06T21:00:00Z'}, 422, INVALID_WINDOW ...)` |

KIS-10 cause (read, not changed): `kis_10` (`tools/demo_combined_finish.py:1071-1090`) builds the estate summary window from Kisiwa's Site-local day starts (Africa/Dar_es_Salaam, 21:00Z). `estate/scope.py:108` requires midnight-aligned UTC bounds, so the estate route refuses it. The other estate-summary rows use `ctx.day(...)` (UTC-aligned). Needs a code fix (align the window to UTC midnight) before KIS-10 can pass; it is a stop to the coordinator and the Architect, not edited here.

## KIS-10 fix and check re-run (coordinator decision, mechanical)
- Fix: `tools/demo_combined_finish.py` new `utc_aligned_window(lo, hi)` (UTC midnight at/before `lo`, at/after `hi`); `kis_10` calls the estate summary with it, over the same story days (window now 2026-10-30T00:00Z to 2026-11-07T00:00Z). KIS-10's assertion, `demo_rows.kis10` and the estate scope rule are unchanged.
- L0 test `backend/tests/test_k7f_kis10_window.py` (3 tests): the old local-start window is refused by the real `estate.scope.check_window` (so the test fails against the old window); the aligned window passes it and covers the story days; an already aligned window is unchanged.
- Re-run (check only, no prepare, read-only) against kept DB `assetops_demo3_kisiwa_test`, work `var/demo3_kisiwa`: `demo_combined_kisiwa.py check <url> var/demo3_kisiwa` from `backend/tests`, exit 0. KIS-3, KIS-4, KIS-5, KIS-9 and KIS-10 all pass. KIS-10 read: entry "ACT-001 verified on example data", one thread; no extra night became visible.
- Tests: K7 story, KIS-10 window, finish CO1, K6b rules, chain coherence: 302 passed. `probe_kisiwa_fuel.py --check` and `probe_kisiwa_nights.py --check`: both "probe result current", exit 0.

## Deviation accepted by the coordinator
The `.demo3-combined-work` marker was hand-copied from the k7 work folder into `var/demo3_kisiwa` for the scratch prepare. The database is a throwaway test DB; the coordinator accepts this and it is recorded here as a deviation.

## Kept
Database `assetops_demo3_kisiwa_test` and `var/demo3_kisiwa` kept, nothing dropped. `assetops_demo3_full_test` untouched.
