# S2-01b phase-1 questions for Architect — 2026-10-08

None of these block phase 2. Each is built on the fail-closed default named here (commit `775f8f9`). Changing any of them changes V3/Batch V2 bytes and the vectors in `contract-fixtures/source-envelope-v3-vectors.json`, so a different answer should come before phase 2 seals any reviewer-visible rows.

## Q1: Does a V3 envelope carry the original source reading or the converted one?

Technical design §3 gives `AcceptedEvidence` both `original:{value,unit}` and `normalized:{value,unit}`, and the edge `device_signal_mapping` stores `conversion_json`. Neither says which one the envelope payload holds.

- **Built (default):** the envelope carries the reading as the device published it, in the binding's `source_unit`. The gateway only validates. It holds the reading with `UNIT_INCOMPATIBLE` if the unit is not `source_unit`. For ENUM it holds with `INVALID_ENUM` if the label is not in the map, and also if the label is not publishable member text (`[A-Z0-9_]`). For IDENTITY it holds with `INVALID_VALUE` if the value is not a canonical decimal. Central S2-02 then applies the binding conversion to produce `normalized`. This is lossless. Today's two kinds, IDENTITY and ENUM, both require `source_unit == canonical_unit`, so the unit is the same either way.
- **Alternative:** the gateway applies the conversion and the envelope carries the canonical value. That is simpler for central, but `original` could then only be rebuilt from the edge.

Recommendation: keep the default. One gap: an ENUM source label that is not uppercase member text, such as `on`, would need a V3 value rule for raw labels. No current Kobo binding needs one.

## Q2: V3 POLICY and OPERATIONAL_RECORD families

V3 names `record_detail?: versioned-object`, but no record_detail contract exists. **Built:** V3 writes and reads MEASUREMENT only and refuses the other two families as `SCHEMA_UNSUPPORTED`. The registered Kobo daytime scenario publishes measurements only. Recommendation: S2-02 or a later slice defines `record_detail` before any registered policy or operator record is published.

## Q3: Foundation `valid_from` spelling in Batch V2

The snapshot writes instants with Python `isoformat()` plus `Z`, so a value with microseconds keeps its fraction. **Built:** Batch V2 `configuration.foundation_valid_from` carries the snapshot's spelling exactly (`YYYY-MM-DDTHH:MM:SS[.ffffff]Z`). Truncating it to seconds would change the reference. Envelope instants stay whole-second UTC. Recommendation: accept this. S2-02 compares the value exactly as spelled.
