# S4-02b phase 2b handoff: Financials UI, walkthrough and evidence

Branch `task/S4-02b-fuel-consequence`, commits `dbaba10`..HEAD (`git log 3793e4d..HEAD`). The slice is `in_review`; packet `.agent/S4-02b-review-packet.md`.

## Landed (anchors)

- Backend: `financials/consequence_read.py` `read(..., source_open)` → `AUDIT_ONLY`; `finding_api.py` `finding_consequences` and `bridge(...)` pass `source["permitted"]`; `REASONS` STALE / STALE_QUEUED / AUDIT_ONLY; `bridge_consequence` adds `recalculation_queued`, `currentness_reasons`; `demonstration_label.demonstration_case` feeds `demonstration` on both reads.
- Frontend: `sites/FindingConsequence.tsx` `FindingBridge`, `BridgeTable`, `HowWorkedOut`, `ConsequenceHistory`; `SiteFinancials.tsx` `SiteFinancialsOverview` (bridge, then consequences with `consequence_revision_id`), `History` appends; `FinancialsLinks.consequence`; `siteFinancialsHref(..., consequenceRevisionId)`.
- Tools: `tools/s402b_fuel_cost_walkthrough.py`, `tools/s402b-fuel-cost-evidence.mjs`.

## Reviewer setup

- Template: `assetops_s402bcases` (exists; `tools/s402b_power_cases.py run` rebuilds it).
- Evidence DBs `assetops_s402bevwalk`/`assetops_s402bevempty` (work `s402b-evidence`) are post-v4, recomputed, gate reopened. Rebuild with `prepare` before rerunning the evidence tool (it publishes v4 itself).
- Owner DBs `assetops_s402bwalk`/`assetops_s402bempty` (work `s402b-owner`) are pristine pre-v4: do not use them for evidence; owner ports 8872/8873/5372/5373.
- Evidence command: `node tools/s402b-fuel-cost-evidence.mjs http://localhost:<web> http://localhost:<emptyweb> b524cc00-3bff-40a0-b9d1-1e97ce20f8c2 edf43435-d5c9-4fec-87d4-168c3d8d4560 56400f93-edef-4ee1-b99e-36129bf7f87d 24ddcfa6-4e6a-499f-86fb-7286dca8df9e <out>` (IDs are stable across template copies).
- Scratch test DBs `assetops_s402b3_a_test`, `assetops_s402b3_full_test` may be dropped.

## Next

Fresh Claude review of 2b and the whole slice, then the S4-02 owner checkpoint (walkthrough questions 1-6), then registry/ledger closeout (`I-S4-02`, `financials:1#a`, `financials:2#a`, `assumptions:1#a`, `assumptions:3#a`) by the coordinator. Architect batch: 2a Q2, 2b Q11/Q12.

## Open risks

Demonstration label by declared day (Q11); no Site-level consequence list (Q12); fresh derivation on every read.
