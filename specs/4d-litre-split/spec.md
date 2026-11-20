# 4d: the monthly litre split (implementer spec)

Status: rev 1, Architect (Claude), 2026-11-20. Handshake not started (`handshake.md`). Lane B, on the deep-dive path
(`two-week-build-plan.md` §0.1 row 12; D-BW1.8, D-BW1.11). **3 units.** Discovery review (W5): a new mechanism that
puts litres, and through `5b` money, on the fuel line.
- **Structure:** the MINI_GRID registry (`structure/rows_mini_grid.py`): `diesel_l = necessary_l + candidate_l +
  unexplained_l + extra_l`, `fuel_cost = diesel_l * diesel_price`. The three leaves' `filled_by`: dispatch-3.2
  (generator state, solar available power, battery charge), the fuel balance (FUEL_DELIVERY, TANK_DIP). `3B3` holds
  them HELD_NOT_CALCULATED (D-3B3.4: "dispatch minutes are not litres"); D-BW1.11 gives them to `4d`.
- **Owner rules kept:** unknown is never zero; claim only what was tested; "unexplained fuel", never "theft"; a
  modelled figure is never shown as recorded; data without a source reads "Not available yet" naming the record.
- **Builds on (merged on `main` at `d93815f0d`):** `3B3` (`ReadContext`, `LeafSource`, `LeafValue`, `Missing`,
  `SOURCE_STATE`, `month_window`, `_absent`'s shape), `4b` (`CommercialLeafSource`, `build_structure_read`),
  `analytics/dispatch_v3.py` (dispatch-3.2 segments; `NECESSARY`, `CANDIDATE`, `INDETERMINATE` from
  `analytics/dispatch.py`), `PostgresAssessmentStore.select_dispatch_days_on` and `_run_detail` (W3-01),
  `fuel_balance/rules.py` (`use_from_readings`, `relevant_readings`, `ROLES`, `GENERATOR_POWER`, `GENERATOR_STATE`),
  `fuel_balance/service.py` (`no_load_basis`, `NO_LOAD_BASIS_KEY`), `financials/trial_fuel_comparison.py`
  (`sfc_for`, `no_load_for`, `WindowFacts`), `PostgresFuelBalanceStore` and its `_Tx`.
- **Decisions:** `rulings.md` (D-4D.1 to D-4D.9). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- Branch `task/4d-litre-split` off `main`, worktree `/opt/assetecon/AssetOpsV1-4d`. Start when the handshake has no
  open question. Units 1 and 2 need only `main`; unit 3 needs nothing else either.
- **Read:** `rulings.md`; 3B3 `spec.md` §2 and §3 (HELD_NOT_CALCULATED, `Missing`); `structure/sources.py`,
  `structure/money.py:150-240`, `structure/composition.py`; `fuel_balance/rules.py:155-215` (`use_from_readings`);
  `fuel_balance/service.py:66-115` (how K3 picks the tank, the generator, SFC and the no-load rate);
  `analytics/adapters/postgres_assessment_store.py:1019-1150`; `analytics/dispatch_v3.py:107-135` and `:436-475`.
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- <command>`. Never ports 5490 or 8990, the
  walkthrough database or Docker. **No migration.**
- **Collisions.** New package `structure/litres/`. Edits outside it, and only these: `structure/sources.py` (three
  `SOURCE_STATE` rows and `LITRE_LEAVES`, §3.1), `structure/composition.py` (the fourth builder, §4.3),
  `fuel_balance/adapters/postgres_fuel_balance_store.py` (`read_at`, §4.1), `analytics/adapters/
  postgres_assessment_store.py` (`dispatch_spans`, §4.2), and the 3B3 test lines that pin the three rows (§5).

## 1. Outcome and why

For a mini-grid Site and a closed month, three litre figures, each *Modelled*:
- **necessary litres:** fuel the generator burned while dispatch-3.2 judged it needed (or could not judge: D-4D.3);
- **candidate litres:** fuel burned while solar and battery could have carried the load;
- **unexplained litres:** fuel that left the tank between two dips (opening dip plus deliveries minus closing dip)
  beyond what the generator's running, at its fuel curve, accounts for.

Each litre is the generator's measured output in each running slot at its declared fuel curve (litres per kWh, and
litres per hour idle), classified by the slot's dispatch-3.2 segment. With them, `5b` splits Kobo's fuel cost gap
(−600.00) into −37.50 necessary, −412.50 candidate and −150.00 unexplained with no change to `5b` (5b §8).

Without the EMS interval export (generator state and output, solar available power, battery charge), the Site's
declared generator and tank with its fuel curve, or tank dips at both ends of the month, each figure reads
"Not available yet" and names what is missing (§2.4). A typical operator has none of these, so on the first deep-dive
the fuel line shows fuel *cost* from invoices and stops there, saying why (`two-week-build-plan.md` §0.4).

**Where the inputs come from (D-4D.1).** No new intake. The EMS export arrives as readings through the existing
evidence path and is classified by the existing dispatch-3.2 analytic; dips and deliveries are the existing
FUEL_DELIVERY and TANK_DIP operational records; the fuel curve is the Foundation's generator properties (FUEL-1).
Telemetry and fuel records keep their formats (D-2A.7).

## 2. Unit 1: the rules (`structure/litres/rules.py`; pure)

### 2.1 Literals and types

```python
LITRE_LEAVES = ("necessary_l", "candidate_l", "unexplained_l")       # registry order
EDGE = timedelta(hours=24)                 # how far outside the month a dip may lie (D-4D.5)
SLOT = timedelta(minutes=5)                # A2's slot (fuel_balance.rules)
QUANTUM = Decimal("0.001")                 # one millilitre; the only rounding, at the end (D-4D.6)
DAY_STATES = ("ASSESSED", "NOT_ASSESSED", "UNAVAILABLE", "NO_READINGS")
NOTES = ("MONTH_OPEN", "GENERATOR_OR_TANK_NOT_DECLARED", "NO_RUNNING_RECORD", "RUNNING_RECORD_GAP",
         "DISPATCH_NOT_ASSESSED", "SPANS_OVERLAP", "FUEL_CURVE_MISSING", "GENERATOR_USE_INCOMPLETE",
         "NO_LOAD_RATE_MISSING", "TANK_DIPS_MISSING", "TANK_DIPS_CONFLICT")     # this precedence, always
CAUSE_OF = {"DISPATCH_NOT_ASSESSED": "NOT_CALCULATED_YET", "SPANS_OVERLAP": "NOT_CALCULATED_YET"}  # else NOT_RECEIVED

@dataclass(frozen=True)
class RunSpan:            # one dispatch-3.2 segment: [start, end), UTC
    start: datetime; end: datetime; claim: str          # NECESSARY | CANDIDATE | INDETERMINATE
@dataclass(frozen=True)
class DispatchDay:        # one UTC day as select_dispatch_days_on gives it at known_at
    day: date; state: str; run_id: str | None; spans: tuple[RunSpan, ...]   # spans () unless ASSESSED
@dataclass(frozen=True)
class SpanUse:            # A2's slot rule over [a, b): fuel_balance.rules.use_from_readings
    kwh: Fraction | None; idle_seconds: int | None
@dataclass(frozen=True)
class FuelCurve:
    sfc: Fraction | None; sfc_ref: str | None           # litres per kWh, "foundation:<revision id>"
    no_load: Fraction | None; no_load_ref: str | None   # litres per hour at zero output
@dataclass(frozen=True)
class TankRecord:
    kind: str; occurred_at: datetime; litres: Decimal; ref: str   # FUEL_DELIVERY | TANK_DIP; ref the root id
@dataclass(frozen=True)
class LitreInputs:
    month: str; lo: datetime; hi: datetime; known_at: datetime    # lo, hi: month_window's UTC instants
    assets: str                                  # "ONE_EACH" | "NOT_ONE_EACH" (active GENERATOR and FUEL_TANK)
    days: tuple[DispatchDay, ...]                # every UTC day meeting [lo - EDGE, hi + EDGE), in order
    use: Callable[[datetime, datetime], SpanUse] # bound by the adapter to the Site's readings
    readings_held: bool                          # any generator power or state reading with instant in (lo, hi]
    curve: FuelCurve
    tank: tuple[TankRecord, ...]                 # the one tank's records occurring in [lo - EDGE, hi + EDGE)
@dataclass(frozen=True)
class LitreMonth:
    values: Mapping[str, LeafValue]              # LITRE_LEAVES order
    indeterminate_l: Decimal | None              # the part of necessary_l from INDETERMINATE segments (D-4D.3)
    window: tuple[datetime, datetime] | None     # the dip window [t_o, t_c), when found
    burned_l: Decimal | None; modelled_window_l: Decimal | None

def month_litres(inp: LitreInputs, filled_by: Mapping[str, FilledBy]) -> LitreMonth
```
All arithmetic in `Fraction` until §2.3's last step; no `float`.

### 2.2 Slots, spans and litres

- **Align.** `up(t)`: the first instant on the 5-minute UTC grid at or after `t`. A span `[s, e)` covers the slots
  starting in `[up(s), up(e))` (D-4D.4: a slot takes the class of the span holding its start).
- **Clip.** `clip(span, a, b)` = `[max(up(s), a), min(up(e), b))`, empty when start ≥ end. `lo`, `hi` and the dip
  instants after `up` are on the grid.
- **Litres of a clipped span `[a, b)`:** `u = inp.use(a, b)`; `u.kwh` or `u.idle_seconds` None: *incomplete*.
  `u.idle_seconds > 0` and `curve.no_load` None: *needs the idle rate*. Else
  `litres = curve.sfc * u.kwh + (curve.no_load or 0) * Fraction(u.idle_seconds, 3600)`.
- **Spans of a range `[a, b)`:** every `RunSpan` of every ASSESSED day, clipped to `[a, b)`, non-empty. Two clipped
  spans that overlap: `SPANS_OVERLAP`.

### 2.3 The month (judged in `NOTES` order; the first that applies gives every leaf it names its note)

For `necessary_l` and `candidate_l` (and, through them, `unexplained_l`):
1. `known_at < hi`: `MONTH_OPEN`.
2. `assets == "NOT_ONE_EACH"`: `GENERATOR_OR_TANK_NOT_DECLARED`.
3. `not readings_held` and every day meeting `[lo, hi)` is `NO_READINGS`: `NO_RUNNING_RECORD`.
4. Some day meeting `[lo, hi)` is `NO_READINGS` (others hold readings): `RUNNING_RECORD_GAP`.
5. Some day meeting `[lo - 1 day, hi)` is `NOT_ASSESSED` or `UNAVAILABLE`: `DISPATCH_NOT_ASSESSED` (the day before
   the month is read because an interval belongs to the day of its first running report).
6. Spans of `[lo, hi)` overlap: `SPANS_OVERLAP`.
7. `curve.sfc` None: `FUEL_CURVE_MISSING`.
8. Any span of `[lo, hi)` incomplete: `GENERATOR_USE_INCOMPLETE`.
9. Any span of `[lo, hi)` needs the idle rate: `NO_LOAD_RATE_MISSING`.
10. Else `N = Σ litres` of NECESSARY and INDETERMINATE spans, `C = Σ` of CANDIDATE spans, `I = Σ` of INDETERMINATE
    spans.

For `unexplained_l`, when 1 to 9 gave none:
11. `t_o` = the latest TANK_DIP with `lo - EDGE <= occurred_at <= lo`; `t_c` = the earliest with `hi <= occurred_at
    <= hi + EDGE`. Either absent: `TANK_DIPS_MISSING`. Two TANK_DIPs at the chosen instant with different litres:
    `TANK_DIPS_CONFLICT`.
12. The window `[up(t_o), up(t_c))`. Rules 4, 5, 6, 8 and 9 again over the window's parts outside `[lo, hi)` (rule 5
    over days meeting `[up(t_o) - 1 day, up(t_c))`); the first that applies is the note.
13. `O`, `Cl` the two dips' litres; `D = Σ` FUEL_DELIVERY litres with `t_o <= occurred_at < t_c`; `M = Σ litres` of
    every span of the window (any claim). `U = O + D - Cl - M` (D-4D.7: negative allowed).

**Values (D-4D.6).** `q(x) = (Decimal(x.numerator) / Decimal(x.denominator))` under `Context(prec=34,
rounding=ROUND_HALF_EVEN)`, then `.quantize(QUANTUM)`. Each valued leaf: `LeafValue(q(v), "MODELLED", sources, None,
None, None, ("unknown",))` (D-4D.8). `sources` (D-4D.9), in this order, no repeats: the run ids of the days whose
spans contributed (`"dispatch-run:<id>"`, sorted), `curve.sfc_ref`, `curve.no_load_ref` when any contributing span had
idle seconds, then for `unexplained_l` the dip and delivery refs used (`"fuel-record:<ref>"`, by `occurred_at`).
**Absent leaf:** `LeafValue(None, "NOT_AVAILABLE", (), None, Missing(fb.kind, fb.family, CAUSE_OF.get(note,
"NOT_RECEIVED"), None, (), fb.words, None, note), None)` with `fb = filled_by[leaf]` (3B3's `_absent` shape, `blocks`
empty). `indeterminate_l` = `q(I)` when `necessary_l` is valued, else None; `burned_l` `q(O + D - Cl)` and
`modelled_window_l` `q(M)` when `unexplained_l` is valued.

### 2.4 What each note means to a person (for `5c`; the words are 5c's)

| Note | Missing record |
|---|---|
| `GENERATOR_OR_TANK_NOT_DECLARED` | the Site's generator and fuel tank, declared in its setup |
| `NO_RUNNING_RECORD`, `RUNNING_RECORD_GAP`, `GENERATOR_USE_INCOMPLETE` | the EMS interval export (generator running and output, solar available power, battery charge) |
| `FUEL_CURVE_MISSING`, `NO_LOAD_RATE_MISSING` | the generator's fuel curve (litres per kWh; litres per hour idle) |
| `TANK_DIPS_MISSING`, `TANK_DIPS_CONFLICT` | tank dips at the start and end of the month |
| `DISPATCH_NOT_ASSESSED`, `SPANS_OVERLAP` | none: the running record is still being analysed ("Not analysed yet") |
| `MONTH_OPEN` | none: the month is not closed |

## 3. Unit 2: the provider and the wiring (`structure/litres/source.py`; `structure/sources.py`)

### 3.1 `structure/sources.py`

- `SOURCE_STATE["MINI_GRID"]`: `necessary_l`, `candidate_l`, `unexplained_l` become `PROVIDED`; their comments become
  `# 4d: dispatch-3.2 slots at the fuel curve` and `# 4d: dips and deliveries less the modelled litres`.
- `LITRE_LEAVES = frozenset({"necessary_l", "candidate_l", "unexplained_l"})` beside `COMMERCIAL_LEAVES`;
  `ProductLeafSource` treats them exactly as it treats `COMMERCIAL_LEAVES` (read alone: `NOT_CONNECTED` naming their
  `filled_by`). No other line changes.

### 3.2 `LitreLeafSource`

```python
class LitreInputsPort(Protocol):
    def read(self, site: SiteRef, month: str, known_at: datetime) -> LitreInputs: ...

class LitreLeafSource:
    def __init__(self, inputs: LitreInputsPort, fallback: LeafSource, now: Callable[[], datetime]) -> None
    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue
```
`factor_id` not in `LITRE_LEAVES`: `fallback.leaf(ctx, factor_id)`. Else `k = ctx.known_at or now()`; `month_litres(
inputs.read(ctx.site, ctx.month, k), filled_by)` with `filled_by` the MINI_GRID registry rows' `filled_by`; its
`values[factor_id]`. A Site whose type is not MINI_GRID never reaches here (3B3 refuses it first). **Memo:** within
one instance, the `LitreMonth` for `(tenant_id, site_id, month, known_at)` is kept only when `ctx.known_at` is not
None (at most 16 entries, least recently used dropped), so the three leaves of one pinned read cost one input read; a
live read (`known_at` None) is never memoised.

## 4. Unit 3: the adapters and the composition

### 4.1 `PostgresFuelBalanceStore.read_at(tenant_id, site_id, known_at, work: Callable[[_Tx], T]) -> T`

One `REPEATABLE READ READ ONLY` transaction; `work(_Tx(c, self._actions, self._fuel_records, tenant_id, site_id,
known_at))`. Nothing else in the store changes; `lock` and `append` are never called through it.

### 4.2 `PostgresAssessmentStore.dispatch_spans(tenant_id, site_id, lo, hi, known_at) -> tuple[dict, ...]`

One `REPEATABLE READ READ ONLY` transaction: `days = self.select_dispatch_days_on(c, tenant_id, site_id, lo, hi,
known_at)`. Per day, in order, a dict `{"day", "state", "run_id", "spans"}`:
- `available` false: `UNAVAILABLE`, spans `()`;
- `selection` None and `accepted_reading_count` in (None, 0): `NO_READINGS`; `selection` None otherwise:
  `NOT_ASSESSED`;
- else `ASSESSED`, `run_id` `str(selection["run_id"])`, spans from `self._run_detail(c, tenant_id, site_id,
  run_id)["revisions"]`: each revision whose id is in the day's `assessment_revision_ids` and whose scope is the
  interval scope (not `"WINDOW"`), each of its `result["segments"]` as `(start, end, classification)` parsed from
  ISO, in the revision's order.

### 4.3 `structure/litres/inputs.py` and `structure/litres/composition.py`

`StoreLitreInputs(fuel, assessments)` implements `LitreInputsPort.read(site, month, k)`:
1. `lo, hi = month_window(month, site.timezone)[:2]`.
2. `fuel.read_at(site.tenant_id, site.site_id, k, work)`; in `work`: the active assets; exactly one `GENERATOR` and
   one `FUEL_TANK` is `ONE_EACH`, else `NOT_ONE_EACH` (then `curve` all None, `tank ()`, `readings_held` False, `use`
   a function that is never called). For `ONE_EACH`, exactly K3's choice (`fuel_balance/service.py:96-107`) over
   `WindowFacts((), False, None, None, lo, hi)`: `sfc` and `no_load` (the no-load rate only when its basis is in
   `NO_LOAD_BASES`), refs `f"foundation:{revision id}"`; `tank` from `tx.fuel_records(tank.id, lo - EDGE, hi + EDGE)`
   (`kind`, `occurred_at`, `quantity_l`, `root_id`); `readings = relevant_readings(tx.readings(lo - EDGE -
   30 min, hi + EDGE + 30 min, ROLES), tank.id, gen.id)`; `readings_held` per §2.1 with instant `interval_end or
   source_time`; `use(a, b)` = `use_from_readings(a, b, [r for r in readings if a - 30 min <= instant(r) <= b +
   30 min], gen.id)` mapped to `SpanUse(generator_kwh, idle_seconds)`.
3. `days` from `assessments.dispatch_spans(site.tenant_id, site.site_id, lo - EDGE, hi + EDGE, k)` as `DispatchDay`.
4. `LitreInputs(month, lo, hi, k, assets, days, use, readings_held, curve, tank)`.

`build_litre_inputs(database_url) -> LitreInputsService(inputs, dispose)` from `fuel_balance.composition.
build_fuel_balance_store` and `analytics.composition.build_postgres_assessment_store`. `structure/composition.py`:
the fourth builder, after the commercial reads (a failure disposes the three before it, L1); the chain becomes
`CommercialLeafSource(reads.months, reads.store, LitreLeafSource(litres.inputs, fallback, _utc_now))`; `dispose`
disposes all four.

## 5. Fixtures (hand-computed; the tests write these literals, W2)

**KOBO-OCT** (unit 1; no records). Site `KOBO-001`, `Africa/Nairobi`, month `2026-10`: `lo` 2026-09-30T21:00Z,
`hi` 2026-10-31T21:00Z, `known_at` 2026-11-20T08:00Z, `assets` ONE_EACH, `readings_held` True. Days 2026-09-29 to
2026-11-01 all ASSESSED, run id `run-<MM>-<DD>`; spans (local times, +03:00):
- NECESSARY 18:00–24:00 on 1 to 24 October (144 h); INDETERMINATE 18:00–20:00 on 25 October (2 h); CANDIDATE
  07:00–13:00 on 1 to 11 October (66 h). Each span lies in its own local day's UTC day.
- `use(a, b)`: 20 kW throughout: `kwh = Fraction(20) * (b - a) / 1 h`, `idle_seconds = 0`.
- `curve`: `sfc` 1/4 (`foundation:sfc-1`), `no_load` 2 (`foundation:nl-1`).
- `tank`: TANK_DIP 500 at 2026-10-01T00:00+03:00 (`dip-open`); FUEL_DELIVERY 400 at 2026-10-01T09:00+03:00 (`del-1`),
  400 at 2026-10-11T09:00+03:00 (`del-2`), 380 at 2026-10-21T09:00+03:00 (`del-3`); TANK_DIP 500 at
  2026-11-01T00:00+03:00 (`dip-close`).

Hand computation: 20 kW at 0.25 L/kWh is 5 L an hour. `necessary_l` = (144 + 2) × 5 = **730.000**
(`indeterminate_l` 10.000); `candidate_l` = 66 × 5 = **330.000**; window `[lo, hi)`; burned = 500 + 1180 − 500 =
1180; modelled in the window 1060; `unexplained_l` = **120.000**. Sources: `necessary_l` `dispatch-run:run-10-01` to
`run-10-25` then `foundation:sfc-1`; `candidate_l` `run-10-01` to `run-10-11` then `foundation:sfc-1`;
`unexplained_l` `run-10-01` to `run-10-25`, `foundation:sfc-1`, then `fuel-record:dip-open`, `del-1`, `del-2`,
`del-3`, `dip-close`.

**Variants** (one change to KOBO-OCT each):

| # | Change | Expected |
|---|---|---|
| V1 | add NECESSARY 18:00–19:00 on 26 Oct at 0 kW, `idle_seconds` 3600 for that span | `necessary_l` 732.000 (sources gain `foundation:nl-1`), `candidate_l` 330.000, `unexplained_l` 118.000 |
| V2 | V1 with `no_load` None | all three `NO_LOAD_RATE_MISSING`, cause NOT_RECEIVED |
| V3 | `no_load` None, no idle | as KOBO-OCT |
| V4 | `use` gives `kwh` None for the CANDIDATE span of 3 Oct | all three `GENERATOR_USE_INCOMPLETE` |
| V5 | no TANK_DIP | 730.000, 330.000; `unexplained_l` `TANK_DIPS_MISSING` |
| V6 | closing dip 560 / 440 / 620 / 700 | `unexplained_l` 60.000 / 180.000 / 0.000 / −80.000 |
| V7 | opening dip 520 at 2026-09-30T18:00+03:00; NECESSARY 18:00–19:00 on 30 Sep | `necessary_l` 730.000; window from 2026-09-30T15:00Z; burned 1200; modelled 1065; `unexplained_l` 135.000 |
| V8 | day 2026-10-12 NOT_ASSESSED / UNAVAILABLE | all three `DISPATCH_NOT_ASSESSED`, cause NOT_CALCULATED_YET |
| V9 | day 2026-10-12 NO_READINGS | all three `RUNNING_RECORD_GAP` |
| V10 | every day NO_READINGS, `readings_held` False | all three `NO_RUNNING_RECORD` |
| V11 | `assets` NOT_ONE_EACH (and V10 too) | all three `GENERATOR_OR_TANK_NOT_DECLARED` |
| V12 | `known_at` 2026-10-31T20:59Z (and V11 too) | all three `MONTH_OPEN` |
| V13 | `sfc` None | all three `FUEL_CURVE_MISSING` |
| V14 | a second TANK_DIP of 510 at the opening instant | 730.000, 330.000; `unexplained_l` `TANK_DIPS_CONFLICT` |
| V15 | a CANDIDATE span 19:00–20:00 on 2 Oct (inside a NECESSARY span) | all three `SPANS_OVERLAP`, cause NOT_CALCULATED_YET |
| V16 | a FUEL_DELIVERY 100 at 2026-11-01T06:00+03:00 (after the closing dip) | as KOBO-OCT |
| V17 | NECESSARY 07:02–07:58 local on 12 Oct | slots 07:05 to 07:55 start inside it: +11 slots of 5/12 L: `necessary_l` 734.583 (730 + 55/12 = 734.58333…), `candidate_l` 330.000, `unexplained_l` 115.417 (120 − 55/12) |

**The bridge (unit 2).** 5b's Lakeside world (5b §5.2 without its own step; 4b's `money_leaves_lakeside.json` and
5a's `targets_lakeside.json`) read through `CommercialLeafSource(months, store, LitreLeafSource(FakeInputs, fallback(),
lambda: READ_AT))`, where `FakeInputs` gives KOBO-OCT for `KOBO-001` and V11 for the other two. Expected
`site_bridge` for Kobo, `contribution` root: −562.00 unchanged; `fuel_cost` TERM −600.00 `SPLIT`; VOLUME `diesel_l`
scale −1.25, gap 480, −600.00 `SPLIT`; TERM `necessary_l` gap 30, −37.50; `candidate_l` gap 330, −412.50;
`unexplained_l` gap 120, −150.00; PRICE `diesel_price` 0. The VOLUME, TERM litre rows' evidence MODELLED. Kisiwa and
Mto: `fuel_cost` `NOT_SPLIT` `DETAIL_NOT_AVAILABLE`, `unobserved_actual == ("candidate_l", "necessary_l",
"unexplained_l")`, each absent leaf's `missing.note == "GENERATOR_OR_TANK_NOT_DECLARED"`. Portfolio: `fuel_cost`
−755.00, 3 of 3; `diesel_l` 1180.000 against 700, gap 480.000, −600.00, 1 of 3, `out` Kisiwa and Mto `("NOT_SPLIT",)`.

## 6. Tests (written first)

**No database** (`backend/tests/test_4d_litre_split.py`):
1. KOBO-OCT: the three values, `indeterminate_l`, window, burned, modelled, sources, evidence, origins, field by field.
2. V1 to V17, each in its own case; absent leaves checked field by field (`Missing` and note).
3. Invariants over every valued case: `necessary_l + candidate_l == q(Σ litres of the month's spans)`;
   `unexplained_l + modelled_window_l == burned_l`; no value is `-0`.
4. Precedence: a case with V12, V11, V10 and V13 together gives `MONTH_OPEN`; V11 with V13 gives
   `GENERATOR_OR_TANK_NOT_DECLARED`.
5. `LitreLeafSource`: a non-litre factor goes to the fallback; with `known_at` set, three leaves cost one
   `inputs.read` (a counting fake); with `known_at` None, three.
6. *(unit 2)* The bridge (§5): every named field.
7. *(unit 2)* `ProductLeafSource` alone gives the three leaves `NOT_CONNECTED` with their `filled_by`; the 3B3 test
   lines that pinned HELD_NOT_CALCULATED for them now pin PROVIDED (the only 3B3 test edit; listed in the packet).
8. Grep: no `float(` under `structure/litres/`; no module under it imports an `adapters` module; only
   `composition.py` imports `fuel_balance.composition` or `analytics.composition`.

**Postgres** (pooled, `--db`; `backend/tests/test_4d_litre_split_postgres.py`):
1. `dispatch_spans` on the S4 F06 world (`test_ar3_dispatch_day_rows_postgres.py`'s `F06`, day 2026-10-15): the day
   is ASSESSED with the run id `select_dispatch_days_on` selected, and its spans equal the selected interval
   revisions' `result["segments"]` `(start, end, classification)` in order; a `known_at` before the run reads the day
   not ASSESSED.
2. `read_at` on K3's Kobo world (`test_k3_fuel_balance_postgres.py`'s `kobo` fixture): `active_assets` gives one
   generator and one tank; `fuel_records` returns the fixture's dips; `sfc_history` the fixture's revision; the
   transaction is read-only (an `INSERT` through `tx.c` raises).
3. `build_structure_read(url).read.site_inputs(...)` for a Site with no assets: the three leaves absent
   `GENERATOR_OR_TANK_NOT_DECLARED`; `dispose()` runs; a failing fourth builder disposes the first three.

**Regression:** `test_3b3_*`, `test_4b_*`, `test_5a_*`, `test_5b_*`, `test_k3_*`, `test_ar3_*`, the 3B7a tests;
check-all once at the end; `select-tests` before review.

## 7. Done (questions; each can fail)

1. Does KOBO-OCT give 730.000, 330.000 and 120.000, and every variant its literal or note?
2. Does Kobo's −600.00 fuel cost gap split into −37.50, −412.50 and −150.00 through `5b` with no change to `5b`?
3. Is every litre *Modelled*, and is an INDETERMINATE litre never counted as candidate?
4. With no generator and tank declared, no EMS readings, no fuel curve, an incomplete output, or no dips, does each
   leaf read absent with the note that names the missing record, never 0?
5. Is a month read only when closed, and is a day still being analysed reported as such (NOT_CALCULATED_YET)?
6. Does each planted violation in `reviewer-guide.md` fail its named test?
7. Is nothing changed outside §0's list, the new package, the two test files and the packet?

Packet: `specs/4d-litre-split/packet.md` (module paths, the mid-build count).

## 8. Out of scope

New intake for EMS exports or dips (D-4D.1; an EMS export in another shape needs a field profile: queued `4e`); the
monthly fuel-level sensor balance (dips only, D-4D.5); extra litres of an option (`extra_l`, OPTION_ONLY); the
registry's 2 % tolerance on `unexplained_l` (shown by a later screen slice); fuel bought against fuel burned (5b's
`RECORD_AND_FACTORS_DIFFER` stays the honest stop; queue Q3); cold-chain and EV (RC5).

## 9. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 1 (1.25) | §2: rules; tests 1 to 4 | `main` | 1 |
| 2 (1) | §3: provider, `sources.py` rows; tests 5 to 8 | unit 1 | 1 |
| 3 (0.75) | §4: `read_at`, `dispatch_spans`, inputs, composition; Postgres 1 to 3; check-all; packet | unit 2 | 1 |

## 10. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Litres from fuel the generator ran while dispatch could not judge (INDETERMINATE) | Counted as necessary, never candidate (D-4D.3); the figure keeps how much was indeterminate (`indeterminate_l`) |
| Q2 (owner) | A month with any running time whose output is missing | No litre figure for the month (D-4D.2), naming the EMS export; a bounded figure is a later choice |
| Q3 (owner) | Fuel bought (invoices) differs from fuel burned (dips) when the tank's stock changes | Unchanged: 5b stops the fuel split and 5c shows both figures; a stock-change factor in the structure is a registry change for the owner |
| Q4 | Dips only, or the fuel-level sensor too, for the month's ends | Dips only (D-4D.5): an operator's export is the manual dip; the sensor stays K3's night check |
| Q5 | A reshaped EMS export (the analyst's workaround) | Out of scope this fortnight: queued `4e` (a field profile per EMS layout) |
