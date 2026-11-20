> Finished; historical. Archived from .agent/DATA-17N-review.md on 2026-11-18 (declutter step 4).
# DATA-17N review (fresh Claude reviewer, 2026-11-13)

Branch `task/DATA-17N-coverage`, head `c2cc3f906`, base `bd4c0086e` (merge-base with main). Scope: DATA-5/10/13/8,
D-DATA.1-6 fixes, DATA-4 (D-DATA.5 A/B/C). Judged against rev 7 §7.4 (D-17N.4) and D-DATA.1-6.

## Verdict: ACCEPT WITH NOTES

No High or Medium finding. Three Low notes below; none blocks the merge. The scratch prepare and the Sat-night
finish check remain the data gate (D-17N.4) and were not part of this review.

## Checks run (by this reviewer)

- No-DB backend/host: 34 non-Postgres test files importing a touched module (site_outcomes.ev, ev_availability,
  CH-5a1 golden, demo_combined_{cold,ev,kisiwa}, w504 cases, demo_story_clock, story_diagnostics), `-n 4`:
  **665 passed, 23 skipped, 0 failed** (16 s). The five new DATA test files plus EV/evhb/k1/own_g1 run alone: 169 passed, 1 skipped.
- Postgres on `assetops_data17n_test` (harness-owned `_pt*_test` clones): `test_w503_ev_availability_postgres.py` +
  `test_out_c4_ev_warnings_postgres.py`: **16 passed, 0 skipped** (101 s).
- vitest: evFoundation, evDepth, siteFoundationRevision (+ MissingClaim tests): **4 files, 164 passed**.
- `tsc --noEmit`: exit 0, no output.
- Guards run singly: dependency registry exit 0; missing-claim orphan scan passed (43 tagged placements).
- check-all: for coordinator. Worktree clean; diff touches 32 files, no stray files.

## Points checked

- **D-DATA.2.** `story_diagnostics.gateway_clock` is `datetime.now(timezone.utc)`; the gateway is a real
  `python -m assetops_gateway serve` subprocess (`host/tests/gateway_process.py`) with no clock override, and
  `GatewayService` defaults to `_utc_now`. Cold (`w202.DIAGNOSTIC_CLOCK = gateway_clock`), EV
  (`diagnostics_router(URL, gateway_clock)`) and Kisiwa (`diagnostics_service(URL, gateway_clock)`) all use it; none
  uses the story `received` or the chain decision clock. Cold's `_RecordedNow` patches only the producer module during
  attest, not the gateway. Kobo forwarding stays off (D-DATA.1, pinned).
- **D-DATA.4.** `service_plan.due_at = "S+9d 21:00"` (UTC) = S+10d 00:00 Africa/Dar_es_Salaam; the test pins the
  local date and midnight, and written S-8d 09:00. Kisiwa installs last, so no other Site's PM codes shift.
- **DATA-4 frontend exact keys.** `CONNECTOR_KEYS` and `isConnector` take the three keys (nullable decimal / string);
  the only producer is `ev_availability.availability`, which always emits them, and the only other TS consumer
  (`evDepth.test.tsx`) was updated. No other fixture carries the availability shape. Safe.
- **Missing-claim placement + vocabulary gloss.** "Reporting is not assessed on this diagram" is exactly the
  G-sld-reporting-status claim; a new placement is required because a placement renders once. Registered in both the
  registry JSON and `gapCatalogue.ts`, rendered via `MissingClaim` as an inline `span` inside the `<p>` (valid). The
  gloss is the exact Architect phrase only, so `load` stays flagged elsewhere. Justified.
- **SLD slots.** No `data-ev-slot` attribute added or removed; the test now asserts 11 rendered slots.
- **Story/prepare vs finish checks.** `KIS7_ITEM3_REPORT_ONLY = False` untouched (`tools/demo_combined_rows.py:1338`);
  KIS-1/KIS-6 not touched; no MG-1. Kisiwa's `work_service` clock override in `write_service_plan` is not reused after.
- **Tests.** Not vacuous: `charger_use` covers every state, precedence, cap, claim-path kWh and the real
  `ev-lab-001` fixture through `availability()`. DATA-5/10/13 tests mix behaviour with source-string pins on the
  harness wiring; acceptable here because the scratch prepare is the behavioural gate.

## Builder calls (packet interpretations 1-4)

1. **Partly undeclared rating -> "charger rating not declared".** Accept: a partial sum would overstate the share.
2. **Hours summed across chargers.** Accept for the uncapped case (rating x summed hours = capacity when ratings are
   equal). Wrong together with the cap: see L1.
3. **Import-limit cap by limit / rating sum, "at the {limit} kW import limit".** Accept the arithmetic; the words need L1.
4. **Overview read failure -> `NOT_LOADED`.** Accept: `NO_SESSION_ASSESSMENT` would state an assessment absence that
   was never read; matches the sibling Grow lines.

## Findings

- **L1 (Low, latent wording; not on demo data).** `backend/assetops_backend/site_outcomes/ev.py:373-383`: in the
  capped multi-charger case the line prints summed charger-hours with the import limit, e.g. the test-pinned
  "50% ... 320 kWh ... in 16 h of scheduled charging at the 80 kW import limit" (`test_data4_charger_use.py`
  import-limit case). 80 kW x 16 h = 1,280 kWh, but the capacity used is 640 kWh, so the sentence contradicts its own
  percentage. The EV demo Site (one 60 kW charger, 80 kW limit) never caps, so nothing shown on 17 Nov is wrong.
  Fix: in the capped case print the longest scheduled hours (wall-clock, `limit x hours`), or ask the Architect for
  capped-case words; update the test.
- **L2 (Low, stale comments).** `backend/tests/test_w202_cold_replay_postgres.py:158` says the demo child sets
  `DIAGNOSTIC_CLOCK` to "the day's story clock", and `backend/tests/test_w205b_ev_replay_postgres.py:50-51` says
  "on the chain's decision clock". Both contradict D-DATA.2 and the code. Fix: say "the gateway's own clock".
- **L3 (Low, Architect note).** `frontend/src/sites/SiteSingleLineDiagram.tsx:1722`: the footnote's
  "Energy is metered at each connector" is unconditional, while the feeder meter reads "At each connector" only when
  every connector declares a meter. For an EV Site without connector meters the two would disagree. These are the
  Architect's verbatim words and the demo Site declares the meters, so no change now; flag for the Architect.

## Residual risk (beyond the packet)

- The Kisiwa plan is recorded at S-8d 09:00 after operational records with later recorded instants; any store
  ordering rule on recorded time is only exercised by the scratch prepare.
- KIS-7 item 3 passing depends on DATA-8's measured `productive_kwh`; proven only by the prepare/finish check.
- Frontend full suite and build not run (policy); only the touched files.
