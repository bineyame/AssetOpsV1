# DD3d-a review (discovery, round 1)

Reviewer: Claude (fresh, not the author), 2026-11-23. Branch `task/DD3d-fuel-floor`, head `96e1566e3`; diff
`git diff main...HEAD` (merge base = main `7c47ec357`).

## Summary (round 1)

- **Verdict: ACCEPT.** No High, no Medium. Six Low, none blocking.
- Floor rule, port and wiring are D-DD.153 as written: adverse branch only, strict `>`, `NONE` keeps 0, filtered by
  `FLOORED`, `basis()`/`claim()` change only when the floor binds. `git diff main` on the protected paths is empty.
- Recomputed with my own script (no `dd_check`, no product import): Kobo July 12.00 L unexplained of 12.000 used, 2 % 0.24,
  2a 50: INSIDE (2 % alone: RAISED). Kisiwa September 18.00 of 710.945, 2 % 14.22, 2a 100: INSIDE (2 % alone: RAISED).
  Kobo October 120.00 of 634.224, 2a 50: RAISED.
- H5 Kisiwa 2026-09: 73 + 737 + 18 = 828 L, 2 % = 16.56, 2a = 100; 18 <= 100 passes. FAIL without a declared a is
  shown by the builder's `plant-b.log`.
- Deviations 1 to 4: accepted (below). Deviation 3's open point is answered for the file: `valid_from` is July's start.
- Night states rerun: 127 WITHIN_MARGIN per Site, none UNEXPLAINED or EXCESS, one DELIVERY_RECORDED_LATE (Kobo).
- Questions for the Architect: none.

## Findings

All Low. None is an acceptance gap.

### L1: no test pins the floor to July on the published Foundation
- `backend/tests/test_dd3d_fuel_records_postgres.py:258-268` takes its window from the stored revision's own `valid_from`.
  It would pass if the file or the publisher dated the Foundation in November, when July to October would have no floor.
- The file is right today: `lakeside-power.onboarding.json:17,622,1146` `valid_from` `2026-06-30T21:00:00Z` is
  1 July 00:00 EAT, equal to `month_bounds("2026-07", "Africa/Nairobi")[0]`; `operator_file.py:146` publishes it.
- Fix: read the floor over `month_bounds("2026-07", "Africa/Nairobi")` at the three Sites (2a = 50, 100, 20).

### L2: C-DD17's relative tolerance falls back to 0 % silently
- `tools/dd_check.py` `judge_pure_c_dd17`: `tolerances.get(code, Decimal(0))`. Before this slice a missing
  `tolerance_pct` raised. Mto declares none in `M` (its line prints `0 %`), which is harmless while it is NO_GAP. If
  Kobo or Kisiwa lost theirs, C-DD17 would judge on the floor alone.
- Fix: a FAIL line when a Site with a non-zero draw declares no `tolerance_pct`.

### L3: some loader failures end in a traceback, not exit 2 with the record's id
- `backend/assetops_backend/load_fuel_records.py:81-93`: only `WorkRefused` is caught. A malformed record (missing key,
  bad `recorded_at`) or `WorkStoreUnavailable` from `site_context` or the store exits 1 with a traceback. A naive
  `recorded_at` is read in the host's zone. The world's own writer produces none of these.
- Fix: refuse `FUEL_RECORDS_FILE <id>` on a key or instant error and on a naive instant; catch `WorkStoreUnavailable`.

### L4: deviation 4's list of old wording is incomplete
- Also stale: `demo-build-cost-plan.md:33` "(above 2%)" and `derivation-register.md:1695` (quotes the `PLAIN` key this
  slice replaced in `loop-core.js`). Both are in `Docs/demo-sprint/product-direction-layer4/`.
- Fix: add them to the list for the design-doc alignment pass.

### L5: the refusal text names only the old databases
- `backend/assetops_backend/prepare_clock.py:31` still says "it needs assetops_polish_* or *_test". World rungs are now
  admitted. The handoff says a baseline pins the text; the tests match only the code and the name.
- Fix: name the rungs when the text next moves. Leave it if a baseline pins it.

### L6: packet, cited counts
- "`main-4files.log` ... (three files ...)": the log's name and the packet disagree. The four failing ids match main's.

## Deviations

1. **C-DD2 read as the books: accept.** The literal reading cannot hold (Mto buys none; Kobo none in July and August;
   D-DD.154 says one per accepted note, D-DD.175 covers a month with none). Litres equal to the FUEL rows is stronger than
   presence: it also catches a delivery the books did not buy. If both sides were dropped together, C-DD8's balance fails.
2. **C-DD8 live and failing until DD5.1: accept.** Same shape as C-DD6; a stub also failed, and this one names what is
   missing. The balance uses the checker's own curve and JSON reads. Note for DD6.1: a Site with one assessed night and the
   rest NOT_ASSESSED passes; the counts print and should be read.
3. **Clock on the one store: accept**, safer than a module swap and within D-DD.168 ("set on the work store built").
   The window point: `valid_from` covers July exactly (L1). DD6.1 keeps the served assertion.
4. **Older wording: accept** for the alignment pass, with L4's two lines.

## Checks I ran

- Own recompute: `/opt/assetecon/evidence/DD3d/review/recompute.py`, `recompute.log`.
- `nights.py` rerun: identical. `nights5.py` (5 Nov): NOT_ASSESSED `MISSING_CLOSING` at all three; readings end 6 Nov.
- `check-manifest-{before,after}.log`: 12 to 6; the diff is exactly the six H5 lines plus H9's printed count.
- `fixtures.js` diff by token: the two sentences and the sha only.
- `test_dd3d_checks.py`, `test_dd3d_fuel_records_file.py`, `test_telemetry_join_parity.py`: 48 passed.
- Architecture and agent-workflow guards: pass.
- Cited, not rerun: backend reach set (1104 passed, 4 failed; same four ids as main), world suite (525 passed, 1 failed,
  that one now in my 48), plants.

## Not verified, residual risk

- No Postgres run of mine. The served observation and stored nights are DD5.1 and DD6.1.
- DD5b's night run must use a `known_at` after the load: the Foundation is recorded at load, so a past `known_at` reads no
  accuracy and gives NOT_ASSESSED.
- `exports --telemetry` with no tenant filter now refuses when a mini-grid Site has no readings (ruled, D-DD.168); DD5b's
  step list should pass the mini-grid directory or a tenant filter.
