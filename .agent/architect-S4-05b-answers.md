# Architect answers - S4-05b phase 1 (2026-10-16)

Authority: `.agent/architect-S4-05b-request.md`, the S4-05 shared contract and S4-05b packet, `D-2026-10-15-s405-stored-demo-provenance`, the phase-1 handoff, and the owner's T028 presentation direction. These are interim implementation rulings. The owner still approves final visible wording at the W1 copy checkpoint before S4-05b merges.

## 1. Source wording and placement

Use these interim operator-facing labels on Finding, Evidence, consequence, Financials, and S5 Overview wherever the selected source state is shown:

| Stored state | Default label | Adjacent plain statement |
| --- | --- | --- |
| `AUTHORED_DEMONSTRATION` | `Prepared example data` | `These records were prepared for an example. They are not readings from physical equipment.` |
| `REGISTERED_SIMULATION` | `Generated test data` | `These records were generated for a test. They are not readings from physical equipment.` |
| `MIXED` | `Sources do not agree` | `The records behind this result have different or unverified sources. No current cost is shown.` |
| `UNKNOWN` | `Source unverified` | `We cannot establish the source of all records behind this result. No current cost is shown.` |

Show the label and statement together near the Finding or Evidence result and next to any eligible current amount or withheld-current-cost state. The label must remain visible without opening a disclosure, including at narrow width and to assistive technology. A positive authored or generated designation applies only to the exact selected citation set (and the consequence's additional power records), not the Site or all its records. For `MIXED` and `UNKNOWN`, do not imply the records are physical, generated, or zero cost. Historical amounts remain labelled historical and audit-only with the exact revision and its own source state.

Put the detailed per-record source, publication, fixture/version or recorded-run identity, reasons and exact IDs in the existing deeper source detail disclosure or Analysis layer. Explain the method there in ordinary language; raw API enum values and IDs may remain in machine-readable data, but do not print the enum or implementation words as product prose. The T028 vocabulary guard scans disclosures and accessible labels as well as default text. The four labels and statements above avoid its banned terms; no vocabulary exemption is authorized. In particular, `Simulated data` must not be rendered, and `Demonstration data` is replaced by the more explicit prepared-example wording. The source-owned identifier, user-owned and Lab exemptions remain limited to their existing purposes, not source-state copy. Test populated positive, mixed and unknown states with the product vocabulary scan. The final wording, placement and visual treatment remain the owner's W1-conclusion copy checkpoint.

## 2. Partly sealed registered Lab stage

Accept the phase-1 fail-closed change. A registered Lab stage may be committed only after every batch in that stage is sealed and can receive the immutable pre-admission publication. If any batch is still sealing or was refused, return `SOURCE_PUBLICATION_REFUSED` and release none of the stage. Do not publish or upload the sealed subset as an implicit partial Commit. A later explicit retry may succeed only after the whole stage meets the same rule; do not backfill or relabel already admitted evidence. Keep the refused state visible in Lab so the operator knows that no partial release occurred. This is a deliberate change from the former "as far as sealed" behavior and needs the phase-2 walkthrough/regression proof.

## 3. Action source cutover

Yes. Phase 2 must remove `demonstration_label.py` runtime use from `actions/service.py` as part of the same heuristic retirement. The recommendation and persisted Action detail must obtain source state for their exact pinned origin FindingRevision from the stored provenance resolver, preserving that revision and its evidence IDs. Do not decide an Action's source from Site, episode dates, a fixture file or the latest Finding head. If the resolver is unwired, fails, or cannot resolve the pinned revision, show `Source unverified` and the typed source limitation; do not return an authored/generated label. Keep any Action application, capability and outcome rules governed by their existing contracts; this ruling changes source presentation and its read basis only. Update Action API/UI consumers and focused regressions so no product read still uses the date/spec heuristic. The owner reviews Action-visible copy with the same W1 wording checkpoint.
