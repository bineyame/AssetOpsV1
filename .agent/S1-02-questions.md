# S1-02 questions for the Architect (Implementer, 2026-10-08)

**Answered 2026-10-08:** see `.agent/architect-S1-02-answers-2026-10-08.md` (decision `D-2026-10-08-s1-bindings-roles-and-snapshot`). The PROPOSED values below are superseded by those answers.

The packet says to convert legacy `signal_mappings` only after explicit role,
unit and conversion decisions. None is recorded in `.ai/DECISIONS.md`, the S1-01
addendum or the technical design (which says only "role vocabulary is
code-owned per domain/analytic"). The binding storage, publication, validation,
snapshot, Readiness and SLD mechanism does not depend on these answers and is
built. The answers decide one code-owned vocabulary module
(`backend/assetops_backend/sites/binding_roles.py`) and one conversion fixture
(`backend/conversions/kobo-001-bindings.json`). Both are built to the
**proposals below, marked PROPOSED**. The conversion has **not** been applied to
the developer database; it has run only against the disposable test database
and a scratch database.

Each question gives the options and the Implementer's proposal. The proposal is
not a decision.

## Q1. The MINIGRID role vocabulary and which roles Readiness requires

The packet names generator state/power, feeder demand and battery reserve. The
demo also traces battery SOC.

Proposal (`minigrid-roles-1`):

| Role | Asset type | Canonical unit | Cardinality | Required |
| --- | --- | --- | --- | --- |
| `generator_state` | GENERATOR | `state` (enum) | one | yes |
| `generator_power` | GENERATOR | `kW` | one | yes |
| `feeder_demand` | LOAD | `kW` | one per declared LOAD asset | yes, every declared load |
| `battery_soc` | BATTERY | `%` | one | yes |
| `battery_reserve` | BATTERY | `%` | configuration | yes, see Q3 |
| `pv_power` | INVERTER | `kW` | one | no |
| `pv_irradiance` | PV_ARRAY | `W/m2` | one | no |
| `battery_power` | POWER_CONVERSION_SYSTEM | `kW` | one | no |
| `fuel_level` | FUEL_TANK | `L` | one | no |

Options:
- (a) The proposal.
- (b) Battery SOC is not a required configuration role in S1.
- (c) A different name set. For example, the legacy analytic's labels ("Generator state", "Load", "Battery state" and so on).

## Q2. Generator state: Kobo declares no generator status channel

`var/sites/kobo-001.yaml` declares only `generator-controller / ac-power`. The
newer Site documents (`gondar-01`, `sitet26`) also declare
`generator-controller / status` (unit `state`), which the dispatch analytic
reads. The packet demo says "trace generator controller status".

Options:
- (a) Proposed. The first conversion is a joint, atomic Foundation-plus-binding publish. It adds the declared signal `status` (unit `state`, "Generator status") to the `generator-controller` device in every current Foundation period from the binding effective time. It then binds that signal as `generator_state`. This is the "first atomic Foundation-plus-binding snapshot". No new source is registered, because the signal belongs to the existing generator-controller report stream.
- (b) Bind nothing for generator state. Kobo Readiness permanently names "generator state: no channel bound" until a later device-authoring slice.
- (c) Derive generator state from `ac-power` (a threshold conversion). The Implementer advises against this: it is an analytic choice, not a binding.

## Q3. Battery reserve: a binding or the configured control?

Kobo has no reserve channel. Its reserve is the Foundation property
`reserve-state-of-charge` (30%). The legacy analytic reads a POLICY signal,
`battery-pcs-controller / policy-reserve-soc`, which Kobo does not declare.

Options:
- (a) Proposed. Readiness reports battery reserve as covered by the configured Foundation control and cites the Foundation revision. There is no channel binding. A Foundation without the property (KOBO-GAP-001) names it as missing.
- (b) Battery reserve requires a POLICY channel binding. It stays unbound for Kobo until a channel is declared.

## Q4. Units and conversions

Proposal: the canonical unit is fixed per role (Q1). The source unit must equal
the unit the Foundation declares for that signal. Conversion kinds:
- `IDENTITY`: source unit is the canonical unit.
- `LINEAR`: decimal-string `scale` and `offset`, numeric roles only.
- `ENUM`: a map from source labels to the canonical states `STOPPED`, `STARTING`, `RUNNING` and `FAILED`, used by `generator_state`.

Every Kobo legacy mapping is `IDENTITY`: kW to kW, % to %, W/m2 to W/m2, and L
to L. `generator_state` uses `ENUM` with the identity label map.

Is a source unit that differs from the declared signal unit (for example W
declared and kW canonical, with LINEAR scale 0.001) allowed in S1? Or is
IDENTITY plus ENUM enough? The build accepts LINEAR. It refuses any source unit
that differs from the declared unit.

## Q5. When the first binding set takes effect

Options:
- (a) Proposed. Effective from the imported Foundation's original `valid_from`, the basis of the legacy mappings, and open-ended. Recorded now.
- (b) Effective from conversion time, so earlier periods have no binding set and show Unknown/unbound.

## Q6. Snapshot persistence (recorded deviation, confirm)

The snapshot is derived deterministically from immutable rows: the Foundation revision row with its persisted `content_sha256`, and the binding set revision with its persisted `bindings_sha256`. Its canonical bytes and SHA-256 are therefore reproducible for any earlier pair. No separate snapshot table is written.

"Authenticated" download currently means the product request boundary (the fixed development tenant), because no product authentication or gateway credential exists until S2.

Confirm, or require a persisted snapshot row and a gateway-credential route now.
