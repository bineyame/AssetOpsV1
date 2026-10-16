# S4-08 handoff (build complete, in_review)

Branch `task/S4-08-assumption-history` (from main `e46bbd7c`), final code revision `46dc42cb`; docs commit after it. Not merged. Packet `.agent/S4-08-review-packet.md`.

Blocking gap: the one full backend suite hit the 30-minute cap at 63% with no failure printed (packet "Checks run"); a complete run on `46dc42cb` is still needed.

Next: fresh independent Claude slice review (merge gate). Then merge before W1-UX-02 restyles `SiteAssumptions` (packet merge order). Owner review is in the combined W1 walkthrough (`tasks/W1-UX-mockup-fidelity.md` assumptions row updated).

Anchors for the reviewer:
- Read: `backend/assetops_backend/financials/consequence_history.py` (`classify`, `ConsequenceHistoryService.read/_row`, cursor), `financials/adapters/postgres_consequence_store.py` `site_history`, `consequence_history_api.py`, `main.py` (router before the price-revision route).
- UI: `frontend/src/sites/ConsequenceHistory.tsx`, `SiteFinancials.tsx` `SiteAssumptions`.
- Proof: `backend/tests/test_s4_consequence_history{,_postgres}.py`, `frontend/src/sites/__tests__/siteFinancials.test.tsx` "Interpretation history (S4-08)".
- Walkthrough: `tools/s408_assumption_history_walkthrough.py prepare|links|serve|close-gate|open-gate|drop` (API 8968, web 5468, DBs `assetops_s408_owner|mixed`), evidence `node tools/s408-assumption-history-evidence.mjs http://localhost:5468 var/s408_owner/s408-state.json <out> owner|closed|mixed`.

Open risks: Known deviations 1-5 in the packet (LR-01 not applied to audit amounts; Finding links pin IDs not cutoff; `history_limit` in URL; Finding named by its window). Test DBs `assetops_s408_test` and `assetops_s408_pt*` dropped after the capped run; `var/sites/*.yaml` copies removed.
