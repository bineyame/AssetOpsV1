# 3A7: one month reconciled against the operator's own accounts (implementer spec)

Status: **spec rev 1, handshake open** (`handshake.md`). Questions during the build: `mid-build-questions.md`.
Reviewer: `reviewer-guide.md`. Decisions with reasons: `rulings.md` (D-3A7.1 to D-3A7.7).

Architect (Claude), 2026-11-20. Lane A (sources), the deep-dive path's unit 7 (`two-week-build-plan.md` §0.1 row 7,
§0.4 "Recorded money reads *not yet reconciled* until one closed month matches their management accounts", §0.6 risk
2; D-BW1.11; owner RC8 "reconciliation tolerance 1 in 100 of the month's revenue and of its fuel or energy cost; the
owner may set it per operator", RC5 mini-grid only: `owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`).
- **Structure:** integration design `integration-source-to-canonical-design.md` §7.2, the pilot validation gate:
  "one closed month reconciled, within a tolerance agreed at the start, against the operator's management accounts on
  revenue and fuel or energy cost before any value is shown as Recorded money; until then the money factors are
  labelled with their provenance".
- **Builds on (merged, `main` e2387b334):** `3A4` (`commercial/months.py`: `CommercialMonths.site_month`,
  `MonthAmounts.closed`, `MonthLine`, `month_bounds`; the store's `site_zones`, `site_ids`); `4b`
  (`structure/money.py`: `COST_STATUSES`, the revenue and fuel-cost rows of its §3.4 table; `CommercialLeafSource`);
  `3A3` (`AccountService.onboard_person`, the loader's person checks); `3A2` (`commercial_upload_settings`,
  `has_control_character`); `3C1a` (`COMMAND_ROLES`, `roles_of`). **Branches after `3A6` merges** (same store,
  adapter, model, composition, words, permissions and guard).

Non-screen. **1.5 units, two commits.** Discovery review (W5): a money figure's label and a new table.

## 0. Before you start

- **Branch** `task/3A7-month-reconciled` off `main` after `3A6` merges; worktree `/opt/assetecon/AssetOpsV1-3a7`.
  Code starts when the handshake has no open question.
- **Python, PYTHONPATH, module-path record:** as 3A3 §0.
- **Read:** this spec and `rulings.md`; 3A4 `spec.md` §3 and §4 (its fixture is reused, never edited); 4b `spec.md`
  §3.3 and §3.4; `commercial/months.py`; `structure/money.py`; `commercial/store.py`;
  `commercial/adapters/postgres_commercial_store.py`; `load_emulated_exports.py` (the person checks to copy);
  `backend/tests/test_3a4_commercial_months.py` (`MonthsMemoryStore`) and `test_4b_money_leaves.py` (its world).
- **Databases:** `*_test` only, through the harness; Postgres runs `tools/heavy-slot.sh --db -- <command>`.
- **Migration** `0068_commercial_reconciliation`, revising `0067_source_profile` (renumber at merge preparation if
  another lands first; tests read head and `down_revision` from the modules).
- **Collisions.** `5c` (UI lane) reads this unit's service; it adds its own route. `3B7a` does not snapshot the
  standing (it is read live, D-3A7.6).

## 1. Outcome and why

The finance lead records a closed month's totals from the operator's management accounts: revenue and fuel cost, for
one Site or for the whole organisation, with where the figures came from. The product compares them with the same
money it shows (4b's revenue and fuel cost, summed over the scope) within the tolerance (1 in 100 by default, RC8).
Until at least one recorded month matches, every money figure reads "*<origin>*, not yet reconciled" ("Recorded, not
yet reconciled" for an operator's own records), and the standing says why in plain words. A month whose own recorded
totals do not match reads "not yet reconciled" whatever other months show, and says exactly what did not match:
which heading, the accounts' figure, the records' figure, the difference, its share and the amount allowed; or what is
missing (no fuel invoices, another currency, the month still open). A late record that pushes a matched month outside
the tolerance makes it unmatched again, because the comparison is made on every read.

Why next: the deep-dive screen (`5c`) must not show an operator's money as Recorded while it disagrees with their own
accounts (§7.2's gate; build plan risk 2: "the screen then says so; the conversation must expect it").

## 2. Rules

### 2.1 What is compared (D-3A7.1)

- **Headings**, in this order: `revenue`, `fuel_cost` (RC5: mini-grid; `energy_cost` is not accepted, queue Q2).
- **Scope:** one Site (`site_id`), or the organisation (`site_id` None: every Site of the tenant from `site_zones`,
  each read with `site_month`; portfolio-level records are not money of either heading).
- **Recorded figure** over the scope's Site-months for `period`, from `MonthAmounts.lines`:
  - `revenue`: Σ `value` of lines with `kind == "CHARGE"` and `measure == "AMOUNT"` (any dims, any provenance).
  - `fuel_cost`: Σ `value` of lines with `kind == "EXPENSE"`, `measure == "AMOUNT"`, dims `category` `FUEL` and
    `status` in `COST_STATUSES` (imported from `structure/money.py`, the definition 4b shows; D-3A7.1).
  - The heading's **used lines** are those lines; `sources` = sorted distinct `f"commercial:{s}"` over their
    `source_systems`; `origins` = the distinct provenances in `ORIGIN_ORDER` (`structure/evaluate.py`).
- **Arithmetic** exact, under `Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])` (D-3A4.9); no float.
  `difference = recorded - accounts`; `allowed = tolerance * accounts`.

### 2.2 A heading's state (exact order)

1. Any Site-month of the scope has `closed` false: `NOT_COMPARABLE`, reason `MONTH_OPEN`.
2. No used line: `accounts == 0` gives `MATCHED`, reason `NONE_RECORDED_ZERO_STATED` (`recorded` None); else
   `NOT_COMPARABLE`, reason `NOT_RECEIVED`.
3. The used lines' currencies are not exactly `{statement currency}`: `NOT_COMPARABLE`, reason `CURRENCY_MISMATCH`
   (`record_currencies` the sorted distinct list).
4. `abs(difference) <= allowed`: `MATCHED`; else `NOT_MATCHED`.

A **statement's** state: `MATCHED` when both headings are; else `NOT_MATCHED` when either is; else `NOT_COMPARABLE`.

### 2.3 The standing of a Site-month (D-3A7.2, D-3A7.3)

- A statement is **current** when it is the latest (by `recorded_at`, then `id` text) for its `(site_id, period)`.
- `covering(site_id, period)` = the current statement for `(site_id, period)` (when `site_id` is not None) and the
  current organisation statement for `period`, each when present, Site first.
- **The gate:** at least one current statement of the tenant whose live check (§2.2, now) is `MATCHED`.
- `standing(tenant_id, site_id, period)`, in order:
  1. a covering statement that is `NOT_MATCHED`: `reconciled` false, reason `THIS_MONTH_NOT_MATCHED`, `this_month`
     that statement's check (the first such, Site first);
  2. else a covering statement that is `NOT_COMPARABLE`: false, `THIS_MONTH_NOT_COMPARABLE`, `this_month` it;
  3. else the gate holds: true, `RECONCILED`; `this_month` the first covering statement if any (it is `MATCHED`); the
     **cited** month is `this_month` or else the matched current statement with the latest `period`, organisation
     before Site, then Site code;
  4. else no statement exists for the tenant: false, `NO_STATEMENT`;
  5. else: false, `NONE_MATCHED`.
- `money_word(base: str, standing) -> str`: `base` when `standing.reconciled`, else `f"{base}, not yet reconciled"`.
  `base` is the figure's own origin word, which `5c` takes from 3A5's rule (D-BW1.9); this unit does not choose it.
- The check is made on every read. The stored `result_at_record` and `tolerance_at_record` record what the finance
  lead saw when recording; they are never read back into the standing.

### 2.4 Tolerance (D-3A7.4)

`DEFAULT_TOLERANCE = Decimal("0.01")` (RC8). A tenant's tolerance is its latest `commercial_reconciliation_tolerance`
row, else the default. Every check reads the tenant's tolerance **now**. Set only by
`reconcile_month set-tolerance`, which requires `--owner-ref` naming an `owner/owner-<topic>-<date>.md` file that
exists in the repository checkout the command runs from; `0 < tolerance <= 0.05`, at most four decimals.

### 2.5 Recording a statement (D-3A7.5)

`CommercialReconciliation.record(tenant_id, actor, *, site_code, period, currency, revenue, fuel_cost, source_ref,
by_script) -> StatementCheck`. Refusals, in order, `ReconRefused(code, params)` (nothing written):
1. `actor.role` not in `roles_of("commercial.accounts_statement")` (new key: `(FINANCE,)`): `RECON_ROLE`.
2. `period` not `[0-9]{4}-(0[1-9]|1[0-2])` (ASCII): `RECON_PERIOD`.
3. `site_code` given and not the tenant's (`store.site_ids`): `RECON_SITE_UNKNOWN {site}`.
4. `currency` not `[A-Z]{3}`: `RECON_CURRENCY`.
5. `revenue` or `fuel_cost` not `(0|[1-9][0-9]{0,11})\.[0-9]{2}` (ASCII): `RECON_AMOUNT {heading}`.
6. `source_ref`: 1 to 200 characters, equal to its strip, no control character (`has_control_character`):
   `RECON_SOURCE_REF`.
7. The month is not closed for the scope (any of its Site-months `closed` false; an organisation with no Site is
   `RECON_SITE_UNKNOWN`): `RECON_MONTH_OPEN {period}`.

Then the live check (§2.2) and one `add_accounts_statement` row with `result_at_record` and `tolerance_at_record`.
Returns the check.

### 2.6 The service

`backend/assetops_backend/commercial/reconciliation.py`:

```python
HEADINGS = ("revenue", "fuel_cost")
DEFAULT_TOLERANCE = Decimal("0.01")

@dataclass(frozen=True)
class HeadingCheck:
    heading: str
    state: str                       # MATCHED | NOT_MATCHED | NOT_COMPARABLE
    reason: str | None               # NONE_RECORDED_ZERO_STATED | MONTH_OPEN | NOT_RECEIVED | CURRENCY_MISMATCH | None
    accounts: Decimal
    recorded: Decimal | None
    difference: Decimal | None
    allowed: Decimal
    record_currencies: tuple[str, ...]
    sources: tuple[str, ...]
    origins: tuple[str, ...]
    words: Message
    text: str

@dataclass(frozen=True)
class StatementCheck:
    statement_id: UUID; site_id: UUID | None; site_code: str | None; period: str; currency: str
    tolerance: Decimal; state: str; headings: tuple[HeadingCheck, HeadingCheck]
    recorded_by: UUID; recorded_at: datetime; recorded_by_script: bool; source_ref: str
    words: Message; text: str

@dataclass(frozen=True)
class MoneyStanding:
    tenant_id: UUID; site_id: UUID | None; period: str
    reconciled: bool
    reason: str                      # RECONCILED | THIS_MONTH_NOT_MATCHED | THIS_MONTH_NOT_COMPARABLE | NO_STATEMENT | NONE_MATCHED
    this_month: StatementCheck | None
    cited: StatementCheck | None     # the month the sentence names (RECONCILED only)
    tolerance: Decimal
    words: Message; text: str

class CommercialReconciliation:
    def __init__(self, months: CommercialMonths, store: CommercialStore) -> None
    def record(...) -> StatementCheck                         # §2.5
    def check(self, tenant_id, statement: StatementRow) -> StatementCheck
    def statements(self, tenant_id) -> tuple[StatementCheck, ...]   # current ones, live, by (period, org first, site code)
    def standing(self, tenant_id, site_id: UUID | None, period: str) -> MoneyStanding
    def tolerance(self, tenant_id) -> Decimal
    def set_tolerance(self, tenant_id, tolerance: str, owner_ref: str) -> None
def money_word(base: str, standing: MoneyStanding) -> str
```

The clock is the months service's (`months.clock`, exposed as a read-only property if it is not public). One
`standing` read calls `statements` once and `site_month` once per Site-month it checks.

### 2.7 Words (`i18n/messages.py`, a `# 3A7` block; every figure formatted as below)

Formats: money `f"{q:,.2f}"` with `q` quantised to 0.01 `ROUND_HALF_EVEN` (display only); share `abs(difference) /
accounts * 100` quantised to 0.01 `ROUND_HALF_EVEN` with `%`, omitted when `accounts` is 0; tolerance
`format((tolerance * 100).normalize(), "f") + "%"` (`1%`, `0.5%`); month `"October 2026"` (English month name);
scope: the Site code, or `the organisation`; heading names `Revenue`, `Fuel cost`; record nouns `billing records`
(revenue), `fuel invoices` (fuel cost); currencies listed `A`, `A and B`, `A, B and C`. `{gap}` is `"{d} more"`,
`"{d} less"` (`d` = money of `abs(difference)`) or `"the same"`.

| Key | English |
|---|---|
| `reconciliation.heading.matched` | {heading}: the accounts say {accounts} {currency} and the records say {recorded} {currency}, {gap}, within the {allowed} allowed ({tolerance}). |
| `reconciliation.heading.not_matched` | {heading}: the accounts say {accounts} {currency} and the records say {recorded} {currency}, {gap}{share}, beyond the {allowed} allowed ({tolerance}). |
| `reconciliation.heading.zero_stated` | {heading}: the accounts say 0.00 {currency} and no {records} are recorded. |
| `reconciliation.heading.not_received` | {heading}: the accounts say {accounts} {currency}, but no {records} are recorded for {month}. |
| `reconciliation.heading.currency_mismatch` | {heading}: the accounts are in {currency}, but the records are in {record_currencies}. |
| `reconciliation.heading.month_open` | {heading}: {month} is not closed yet. |
| `reconciliation.statement.matched` | {month} ({scope}) matches the management accounts within {tolerance}. |
| `reconciliation.statement.not_matched` | {month} ({scope}) does not match the management accounts within {tolerance}. |
| `reconciliation.statement.not_comparable` | {month} ({scope}) cannot be compared with the management accounts yet. |
| `reconciliation.standing.reconciled` | Reconciled: {month} ({scope}) matches the management accounts within {tolerance}. |
| `reconciliation.standing.this_month_not_matched` | Not yet reconciled: {month} ({scope}) does not match the management accounts within {tolerance}. |
| `reconciliation.standing.this_month_not_comparable` | Not yet reconciled: {month} ({scope}) cannot be compared with the management accounts yet. |
| `reconciliation.standing.no_statement` | Not yet reconciled: no closed month has been compared with the management accounts. |
| `reconciliation.standing.none_matched` | Not yet reconciled: no month matches the management accounts within {tolerance} yet. |
| `reconciliation.suffix` | not yet reconciled |
| `reconciliation.refused.<code lower>` | `recon_role` Only the finance lead records the management accounts. · `recon_period` Write the month as YYYY-MM, like 2026-10. · `recon_site_unknown` This Site is not one of this organisation's: {site}. · `recon_currency` Write the currency as three capital letters, like USD. · `recon_amount` Write the {heading} with two decimals and no separators, like 1200.00. · `recon_source_ref` Say where the figures come from, in at most 200 characters. · `recon_month_open` {period} is not closed yet: record a closed month. |

`{share}` is `" (" + share + ")"` or `""`. `money_word` composes with `render(message("reconciliation.suffix"))`.

## 3. Code

| File | Holds |
|---|---|
| `backend/migrations/versions/0068_commercial_reconciliation.py` | §4 |
| `backend/assetops_backend/commercial/model.py`, `store.py`, `adapters/postgres_commercial_store.py` | `StatementRow`, `ToleranceRow`; `add_accounts_statement`, `accounts_statements`, `add_tolerance`, `latest_tolerance`, `site_codes` |
| `backend/assetops_backend/commercial/reconciliation.py` | §2.1 to §2.6 |
| `backend/assetops_backend/commercial/composition.py` | `build_commercial_reconciliation(database_url) -> (CommercialReconciliation, dispose)`, on `build_commercial_reads` |
| `backend/assetops_backend/reconcile_month.py` | §5 |
| `backend/assetops_backend/accounts/permissions.py` | `"commercial.accounts_statement": (FINANCE,)` |
| `backend/assetops_backend/i18n/messages.py` | §2.7 |
| `tools/checks/configuration-persistence.ps1` | both new tables join `$commercialTables` (same writer, plain-INSERT shape) |

## 4. Migration `0068_commercial_reconciliation`

```sql
CREATE TABLE commercial_accounts_statement (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,                                   -- NULL: the organisation's accounts
    period text NOT NULL CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    currency text NOT NULL CHECK (currency ~ '^[A-Z]{3}$'),
    revenue text NOT NULL CHECK (revenue ~ '^(0|[1-9][0-9]{0,11})\.[0-9]{2}$'),
    fuel_cost text NOT NULL CHECK (fuel_cost ~ '^(0|[1-9][0-9]{0,11})\.[0-9]{2}$'),
    source_ref text NOT NULL CHECK (char_length(source_ref) BETWEEN 1 AND 200 AND source_ref = btrim(source_ref)),
    recorded_at timestamptz NOT NULL,
    recorded_by uuid NOT NULL,
    recorded_role text NOT NULL CHECK (recorded_role = 'FINANCE_AND_COMMERCIAL_LEAD'),
    recorded_by_script boolean NOT NULL,
    result_at_record text NOT NULL CHECK (result_at_record IN ('MATCHED', 'NOT_MATCHED', 'NOT_COMPARABLE')),
    tolerance_at_record text NOT NULL CHECK (tolerance_at_record ~ '^0\.[0-9]{1,4}$'),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id)
);
CREATE INDEX commercial_accounts_statement_tenant ON commercial_accounts_statement (tenant_id, period, recorded_at);
CREATE TABLE commercial_reconciliation_tolerance (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    tolerance text NOT NULL CHECK (tolerance ~ '^0\.[0-9]{1,4}$' AND tolerance::numeric > 0
                                   AND tolerance::numeric <= 0.05),
    owner_ref text NOT NULL CHECK (owner_ref ~ '^owner/owner-[a-z0-9-]+\.md$'),
    set_at timestamptz NOT NULL
);
```
Both append-only (`ledger_append_only` triggers); no defaults; downgrade refused if a row exists (0065's pattern).
Reads: `accounts_statements(tenant)` every row `ORDER BY recorded_at, id`; `latest_tolerance(tenant)` `ORDER BY set_at
DESC, id DESC LIMIT 1`; `site_codes(tenant)`: `SELECT id, site_code FROM site WHERE tenant_id = :t`. The memory store
mirrors them.

## 5. The command (D-3A7.5)

`python -m assetops_backend.reconcile_month {record,show,set-tolerance} --tenant SLUG ...`; `build_parser()` public;
`main(argv, *, reconciliation=None, accounts=None)` (injected services skip the composition; tests).
- Before any connection: `DATABASE_URL` unset `DATABASE_URL_REQUIRED`; `commercial_upload_settings(url)` (a
  `ConfigurationError` is `CONFIGURATION <message>`), exit 2. The tenant from `--tenant` (`tenant_id` by slug through
  the accounts service; unknown `TENANT_NOT_FOUND`, exit 2).
- `record --as EMAIL --period P [--site CODE] --currency C --revenue R --fuel-cost F --source-ref TEXT`: the person
  as 3A3 §2.6 step 5 (`PERSON_NOT_FOUND`, `PERSON_ROLE_REQUIRED` for `commercial.accounts_statement`), exit 2; a
  `ReconRefused` prints `{"state": "REFUSED", "code", "params", "text"}`, exit 3; else one JSON line, the statement
  check (§6.1's shape) with `"recorded_by_script": true`, exit 0.
- `show --period P [--site CODE]`: one JSON line, the standing (§6.1's shape), exit 0.
- `set-tolerance --tolerance T --owner-ref PATH`: `TOLERANCE_INVALID` or `OWNER_REF_INVALID` (pattern, or the file
  absent under the repository root resolved from the module's path), exit 2; else `{"state": "SET", "tolerance"}`.

### 6.1 JSON shapes (stable; `5c` reads the service, the command prints these)

Decimals as strings in plain notation (`format(d, "f")`, exact, unquantised); `words` omitted, `text` kept.
- Heading: `{"heading", "state", "reason", "accounts", "recorded", "difference", "allowed", "record_currencies",
  "sources", "origins", "text"}`.
- Statement: `{"statement_id", "site_code", "period", "currency", "tolerance", "state", "headings": [<2>],
  "recorded_by", "recorded_at", "recorded_by_script", "source_ref", "text"}`.
- Standing: `{"site_code", "period", "reconciled", "reason", "tolerance", "this_month": <statement> | null, "cited":
  <statement> | null, "text"}`.

## 6. Fixtures (hand-computed; the tests write these literals, W2)

### 6.1 3A4's `commercial_months_kobo.json`, reused (never edited)

Kobo `2026-10`. After A to D (read clock `2026-11-20T08:00:00+00:00`): revenue lines 120.00, 300.00, 75.50 and the
FIXED 10.00 → **505.50**; fuel cost lines PAID 500.00, INVOICED 262.50 → **762.50** (the 900.00 QUOTE is a REPAIR
expense and not fuel; it is excluded either way). After E and F: revenue **495.50** (FIXED moved to November); fuel
**775.00** (262.50 corrected to 275.00).

Statement K (Site KOBO-001, `2026-10`, USD, revenue `500.00`, fuel cost `780.00`, tolerance 0.01):
- After A to D: revenue `NOT_MATCHED`: "Revenue: the accounts say 500.00 USD and the records say 505.50 USD, 5.50
  more (1.10%), beyond the 5.00 allowed (1%)." Fuel `NOT_MATCHED`: "Fuel cost: the accounts say 780.00 USD and the
  records say 762.50 USD, 17.50 less (2.24%), beyond the 7.80 allowed (1%)." Statement `NOT_MATCHED`.
- After E and F: revenue `MATCHED` (4.50 less, within 5.00); fuel `MATCHED` (5.00 less, within 7.80); statement
  `MATCHED`: "October 2026 (KOBO-001) matches the management accounts within 1%."
- Same statement in EUR: both `CURRENCY_MISMATCH`: "Revenue: the accounts are in EUR, but the records are in USD."

### 6.2 `backend/tests/fixtures/3a7/reconciliation_two_sites.json` (3A4's format)

Tenant `lakeside-power`, Sites `KOBO-001` and `MTO-001` (both `Africa/Nairobi`), provenance `source-emulated`, USD,
`source_version` "1", period `2026-10`, read clock `2026-11-20T08:00:00+00:00`.

| Step, `at` | Batch | Records |
|---|---|---|
| A, `2026-11-03T06:00:00+00:00` | `billing_export`, `kobo-vending` | CHARGEs, effective `2026-10-01` to `2026-11-01`, USAGE, `tariff_code` `T-RES`: `KOBO-CH-1001` KOBO-001 300.00, 750 kWh, `C-0001`; `KOBO-CH-1002` KOBO-001 200.00, 500 kWh, `C-0002`; `MTO-CH-1001` MTO-001 250.00, 625 kWh, `C-0101` |
| B, same | `expense_ledger`, `lakeside-accounts` | EXPENSEs, occurred `2026-10-14T11:00:00+03:00`, `counterparty_ref` `SUP-X`, `document_ref` the ID, subject SITE: `KOBO-EX-F-1` KOBO-001 FUEL PAID 400.00, 320 L; `KOBO-EX-F-2` KOBO-001 FUEL INVOICED 100.00, 80 L; `KOBO-EX-F-Q` KOBO-001 FUEL QUOTE 900.00, 720 L; `MTO-EX-OM-1` MTO-001 OM PAID 120.00 |
| C, `2026-11-10T09:00:00+00:00` | `expense_ledger`, `lakeside-accounts` | `KOBO-EX-F-3` KOBO-001 FUEL INVOICED 12.50, 10 L (late) |

Recorded: organisation revenue **750.00** (300.00 + 200.00 + 250.00); fuel cost **500.00** after A and B (QUOTE
excluded), **512.50** after C. KOBO-001: revenue 500.00, fuel 500.00 then 512.50. MTO-001: revenue 250.00, no fuel
line.

| Case | Statement (USD, tolerance 0.01 unless stated) | Expected |
|---|---|---|
| T1 | S1 organisation, revenue `755.00`, fuel `505.00`, recorded at `2026-11-05T10:00:00+00:00` after A, B | revenue MATCHED (5.00 less, within 7.55); fuel MATCHED (5.00 less, within 5.05); stored `result_at_record` MATCHED. Standing KOBO-001 and MTO-001 `2026-10`: reconciled, `RECONCILED`, "Reconciled: October 2026 (the organisation) matches the management accounts within 1%." |
| T2 | after C, S1 read again | fuel NOT_MATCHED: "Fuel cost: the accounts say 505.00 USD and the records say 512.50 USD, 7.50 more (1.49%), beyond the 5.05 allowed (1%)." Standing KOBO-001 and MTO-001 `2026-10`: `THIS_MONTH_NOT_MATCHED`; `money_word("Recorded", ...)` is "Recorded, not yet reconciled"; S1's stored `result_at_record` still MATCHED |
| T3 | after T2, tolerance set to 0.02 (owner ref) | S1 fuel MATCHED (7.50 more, within 10.10 (2%)); standing reconciled, text ends "within 2%." |
| T4 | after T2 (tolerance 0.01), S2 organisation revenue `755.00`, fuel `510.00` at `2026-11-12T10:00:00+00:00` | S2 current, supersedes S1: fuel 2.50 more, within 5.10; standing reconciled |
| T5 | S3 MTO-001 revenue `250.00`, fuel `0.00` | revenue MATCHED "..., the same, within the 2.50 allowed (1%)."; fuel MATCHED `NONE_RECORDED_ZERO_STATED`: "Fuel cost: the accounts say 0.00 USD and no fuel invoices are recorded." |
| T6 | S4 MTO-001 revenue `250.00`, fuel `40.00` | fuel NOT_COMPARABLE `NOT_RECEIVED`: "Fuel cost: the accounts say 40.00 USD, but no fuel invoices are recorded for October 2026."; statement NOT_COMPARABLE; standing MTO-001 `2026-10` (no other statement for MTO) `THIS_MONTH_NOT_COMPARABLE` |
| T7 | no statement at all | standing KOBO-001 `2026-10`: `NO_STATEMENT`, "Not yet reconciled: no closed month has been compared with the management accounts." |
| T8 | only S1 after C (unmatched); standing KOBO-001 `2026-09` (not covered) | `NONE_MATCHED`, "Not yet reconciled: no month matches the management accounts within 1% yet." |
| T9 | period `2026-11` at the read clock | `RECON_MONTH_OPEN`, nothing written |

**Boundary (pure, `_compare(accounts, recorded, tolerance)`):** accounts 505.00, tolerance 0.01: recorded 510.05
MATCHED, 510.06 NOT_MATCHED, 499.95 MATCHED, 499.94 NOT_MATCHED. Accounts 0.00, recorded 3.00: NOT_MATCHED, text
"..., 3.00 more, beyond the 0.00 allowed (1%)." (no share). Accounts 1,234,567.89 renders `1,234,567.89`.

## 7. Tests

**Service, no database** (`backend/tests/test_3a7_reconciliation.py`; 3A4's `MonthsMemoryStore` extended with §4's
tables; Fiona FINANCE, Ana ANALYST):
- R1 §6.1 K before and after E and F, and in EUR (literals above).
- R2 §6.2's cases, each text literal compared in full: T1, T2, T4, T5, T6 in that order on one world; T3 on its own
  world brought to T2's state; T7, T8 and T9 each on a fresh world in the state the row names.
- R3 Boundary cases.
- R4 Refusals of §2.5, one each, nothing written: Ana `RECON_ROLE`; `2026-13` `RECON_PERIOD`; `NOPE-001`
  `RECON_SITE_UNKNOWN`; `usd` `RECON_CURRENCY`; `755` and `1,200.00` `RECON_AMOUNT revenue`; `""` and a 201-character
  ref `RECON_SOURCE_REF`; T9.
- R5 Latest wins: two statements for one `(site, period)` with equal `recorded_at` resolve by `id` text order.
- R6 `money_word`: "Recorded" and "Emulated" bases, reconciled and not.
- R7 **Same definition as the screen (D-3A7.1).** On §6.2 after C, 4b's `CommercialLeafSource.stated(ctx,
  "revenue")` and `stated(ctx, "fuel_cost")` for KOBO-001 `2026-10` equal this unit's KOBO-001 recorded figures
  (500.00, 512.50); for MTO-001 revenue 250.00, and 4b's `fuel_cost` is absent exactly where this unit's fuel heading
  has no used line. Built with 4b's test world (`test_4b_money_leaves.py`).
- R8 Reads per standing: one `accounts_statements` and one `latest_tolerance` read; `site_month` once per Site-month
  checked (spies).

**Command, no database** (`backend/tests/test_3a7_reconcile_command.py`, injected services): M1 `record` as Fiona
prints the statement JSON with `recorded_by_script` true, exit 0; M2 as Ana `PERSON_ROLE_REQUIRED`, exit 2; M3 a
refused amount prints REFUSED with its text, exit 3; M4 `show` prints the standing; M5 `set-tolerance 0.06`
`TOLERANCE_INVALID`, `--owner-ref owner/nope.md` `OWNER_REF_INVALID`, a real owner file and 0.02 `SET`.

**Postgres** (`backend/tests/test_3a7_reconciliation_postgres.py`, pooled `--db`, `*_test` only): Q1 upgrade;
UPDATE and DELETE refused by the triggers; downgrade refused with a row; a tolerance `0.06` refused by the CHECK. Q2
§6.2 loaded through 3A1's service on the routed database; T1, T2 and T4 give the same literals as R2. Q3 the
statement FK refuses another tenant's Site.

**Regression:** `test_3a4_*`, `test_4b_*`, the 3A6 and 3A3 service files, check-all.

## 8. Done (questions; each can fail)

1. Do the recorded figures equal what the screen shows (R7), summed exactly over the scope (R1, R2)?
2. Is money "not yet reconciled" until a current statement matches within the tenant's tolerance, and does the
   standing say which month reconciled it (T1, T7, T8)?
3. Does a month whose own statement does not match, or cannot be compared, read "not yet reconciled" even when another
   month matched, saying exactly what did not match (T2, T6)?
4. Does a late record change the standing in both directions, because the check is live (R1, T2)?
5. Is every sentence the literal of §2.7 and §6, with the share omitted for a zero figure (R2, R3)?
6. Is a statement refused for an open month, a wrong role, a malformed amount and a foreign Site, writing nothing
   (R4, Q3)?
7. Is the tolerance 1% unless an owner-cited row sets it, and is it read at check time (T3, M5)?
8. Does each planted violation in the reviewer guide fail its named test?
9. Is nothing changed beyond §3's files, the fixture and tests of §6 and §7, and the packet?

Packet: `specs/3A7-month-reconciled/packet.md`.

## 9. Units

| Unit | Content | Commit |
|---|---|---|
| 0.75 | Migration 0068, store and adapter, `reconciliation.py`, words, guard, R1 to R8 | 1 |
| 0.75 | Composition, the command, M1 to M5, Q1 to Q3; check-all; packet | 2 |

## 10. Out of scope

A screen or route (`5c` adds the route that shows the standing); energy cost for cold-chain and EV (RC5); collections
or O&M headings; matching statements line by line; snapshotting the standing (`3B7a`); importing the accounts from a
file.

## 11. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | Must the finance lead type the figures themselves, or may the analyst run the command naming them? | The command names the finance lead (`--as`), stores `recorded_by_script` true, and the runbook records that the finance lead read the figures out; a screen for the finance lead comes with the upload screen (`3C0b`, next fortnight). **Owner to weigh in** if a person must enter them on screen even in the deep-dive; a "yes" moves the entry to `5c`'s route and nothing else changes |
| Q2 | Fuel or energy cost | Fuel cost only (RC5, mini-grid); `energy_cost` comes with the cold-chain and EV records (`9d`, `9e`) |
| Q3 | Does one matched month reconcile the whole tenant, or only that month? | The tenant (§7.2: "one closed month reconciled ... before any value is shown as Recorded money"); a month with its own unmatched statement still reads not yet reconciled |
| Q4 | Tolerance base | The management accounts' figure (the operator's reference), per heading; both headings must match |
| Q5 | Revenue: billed charges or net of credit notes? | Billed charges, the figure 4b shows (R7); credit notes (ADJUSTMENT) are not in either. If the operator's accounts net them, the difference is shown, not hidden |
