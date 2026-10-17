# W2 design review - D-2026-10-17-w2-design

Reviewer: fresh Claude reviewer (independent; did not author). Target `.agent/architect-W2-design.md` at 648f728c, judged against `.agent/architect-W2-design-request.md`. Read-only spot checks; no suites run (as instructed).

## Verdict: RETURN (small amendment)

Two Medium findings, both in the simulator-to-evidence seam and in slice sizing. Domain claim rules, W1 reuse, mockup fidelity and W2-01 are sound. W2-01 does not depend on either Medium, so the Planner can start on it while the Architect amends the design.

## Findings

**M1 - The ordinary gateway/S2 path cannot carry W2 event records today, and the design does not plan the change.** Severity Medium (acceptance gap against request item 3).
- `contracts/assetops_contracts/source_envelope.py:110,117,126`: envelope measurements are `STATE_AT_INSTANT`/`INTERVAL_MEAN` only, and `OPERATIONAL_RECORD_KINDS = {"OVERRIDE_COMMAND"}`. Envelopes have no correlation or session identity field.
- The design needs these records to arrive as accepted evidence: EV session start/end/outcome/fault records correlated "by scoped charger/connector/session ID", and cold manual-log/door/start-request observations. Yet it says the path "continue[s] through SQLite outbox, authenticated Batch V2, S2 receipt and AcceptedEvidence". For W2-02/W2-05 it gives the migration as "only if persisted schema needs it".
- Why it matters: without a planned contract change, the Implementer either encodes sessions as discrete states without identity, which breaks the correlation and duplicate-quarantine rules, or extends the envelope ad hoc inside a pack slice. The second option changes S2 acceptance, normalization and AcceptedEvidence storage without design or review.
- Fix: add an explicit seam and slice phase (before W2-05, and before W2-02 if cold needs record kinds) for the envelope schema version or new record kinds, the identity/correlation field, the gateway mapping allowlist (`simulator/assetops_simulator/gateway/mappings.py` is fuel-only), S2 normalization, typed AcceptedEvidence storage and the migration. Also state which cold signals fit schema 2 discrete/measurement as they are.

**M2 - W2-05 is oversized, and the cost of pack dispatch is hidden.** Severity Medium (request item 4: S or M, at most two phases).
- W2-05 bundles the EV Foundation, bindings and topology, a new pack, Lab/gateway replay with four case types, the vendor-format peer, and three UI screens, all as one M. With M1 added it is well past M. W2-01 through W2-02 split the same scope for cold into an S and an M.
- Pack selection is hard-wired: `host/execution_adapter.py:113-121`, `host/lab_execution.py:119-120` and `simulator/assetops_simulator/kernel/execute.py:96` import the fuel/mini-grid packs directly. Neither W2-02 nor W2-05 names generalising this dispatch.
- Fix: split W2-05 into W2-05a (EV Foundation + `ev-foundation`/`ev-readiness`/`ev-sld`, S, mirroring W2-01) and W2-05b (EV producer + replay + peer, M). Name the host/kernel pack-dispatch change in W2-02.

**L1 - W2-01 code-reality items the Planner should list** (Low, does not block; the design already tells the Planner to state the exact schema change).
- `backend/assetops_backend/sites/models.py:26`: `SITE_TYPES` omits `EV_CHARGING`, although DB CHECK `0001_foundation_identity.py:66` allows it. The design says to "keep" both, as if both already exist.
- `models.py:32-45`: `COMPONENT_TYPES` has `COLD_ROOM` and `METER` but no probe, compressor, transfer switch, charger or connector.
- `models.py:50`: `RATING_UNITS` lacks `degC`, so the 2-4 C policy band has nowhere to live. The contract layer already has `degC` (`execution_contract.py:478`).
- These are mostly closed Python vocabularies rather than DB migrations. W2-01 should say which apply.

**L2 - Missing owner questions** (Low).
- (a) The mock marks every EV screen as "extrapolated (v6.9 has no EV section)" (`screens.js` ev/sessions entries), so "fidelity to the mockup" is weaker for EV. The owner should know this when choosing all 22 or cold-first.
- (b) Is a labelled vendor-format physical peer required in W2 for both domains, or can it be deferred? It adds scope to W2-02 and W2-05.

## Answers to the six questions

1. **Gateway/S2 genuineness and no private truth:** Yes for cold measurements (private world vs public device transform, Stage/Commit, outbox, receipt, exact accepted IDs, no direct seeding). Not yet for EV session records and cold event records: see M1.
2. **Fail-closed and W1 reuse:** Yes.
   - The rules are fail-closed: temperature is never spoilage, intervals are bounded (no interpolation), no gap bridging, each missing causal step is reported, incomplete sessions are unknown rather than failed, a tariff is a scenario rather than collections, nothing is summed across overlapping Findings, late evidence makes the prior revision stale, and gateway contact is never status.
   - The W1 contracts are reused correctly: Foundation and bindings, S4-05 provenance and labels, LR money gates, the plain default reading, and the separate Analysis destination. The rail rule is implicit (W1 Site shell), which is acceptable.
3. **Slice order:** The order is sound (cold config, then producer, assessment, site/money; EV the same). Every slice has at most two phases. Migrations are named per slice, but the envelope/S2 contract change is missing (M1) and W2-05 is too large (M2).
4. **Mockup fidelity:** Holds. Each UI phase carries the v69 content/placement check, 1440/390 behaviour and a vocabulary scan. The design honestly reconciles the mock's sessions 120 kWh/3.6 kWh inconsistency and the cold sampled bounds against `screens.js`. Panels that depend on work cases are honest gaps.
5. **W2-01 ready for the Planner:** Yes, with L1 folded into the packet. Its scope is configuration only and touches neither M1 nor M2.
6. **Owner questions:** The right three (scope, core panels, demo targets, each with a recommendation). Add L2(a) and (b).

## Checked and confirmed
- Registry W2 manifest is exactly the 22 IDs. All 20 existing nodes the design cites are present and `open`. The proposed nodes are not inserted, so the checker is not affected.
- The decision is recorded at `.ai/DECISIONS.md:5,53`, and it does not promote panels or record owner acceptance.
- The cited paths exist: packs (`fuel.py`, `mini_grid.py`, `minigrid.py`), `config/scenarios/*.yaml`, `host/gateway_publication.py` and `runs/profiles.py` (`MODEL_PROFILES` at :2021).

## Not verified
- The registry checker was not run (no registry change).
- Mock panel numbering against `v69-panel-contracts.json:912-1000` was not checked line by line.
- `.agent/architect-W2-design-log.txt` (2214 lines) was not read.
