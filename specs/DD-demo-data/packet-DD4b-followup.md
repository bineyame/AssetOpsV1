# DD4b follow-up review packet (D-DD.158, D-DD.161's DD4b part; 0.5 u)

Branch `task/DD4b-followup` from main `ba0e3994a`. Rulings `rulings.md` D-DD.158 and D-DD.161 (deviation 4, the DD4b
bullet); DD5a packet deviation 6 (`/opt/assetecon/AssetOpsV1-dd5a/specs/DD-demo-data/packet-DD5a.md`). Nothing else
designed. Evidence: `/opt/assetecon/evidence/DD4b/followup/`.

## What was built
- D-DD.158: the EV `<month>` of `measured.json` gains `"windows": {"0000_0500", "2200_2400"}`, the depot import summed
  over local minutes [00:00, 05:00) and [22:00, 24:00) of each day, exact, rounded once by the frame
  (`telemetry_ev.HOUR_WINDOWS`, `EvSiteRun.measured_months`). `read_measured` refuses `TEL_FOUNDATION` on an absent
  `windows` or an absent/extra window key (`exports_measured.EV_WINDOW_KEYS`). `meter_billed` writes them as `metered`
  for `kwh_2200_2400` and `kwh_0000_0500`.
- C-DD7's EV window clause (`tools/dd_check.py`): `judge_meter_books(..., measured=)` takes Site code -> `measured.json`
  months and judges each window equal to the `site-meter/import` energy over the same local minutes, exactly
  (`EV_WINDOWS`, the checker's own table). Given `measured`, the EV pending line is dropped.
- D-DD.161: `EvSiteRun` rows are eight elements; a connector measurement row inside a session (the pack's session,
  plug to unplug: state, energy, power, requested-power, allocated-limit) carries `{"session_id", "connector_id"}`,
  the same pair as that session's events (`connector_id` = the connector asset, as the events). Events, the depot
  import and rows outside a session carry none. The frame's `VerticalBinding.rows` writes it as the row's `session`;
  cold's seven-element rows are unchanged.

## Commits
| Commit | What |
|---|---|
| `fef624237` | tests first: m8, m2 key set, e12 (+ `windows` in the e-tests' hand doc), c7 window clause, j6. All 5 failed first (`red.log`: KeyError `windows`, key-set refusals, no `session`) |
| `2facff231` | the build (writer, exports_measured, frame, checker) |
| `fc003ac91` | j3 pins eight elements; j6's bounds corrected to the pack's session (my first test took the START event's minute as the session's start; the pack's session starts at PLUG, one minute earlier) |
| `7fcee0989` | `fixtures/measured/metro-bus.measured.json` from the branch plant |

## Tests (plain pytest from `simulator/`, host venv; backend via `tools/heavy-slot.sh --db-lane -- pwsh tools/run-host-tests.ps1`)
- New/edited, green at `7fcee0989`: 5 of 5 (`green.log` before the fixture, then the reach set).
- Writer reach set, 21 files of `simulator/tests/world` (`reach.log`): **248 passed, 3 failed**, 200 s, 168 MB. The 3 are
  `test_scope_seasons_parity` (all three digest tests), **main's own**: the same 3 fail on main `ba0e3994a`
  (`scope-main.log`). `.agent/main-baseline/23d2cd9f6.md` lists no simulator files, so main was rerun for this file.
- Backend `test_dd4_check.py`, `test_dd1_check.py`, `test_dd45_charger_bound.py`: **44 passed**, 4.3 s (`backend.log`;
  `test_dd4_check`'s pending assertion holds unedited: without `measured` the EV line stays, reworded).

## Plants (each reverted; `plants.log`)
a. writer window 22:00 -> 21:59: m8 and c7 fail. b. writer drops the session pair: j6 fails. c. `read_measured` skips
the window key set: e12 fails. d. checker window 22:00 -> 21:59: c7 fails ("measured 800.000 kWh, meter 806.667").
e. `meter_billed` writes the windows as null: e12 fails.

## Parity (the EV writer run, once, plus the golden from main)
`plant.sh` (books; site-inputs; Kobo + Mwea 14-15 Oct; the three depots over the full span in one process; `exports
--telemetry` for metro-bus). Golden from main `ba0e3994a` (detached worktree): EV run 26:17, 150,712 kB. Branch at
`fc003ac91` (the code of the head; only the fixture follows): EV run **26:52, 163,672 kB**, exit 0. `compare.py` (`parity.log`): 423 files;
31 byte-identical (books, sites.json, Kobo/Mwea readings and measured, the 3 session-free days); 392 differ, and with the
new fields taken off only the three EV `manifest.json` differ, in `golden_digests` alone (the day files' digests).
New fields: 4,928,190 `session` objects, 15 `windows` blocks, 8 meter-billed window leaves. Main's `measured.json` was
byte-identical to the committed fixture before it was replaced.

Information (not judged): Embakasi's metered windows sit beside `M`'s, e.g. Oct 2200_2400 23495.900 vs `M` 15500,
0000_0500 21340.867 vs 23560 (`branch/extras/metro-bus.meter-billed.json`). D-DD.20 prints, never tunes.

## Checks
`tools/check-architecture.ps1` passed (`arch.log`); `tools/checks/statement_catalogue.py` OK (`stmt.log`);
`tools/check-agent-workflow.ps1` passed (`workflow.log`).

## Known deviations
1. C-DD7's EV window clause is live in the judge, but `check_meter_books` (the live run on the clone) passes no
   `measured`: the checker has no input for the loaded world's `measured.json`; D-DD.160 gives that fetch to DD5b (for
   the mini-grid clause). Until DD5b wires it, the live run keeps the EV line pending (reworded). Architect to confirm
   DD5b passes the same documents to the EV clause.
2. `session` is put on every in-session connector measurement row (state and means as well as energy), per the
   ruling's "a connector measurement row inside a session"; DD5a's sealer copies it from energy only. In-session is the
   pack's session (plug to unplug), the same test CLOCK-1 already uses.
