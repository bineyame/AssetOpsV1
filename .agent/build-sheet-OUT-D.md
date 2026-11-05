# Build sheet OUT-D · declared objectives and status (self-contained)

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-30, owner away (decisions delegated; every call is in
`.agent/decisions-while-owner-away-2026-10-30.md`). Code read at main **`833e7c95`**. Build after OUT-W merges.
Branch **`task/OUT-D-declared-objectives`**, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outD`.
Backend paths are relative to `backend/assetops_backend/` unless they start with `backend/`, `tools/` or `frontend/`.
**This sheet replaces the Slice D outline of `build-spec-outcome-sprint-2026-10-29.md` for building.** Read nothing
else unless a step names it.

## 0. Rules that bind every unit

- Do not touch `main.py`, `field/ gateway/ contracts/ simulator/ host/ contract-fixtures/`, `estate/financials.py`,
  `financials/**`, `estate/money_invariants.py`, any existing migration. D adds **one** migration and edits exactly
  one guard (`tools/checks/configuration-persistence.ps1`, U1).
- `outcomes/*.py` stays pure (AST test `backend/tests/test_out_a1_outcome_map.py`: `__future__`, `dataclasses`,
  `typing`, `collections.abc`, `outcomes.*`). No `Decimal` import there: composers pass `Decimal` values that the
  pure module only **compares**, plus pre-formatted number texts.
- A **leading** objective never carries money (DB CHECK and pure test). Only `energy_cost_per_km` is a money target.
- No outcome code, measure key, verdict code or policy version on screen, in `title` or `aria-label`.
- The frontend authors no "Not available yet" text. D adds no such string at all.
- Every string in §4 was scanned against `terms` + `w1.terms` + `w1.codes` + the w1 patterns of
  `frontend/src/test/productVocabulary.json`: 0 hits. Scan any string you add the same way.

## 1. Code reality (verified at 833e7c95)

| Element | Source | Verdict |
|---|---|---|
| Status rules | `outcomes/status.py:52-77` `outcome_state` (rules 1-6, 8; `NO_OBJECTIVE` fallback `:77`), `STATUS_POLICY = "outcome-status/1"` `:14`, labels/tones `:24-29` (ON_TRACK green, NO_OBJECTIVE gray) | **EXTEND** to `/2` |
| Board calls status | `site_outcomes/board.py:369-376` `_row` → `outcome_state(o, settled=..., signals=..., readiness=...)`; contributors `:497`; NOT_MEASURED rows return early `:390-392` | **EXTEND** |
| Mini MG-2 measure | `site_outcomes/mini.py:361` `_dispatch_minutes(dispatch)` → `(avoidable, unclear)` minutes (`Decimal|None`), already read `:247` | OK |
| Mini MG-5 measure | mini depth `service.cards.unserved_kwh` (`mini_depth/read.py:63`; computed for the critical role, `mini_depth/rules.py:449-524`); `None` when not known | OK (may be None in data) |
| Mini MG-1 measure | no sales or productive-use energy record anywhere | **NOT AVAILABLE** → objective "Not checked yet" |
| Cold CC-1 objective | the existing chamber range: overview `objective {policy_low_deg_c, policy_high_deg_c, limitation}` (`analytics/cold_site_reads.py:356-371`), read in `cold.py:118` | OK (read, **not** stored) |
| Cold CC-1 measure | open in-window `COLD_EXCURSION` Finding (`cold.py:110-111`, `by_mech`) | OK |
| Cold CC-6 measure | `_backup` facts: `START_FAILURE` in `needs_attention` codes / `backup_summary.observed_success` (`cold.py:230-239`) | OK |
| EV EV-1 measure | overview `denominator.fault_aborted`, `incomplete + contradictory` (`ev.py:130-133`) | OK |
| EV EV-2 | catalogue `measured = False` (`outcomes/catalogue.py`), row NOT_MEASURED | stays Not measured |
| Mini Assure line | `mini.py:50` `FIXED["plan_target"]`, used `:574` | **REPLACE** when objectives exist |
| Portfolio Assure detail | `frontend/src/estate/PortfolioOutcomes.tsx:167` "No verified result yet · no targets declared · {gap}" | **REPLACE** |
| Declared-input pattern | `financials/assumptions.py:59-73` `SystemPrincipal`, `SYSTEM_CHANNELS = ("SYSTEM_CLI", "SYSTEM_FIXTURE")`; CLI `publish_assumption.py` (`fixture` subcommand, idempotent, exit 3 on refusal) | OK (copy) |
| Append-only trigger | `w4_append_only()` (migration 0027) | OK |
| Board wiring | `site_outcomes/composition.py:51-73` opens its own store from `database_url` (`build_global_work_read`); no `main.py` edit needed | **EXTEND** |
| Writer guard | `tools/checks/configuration-persistence.ps1:852-854` `$pgWriters`; per-writer table confinement as `$assumptionWriter` (`:692-694`, `:1241`) | **EXTEND** |
| Migration head | main head `0035_w5_ev_work`; `0036_cc_mini_contribution`, `0037_cc_trial_cost_comparison` exist only on `task/CC-M-combined-schema`; 20 test files assert the head literal (`grep -rln "0035_w5_ev_work" backend tools`, excluding `migrations/versions`) | see U1 |

## 2. Migration number (decided)

D's migration is **`0038_out_objectives`** with `down_revision = "0035_w5_ev_work"`. It does not use 0036 or 0037,
so CC-M's files merge in E byte-for-byte (except the docstring rewording). E then adds an empty alembic merge
revision `0039_merge_objectives_cc` with `down_revision = ("0037_cc_trial_cost_comparison", "0038_out_objectives")`
(OUT-E §2 E1). Neither slice edits a merged migration.

## 3. Units (6). Effort 4.5 builder days including one full suite

### U1 · Migration, head literals, writer guard · 0.75 d · per-unit review
Files: new `backend/migrations/versions/0038_out_objectives.py`; new `backend/tests/test_out_d1_schema_postgres.py`;
the 20 head-literal files; `tools/checks/configuration-persistence.ps1`; `tools/writer_guard_probes.py` if the
probe corpus lists writers.
- Migration (pattern of CC-M 0037: module constants, `_in`, `SCHEMA` string, `op.execute`; downgrade drops the table):
```sql
CREATE TABLE outcome_objective_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    outcome_key text NOT NULL CHECK (outcome_key ~ '^(MG|CC|EV)-[1-9]$'),
    revision_no integer NOT NULL CHECK (revision_no > 0),
    supersedes_revision_id uuid NULL,
    measure_key text NOT NULL CHECK (measure_key IN ('avoidable_generator_minutes','productive_use_kwh',
        'unserved_critical_kwh','backup_start_failures','interrupted_sessions','energy_cost_per_km')),
    measure_kind text NOT NULL CHECK (measure_kind IN ('VALUE','LEADING')),
    comparison text NOT NULL CHECK (comparison IN ('AT_MOST','AT_LEAST')),
    target numeric NOT NULL CHECK (target >= 0),
    unit text NOT NULL CHECK (unit IN ('min/day','kWh/month','kWh','failures','sessions','currency/km')),
    currency text NULL CHECK (currency ~ '^[A-Z]{3}$'),
    window_rule text NOT NULL CHECK (window_rule IN ('BOARD_DAY','BOARD_WINDOW')),
    source text NOT NULL CHECK (source IN ('DECLARED','RECORDED')),
    source_note text NOT NULL CHECK (length(source_note) BETWEEN 1 AND 500),
    actor_kind text NOT NULL CHECK (actor_kind = 'SYSTEM'),
    actor_id text NOT NULL CHECK (actor_id ~ '^service:[a-z0-9-]+$'),
    authorization_basis text NOT NULL CHECK (length(authorization_basis) BETWEEN 1 AND 500),
    source_channel text NOT NULL CHECK (source_channel IN ('SYSTEM_CLI','SYSTEM_FIXTURE')),
    idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 8 AND 128),
    payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    recorded_at timestamptz NOT NULL,
    CONSTRAINT outcome_objective_revision_chain_check CHECK ((revision_no = 1) = (supersedes_revision_id IS NULL)),
    CONSTRAINT outcome_objective_revision_money_check CHECK ((unit = 'currency/km') = (currency IS NOT NULL)),
    CONSTRAINT outcome_objective_revision_leading_no_money CHECK (measure_kind = 'VALUE' OR currency IS NULL),
    CONSTRAINT outcome_objective_revision_site_fk FOREIGN KEY (tenant_id, site_id) REFERENCES site(tenant_id, id),
    CONSTRAINT outcome_objective_revision_no_unique UNIQUE (tenant_id, site_id, outcome_key, revision_no),
    CONSTRAINT outcome_objective_revision_id_unique UNIQUE (tenant_id, site_id, outcome_key, id),
    CONSTRAINT outcome_objective_revision_supersedes_fk FOREIGN KEY (tenant_id, site_id, outcome_key,
        supersedes_revision_id) REFERENCES outcome_objective_revision(tenant_id, site_id, outcome_key, id),
    CONSTRAINT outcome_objective_revision_idempotency_unique UNIQUE (tenant_id, site_id, idempotency_key)
);
CREATE INDEX outcome_objective_revision_read ON outcome_objective_revision (tenant_id, site_id, outcome_key, recorded_at);
CREATE TRIGGER outcome_objective_revision_immutable BEFORE UPDATE OR DELETE ON outcome_objective_revision
    FOR EACH ROW EXECUTE FUNCTION w4_append_only();
```
- Head literal `"0035_w5_ev_work"` → `"0038_out_objectives"` wherever it means "the current head" (the CC-M review
  list: `tests/mini_depth_probe.py:22`, `test_s1_bindings_postgres.py:118`, ... `test_w504_ev_intent_postgres.py:45`;
  re-grep). A downgrade **target** or a `down_revision == PARENT` assertion stays. List every file in the packet.
- Guard: `$objectiveWriter = "$backendRoot/objectives/adapters/postgres_objective_store.py"` added to `$pgWriters`;
  `$objectiveTables = @('outcome_objective_revision')` INSERT-only (no UPDATE/DELETE/TRUNCATE/MERGE/COPY/DO UPDATE from
  any module); only that writer writes it; an INSERT-seen anti-vacuity counter like `$domainIntentInsertsSeen`
  (`:845`). Follow the `$domainIntentWriter` lines exactly (`:852-854`, `:907`, `:911`). No other rule changes.
- Test (`pg_harness` module-fresh DB, pattern `test_cc_schema_postgres.py` on the CC-M branch): catalog (columns,
  constraint names, index, trigger); `upgrade head`, `downgrade 0035_w5_ev_work`, `upgrade head`, `assert_at_head`;
  each CHECK refuses by name (bad outcome key, bad measure, `LEADING` with a currency, `currency/km` without one,
  revision 2 without supersedes); UPDATE and DELETE refused by the trigger.

### U2 · Pure objective rule and status `/2` · 0.5 d · per-unit review
Files: new `outcomes/objectives.py`; `outcomes/status.py`; tests `backend/tests/test_out_d2_objectives.py`,
`test_out_b1_status.py`.
```python
POLICY = "outcome-objectives/1"
MET, MISSED, NOT_JUDGED = "MET", "MISSED", "NOT_JUDGED"
VERDICT_LABEL = {MET: "Met", MISSED: "Missed", NOT_JUDGED: "Not checked yet"}
VERDICT_CHIP = {MET: {"label": "Met", "tone": "green"}, MISSED: {"label": "Missed", "tone": "amber"},
                NOT_JUDGED: {"label": "Not checked yet", "tone": "gray"}}
@dataclass(frozen=True) class Measure: key; outcome; kind; comparison; unit; target_zero: str; target_any: str
MEASURES: Mapping[str, Measure]          # the six keys of §4 (outcome, kind, comparison, unit, templates)
@dataclass(frozen=True) class ObjectiveFact:
    outcome_key: str; measure_key: str; comparison: str; target: Any; target_is_zero: bool; target_text: str
    source: str; revision_id: str | None      # None = read from an existing Site policy (CC-1)
@dataclass(frozen=True) class Reading:
    value: Any | None; complete: bool; actual_text: str | None
def judge(o: ObjectiveFact, r: Reading | None) -> str
```
- `judge`: `r is None or r.value is None` → NOT_JUDGED. `AT_MOST`: `value > target` → MISSED (even when incomplete:
  the miss is already proven); `value <= target` and `complete` → MET; else NOT_JUDGED. `AT_LEAST`: `value >= target`
  → MET; `value < target` and `complete` → MISSED; else NOT_JUDGED. Values are only compared.
- `status.py`: `STATUS_POLICY = "outcome-status/2"`. `outcome_state(..., objective: str | None = None,
  objectives_ok: bool = True)`; defaults keep every B/C call byte-identical. Order (first match wins):
  1 N/A · 2 NOT_MEASURED · 3 UNKNOWN unsettled · **4** NEEDS_ATTENTION: (a) primary Finding open, not applied;
  (b) warning NEEDS_ATTENTION; **(c) `objective == MISSED` → reason `OBJECTIVE_MISSED`** · 5 WATCH (unchanged) ·
  6 OPPORTUNITY · **7 `objective == MET` → ON_TRACK, `OBJECTIVE_MET`** · **7b `objective == NOT_JUDGED` → UNKNOWN,
  `OBJECTIVE_NOT_JUDGED`** · **7c `not objectives_ok` → UNKNOWN, `OBJECTIVES_NOT_READ`** · 8 NO_OBJECTIVE.
  7b sits after 6, so a Site with an open opportunity keeps Opportunity (Kobo Grow).
- Roll-up unchanged. §1.4's "a row is On track only when every applicable outcome is" already holds: precedence puts
  NO_OBJECTIVE and UNKNOWN above ON_TRACK.
- Tests: every `judge` branch (both comparisons × met/missed/incomplete/None); each new status rule positive and
  negative; 4c loses to 4a only in its reason; 7 loses to 5 and 6; 7b loses to 6; NOT_MEASURED beats an objective;
  MEASURES leading entries have no money unit; every template passes the vocabulary scan (Python copy, as
  `test_out_a1_outcome_map.py` test 5); golden grid in `test_out_b1_status.py` unchanged when no objective is passed;
  policy string updated wherever asserted (list them).

### U3 · Store, declare command, demo file · 1.0 d · per-unit review
Files: new package `objectives/` (`__init__.py`, `model.py`, `adapters/__init__.py`,
`adapters/postgres_objective_store.py`, `composition.py`); new `declare_objective.py` (top level, beside
`publish_assumption.py`); new `backend/conversions/demo-objectives.json`; tests
`backend/tests/test_out_d3_declare.py` (pure) and `backend/tests/test_out_d3_objective_store_postgres.py`.
- `model.py`: `Declaration(site_code, outcome_key, measure_key, target: Decimal, currency: str | None, source,
  source_note, expected_prior: UUID | None, idempotency_key)`; `validate(decl) -> None` raising `ObjectiveRefused
  (status, code, message)` (422 `OBJECTIVE_INVALID`: unknown measure, measure not of that outcome per
  `outcomes.objectives.MEASURES`, negative target, currency rules); `payload_sha256(decl)` (sorted compact JSON
  without the key); `SYSTEM_DECLARER = SystemPrincipal("service:assetops-objective-declarer", "SERVER_ADMINISTRATIVE_
  TRIGGER: declared by the server-side objective declarer for the demonstration; not a customer target")` (reuse
  `financials.assumptions.SystemPrincipal`). `unit`, `measure_kind`, `comparison`, `window_rule` come from MEASURES
  (window_rule: mini `BOARD_DAY`, cold/EV `BOARD_WINDOW`), never from the caller.
- Store: `declare(tenant_id, decl, principal, channel) -> (row, inserted)`: one transaction, `SELECT ... FOR UPDATE`
  of the current head for `(tenant, site, outcome)`; same key + same payload → stored row, `inserted=False`; same key,
  other payload → 409 `IDEMPOTENCY_KEY_REUSED`; `expected_prior` ≠ head id (None vs a head, or the reverse) → 409
  `OBJECTIVE_PRIOR_MISMATCH`; unknown Site → 404 `SITE_NOT_FOUND`; else INSERT with `revision_no = head+1`,
  `supersedes = head`, `recorded_at = clock_timestamp()`. `current(tenant_id, site_id, known_at: datetime | None)
  -> list[dict]`: `DISTINCT ON (outcome_key) ... WHERE recorded_at <= coalesce(:k, now()) ORDER BY outcome_key,
  revision_no DESC`. That cutoff is what makes an earlier reading reproducible.
- `composition.py`: `build_objective_store(database_url) -> PostgresObjectiveStore | None` (None without a URL);
  the only importer of the adapter.
- CLI `python -m assetops_backend.declare_objective fixture --file backend/conversions/demo-objectives.json
  [--site CODE ...]` and `declare --site ... --outcome ... --measure ... --target ... [--currency ...] --source-note
  ... --expected-prior none|<uuid> --idempotency-key ...`. `main(argv, store=None)` for in-process use. Output one
  JSON line per row; refusal exit 3. A fixture entry whose Site is not imported is skipped with a JSON `skipped`
  line (one file serves every demo DB).
- `demo-objectives.json` (owner-accepted defaults; each `source: "DECLARED"`, `source_note: "Declared for the
  demonstration; not a customer target"`, keys `out-d-{site}-{outcome}-v1`):

| Site | Outcome | Measure | Comparison | Target | Unit |
|---|---|---|---|---|---|
| KOBO-001 | MG-2 Supply cost per kWh | avoidable_generator_minutes | AT_MOST | 0 | min/day |
| KOBO-001 | MG-1 Productive electricity sales | productive_use_kwh | AT_LEAST | 300 | kWh/month |
| KOBO-001 | MG-5 Reliable service | unserved_critical_kwh | AT_MOST | 0 | kWh |
| COLD-LAB-001 | CC-6 Cooling continuity | backup_start_failures | AT_MOST | 0 | failures |
| EV-LAB-001 | EV-1 Buses ready for service | interrupted_sessions | AT_MOST | 0 | sessions |
| EV-LAB-001 | EV-2 Energy cost per km | energy_cost_per_km | AT_MOST | 0.20 USD | currency/km |

  CC-1 Stock kept saleable is **not** in the file: it is the existing chamber range, read from the cold overview (U4).
- Postgres test (fresh `assetops_out_d_store_test`): fixture twice → 6 rows then 6 `inserted=False`; a v2 for KOBO
  MG-2 (target 5, expected prior = v1) → revision 2; **reproducibility**: `current(K1)` before v2 returns v1,
  `current(None)` returns v2, `current(K1)` after v2 still returns v1; prior mismatch and key reuse refusals; the
  trigger refuses UPDATE.

### U4 · Board: readings, verdicts, contributors, summary · 1.0 d · slice review (shared seam)
Files: `site_outcomes/read.py`, `composition.py`, `board.py`, `mini.py`, `cold.py`, `ev.py`; tests
`backend/tests/test_out_d4_board.py`; fakes in `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`, `test_out_b4_read.py`
only if they break (list them).
- Port: `BoardServices.objectives: Any = None`; `build_outcome_board_service` sets
  `objectives=build_objective_store(database_url)` and disposes it. `_shared` adds
  `"objectives": lambda: _need(s.objectives, "objectives").current(site.tenant_id, site.site_id, known_at)`.
  `MiniPorts`/`ColdPorts`/`EvPorts` gain `objectives: Callable[[], list[dict]] = lambda: []` as the **last** field
  (existing fakes keep compiling; read.py always passes the real port).
- Each composer: `rows = reads.call("objectives", ports.objectives)`; `objectives_ok = rows is not None` (a failed
  read is PARTIAL, as every port). Build `ObjectiveFact`s from rows (target text from the measure template, number
  via `num`, currency appended for money) and `Reading`s per outcome key, then pass both on `SiteFacts`:
  new fields `objectives: tuple[ObjectiveFact, ...] = ()`, `readings: Mapping[str, Reading] = {}`,
  `objectives_ok: bool = True`.

| Outcome | Reading.value | complete | actual_text |
|---|---|---|---|
| MG-2 | `avoidable` minutes | `unclear == 0` | "{a} min longer than needed on this day"; `a == 0 < unclear`: "{u} min not yet clear on this day"; dispatch None → Reading None |
| MG-1 | None | False | "sales not recorded" |
| MG-5 | `service.cards.unserved_kwh` | value not None | "{x} kWh not served"; None → "critical demand not measured" |
| CC-1 | 1 if an open in-window excursion else 0 | `findings_ok` and `objective.limitation is None` | "above {high}°C in this window" / "held in range in this window" |
| CC-6 | 1 if `START_FAILURE` code, 0 if `observed_success > 0`, else None | overview loaded | "automatic start failed" / "started by itself" / "no backup start in this window" |
| EV-1 | `fault_aborted` | `unknown == 0` | "{f} interrupted" + (" · {u} {outcome|outcomes} unknown" when u > 0) |

  CC-1's `ObjectiveFact` is built from the overview `objective` block when `policy_low_deg_c` and `policy_high_deg_c`
  are both set: measure `excursions` (internal, not stored), `AT_MOST 0`, `source "DECLARED"`, `revision_id None`,
  target text "Stock kept saleable: chamber held between {low} and {high}°C".
- `board.py` `_row`: per outcome, `verdict = judge(objective, readings.get(key))` when an objective exists and the
  outcome is settled, else None; pass `objective=verdict, objectives_ok=facts.objectives_ok` to `outcome_state`.
  After the domain contributors, one contributor per objective of this row's outcomes, in catalogue order:
  `{"key": f"declared_objective:{key}", "label": "Declared objective", "text": f"{target_text} · {actual_text}"`
  (just `target_text` when no actual), `"confidence": VERDICT_CHIP[verdict or NOT_JUDGED], "href": None}`.
  NOT_MEASURED rows stay as today (EV-2 shows no line; R583).
- Board wire: `policy_versions.objectives = "outcome-objectives/1"`; top-level `"objectives": [{"outcome_key",
  "outcome_label", "source", "revision_id", "verdict"}]` (verdict codes never rendered).
- Mini Assure (`mini.py:574`): with ≥ 1 mini objective, "Actual against plan" text =
  "{met} of {n} declared objectives met" + (" · {u} not checked yet" when u > 0), chip none, href None; with none,
  keep `FIXED["plan_target"]`. Add the template strings to `COPY`.
- Summary (`read.py` `summary()`): `objective_site_count` = Sites whose board `objectives` is non-empty (a failed
  Site counts 0). `null` when every Site failed.
- Tests: verdict → status per rule with fake readings (Kobo MG-2 12 min → Missed → cost row NEEDS_ATTENTION reason
  4a still first; MG-2 0 min, unclear 0, no Finding → ON_TRACK; MG-1 with headroom → OPPORTUNITY, contributor
  "Not checked yet"); objectives port failure → PARTIAL and unjudged outcomes UNKNOWN; contributor order and text;
  CC-1 from the policy only; summary count; no measure key, verdict code or policy string in any rendered text.

### U5 · Portfolio text, real-data proof · 0.75 d · slice review
Files: `frontend/src/estate/estateClient.ts:473-488`, `frontend/src/estate/PortfolioOutcomes.tsx:163-170`,
`frontend/src/estate/__tests__/estatePortfolio.test.tsx`, `portfolioFixtures.ts`, new
`backend/tests/test_out_d5_objectives_postgres.py`.
- Type: `EstateOutcomeSummaryBody.objective_site_count: number | null`.
- Assure detail: n = `summary?.objective_site_count`; n ≥ 1 → "No verified result yet · targets declared at {n}
  {site|sites} · {gap}"; n === 0 → today's text; summary null or n null → "No verified result yet · {gap}" (never
  claim "no targets" unread). Vitest: 3, 1, 0, null and summary-not-loaded.
- The board contributor needs no component change (it is a contributor with a chip). Vitest renders a row fixture
  with one objective contributor and runs `scanProductVocabulary(root, page, {set: "w1"})`.
- Postgres test (pattern `test_out_b4_board_postgres.py`): Kobo `estate` build (`_build_kobo(url, work, "estate")`,
  board day 2026-10-21), w502 `positive` and w504 (`EV_BUILD`), each then `declare_objective.main(["fixture",
  "--file", ...], store=...)`. Assert per Site: board `objectives` keys (Kobo MG-2, MG-1, MG-5; GreenHarvest CC-1,
  CC-6; Depot EV-1, EV-2), each declared outcome's contributor present with a verdict chip, no "No objective
  declared" on an outcome that has an objective, the Portfolio summary `objective_site_count == 3`. **Record**, then
  assert only what the data proves: each verdict and row state. Expected (record if different, do not force):
  Kobo Cost Needs attention (MG-2 Missed), Grow Opportunity (MG-1 Not checked yet), GreenHarvest Protect Needs
  attention (CC-1, CC-6 Missed), Depot Protect Needs attention (EV-1 Missed). Reproducibility on real data: board at
  `known_at = K1`, then declare KOBO MG-2 v2 (target 30), board at K1 → same MG-2 state and text; board now →
  the v2 text.

### U6 · Captures, register, full suite · 0.5 d · slice review
- Captures 1440 and 390 vs v70: Kobo Overview (Cost, Grow, Protect, Assure rows open), GreenHarvest Overview,
  Depot Overview, Portfolio (Assure card text, matrix). Record pairs in `.agent/OUT-D-packet.md`.
- Register rows §6. Full suite (schema change).

## 4. Copy (exact; scanned, 0 hits)

Label "Declared objective". Chips "Met" · "Missed" · "Not checked yet".
Targets: MG-2 zero "Supply cost per kWh: no generator time longer than needed", any "Supply cost per kWh: at most
{t} min a day with the generator on longer than needed" · MG-1 "Productive electricity sales: at least {t} kWh sold
for productive use a month" · MG-5 zero "Reliable service: all critical demand served", any "Reliable service: at
most {t} kWh of critical demand not served" · CC-1 "Stock kept saleable: chamber held between {low} and {high}°C" ·
CC-6 "Cooling continuity: every backup start succeeds by itself" (zero only; a non-zero target is refused, 422) ·
EV-1 zero "Buses ready for service: no interrupted charging sessions", any "Buses ready for service: at most {t}
interrupted charging sessions" · EV-2 "Energy cost per km: at most {t} {currency} per km".
Actuals: as the U4 table. Assure: "{met} of {n} declared objectives met" · " · {u} not checked yet".
Portfolio: "targets declared at {n} {site|sites}".

## 5. Validation tier

| Unit | Focused backend | Frontend |
|---|---|---|
| U1 | `test_out_d1_schema_postgres.py` + the 20 head-literal files | — |
| U2 | `test_out_d2_objectives.py test_out_b1_status.py test_out_a1_outcome_map.py` | — |
| U3 | `test_out_d3_declare.py test_out_d3_objective_store_postgres.py` | — |
| U4 | `test_out_d4_board.py` + the OUT-C U2 set (`test_out_c2_board.py test_out_b1_board.py test_out_b2_mini.py test_out_b2_vocabulary.py test_out_b3_cold_ev.py test_out_b4_read.py test_out_b4_imports.py test_out_b4_route.py test_out_b4_window.py`) + `test_out_w2_summary_window.py` | — |
| U5 | `test_out_d5_objectives_postgres.py` | `npx vitest related --run <changed>`, `npx tsc --noEmit` |

`tools/check-all.ps1` at every unit commit. Slice end: **one full backend run** (`tools\run-backend-suite-in-container.ps1
-Tier all`, idle machine) and one full `npx vitest run`.

## 6. Register rows (R580-R586; new range, the sprint reserve R575-R579 is used up by C and W)

- **R580** · D U4 · mini, cold, ev · D2 · standing. Mock: no objective line in the board rows. Shown: a
  "Declared objective" contributor with a Met / Missed / Not checked yet chip. Reason: rev 6 §4.3 requires the
  objective to be labelled on screen.
- **R581** · D U4 · mini · D3 copy honesty · standing. Supply cost per kWh is judged on avoidable generator minutes,
  a leading measure; no supply cost per kWh value is recorded.
- **R582** · D U4 · mini · D1 · standing. Productive electricity sales: no sales record; the objective shows
  "Not checked yet" and Grow keeps Opportunity.
- **R583** · D U4 · ev · D2 · standing. Energy cost per km stays "Not measured yet" with its existing sentence; the
  declared objective is counted on the Portfolio but has no board line.
- **R584** · D U4 · cold · D2 · standing. Stock kept saleable reads the existing chamber range; it is not a stored
  objective revision.
- **R585** · D U2 · all · D4 reading · standing. On track appears only where a measure meets its objective on a
  complete window; the demo data may show none (record which in the packet).
- **R586** · D U5 · portfolio · D2 · standing. Mock "no targets declared"; shown "targets declared at {n} sites".
- Notes: **R543** (NO_OBJECTIVE gray) unchanged; **R542** (Kobo cost after ACT-048 reads Watch) now reads Needs
  attention when MG-2 is Missed on the board day: add the note.

## 7. Pre-flight checklist (answer in one batch before code, then stop)

- [ ] Worktree on main after OUT-W; `git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'` empty; `.venv` junction;
  PYTHONPATH and `assetops_backend.__file__` as OUT-W §7.
- [ ] A new top-level package `objectives/`: run `tools/check-all.ps1` on an empty skeleton first. If
  `module-roots.ps1` or `dependency-direction.ps1` refuses it, stop and ask (fallback: `site_outcomes/objectives/`).
- [ ] `alembic heads` shows exactly `0038_out_objectives` after U1; the CC-M branch is untouched.
- [ ] Re-grep the head literal; never change a downgrade target or a `down_revision == PARENT` assertion.
- [ ] Kobo `estate` board day 2026-10-21 dispatch body: record `avoidable`/`unclear` before U5 (decides MG-2's
  verdict); record depth `service.cards.unserved_kwh` (likely None → Not checked yet).
- [ ] `outcome_state` defaults: run `test_out_b1_status.py` unchanged after U2 except the policy string.
- [ ] Vocabulary: `ran running run runs runtime load draft claim candidate necessary binding scenario simulated stage
  fixture cursor projection replay`, case-sensitive `SOC PV PCS`, uppercase codes, `UPPER_UNDERSCORE` are forbidden on
  screen. "load" rules out "critical load": the copy says "critical demand".
- [ ] No `<svg>`, no `variant` prop, no new CSS.
- [ ] DB names `assetops_out_d_<x>_test`; dropped by the fixture.
- [ ] `grep -c "| R58[0-6] " .agent/mock-departure-register.md` is 0.

**Known failures:** as OUT-W §7.

## 8. Acceptance

1. Migration 0038 round-trips; every CHECK, the chain and the trigger refuse by name; the writer guard registers the
   store and fails with it removed (anti-vacuity counter).
2. The demo file declares 6 objectives idempotently; CC-1 reads the chamber range.
3. Status `/2`: MISSED → Needs attention, MET → On track (an AT_MOST objective needs a complete window; an AT_LEAST
   objective already met is MET early, since the measure only grows), NOT_JUDGED → Unknown after Opportunity; no
   objective → No objective declared as before. (Ruling L3, 2026-10-31.)
4. Each board row with an objective shows "Declared objective" with its chip; the mini Assure line counts met
   objectives; the Portfolio Assure card says "targets declared at 3 sites".
5. An earlier status reading (same `known_at`) survives an objective change; the current reading shows the change.
6. Full backend, full vitest and `check-all` pass, except the known failures.

## 9. Review points

- **U1:** migration matches §3 exactly; no merged migration edited; head literals only where they mean head; guard
  change confined to the new writer.
- **U2:** purity; MISSED needs no complete window for AT_MOST, MET does; 7b after 6; defaults keep B/C goldens.
- **U3:** unit, kind, comparison and window rule never from the caller; the cutoff read; idempotency and prior check
  in one locked transaction; demo note says "not a customer target".
- **U4:** no reading parses prose; CC-1 never stored; a failed objectives read is PARTIAL and never "No objective";
  no code on screen.
- **U5/U6:** the Portfolio never says "no targets" unread; verdicts recorded from data, not forced; register complete.
