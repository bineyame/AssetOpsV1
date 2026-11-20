> Finished; historical. Archived from .agent/DATA-17N-packet.md on 2026-11-18 (declutter step 4).
# DATA-17N coverage — lane B packet (2026-11-12, VPS update 2026-11-13)

Branch `task/DATA-17N-coverage`, worktree `/opt/assetecon/AssetOpsV1-data`. Scope: D-17N.4 / rev 7 §7.4; item
specs in `architect-answer-non-kobo-sites-2026-11-10.md`; rulings D-DATA.1-6 (`build-sheet-OWN-GAPS-2026-11-08.md`).
main merged twice on 2026-11-13 (`53de574b9`, then `6f8bb3403`), no conflicts.

## Per-item status

| Item | Commits | Status |
|---|---|---|
| DATA-5 | `b5f58bec3`, `cd3cdf183` (D-DATA.2) | built, no-DB tested; **scratch prepare pending**. Forwarded diagnostics are received on `story_diagnostics.gateway_clock`, the gateway process's real UTC clock (`assetops_gateway.service._utc_now`; the process runs with no clock override). All three paths use it: Cold `w202.DIAGNOSTIC_CLOCK = gateway_clock`, EV `diagnostics_router(URL, gateway_clock)` and the Kisiwa replay `diagnostics_service(URL, gateway_clock)`. Kobo forwarding stays off (D-DATA.1). |
| DATA-10 | `5933243e1`, `9b13a8dc6` (D-DATA.4) | built, no-DB tested; **prepare pending**. Due is `S+9d 21:00` UTC, which is S+10d 00:00 Africa/Dar_es_Salaam (story tokens are UTC; the test pins the local date and midnight). |
| DATA-13 | `ecf2d153a` | built, no-DB tested; **prepare pending**. Rule confirmed (D-DATA.3); Kobo unchanged. |
| DATA-8 | `0926c7ae9` | built, no-DB tested; **prepare pending**. KIS-1 checked: `price_selection` reads `fuel_cost.PRICE_KEY` only, and the KIS-2 SQL filters `assumption_key = 'diesel_price_per_litre'`, so no change is needed. No MG-1 (D-DATA.6). |
| DATA-4 | `b58bb0a9a` (A/B), `4e334b878` (C), plus the w503 key list in the packet commit | built, no-DB tested, EV Postgres files green; **prepare pending**. |

## DATA-4 (D-DATA.5) as built

- **A.** `analytics/ev_availability.py` rows gain `connector_rated_kw`, `charger_asset_id` and `charger_rated_kw`:
  the decimal text of the stored value (e.g. "60.0"), with the SIGNAL parent taken from the same revision's topology.
  The frontend's exact `ev-depth-1` connector shape (`evDepthClient.ts`) also had to take the three keys. Otherwise EV
  Availability would read "unexpected shape": the spec says "additive", but the client checks exact keys.
  `test_w503_ev_availability_postgres.ROW_KEYS` is extended to match.
- **B.** `site_outcomes/ev.py` gains `charger_use(kwh, availability_body, limit_kw, rc)`. It replaces the constant in
  `compose` and in `_charging_from_claim` (which uses the claim's kWh). The CH-5a1 EV golden is regenerated: its window
  has no session assessment, so the text becomes `NO_SESSION_ASSESSMENT`.
- **C.** The feeder meter reads "At each connector" and carries `data-ev-declared`. The empty slot's second line is
  dropped. The footnote uses the Architect's words. Two guards fired, and both are handled without loosening them:
  - "Reporting is not assessed on this diagram" matches a missing-claim cue. It now renders through
    `G-sld-reporting-status` at a **new registered placement** `sld.diagram.ev-undeclared-note` (registry and
    `gapCatalogue.ts`), because a placement may render only once.
  - The footnote's "load manager" hits the W1 term `load`. The exact footnote phrase is added as a W1 gloss in
    `productVocabulary.json`, citing D-DATA.5.

  The slot count is unchanged (11 `data-ev-slot`).
- **Interpretations for the reviewer to confirm:**
  1. A charger reads "charger rating not declared" when no rating is declared for it and any of its connectors lacks
     a rating, and also when any scheduled unit has no rating. A partial capacity would overstate the share.
  2. With several chargers, `{h}` is the sum of their scheduled hours.
  3. Under the import-limit cap, capacity is scaled by limit / rating sum, and the line ends "at the {limit} kW import
     limit". No words were specified for the capped case.
  4. When the overview read fails, the line reads `NOT_LOADED`, not `NO_SESSION_ASSESSMENT`.

## Checks run (VPS, 2026-11-13, after the second main merge)

- **No-DB backend/host.** Every non-Postgres test file importing a changed module (107 files, `-n 4`):
  **1792 passed, 113 skipped, 1 failed**. The failure is
  `test_dd1b2b_drain_failure::test_a_degraded_prebuild_tick_does_not_stop_the_serve_loop` (`KeyError: 'sites'`). It
  fails the same way on main `6f8bb3403`, so it is pre-existing and not from this branch.
- **New or changed tests:** `test_data4_charger_use.py` (8), `test_data5_story_diagnostics.py` (8),
  `test_data10_kisiwa_service_plan.py` (6).
- **Postgres** on own `assetops_data17n_test`: `test_w503_ev_availability_postgres.py` and
  `test_out_c4_ev_warnings_postgres.py`, **16 passed** (139 s).
- **Frontend vitest:** evFoundation, evDepth, MissingClaim, siteFoundationRevision, siteConfiguration, foundationScreen
  and coldFoundation, **321 passed**. `tsc --noEmit` is clean.
- **Guards run singly:** missing-claim scan PASS (its fixtures 26/0), frontend hard-wiring PASS, mock-deviation labels
  OK. check-all: for coordinator.

## Scratch prepare (NOT run: it runs after the owner's 06:50 UTC walkthrough; about 3 h; one heavy job at a time)

The DB name must match `DB_RE` `^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$`, so the old `<prefix>_audit*` name
cannot be used. Never use `assetops_polish_vps1_test`.

```
cd /opt/assetecon/AssetOpsV1-data
W=/opt/assetecon/AssetOpsV1-data
export PYTHONPATH=$W/backend:$W/backend/tests:$W/contracts:$W/simulator:$W/gateway:$W/field:$W/host:$W/tools:$W/host/tests
export PYTHONUNBUFFERED=1 ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python
setsid nohup pwsh -NoProfile -File tools/keep-awake-during-tests.ps1 > /dev/null 2>&1 &
setsid nohup /opt/assetecon/AssetOpsV1/.venv/bin/python tools/demo_combined.py --db assetops_polish_data17n_test \
  --work var/polish_data17n prepare > var/polish_data17n-prepare.log 2>&1 &
```

Cap the run at 2x its expected time and stop and report if it runs past that. The run is finished when every row in
`var/polish_data17n/check.json` passes and the log ends without `SELF-CHECK FAILED`. Then, on that DB:

1. **DATA-5 / D-DATA.2.**
   - `SELECT s.site_code, count(*) FROM gateway_diagnostic d JOIN site s ON s.id = d.site_id GROUP BY 1`: Cold, EV and
     Kisiwa > 0, with no `gateway_diagnostic_refusal` rows for them.
   - `SELECT count(*) FROM gateway_diagnostic WHERE observed_at > received_at + interval '5 seconds'` = 0, and no row
     has `received_at > now()`.
   - Health on the three Sites returns 200, with no "Unknown age" line and no clock-untrusted line. "Stale" is
     accepted.
   - Report the receipt lag (`received_at - observed_at`, min and max).
2. **DATA-10.** One Kisiwa `maintenance_plan` "Generator 250-hour service", due S+10d 00:00 EAT. Overview › Protect
   no longer reads "No preventive plan recorded", and the plan reads DUE_SOON on Mon 17 Nov.
3. **DATA-13.** `domain_action.due_at` = raised_at + 14 d for the Cold, EV and Kisiwa story Actions. List each
   Action's `raised_at`, `due_at` and state on Mon 17 Nov; overdue ones go to the presenter notes. Kobo Actions have
   no due date.
4. **DATA-8.** Kisiwa `financial_assumption` `productive_use_price_per_kwh` is 0.25 USD. Grow shows productive-use
   sales and "No objective declared". KIS-7 item 3 must pass (never set it to report-only); KIS-1 and KIS-6 are green.
5. **DATA-4.** EV Overview › Grow on the story day shows "{p}% of declared charging capacity …". Recapture the EV
   Overview and Foundation pairs. Recapture the Kobo Health pairs, which must equal the previous capture (D-DATA.1).
6. **Postgres files**, one at a time, on `assetops_data17n_test`:
   - `test_w202_cold_replay_postgres.py`
   - `test_w205b_ev_replay_postgres.py`
   - `test_k1_kisiwa_site_postgres.py`
   - `test_w504_ev_work_producer_postgres.py`
   - `test_walk1_productive_producer_postgres.py`

   Afterwards, drop `assetops_polish_data17n_test` and `assetops_data17n_test`.

## Open questions

- None blocking. Please confirm DATA-4 interpretations 1-4 above, the new gap placement and the vocabulary gloss.

## Residual risk

- DATA-8 gives Kisiwa a measured `productive_kwh` subject. The Grow/Optimize rows and any PRODUCTIVE_USE_HEADROOM
  opportunity may change, and only the finish check proves them.
- DATA-5 adds one diagnostic post per cadence slot to each delivery pass. The added prepare time is not measured.
- No EV finish row reads "Charger use": a grep found the old text only in the CH-5a1 golden.

## Fix round (review L1-L3)

- L1 fixed: `charger_use` (ev.py) prints, when the import limit caps the sum, the hours the limit alone would need for the same capacity (capacity / limit), so "limit x hours" is the capacity behind the percentage; uncapped it prints summed charger-hours. Tests: one charger, several chargers with equal and unequal hours, with and without the limit (`test_data4_charger_use.py`).
- L2 fixed: the two stale comments now say "the gateway's own clock".
- **Architect question (L3, unchanged):** `SiteSingleLineDiagram.tsx:1722` footnote always says "Energy is metered at each connector", but the feeder meter slot says "At each connector" only when every connector declares a meter. Should the footnote be conditional, or is it acceptable as verbatim Architect words?
