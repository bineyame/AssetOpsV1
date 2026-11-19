## 9d. Ruling DIESEL-1-R3d: the K3 consolidated card (`fuel-balance-1`, migration 0055)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `5d8ac9ee3` (K2 merged, review `.agent/review-K2.md` ACCEPT with L1). K1 read on `task/DIESEL-K1-kisiwa-site` at `18b5bbcdc` (review packet; not merged). A2 (`099b57c96`) and K1a (`f9d27116b`) are merged.
- Owner decisions in force, verbatim: `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-diesel-night-window-2026-11-07.md` (a night runs "6 pm to noon"); `.agent/owner-fuel-scope-2026-11-07.md` ("Generic 3.3 L/h, labelled (Recommended)"; Kisiwa's generic rate is 4.9 L/h); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions").
- **This card replaces** the K3 row of §8.4 and §9.5 and binds §9c.3 item 2. Builders read only this card. Paths use the header's short forms; `T/` = `tools/`.

### 9d.1 What K3 delivers

- The `fuel-balance-1` night check, as product code: for one Site, one fuel tank and one local night (18:00 to 12:00 next day, Site time), it compares the tank's change from **accepted `fuel_level` readings** with the generator's expected burn from **accepted generator readings** and the **recorded deliveries** (K2). The result is a residual band with a margin, a state, a reason when not assessed, limitations and reporting-gap minutes.
- One append-only stored row per night per tank. A new revision is written only when the inputs, as known, change.
- An explicit service and CLI that assess named nights. **No tick stage** in v1 (§9d.7).
- A read port K4 (Finding) and K6 (verification) use.
- **Unchanged:** dispatch Findings and their fuel-cost-1/2 money (K3 never feeds a dispatch consequence); `mini_depth.rules.assess_fuel_hour` and Kobo's Fuel page (byte-equal); every Kobo, Cold and EV file; `B/work/` (K2's read is called, not edited); `B/actions/` and `B/financials/` (imported, not edited); the probe files and `probe-result.json`.
- **No served copy and no UI string.** Reason and limitation codes are internal. K4/K5 own client wording. None of theft, stolen, stole, siphon or pilfer appears anywhere (H4).

### 9d.2 The calculation (pure, exact `Fraction`, in `B/fuel_balance/rules.py`)

**Parameters: F0's declaration, verbatim.** `PARAMETERS` is `T/probe_kisiwa_fuel.py:80-94` `PARAMETERS` copied byte-for-byte, plus one key `"parameter_version": "fuel-balance-1/v1"`. Constants, exactly as F0 (`:72-78`):
- `TANK_MARGIN_FACTOR = 2` (margin = 2 × a); `DELIVERY_TOLERANCE = Fraction(1, 100)`;
- `USE_LOW_FACTOR = Fraction(9, 10)`, `USE_HIGH_FACTOR = Fraction(11, 10)` (= fuel-cost-2's `MULTIPLIER`, asserted by a test);
- `MATERIALITY_L = Fraction(40)`; `EDGE_SEARCH_MIN = 30`; `GAP_LONGER_THAN_MIN = 60`; slot = 5 min.
- **a, SFC and r are not constants.** They are the Site's declared values as known (below). At Kisiwa they are 10 L `GENERIC_DEFAULT`, 0.355 L/kWh and 4.9 L/h `GENERIC_DEFAULT`, which are F0's values.
- Any change is a new parameter version, never a retune.

**Window.** Night `d` (a Site-local date) = `[local(d, 18:00), local(d + 1, 12:00))` converted to UTC with fold 0, using `mini_depth.inputs.zone(site timezone)`. A non-existent or ambiguous local instant refuses `FUEL_BALANCE_WINDOW_INVALID`. The window must start and end on a UTC 5-minute boundary (else the same refusal). At Kisiwa (`Africa/Dar_es_Salaam`, UTC+3) night `2026-10-04` = `[2026-10-04T15:00Z, 2026-10-05T09:00Z)`, 216 slots.

**Inputs (all as known at the cutoff `known_at`, §9d.4):**
- `fuel_level` readings of the tank asset with `source_time` in `[start − 30 min, end + 30 min]`; only quality `GOOD`, unit `L`, a finite decimal value (`verification_rules.parse_exact`, no `p/q`). Others are ignored.
- `generator_power` (INTERVAL_MEAN, kW) and `generator_state` (STATE_AT_INSTANT) readings of the generator asset over the same span, converted to `verification_rules.Reading` exactly as `B/actions/verification.py:653-658`.
- SFC: `PostgresActionStore.sfc_history(..., generator, start, end, known_at)` with `trial_fuel_comparison.sfc_for` semantics (one positive value in force over the whole window).
- r: `PostgresActionStore.no_load_history(...)` with `trial_fuel_comparison.no_load_for` semantics; its basis is read with the tank properties' query below (generator component, `generator-no-load-fuel-rate-basis`).
- a: the tank component's `fuel-level-sensor-accuracy` (unit `L`, one finite positive value) and `fuel-level-sensor-accuracy-basis` ∈ {`GENERIC_DEFAULT`, `MANUFACTURER_DATASHEET`, `SITE_CALIBRATION`}, on one Foundation revision in force over the whole window (K1's vocabulary literals, §9c.1). Read by K3's own adapter query, the `_generator_property_history` SQL shape (`B/actions/adapters/postgres_action_store.py:647-670`) with the tank's asset code and `value` kept as text for the state property.
- Fuel records: K2's `select_fuel_records(c, tenant, site, tank, lo=start, hi=end, known_at)` on K3's own connection (`B/work/adapters/postgres_fuel_records.py:40`). Deliveries = records whose `kind == "FUEL_DELIVERY"`; dips = `kind == "TANK_DIP"`.

**Use, only from accepted generator readings (§9c.3 L2 (a); A2's slot rule, never re-derived).** For each slot `t` in `[start, end)`:
- `kwh_t` = `verification_rules._power_slot(t, generator_power readings)[1]` (None when UNKNOWN);
- `state_t` = `verification_rules._instant(t, generator_state readings, numeric=False)[1]` (None when UNKNOWN);
- the slot is idle iff `state_t in verification_rules.RUNNING_STATES and kwh_t == 0` (A2's rule, `verification_rules.py:487-491`).
- `generator_kwh = Σ kwh_t`; `loaded_litres = SFC × generator_kwh` (A2's `fuel = SFC × generator kWh`, every slot's kWh, as fuel-cost does); `idle_seconds = 300 × idle slots`; `idle_h = idle_seconds / 3600`.
- Any `kwh_t` None → reason `GENERATOR_KWH_UNKNOWN`. Otherwise any `state_t` None → `IDLE_SECONDS_UNKNOWN` (A2's reason names).
- `verification_rules.py` is **imported, never edited** (the two private helpers are imported by name; K6 owns the next edit of that file). K3 never reads a run, a trajectory or the simulator.
- **Amended by DIESEL-1-R3h (§9h):** the idle test is the shared `verification_rules.idle_slot(...)`, which excludes the stop slot (RUNNING at `t`, a not-running sample at `t + 5 min`). K3 makes that one named edit to `verification_rules.py`.

**Opening, closing and conflicts (F0's rule).**
- Opening O = the value of the **last** accepted reading with `source_time` in `[start − 30 min, start]`; closing C = the **first** in `[end, end + 30 min]` (both ends inclusive).
- Two accepted readings at the instant chosen for O or C with different values → reason `FUEL_LEVEL_CONFLICT`.
- None found → `MISSING_OPENING` / `MISSING_CLOSING`.

**The band (F0's `balance`, `T/probe_kisiwa_fuel.py:106-134`, exactly):**
```
D      = Σ quantity_l of FUEL_DELIVERY records          D_tol = 1/100 × D
use_low  = 9/10 × loaded_litres
use_high = 11/10 × (loaded_litres + idle_h × r)
residual_low  = (O − C) + D − D_tol − use_high − 2a
residual_high = (O − C) + D + D_tol − use_low  + 2a
state: UNEXPLAINED        iff residual_low ≥ 40
       else EXCESS        iff residual_high < 0
       else WITHIN_MARGIN iff residual_low ≤ 0 ≤ residual_high
       else BELOW_MATERIALITY
```
- The evaluation order above is F0's. `residual_low == 0` is WITHIN_MARGIN.
- The five states are F0's: the brief's WITHIN_MARGIN / UNEXPLAINED / NOT_ASSESSED plus F0's BELOW_MATERIALITY and EXCESS (reported, no Finding in v1).

**NOT_ASSESSED reasons, in this precedence (the first that applies is stored):**
1. `NO_SENSOR_ACCURACY` (no single positive accuracy with a recognised basis in force over the window; Kobo's case);
2. `SFC_MISSING`; 3. `NO_LOAD_RATE_MISSING` (no rate in force over the window, or no recognised basis);
4. `MISSING_OPENING`; 5. `MISSING_CLOSING`; 6. `FUEL_LEVEL_CONFLICT`;
7. `GENERATOR_KWH_UNKNOWN`; 8. `IDLE_SECONDS_UNKNOWN`.
- F0 had only reasons 4 and 5, because a, SFC and r were probe constants and use came from the trajectory. Reasons 1–3 and 6–8 refuse a band when an input F0 held fixed is missing. They never change a band that is computed.
- Gap minutes and spans are computed and stored for NOT_ASSESSED windows too (F0 did the same).

**Reporting gap (F0's `reporting_gap_minutes`, `:100-103`).** Points = `[start] + sorted(source_time of accepted readings with start < t < end) + [end]`. `gap_minutes` = Σ of consecutive differences longer than 60 min. `gap_spans` = those `(from, to)` pairs, in order (K4's "from {a} to {b}"). Night 4: one span, `2026-10-04T21:45Z` to `2026-10-04T23:30Z`, 105 min.

**Limitations (information only; they never change the state; fixed order, each at most once):**
1. `REPORTING_GAP` iff `gap_minutes > 0`.
2. `DIP_SENSOR_CONFLICT` iff some dip in the window has a nearest accepted `fuel_level` reading within 30 min of its `occurred_at` (by |Δt|, ties to the earlier) and `|dip − reading| > a + 10 L` (strictly). A dip with no reading within 30 min is not checked.
3. `DELIVERY_RECORDED_LATE` iff some counted delivery has `root_recorded_at > end + 30 min` (strictly), §9d.3.

**Result shape** (`WindowResult`, frozen): `state`, `reason`, `residual_low`, `residual_high` (Fraction or None), `gap_minutes`, `gap_spans`, `limitations`, and `terms` = `{opening_l, opening_at, closing_l, closing_at, deliveries_l, delivery_tolerance_l, generator_kwh, loaded_litres, idle_seconds, use_low, use_high, accuracy_l, accuracy_basis, accuracy_revision_id, sfc_l_per_kwh, sfc_revision_id, no_load_l_per_h, no_load_basis, no_load_revision_id, unknown_slots}`. Exact values are serialised with `verification_rules.fmt` (decimal, or `p/q`); unknown terms are null.

### 9d.3 Rulings on K2's review (L1 and the residual risk)

- **L1 is closed in K3's tests (§9d.6 B2–B4).** A correction that changes a dip's kind or tank must drop it from the old tank's read after the correction's `recorded_at`, and keep it before. The tests are written so that each of the reviewer's three mutations of `postgres_fuel_records.py:33` (root kind only; root tank only; both) fails at least one test. K2's code is not edited.
- **Cross-kind correction (OPERATOR_LOG → FUEL_DELIVERY) keeps the root's code and first-recorded time: intended, and pinned.**
  - The question `DELIVERY_RECORDED_LATE` answers is whether the operator **first wrote the delivery down** after the night could be checked. An operator who logged "300 L delivered" as a free-text log on time and later retyped it as a fuel delivery reported it on time. The retyping is a correction of the record's type, not a late report. So lateness is measured from `root_recorded_at`.
  - What the late retyping does change is **what the check could count**. Before the correction's `recorded_at`, the head is an OPERATOR_LOG, so the delivery is absent from `fuel_records` and from the band. K3's as-known revisions keep both: the window assessed before the correction (the delivery missing, typically EXCESS or a low residual) and the window assessed after (the delivery counted). Nothing is rewritten.
  - The record keeps the root's public code (`REC-nnnnnn`), so the Finding and the records page point to one record.
  - B4 pins all three: absent before the correction, counted after with the root's code and `root_recorded_at`, and no `DELIVERY_RECORDED_LATE` when the root was recorded on time; plus the converse, a FUEL_DELIVERY root first recorded after `end + 30 min` is flagged.
- **The partial index is unused by K2's read** (review residual risk 2). Acceptable at demo scale (one tank, tens of records a night). After-the-demo list: "fuel_records read: use the asset index (filter tank and occurrence before the per-root head scan)".

### 9d.4 Storage, service and when it runs

**Migration `backend/migrations/versions/0055_fuel_balance_window.py`.** `revision = "0055_fuel_balance_window"`, `down_revision = "0054_operational_fuel_records"`. Renumber rule (§8.4): if another migration lands first, K3 takes the next free number; K4 then follows.
```sql
CREATE TABLE fuel_balance_window (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    tank_asset_id uuid NOT NULL,
    generator_asset_id uuid NOT NULL,
    night_date date NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    revision integer NOT NULL CHECK (revision >= 1),
    parameter_version text NOT NULL CHECK (parameter_version = 'fuel-balance-1/v1'),
    recorded_at timestamptz NOT NULL,
    state text NOT NULL CHECK (state IN ('UNEXPLAINED','BELOW_MATERIALITY','WITHIN_MARGIN','EXCESS','NOT_ASSESSED')),
    reason text NULL CHECK (reason IN ('NO_SENSOR_ACCURACY','SFC_MISSING','NO_LOAD_RATE_MISSING','MISSING_OPENING',
        'MISSING_CLOSING','FUEL_LEVEL_CONFLICT','GENERATOR_KWH_UNKNOWN','IDLE_SECONDS_UNKNOWN')),
    residual_low text NULL,
    residual_high text NULL,
    gap_minutes integer NOT NULL CHECK (gap_minutes >= 0),
    gap_spans jsonb NOT NULL,
    limitations jsonb NOT NULL,
    terms jsonb NOT NULL,
    evidence_ids jsonb NOT NULL,
    record_ids jsonb NOT NULL,
    input_sha256 text NOT NULL CHECK (input_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT fuel_balance_window_revision_unique UNIQUE (tenant_id, site_id, tank_asset_id, night_date, revision),
    CONSTRAINT fuel_balance_window_tank_fk FOREIGN KEY (tenant_id, site_id, tank_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT fuel_balance_window_generator_fk FOREIGN KEY (tenant_id, site_id, generator_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT fuel_balance_window_closed CHECK (window_end > window_start
        AND recorded_at >= window_end + interval '30 minutes'),
    CONSTRAINT fuel_balance_window_reason CHECK ((state = 'NOT_ASSESSED') = (reason IS NOT NULL)),
    CONSTRAINT fuel_balance_window_band CHECK ((state = 'NOT_ASSESSED') = (residual_low IS NULL)
        AND (residual_low IS NULL) = (residual_high IS NULL))
);
CREATE INDEX fuel_balance_window_night
    ON fuel_balance_window (tenant_id, site_id, tank_asset_id, night_date, recorded_at);
CREATE TRIGGER fuel_balance_window_immutable BEFORE UPDATE OR DELETE ON fuel_balance_window
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
- `residual_low`/`residual_high` hold `fmt` exact text. `evidence_ids` = sorted accepted-evidence ids read; `record_ids` = sorted `[root_id, head_id]` pairs of the fuel records read.
- Downgrade: refuse with `RuntimeError("0055 downgrade requires no fuel_balance_window rows")` if any row exists; else drop the trigger, index and table.
- The table is **not** a chain-event producer (`0044` `PRODUCERS` unchanged). K4 links its Finding to a window by `id`.

**Store (`B/fuel_balance/adapters/postgres_fuel_balance_store.py`), class `PostgresFuelBalanceStore(database_url, *, statement_timeout_ms=30_000, lock_timeout_ms=5_000, test_db_clock_override=None)`.**
- `test_db_clock_override` is the Work store's test-only seam (`B/work/adapters/postgres_work_store.py:281-291`): constructor-only; no HTTP field, environment variable or composition sets it.
- `assess_inputs(...)` and `append(...)` run in **one** transaction:
  1. `known_at` = `SELECT clock_timestamp()` (or the override), taken first;
  2. `pg_advisory_xact_lock(hashtext('fuel-balance:' || site_id || ':' || tank_asset_id || ':' || night_date))`;
  3. fuel records (`select_fuel_records(c, …)`), the tank and no-load-basis property query, the asset rows, the Site timezone;
  4. readings, SFC and r are read through `PostgresActionStore(database_url)` (`window_readings`, `sfc_history`, `no_load_history`), all with the same `known_at`. These reads are as-known filtered on append-only rows, so they need no shared snapshot;
  5. the latest revision for the night; insert `revision + 1` with `recorded_at = known_at` only when `input_sha256` differs, else return the latest (`appended=False`).
- A `known_at` earlier than the latest revision's `recorded_at` refuses `FUEL_BALANCE_CLOCK_BACKWARDS` (tests only can cause it).

**`input_sha256`** = `financials.fuel_cost.sha256_canonical({"parameter_version", "night_date", "window": [start, end], "tank_asset_id", "generator_asset_id", "accuracy": [value, basis, revision_id], "sfc": [value, revision_id], "no_load": [value, basis, revision_id], "evidence_ids": sorted, "records": sorted [root_id, head_id, recorded_at]})`. The result is a function of these inputs, so equal digests mean an equal result.

**Service (`B/fuel_balance/service.py`), `FuelBalanceService(store).assess_night(tenant_id, site_id, night_date) -> AssessResult(window: FuelBalanceWindow, appended: bool)`.**
1. Assets: the Site's one active `FUEL_TANK` and one active `GENERATOR` asset (`retired_at IS NULL`). Zero or several of either refuses `FUEL_BALANCE_ASSETS_UNSUPPORTED` (v1 is one tank, one generator; nothing written).
2. Window from `night_date` and the Site timezone (§9d.2).
3. `known_at < window_end + 30 min` refuses `FUEL_BALANCE_WINDOW_OPEN` (the closing search is not over; nothing written).
4. Inputs, `rules.assess(...)`, digest, append.
- Refusals are `FuelBalanceRefused(code, detail)`; the four codes above are the only ones.

**When it runs: explicitly, never by itself in v1.**
- CLI `B/fuel_balance/worker.py`: `python -m assetops_backend.fuel_balance.worker assess --site <code> --from <local date> --to <local date>` (nights `[from, to)`), using `DATABASE_URL`. One JSON line per night: `{"site_code", "night_date", "status": "APPENDED"|"REUSED"|"OPEN", "revision", "state", "reason"}`. `OPEN` (window not closed) continues; any other refusal exits 2 after printing it.
- **K7's prepare calls it** for Kisiwa after each story day's acceptance; K4 raises its Finding from the stored UNEXPLAINED window afterwards. K7's card names the instants.
- **No tick stage, no job domain, no HTTP route in K3.** The demo database is prepared, so the demo shows stored windows. After-the-demo list: "fuel-balance tick stage (assess each closed night automatically)". K5 adds its own read route.

### 9d.5 The read K4 and K6 use (`B/fuel_balance/model.py`)

```python
PARAMETER_VERSION = "fuel-balance-1/v1"
STATES = ("UNEXPLAINED", "BELOW_MATERIALITY", "WITHIN_MARGIN", "EXCESS", "NOT_ASSESSED")

@dataclass(frozen=True)
class FuelBalanceWindow:
    id: UUID
    tenant_id: UUID
    site_id: UUID
    tank_asset_id: UUID
    generator_asset_id: UUID
    night_date: date                 # Site-local date of the 18:00 start
    window_start: datetime           # UTC
    window_end: datetime             # UTC
    revision: int
    parameter_version: str
    recorded_at: datetime            # also the inputs' known_at
    state: str                       # one of STATES
    reason: str | None               # set iff NOT_ASSESSED
    residual_low: Fraction | None
    residual_high: Fraction | None
    gap_minutes: int
    gap_spans: tuple[tuple[datetime, datetime], ...]
    limitations: tuple[str, ...]
    terms: Mapping[str, Any]         # §9d.2 result terms, exact text
    evidence_ids: tuple[str, ...]
    record_ids: tuple[tuple[str, str], ...]
    input_sha256: str

class FuelBalanceReadPort(Protocol):
    def windows(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID,
                lo: date, hi: date, known_at: datetime) -> tuple[FuelBalanceWindow, ...]: ...
    def window(self, tenant_id: UUID, site_id: UUID, window_id: UUID) -> FuelBalanceWindow | None: ...
```
- `windows`: per `night_date` in `[lo, hi)`, the latest revision with `recorded_at <= known_at`, ordered by `night_date`. `lo < hi` and a UTC-aware `known_at`, else `ValueError("fuel balance windows need lo < hi and a UTC known_at")`.
- `window`: one stored revision by id, any `known_at` (K4's Finding and K6's baseline cite a fixed revision).
- `PostgresFuelBalanceStore` implements both, read-only, in one `REPEATABLE READ READ ONLY` transaction.

### 9d.6 Tests (localised only; no full suite)

**A. L0 `backend/tests/test_k3_fuel_balance_rules.py` (no DB).** Every "must fail" names the mutation the test kills; the reviewer applies each to a scratch copy.
1. **Parameters verbatim.** `PARAMETERS` minus `parameter_version` equals `.agent/DIESEL-F0/probe-result.json` `assumptions.fuel_balance_1` exactly. The constants equal F0's. `Fraction(fuel_cost_v2.MULTIPLIER) == USE_HIGH_FACTOR`.
2. **Rule parity, all 10 nights.** For each night, feed `probe-result.json` `nights[k].readings` terms (opening, closing, deliveries, `loaded_litres`, idle 0, gap) with a = 10, r = 49/10 into `rules.balance`. State, `residual_low`, `residual_high`, `use_low`, `use_high`, `opening_minus_closing`, D and D_tol equal the committed exact values. Repeat for `true_tank` terms.
3. **Idle term (§9c.3 L2 (b)).** An idle-only night: loaded 0, 24 slots RUNNING at 0 kWh (idle 7200 s, built from synthetic readings through the slot path), r = 49/10, O = 100, C = 35, no delivery. Expect `use_high == Fraction(539, 50)` (10.78), `use_low == 0`, `residual_low == Fraction(1711, 50)` (34.22), **BELOW_MATERIALITY**. Must fail if the idle term is dropped (it would give UNEXPLAINED at 45) or if r is a constant (re-run with r = 33/10 and assert `use_high == Fraction(363, 50)`).
4. **`residual_low == 0` edge.** loaded 40, idle 0, O = 500, C = 436, no delivery: `residual_low == 0`, `residual_high == 48`, **WITHIN_MARGIN**. Must fail with `<` for `<=`. Also: `residual_low == 40` exactly → UNEXPLAINED; `40 − 1/1000` → BELOW_MATERIALITY; `residual_high == 0` → WITHIN_MARGIN; `residual_high < 0` → EXCESS.
5. **Delivery night high edge, exact.** F0's night-2 readings terms (O = 656071667/1000000, C = 912643333/1000000, D = [300], loaded 26057/600): `residual_high == Fraction(13671417, 500000)`, `residual_low == Fraction(-41014249, 1500000)`, `D_tol == 3`. Two tickets 300 and 150: `D_tol == Fraction(9, 2)`. Must fail without `+ D_tol` in the high edge, or with its sign flipped.
6. **Use only from accepted generator readings (§9c.3 L2 (a)).** Synthetic 5-min readings: `loaded_litres == SFC × Σ kWh` exactly; one missing power slot → NOT_ASSESSED `GENERATOR_KWH_UNKNOWN`; one missing state sample → `IDLE_SECONDS_UNKNOWN`; one non-GOOD power reading → `GENERATOR_KWH_UNKNOWN`. **A2 parity:** over one UTC hour of the same readings, K3's kWh and idle seconds equal `verification_rules.window_evidence(...)["generator_kwh"]` and `["generator_idle_seconds"]`. **Static test:** no module under `B/fuel_balance/` imports `assetops_simulator`, `host`, `tools`, `assetops_backend.runs`, or contains the word `trajectory`.
7. **Opening and closing.** A reading at exactly `start` is the opening; at `start − 30 min` counted, at `start − 31 min` not; at `end` and `end + 30 min` counted, `end + 31 min` not; the last-in-range opening and first-in-range closing are chosen; MISSING_OPENING, MISSING_CLOSING; two different values at the chosen instant → FUEL_LEVEL_CONFLICT; a non-GOOD reading is ignored.
8. **Gap.** Spans of 60 min → 0; 61 → 61; edges included; night-4-shaped readings (00:45 and 02:30 local) → 105 and the one span.
9. **Reason precedence** 1–8, each with all later reasons also present.
10. **Limitations.** DIP_SENSOR_CONFLICT at `|Δ| = a + 10` → absent, `a + 10 + 1/1000` → present; a dip with no reading within 30 min → absent. DELIVERY_RECORDED_LATE at `root_recorded_at = end + 30 min` → absent, `+ 1 s` → present. Fixed order.
11. **Window.** `Africa/Dar_es_Salaam` night `2026-10-04` → `[2026-10-04T15:00Z, 2026-10-05T09:00Z)`, 216 slots; a zone with a DST gap at 18:00 → `FUEL_BALANCE_WINDOW_INVALID`.
12. **Digest.** Equal inputs → equal `input_sha256`; one extra evidence id → different.

**B. L2 `backend/tests/test_k3_fuel_balance_postgres.py`, own `assetops_k3_test`** (Kobo imported as K2's L2 does, `test_s1_bindings_postgres.imported`; `VirtualDbClock` as W401).
1. Migration up/down/up on an empty table (exact constraint text, columns, index, trigger); downgrade refused with a row; single alembic head; UPDATE and DELETE refused by the trigger; a raw insert violating each CHECK (NOT_ASSESSED without reason; `recorded_at < window_end + 30 min`; a band on NOT_ASSESSED) fails.
2. **K2 L1, kind change.** On Kobo's tank: a TANK_DIP at T0, corrected at T1 to OPERATOR_LOG ("not a dip"). `fuel_records(known_at < T1)` contains it with kind TANK_DIP; `known_at >= T1` does not.
3. **K2 L1, tank change.** A second Site imported from `C/site-templates/twin-tank-mini-grid-150kw.yaml` (`site_from_template` + `import_site` on `PostgresFoundationStore`, K1's `register_in` step 1 pattern; PRE-FLIGHT (b)). A TANK_DIP on `north-tank` at T0, corrected at T1 to `south-tank`. North before T1: present; north after: absent; south before: absent; south after: present.
4. **Cross-kind correction (§9d.3).** On Kobo's tank: an OPERATOR_LOG "Fuel delivery of 300 L received, ticket KIS-DT-0001." at T0 (on time), corrected at T1 (after the window's `end + 30 min`) into a FUEL_DELIVERY of 300 L on the tank with a ticket digest. Absent before T1; after T1 present with `kind == "FUEL_DELIVERY"`, the root's `code`, `root_recorded_at == T0`; K3's rules on that record give **no** `DELIVERY_RECORDED_LATE`. Converse: a FUEL_DELIVERY root first recorded at `end + 31 min` gives the limitation.
   - Mutation check (reviewer, scratch copy of `postgres_fuel_records.py:33`): root kind only → B4 fails; root tank only → B3 fails; both → B2 fails.
5. **Kobo is NOT_ASSESSED.** `assess_night` for a Kobo night → stored NOT_ASSESSED `NO_SENSOR_ACCURACY`. No Kobo file changes (`git diff --stat main` lists none).
6. **Store.** `FUEL_BALANCE_WINDOW_OPEN` before `end + 30 min` writes nothing; equal inputs → `appended=False`, same id; `FUEL_BALANCE_CLOCK_BACKWARDS`; a Site with two FUEL_TANKs (the twin-tank Site) → `FUEL_BALANCE_ASSETS_UNSUPPORTED`; `windows()` argument checks.

**C. L2 parity `host/tests/test_k3_fuel_balance_parity.py`, own `assetops_k3_test`. Needs K1 merged.**
- Module fixture: `pg_harness.fresh_database()`; `demo_combined_kisiwa.register(URL, work, 2026-09-29T09:00Z, 2026-09-29T09:30Z)` (K1's flow: accuracy 10 L GENERIC_DEFAULT, no-load 4.9 L/h, SFC 0.355).
- **Nights 2, 4 and 6** (delivery, incident, after-phase dips). For each `k`:
  - start state = `float(Fraction(ref["runs"][k-1]["start"]["soc"]))`, likewise fuel (the probe's own chaining); document `probe_kisiwa_nights.day_document(soc, fuel)`;
  - draft through `KisiwaRegistered(store, "2026-09-29T11:00:00Z").draft(document, run k start, run k end)` (product v7, v5);
  - apply the F0 actions with **`probe_kisiwa_fuel.apply_actions(run, probe_kisiwa_fuel.load_actions(), run_start)`** (K0 is not merged; this is F0's hook, unchanged). Assert the returned history equals `ref["runs"][k-1]["intervention_history"]`;
  - publish and accept with `test_s6_verification_replay._publish_and_accept(tmp, run, f"epoch-{k}", run_end + 10 min)`;
  - assert the run's end tank and SOC equal `ref["runs"][k-1]["end"]` (physics guard).
- Records through `WorkService.post_operational_record` (K2), `PostgresWorkStore(test_db_clock_override=…)`, actor and fixtures as K2's L2:
  - night 2: K2's FUEL_DELIVERY example body verbatim (§9c.2), `occurred_at 2026-10-03T07:00:00Z`, recorded `07:30:00Z`, ticket digest = sha256 of the ASCII text `Fuel delivery ticket KIS-DT-0001, 300 L` (test literal);
  - dips, recorded 15 min after: night 4 `"Tank dip at the 07:00 round: 706 L."` at `2026-10-05T04:00:00Z`; night 6 663 L at `2026-10-06T15:00:00Z` (18:00 round) and 619 L at `2026-10-07T03:00:00Z` (06:00 round), values from `ref["dips"]`.
- Assess each night with the store clock at `run_end + 30 min`. Compare with `ref["nights"][k-1]["readings"]`:
  - **exact:** `state`, `reason` None, `gap_minutes`, opening and closing (`opening_reading_l.exact`, `closing_reading_l.exact`), D, D_tol;
  - **within 1/100000 L:** `loaded_litres`, `use_low`, `use_high`, `residual_low`, `residual_high`. Reason: generator power is published at 0.000001 kW resolution; over 216 slots that bounds the use error below 4 × 10⁻⁶ L. Print each term's |Δ|;
  - `idle_seconds == 0` on all three nights;
  - night 4: `gap_spans == ((2026-10-04T21:45Z, 2026-10-04T23:30Z),)`, `limitations == ("REPORTING_GAP",)`; nights 2 and 6: `()` (no dip conflict, delivery on time);
  - **independent use check (L2 (a)):** night 4's `generator_kwh` equals a test-side SQL sum over `accepted_evidence` of `generator_power` value × 5/60 h in the window, exactly.
- **As known.** Night 4 assessed first at `2026-10-05T09:45Z`, before acceptance (`12:10Z`): revision 1, NOT_ASSESSED `MISSING_OPENING`. Then at `12:30Z`: revision 2, UNEXPLAINED. `windows(known_at=10:00Z)` returns revision 1; at `12:30Z` revision 2; `window(id of revision 1)` returns revision 1.
- CLI once: `worker assess --site KISIWA-001 --from 2026-10-06 --to 2026-10-07` → one line, `REUSED`.
- Machine time about 12–18 min (three gateway days, as K1's one day at 3–5 min).
- **Packet evidence (§9c.3 L2 (c)):** "Kisiwa has 0 idle minutes on every night (F0 and these three nights), so on Kisiwa's own nights the idle × 4.9 L/h term is exercised only by test A3." All 10 nights are reproduced from stored windows in K7's KIS-3.

**Existing tests that must stay green unchanged:** `test_k2_fuel_records.py`, `test_k2_fuel_records_postgres.py`, `test_w401_work_service_postgres.py`, the single-alembic-head test, `test_fuel_cost_v2.py`, the A2 verification-rules tests, `host/tests/test_k1_registered_kisiwa.py`, and both probe `--check`s ("probe result current"). A test that only counts migrations, tables or indexes may take the new head and objects (K2's `INDEX_TOTAL` precedent); any behaviour edit is a stop.

**Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` if the worktree has no venv), `tools\check-agent-workflow.ps1`, `tools\check-navigation-truthfulness.ps1`, run directly, no `-ExecutionPolicy`. Allowlist joins (rule-8 `$pgReaders` for the new adapter, as K2) are listed in the packet with the reason; membership only, never a loosened rule.

### 9d.7 Files

| # | File | Content |
|---|---|---|
| 1 | `backend/migrations/versions/0055_fuel_balance_window.py` | §9d.4 |
| 2 | `B/fuel_balance/__init__.py` | empty |
| 3 | `B/fuel_balance/rules.py` | §9d.2: `PARAMETERS`, constants, `night_window`, `opening_closing`, `use_from_readings`, `reporting_gap`, `balance`, `limitations`, `assess`, `input_sha256` |
| 4 | `B/fuel_balance/model.py` | §9d.5, `FuelBalanceRefused`, the codes |
| 5 | `B/fuel_balance/service.py` | §9d.4 service |
| 6 | `B/fuel_balance/adapters/__init__.py`, `postgres_fuel_balance_store.py` | store and read port |
| 7 | `B/fuel_balance/worker.py` | CLI |
| 8 | the three test files of §9d.6 | |
| 9 | guard allowlists, only as PRE-FLIGHT (c) names | membership |

### 9d.8 PRE-FLIGHT (no code first; batch every question in one message)

- (a) Confirm, with file:line, that `test_s6_verification_replay._publish_and_accept` executes the **passed** in-memory run (with `apply_actions`' added frozen causes and reporting condition) and that `run_attestation` and `register_run` accept it. If either re-reads the run from a store or refuses, that is a stop (S2 below).
- (b) Confirm that importing the twin-tank template creates two active `FUEL_TANK` asset rows, and name the calls.
- (c) Name every guard list, allowlist and catalogue-count test the new package, adapter, table, index and trigger must join, and confirm the table needs no chain-producer classification.
- (d) From K1's L2 printout, the `measurement`, `source_time`, `interval_start` and `interval_end` of Kisiwa's accepted `fuel_level`, `generator_power` and `generator_state` rows (confirms the slot rule applies as written).
- (e) The call that gives the Site's timezone and its asset rows inside one transaction.

### 9d.9 Stops (report to the Architect; never design around them)

- **S1** any parity item of C differs (an exact item, or a toleranced term beyond 1/100000 L): report the night, the term and both values. Never edit `probe-result.json`, the probe, the parameters or the tolerance.
- **S2** the action-applied run cannot be published and accepted through `_publish_and_accept` (PRE-FLIGHT (a)). Report verbatim; never write a scenario entry (OA-1).
- **S3** a Kisiwa night in C has an UNKNOWN generator slot (power or state). Report it; never relax A2's slot rule.
- **S4** a need to edit `B/actions/verification_rules.py`, `B/actions/adapters/postgres_action_store.py`, `B/work/`, `B/financials/`, `B/mini_depth/`, `contracts/`, `B/runs/`, any Kobo, Cold or EV file, either probe or its result.
- **S5** an existing test in §9d.6 needs a behaviour change.
- **S6** PRE-FLIGHT (b) fails (no two FUEL_TANK assets). The Architect rules on B3.
- **S7** more than 1.9 units.

### 9d.10 Dependencies, start, branch, size and date

- **Depends on:** K2 merged (yes, `5d8ac9ee3`), A2 merged (yes), K1a merged (yes), and **K1 merged for part C only** (the `register` flow, `host/tests/kisiwa.py` and the accuracy vocabulary). K3 never merges before K1.
- **It can start before K1 merges, in two phases:**
  - **Phase A, now (about 1.1):** pre-flight, rules and A1–A12, migration, store, read, service, CLI, and B1–B6. None needs K1: the accuracy property key is a literal (§9c.1), and B runs on Kobo and the twin-tank Site.
  - **Phase B, after K1 merges (about 0.5):** merge main, then part C and the packet.
  - A builder free now takes phase A. If none is free, K3 starts on lane 3 when K1 merges, as §9.5 planned. K1 is at its review packet, so the overlap gained is at most about half a unit.
- **Branch** `task/DIESEL-K3-fuel-balance`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k3`, from main at or after `5d8ac9ee3`. Opus does the first build and the first review. Commit with `git add -f` of explicit paths.
- **DB:** only `assetops_k3_test` (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick, `serve` or suite. Run part C when the machine is idle (free RAM checked first).
- **Size: 1.6** (range 1.4–1.9), +0.1 against §9.5's 1.5:
  - rules and L0 0.4; migration, store and read 0.3; service, inputs and CLI 0.3; B (K2 L1, cross-kind, twin-tank) 0.25; C parity 0.3; pre-flight 0.05.
  - The +0.1 is K2's L1 and residual-risk tests and the readings-based parity that F0 did not have. It is paid from the remaining contingency (0.25 → 0.15), so the Kisiwa total stays **17.25**.
- **Critical path:** F0r 0.65 → K1 1.25 → K3 1.6 → K4 2.0 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.75 lane-units** (8.65 before), or about 8.25–8.5 if phase A overlaps K1. **Below the 9.75 tripwire; no cut.**
- **Demo date: unchanged at about +3.25 working days** (range 2.75–5.25).
- **Plan HTML rows (coordinator):** the DIESEL-1-R3 build-units row keeps 17.25 with K3 1.6 and contingency 0.4; rulings table gains "DIESEL-1-R3d: K3 card (fuel-balance-1 from accepted readings, 0055, explicit assess, cross-kind lateness from the first recording)"; after-the-demo list gains "fuel-balance tick stage" and "fuel_records read uses the asset index".

**Reading budget:** this §9d; §8.3's `fuel-balance-1` block; `T/probe_kisiwa_fuel.py:56-135`, `:600-640`; `.agent/DIESEL-F0/probe-result.json` (`assumptions.fuel_balance_1`, `runs`, `nights`, `dips`); `B/actions/verification_rules.py:1-120`, `:170-340`, `:370-548`; `B/actions/verification.py:643-670`; `B/actions/adapters/postgres_action_store.py:590-670`; `B/financials/trial_fuel_comparison.py:40-105`; `B/financials/fuel_cost_v2.py:1-80`; `B/work/fuel_records.py`; `B/work/adapters/postgres_fuel_records.py`; `B/work/adapters/postgres_work_store.py:1-12`, `:281-320`; `B/mini_depth/inputs.py:55-80`; `backend/migrations/versions/0054_operational_fuel_records.py` (pattern); `backend/tests/test_k2_fuel_records_postgres.py`; `host/tests/test_s6_verification_replay.py:88-260`; K1's `host/tests/kisiwa.py`, `T/demo_combined_kisiwa.py` and `backend/tests/test_k1_kisiwa_site_postgres.py` (after K1 merges).

### 9d.11 Owner questions

None.

---

## 9e. Ruling DIESEL-1-R3e: F0 evidence line endings (K1 review L1)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `da51c7a8a`. Source: L1 in `.agent/review-K1.md` on `task/DIESEL-K1-kisiwa-site` at `5218fba34`.
- **What the Architect verified on this checkout** (`core.autocrlf=true`; `git ls-files --eol` gives `i/lf w/crlf` for all five files under `.agent/DIESEL-F0/` and `.agent/DIESEL-D0/`):
  - `T/probe_kisiwa_nights.py --check` prints "probe result current (G6 pass)".
  - `T/probe_kisiwa_fuel.py --check` prints "probe result differs from the committed file".
  - A field-by-field diff of a fresh seeded `build()` against the committed F0 JSON shows **exactly two differences**: `assumptions.actions_sha256` and `assumptions.registered_path.bindings_sha256`. Both are working-copy CRLF hashes against committed LF hashes. Every litre, band, state, gap, dip, count and gate value is equal.
  - When each input is hashed after normalising it to LF (`read_text(encoding="utf-8").encode("utf-8")`), the hashes are actions `77777c82…`, bindings `68a54ef8…` and D0 template `261b7e64…414b`. None of the three files contains a lone CR.
- **D0 has no exposure.** `T/probe_kisiwa_nights.py:466-467` already hashes the template LF-normalised (`template_sha256_lf`). Its `--check` (`:506`) compares `read_text` output, which normalises line endings. D0's committed result already pins `template_sha256_lf = 261b7e642aa7e2f3a2d5175868cf7b2a406b2c89154b1229ca78424e65a6414b`, so the value F0 is re-pinned to is one D0 pre-registered independently. No D0 file is edited.

### 9e.1 Decision: the correction happens, as unit F0e

1. **Probe (`T/probe_kisiwa_fuel.py`, the only code edit).**
   - Add `def _sha256_lf(path): return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()`. This is D0's pattern (`probe_kisiwa_nights.py:466-467`).
   - Use it at `:698` (`d0_template_sha256`), `:699` (`actions_sha256`) and `:708` (`bindings_sha256`).
   - Key names stay as they are. Renaming them would move more of the pre-registered file than this fix needs.
   - `IMPORT_PATH`'s payload hash (`:261-262`) is canonical YAML and stays untouched.
2. **Re-pin by `--write`, never by hand.** The only line `git diff .agent/DIESEL-F0/probe-result.json` may show is `d0_template_sha256`, changing from `d9a4107a…aa11` to `261b7e642aa7e2f3a2d5175868cf7b2a406b2c89154b1229ca78424e65a6414b`. Any other changed line is a stop.
3. **`.gitattributes`**, appended after the PERF-01 lines:
   ```
   # DIESEL-1-R3e: Kisiwa probe evidence (pre-registered inputs and committed results) is LF on every host
   .agent/DIESEL-F0/* text eol=lf
   .agent/DIESEL-D0/* text eol=lf
   ```
   - **No renormalise commit is needed.** The index already holds LF for all five files. Proof: `git add --renormalize .agent/DIESEL-F0 .agent/DIESEL-D0`, after which `git diff --cached --name-only` lists none of them except the intentionally edited `probe-result.json`.
   - The rule is belt and braces. After item 1, both `--check`s are independent of checkout line endings. The rule makes the working-copy bytes equal the blob bytes, so a plain `sha256sum` by any reviewer matches the pins.
4. **Evidence note.** Append a section "Evidence correction (DIESEL-1-R3e)" to `.agent/DIESEL-F0-probe-results.md`. It records the cause (a mixed CRLF and LF reference), the one re-pinned value with its old and new hashes, the fact that it equals D0's `template_sha256_lf`, and the proof outputs of §9e.3. The section uses plain words and changes no earlier text.
5. **K1's monkeypatch** (`host/tests/test_k1_registered_kisiwa.py:94-101`, the `Path.read_bytes` patch and its comment) is removed. After item 1 the probe no longer calls `read_bytes` on those files, so the patch is inert, and leaving it would misstate why the parity test holds. See §9e.2 for who removes it.

**Why this re-pin is admissible under §9.4's evidence integrity:** the value re-pinned is an *input identity*, not a measurement. The proof shows the following:
- the probe's parse of each file (`yaml.safe_load` and `json.loads` over `read_text`) is line-ending-blind;
- the per-action `content_sha256` is over canonical JSON;
- the field diff in §9e.3 (c) shows every measured value byte-equal.

The new value was not computed to make a check pass. It is the LF blob hash and equals D0's independently committed pin. This is the F8 precedent (§9b item 1): the evidence changes where an identity was taken carelessly, and the measurement does not move.

### 9e.2 Who and when

- **A separate unit, F0e, now. Not folded into K3.** K3's S4 forbids it to edit either probe or its result, and K3 phase A is in build. Folding this in would mean re-carding a running builder. F0e touches no K3 file.
- **Builder:** Sonnet, a fix-round class job (mechanical, like F8). Branch `task/DIESEL-F0e-probe-eol`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-f0e`, from main at or after `da51c7a8a`. Files: `T/probe_kisiwa_fuel.py`, `.agent/DIESEL-F0/probe-result.json`, `.gitattributes`, `.agent/DIESEL-F0-probe-results.md`, plus `host/tests/test_k1_registered_kisiwa.py` only in case (b) below. Commit with `git add -f` of those explicit paths.
- **Verification:** the coordinator runs the §9e.3 mechanical checks. There is no reviewer judgement and no separate review, as with F8. Merge when every check passes.
- **Sequencing with K1 (K1 is on the critical path; F0e never blocks it):**
  - **(a) F0e merges before K1 is merge-ready (expected).** K1's fix round merges main and deletes the monkeypatch. Its own L2 run of `test_f0r_reproduces_on_the_registered_site` on `assetops_k1_test` is the proof. K1's reviewer or the coordinator confirms that the test passes with no patch.
  - **(b) K1 merges first.** K1 merges with the monkeypatch, which is correct on this checkout and accepted by its reviewer. F0e then merges main, deletes the monkeypatch and runs that one test once on `assetops_k1_test` (an authorised test DB; machine idle; no suite).
  - Rule: **the unit that merges second removes the monkeypatch.**
- **Hard deadline:** F0e merges **before K3 phase B**. K3 §9d.6 requires both `--check`s to print "probe result current", and on main today the F0 check cannot pass on any checkout. F0e also merges before K7 and before any Linux or container run of either probe. K3 §9d.10 gains this dependency. Phase A is unaffected.

### 9e.3 Proof steps (each output pasted into the evidence section)

Run with `PYTHONPATH` set to the worktree's `simulator;backend;contracts;host`. The plan2 `.venv` is installed editable against another checkout. Without this, the probes import the wrong tree and fail with `ImportError`. That failure is not a probe result.

- **(a) Before (CRLF, F0e worktree, before any edit).** D0 `--check` is current. F0 `--check` "differs", which records the defect.
- **(b) After, CRLF working copies.** Apply items 1–3, run `--write` once, then run each `--check` in a fresh process, twice. Both print current. This is done before any re-checkout, so the evidence files are still CRLF on disk.
- **(c) Field diff.** A scratch script compares the new committed JSON with `git show main:.agent/DIESEL-F0/probe-result.json` field by field. Exactly one path differs: `assumptions.d0_template_sha256`. `git diff --stat` shows one line changed in that file and no change to any `.agent/DIESEL-D0/` file.
- **(d) After, LF.** Run `git -c core.autocrlf=false archive HEAD | tar -x` into a scratch directory, and confirm with `git ls-files --eol` or a byte check that the five evidence files have no CR. Run both `--check`s there with `PYTHONPATH` pointing at the extracted tree. Both print current. This is the Linux or fresh-clone case.
- **(e) After re-checkout in the worktree.** Delete the five evidence files and run `git checkout -- .agent/DIESEL-F0 .agent/DIESEL-D0`. They come back LF (`w/lf`). Run both `--check`s; both print current. Run `git status`; the tree is clean.
- **(f) Renormalise.** Run `git add --renormalize .agent/DIESEL-F0 .agent/DIESEL-D0`. Nothing is staged beyond the intended commit.
- **(g) Band test.** `host/tests/test_probe_kisiwa_fuel_band.py` (no DB) passes unchanged.
- **(h) Case (b) only.** The single K1 parity test passes without the monkeypatch.

**Stops:**
- (c) shows any second changed path;
- any `--check` fails in (b), (d) or (e);
- a lone CR or a non-UTF-8 byte is found in an input;
- any D0 file would change.

On a stop, the builder reports it and never adjusts a value by hand.

### 9e.4 Size

- **F0e: 0.1** (range 0.1–0.15): code and re-pin 0.03; the proof matrix 0.05; the evidence note 0.02. Case (b)'s one L2 test run adds about 0.03 if it happens.
- Paid from contingency, 0.15 → 0.05. **The Kisiwa total stays 17.25.**
- F0e is off the critical path: it runs in parallel now and only gates K3 phase B, which is at least half a unit away. The critical path is still about **8.75 lane-units**, below the 9.75 tripwire. **The demo date is unchanged** at about +3.25 working days.
- After-the-demo list: none.

### 9e.5 Owner questions

None. For the owner, in plain words: one fingerprint in the fuel trial's record was taken from a Windows copy of a file instead of the stored copy, so the check failed on other machines. We fix how the fingerprint is taken. No measured fuel number changes.

---

