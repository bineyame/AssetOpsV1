# DATA-17N gate (STOPPED at prepare: SELF-CHECK FAILED)

- Branch task/DATA-17N-coverage; `git merge main` clean (no conflicts).
- Prepare on assetops_polish_data17n_test: started 03:41 UTC, ended ~05:49 UTC 2026-11-13 (about 2 h 08 min). Log var/polish_data17n-prepare.log.
- Self-check (var/polish_data17n/check.json, 54 rows): 52 pass, 2 fail, 0 skipped. Log ends `SELF-CHECK FAILED`.
  - CO-10 (EV): AssetionError lists one extra CONNECTOR_OUT_OF_SERVICE row, "Connector c1 out of service" (EV-LAB-001, RISK, '7 h 44 min out and 16 min unknown on 10 Nov', price_needs 'Needs the bus roster', href /sites/EV-LAB-001/performance/availability); the check expected it not to appear in the list it asserted on.
  - F-COH (Portfolio): "COH-17 None month: a Portfolio card holds the sum of an unexplained-fuel amount and another amount: ['300.00']".
- Items 1-6: NOT RUN (stopped per rule: log shows FAILED). DBs left in place.
