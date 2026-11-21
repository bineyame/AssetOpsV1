# 4a: energy to cash, where the kWh went (implementer spec)

Status: rev 1, Architect (Claude), 2026-11-21, written on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`;
pull order `specs/OWNER-AWAY/decisions-2026-11-21.md` row 4; rows 13 to 17 for the calls made here). `delivery-plan.md`
§2 row `4a`: "Energy-to-cash observer: delivered, metered, billed, collected, with named leaks" (step 4, construct B1,
2.5 units, depends on `3A4`, `3B3`, non-screen). Off the deep-dive path (`two-week-build-plan.md` §0.1, "Not on the
path": 4a explains *where* kWh leaked, not the money gap). **3.0 units** (0.5 over the plan, D-4A.1). Discovery
review (W5): a new mechanism on the structure read, a change to the stated-node rule, kWh under a money heading.
Non-screen; adds no user-facing text (D-SC1.28; D-4A.12). `USER_REVIEW_REQUIRED: false` (the screen is `5c`'s).

- **What it is.** The mini-grid structure's energy chain (`structure/rows_mini_grid.py`): `metered_kwh =
  delivered_kwh - technical_loss_kwh - unexplained_loss_kwh`, `billed_kwh = metered_kwh - adjustments_kwh -
  unmapped_kwh`, `revenue = billed_kwh * tariff + productive_kwh * productive_tariff`, `collected = revenue -
  in_transit - outstanding`. Today six of its leaves read NOT_CONNECTED or HELD_NOT_CALCULATED (`structure/sources.py`
  `SOURCE_STATE`), so revenue's gap stops at its heading (D-5B.4). 4a observes each stage from the operator's own
  records and the feeder meters: delivered kWh from `feeder_demand` readings, metered kWh from the customer meter
  reads, billed kWh from the billing export, the leaks between them by name (expected technical loss from a declared
  band, losses beyond it, kWh on meters billing does not charge, authorised adjustments), and the tariff from billed
  money over billed kWh. Collected, in transit and outstanding are already `4b`'s.
- **Design source:** `domain-and-decision-models.md` §3.2 (the observer: mechanism, error modes `REGISTER_GAP`,
  `FEEDER_GAP`, `LOSS_BAND_UNDECLARED`, negative control, refusal); `economic-metric-and-effect-contracts.md` §2.2
  (node table, "Kobo and Kisiwa report loss as one figure ... their unexplained cell is '—', not zero");
  `integration-source-to-canonical-design.md` §1.1 rows "Service" and "Chargeable", §3.1 Trace A (Mto's meter swap,
  MAP-1), §6.4; `worked-portfolios.md` Mto "Energy to cash" table. Build plan §0.4 "Where the kWh went".
- **Owner rules kept:** unknown is never zero; a figure needing a record the operator lacks reads "Not available yet"
  naming the record (here: a code naming it; the words are `5c`'s, D-4A.12); no silent estimate; simulated readings
  never read as observed (D-4A.2); unexplained losses are never called theft and never shown as money to recover
  (D-4A.5); claim only what was tested.
- **Builds on (merged on `main` at `e844e9d18`):** `3B1` (`structure/registry.py` `FactorRow`, `FilledBy`,
  `REGISTRIES`; `rows_mini_grid.py` v3), `3B3` (`structure/sources.py` `ReadContext`, `LeafSource`, `StatedSource`,
  `SOURCE_STATE`, `ProductLeafSource.leaf`, `month_window`; `structure/evaluate.py` `LeafValue`, `Missing`, `Coverage`,
  `ORIGIN_ORDER`, `ORIGIN_UNKNOWN`, `_stated_node`; `structure/read.py` `StructureRead.site_inputs`), `4b`
  (`structure/money.py` `CommercialLeafSource`, `READ_AS`, `CHARGE_RECORD`; `structure/check.py` `_stated`;
  `STATED_STATE`), `4d` (`structure/litres/source.py`, the provider pattern), `3A1`/`3A2` (`commercial/store.py`
  `CommercialStore.latest_revisions`, `commercial/model.py` `RevisionRow`; pseudonyms per tenant, `commercial/
  pseudonym.py`, so meter and customer references join across kinds), `3A4` (`commercial/months.py`: placement by
  `recognition_period`, D-3A4.2; exact sums, D-3A4.9; `known_at`, D-3A4.7), `5a` (`structure/targets/read.py`
  `TargetRead.site`, `structure/targets/rules.py` `MAIN_OF`, `TARGET_RULE`), `5b` (`structure/attribution/bridge.py`),
  `mini_depth/read.py` (`MiniDepthRead._readonly`, `productive_readings`), `mini_depth/store.py` (`_ACCEPTED`,
  `_KNOWN`, `_OVERLAPS`, `read_hour_rows`), `site_outcomes/productive_use.py` (`productive_energy`), `sites/models.py`
  (`COMPONENT_PROPERTY_DEFINITIONS`, `MINIGRID_PROPERTY_CARRIERS`, `STATE_PROPERTY_VALUES`),
  `sites/minigrid_foundation.py` (`validate_minigrid_properties`), `assetops_contracts.canonical` (`loads_canonical`,
  `parse_record`; kinds `CHARGE`, `ADJUSTMENT`, `CUSTOMER_METER_READ`, `METER_ASSIGNMENT`).
- **Not what the brief assumed.** `ON1` does **not** declare a tariff or a loss band (D-ON1.8: "the expected technical
  loss band waits for `4a`"; the tariff "arrive[s] as the operator's own records"). 4a places both (D-4A.3, D-4A.6).
- **Decisions:** `rulings.md` (D-4A.1 to D-4A.14). **Reviewer guide:** `reviewer-guide.md`. **Handshake:**
  `handshake.md`.

## 0. Before you start (gates; each is a hard stop)

- **Start:** the handshake has no open question; `3B2` has merged (it edits `structure/check.py`; branch after it).
  No other unmerged dependency. Not a heavy database job.
- **Branch** `task/4a-energy-to-cash` off `main`; worktree `/opt/assetecon/AssetOpsV1-4a`; symlink
  `frontend/node_modules` from the main checkout.
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 --
  <file>`. Never ports 5490 or 8990, the walkthrough database or Docker. **No migration. No guard edit.**
- **Read:** `rulings.md`; `structure/sources.py` (whole); `structure/money.py:150-245`; `structure/evaluate.py:200-300`
  and `:375-420`; `structure/check.py:175-195`; `structure/composition.py`; `structure/litres/source.py`;
  `structure/targets/read.py:100-190`, `structure/targets/rules.py:30-55`; `mini_depth/read.py:386-460`;
  `mini_depth/store.py:255-325`; `site_outcomes/productive_use.py`; `commercial/months.py:100-160`;
  `sites/models.py:100-360`; `5b-attribution/spec.md` §5.1; `5c-deep-dive-screen/spec.md` §2.3.
- **Pre-flight (handshake, before code).** (a) Run `pwsh -NoProfile -File tools/check-architecture.ps1` on a scratch
  branch where `structure/energy/composition.py` imports `assetops_backend.mini_depth.read` and
  `structure/energy/inputs.py` imports `assetops_backend.site_outcomes.productive_use`: if refused, it is a handshake
  question (no guard edit; D-4A.13). (b) Print the role set of the Kobo `Kit` binding set in
  `backend/tests/test_s2_evidence_ledger_postgres.py` and its `feeder_demand` bindings: if it is not
  `minigrid-roles-4`, a handshake question. (c) Print the Kit's clock and the `received_at` it gives readings: test
  PG1 needs a `known_at` after 2026-11-01T00:00+03:00 that is not before the readings' receipt.
- **Files.** New package `backend/assetops_backend/structure/energy/` (`__init__.py`, `rules.py`, `inputs.py`,
  `source.py`, `composition.py`); tests `backend/tests/test_4a_energy_to_cash.py` (no database),
  `backend/tests/test_4a_energy_to_cash_postgres.py`; fixture `backend/tests/fixtures/energy_to_cash_mto.json`.
  Edited, and only these: `structure/rows_mini_grid.py` (two `stated_by`, §2.1), `structure/registry.py` (version
  4), `structure/check.py` (`_stated`, §2.1), `structure/sources.py` (§2.2), `structure/money.py` (one branch in
  `stated`, §2.2), `structure/composition.py` (the fifth builder, §4.3), `structure/targets/rules.py` and
  `targets/read.py` (`MAIN_OF`, §2.3), `sites/models.py` and `sites/minigrid_foundation.py` (two properties, §4.1),
  `mini_depth/read.py` (one read method, §4.2), and the test lines the W6 sweep names (§6.4).

## 1. Outcome and why

For a mini-grid Site and a closed month: energy delivered into the network (*Measured*, or *Simulated* when the
readings are), expected technical losses and losses beyond them (*Modelled*: a declared band applied to a
measurement), energy metered at customers and energy billed (*Recorded*, from the operator's own files),
billing adjustments (*Recorded*), energy on meters billing does not charge (*Calculated*), and the tariff (*Calculated*,
billed money over billed kWh). The energy-to-cash chain then reads stage by stage, and the bridge (`5b`, unchanged)
splits revenue's gap into kWh billed and price, and kWh billed into the named leaks, as far as each side is observed.

Why it converts: a monitoring tool shows feeder power; a billing system shows charges. Only the join shows an
executive that 140 kWh at Mto were read on six new meters billing never charged (a correctable charge, not a loss)
and that 120 kWh more left the network than the expected losses explain (investigated, never called theft).

**On a typical operator's exports** (billing, payments, invoices, budget; no feeder meter, no meter register, no
meter reads; build plan §0.4) 4a adds billed kWh and the tariff from the billing export, so where the budget states
billed kWh, revenue's gap splits into kWh billed and price (Kobo: +38.00 and 0.00, §5.3; build plan §0.4: "kWh × tariff
... splits appear only where the budget states volumes"). Every other energy figure reads "Not available yet", naming
the feeder meter export, the meter reads, the meter register or the declared loss band. Nothing is estimated.

**Gate questions** (`delivery-plan.md` §3 step 4 and §4, for the energy chain): from records and readings, do Mto's
delivered 6,000, expected loss 300, losses beyond 120, metered 5,580, unmapped 140, adjustments 40 and billed 5,400
appear, with the 140 on unmapped meters and not on loss (MAP-1)? Do Kobo and Kisiwa, with no declared band, show
technical and unexplained losses as "Not available yet", never 0? Does a Site with a full register and no swap
show unmapped 0 (negative control)? Is each node built from mixed evidence given its weakest class?

## 2. Unit 1: the structure, the rules and the wiring (pure)

### 2.1 Two stated kWh nodes (`rows_mini_grid.py`, `registry.py`, `check.py`; D-4A.1)

- `rows_mini_grid.py`: `metered_kwh` gains `stated_by=FilledBy("COMMERCIAL_RECORD", "CUSTOMER_METER_READ", "Customer
  meter reads for the month")`; `billed_kwh` gains `stated_by=FilledBy("COMMERCIAL_RECORD", "CHARGE (USAGE kWh)",
  "Billing export: the month's billed kWh")`. Expressions, homes and `composes` unchanged. The module docstring adds
  one sentence: "4a made it version 4: `metered_kwh` and `billed_kwh` name the record that states their kWh (D-4A.1)."
- `registry.py`: `REGISTRIES["MINI_GRID"]` version 3 → **4**; its comment adds "4a (D-4A.1): v4, metered_kwh and
  billed_kwh gained stated_by."
- `check.py` `_stated`: the unit condition `not row.unit.is_money` becomes `not (row.unit.is_money or row.unit == KWH)`
  (`KWH` from `assetops_contracts.canonical.units`); docstring "a record states only a summed money or kWh node's
  total". Every other condition unchanged; the existing S8 plants (`diesel_l` in litres, `MONEY * MONEY`,
  `MONEY * KWH`, `MONEY / KWH`) stay refused.
- `evaluate.py`, `bridge.py` and `5a`'s reading of stated rows are **not** edited: `_stated_node` and step 4 of the
  bridge (`RECORD_AND_FACTORS_DIFFER`) already treat any stated row; `TargetRead.site` already turns a budget line on
  a stated node into its target (D-5A).

### 2.2 `structure/sources.py` and `structure/money.py`

- `SOURCE_STATE["MINI_GRID"]`: `delivered_kwh`, `technical_loss_kwh`, `unexplained_loss_kwh`, `adjustments_kwh`,
  `unmapped_kwh`, `tariff` become `PROVIDED`, each commented `# 4a: energy-to-cash@1`. `STATED_STATE["MINI_GRID"]`
  gains `"metered_kwh": PROVIDED, "billed_kwh": PROVIDED`.
- `ENERGY_LEAVES = frozenset({"delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh",
  "unmapped_kwh", "tariff"})` and `ENERGY_STATED = frozenset({"metered_kwh", "billed_kwh"})` beside `LITRE_LEAVES`,
  both in `__all__`. `ProductLeafSource.leaf` treats `ENERGY_LEAVES` exactly as `LITRE_LEAVES` (read alone:
  `NOT_CONNECTED` naming the row's `filled_by`).
- `CommercialLeafSource.stated` (`money.py:173`): before its refusal, `if factor_id in ENERGY_STATED: return
  _absent(_MG.row(factor_id).stated_by, "NOT_CONNECTED")`, so a read wired without 4a's source keeps evaluating the
  two nodes from their expressions (evaluate row 2, "nothing to read"). No other line of `money.py` changes.

### 2.3 5a: the main factor's heading (`targets/rules.py`, `targets/read.py`; D-4A.9)

`MAIN_OF` values become tuples, nearest heading first: `{"delivered_kwh": ("billed_kwh", "revenue"), "necessary_l":
("fuel_cost",)}`. In `TargetRead.site`, the main factor is solved under the **first** heading in its tuple whose
stated target has a value; none: `MAIN_FACTOR_UNSOLVED:<last heading>` (today's note for `necessary_l`, and for
`delivered_kwh` when the budget states neither). `solve_main` is unchanged. The `under` origins line uses the chosen
heading.

### 2.4 The rules (`structure/energy/rules.py`; pure, no I/O)

```python
OBSERVER = "energy-to-cash@1"
ENERGY_ORDER = ("delivered_kwh", "technical_loss_kwh", "metered_kwh", "unexplained_loss_kwh", "adjustments_kwh",
                "unmapped_kwh", "billed_kwh", "tariff")
ONE_SET, NOT_BOUND, BINDINGS_CHANGED = "ONE_SET", "NOT_BOUND", "BINDINGS_CHANGED"
DECLARED, NOT_DECLARED, CHANGED = "DECLARED", "NOT_DECLARED", "CHANGED"

@dataclass(frozen=True)
class FeederInput:
    asset_id: UUID; asset_code: str
    day_kwh: tuple[Decimal | None, ...]     # one per Site-local day of the month; None = the day is not covered
    origins: tuple[str, ...]                # ORIGIN_ORDER order
    band_state: str                         # DECLARED | NOT_DECLARED | CHANGED
    band_pct: Decimal | None                # set only when DECLARED

@dataclass(frozen=True)
class FeederMonth:
    state: str                              # ONE_SET | NOT_BOUND | BINDINGS_CHANGED
    feeders: tuple[FeederInput, ...]        # sorted by asset_code; empty unless ONE_SET
    days: int                               # Site-local days in the month

@dataclass(frozen=True)
class Charge:          # a CHARGE revision placed in the month (recognition_period == month)
    line_type: str; tariff_class: str | None; kwh: Decimal | None; amount: Decimal; currency: str
    subject: tuple[str, str] | None; account_ref: str; provenance: str; source_system: str

@dataclass(frozen=True)
class Adjustment:      # an ADJUSTMENT revision placed in the month with a kWh quantity
    kwh: Decimal; provenance: str; source_system: str

@dataclass(frozen=True)
class MeterRead:       # a CUSTOMER_METER_READ revision whose [effective_from, effective_to) meets the month
    meter_ref: str; start: date; end: date; kwh: Decimal; provenance: str; source_system: str

@dataclass(frozen=True)
class Assignment:      # every METER_ASSIGNMENT revision of the Site
    meter_ref: str; customer_ref: str; start: date; end: date | None

@dataclass(frozen=True)
class EnergyInputs:
    month: str; first: date; next_first: date; closed: bool
    feeders: FeederMonth
    held: frozenset[str]                    # kinds with any revision of the Site at the cutoff (D-4B.5)
    charges: tuple[Charge, ...]; adjustments: tuple[Adjustment, ...]
    reads: tuple[MeterRead, ...]; assignments: tuple[Assignment, ...]

@dataclass(frozen=True)
class EnergyMonth:
    values: Mapping[str, LeafValue]         # every factor of ENERGY_ORDER

def month_energy(inputs: EnergyInputs, names: Mapping[str, FilledBy]) -> EnergyMonth
```
`names[f]` is the row's `filled_by` for a leaf and its `stated_by` for `metered_kwh` and `billed_kwh`; every absent
value is `LeafValue(None, "NOT_AVAILABLE", (), coverage, Missing(fb.kind, fb.family, cause, None, (), fb.words, None,
note), None)` (3B3's `_absent` shape, `blocks` empty). All arithmetic in one `Context(prec=34,
rounding=ROUND_HALF_EVEN)`; nothing is quantised; a zero is `copy_abs()`-normalised. Sums of record quantities are
exact (D-3A4.9: a 200-digit context that traps rounding).

**Standard usage** `S` = the charges with `line_type == "USAGE"`, `kwh` not None and `tariff_class in ("STANDARD",
None)` (productive-class lines are `4b`'s `productive_kwh`). **Read kWh** of a read: its `quantity` for INTERVAL,
`register_end - register_start` for REGISTER (the input adapter computes it, §4.2).

Each factor is judged in the order written; the first step that applies gives the value or the absence.

| Factor | Steps (cause, note) | Value, evidence, sources, origins |
|---|---|---|
| `delivered_kwh` | 1. feeders `NOT_BOUND`: NOT_CONNECTED, `FEEDER_NOT_BOUND`. 2. not `closed`: NOT_RECEIVED, `MONTH_OPEN`. 3. `BINDINGS_CHANGED`: NOT_CALCULATED_YET, `FEEDER_BINDINGS_CHANGED`. 4. any day with some feeder's `day_kwh` None: NOT_RECEIVED, `FEEDER_READINGS_GAP` | Σ over feeders and days; MEASURED; `("readings:feeder_demand",)`; union of feeders' origins. **Coverage** on every value and on steps 2 and 4: `Coverage(covered, days, {"COMPLETE": covered, "NO_DATA": days - covered})`, a day covered when every feeder covers it |
| `technical_loss_kwh` | 1. as delivered step 1. 2. any feeder `NOT_DECLARED`: NOT_CONNECTED, `LOSS_BAND_NOT_DECLARED`. 3. any `CHANGED`: NOT_CALCULATED_YET, `LOSS_BAND_CHANGED`. 4. delivered absent: delivered's cause and note | Σ_f (Σ_d day_kwh) × band_pct / 100; MODELLED; `("readings:feeder_demand", "foundation:technical-loss-band")`; delivered's origins |
| `metered_kwh` (stated) | 1. `CUSTOMER_METER_READ` not in `held`: NOT_CONNECTED, None. 2. not `closed`: NOT_RECEIVED, `MONTH_OPEN`. 3. `METER_ASSIGNMENT` not in `held`: NOT_CONNECTED, `NEEDS:METER_ASSIGNMENT`. 4. a read meeting the month not inside `[first, next_first)`: NOT_CALCULATED_YET, `METER_READ_STRADDLES`. 5. two reads of one meter overlapping: NOT_CALCULATED_YET, `METER_READS_OVERLAP`. 6. an assignment whose span inside the month is not covered by its meter's reads: NOT_RECEIVED, `METER_READS_INCOMPLETE`. 7. no read inside the month: NOT_RECEIVED, None | Σ read kWh of the reads inside the month; RECORDED; `commercial:<source_system>` sorted; their provenances in ORIGIN_ORDER |
| `unexplained_loss_kwh` | 1. delivered absent: its cause, note. 2. technical absent: its cause, note. 3. metered absent: its cause, note | delivered − technical − metered (may be negative, D-4A.5); MODELLED; union of the three's sources; union of their origins |
| `adjustments_kwh` | 1. `CHARGE` not in `held`: NOT_CONNECTED, `NEEDS:CHARGE`. 2. not `closed`: `MONTH_OPEN`. 3. no charge in the month: NOT_RECEIVED, `NEEDS:CHARGE` | Σ adjustment kWh (0 when none: the month's billing is held, ZERO_WHEN_HELD); RECORDED; sources and origins of the adjustments, else of the month's charges |
| `unmapped_kwh` | 1. `METER_ASSIGNMENT` not in `held`: NOT_CONNECTED, `NEEDS:METER_ASSIGNMENT`. 2. `CUSTOMER_METER_READ` not held: NOT_CONNECTED, `NEEDS:CUSTOMER_METER_READ`. 3. `CHARGE` not held: NOT_CONNECTED, `NEEDS:CHARGE`. 4. not `closed`: `MONTH_OPEN`. 5. metered absent at its steps 4 to 7: metered's cause and note. 6. no charge in the month: NOT_RECEIVED, `NEEDS:CHARGE` | Σ read kWh of the month's reads that are **not charged** (below); 0 when every read is charged; DERIVED; sources and origins of the reads and charges used |
| `billed_kwh` (stated) | 1. `CHARGE` not held: NOT_CONNECTED, None. 2. not `closed`: `MONTH_OPEN`. 3. no charge in the month: NOT_RECEIVED, None | Σ kwh of `S` (0 when `S` is empty: a recorded zero); RECORDED; sources and origins of `S`, else of the month's charges |
| `tariff` | 1. `CHARGE` not held: NOT_CONNECTED, `NEEDS:CHARGE`. 2. not `closed`: `MONTH_OPEN`. 3. `S` empty: NOT_RECEIVED, `NEEDS:CHARGE`. 4. two or more currencies in `S`: NOT_CALCULATED_YET, `CURRENCY_MISMATCH:<sorted codes joined by ",">`. 5. Σ kwh of `S` is 0: NOT_CALCULATED_YET, `ZERO_DENOMINATOR:billed_kwh` | Σ amount of `S` / Σ kwh of `S`; DERIVED; currency the one code; sources and origins of `S` |

**Charged** (D-4A.7). A read `r` of meter `m` is charged when some charge of `S` or of the month's productive-class
usage lines has `subject == ("METER", m)`, **or** has no meter subject (a CUSTOMER or SITE subject, or none) and an
`account_ref` equal to the customer of `r`. The customer of `r` is the `customer_ref` of the one assignment of `m` whose `[start, end)` (`end`
None is open) contains `[r.start, r.end)`; with no such assignment, or more than one, `r` has no customer
(`REGISTER_GAP`: never charged through a customer, only through its meter).

**Notes, in one list** (`NOTES`, this order; `5c` maps each to a record, D-4A.12): `FEEDER_NOT_BOUND`,
`FEEDER_BINDINGS_CHANGED`, `FEEDER_READINGS_GAP`, `LOSS_BAND_NOT_DECLARED`, `LOSS_BAND_CHANGED`,
`METER_READ_STRADDLES`, `METER_READS_OVERLAP`, `METER_READS_INCOMPLETE`, `NEEDS:METER_ASSIGNMENT`,
`NEEDS:CUSTOMER_METER_READ`, `NEEDS:CHARGE`, `MONTH_OPEN`, and the two parametrised forms `CURRENCY_MISMATCH:` and
`ZERO_DENOMINATOR:billed_kwh` (4b's spellings).

## 3. Unit 1: the provider (`structure/energy/source.py`)

```python
class EnergyInputsPort(Protocol):
    def read(self, site: SiteRef, month: str, known_at: datetime) -> EnergyInputs: ...

class EnergyLeafSource:          # implements LeafSource and StatedSource
    def __init__(self, inputs: EnergyInputsPort, fallback: Any, now: Callable[[], datetime]) -> None
    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue
    def stated(self, ctx: ReadContext, factor_id: str) -> LeafValue
```
`leaf`: `factor_id in ENERGY_LEAVES` and `SOURCE_STATE[key][factor_id] == PROVIDED`: `self._month(ctx).values[f]`;
else `fallback.leaf(ctx, factor_id)`. `stated`: `factor_id in ENERGY_STATED` and `STATED_STATE[key][f] == PROVIDED`:
the same; else `fallback.stated(ctx, factor_id)`. `_month(ctx)`: once per `ReadContext` **object** (`self._last[0] is
ctx`, D-4B.12's rule): `month_energy(inputs.read(ctx.site, ctx.month, ctx.known_at or now()), NAMES)` with `NAMES` the
MINI_GRID rows' `filled_by` (leaves) and `stated_by` (the two nodes). A Site that is not MINI_GRID never reaches here
(3B3 refuses it first).

## 4. Unit 2: the inputs

### 4.1 The declared loss band, per feeder (`sites/models.py`, `sites/minigrid_foundation.py`; D-4A.3)

- `COMPONENT_PROPERTY_DEFINITIONS` gains `"technical-loss-band": PropertyDefinition(unit="%", kind="PHYSICAL",
  display_name="Expected technical loss")` and `"technical-loss-band-basis": PropertyDefinition(unit="state",
  kind="PHYSICAL", display_name="Expected technical loss basis")`, each with a comment `# 4a (D-4A.3): the share of a
  feeder's delivered energy expected to be lost before a customer meter; read by structure/energy.`
- `STATE_PROPERTY_VALUES["technical-loss-band-basis"] = frozenset({"GENERIC_DEFAULT", "DESIGN_STUDY",
  "METERED_HISTORY"})`. `MINIGRID_PROPERTY_CARRIERS` gains both keys → `"LOAD"`.
- `validate_minigrid_properties`: a `technical-loss-band` of 100 or more is refused: message
  `f"technical-loss-band on {component.component_id} must be below 100 in {source}."` (developer text of the
  Foundation parser, as its neighbours; not served to the executive). The shared parser already refuses a negative.

### 4.2 The reads

**Feeders** (`mini_depth/read.py`, new method, SELECT only, through `_readonly`):
```python
@dataclass(frozen=True)
class FeederMonthRows:
    binding_sets: tuple[tuple[UUID, datetime, datetime | None], ...]      # (id, valid_from, valid_to)
    feeder_bindings: tuple[tuple[UUID, UUID, datetime, datetime | None], ...]  # (set id, asset_id, valid_from, valid_to)
    assets: tuple[tuple[str, UUID], ...]                                  # (asset_code, id)
    foundations: tuple[tuple[UUID, datetime, datetime | None, Any], ...]  # (id, valid_from, valid_to, content)
    readings: tuple[dict[str, Any], ...]  # evidence_id, asset_id, start, end, value_kw (None unless kW), quality, source_mode

def feeder_month(self, *, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                 known_at: datetime | None) -> FeederMonthRows
```
Statements, each on the `_readonly` connection with `k` its cutoff: binding sets of `role_set = 'minigrid-roles-4'`
(`ROLE_SET_MINIGRID_4`) with `_KNOWN` and `_OVERLAPS` (as `read_hour_rows`); bindings `role = 'feeder_demand'` of
those sets; the Site's assets; Foundation revisions with `_KNOWN` and `_OVERLAPS`; and the accepted feeder readings:
`_ACCEPTED`'s statement with `roles = ['feeder_demand']` and `e.source_mode` added to its select list (a new module
constant `_ACCEPTED_FEEDERS` in `read.py`, built from `store._COLUMNS`; `_ACCEPTED` itself is not edited). Only rows
with `interval_start` and `interval_end` set are returned.

**`StoreEnergyInputs(mini, store).read(site, month, known_at) -> EnergyInputs`** (`structure/energy/inputs.py`):
`lo, hi, first, last = month_window(month, site.timezone)`; `closed = hi <= known_at`.
- **FeederMonth** (pure helper `feeder_month(rows, lo, hi, first, last, tz) -> FeederMonth`, tested alone). No
  binding set, or sets with no feeder binding: `NOT_BOUND`. More than one set, or one set or binding not covering
  `[lo, hi)` whole (`valid_from <= lo` and `valid_to` None or `>= hi`): `BINDINGS_CHANGED`. Else `ONE_SET`, feeders
  the bound assets. For each feeder and Site-local day `d` (`[local midnight d, local midnight d+1)` as UTC):
  `productive_energy(that feeder's readings, day_lo, day_hi)`; the day's kWh is its `kwh` when not None, no
  `conflict_assets`, and `measured_seconds == (day_hi - day_lo).total_seconds()`; else None. Origins: a reading used
  with `source_mode == "SIMULATED"` gives `demo-simulated`, any other gives `unknown` (D-4A.2). **Band**: over every
  Foundation revision row, the LOAD component whose `component_id` is the feeder's `asset_code`, property
  `technical-loss-band`: every revision has it and all values equal (`Decimal(str(value))`): DECLARED with that
  value; some revision lacks it, the component is missing, or no revision: NOT_DECLARED; values differ: CHANGED.
- **Commercial**: `store.latest_revisions(site.tenant_id, site_id=site.site_id, known_at=known_at)`, one call;
  `held` = their kinds. Each revision of the four kinds is parsed with `parse_record(loads_canonical(
  row.canonical.encode("utf-8")))` (3A4's `_parse` rule: a stored canonical that does not parse raises
  `RuntimeError("stored canonical does not parse")`). CHARGE and ADJUSTMENT: placed when `row.recognition_period ==
  month` (D-3A4.2); an ADJUSTMENT counts only with a `kWh` quantity, its value signed as recorded (D-4A.8). Reads:
  kept when `effective_from < next_first` and `effective_to > first` (dates, Site-local by 2a). Assignments: all.
  `known_at` is the one cutoff for every read (D-3A4.7).

### 4.3 The composition (`structure/energy/composition.py`; `structure/composition.py`)

`build_energy_inputs(database_url, store) -> EnergyInputsService(inputs: StoreEnergyInputs, dispose)`: one
`MiniDepthRead.from_url(database_url, build_link_rows_reader())`; `store` is the commercial store `build_commercial_reads`
already made (`reads.store`; no second commercial engine); `dispose` disposes the reader only. In
`build_structure_read` it is built **fifth**, after the litres; its failure disposes the four before it (L1), and the
service's `dispose` adds it. The wiring becomes `energy = EnergyLeafSource(energy_inputs.inputs, CommercialLeafSource(
reads.months, reads.store, LitreLeafSource(litres.inputs, fallback, _utc_now)), _utc_now)` and
`StructureRead(energy, stated=energy)`. The module docstring adds one sentence for 4a.

## 5. Fixtures (hand-computed; the tests write these literals, W2)

Every vector is October 2026, Site zone `Africa/Nairobi`, 31 days, `closed` True unless named, currency USD,
commercial provenance `source-emulated`, feeder origins `demo-simulated`.

### 5.1 Mto (the pack's chain; MAP-1)
- **Feeder:** one, `asset_code "mto-feeder"`, band 5 DECLARED; `day_kwh` 194 on days 1 to 30 and 180 on day 31
  (Σ 6,000).
- **Register:** `M-0001`→`C-3001` from 2026-01-01; `M-0099`→`C-0099` from 2026-01-01; `M-OLD-1`…`M-OLD-6`→
  `C-0412`…`C-0417` from 2023-05-01 to 2026-10-03; `M-2201`…`M-2206`→`C-0412`…`C-0417` from 2026-10-03.
- **Reads** (all `[start, end)`): `M-0001` 10-01→11-01 5,400; `M-0099` 10-01→11-01 40; `M-OLD-1…6` 10-01→10-03 0
  each; `M-2201…2206` 10-03→11-01: 31, 27, 22, 25, 18, 17 (Σ 140).
- **Charges** (USAGE, STANDARD, subject METER): `M-0001` 5,400 kWh 2,160.00 (account `C-3001`); `M-0099` 0 kWh 0.00
  (`C-0099`); `M-OLD-1…6` 0 kWh 0.00 each (`C-0412…0417`). **Adjustment:** 40 kWh, subject METER `M-0099`, reason
  `ADJ-CLINIC-ALLOW`.
- **Expected:** delivered 6000 MEASURED coverage (31, 31); technical 300 MODELLED; metered 5580 RECORDED;
  unexplained 120 MODELLED; adjustments 40 RECORDED; unmapped 140 DERIVED; billed 5400 RECORDED; tariff 0.4 DERIVED
  USD (2160.00 / 5400). Evaluated with these as leaves and stated values: `metered_kwh.computed` 5580 and
  `billed_kwh.computed` 5400 (each agrees with its record).

### 5.2 Kobo (no band; customer-level billing; negative control)
- **Feeders:** `clinic-meter` 50 a day (1,550), `mill-meter` 94 on days 1 to 30 and 80 on day 31 (2,900),
  `residential-meter` 150 a day (4,650); none declares a band. Σ 9,100.
- **Register:** `M-1`→`C-1001`, `M-2`→`C-1002`, both from 2026-01-01. **Reads:** `M-1` 5,045; `M-2` 3,645 (both
  10-01→11-01). **Charges** (USAGE, no subject; 4b's records): `C-1001` 5,000 kWh 2,000.00 STANDARD; `C-1002` 3,645
  kWh 1,458.00 (no class). **Adjustment:** 45 kWh, subject CUSTOMER `C-1001`, reason `ADJ-STAFF`.
- **Expected:** delivered 9100; technical and unexplained absent NOT_CONNECTED `LOSS_BAND_NOT_DECLARED` (never 0);
  metered 8690; adjustments 45; unmapped 0 (both reads charged through their customer); billed 8645; tariff 0.4
  (3458.00 / 8645). `billed_kwh.computed` 8645 agrees; `metered_kwh.computed` None (losses not split, D-4A.4).

### 5.3 The bridge consequence (5b unchanged; unit 3 test)
Kobo: 4b's and 5a's fixtures, §5.2's register, reads and adjustment (no feeders), and one more budget line, Kobo
`billed_kwh` 8550 for 2026-10 (step 4 of §5.5's file). Actual: billed 8645 (stated), tariff 0.4. Target: billed 8550
(stated, Declared), tariff at actual 0.4 (AT_ACTUAL), `delivered_kwh` solved under `billed_kwh` to 8550 (§2.3).
`bridge(..., "revenue")` asserts exactly: VOLUME `billed_kwh` [0.40] gap 95, effect +38.00; PRICE `tariff` [8645]
gap 0, effect 0.00; the revenue row's children sum to +38.00. (The productive term follows 5b's rules: with
`productive_tariff` undeclared it gives a RESIDUAL of 0.00 naming it.) Without the billed budget line the target
billed kWh has no value (`delivered_kwh` cannot be solved under `revenue` while `productive_tariff` is unknown,
D-3B3.15), so revenue stays NOT_SPLIT: test PG3(b).

### 5.4 Variants (each on §5.1 unless named; one change each)
| # | Change | Expected |
|---|---|---|
| V1 | `closed` False | every factor NOT_RECEIVED `MONTH_OPEN` except steps before it (delivered coverage kept) |
| V2 | feeders `NOT_BOUND` | delivered, technical, unexplained NOT_CONNECTED `FEEDER_NOT_BOUND`; the rest as §5.1 |
| V3 | day 17 None | delivered, technical, unexplained NOT_RECEIVED `FEEDER_READINGS_GAP`, coverage (30, 31) |
| V4 | band CHANGED | technical, unexplained NOT_CALCULATED_YET `LOSS_BAND_CHANGED`; delivered 6000 |
| V5 | no register held | metered, unmapped NOT_CONNECTED `NEEDS:METER_ASSIGNMENT`; unexplained the same; billed, tariff, adjustments as §5.1 |
| V6 | `M-0001` read 09-28→10-28 | metered, unmapped, unexplained NOT_CALCULATED_YET `METER_READ_STRADDLES` |
| V7 | a second `M-0099` read 10-15→11-01 | `METER_READS_OVERLAP` on metered, unmapped, unexplained |
| V8 | `M-0099` read removed | `METER_READS_INCOMPLETE` on the same three |
| V9 | the `M-2203` assignment removed | unmapped 140 (its read has no customer and no charge names it) |
| V10 | a charge with subject METER `M-2201`, 31 kWh, 12.40 | unmapped 109; billed 5431; tariff 2172.40/5431 |
| V11 | `M-2201` assignment removed and V10 | unmapped 109 (charged through its meter despite the register gap) |
| V12 | `M-0001` read 5,570 | metered 5750; unexplained −50 (not clamped); unmapped 140 (a billing shortfall on a charged meter is not unmapped) |
| V13 | a PRODUCTIVE USAGE charge on `M-0001` 100 kWh 30.00 | billed 5400 and tariff 0.4 unchanged |
| V14 | the `M-0001` charge in KES | tariff NOT_CALCULATED_YET `CURRENCY_MISMATCH:KES,USD`; billed 5400 |
| V15 | `M-0001` as a REGISTER read 1,000 → 6,400 | metered 5580 (6,400 − 1,000) |
| V16 | every charge 0 kWh, 0.00 | billed 0; tariff `ZERO_DENOMINATOR:billed_kwh` |
| V17 | no CHARGE held | billed NOT_CONNECTED (None note); tariff, adjustments, unmapped `NEEDS:CHARGE` |

### 5.5 Postgres fixture `energy_to_cash_mto.json`
Shape of 4b's `money_leaves_lakeside.json` (`_note`, `steps` of `{at, entered_by, batch}`), entered by
`service:test-4a`, tenant `lakeside-power`, Site `MTO-001`: step 1 `meter_register` (§5.1's 14 assignments as
METER_ASSIGNMENT), step 2 `meter_data_export` (§5.1's 14 reads, INTERVAL), step 3 `billing_export` (§5.1's 8
charges and the adjustment), step 4 `budget_workbook` (one BUDGET_LINE: Site `KOBO-001`, `factor_id` `billed_kwh`,
value `8550`, `version_ref` `B-2026`, period 2026-10); step 2b `meter_register` and `meter_data_export` for
`KOBO-001` (§5.2's register and reads) and step 3b `billing_export` for `KOBO-001` with §5.2's adjustment only (its
charges are 4b's). File order 1, 2, 3, 2b, 3b, 4; `at` 2026-11-07T09:00:00+00:00 and every 10 minutes after, in file
order; `produced_at` an hour before each. PG2 and PG3(a) load all steps; PG3(b) all but step 4.
Pseudonymised at intake; the tests assert figures only.

## 6. Tests (written first)

### 6.1 No database (`test_4a_energy_to_cash.py`)
1. §5.1 and §5.2 through `month_energy`, every value, evidence, cause, note, coverage and origin.
2. §5.4 V1 to V17, one test each (parametrised), asserting only the named factors.
3. `feeder_month`: no set → NOT_BOUND; two sets → BINDINGS_CHANGED; a binding from 10-15 → BINDINGS_CHANGED; one
   feeder with a GOOD reading missing for 15 minutes on day 5 → that day None; two overlapping readings of one feeder
   on day 6 → day None (`conflict_assets`); a LIVE reading → origin `unknown`; band in two revisions 5 and 5 →
   DECLARED, 5 and 6 → CHANGED, one revision without it → NOT_DECLARED; a band on a feeder whose code has no LOAD
   component → NOT_DECLARED.
4. The registry: v4; `metered_kwh` and `billed_kwh` carry the §2.1 `stated_by`; `check` passes; the S8 plants still
   refuse; a planted `stated_by` on `delivered_kwh` (a leaf) refuses `STRUCTURE_STATED`.
5. `ProductLeafSource` alone gives every `ENERGY_LEAVES` factor NOT_CONNECTED naming its `filled_by`;
   `CommercialLeafSource.stated` for `metered_kwh` and `billed_kwh` gives NOT_CONNECTED naming the `stated_by`.
6. `EnergyLeafSource` over a fake port: one `read` per `ReadContext` object for ten calls (eight energy factors, two
   other leaves passed to the fallback); a second context reads again.
7. 5a `MAIN_OF`: with a billed budget line 8550, `delivered_kwh` is solved under `billed_kwh`; without it, under
   `revenue`; with neither, `MAIN_FACTOR_UNSOLVED:revenue`.
8. Seams (`ast`): `structure/energy/` imports no `simulator`, `host`, `commercial.adapters` or `*_api` module;
   `rules.py` imports nothing outside `structure.evaluate`, `structure.registry`, the standard library and
   `assetops_contracts`.
9. The Foundation: a Site document with `technical-loss-band` 5 and basis `DESIGN_STUDY` on a LOAD parses; on a
   GENERATOR is refused; 100 is refused; basis `GUESS` is refused.

### 6.2 Postgres (`test_4a_energy_to_cash_postgres.py`)
- **PG1 (feeders):** the Kobo `Kit` world of `test_s2_evidence_ledger_postgres.py`; seal through central ingestion 3
  days (1 to 3 October) of the three feeders at 10 kW every 15 minutes (`Kit.seal`, one batch per feeder per day,
  SIMULATED); `MiniDepthRead.feeder_month` returns one set, the three feeder bindings and 864 readings with
  `source_mode` SIMULATED; a `known_at` before the third day's batches drops them; `StoreEnergyInputs.read(..., known_at
  after 2026-11-01)` gives delivered NOT_RECEIVED `FEEDER_READINGS_GAP` with coverage (3, 31).
- **PG2 (commercial, end to end):** `pgworld` (3A4); 4b's fixture steps, 5a's `targets_lakeside.json`, then §5.5;
  `build_structure_read(URL).read.site(MTO, "2026-10")`: metered 5580 and billed 5400 stated RECORDED, unmapped 140,
  adjustments 40, tariff 0.4, delivered NOT_CONNECTED `FEEDER_NOT_BOUND`, revenue 2160.00 stated; with `known_at`
  2026-11-07T09:05:00+00:00 (after the Mto register, before the reads) metered NOT_CONNECTED.
- **PG3 (the bridge):** (a) §5.3 through the real reads (`build_structure_read`, `TargetRead`, `bridge`); (b) the
  same without step 4: revenue NOT_SPLIT.

### 6.3 Regression
`test_3b1_*`, `test_3b3_*`, `test_4b*`, `test_4d*`, `test_5a*`, `test_5b*`, `test_3b7a*`, `test_3a4*`,
`test_component_properties.py`, `test_w205a_ev_vocabulary.py`, `test_w402_roles_properties.py`, the mini-depth
suites (`select-tests --base main` names them); check-all once at the end.

### 6.4 The W6 sweep (pins that change by design; the packet lists each with its old and new literal)
`MG.version == 3` (`test_3b1_structure_registry.py:88`, `test_3b3_structure_evaluate.py:376`,
`test_4b1_stated_nodes.py:291`); the state tables (`test_3b3_structure_evaluate.py:76-79`, `test_4b_money_leaves.py`
`STATE_TABLE` and `REVENUE_NINE`, `:214`); `test_5b_attribution.py:434` `REVENUE_UNOBSERVED` and the e2e literals of
`test_5b_attribution_postgres.py` (Kobo, Kisiwa, Mto revenue now split as far as billed kWh and tariff are
observed); `test_w205a_ev_vocabulary.py:131` (`STATE_PROPERTY_VALUES`); any `3B7a`, `5c` or `DDR` test on `main` at
build start that pins a revenue `NOT_SPLIT` or the v3 version (grep `version == 3`, `NOT_SPLIT`,
`unobserved_actual`). A changed literal is replaced by the new computed one only when the packet shows why it moved
(the stated kWh nodes or the derived tariff); any other change is a mid-build question.

## 7. Units

| Unit | Content | Commits |
|---|---|---|
| 1 (1.25) | §2 (registry v4, `_stated`, sources, `money.py` branch, `MAIN_OF`), §2.4 rules, §3 provider; tests 1, 2, 4 to 8; the unit-test pins of §6.4 | 1 to 2 |
| 2 (1.0) | §4.1 properties, §4.2 reads (`feeder_month`, `StoreEnergyInputs`), §4.3 composition; tests 3, 9, PG1, PG2 | 1 |
| 3 (0.75) | PG3; the e2e pins of §6.4; plants (reviewer guide); check-all; packet; the 5c record keys if 5c has merged (D-4A.12, after SC-1a's merge) | 1 |

Total 3.0. Packet `specs/4a-energy-to-cash/packet.md`: the sweep table, the plants run, residual risks `R-PRODUCTIVE`
(D-4A.10), `R-TARIFF` (D-4A.6), the mid-build count.

## 8. Done (questions; each can fail)

1. Does Mto's chain read 6000, 300, 5580, 120, 40, 140, 5400 and 0.4 from feeder readings, a declared band and the
   operator's records, with the 140 on unmapped meters and not on loss (tests 1, PG2)?
2. Do Kobo's technical and unexplained losses read "Not available yet" naming the band (`LOSS_BAND_NOT_DECLARED`),
   never 0, and is Kobo's unmapped 0 with a full register (test 1)?
3. Does every absence name its record by cause and note, and does each variant of §5.4 give exactly its row (test 2)?
4. With billing and a budget that states billed kWh, does Kobo's revenue gap split into kWh billed +38.00 and price
   0.00, and without the budget line stay unsplit (PG3)?
5. Is a simulated reading labelled `demo-simulated`, never observed (tests 3, PG1)?
6. Do the stated kWh nodes keep their expressions as `computed`, so a record the factors do not explain shows as a
   disagreement and never as a split (tests 1, PG3)?
7. Is the persistence guard unchanged and passing, with no migration and no user-facing text added?
8. Is every pin of §6.4 changed only for the reason the packet states, and does each plant of the reviewer guide fail
   its named test? Mid-build count 0?

## 9. Out of scope

A tariff sheet reader (`TARIFF_SCHEDULE`; D-4A.6, queued); time-of-use bands (AR3); the productive-class split of
metered kWh (D-4A.10, queued for the owner); Findings on unmapped meters or unexplained losses (`3B2`, step 6:
MTO-BILLING, MTO-METER-AUDIT); the band's tolerance (±1 point) and its two-cycle rule (domain models §3.2: the
Finding's, not the observer's); per-customer drawers (customer-level rows need the customer-data role); a monthly
snapshot of feeder energy (`3B7a` serves the read); cold-room and EV chains (`9d`, `9e`; RC5); any screen text.

## 10. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Should the billing export and the meter reads state billed and metered kWh, as invoices state revenue? | Yes (D-4A.1; OWNER-AWAY row 13): the revenue gap splits from billing alone |
| Q2 (owner) | Where is the expected loss declared? | In the Site's setup, per feeder, with its basis (D-4A.3; row 14); not the onboarding file |
| Q3 (owner) | The tariff from a tariff sheet, or billed money over billed kWh? | Billed money over billed kWh, *Calculated* (D-4A.6; row 15); the sheet reader is queued |
| Q4 (owner) | Are unexplained losses priced in the bridge? | As unexplained fuel is (gate 5): an effect at the target tariff, never money to recover (D-4A.5; row 16) |
| Q5 (owner) | Productive-class kWh sit inside metered kWh but outside billed kWh | Registry unchanged this fortnight; such a Site shows billed kWh's disagreement (D-4A.10; row 17) |
| Q6 | Partial-month feeder data | No figure: delivered needs every day of every feeder (D-4A.2) |
| Q7 | Telemetry origins beyond SIMULATED | LIVE reads `unknown` ("Estimated" on 5c) until a field-provenance rule exists (D-4A.2) |
