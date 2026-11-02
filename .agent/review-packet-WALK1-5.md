# Review packet: WALK1-5 (5-day spare-solar read; declared price on the opportunity page)

Branch `task/WALK1-5-solar-window-whatif`, worktree `AssetOpsV1-w1f`, base main `635654bf0`.
Spec: `.agent/build-sheet-WALK1.md` §6 WALK1-5, Addendum 4 (fallback copy), Addendum 7 (F3 ruling: option (b),
D-W1-17), with Addenda 3/5/6 unchanged in effect. Scoped tier. Built against the existing mini-depth renewable read
contract; no WALK1-4 area (mini-depth read, simulator v6, publication v5, prepare) is touched.

## Outcome delivered

**Part 1: the spare-solar line reads the last 5 days** (Grow MG-1 opportunity → driver "spare solar").
- `site_outcomes/mini.py` `_depth`: the renewable window is `RENEWABLE_DAYS = 5` Site-local days ending on the board
  day. Fuel, service and backup still read the noon hour. It uses the existing read (`mini_depth/read.py`
  `hour_windows`, `MAX_DAYS = 5`, `compose_renewable`).
- `_grow` "Productive use" line: "Spare solar on {e} of {a} well-observed {day|days}", plus
  " · {5−a} of the last 5 days not checked" when a < 5. With no checked day: "Not available yet · spare solar not
  checked on the last 5 days" (Addendum 4). A refused read keeps the generic "Not available yet" line.
- The headline form, the headroom issue (eligible ≥ 1 over the window), the L3 precedence and the WALK1-3b state
  rules are unchanged.

**Part 2: declared price on the opportunity page** (Addendum 7, lever input → estimate).
- Container `shell/SiteAnalyticsFrames.tsx` `SiteOpportunityFrame`/`OpportunityScreen` gains `financials` (default
  client; `App.tsx` unchanged) and `useDeclaredPrice`. It reads `getAssumptions(site, {key:
  "productive_use_price_per_kwh", limit: 1, recordedAt: known_at when one is given})`; no new endpoint.
  - PRICED → `{value, currency}`; NO_PRICE or no selection → `null`; a failed read or CONFLICT → `"unavailable"`.
  - The page shows its loading line until the price read settles.
- `sites/MiniOpportunity.tsx` `ConsequenceBasis`, Tariff row (label unchanged):
  - "Declared price · {p} {cur} per kWh";
  - "No price per kWh declared";
  - read failed: "The declared price could not be loaded, so none is assumed" (KD1);
  - a linked what-if keeps "Unavailable in this read".
- New row "Value at declared price" (key `declared_value`), after Tariff. It shows only on a SUPPORTED study with a
  known headroom bound and a declared price: "Up to {lo×p}–{hi×p} {cur} for each hour the spare solar is used ·
  estimate, not sales" (one amount when equal). `decimalTimes2dp` is exact BigInt decimal, 2 dp, ROUND_HALF_UP.
  Nothing is stored, projected or summed. "Gross sales" stays tied to a stored what-if.
- F4: the strict capture gate (`tools/demo-combined-vocabulary.mjs`) scans all visible `<main>` text, and
  `productVocabulary.json` bans "scenario". The `screenGlosses` exemptions only apply to vitest. So the gate counts
  it, and "Scenario energy" is renamed "What-if energy" (R686).
- G2: capture key `kobo-opportunity` (`tools/demo-combined-evidence.mjs`). It starts at the S+1 board and follows
  `hops`: the board's renewable link (the Opportunity issue's target), then the renewable page's opportunity link.
  It has a width check after each hop and mock `opportunity-finding`. Finish row **WK-6**
  (`tools/demo_combined_finish.py`): finds the Kobo opportunity for the 5-day study ending S+1, asserts no linked
  what-if and a PRICED declared series, and returns the Tariff text starting "Declared price".
- Register: R685 (suffix), R686 (re-scoped per Addendum 7: D2 added row and labels, D1 authoring not built),
  R687 (no-checked-day text), R655 strings. Review-mode `MOCK DEVIATION (R685/R686)` comments at the code sites.

## Files materially changed

`backend/assetops_backend/site_outcomes/mini.py`; `frontend/src/sites/MiniOpportunity.tsx`;
`frontend/src/shell/SiteAnalyticsFrames.tsx`; `tools/demo-combined-evidence.mjs`; `tools/demo_combined_finish.py`;
tests `backend/tests/test_walk1_5_solar_window.py` (new), `test_out_b2_mini.py`, `test_walk1_productive_sales.py`,
`frontend/src/sites/__tests__/miniDecisions.test.tsx`; `.agent/mock-departure-register.md`.

## Acceptance status

| Criterion | Status |
|---|---|
| 5-day renewable window; other domains unchanged | Met (composer window plus the real `hour_windows` accepting it) |
| "… · {5−a} of the last 5 days not checked" suffix | Met (0/2, 2/3, 1/1 singular, 5/5 no suffix) |
| Compose test, mixed eligible/excluded/missing | Met, through the read's own `compose_renewable` |
| Addendum 4 no-checked-day text | Met |
| S board "0 of 2 … · 3 of the last 5 days not checked" | Met on fixture data of that shape; real actuals are G2's (Addendum 5 forecasts "1 of 3") |
| Container reads the declared price, no new endpoint | Met (request carries `key=productive_use_price_per_kwh`) |
| Three Tariff states, plus linked unchanged | Met; the failed-read text differs from the ruled text (KD1) |
| "Value at declared price" row, conditions, Decimal half-up | Met (present/absent cases; 0.125→0.13, 0.3125→0.31, 6.07725→6.08, 0.1×0.3=0.03, single amount) |
| F4 | Done: counted, renamed "What-if energy" |
| Vitest: Tariff states, value row, rounding, vocabulary scan | Met (3 new tests; T028+W1 terms and raw codes on every new string) |
| R686 re-scoped | Done |
| G2 `kobo-opportunity` + finish check | Added; not run (needs the G2 build) |

## Checks run (final revision: see head)

- Backend, no DB: 20 outcome/board modules **278 passed** (part 1). After the final edit, the 5 mini/Grow modules:
  **87 passed**.
- Backend, Postgres `assetops_walk1f_test`: `test_out_b4_board_postgres`, `test_walk1_productive_producer_postgres`
  **7 passed** (201 s).
- Vitest: `miniDecisions.test.tsx` + `siteWorkCases.test.tsx` **79 passed**. `tsc --noEmit` exit 0.
- `tools/check-all.ps1`: **12/12 PASS** (architecture, estate guards, navigation, workflow, registry, delivery,
  mock-gap, missing-claim scan + fixtures, evidence width, mock labels + vocabulary, screen ledger).
  - Note: `.venv` and `frontend/node_modules` in this worktree are junctions to `AssetOpsV1-plan2`'s (same lockfile).
    They are gitignored; without them check-all reports missing tools.
- Non-vacuity:
  - turning the suffix branch off failed 3 backend tests;
  - turning half-up into strictly-greater failed the rounding vitest;
  - both were reverted with `git checkout`.
- Not run: full suites (scoped tier); layout evidence (no build or dev server here, and the brief says no demo
  prepare). The `kobo-opportunity` capture, the WK-6 row and the opportunity page's real layout are unverified
  until G2.

## Known deviations

- **KD1. Failed-read Tariff text.** The ruled "Not available yet · the declared price could not be loaded" fails
  the missing-claim orphan scan. Every "not available yet" string must be a catalogued `mock_gaps` placement through
  `<MissingClaim>`, and the scan's own rule keeps runtime read failures out of the gap catalogue. I did not loosen
  the guard or catalogue a read failure as a gap. I used the precedent wording of `SiteFinancials.tsx`
  `PRODUCTIVE_NOT_LOADED`: **"The declared price could not be loaded, so none is assumed"**. Accepted by the coordinator (matches the WALK1-3 re-review precedent).
- KD2. CONFLICT on the price series is treated as "could not be loaded" (no single price). `SiteFinancials` shows
  CONFLICT as "not declared".
- KD3. The price read has no `validAt`, so the server default applies; `recordedAt` = the page's single `known_at`.
- KD4. `.ai/CODE_STATE.md` / `ACTIVE_CONTEXT.md` not updated (coordinator at merge, as WALK1-3b L5).

## Open questions / residual risk

- **Q1, resolved** under the standing POLISH Addendum 8 Q3/Q4 ruling (R662): "Gross sales what-if", "No what-if linked",
  "No load what-if", "Linked what-if (name unavailable)" and "{amount} · what-if". The opportunity page now renders no
  "scenario" word. Pinned tests are updated, and the strings are added to R655/R686. After the change: the two vitest
  files 79 passed, tsc clean, `test_mock_deviation_labels.mjs` 14/14, check-all 12/12.
- `kobo-opportunity` assumes the renewable page reached from the board shows an opportunity link. With Kobo's
  sparse story days a 5-day study may not hold 5 assessed days, and then no opportunity may exist ("Opportunity
  decision unavailable for fewer than five assessed days"). Both the capture and WK-6 fail loudly in that case.
  This depends on data and needs WALK1-4's readings.
- The real-data spare-solar texts depend on WALK1-4 (D-W1-10 binding fix, v6/v5 readings).

## User-review focus

No separate task file. Per the W1 rule, the owner sees this in the combined walkthrough after G2. No Architect items remain open.

## Fix round 1 (review-WALK1-5: M1, M2, L1, L2)

- **M2 + L1:** `site_outcomes/mini.py` new `renewable_bounds` (shared with `_depth`) and `renewable_href`; the Productive use
  contributor and the `SIGNAL:PRODUCTIVE_USE_HEADROOM` issue link to `/sites/{c}/performance/renewable?from=&to=` with the
  5 Site-local-midnight bounds `_depth` reads (bare link if the zone is refused). `renewableWindowFromParams` already takes
  `from`/`to` as-is, so the page opens that window and the opportunity link shows. Tests: `test_walk1_5_solar_window.py`
  (link equals 21:00Z bounds for both contributor and issue), `miniRenewableRoutes.test.tsx` (the link's window is 5 days).
  `kobo-opportunity` hops are unchanged (hop 1 now lands on the windowed page); comment updated.
- **M1:** WK-6 takes its list bounds from the board's served Productive use link (Site-local midnights, so no tz guess),
  asserts the span is 5 days and `opp.last_day == S+1`. Test: `_local_day` accepts the link bounds and refuses UTC midnight
  (the old window).
- **L2:** WK-6 no longer builds a Tariff string; it asserts the served price fields (PRICED, value > 0, currency) and returns
  them; wording stays with vitest and the capture.
- Not run here: the G2 finish/capture on a real build.
