# FX-KOBO-V3 packet (D-E5.21; review Lows 2, 3)

Branch `task/FX-KOBO-V3`, one code commit on main d810ecef3.

## Delivered
- `tools/demo_combined_rows.py` (the card's "demo_rows.py"): pure `gap_gated(days_schema)`, true only for schema version >= 4 (dict or int; unreadable/bool is not gated).
- `tools/demo_combined_finish.py`: `Ctx.days_schema` (set in `load` from `days.json`). `wkgap` raises only when gated; on v3 it returns the pattern it read (missed, partial, or the week pattern when it conforms) with `gated: false, calendar: <version>` and passes. Assertions moved unchanged into `_wkgap_assert`. Docstring cites D-E5.21.
- `tools/demo_combined_kobo.py`: manifest `days` label from `days.json` `source` via `days_label(work)` (`tmp.parent` is the work dir).
- Tests: `test_demo_combined_finish_rows.py` (gap_gated; wkgap row: v3 fixture returns `gated: false`, v4 with v3 pattern raises, v4 calendar with v3 grades raises, `_wkgap_assert` ungated v3 raises). `test_demo_story_days.py`: `test_s10_is_fillable_on_v4_with_the_fresh_before_day` (positive half on `DEFAULT_FILE`).

## Checks
- test_demo_combined_finish_rows 69 passed; test_demo_story_days 92 passed; test_demo_combined_mill 15 passed. No build, no full suite, no guards A/W/V/N run (not requested in the dispatch).
- Fail-on-main proof: main's rows + finish restored, finish_rows run: 2 failed (gap_gated test, wkgap row test), 67 passed; restored to HEAD, tree clean. The v4 S-10 test passes on main's code too (coverage addition, not a behaviour change).

## Deviations / risk
- Card path `tools/demo_rows.py` does not exist; the module is `demo_combined_rows.py` (imported as `demo_rows`).
- The wkgap row's v4 positive pass (full DB-backed path) is not unit-tested; only the gate and failures are.
- `days_label` assumes the source file lives under `backend/conversions/`; the name comes from `source`.
