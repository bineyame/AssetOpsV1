# Review packet: WALK1-5 (5-day spare-solar read; declared price in the productive-use what-if)

Branch `task/WALK1-5-solar-window-whatif`, worktree `AssetOpsV1-w1f`, base main `635654bf0`.
Spec: `.agent/build-sheet-WALK1.md` §6 WALK1-5, Addendum 4 (fallback copy), Addenda 3/5/6 (headline precedence,
calendar). **Status: PARTIAL.** Part 1 (5-day solar read) is built. Part 2 (what-if prefill) is blocked at pre-flight
F3; see Blocking question Q1. Not ready to merge until Q1 is ruled and part 2 is built or descoped.

## Outcome delivered (part 1)

Mechanism: Grow MG-1 opportunity → driver "spare solar" → evidence (the 5-day renewable read).

- `site_outcomes/mini.py` `_depth`: the renewable window is the `RENEWABLE_DAYS = 5` Site-local days ending on the
  board day (local midnight of day−4 to local midnight of day+1). Fuel, service, backup are unchanged (noon hour).
  It uses the existing mini-depth renewable read contract (`mini_depth/read.py` `hour_windows`, `MAX_DAYS = 5`,
  `compose_renewable`); no read, simulator, publication or prepare code is touched, so WALK1-4's readings flow
  in unchanged.
- `_grow` contributor "Productive use": `"Spare solar on {e} of {a} well-observed {day|days}"`; when `a < 5` it
  appends `" · {5−a} of the last 5 days not checked"`. With no assessed day in the window (read returns
  `assessed_days: null`): **"Not available yet · spare solar not checked on the last 5 days"** (Addendum 4),
  replacing "solar headroom not read for this day". A refused read stays the generic "Not available yet" line.
- Headline / short value unchanged in form (`"{lo}–{hi} kW of daytime solar unused"`, span over the window's
  eligible days); the `SIGNAL:PRODUCTIVE_USE_HEADROOM` issue fires on `eligible ≥ 1` over the window. The
  Addendum 3 L3 precedence (spare-solar headline leads on a priced zero-use day) and the WALK1-3b state/potential
  rules are untouched and still pass their tests.
- New strings are in `mini.COPY` (vocabulary scan).

## Files materially changed

- `backend/assetops_backend/site_outcomes/mini.py` (constants, `_depth` window, `_grow` text).
- `backend/tests/test_walk1_5_solar_window.py` (new, 8 tests).
- `backend/tests/test_out_b2_mini.py`, `backend/tests/test_walk1_productive_sales.py` (pinned strings and the
  renewable window updated to the 5-day form).
- `.agent/mock-departure-register.md`: R685 (suffix), R687 (no-checked-day fallback), R655 strings added.

## Acceptance status

| Criterion | Status |
|---|---|
| Renewable window = 5 local days ending on board day; other domains unchanged | Met: `test_window_is_five_local_days_...` asserts the composer's window and that the real `hour_windows` accepts it and yields the 5 local noons; `test_depth_windows_follow_the_site_local_day` updated (16..21 Oct) |
| Text "Spare solar on {e} of {a}…" + " · {5−a} of the last 5 days not checked" | Met; pinned for 0/2, 2/3, 1/1 (singular), 5/5 (no suffix) |
| Compose test over 5 days, mixed eligible/excluded/missing | Met: fixture stored hours run through the read's own `compose_renewable` (ELIGIBLE, EXCLUDED, LIMITED, CONFLICT, missing) |
| Addendum 4 fallback "Not available yet · spare solar not checked on the last 5 days" | Met (all-missing and all-LIMITED/CONFLICT windows) |
| Expected S board "0 of 2 … · 3 of the last 5 days not checked" | Met on fixture data of that shape; real-data actuals depend on WALK1-4 and are G2's to report (Addendum 5 forecasts "1 of 3" on S) |
| Headline/short value unchanged in form; headroom issue on S+1 shape | Met on fixtures (`test_mixed_days_...`) |
| What-if prefill "Declared price · {p} {cur} per kWh" / "Entered for this what-if" (R686) | **Not built: blocked at F3 (Q1)** |
| Vitest prefill and label | **Not built (Q1)** |

## Checks run (revision `9adc4639a` + register edit)

- Scoped backend, no DB: 20 modules (`test_walk1_5_solar_window`, `test_out_b2_mini`, `test_walk1_productive_sales`,
  `test_walk1_3b_target_progress`, `test_out_b2_vocabulary`, `test_out_b1_*`, `test_out_b3_cold_ev`,
  `test_out_b4_{imports,read,route,window}`, `test_out_c1/c2/c4`, `test_out_d4_board`, `test_out_w1/w2`,
  `test_out_a1_outcome_map`): **278 passed**, 8.3 s.
- Postgres (`assetops_walk1f_test` base): `test_out_b4_board_postgres.py`, `test_walk1_productive_producer_postgres.py`:
  **7 passed**, 201 s.
- Non-vacuity: disabling the suffix branch made 3 of the 8 new tests fail; reverted with `git checkout`.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Frontend: no frontend file changed; no vitest run. Layout evidence: not run (no layout change; text only).
- Full suites: not run (scoped tier per §7).

## Blocking question (pre-flight F3)

**Q1. There is no productive-use what-if authoring page to prefill.**
- `frontend/src/sites/MiniScenarios.tsx` (`/sites/:siteId/financials/scenarios`, the Grow option
  "Productive-use what-if" target) is read-only by design (header comment, closure 1) and renders the fixed text
  "Scenario creation unavailable" (`:395-397`). No frontend file authors a PRODUCTIVE_LOAD scenario or holds a
  `tariff_per_kwh` input (`proposed_kw` appears only as a display label); `miniDecisionsClient.ts` has no POST.
- The v70 mock's `scenarios` screen is a placeholder ("Placeholder · to be designed with the owner",
  `screens.js:712-713`); the mock has no authoring layout to follow.
- The backend create endpoint exists (`POST /api/sites/{code}/financials/scenarios`, `mini_decisions/scenarios.py:119`
  requires `schema_version, idempotency_key, actor, name, kind, assumptions, pinned_selection…`), and the declared
  price read exists (`financialsClient.getAssumptions(..., {key: "productive_use_price_per_kwh"})`), so the prefill
  itself needs no new endpoint. What is missing is the whole authoring surface: a form (name, proposed kW,
  duration, tariff), renewable-revision pin selection, actor/idempotency, a POST client and its refusal copy.
- That is a new screen without a mock layout, well beyond the 3-unit slice, so I did not design it.
- Options for the Architect: (a) a new authoring slice (form + POST + pins), with the declared-price prefill and
  labels folded in; (b) for this slice, show the declared price read-only on the existing Scenarios page or the
  opportunity page (`MiniOpportunity.tsx` "Tariff: No tariff declared", `:272`) as "Declared price · {p} {cur} per
  kWh", with any result labelled an estimate, and defer authoring; (c) descope the what-if half from WALK1-5.
  G2's `kobo-whatif` capture depends on the choice.

## Known deviations

- KD1: part 2 not built (Q1). R686 stays reserved and unused.
- KD2: no `.ai/CODE_STATE.md` / `ACTIVE_CONTEXT.md` update yet; done when the slice completes (coordinator at merge,
  as WALK1-3b L5).

## Residual risk

- Real-data texts depend on WALK1-4's readings (and its D-W1-10 binding fix); verified here only through fixture
  hours via the read's pure composer. G2 confirms actuals.
- The board's renewable read is now 5× the hours; the read already supports it (`MAX_DAYS`), and the Postgres board
  test passed, but board latency on a large DB is not measured.

## User-review focus

`USER_REVIEW_REQUIRED`: no separate task file; per the W1 rule the owner sees this in the combined walkthrough after
G2. The Architect must rule on Q1 before the slice can complete.
