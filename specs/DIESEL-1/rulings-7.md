## 9j. Ruling DIESEL-1-R3j: the K4 consolidated card (the unexplained-fuel Finding, migration 0056), split K4a / K4b

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `801efc0e2` (K3 merged `ce03ae246`, review `.agent/review-K3.md` ACCEPT; PV-1 `4d7f400c8`, MB-1a/b, CH-5d1, A1, A2, K1, K2 merged; K0 in its fix round; A3 not merged).
- Owner decisions in force, verbatim: `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-fuel-scope-2026-11-07.md` (no combined total; money only from evidence: "Portfolio line per proven result with no combined total"); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions"); `.agent/owner-kisiwa-scope-2026-11-07.md` ("Build it, with the action link (Recommended)"); `.agent/owner-diesel-night-window-2026-11-07.md` (a night runs "6 pm to noon").
- **This card replaces** the K4 rows of §8.4 and §9.5 and §8.4's "Finding literals (K4)". It binds H1–H5 (§8.2). Builders read only their part below (K4a: §9j.1–§9j.9; K4b: §9j.1, §9j.10–§9j.14). Paths use the header's short forms; `T/` = `tools/`.
- READ = the Architect read the code at `801efc0e2`; nothing here was measured.

### 9j.1 Code reality and the decisions it forces (READ)

1. **A Finding is a row in the shared `finding`/`finding_revision` tables, and every Finding there cites an assessment.** `finding.anchor_assessment_revision_id`, `finding_revision.assessment_revision_id` and `analytic_run_id` are NOT NULL FKs (`backend/migrations/versions/0009_finding_store.py:33-106`). Cold and EV Findings meet this with their own `analytic_run` + `assessment_revision` written by the assessment store, then domain-specific inserts in the Finding store (`B/analytics/adapters/postgres_finding_store.py:588-711` `cold_apply`, `:713-828` `ev_apply`). The guard makes the assessment store the only writer of `analytic_run`/`assessment_revision` and the Finding store the only writer of the Finding tables (`T/checks/configuration-persistence.ps1:699-720`, `:1219-1224`).
   - **Decision: K4 follows the cold/EV pattern exactly.** A new Finding storage domain `fuel_balance`; one `analytic_run` + `assessment_revision` (analytic `fuel-balance-1`) per window revision a Finding cites; the Finding and its revisions inserted by a new `fuel_apply` in the Finding store. No NOT NULL is relaxed and no reader loses a join.
2. **The fuel-cost outbox does not fire for a new domain.** `financial_consequence_dirty_on_finding_revision` runs only `WHEN (NEW.domain = 'mini_grid')` (`0022_w2_cold_assessment.py:214-219`). The cold trigger runs only for `cold_chain` (`0023`). So a `fuel_balance` revision enqueues no fuel-cost work: **the Finding can never acquire fuel-cost-1/2 money.**
3. **`financial_consequence_revision` cannot hold this money.** Its CHECKs pin `quantity_low = 0` and `amount_low = 0` (`0011_financial_consequences.py:92-108`); the residual band's low edge is positive. Cold and EV each have their own consequence tables. **Decision:** a new append-only table `fuel_residual_consequence_revision`, written by the consequence store (the guard's sole consequence writer). Own model, own basis, own table: nothing that sums `financial_consequence_revision` can see it.
4. **Threads need one row.** `chain/threads.py:30-32` `SUBJECT_COLUMN`: "A further domain needs one row here, nothing else." Without it `finding_source` raises `KeyError` on the tick's threads step. K4a adds `"fuel_balance": "subject_asset_id"`. Thread key = `(tenant, site, UNEXPLAINED_FUEL, ASSET, tank id)`: every unexplained night of one tank is an occurrence on one thread, and the existing registry gives occurrence numbers and RECURRED (`RECURS_FROM`, `:34`).
5. **The board's Finding read is dispatch-only.** `_FINDING_HEADS` filters `f.domain = :domain AND f.analytic_id = :analytic` (`B/chain/adapters/postgres_chain_read.py:27-45`); the board's `lead_finding`/`money_head` path reads `financial_consequence_revision`. K4b adds a **second, separate** head read for `fuel_balance`, and keeps every dispatch-only path (COST lead, money head, Trial option) on dispatch heads only.
6. **Row placement is declared only in the outcome map.** `board._row` places issues, thread lines, in-hand and earlier items from `outcome_roles` (`B/outcomes/outcome_map.py:17-36`; `board.py:875-1029`). The mini Protect row has only `MG-5` "Reliable service" and `MG-4` "Battery and generator life" (`B/outcomes/catalogue.py:48-49`). Mapping unexplained fuel to either would state a false outcome. **Decision:** a new catalogue outcome **`MG-8` "Fuel accounted for"** (MINI, PROTECT_ASSET), moved by `FINDING:UNEXPLAINED_FUEL`; NOT_APPLICABLE on a Site with no stored fuel-balance window (Kobo), so Kobo's Protect row state cannot change.
7. **§8.4 misplaced one reference.** `NO_FUEL_BALANCE` (`B/site_outcomes/mini.py:81`, `:937`) is the **Optimize** row's "Fuel" contributor (from Kobo's hourly fuel depth), not Protect. It stays byte-equal on every Site. Kisiwa's Protect row gains a new "Fuel in the tank" contributor instead (K4b).
8. **The Portfolio line goes on the Protect card, not Assure.** H2 says the Assure card gains no line for this story, and PV-1's Assure `value_lines` are verified results only (`B/site_outcomes/read.py:820-836`). The unexplained-fuel money is a Finding's, so it is listed on the **Protect** card, PV-1's pattern (one line each, own basis, never summed). **K4b owns it** (moved from K8, §9j.14).
9. **Only two product strings say "theft"**: `F/sites/MiniPerformance.tsx:1311` (`FUEL_NOTICE`) and `:1343` (the RESIDUAL row); the only other hits are tests and `.agent/` logs (`git grep -i theft`). K4a rewords both (moved from K5; K5 must not touch those two lines).
10. **Why split.** K4 as one unit is about 2.4 with the placement work in items 5–6. K6 needs only the Finding, its thread and its money (K4a). The board, outcome and Portfolio placement (K4b) can run on lane 1 beside K6. The split shortens the critical path by about 1.0 (§9j.15).

### 9j.2 K4a: what it delivers (lane 3, critical path)

- Migration 0056 (§9j.3); `fuel_apply` and the window assessment persist (§9j.4); the consequence store's `fuel_residual_append` (§9j.5); the service and CLI that raise Findings from stored K3 windows (§9j.6); the pure client-text module (§9j.7); the threads mapping; the two "theft" strings reworded; K3's single-head test made head-agnostic; K3 review L1 and L2 closed; finish row KIS-4.
- **No board, outcome, Portfolio or route change** (K4b and K5). **No served page renders the Finding's lines yet** (K5's panel). **No tick stage:** like K3, the raise is explicit (K7's prepare calls it after `assess`, then runs the existing threads step).

### 9j.3 Migration `backend/migrations/versions/0056_unexplained_fuel_finding.py`

`revision = "0056_unexplained_fuel_finding"`, `down_revision = "0055_fuel_balance_window"`. Renumber rule (§8.4) stands: if another migration lands first, K4a takes the next number and K6 follows.

1. **Finding domain arm.** Recreate `finding_domain_subject` and `finding_revision_domain_minutes` exactly as `0025_w2_ev_session.py:52-63` (`DOMAIN_SUBJECT_0025`, `DOMAIN_MINUTES_0025`, copied as constants named `..._0025`, used by the downgrade) **plus one arm each**:
   - subject: `OR (domain = 'fuel_balance' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL)`;
   - minutes: `OR (domain = 'fuel_balance' AND candidate_minutes IS NULL AND necessary_minutes IS NULL AND indeterminate_minutes IS NULL)`.
   - Use 0025's `_domain_checks` statement shape (DROP then ADD in one `ALTER TABLE` per table).
2. **The consequence table:**
```sql
CREATE TABLE fuel_residual_consequence_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_id uuid NOT NULL,
    finding_revision_id uuid NOT NULL,
    fuel_balance_window_id uuid NOT NULL,
    model_id text NOT NULL CHECK (model_id = 'fuel-residual-1'),
    basis text NOT NULL CHECK (basis = 'UNEXPLAINED_FUEL_AT_DECLARED_PRICE'),
    litres_low text NOT NULL CHECK (litres_low ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    litres_high text NOT NULL CHECK (litres_high ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    state text NOT NULL CHECK (state IN ('PRICED','UNPRICED')),
    price_reason text NULL,
    price_revision_id uuid NULL,
    price_assignment_id uuid NULL,
    price_value numeric NULL,
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    amount_low text NULL CHECK (amount_low IS NULL OR amount_low ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    amount_high text NULL CHECK (amount_high IS NULL OR amount_high ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    price_known_at timestamptz NOT NULL,
    basis_sha256 text NOT NULL CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),
    recorded_at timestamptz NOT NULL,
    CONSTRAINT fuel_residual_priced CHECK ((state = 'PRICED') = (price_revision_id IS NOT NULL)
        AND (state = 'PRICED') = (price_value IS NOT NULL AND price_value >= 0 AND price_value < 'Infinity'::numeric)
        AND (state = 'PRICED') = (currency IS NOT NULL AND amount_low IS NOT NULL AND amount_high IS NOT NULL)
        AND (state = 'PRICED') = (price_reason IS NULL)),
    CONSTRAINT fuel_residual_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_price_fk FOREIGN KEY (tenant_id, site_id, price_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_window_fk FOREIGN KEY (fuel_balance_window_id) REFERENCES fuel_balance_window(id),
    CONSTRAINT fuel_residual_once UNIQUE (finding_revision_id),
    CONSTRAINT fuel_residual_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX fuel_residual_finding ON fuel_residual_consequence_revision (tenant_id, site_id, finding_id, recorded_at);
CREATE TRIGGER fuel_residual_consequence_revision_immutable BEFORE UPDATE OR DELETE
    ON fuel_residual_consequence_revision FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
   - One consequence row per SUPPORTED Finding revision (`UNIQUE (finding_revision_id)`); none for a NO_LONGER_SUPPORTED revision.
   - The table is **not** a chain-event producer (`0044` `PRODUCERS` unchanged) and has no outbox.
3. **Downgrade:** `LOCK TABLE finding, finding_revision, fuel_residual_consequence_revision IN ACCESS EXCLUSIVE MODE`; refuse with `RuntimeError("0056 downgrade requires no fuel_balance Findings or fuel residual consequences")` if any `finding`/`finding_revision` row has `domain = 'fuel_balance'` or the table has a row; else drop the trigger, index and table and restore the two 0025 CHECKs.
4. No other object changes. The fuel-cost and cold triggers, `fuel_balance_window` and 0044 are untouched.

### 9j.4 Storage: window assessment, Finding, lifecycle (READ-based; copy the cold shapes)

**`PostgresAssessmentStore.fuel_balance_persist(c, window: FuelBalanceWindow, now) -> dict`** (`B/analytics/adapters/postgres_assessment_store.py`, on the caller's connection):
- `analytic_run`: `analytic_id 'fuel-balance-1'`, `model_version 'fuel-balance-1/v1'`, `window_start/end` = the window's, `knowledge_cutoff` = `window.recorded_at`, `input_sha256` = `window.input_sha256`, `cohort_status 'COMPLETE'`, `cohort_sha256` = sha256 of `[]` canonical, `cohort '[]'`, `configuration_sha256` = `window.input_sha256`, `foundation_revision_ids` = sorted distinct `[accuracy_revision_id, sfc_revision_id, no_load_revision_id]` from `window.terms`, `binding_set_revision_ids '[]'`, `role_coverage '{}'`, `watermarks '{}'`, `selection 'EXPLICIT'`, `job_id NULL`, `status 'COMPLETED'`, `started_at = completed_at = now`.
- `analytic_run_evidence`: one row per `window.evidence_ids`.
- `assessment_revision`: `assessment_key` = `f"{tank_asset_id}:{night_date}"`, `revision_no` = `window.revision`, `claim_level 'COMPLETE'`, `result` = `{"fuel_balance_window_id", "revision", "state", "residual_low", "residual_high", "gap_minutes", "limitations"}` (exact text), `evidence_ids` = the window's, `basis_sha256` = `window.input_sha256`; plus the `analytic_run_assessment` row (`scope 'WINDOW'`).
- **Idempotent:** if an `assessment_revision` with that `(site_id, 'fuel-balance-1', assessment_key, revision_no)` exists, return it unchanged (`analytic_run_basis_unique` already makes the run unique).
- Returns `{"revision_id", "run_id", "basis": window.input_sha256}` (cold's `persisted` shape).

**`PostgresFindingStore.fuel_apply(c, tenant_id, site_id, window, persisted, consequence_writer, now) -> list[UUID]`** (Finding store, beside `cold_apply`; module docstring line added "fuel_balance (DIESEL-K4a)"). Constants beside `COLD_MATCHER_VERSION`:
```python
FUEL_DOMAIN, FUEL_MECHANISM, FUEL_ANALYTIC = "fuel_balance", "UNEXPLAINED_FUEL", "fuel-balance-1"
FUEL_MATCHER_VERSION = "fuel-finding/1"      # finding_type = "UNEXPLAINED_FUEL@fuel-finding/1"
FUEL_MODEL_VERSION = "fuel-balance-1/v1"
```
- `finding_key` = `f"fuel:{tank_asset_id}:{night_date.isoformat()}"` (one Finding per tank night, ever).
- **Lifecycle (the only transitions; first match wins):**

| Held Finding for the key | Latest window revision `W` (as passed) | Write |
|---|---|---|
| none | `W.state == "UNEXPLAINED"` | insert `finding`; revision `OPENED` / `SUPPORTED`; consequence |
| none | anything else | nothing |
| held, its latest revision's `claim.fuel_balance_window_id == W.id` | any | nothing (idempotent) |
| held | `UNEXPLAINED` (a newer window revision) | revision `SUPPORT_CHANGED` / `SUPPORTED`; consequence |
| held | not `UNEXPLAINED` | revision `NO_LONGER_SUPPORTED` / `NO_LONGER_SUPPORTED`; no consequence |

- `finding` row: `domain 'fuel_balance'`, `mechanism 'UNEXPLAINED_FUEL'`, `analytic_id 'fuel-balance-1'`, `generator_asset_id NULL`, `subject_asset_id` = tank, `anchor_start` = `window_start`, `anchor_assessment_revision_id` = persisted, `cohort_sha256 NULL`, `matcher_version` = `FUEL_MATCHER_VERSION`, `recurs_after_finding_id NULL`, `split_from_finding_id NULL`, `opened_at = created_at = now`.
- `finding_revision` row: `domain 'fuel_balance'`, `revision_no` = max + 1, `claim_level 'COMPLETE'`, `title` = `finding_text.TITLE` (§9j.7), mechanism, matcher, analytic, `model_version` = `FUEL_MODEL_VERSION`, `assessment_revision_id`/`analytic_run_id` = persisted, `window_assessment_revision_id NULL`, `episode_start/end` = the window, the three minute fields NULL, `basis_sha256` = `input_sha256` = `W.input_sha256`, `support_sha256` = `sha256_json(sorted evidence ids)`, `cited_evidence_sha256` = cold's envelope-digest rule (`:685-687`), `created_at = now`.
  - `claim` (jsonb): `{"fuel_balance_window_id", "window_revision", "night_date", "tank_asset_id", "state", "residual_low", "residual_high", "gap_minutes", "gap_spans": [[from, to], ...] (UTC ISO), "limitations": [...codes], "parameter_version", "accuracy_l"}` (exact text from the window).
  - `limitations` (jsonb, sentences, fixed order): `finding_text.NOT_WHY`, `finding_text.margin_line(accuracy_l)`, then `finding_text.gap_line(spans, tz)` when `gap_minutes > 0`.
  - Links: `finding_revision_assessment` (primary, `'WINDOW'`) and `finding_revision_evidence` for each window evidence id, exactly as `cold_apply`.
- A SUPPORTED revision calls `consequence_writer(c, finding_id, revision_id, W, now)` in the same transaction (§9j.5).
- Re-running with the same window writes nothing (`finding_revision_basis_unique` and the "cites `W.id`" rule).

**Threads and maps (one row each; existing values byte-equal):**
- `B/chain/threads.py:31` `SUBJECT_COLUMN` gains `"fuel_balance": "subject_asset_id"`.
- `B/chain/read.py:25` `SITE_TYPE_OF_DOMAIN` gains `"fuel_balance": "MINIGRID"`.
- PRE-FLIGHT (c) lists every other dict, tuple or SQL `IN` list keyed by a Finding storage domain (`git grep -n "cold_chain" backend/assetops_backend`); each gets the `fuel_balance` entry its reader needs, or the builder states why none. A reader that raises on an unknown domain is a stop (S3).

### 9j.5 The money: `fuel-residual-1` (own basis, never added)

**`PostgresConsequenceStore.fuel_residual_append(c, tenant_id, site_id, finding_id, finding_revision_id, window, price, now)`** (`B/financials/adapters/postgres_consequence_store.py`, the sole consequence writer; guard list gains the table).
- **Litres** = `window.residual_low`, `window.residual_high` (exact `Fraction`, stored with `verification_rules.fmt`). Never rounded in storage.
- **Price** = `price_selection(tenant_id, site_id, window_start, window_end, known_at=window_end)` from `B/financials/composition.py:142-155` `build_trial_comparison_ports(url).price_selection` (the one diesel price over the whole window, `fuel_cost.select_window_price`, as known at the window end; §8.4). K4a calls the existing builder; it adds no price reader.
- **PRICED:** `amount_low = residual_low × price_value`, `amount_high = residual_high × price_value`, exact (`Fraction(residual) × Fraction(str(price_value))`), stored with `fmt`; `price_revision_id`, `price_assignment_id`, `price_value`, `currency` from the selection; `price_reason NULL`.
- **UNPRICED:** `price_reason` = the selection's reason (`NO_PRICE`, `PRICE_CONFLICT`, `PRICE_SPANS_WINDOW`, `PRICE_REVISION_MISSING`, `PRICE_UNIT_MISMATCH`, `PRICE_INVALID`); every price and amount field NULL.
- `price_known_at` = `window_end`; `basis_sha256` = `sha256_canonical({"model": "fuel-residual-1", "window_id", "residual": [lo, hi], "price": [revision_id, value, currency] or [reason]})`; `recorded_at = now`.
- **Never:** a row in `financial_consequence_revision`; a call to `fuel_cost`/`fuel_cost_v2` quantity code; an addition with any other money anywhere (stored, served or displayed). A price republished later does not re-price a stored row in v1 (after-the-demo list: "re-price unexplained-fuel consequences on a price correction").

**Read (`B/fuel_balance/model.py` additions, implemented by `PostgresFuelBalanceStore`, read-only, `REPEATABLE READ READ ONLY`):**
```python
@dataclass(frozen=True)
class FuelFinding:
    finding_id: UUID
    revision_id: UUID
    revision_no: int
    lifecycle: str                      # SUPPORTED | NO_LONGER_SUPPORTED
    night_date: date
    window: FuelBalanceWindow           # the revision the Finding revision cites
    consequence: Mapping[str, Any] | None   # the row's columns (exact text), None when NO_LONGER_SUPPORTED
    created_at: datetime

class FuelFindingReadPort(Protocol):
    def fuel_findings(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                      known_at: datetime | None) -> tuple[FuelFinding, ...]: ...   # latest revision per Finding at known_at, window intersecting [lo, hi), by night_date
    def fuel_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
                     known_at: datetime | None) -> FuelFinding | None: ...
```
- `known_at None` = now. `lo < hi`, UTC-aware, else `ValueError("fuel findings need lo < hi and UTC instants")`.

### 9j.6 Service and CLI (explicit, never by itself)

- **`B/fuel_balance/findings_service.py`**, `FuelFindingService(store_factory).raise_night(tenant_id, site_id, night_date) -> RaiseResult(status, finding_id|None, revision_id|None)`, status ∈ `OPENED`, `REVISED`, `WITHDRAWN`, `UNCHANGED`, `NO_FINDING`, `NO_WINDOW`:
  1. One transaction; `pg_advisory_xact_lock(hashtext('fuel-finding:' || site_id || ':' || night_date))`.
  2. The latest window revision for the night, as known now (`windows(...)` with `known_at` = the transaction's `clock_timestamp()` or the composition's test-only clock override). None → `NO_WINDOW`.
  3. If a Finding must be written (§9j.4 table): `fuel_balance_persist`, then `fuel_apply` (which calls `fuel_residual_append`), on the same connection.
  - The transaction owner mirrors the cold worker (`B/analytics/assessment_worker.py`, the guard's `$coldTransactionOwner`): PRE-FLIGHT (a) names its engine/connection pattern with file:line; K4a copies it in `findings_service.py` and joins the guard's owner list (membership only).
- **Composition** `B/fuel_balance/composition.py` gains `build_fuel_finding_service(database_url, *, test_db_clock_override=None)`, wiring the three stores and the price selection. Test-only clock: constructor-only, as K3.
- **CLI** in `B/fuel_balance/worker.py`: `python -m assetops_backend.fuel_balance.worker raise --site <code> --from <local date> --to <local date>`; one JSON line per night `{"site_code", "night_date", "status", "finding_id", "revision_id"}`; any refusal exits 2 after printing it. `assess` is unchanged.
- **K7's prepare order (for K7's card):** per story day: accept → `assess` the closed nights → `raise` the same nights → the existing threads step (`B/chain/backfill.py:33` `run_threads`, as the Kobo prepare does). The board reads PARTIAL until the threads consumer has consumed the `finding.revised` event (`postgres_chain_read.py:48-54`, R8); that is correct behaviour.

### 9j.7 Client wording (K4a literals; `B/fuel_balance/finding_text.py`, pure, no I/O)

Rules: H1–H5 (§8.2). **H4: none of theft, stolen, stole, siphon, pilfer, and nothing implying them.** The word "running" is avoided (guard V/N's "run" rule; `mini.py:71` precedent). Numbers are formatted here, never in the browser. Litres: one decimal, half-even on the exact `Fraction` (`Decimal(round(F * 10)) / 10`, `:.1f`). Money: `chain.vocabulary.money2` on the exact amount. Price `{p}`: `money2(price_value)`. `{date}`: `f"{d.day} {d:%b}"` of `night_date` (the board's `_short_day` form, e.g. "4 Oct"). Times `{a}`, `{b}`: Site-local `HH:MM` (24 h).

```python
TITLE = "Unexplained fuel overnight"
CLAIM_LINE = ("About {lo}–{hi} L left the tank on the night of {date} (6 pm to noon) that the generator's "
              "modelled use and the recorded deliveries don't explain.")
GAP_LINE = "The tank sensor sent no readings {spans}."          # SPAN joined with ", and "
SPAN = "from {a} to {b}"
MONEY_LINE = ("Worth about {lo_m}–{hi_m} {cur} at your declared {p} {cur} per litre "
              "(a modelled range that includes the stated margin)")
UNPRICED_NO_PRICE = "Not available yet · no diesel price declared for this night"
UNPRICED_PRICE_CHANGES = "Not available yet · the declared diesel price changes during this night"   # PRICE_CONFLICT, PRICE_SPANS_WINDOW
UNPRICED_OTHER = "Not available yet · the declared diesel price could not be used for this night"   # any other reason
NOT_WHY = "This does not say why the fuel left the tank."
MARGIN_LINE = ("The range allows for the tank sensor's declared accuracy of {a} L at each reading, 10 % either way "
               "on the generator's modelled use, and 1 % on each recorded delivery.")
NO_LONGER = "A later check of this night no longer finds unexplained fuel."
```
- `finding_lines(ff: FuelFinding, tz) -> {"title", "claim", "gap" | None, "money", "not_why", "margin", "no_longer" | None}`: SUPPORTED → `claim`, `gap` (only if `gap_minutes > 0`), `money` (MONEY_LINE or the UNPRICED literal), `not_why`, `margin`; NO_LONGER_SUPPORTED → `title`, `no_longer`, `not_why` only.
- **Expected values on Kisiwa night 4 (computed from F0's committed exact bands and price v1 1.25 USD; K4a asserts them, never forces them):** "About 95.7–144.3 L left the tank on the night of 4 Oct (6 pm to noon) …"; "The tank sensor sent no readings from 00:45 to 02:30."; "Worth about 119.57–180.43 USD at your declared 1.25 USD per litre (a modelled range that includes the stated margin)". If the stored band differs from F0's, that is K3's parity (already proven), not a K4a choice: K4a's test reads the stored window, so a mismatch with these strings is stop S1.
- **The two "theft" strings (`F/sites/MiniPerformance.tsx`), MD-FUEL-K-2, on every Site:**
  - `FUEL_NOTICE` (`:1310-1311`) becomes: "Unexplained fuel is fuel that left the tank and that the generator's modelled use and the recorded deliveries don't account for, within a stated margin. It does not say why the fuel left, and it is never added to the generator's possible extra fuel."
  - The RESIDUAL row (`:1343`) becomes: "Needs every term with a supported range; never says why fuel left".
  - Header comment at each: `// MOCK DEVIATION MD-FUEL-K-2 (DIESEL-1-R3j): v69 :627-628 say "never infer theft" / "cannot establish theft"; owner 2026-11-07: "'Unexplained fuel', never 'theft'".`
  - These are the only Kobo Fuel-page bytes that change. `F/sites/__tests__/miniFuelRoutes.test.tsx:188`, `:191` take the new literals (import the constant for `:191`; retype `:188`'s row literal).

### 9j.8 K4a tests (localised; no full suite). Every "must fail" names the mutation the reviewer applies to a scratch copy.

**A. L0 `backend/tests/test_k4a_fuel_finding_rules.py` (no DB)**
1. **Text, night 4.** `finding_lines` on a FuelFinding built from `probe-result.json` night 4 `readings` band (exact), `accuracy_l = 10`, price 1.25 USD, `Africa/Dar_es_Salaam`: the three expected strings of §9j.7 exactly. Must fail if litres round half-up at a `.x5` case (add a synthetic band `[1.25, 2.35]` → "1.2–2.4"), or if `money2` is replaced by `round(x, 2)` on a float.
2. **Gap.** No gap → `gap is None`; two spans → "from 00:45 to 02:30, and from 03:00 to 04:10"; times in Site time, not UTC (must fail if UTC).
3. **Unpriced.** Each reason maps to its literal; `money` never contains a digit when UNPRICED.
4. **Wording guard (local).** Every K4a literal and both new `MiniPerformance` strings, lower-cased, contain none of `theft`, `stolen`, `stole`, `siphon`, `pilfer`; and `F/sites/MiniPerformance.tsx` (read as text) contains none of them. Must fail if either old string is restored.
5. **Amounts exact.** For the night-4 band and 1.25: `amount_low == residual_low × 5/4` exactly, stored text round-trips through `fmt`/`parse`; must fail if amounts are computed from the 0.1-L display litres (95.7 × 1.25 = 119.625 → "119.62", not "119.57").
6. **Never summed (static).** No module under `B/fuel_balance/` and no `fuel_residual_*` function imports `fuel_cost_v2`, `financial_consequence`, or calls `sum(`/`+` over two consequence amounts (AST check over the new files: no `BinOp(Add)` whose operands both name an `amount_*`).
7. **Lifecycle table** (§9j.4) on a fake store: all five rows; the idempotent re-run writes nothing.
8. **K3 L1 (follow-up):** in `backend/tests/test_tfc2.py` `test_window_idle_seconds_exclude_the_stop_slot`, one more case: RUNNING at 0–11, **FAILED** at the window end → 3300. Must fail with `NOT_RUNNING_STATES = {"STOPPED"}`.

**B. L2 `backend/tests/test_k4a_fuel_finding_postgres.py`, own `assetops_k4_test`** (Kobo imported as K3's B does; synthetic windows through `PostgresFuelBalanceStore.append` with the test clock):
1. **0056** up/down/up on empty tables: the two recreated CHECKs' text (pg_get_constraintdef) equals 0025's plus the one arm; the consequence table's columns, constraints, index and trigger; downgrade refused with a `fuel_balance` Finding row and with a consequence row; single alembic head **head-agnostic** (below); UPDATE/DELETE refused; raw inserts violating `fuel_residual_priced` (priced without amount; unpriced with a price) fail; a `fuel_balance` Finding with a `generator_asset_id` fails the subject CHECK.
2. **Kobo's existing Findings byte-equal:** `domain = 'mini_grid'` rows and the fuel-cost trigger unchanged; inserting a `fuel_balance` revision adds **no** `financial_consequence_work` row (must fail if the trigger's `WHEN` is dropped).
3. **Raise lifecycle on a stored window** (tank = Kobo's tank, accuracy declared by the test): UNEXPLAINED → OPENED + one PRICED consequence; same again → UNCHANGED; a newer WITHIN_MARGIN revision → WITHDRAWN (`NO_LONGER_SUPPORTED`, no consequence); a later UNEXPLAINED revision of a second night → a second Finding on the **same** thread after `run_threads` (occurrence 2). No price declared → UNPRICED `NO_PRICE`.
4. **Threads:** after `raise` and `run_threads`, one `finding_thread` with mechanism `UNEXPLAINED_FUEL`, `subject_kind 'ASSET'`, `subject_ref` = tank id, `finding_type 'UNEXPLAINED_FUEL@fuel-finding/1'`; the R8 unsettled read is False after the consumer ran and True before.
5. **Reads:** `fuel_findings`/`fuel_finding` as known before and after the WITHDRAWN revision.
6. **Head-agnostic edit (K3 residual risk):** `backend/tests/test_k3_fuel_balance_postgres.py:183-187` `test_b1_single_alembic_head` asserts `script.get_heads() == [alembic_head()]`, `head(engine) == alembic_head()`, and `script.get_revision(MIGRATION).down_revision == PREVIOUS`; it no longer names 0055 as head. K4a's own head test is written the same way. The packet lists these lines as a head-bookkeeping edit (the §9g.5 precedent), not a behaviour change.

**C. L2 parity `host/tests/test_k4a_kisiwa_night4.py`, own `assetops_k4_test`** (machine idle, free RAM checked first; about 6–8 min): K3 part C's module fixture and steps for **night 4 only** (§9d.6 C, reusing its helpers by import), then `assess` and `raise` night 4 at `run_end + 30 min` through `build_fuel_finding_service`, then `run_threads`:
- one Finding, SUPPORTED; its claim's band equals the stored window's exactly and equals F0's night-4 `readings` band within K3's 1/100000 L;
- consequence PRICED, price revision = Kisiwa diesel v1, `amount_* = residual_* × 1.25` exactly;
- `finding_lines` gives the §9j.7 expected strings;
- **KIS-4 pure check** (below) passes on this DB;
- no `financial_consequence_revision` row cites this Finding.

**Must stay green unchanged:** K3's L0/L2 (except the head edit), `test_k2_*`, `test_tfc2.py` existing cases, `test_fuel_cost_v2.py`, the cold and EV Finding store tests, `test_w401_work_service_postgres.py`, CH-2 thread tests (`test_ch2_*`), and both probe `--check`s. Any behaviour edit is stop S5.

**Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` if no venv), `tools\check-agent-workflow.ps1`, run directly, no `-ExecutionPolicy`. Guard-list joins (the consequence writer's table list, the transaction owner, rule-8 readers) are membership only, listed in the packet with the reason.

### 9j.9 K4a finish row, files, pre-flight, stops, size, branch

**Finish row KIS-4** (written now; runs at E3). Pure logic `kis4(windows, findings, consequences, prices, dispatch_consequences)` in `T/demo_combined_rows.py`, wired in `T/demo_combined_finish.py` after the PV-A row; L0 self-test with pass and fail bodies:
- every SUPPORTED Kisiwa fuel Finding's consequence litres equal its cited window's `residual_low/high` exactly;
- PRICED amounts equal litres × the stored price value exactly, and the stored price revision equals a re-run of `select_window_price` at `known_at = window_end`;
- no `financial_consequence_revision` row has this Finding's id;
- no stored or served amount equals (as `Decimal`, two places) the sum of a fuel amount with any Kisiwa dispatch `amount_high`, or of two fuel amounts.
- §8.7's KIS-3 and KIS-5 stay K9's.

**Files (approved list; anything else is stop S6):**
1. `backend/migrations/versions/0056_unexplained_fuel_finding.py`
2. `B/analytics/adapters/postgres_assessment_store.py` (`fuel_balance_persist` only)
3. `B/analytics/adapters/postgres_finding_store.py` (constants, `fuel_apply` and its private helpers only)
4. `B/financials/adapters/postgres_consequence_store.py` (`fuel_residual_append` only)
5. `B/fuel_balance/model.py` (§9j.5 read types), `adapters/postgres_fuel_balance_store.py` (the two reads), `findings_service.py` (new), `finding_text.py` (new), `composition.py`, `worker.py` (`raise`), `rules.py` (docstring only: K3 L2, name `idle_slot` and R3h at `:9-10`, wrap `:174`)
6. `B/chain/threads.py:31`, `B/chain/read.py:25`, and the PRE-FLIGHT (c) maps (one entry each)
7. `F/sites/MiniPerformance.tsx` (the two strings), `F/sites/__tests__/miniFuelRoutes.test.tsx` (`:188`, `:191`)
8. `T/demo_combined_rows.py`, `T/demo_combined_finish.py` (KIS-4), `T/checks/configuration-persistence.ps1` (list membership only)
9. Tests: §9j.8 A, B, C; `backend/tests/test_tfc2.py` (one case); `backend/tests/test_k3_fuel_balance_postgres.py` (head lines); `backend/tests/test_out_b2_vocabulary.py` (K4a literals added to the scan list).

**PRE-FLIGHT (no code first; batch every question in one message):**
- (a) The cold worker's shared-transaction pattern (`assessment_worker.py`, file:line) and how `cold_apply` receives its connection; confirm `fuel_apply` can be called the same way from `findings_service.py`.
- (b) Every reader of `finding`/`finding_revision` that would see a `fuel_balance` row and dereference a dispatch-only field (candidate minutes, `generator_asset_id`, the dispatch claim keys) without a domain filter: list file:line and state whether it filters by domain/analytic. In particular the Finding detail API (`B/finding_api.py`), the Findings index (`index_snapshot`), `estate/placement.py`, `estate/coverage.py`, `work/site_index.py:186`, `work/adapters/postgres_work_read.py:303`, `chain/lookup.py`.
- (c) The `git grep -n "cold_chain" backend/assetops_backend` map list (§9j.4).
- (d) Whether the lifecycle runner (`chain/lifecycle_run.py`, `config/chain/thread-lifecycle-v1.json` `clean_day_measures`) raises for a mechanism with no `clean_day_measures` entry. If it does, that is stop S4 (the Architect rules; K4a does not add a measure).
- (e) The guard lists the new writers, owner and table must join.

**Stops (report to the Architect; never design around them):**
- **S1** a §9j.8 C item differs (band, amount, text). Never edit the probe, its result, K3's parameters or the price.
- **S2** a write needs a NOT NULL relaxed, a dispatch column filled with an invented value, or a row in `financial_consequence_revision`.
- **S3** a reader in PRE-FLIGHT (b)/(c) raises or mis-renders on a `fuel_balance` row and is not fixed by one map entry.
- **S4** PRE-FLIGHT (d) shows the lifecycle runner needs a measure.
- **S5** an existing test needs a behaviour change (head bookkeeping excepted, §9j.8 B6).
- **S6** a file outside the approved list, or any Cold/EV byte change, or a Kobo board/golden change.
- **S7** more than 1.6 units.

**Dependencies, start, branch, DB, size:**
- Depends on K3 merged (yes, `ce03ae246`). Needs nothing from K0, K5, A3 or K6. **K4a can start now**, on lane 3.
- Branch `task/DIESEL-K4a-unexplained-fuel-finding`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k4a`, from main at or after `801efc0e2`. Opus first build and first review. `git add -f` of explicit paths.
- **DB: only `assetops_k4_test`** (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick, `serve` or suite. Part C when the machine is idle.
- **Size 1.4** (range 1.2–1.6): migration 0.25; three store methods 0.4; service, composition, CLI, price 0.2; text, maps, the two strings, K3 Lows 0.1; tests A+B 0.25; C and KIS-4 0.15; pre-flight 0.05.
- Reading budget: this §9j.1–§9j.9; §9d.4–§9d.5; `0009_finding_store.py:32-110`; `0022_w2_cold_assessment.py:40-80`, `:212-225`; `0025_w2_ev_session.py:40-80`, `:468-479`; `0011_financial_consequences.py:43-120`; `postgres_finding_store.py:39-50`, `:181-247`, `:586-711`; `postgres_assessment_store.py` (the cold persist it mirrors; pre-flight names lines); `B/financials/composition.py:134-155`; `B/financials/fuel_cost.py:440-464`; `B/chain/threads.py:1-180`; `B/chain/backfill.py:33-60`; `B/chain/adapters/postgres_chain_read.py:27-54`; `F/sites/MiniPerformance.tsx:1305-1345`; `host/tests/test_k3_fuel_balance_parity.py`.

### 9j.10 K4b: what it delivers (lane 1, after K4a merges; off the critical path)

- The Kisiwa board's **Protect** row shows the unexplained-fuel Finding (issue, thread line, in-hand/earlier Actions), a **"Fuel in the tank"** contributor and the new outcome **MG-8 "Fuel accounted for"**.
- The Portfolio **Protect** card lists each Site's unexplained-fuel line, never summed.
- COH-17 row **UF1** and its self-tests; the KIS-8 Protect-line half.
- **Unchanged:** every Cold and EV byte; Kobo's rows except the one MG-8 outcome entry (N/A); the Optimize row's "Fuel" contributor (`NO_FUEL_BALANCE`); the Grow, Optimize and Assure cards; PV-1's lines.

### 9j.11 K4b design (literals verbatim)

**Outcome MG-8 (`B/outcomes/catalogue.py`, `outcome_map.py`):**
- Catalogue, after MG-4 (PROTECT order MG-5, MG-4, MG-8): `_o("MG-8", MINI, "PROTECT_ASSET", "Fuel accounted for")`, measured.
- Map: `"FINDING:UNEXPLAINED_FUEL": (("MG-8",), ())`. No `@` alias changes.
- **Applicability:** `SiteFacts` gains `not_applicable: frozenset[str] = frozenset()` (last field, after `verified_values`). `board._row` and its `state_on` pass `applicable=o.key not in facts.not_applicable` to `outcome_state`. Cold/EV never set it.
- `mini.compose`: `not_applicable = {"MG-8"}` when the Site has **no** stored fuel-balance window at all as known at the board cutoff (Kobo); else empty. `settled["MG-8"]` = the window for **night D − 1** (the night that ends on board day D) exists as known and is not `NOT_ASSESSED`, and the fuel Finding read succeeded (`findings_ok` rule).
- Kobo's Protect row therefore gains exactly one `outcomes` entry `{"key": "MG-8", "label": "Fuel accounted for", "state": "NOT_APPLICABLE", "reason": "CONFIGURATION_NOT_APPLICABLE"}`; its state, tone, lead, headline and every other field are unchanged (NOT_APPLICABLE ranks last, `status.py:34`).

**Board reads (`B/site_outcomes/mini.py`, `read.py`):**
- `MiniPorts` gains, last and defaulted: `fuel_windows: Callable[[date, date], Any] = lambda lo, hi: ()` (K3's `windows`, tank resolved by the port) and `fuel_findings: Callable[[datetime, datetime], Any] = lambda lo, hi: ()` (K4a's `fuel_findings` at the board cutoff). Bound in `read.py` `mini_ports` from the fuel-balance composition; a failure is recorded by `Reads` (board PARTIAL), never a "0" claim.
- `FindingFact`s for fuel Findings are built from `fuel_findings(work_lo, end)` plus their thread rows (the chain reader's thread for `subject_ref` = tank) and **appended** to `findings`. `heads`, `lead_finding`, `money_head`, `lead` (the COST lead and the Trial option) stay on **dispatch heads only**: `lead` is chosen from Findings whose `mechanism == "GENERATOR_SUPPORT_CANDIDATE"`.
- Title on the board: `FINDING_TITLE_BY_MECHANISM = {"UNEXPLAINED_FUEL": {"SUPPORTED": "Unexplained fuel overnight", "NO_LONGER_SUPPORTED": "Unexplained fuel no longer supported by the latest check"}}`; the dispatch `FINDING_TITLE` map is unchanged and used for every other mechanism.
- Link: `refs.finding_ref(c, finding_id)` (K5 renders the page).

**Protect contributor "Fuel in the tank" (key `fuel_stock`), only on a Site with any stored window; placed after "Backup readiness".** For night D − 1's window `W` (latest as known):

| Case | Text | Chip |
|---|---|---|
| no window for the night | `FUEL_NO_WINDOW = "Not available yet · no fuel check for the night of {date}"` | none |
| `NOT_ASSESSED` | `FUEL_NOT_CHECKED = "Not available yet · the night of {date} could not be checked: {why}"` | `UNKNOWN_CHIP` |
| `WITHIN_MARGIN` | `FUEL_WITHIN = "Accounted for within the margin on the night of {date}"` | `HIGH_CHIP` |
| `BELOW_MATERIALITY` | `FUEL_BELOW = "About {lo}–{hi} L unexplained on the night of {date}, below the 40 L the check flags"` | `UNKNOWN_CHIP` |
| `UNEXPLAINED` | `FUEL_UNEXPLAINED = "About {lo}–{hi} L unexplained on the night of {date}"` | `{"label": "Limited", "tone": "amber"}` (the existing `PLACEMENT_CHIP["LIMITED"]`) |
| `EXCESS` | `FUEL_EXCESS = "More fuel in the tank than recorded on the night of {date}; a delivery may be unrecorded"` | `UNKNOWN_CHIP` |

`{why}` from `FUEL_REASON_WORDS = {"NO_SENSOR_ACCURACY": "no tank sensor accuracy declared", "SFC_MISSING": "no generator fuel rate declared", "NO_LOAD_RATE_MISSING": "no generator no-load rate declared", "MISSING_OPENING": "no tank reading at 6 pm", "MISSING_CLOSING": "no tank reading at noon", "FUEL_LEVEL_CONFLICT": "two different tank readings at the same time", "GENERATOR_KWH_UNKNOWN": "generator power readings incomplete", "IDLE_SECONDS_UNKNOWN": "generator state readings incomplete"}`. Litres and dates as §9j.7. Link: `refs.evidence_ref(c, "fuel")`.

**Board node and the Portfolio Protect line (PV-1's pattern):**
- `SiteFacts` gains `unexplained_fuel: tuple[Mapping[str, Any], ...] = ()`; `_row` adds `row["nodes"] = {**row["nodes"], "unexplained_fuel": [...]}` for `PROTECT_ASSET` only when non-empty (absent key = `[]`; every other board byte-equal).
- Entries: every fuel Finding whose latest revision (as known) is SUPPORTED and whose window ends inside the board's work window, by `night_date`: `{"key": finding_id, "night_date", "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE", "litres_low", "litres_high" (0.1 text), "amount_low", "amount_high" (money2 text or null), "currency" (or null), "text"}` with
  - `FUEL_LINE = "Unexplained fuel on the night of {date}: about {lo}–{hi} L, {lo_m}–{hi_m} {cur} at your declared price (a modelled range, shown on its own)"`;
  - unpriced: `FUEL_LINE_UNPRICED = "Unexplained fuel on the night of {date}: about {lo}–{hi} L (no money estimate)"`.
- `B/chain/vocabulary.py` `CARD_TEXT`, under Protect: `"protect.fuel_line": "{site} · {text}"`, `"protect.fuel_separate": "Unexplained fuel is shown on its own and never added to any other money"`.
- `portfolio_cards` (`read.py:794-837`): the `PROTECT` card gains `"fuel_lines"` (Site order, then `night_date`) and `"fuel_note"` (`protect.fuel_separate` iff lines, else `None`). **No total, no sum, no arithmetic across entries or with any other card.** Every other Protect key is byte-equal.
- Frontend (`F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`): `EstatePortfolioCard` gains `fuel_lines?: string[]; fuel_note?: string | null;`; rendered on the Protect card after `c.detail`, as PV-1 renders values: `<p className="oc-pfnote" data-portfolio-card-fuel-line>` per line, then `data-portfolio-card-fuel-note`. Server text only; no new CSS.

**Chain vocabulary and claims:** PRE-FLIGHT (b) confirms that `chain/claims.py`'s Protect claim (`SITES_DISRUPTED`) counts only service-disruption evidence and not an MG-8 Finding. If it would count it, K4b excludes `UNEXPLAINED_FUEL` from that claim's input, with a test. The open/in-hand/verified thread counts (`threads.classify`) include the fuel thread unchanged: that is correct.

**MOCK DEVIATIONs (header comment at each render or literal, and a packet row each):**
- **MD-FUEL-K4-1** (K4a text, K4b board issue): a Finding kind "Unexplained fuel overnight" that v69 does not have; v69 `:623-630` shows the fuel balance with no residual conclusion and defers "theft detection" (`:630`).
- **MD-FUEL-K4-2** (K4b): the Protect row gains outcome "Fuel accounted for" and contributor "Fuel in the tank"; v69's mini readiness lists "Fuel balance · None · No fuel balance" (`:345`) and no Protect fuel outcome.
- **MD-FUEL-K4-3** (K4b): the Portfolio Protect card lists unexplained-fuel lines; v69 `:131`, `:482` forbid a combined total, so each is its own line (as MD-FUEL-PV1-1).
- **MD-FUEL-K-2** (K4a): §9j.7.

### 9j.12 K4b coherence and finish rows

- **COH-17 row UF1** (`T/checks/chain_coherence.py`, new `coh17_fuel(w, summary, files, tally)` called right after `coh17_values`):
  - (i) `cards.PROTECT_ASSET.fuel_lines` equals the list rebuilt from `summary.sites[]` Protect `nodes.unexplained_fuel` with `protect.fuel_line` imported from `CARD_TEXT`;
  - (ii) for every same-currency pair drawn from {all fuel amounts} ∪ {Optimize claim amounts} ∪ {Assure `verified_values` amounts}, with at least one fuel amount in the pair, `f"{Decimal(a) + Decimal(b):.2f}"` appears in no string of any Portfolio card (walk all four cards' JSON);
  - (iii) `fuel_note` is `fuel_separate` iff lines;
  - an older bundle without the keys is skipped and counted.
  - Self-tests in `T/checks/test_chain_coherence.py`: pass (two lines); fail (i); fail (ii) with a fuel+Optimize sum in the Protect `detail`; fail (ii) with a fuel+fuel sum; fail (iii); skipped.
- **Finish row KIS-8a** (Protect half of §8.7 KIS-8; written now, runs at E3; `T/demo_combined_rows.py` `kis8_protect`, wired after KIS-4): on the week estate summary that contains Kisiwa's S+0 board, the Protect card's `fuel_lines` contains `card_text("protect.fuel_line", site=<Kisiwa name>, text=<the board node text>)` for night 4, and UF1 passes on that summary. L0 self-test pass/fail. The wording-guard half of KIS-8 stays K9's.

### 9j.13 K4b tests, files, pre-flight, stops, size, branch

**Tests (L0 unless named):**
- `backend/tests/test_k4b_protect_fuel.py` (fake ports): MG-8 NOT_APPLICABLE with no windows, UNKNOWN when night D−1 is NOT_ASSESSED, NEEDS_ATTENTION with an open SUPPORTED fuel Finding (rule 2), WATCH once its thread is ACTION_IN_HAND/applied; the six contributor cases and chips; the issue on Protect and on no other row; the COST lead and Trial option unchanged with and without a fuel Finding (must fail if `lead` is chosen from all Findings); thread line on Protect only; node present only when non-empty; Kobo Protect row with no windows equals main's except the MG-8 entry (must fail on any other diff).
- `test_pv1_value_lines.py`, `test_ch6b2_portfolio_cards.py`: Grow, Optimize, Assure byte-equal; Protect gains only `fuel_lines`/`fuel_note`; no card string contains a fuel sum.
- Goldens (`test_ch5a2_contract.py` and any mini board/estate goldens) regenerated by the DRIFT-R1 §2.2 procedure. **Acceptance:** the diff against main is only (a) each mini Protect row's `outcomes` gaining the MG-8 N/A entry and (b) `cards.PROTECT_ASSET` gaining `"fuel_lines": []` and `"fuel_note": null`. Anything else is stop S-b.
- `backend/tests/test_out_b2_vocabulary.py` gains every K4b literal; `test_out_b3_cold_ev.py` unchanged; `test_out_b4_imports.py` unchanged (no new import in `site_outcomes/` beyond the port call).
- Frontend: `F/estate/__tests__/estatePortfolio.test.tsx` and `portfolioFixtures.ts` (Protect renders lines and note; absent keys render nothing); the board's outcome list renders "Fuel accounted for" with its state label from the server (no new client words); `tsc`.
- Guards: A, W, N, V, M, chain coherence, `node tools/checks/frontend-hardwiring.mjs` (no rise); fast tier for the edited backend files. **Not run:** full suite, prepare.

**Files (approved list):** `B/outcomes/catalogue.py`, `B/outcomes/outcome_map.py`, `B/site_outcomes/board.py` (`SiteFacts` two fields, `_row` applicability and the node), `B/site_outcomes/mini.py`, `B/site_outcomes/read.py` (ports, `portfolio_cards` Protect keys), `B/chain/vocabulary.py` (two `CARD_TEXT` entries), `B/chain/claims.py` only if PRE-FLIGHT (b) requires, `F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`, `T/checks/chain_coherence.py`, `T/checks/test_chain_coherence.py`, `T/demo_combined_rows.py`, `T/demo_combined_finish.py`, the tests and goldens above.

**PRE-FLIGHT:** (a) every consumer of the mini catalogue list or `SITE_OUTCOMES` that enumerates outcomes (counts, frontend words, COH rows, estate categories), file:line, and what MG-8 does there; (b) the `SITES_DISRUPTED` claim input (above); (c) the chain reader call that gives a fuel Finding's thread view for `FindingFact.thread`/`lifecycle_view`; (d) whether A3 has merged (it edits `mini.py`/`board.py`; whichever of A3 and K4b merges second merges main first, PV-1-R's order rule).

**Stops:** **S-a** a guard rejects a literal (report the message; never reword silently); **S-b** a golden or Kobo diff beyond the acceptance above, or any Cold/EV change; **S-c** MG-8 changes Kobo's Protect row state, tone, lead or headline; **S-d** a placement needs a second placement path outside the outcome map; **S-e** more than 1.2 units.

**Dependencies, start, branch, DB, size:**
- Depends on **K4a merged**; PV-1, MB-1, CH-5d1 merged (yes). A3 is not a blocker (order rule above).
- Lane 1, after K5's first build (or whichever lane-1 builder frees first). Branch `task/DIESEL-K4b-protect-fuel`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k4b`. DB only `assetops_k4b_test` if a Postgres golden check needs one; never `assetops_demo3_full_test`. Opus first build and review.
- **Size 1.0** (range 0.85–1.2): MG-8 and applicability 0.2; board reads, Finding merge, lead restriction, titles 0.25; contributor, node, card, frontend 0.25; UF1, KIS-8a 0.1; goldens and tests 0.2.

### 9j.14 Effects on other cards

- **K5:** owns the Finding page panel (`finding_lines` server-composed, served by K5's own read route), the Findings-list entry for the fuel Finding and the Fuel page in window mode. K5 **must not** edit `FUEL_NOTICE` or the RESIDUAL row (K4a owns them). If K5 builds before K4a merges, it merges main before its packet.
- **K6:** raises its W1 Action from the fuel Finding's thread. Its card must confirm (pre-flight) that the Action path accepts an origin Finding of domain `fuel_balance` (`action.origin_finding_id` is a plain FK to `finding`; any service-level check for a dispatch Finding is K6's to rule on). K6 needs K4a only, not K4b.
- **K7:** prepare order of §9j.6; the night-4 Finding is raised after night 4 is assessed.
- **K8:** the Portfolio Protect line moved to K4b, so K8 = **0.85** (plus §9c.4's device-id copy risk, +0.1–0.25). K8 keeps the four-Site lists, COH re-expectations and the all-26 recapture, which now also captures the reworded Fuel notice and Kobo's MG-8 N/A entry.
- **K9:** the repo-wide wording guard (H4) stays K9's; K4a's local test is not a substitute.

### 9j.15 Sizes, critical path, tripwire, date

- **K4 = K4a 1.4 + K4b 1.0 = 2.4** (§9.5 had 2.0; +0.4: the assessment-backed Finding domain, the own consequence table, MG-8 and the Protect card line). **K8 −0.15** (line moved). Net **+0.25**, reported, not absorbed (contingency spent, §9h.8): **Kisiwa total 17.35 → 17.6**.
- **Critical path** (F0r 0.65 → K1 1.25 → K3 1.75 already spent = 3.65), then **K4a 1.4 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0 ≈ 8.3 lane-units**. The lane-1 branch (K4a → K4b 1.0 → K8 code 0.85–1.1 → captures → K9) is about 8.15–8.4 and joins at the captures. **The path is about 8.3–8.4, below the 9.75 tripwire (8.9 before this ruling). No cut is needed and no owner question arises.**
- K0 keeps its float (needed by K7's data part, which runs beside K4a and K6).
- **Demo date:** unchanged at about +3.25 working days (it may come in by up to about 0.2 day, because the split takes K4b off the critical path).
- **Plan HTML rows (coordinator):** the DIESEL-1-R3 build-units row becomes 17.6 with "K4a 1.4, K4b 1.0, K8 0.85"; the lanes figure shows K4a on lane 3 before K6 and K4b on lane 1 between K5 and K8; the rulings table gains "DIESEL-1-R3j: K4 split; unexplained-fuel Finding as a `fuel_balance` domain on the cold/EV pattern; own consequence table `fuel-residual-1` (0056), never summed; outcome MG-8 'Fuel accounted for' on Protect (Kobo N/A); Portfolio Protect line moved from K8; the two 'theft' strings reworded in K4a"; the after-the-demo list gains "re-price unexplained-fuel consequences on a price correction" and "fuel-finding tick stage".

### 9j.16 Owner questions

None. For the owner's information, in plain words: the "unexplained fuel" finding gets its own place under "Protect asset & capital", with a new line "Fuel accounted for". Sites that cannot check their fuel yet, such as Kobo, show that line as not applicable, and nothing else on their screens changes. The fuel's dollar value is always shown on its own and is never added to any other figure. The plan is about a quarter-unit bigger, but splitting the unit lets more of it run in parallel, so the demo date does not move.

