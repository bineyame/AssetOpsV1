# CH-6b3 handoff

- **State:** rulings CH6b3-R in `.agent/build-sheet-CH-6.md:833`. Committed: Q4b + L1 test (`7c508b132`), COH-17 table, COH-18, collector, fixtures `clean_full` / `coh18_day_grades` (`0e215cbcf`). L0 133 pass. L2m test added.
- **Next:** polish clone L3 (running, log `var/ch6b3_l3.log`, clone `ch6b3`, work `var/ch6b3work`, bundle `var/ch6b3_bundle`, drop afterwards); one template rebuild (`mechanism_dataset.py ensure`), L2m (`test_ch6b_estate_postgres.py`), L3m; register R707; packet; remove the `frontend/node_modules` junction non-recursively (it points into plan2).
- **Anchors:** `tools/checks/chain_coherence.py` `_coh17_full`, `coh18_day_grades`, `info_coh17_period_nodes`, `Collector.day_bodies`; `backend/assetops_backend/estate/portfolio.py` `priority_site_count`.
- **Alive:** clone `assetops_chainclone_ch6b3_test` until L3 is read. Mechanism templates stale (`usable: false`), not yet rebuilt.
