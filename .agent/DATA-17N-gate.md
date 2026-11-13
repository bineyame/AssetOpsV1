# DATA-17N gate (STOPPED at prepare: SELF-CHECK FAILED)

- Branch task/DATA-17N-coverage; `git merge main` clean (no conflicts).
- Prepare on assetops_polish_data17n_test: started 03:41 UTC, ended ~05:49 UTC 2026-11-13 (about 2 h 08 min). Log var/polish_data17n-prepare.log.
- Self-check (var/polish_data17n/check.json, 54 rows): 52 pass, 2 fail, 0 skipped. Log ends `SELF-CHECK FAILED`.
  - CO-10 (EV): AssetionError lists one extra CONNECTOR_OUT_OF_SERVICE row, "Connector c1 out of service" (EV-LAB-001, RISK, '7 h 44 min out and 16 min unknown on 10 Nov', price_needs 'Needs the bus roster', href /sites/EV-LAB-001/performance/availability); the check expected it not to appear in the list it asserted on.
  - F-COH (Portfolio): "COH-17 None month: a Portfolio card holds the sum of an unexplained-fuel amount and another amount: ['300.00']".
- Items 1-6: NOT RUN (stopped per rule: log shows FAILED). DBs left in place.

## Items 1-6 (run after coordinator go-ahead; API reads, no Chrome on VPS)
1 DATA-5: PASS. gateway_diagnostic rows Cold 8, EV 3, Kisiwa 21; 0 refusal rows; 0 rows observed>received+5s; 0 future received_at; receipt lag min 0.11 s, max 15.33 s. source-health 200 on all three (states NOT_ALL_CURRENT/OLD/STALE; no unknown-age or untrusted-clock marker). UI lines not seen (no browser).
2 DATA-10: FAIL. One Kisiwa plan "Generator 250-hour service", CALENDAR, due 2026-11-20 21:00Z = 21 Nov 00:00 EAT (S+10d), state DRAFT. outcome-board 11 Nov and 17 Nov: warning PLAN_DUE_SOON "Due 21 Nov" present, but Protect > Generator contributor still reads "No preventive plan recorded".
3 DATA-13: PASS. due_at = raised_at + 14 d: Cold 11 Nov->25 Nov, EV 10 Nov->24 Nov, Kisiwa 6 Nov->20 Nov; Kobo none. None overdue on 17 Nov.
4 DATA-8: PASS. productive_use_price_per_kwh 0.25 USD (Kobo and Kisiwa rows). Kisiwa Grow on 11 Nov: "120 kWh used by Cold store, Water pump in 48 measured hours" + "No objective declared". KIS-1/6/7 pass in check.json.
5 DATA-4: PARTIAL. EV Grow line present on 10 Nov: "3% of declared charging capacity - 15 kWh ... 60 kW" (absent on 11 Nov). Recaptures NOT RUN (no Chrome; capture tool uses a Windows path).
6 Postgres files on assetops_data17n_test: running detached via setsid (script scratchpad pg.sh); results in var/pg_summary.txt (ends with DONE) and var/pg_<file>.log.
API serve I started (PID 1444498) was stopped. DBs not dropped.
