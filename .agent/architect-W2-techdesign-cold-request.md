# Architect request - W2 technical design, part 1: shared source-format extension + cold-chain (2026-10-17)

You are the AssetOps Architect (Codex). Owner (verbatim): "make sure the architect creates proper technical design and not leave too much to the implementer architecturally and technically." Also: be token-efficient - one pass, concise, tables over prose, cite path:line.

Inputs: your `.agent/architect-W2-design.md` (`D-2026-10-17-w2-design`), the review `.agent/W2-design-review.md` (M1 envelope/record kinds, M2 split W2-05, L1 model gaps, L2 owner questions), and the code it cites: `contracts/assetops_contracts/source_envelope.py`, `simulator/assetops_simulator/gateway/mappings.py`, `host/execution_adapter.py`, `host/lab_execution.py`, `simulator/assetops_simulator/kernel/execute.py`, `backend/assetops_backend/sites/models.py`, the S2 intake/accepted-evidence code, `backend/migrations/versions/` (head `0019_verification_core`), the S3/S4 assessment/Finding store, S4-05 provenance, and the v69 cold screens.

Deliver:
A. Amend `.agent/architect-W2-design.md`: add the shared source-format slice (W2-00, before W2-02/W2-05) for M1; split W2-05 into W2-05a (EV Foundation + 3 screens, S) and W2-05b (EV pack/replay/adapter, M); W2-02 names the host pack-selection change; add the two L2 owner questions with recommendations.
B. Write `.agent/W2-technical-design-cold.md` - an implementable technical design, so Planner packets only sequence and test it. For W2-00 and W2-01..W2-04 specify:
 1. Source envelope v-next: exact new measurement/record kinds, fields (incl. session/event identity and correlation), versioning and backward compatibility, validation and refusal codes, gateway mapping allowlist changes, S2 intake/dedup/accepted-evidence storage changes.
 2. Data model: every new/changed table, column, type, constraint, index, FK, immutability trigger, and the migration sequence (numbered after 0019) with downgrade rules; `models.py` enum additions (site type, component types incl. probe/compressor/transfer switch, `degC` unit, policy band).
 3. Foundation/bindings: the cold role set (names, kinds, units, cardinality), validation rules and readiness messages.
 4. Simulator: cold thermal pack - state variables, equations/update rules, parameters and defaults, door/compressor/power-loss/backup behaviour, probe failure; scenario files and Lab publication profile (versions, channels, cadences, semantics); host pack-selection change; deterministic seeds; how each demo case (normal, excursion, backup start chain, missing probe, late reading, contradictory) is produced.
 5. Assessment rules: excursion definition (band, duration, hysteresis), backup start-chain claim, evidence sufficiency/coverage, currentness and recompute, Finding episode identity and revisions, claim levels, fail-closed cases.
 6. Money: consequence model inputs, assumptions, units, gates (unpriced/withheld), no stock value unless declared.
 7. Reads/APIs: each new route with request params, response shape (fields), refusals (401/403/404/409/422/503), currentness/watermark, paging.
 8. UI mapping: each cold screen panel (v69 numbering) to its read fields and shared W1 components, with honest gap states.
 9. Tests/fixtures per slice: the replay manifest(s) and the exact cases each slice must prove.
Keep part B <= 400 lines; reuse W1 contracts by reference instead of restating. Record `D-2026-10-17-w2-techdesign-cold` in `.ai/DECISIONS.md`. Leave the registry unchanged unless the checker stays valid. No code. Print a short summary.
