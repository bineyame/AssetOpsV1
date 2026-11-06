# CH-6b3 handoff

- **State:** pre-flight committed; stopped for Architect rulings on Q1-Q4 of `.agent/CH-6b3-preflight.md`. No code changed.
- **Next:** apply the rulings. Build order: L1 test (Q5); COH-17 + COH-18 + collector + L0 fixtures (Q1-Q3, Q6); Q4 outcome; L2m bullets (Q7); polish clone L3; the one template rebuild, then L2m and L3m; register R707; packet.
- **Anchors:** `tools/checks/chain_coherence.py:1094` COH-17, `:166-186` collector estate reads, `:1145` RULES, `:1166` check; `tools/checks/test_chain_coherence.py:771`; `backend/tests/test_ch6b_estate_postgres.py`; `backend/assetops_backend/site_outcomes/read.py:665`.
- **Alive:** no clones, DBs or processes started by this unit. Mechanism templates are stale (`usable: false`) and not rebuilt.
