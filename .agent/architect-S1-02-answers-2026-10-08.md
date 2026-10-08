# S1-02 Architect answers — 2026-10-08

Author: **Codex Architect**, per `.ai/ROLE_CONFIG.md`.

This is an architecture decision response, not implementation acceptance, owner acceptance, or the later combined S1 review. The established review/test results are taken as given; no tests were rerun. References below use repository-relative paths.

## Q1 — Accept (a): `minigrid-roles-1`

**Decision and reason:** Accept the proposed role names, asset types, canonical units, cardinalities and required flags, including required `battery_soc` and `feeder_demand` for every declared LOAD. The S1-02 contract names generator state/power, feeder demand and reserve, and its first demonstration explicitly traces battery SOC; the technical design §1 makes the vocabulary code-owned per domain/analytic, so legacy display labels need not become identifiers. This is configuration coverage for the supported mini-grid slice, not proof of reporting, health or sufficient evidence for every future analytic.

**Implementer change:** Keep the role table in `binding_roles.py` and the fixture's role assignments; replace PROPOSED wording with this decision ID. `ONE` remains one binding per Site for this bounded role set, not an implicit choice among multiple generators/batteries; reject ambiguity rather than choosing an asset silently. No multi-generator or multi-battery expansion is requested.

**Later-slice effect:** S2 producers and consumers must use these identifiers and units. Optional solar, battery-power and fuel roles do not authorize their later analytic screens.

## Q2 — Accept (a), as an explicit configuration addition

**Decision and reason:** Authorize declaring `generator-controller / status`, unit `state`, and binding it to `generator_state` in the first atomic Foundation-plus-binding publication across the applicable currently recorded Foundation periods. This satisfies S1-02's explicit status-channel demonstration and its first-joint-snapshot requirement without inventing a power-threshold analytic; the addendum's one-source-per-device-stream rule means the existing generator source owns the added channel. This is an Architect-authorized declaration for the planned simulated configuration, not a fact recovered from Kobo YAML or evidence that a device has ever emitted status.

**Implementer change:** Keep `declare_signals`, the null `legacy_mapping_id`, and the ENUM status binding in the conversion fixture. Replace its reason based on newer Site documents with explicit provenance citing this decision and saying that status is newly declared, absent from the original Kobo import; carry that distinction into the conversion report. Publish new immutable Foundation revisions and binding sets together under the Site lock, preserving each period's existing controls and old recorded basis; do not alter imported revision content or the YAML. No `binding_roles.py` role change is needed.

**Scope/later-slice effect:** This authorizes one narrow migration declaration, not broad device authoring. S2 must produce public status reports with the agreed enum; S1 does not synthesize reports, enable ingestion, or reopen gated Lab execution.

## Q3 — Accept (a): reserve is a Foundation control

**Decision and reason:** Cover `battery_reserve` with the selected Foundation's typed battery `reserve-state-of-charge` property, without a channel binding. The S1-01 addendum explicitly establishes this property as reserve (initially 30%) and uses its absence for the gap fixture; requiring an undeclared POLICY channel would replace that contract with legacy analytic behavior. Readiness must distinguish “configured control” from a channel “ready to report” and cite the selected Foundation revision, including later reserve edits.

**Implementer change:** Keep `covered_by="FOUNDATION_CONTROL"` and no reserve binding in the conversion fixture. Ensure missing or invalid reserve remains a named gap and prevents a complete acquisition snapshot; do not add `policy-reserve-soc` or a source for it. No further role/fixture change is required.

**Later-slice effect:** Carry reserve from the registered Foundation snapshot into S2's Lab/controller basis and later analysis; a legacy POLICY observation is not required and must not silently override the configured control. Observed controller policy, if needed later, needs a separately defined meaning and conflict rule.

## Q4 — Choose the narrower listed alternative: IDENTITY plus ENUM in S1

**Decision and reason:** Approve numeric `IDENTITY` and generator-state `ENUM`; defer publication of `LINEAR` conversions. All nine legacy Kobo mappings already use their roles' canonical units, while S1-02 requires rejection of role/unit conflicts and the technical design requires validation of units; arbitrary scale/offset strings alone do not establish a valid unit conversion. The declared Foundation signal unit must always equal binding `source_unit`: a Foundation declaration of W and binding source W/canonical kW would be internally consistent, but its conversion is outside this S1 choice; declaring W and claiming source kW is always a mismatch.

**Implementer change:** In `binding_roles.py`, remove LINEAR from accepted conversion kinds and reject it at publication (remove or clearly defer its unused validation branch). Keep numeric IDENTITY restricted to equal source/canonical units; retain ENUM with the exact canonical targets `STOPPED`, `STARTING`, `RUNNING`, `FAILED`, with source unit `state`. The fixture's nine IDENTITY mappings and one identity-label ENUM map need no semantic change; update API/documentation and affected expectations to state the supported kinds consistently.

**Scope/later-slice effect:** This narrows the proposed build without expanding S1. S2 uses only these published kinds; any later LINEAR support needs an explicit supported-unit-pair and coefficient rule plus normalization semantics before publication is enabled. Unknown enum labels must never default to RUNNING or STOPPED; S2 must give them an explicit invalid/unmapped disposition.

## Q5 — Accept (a), with period-aligned publication

**Decision and reason:** Start the first conversion at the imported Foundation's original `valid_from`, `2026-09-29T11:57:49Z`, and record it at the actual conversion transaction time. The addendum preserves that original effective basis, and S1-02 plus technical design §1 explicitly allow backdated configuration with separate recorded-time history. This records a present decision about historical configuration, including the newly declared status channel; it does not claim those bindings or that channel were known at the original import or that evidence existed then.

**Implementer change:** Keep `FOUNDATION_ORIGINAL_VALID_FROM` in the fixture. “Open-ended” means continuous coverage through the final open Foundation period: publish a matching binding set for each effective Foundation segment, not one set tied to the original Foundation across later reserve changes. Preserve old rows and their original validity, stamp actual recorded time, and let an earlier `knowledge_at` recover the previous Foundation-only/unbound state; the conversion report must explain this distinction. No role change is needed.

**Later-slice effect:** S2 resolves the cited registered Foundation/binding pair and its original valid ranges. Backdating does not release legacy stages, authorize old file-backed evidence, or rewrite any subsequently accepted envelope.

## Q6 — Do not accept hash derivation alone; accept the development boundary only as a scoped deferral

**Decision and reason:** Require persistence of the canonical acquisition snapshot hash at atomic publication; a separate snapshot table is an implementation choice, not a mandatory architecture shape. Technical design §4, “Register configuration,” explicitly says to persist that hash, and S1-02 requires old snapshots to survive edits: separate Foundation/binding hashes do not pin the published combined representation against serializer or schema changes. Accept the fixed development-tenant boundary for S1 under the addendum's explicit authentication deferral, but do not call that boundary authenticated gateway access.

**Implementer change:** Persist, in the same publication transaction, the combined snapshot SHA-256, snapshot schema/canonicalization version, and exact tenant/Site/gateway/Foundation/binding references, on a suitable immutable publication record (existing row or a small snapshot record). Retain the canonical bytes, or preserve the versioned serializer and all immutable inputs needed to reproduce exactly those bytes; hash input must exclude mutable recorded closures, request-time selection metadata and current gateway status. Download must return the pinned representation and verify its persisted hash; historical access must still resolve the original registered pair after supersession. This requires storage/publication/download changes and corresponding migration/verification coverage, but no role or conversion-fixture semantic change. Label the S1 route as a tenant-scoped development configuration download, with gateway authentication pending.

**Scope/later-slice effect:** Persisting the published hash closes an existing S1 obligation; it is not new acquisition scope. No credential provisioning, gateway-auth route or detached signature is required now. S2 must add registered gateway authentication scoped to tenant/Site/gateway/source and consume the same pinned snapshot/hash; the fixed tenant alone must never authorize ingestion.

## Proposed entry for `.ai/DECISIONS.md`

The coordinator should commit the following entry after incorporating these decisions into the implementation and its handoff. This response does not apply the conversion to the developer database.

```markdown
## 2026-10-08

Decision: `D-2026-10-08-s1-bindings-roles-and-snapshot`. Codex Architect, resolving the six S1-02 Implementer questions under `.ai/ROLE_CONFIG.md`. This is an Architect contract resolution, not owner slice acceptance or the combined S1 review. Detailed rationale and implementation directions are in `.agent/architect-S1-02-answers-2026-10-08.md`.

Adopt `minigrid-roles-1`: required generator_state (GENERATOR/state), generator_power (GENERATOR/kW), feeder_demand (LOAD/kW, every declared load), battery_soc (BATTERY/%) and battery_reserve (BATTERY/%, Foundation control). Other channel roles are optional: pv_power (INVERTER/kW), pv_irradiance (PV_ARRAY/W/m2), battery_power (POWER_CONVERSION_SYSTEM/kW), fuel_level (FUEL_TANK/L). Channel roles other than feeder_demand permit one binding per Site in this slice. Coverage is configuration only, never observed health or reporting.

Explicitly authorize adding generator-controller/status (state) to the registered simulated Kobo Foundation during the atomic conversion. It uses the existing device source and is recorded as a new declaration, not original YAML content or an observed capability. Preserve the original YAML, immutable import revisions and all period-specific control values. Battery reserve remains the selected Foundation's typed reserve-state-of-charge property; no POLICY channel or reserve binding is required.

S1 accepts numeric IDENTITY with equal declared/source/canonical units, and generator-state ENUM targeting STOPPED, STARTING, RUNNING and FAILED. Source unit must always match the Foundation declaration. Defer LINEAR publication until supported unit pairs, coefficients and normalization rules are decided. Kobo retains nine legacy IDENTITY mappings plus the explicitly added status ENUM mapping.

The conversion is effective from 2026-09-29T11:57:49Z and recorded at actual publication time, with Foundation-aligned binding periods through the final open period. Earlier knowledge_at reads retain the former Foundation-only basis. Backdating config does not establish historical observations, release legacy evidence or mutate accepted envelopes.

Persist the canonical combined snapshot SHA-256, schema/canonicalization version and exact registered references in the atomic publication. A separate table is optional; exact historical bytes must remain available or reproducible under a preserved versioned serializer and checked against the stored hash. Independent component hashes alone are insufficient. S1 download uses the fixed development-tenant boundary and is explicitly not authenticated gateway access. S2 adds scoped gateway credentials and consumes the same immutable snapshot contract; detached signatures remain deferred. Broad device authoring, acquisition, analytics and reopening imported Kobo Lab execution remain outside S1-02.
```
