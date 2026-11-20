# Build sheet CH-1a: day snapshots, quality grades, evidence class, subjects

- Architect: Claude, 2026-11-03.
- Plan: `Docs/demo-sprint/client-demo-plan.html` (agreed). Lane 1 starter.
- Design: `Docs/demo-sprint/implementation-logic-design-proposal.html`:
  - AG-2 to AG-5, AG-9, AG-10, AG-27;
  - §4.3 `site_day_snapshot`, §4.3b evidence classes;
  - §5.2 A1;
  - §5b catalogue `measures:` excerpt;
  - §15 CH-1a row (5 units).
- Branch: `task/CH-1a-day-snapshots`, cut from main after **CH-0** merges.
- Paths: `B/` = `backend/assetops_backend/`, `M/` = `backend/migrations/versions/`. Lines are to `73a558a1b`.

## 0. Result and boundary

**Observable result.** For every Site and Site-local day, one graded snapshot row per measure: coverage, grade, value and money. They are built by one builder from the same coverage policy and calendar, and read by one reader that answers "how many days, of which grade". The L3 clone shows the design's data check (§5).

**Not in this slice.**
- No screen reads the snapshots yet. CH-5a (ChainReader) and CH-6 (Portfolio/Grow) switch screens over, so the board's "21 Oct shows no spare solar" becomes visible in CH-5a. In this slice it is proven at the snapshot level.
- No event register, outbox or dirty queue (CH-1b).
- No tick stage. CH-1b adds the drain; here the builder runs from a CLI and from CH-2's backfill.
- No change to matchers, money models or verification rules (design §11: a High finding).
- No QW files are edited: `B/site_outcomes/*`, `B/estate/*`, `B/outcome_api.py`, `B/estate_portfolio_api.py` and `B/perf.py` are read only. Adapters **call** existing pure functions; they do not edit them.

## 1. Migration `0043_chain_snapshots` (Architect ruling: migration split for two lanes)

- **File:** `M/0043_chain_snapshots.py`, with `revision = "0043_chain_snapshots"`.
- **`down_revision` depends on merge order.**
  - If CH-2's `0042_chain_threads` is **not** on main when this merges, use `"0041_walk1_objective_min_days"`; CH-2 then rebases its `down_revision` to `"0043_chain_snapshots"`.
  - If 0042 is on main, use `"0042_chain_threads"`.
  - The one-line rebase is proven by the scoped migration test (§6 step 2) before merge.
- **No merge migration.**
- **Header:** the docstring follows `M/0041_walk1_objective_min_days.py:1-21` (Revision ID / Revises / Create Date).

```sql
CREATE TABLE site_day_snapshot (
  tenant_id uuid NOT NULL,
  site_id uuid NOT NULL,
  local_day date NOT NULL,                       -- Site-local calendar day (AG-27), site.timezone (M/0001:67)
  subject_kind text NOT NULL DEFAULT 'SITE' CHECK (subject_kind IN ('SITE','ASSET','CONNECTION','CUSTOMER')),
  subject_ref text NOT NULL DEFAULT 'SITE',      -- asset id (text) or 'SITE'                       (AG-10)
  measure text NOT NULL CHECK (measure ~ '^[a-z][a-z0-9_]{1,62}$'),
  evidence_class text NOT NULL CHECK (evidence_class IN ('MEASURED','RECORDED','DECLARED','MODELLED','EXTERNAL')),  -- AG-9
  revision int NOT NULL CHECK (revision >= 1),
  expected boolean NOT NULL,
  required_seconds int NOT NULL CHECK (required_seconds >= 0),
  covered_seconds int NOT NULL CHECK (covered_seconds >= 0),
  coverage_pct numeric(5,2) NOT NULL CHECK (coverage_pct BETWEEN 0 AND 100),
  grade text NOT NULL CHECK (grade IN ('COMPLETE','PARTIAL','LOW','NO_DATA','NOT_EXPECTED','PENDING')),
  value jsonb NULL,
  money jsonb NULL,                              -- {"amount": "42.08", "currency": "USD", "assumption_revision_id": "<uuid>"}
  policy_version text NOT NULL,                  -- 'coverage-policy/1'
  calendar_version text NOT NULL,                -- 'operating-calendar/1'  (added: the calendar is an input; see §2)
  catalogue_version int NOT NULL,                -- 1 until CH-1b's catalogue file
  input_fp text NOT NULL CHECK (input_fp ~ '^[0-9a-f]{64}$'),
  computed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (tenant_id, site_id, local_day, subject_kind, subject_ref, measure, revision),
  UNIQUE (tenant_id, site_id, local_day, subject_kind, subject_ref, measure, input_fp),
  FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),       -- site_tenant_id_unique, M/0001:78
  CHECK (NOT expected = (grade = 'NOT_EXPECTED')),
  CHECK (grade <> 'NO_DATA' OR covered_seconds = 0),
  CHECK ((money IS NULL) OR (value IS NOT NULL))
);
CREATE INDEX site_day_snapshot_read
  ON site_day_snapshot (tenant_id, site_id, measure, local_day, subject_kind, subject_ref, revision DESC);
CREATE INDEX accepted_evidence_site_role_time
  ON accepted_evidence (site_id, role, source_time);                     -- design §11b P-6 (no role index today)
CREATE TRIGGER site_day_snapshot_immutable BEFORE UPDATE OR DELETE ON site_day_snapshot
  FOR EACH ROW EXECUTE FUNCTION ledger_append_only();                    -- as M/0030:228-229 (function M/0005:310)
```

**Downgrade.** Refuse when rows exist, in the 0030 style (`M/0030:240-252`): `LOCK TABLE site_day_snapshot IN ACCESS EXCLUSIVE MODE`, then `IF EXISTS (SELECT 1 FROM site_day_snapshot) THEN RAISE EXCEPTION 'Downgrade of 0043_chain_snapshots refused: snapshot history exists'`. Otherwise drop the trigger, the two indexes and the table.

**Deviations from §4.3, recorded as Architect rulings:**
- `calendar_version` is added, because a calendar change must re-revision a day.
- The composite FK to `site(tenant_id, id)` matches the codebase's scoped FKs.
- Three CHECKs are added.
- Revision ids are split per lane.

## 2. Declared policy and calendar (config, reviewed as code; DECLARED class)

### `config/chain/coverage-policy-v1.json`

```json
{"schema": "coverage-policy", "version": 1, "policy_version": "coverage-policy/1",
 "bands": {"complete": 0.80, "partial": 0.25},
 "objective_min_complete_days": 3,
 "share_of_expected_days": null}
```

- Bands are from AG-4. The minimum days come from AG-3 (N = 3) and match the existing configurable minimum in `M/0041`. Do **not** wire it into objectives here; CH-6 does that.
- A per-measure `threshold` (§3) overrides `bands.complete` for that measure. For example, `noon_headroom_kw` uses 1.0, so it is COMPLETE only when the whole midday period is covered.

### `config/chain/operating-calendar-v1.json`

The operating calendar comes from AG-2 and OD-8. There is no operating-hours field anywhere in the build today (research: no hit in the backend, config, frontend or YAML). So the calendar is declared here and keyed by Site code. A later Foundation property may replace the file without changing the reader interface.

```json
{"schema": "operating-calendar", "version": 1, "calendar_version": "operating-calendar/1",
 "sites": {
   "KOBO-001":     {"kind": "OPERATING", "label": "Declared operating hours", "days": "ALL",
                    "hours": [{"from": "00:00", "to": "24:00"}],
                    "reason": "mini-grid: supplies power all day"},
   "COLD-LAB-001": {"kind": "OPERATING", "label": "Declared operating hours", "days": "ALL",
                    "hours": [{"from": "00:00", "to": "24:00"}],
                    "reason": "cold room: holds temperature all day"},
   "EV-LAB-001":   {"kind": "OPERATING", "label": "Declared charging hours", "days": ["TUE"],
                    "hours": [{"from": "08:00", "to": "16:00"}],
                    "reason": "declared connector enable schedule",
                    "source": "backend/tests/fixtures/w2/ev-lab-001.yaml:154-168 (enforced host/ev_publication.py:331-336)"}
 },
 "default": {"kind": "OPERATING", "label": "Declared operating hours", "days": "ALL", "hours": [{"from": "00:00", "to": "24:00"}]}}
```

- Hours are **Site-local**, from `site.timezone`:
  - Kobo and Cold lab are `Africa/Addis_Ababa`.
  - EV is `Etc/UTC` (`backend/tests/fixtures/w2/ev-lab-001.yaml:9`).
- The loader requires `kind` and `reason` on every entry. It also requires `source` on every `LAB_SESSION` entry.

**Ruling on demo-shaped item 5 (DS-R1, never tune numbers; coordinator 2026-11-03).**

- **Kobo is 24 h.**
  - An earlier draft of this sheet declared 06:00–14:00. Those are exactly the hours the demo runs cover (03:00–11:00 UTC), so that was config fitted to the data. It is withdrawn.
  - A mini-grid supplies power all day, so it declares 24 h. That is option (a)/(b) in the coordinator's note.
  - Option (c), keeping 06:00–14:00 as a "daytime-only Site", is rejected: Kobo serves residential customers and a clinic, so there is no genuine operating reason to stop at 14:00.
- **Consequence on the current data (honest, not hidden).** Each Kobo run day covers 8 of 24 h, about 33%. So `productive_kwh` and `avoidable_gen_min` grade **PARTIAL**.
  - Under AG-5, partial days still count in totals, labelled and split.
  - Under AG-6, they do not count towards N, so the monthly target would read "too early to judge".
- **DD-1 then extends Kobo's story days to the full local day.**
  - It may use only the simulator's existing scenarios, for example a normal night with no generator and low demand. If no such scenario exists, DD-1 stops; nobody writes one tuned to produce a result.
  - With the extension, the grades become honestly COMPLETE.
  - DD-1 pre-flight first measures one 24 h Kobo day build.
  - **Budget:** the whole Kobo build may grow by at most 50% (measured 611.8 s at WALK1-G2, so a cap of about 920 s).
  - **Fallback:** if the measured cost exceeds this, or no existing scenario fits, the extension is not built. Kobo days stay PARTIAL and are shown as "8 of 24 h measured". The coordinator tells the owner, because this changes the Grow target story.
- **Labs: revised after pre-flight P7 (CH-1a pre-flight Q1/Q2). There is no `LAB_SESSION` kind.**
  - **EV:**
    - The Site really declares a connector enable schedule of Tuesdays 08:00–16:00 UTC, so that is its calendar.
    - The earlier 08:00–09:00 was the scenario run window, fitted to the data, and is withdrawn.
    - Tuesday-only still gives the design's "EV 26 Oct: NOT_EXPECTED".
  - **Cold:**
    - No session is declared anywhere except the story-day file. The scenarios run 19:00–20:00 UTC, while the story nights are 16:00–17:05 UTC, so any session hours would be inferred.
    - A cold room holds temperature all day, so it declares 24 h.
  - **Effect on today's data:** Cold nights cover about 65 min of 24 h, and EV fault days cover 1 h of 8 h. Both grade **LOW**: shown, not totalled (AG-5).
  - **DD-1 extension:** DD-1 extends the Cold and EV story days in the same way as Kobo, using existing scenarios only and within the same budget rule (§5c). If that is not possible, they stay LOW and are labelled.
- **No `source` placeholder remains.** The loader requires `source` only when an entry cites one.

**Loader.** `B/chain/policy.py` loads both files once per process. Each is validated against a small schema (types and ranges; `from < to`, or `to == "24:00"`; day names in MON..SUN). An invalid file raises `ChainConfigError` at load. Tests use their own files through an explicit path argument, never by editing the shipped files.

## 3. Measures (code registry in CH-1a; CH-1b moves the declarations into the catalogue's `measures:` section unchanged)

`B/chain/measures.py` holds `MEASURES: dict[str, MeasureSpec]`:

```
MeasureSpec(key, subject_kind, evidence_class, period, threshold, adapter)
```

- **No outcome link (OL-1, plan §2.4).** A `MeasureSpec` names no outcome id, node or strategy. Which outcome a measure feeds is declared only in `B/outcomes/outcome_map.py` `CONTRIBUTIONS`, which CH-6 adds. Do not add `MG-`/`CC-`/`EV-` literals in `B/chain/`. CH-6's ratchet guard will fail on them.
- `period` ∈ {`operating_hours`, `midday`}.
- `threshold` overrides the complete band.
- `adapter` names a registered `MeasureAdapter` with a version, e.g. `mini.productive_energy@1`.

| Measure | Site domain | Subject | Class | Period | Threshold | Inputs (coverage) | Value (jsonb) | Money | Adapter calls (existing pure code) |
|---|---|---|---|---|---|---|---|---|---|
| `productive_kwh` | MINIGRID | ASSET (each supply-use=PRODUCTIVE asset; subject_ref = asset id) | MEASURED | operating_hours | 0.8 | Accepted `feeder_demand` readings with GOOD quality for that asset, as interval seconds inside the period (`B/mini_depth/store.py:257-261` `_ACCEPTED` cutoff and overlap rules) | `{"kwh": "<dec>", "measured_seconds": n}` | kWh × the declared productive price valid that day; null when no price is valid | `B/site_outcomes/productive_use.py:37` `productive_energy` |
| `noon_headroom_kw` | MINIGRID | SITE | MEASURED | midday = local 12:00–13:00 (today's basis, `B/mini_depth/inputs.py:79-80` `local_noon`; CH-9 replaces it with the daylight window) | 1.0 | The renewable hour's combined inputs (`pv_available_power`, `pv_power`, `storage_charge_requested_power`) | `{"low_kw": "<dec>", "high_kw": "<dec>", "decision": "ELIGIBLE"\|"EXCLUDED"\|null}` | null | `B/mini_depth/rules.py:359-372` (combine) and `:395` `summarize_renewable` for one day |
| `avoidable_gen_min` | MINIGRID | ASSET (generator; subject_ref = `generator_asset_id`) | MEASURED | operating_hours | 0.8 | The S3 dispatch result for the day (`B/analytics/adapters/postgres_assessment_store.py:913` `select_dispatch_days_on`), seconds covered by the assessed interval inside the period | `{"minutes": n}` | null (the money model is unchanged; CH-3/CH-6 own "modelled, not saved") | the dispatch result fields (pre-flight P3) |
| `chamber_temp_c` | COLDCHAIN | ASSET (chamber) | MEASURED | operating_hours (the lab session) | 0.8 | Accepted chamber-temperature role readings (role name: pre-flight P4) | `{"peak_c": "<dec>"}` | null | cold assessment reader (pre-flight P4) |
| `backup_start_chain` | COLDCHAIN | ASSET (backup unit) | MEASURED | operating_hours | 1.0 | The backup start-chain events (role or event kind: pre-flight P4) | `{"starts": n, "failed": n}` | null | same |
| `charging_kwh` | EV_CHARGING | SITE | MEASURED | operating_hours (the lab session) | 0.8 | EV session measurements (`M/0024:24` ev_measurement; pre-flight P5) | `{"kwh": "<dec>", "sessions": n, "completed": n}` | kWh × the declared EV tariff valid that day | EV session reader (pre-flight P5) |

**Adapter interface** (`B/chain/measures.py`):

```python
class MeasureAdapter(Protocol):
    key: str                                # "mini.productive_energy@1"
    def inputs(self, ctx: DayCtx, subject_ref: str) -> InputSet: ...   # ids + covered intervals + pending flag
    def measure(self, ctx: DayCtx, subject_ref: str, inputs: InputSet) -> dict | None: ...
    def money(self, ctx: DayCtx, subject_ref: str, value: dict) -> dict | None: ...
    def subjects(self, ctx: DayCtx) -> list[str]: ...                  # ['SITE'] or asset ids
```

- `DayCtx` carries tenant_id, site_id, site_code, domain, tz, local_day, period_start_utc, period_end_utc and known_at.
- `InputSet` carries `ids: tuple[str, ...]`, `covered: list[tuple[datetime, datetime]]` and `pending: bool`.
- Adapters read through **one** reader port, `ChainInputReader` (`B/chain/ports.py`), implemented in `B/chain/adapters/postgres_chain_inputs.py` (a registered `$pgReaders` entry). They never import a driver.
- Adapters call the existing pure functions named in the table. If a function needs a shape that only a QW-touched module builds, **call it; do not edit it**. Raise a pre-flight point if a call is impossible without an edit.

## 4. Builder, store and reader (`B/chain/`)

New package `B/chain/` (no `__init__` side effects):
- `policy.py`: the loaders from §2.
- `grading.py`: pure.
- `measures.py`
- `ports.py`
- `builder.py`
- `reader.py`
- `snapshots.py`: the CLI.
- `adapters/postgres_snapshot_store.py`: the writer.
- `adapters/postgres_chain_inputs.py`: the input reader.

### 4.1 `grading.py` (pure, A1)

```python
def period_bounds(cal, tz, local_day, period) -> tuple[datetime, datetime] | None   # None = NOT_EXPECTED
    # operating_hours: union of the day's declared hours (local → UTC); midday: local 12:00–13:00 if expected
def covered_seconds(intervals, lo, hi) -> int      # union of intervals clipped to [lo, hi), no double counting
def classify_day(expected, required, covered, pending, bands, threshold) -> str
    # not expected → NOT_EXPECTED; pending → PENDING; pct = covered/required (required 0 → NO_DATA)
    # pct >= (threshold or bands.complete) → COMPLETE; pct >= bands.partial → PARTIAL; pct > 0 → LOW; else NO_DATA
def input_fp(ids, pending, policy_version, calendar_version, catalogue_version, adapter_key) -> str
    # sha256 hex of sorted ids + pending flag + versions
    # (review M1) ids include, for EVERY measure with analytic inputs, the selected analytic run/revision id:
    #   dispatch selection (avoidable_gen_min), mini_depth_revision (noon_headroom_kw),
    #   cold assessment run (chamber_temp_c, backup_start_chain), EV assessment/session revision (charging_kwh),
    # so a re-assessment over the same evidence adds a revision, and PENDING -> settled always re-revisions
```

- PENDING takes precedence over grading only when `expected`.
- `coverage_pct` = round(100 × covered/required, 2), capped at 100.

### 4.2 `builder.py` `SnapshotBuilder.build(tenant_id, site, local_day, measure) -> list[Written]`

For each subject from `adapter.subjects`:
1. Compute the period.
2. Read the inputs.
3. Grade.
4. `value = adapter.measure(...)` when covered > 0 (AG-4: calculate anyway).
5. `money = adapter.money(...)` when the value is not None.
6. Compute the fp.
7. If the fp equals the latest revision's `input_fp`, skip (idempotent).
8. Otherwise append `revision = latest + 1`.

`build_range(tenant_id, site, from_day, to_day, measures=None)` loops the days in the Site's tz over the measures for the Site's domain. It is the entry point for the CLI and for CH-2's backfill step (a).

### 4.3 `adapters/postgres_snapshot_store.py`

- `append(row)` is a plain INSERT.
- `latest_fp(key)` and `latest_revision(key)` read the store.
- It is insert-only; any UPDATE or DELETE text in the file fails the guard.

### 4.4 `reader.py` `SnapshotReader`

```python
latest(tenant_id, site_id, from_day, to_day, measures=None, known_at=None) -> list[SnapshotRow]
    # latest revision per (local_day, subject_kind, subject_ref, measure); with known_at: latest computed_at <= known_at
grade_counts(tenant_id, site_id, from_day, to_day, measures, known_at=None) -> GradeCounts
    # {requested, expected, complete, partial, low, no_data, not_expected, pending, enough_data_days}
    # enough_data_days = days where every listed measure (every subject) is COMPLETE  (A1 last line)
```

`GradeCounts` is the single "graded day count" that CH-5a and CH-6 will render. It is a frozen dataclass with a `to_json()`.

**Measured need (QW-1, design §11b measured diagnosis).** The board spends 1.25 s in `evidence_readiness`, and the summary 1.5 s in readiness. CH-5a will replace both with snapshot reads. So the reader also offers `grade_counts_many(tenant_id, site_ids, from_day, to_day, measures_by_site, known_at=None) -> dict[site_id, GradeCounts]`.

- It runs **one** SQL statement for all Sites, using `DISTINCT ON` over the read index.
- An L2 test asserts its result equals `grade_counts` per Site, and that it runs one statement (count the cursor executes).
- On the L3 clone, report its time for the three Sites over the story month. The target is ≤ 50 ms (est.).

### 4.5 CLI `python -m assetops_backend.chain.snapshots`

```
build --site <code> [--from YYYY-MM-DD --to YYYY-MM-DD] [--measure <key> ...] [--tenant <slug>]
show  --site <code> --from --to [--measure ...] [--known-at <iso>]
```

- It is modelled on `B/declare_objective.py`: argparse `prog`, the tenant defaults to `DEVELOPMENT_TENANT_SLUG` and any other tenant exits 2, DATABASE_URL is required (exit 1 without it), and it writes one JSON line per written row or per day.
- The default range is from the Site's first accepted evidence day to today, local.
- The CLI is composed in `B/chain/composition.py` (the pattern of `B/objectives/composition.py:12`).

## 5. Expected results on the L3 clone (the design's A1 data check; S = 2026-10-31)

| Site · day | Measure | Expected grade | Expected value / money |
|---|---|---|---|
| Kobo 28, 30, 31 Oct | `avoidable_gen_min`, `productive_kwh` | **PARTIAL**, 8 of 24 h at about 33%, under the 24 h calendar (§2 ruling). The design's "8 of 8 h COMPLETE" assumed the withdrawn 06:00–14:00 calendar. They become COMPLETE only after DD-1's extension. | 31 Oct `productive_kwh` 0 kWh; 30 Oct 168.3 kWh, money 42.08 USD (WALK1-G2 report). Values are calculated anyway (AG-4). |
| Kobo 31 Oct | `noon_headroom_kw` | COMPLETE | 25–31 kW |
| Kobo 21 Oct, and 25, 26, 27, 29 Oct | all Kobo measures | NO_DATA (`noon_headroom_kw` has no value) | none. This is the I-14 basis. |
| EV 26 Oct | `charging_kwh` | NOT_EXPECTED | none |
| EV 27 Oct; EV 20 Oct | `charging_kwh` | **LOW** (about 1 of 8 declared hours) until DD-1 | 27 Oct: 15 kWh, 4.50 USD. 20 Oct: money 9.00 USD (register I-05). The values are calculated anyway (AG-4). |
| Cold 28 Oct | `chamber_temp_c` / `backup_start_chain` | NO_DATA / LOW (covered by backup-role readings only in the session) | none / chain |
| Cold 31 Oct | `chamber_temp_c` | **LOW** (about 65 min of 24 h) until DD-1 | peak 4.9 °C (the highest probe reading in the period) |

## 5c. Pre-flight rulings (CH-1a pre-flight Q1–Q8, 2026-11-03)

1. **EV calendar:** Tuesdays 08:00–16:00, from the declared schedule (§2).
   - `charging_kwh` coverage = the seconds in the period with a known connector state: the session meter intervals ∪ the status intervals the charger reports, minus `unknown_meter_seconds`.
   - Idle time with a known status counts as covered at 0 kWh. Time with an unknown status does not count.
2. **Cold calendar:** 24 h, with no inferred session (§2).
   - The inferred session hours, and the scenario/story-day mismatch (19:00–20:00 UTC versus 16:00–17:05 UTC), go into SWEEP-DS's inventory.
3. **`avoidable_gen_min`:**
   - (a) Accepted. Coverage = the union of the accepted-reading intervals that the selected dispatch run used, clipped to the local period.
   - (b) Accepted. The value is `{"minutes": Σcandidate, "indeterminate_minutes": Σindeterminate}`.
   - (c) **Do not import the private helper.** QW has merged, so the QW-file restriction lapses. Move `_dispatch_minutes` unchanged into a public pure function, `dispatch_minutes(intervals)`, in `B/analytics/dispatch_read.py`. Make `B/site_outcomes/mini.py:615` import it. That is one rule with two callers. A test asserts the board output is byte-identical before and after (the existing `test_out_b1_board.py`, `test_out_b4_board_postgres.py`).
   - (d) Accepted. Read both overlapping UTC days, and clip their intervals to the local period.
4. **`noon_headroom_kw`:** accepted. Read the stored, selected `mini_depth_revision.result`, and do not recompute.
   - For ELIGIBLE or EXCLUDED, the value is `{"low_kw", "high_kw", "decision"}`.
   - For LIMITED or CONFLICT, the value is `{"low_kw": null, "high_kw": null, "decision": null, "result_state": "<LIMITED|CONFLICT>"}`.
   - Coverage = the hour minus the result's gaps. PENDING = a live `mini_renewable` job.
5. **`backup_start_chain`:** the coverage is not built from the instant events.
   - Coverage = the seconds in the period covered by the accepted readings of the backup-chain roles (grid, generator, transfer and bus status; `B/analytics/cold.py:39-55`).
   - The value is `{"starts": n, "failed": n}` from `backup_chain(...)`. A covered night with no start request is valid: the value is `starts: 0`, never NO_DATA.
6. **`chamber_temp_c`:**
   - Coverage = the period minus `temperature().gaps`.
   - The value is the highest probe reading in the period, from the raw `chamber_temperature` readings through `ChainInputReader`. The peak is a daily measure; an excursion is a Finding.
7. **Zero kWh:** money is `0.00` in the price's currency on a priced day. Whether the board shows it is CH-6's display rule.
8. **L2 seeding:** accepted as proposed. `noon_headroom_kw` uses the real adapter on MG-W402. `productive_kwh`, idempotency and revision 2 use a stub `ChainInputReader` against the real store. The real productive adapter is then proven on the L3 clone (§6 step 4).
- **The builder's deviations are accepted:** the JSON read in `chain/adapters/file_chain_config.py`, one window per day in v1, and the branch name `task/CH-1a-snapshots`.

**Effect on the client story until DD-1 extends the days (for the owner):**
- Kobo days are PARTIAL (8 of 24 h). They are counted and labelled, but the monthly target reads "too early to judge".
- Cold nights and EV days are LOW.
  - They are shown with "too little data", not totalled.
  - EV's charging income stays visible on its board, but is left out of the Portfolio Grow total.
  - Protect findings are unaffected.
- **DD-1 extends the story days of all three Sites to their declared hours**, using existing scenarios only.
  - **Budget:** the whole prepare may grow by at most 50% (951 s measured at G2, so a cap of about 1,430 s). Kobo is the costly one, at 611.8 s.
  - If it does not fit, or no scenario fits, the grades stay as they are, shown honestly, and the owner is told before E3.

- A difference from this table is **not** fixed by tuning. Report it in the packet with the reason; the Architect rules on it.
- **Note on the clone date:** the clone's data is dated S = 2026-10-31, so its local-day range is fixed. Build over `2026-10-01..2026-11-02`.

## 5b. Demo-shaped logic this slice touches (standing rule DS-R1, plan §2.3)

| Item | Touched how | Resolution in this slice |
|---|---|---|
| 5. Config fitted to the data (operating hours) | It declares the calendar | **Fixed.** Kobo and Cold are 24 h. EV uses its declared connector schedule, Tuesdays 08:00–16:00, which `source` cites. No hours are chosen to fit the data (§2, §5c). |
| 4. One-noon-hour spare-solar read (`B/mini_depth/inputs.py:79-80`) | The `noon_headroom_kw` period adopts it | **Labelled keep, owned by CH-9.** The measure spec carries `period: midday` with a comment `# DS-R1 keep: one-noon-hour basis; CH-9 replaces with the declared daylight window`. The policy loader exposes the period name, so CH-9 changes it in one place. |
| 3. Generator-shaped subject | `avoidable_gen_min` uses the generator asset | **Fixed for snapshots.** Subjects are generic ASSET or SITE refs from stored columns (AG-10); nothing assumes a generator outside the Kobo adapter. |
| 3. Dispatch thresholds held as constants | Not touched; the adapter reads the dispatch result only | Not in scope (SWEEP-DS / CH-8). |

Reviewers check this table against the diff (DS-R1).

## 6. Localised test ladder (no full suite, no full vitest, no demo prepare)

1. **L0, pure:** `tools\run-host-tests.ps1 -- backend/tests/test_ch1a_grading.py`. Truth tables for:
   - `classify_day`: every band edge (0, >0, 0.25, 0.7999, 0.8, 1.0, the threshold override, PENDING, NOT_EXPECTED, required 0);
   - `covered_seconds`: overlaps, clipping and touching intervals;
   - `period_bounds`: Addis and UTC, the TUE-only calendar, `24:00`, a DST-free check;
   - `input_fp`: stable under id order, changing on each version;
   - the policy and calendar loaders: valid, invalid range, unknown day name.
2. **L2, Postgres, scoped:** `tools\run-host-tests.ps1 -- backend/tests/test_ch1a_snapshot_postgres.py`. This uses `pg_harness.fresh_database()` as `backend/tests/test_s1_bindings_postgres.py:66-85` does, which migrates to head and so proves 0043 and its `down_revision`.
   - The 0043 catalogue: columns, CHECKs, indexes, the trigger.
   - UPDATE and DELETE are refused.
   - Downgrade is refused with a row present, and succeeds with none.
   - The builder on a small seeded set-up: one Site, 3 days, `productive_kwh` and `noon_headroom_kw`. Seed through the existing ingestion helpers that `test_w402_reads_postgres.py:49-70` uses (`_ingest`, `_reconcile`), and register the set-up in `setup_cache` `FUNCTION_OPS` (`backend/tests/setup_cache.py:77`) so reruns take seconds.
   - Idempotency: a second `build_range` writes 0 rows. A changed input writes revision 2.
   - `grade_counts` matches the expected counts.
3. **Existing, scoped** (they import modules the adapters call; run them unchanged):
   - `backend/tests/test_w301_estate_coverage.py`
   - `backend/tests/test_cov_partial_portfolio.py`
   - `backend/tests/test_walk1_objective_min_days_postgres.py`
   - any test file importing `site_outcomes.productive_use` or `mini_depth.rules` (list them in the packet).
4. **L3, real data:**
   - `python tools/chain_clone.py create ch1a --migrate`.
   - With DATABASE_URL set to the clone, run `python -m assetops_backend.chain.snapshots build --site KOBO-001 --from 2026-10-01 --to 2026-11-02`, then the same for COLD-LAB-001 and EV-LAB-001.
   - Run `show` for each Site and compare with §5.
   - Time the build: the budget is ≤ 50 ms per measure-day (§11b). Report the measured number.
   - Run the build a second time and expect 0 rows written.
   - `python tools/chain_clone.py drop ch1a`.
   - Only with serve stopped, and on a quiet machine.
5. **Guards, run directly** with their check-all lines:
   - A, Architecture seams (`tools/check-all.ps1:56`);
   - W, Agent workflow (`:59`);
   - the chain-coherence fixtures line (from CH-0);
   - **the estate guard self-tests** (`:57`, about 6 min). They run here because this slice edits `tools/checks/configuration-persistence.ps1`. That is the plan's §4.3 exception.
   - All other guards are deferred.

## 7. Guard registration (`tools/checks/configuration-persistence.ps1`)

Follow the `$trialComparisonWriter` example exactly (research: `:866-869`, `:878`, `:933`, `:938`, `:1012`, `:1234-1247`, `:1499-1501`):
- `$snapshotWriter = "backend/assetops_backend/chain/adapters/postgres_snapshot_store.py"` with `$snapshotTables = @('site_day_snapshot')` and an insert-only rule.
- Add it to `$pgWriters`.
- `$pgReaders` gains `backend/assetops_backend/chain/adapters/postgres_chain_inputs.py`.
- A `chain` context entry goes in the `$domains` list (`:52-186`), with the `objectives` entry (`:177-185`) as the model.
- The anti-vacuity check must see at least one INSERT into `site_day_snapshot`.

## 8. Pre-flight items (answer from code, batch them, then stop)

- **P1.** The declared productive-price read: the table or adapter from `M/0040_walk1_productive_price.py` and its "valid that day" rule. Do the same for the EV declared tariff (WALK1-2).
- **P2.** How supply-use=PRODUCTIVE assets are found (the Foundation property behind `ports.productive_readings`, `B/mini_depth/read.py:382`).
- **P3.** The dispatch result fields for `avoidable_gen_min` (minutes, assessed interval), and the PENDING signal for S3 and mini jobs: which job table and statuses.
- **P4.** The cold chamber-temperature role and the backup start-chain inputs, from the cold assessment code.
- **P5.** The EV session energy source and the "completed" flag.
- **P6.** Whether any adapter needs a function that only exists inside a QW-touched module in a non-pure form. If so, propose the smallest call shape; do not edit the module.
- **P7.** Where the Cold lab and EV lab session windows are declared, outside `backend/conversions/demo-story-days-v1.json`: the lab scenario or the w502/w504 producers. Cite file:line for each calendar `source`. If they are declared nowhere else, say so (§2 ruling).

## 9. Review focus

- Every grade comes from `grading.classify_day`, and every count from `SnapshotReader.grade_counts`. No second day-count rule is added.
- The calendar and policy are declared files with versions in `input_fp`, and no numbers are tuned.
- DS-R1: the §5b table matches the diff. Kobo is not given hours that fit the data.
- The store is insert-only, and the downgrade refuses.
- No edits to QW files, matchers, money models or verification rules (High).
