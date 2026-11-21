# 3A7: one month reconciled against the operator's own accounts (implementer spec)

Status: **in_review (commit 1 of 2, D-SC1.28; commit 2 waits for SC-1a: `handoff.md`)**; spec rev 2, handshake round 1 answered (`rulings.md` "Handshake answers (round 1)"; coding may start once
3A6 has merged). Questions during the build: `mid-build-questions.md`. Reviewer: `reviewer-guide.md` rev 2. Decisions
with reasons: `rulings.md` (D-3A7.1 to D-3A7.13).

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

Non-screen. **1.75 units, two commits** (rev 2: +0.25 for `known_at`, the opener rule, display rounding and scope). Discovery review (W5): a money figure's label and a new table.

## 0. Before you start

- **Branch** `task/3A7-month-reconciled` off `main` after `3A6` merges; worktree `/opt/assetecon/AssetOpsV1-3a7`.
  Code starts when the handshake has no open question.
- **Python, PYTHONPATH, module-path record:** as 3A3 §0.
- **Read:** this spec and `rulings.md`; 3A4 `spec.md` §3 and §4 (its fixture is reused, never edited); 4b `spec.md`
  §3.3 and §3.4; `commercial/months.py`; `structure/money.py`; `commercial/store.py`;
  `commercial/adapters/postgres_commercial_store.py`; `load_emulated_exports.py` (the person checks to copy);
  `backend/tests/test_3a4_commercial_months.py` (`MonthsMemoryStore`) and `test_4b_money_leaves.py` (its world).
- **Databases:** `*_test` only, through the harness; Postgres runs `tools/heavy-slot.sh --db -- <command>`.
- **Migration (D-3A6.12; renumbered at the main merge for commit 2)** `0069_commercial_reconciliation` revises
  `0068_structure_finding` (3B4 took 0068 on main first). Q1 asserts the chain link
  `("0069_commercial_reconciliation", "0068_structure_finding")`, never
  "is head" (D-3B7A.14).
- **Collisions.** `5c` (UI lane) reads this unit's service; it adds its own route, and passes the shown snapshot's
  `as_of` as `known_at` (D-3A7.9; 5c's spec must cite it). `3B7a` does not snapshot the standing (D-3A7.6).

## 1. Outcome and why

The finance lead records a closed month's totals from the operator's management accounts: revenue and fuel cost, for
one Site or for the whole organisation, with where the figures came from. The product compares them with the same
money it shows (4b's revenue and fuel cost, summed over the scope) within the tolerance (1 in 100 by default, RC8).
Until at least one recorded month matches on both revenue and fuel cost against recorded money (D-3A7.8), every money
figure reads "*<origin>*, not yet reconciled" ("Recorded, not
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
- **Scope:** one mini-grid Site (`site_id`), or the organisation (`site_id` None: every Site of the tenant whose
  `site_type` maps to `MINI_GRID` through `structure.read.SITE_TYPE_TO_STRUCTURE`, from `store.site_rows`, each read
  with `site_month`; portfolio-level records are not money of either heading; D-3A7.11).
- **Recorded figure** over the scope's Site-months for `period`, from `MonthAmounts.lines`:
  - `revenue`: Σ `value` of lines with `kind == "CHARGE"` and `measure == "AMOUNT"` (any dims, any provenance).
  - `fuel_cost`: Σ `value` of lines with `kind == "EXPENSE"`, `measure == "AMOUNT"`, dims `category` `FUEL` and
    `status` in `COST_STATUSES` (imported from `structure/money.py`, the definition 4b shows; D-3A7.1).
  - The heading's **used lines** are those lines; `sources` = sorted distinct `f"commercial:{s}"` over their
    `source_systems`; `origins` = the distinct provenances in `ORIGIN_ORDER` (`structure/evaluate.py`).
- **Arithmetic** exact, under `EXACT = Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])` (D-3A4.9); no
  float. `difference = recorded - accounts`; `allowed = tolerance * accounts`; the comparison of §2.2 rule 4 is made on
  these exact values. Display figures and the share are computed only in `DISPLAY` (§2.7; D-3A7.10).

### 2.2 A heading's state (exact order)

1. Any Site-month of the scope has `closed` false: `NOT_COMPARABLE`, reason `MONTH_OPEN`.
2. No used line: `accounts == 0` gives `MATCHED`, reason `NONE_RECORDED_ZERO_STATED` (`recorded` None); else
   `NOT_COMPARABLE`, reason `NOT_RECEIVED`.
3. The used lines' currencies are not exactly `{statement currency}`: `NOT_COMPARABLE`, reason `CURRENCY_MISMATCH`
   (`record_currencies` the sorted distinct list).
4. `abs(difference) <= allowed`: `MATCHED`; else `NOT_MATCHED`.

A **statement's** state: `MATCHED` when both headings are; else `NOT_MATCHED` when either is; else `NOT_COMPARABLE`.
A statement **opens** the gate when its state is `MATCHED` and both headings' `reason` is None, i.e. both matched
against used lines (D-3A7.8); a `NONE_RECORDED_ZERO_STATED` heading makes its statement `MATCHED` but not an opener.

### 2.3 The standing of a Site-month (D-3A7.2, D-3A7.3, D-3A7.8, D-3A7.9, D-3A7.13)

- **The instant.** Every read takes `known_at: datetime | None = None`; `k = known_at` or, when None, `months.clock()`.
  At `k` only statements with `recorded_at <= k` exist, the tolerance is §2.4's at `k`, and every Site-month is read
  with `site_month(tenant_id, site_id, period, known_at=known_at)` (None stays None: live). `5c` passes the `as_of`
  of the 3B7a snapshot whose figures it shows, and None beside live figures.
- A statement is **current** when it is the latest (by `recorded_at`, then `id` text) among those existing at `k` for
  its `(site_id, period)`.
- `covering(site_id, period)` = the current statement for `(site_id, period)` (when `site_id` is not None) and the
  current organisation statement for `period`, each when present, Site first.
- **Cited order** of current statements: `period` descending, the organisation's before Sites', then Site code.
- **The gate:** the first current statement, in cited order, whose live check (§2.2, at `k`) **opens** (D-3A7.8); the
  walk stops there.
- `standing(tenant_id, site_id, period, *, known_at=None)`, in order:
  1. a covering statement that is `NOT_MATCHED`: `reconciled` false, reason `THIS_MONTH_NOT_MATCHED`, `this_month`
     that statement's check (the first such, Site first);
  2. else a covering statement that is `NOT_COMPARABLE`: false, `THIS_MONTH_NOT_COMPARABLE`, `this_month` it;
  3. else the gate holds: true, `RECONCILED`; `this_month` the first covering statement if any (it is `MATCHED`); the
     **cited** month is `this_month` or else the gate's statement;
  4. else no statement exists for the tenant at `k`: false, `NO_STATEMENT`;
  5. else: false, `NONE_MATCHED`.
- **Text (D-3A7.13).** For reasons 1 and 2, `text` = the standing sentence + `" "` + the `text` of each of
  `this_month`'s headings whose state is not `MATCHED`, in heading order, joined by `" "`. Otherwise `text` is the
  standing sentence. `words` is always the standing sentence's message.
- **Reads per call (handshake R9).** One `store.accounts_statements`, one `store.tolerances`, one `store.site_rows`;
  `site_month` at most once per `(site_id, period)` within the call (a memo local to the call; no cache across calls).
- `money_word(base: str, standing) -> str`: `base` when `standing.reconciled`, else `f"{base}, not yet reconciled"`.
  `base` is the figure's own origin word, which `5c` takes from 3A5's rule (D-BW1.9); this unit does not choose it.
- The check is made on every read. The stored `result_at_record` and `tolerance_at_record` record what the finance
  lead saw when recording; they are never read back into the standing.

### 2.4 Tolerance (D-3A7.4, D-3A7.12)

`DEFAULT_TOLERANCE = Decimal("0.01")` (RC8). A tenant's tolerance at `k` is its latest
`commercial_reconciliation_tolerance` row (by `set_at`, then `id` text) with `set_at <= k`, else the default. Every
check reads it at its `k`. Set only by `reconcile_month set-tolerance`, which requires `--owner-ref` naming an
`owner/owner-<topic>.md` file that exists under the owner root (the repository root resolved from the module's path;
`main(..., owner_root=...)` in tests) and whose UTF-8 text contains the tenant's slug and the tolerance as written
(`0.02`) or as §2.7's percentage (`2%`), each as a whole token (not preceded by a digit or `.`, not followed by
a digit), so `12%` does not cite `2%`; else `OWNER_REF_INVALID`. `0 < tolerance <= 0.05`, at most four decimals. The
row stores `owner_ref_sha256` (SHA-256 of the file's bytes). A deployment without the owner root cannot set a
tolerance (1% stands).

### 2.5 Recording a statement (D-3A7.5)

`CommercialReconciliation.record(tenant_id, actor, *, site_code, period, currency, revenue, fuel_cost, source_ref,
by_script) -> StatementCheck`. Refusals, in order, `ReconRefused(code, params)` (nothing written):
1. `actor.role` not in `roles_of("commercial.accounts_statement")` (new key: `(FINANCE,)`): `RECON_ROLE`.
2. `period` not `[0-9]{4}-(0[1-9]|1[0-2])` (ASCII): `RECON_PERIOD`.
3. `site_code` given and not the tenant's (`store.site_rows`): `RECON_SITE_UNKNOWN {site}`.
3a. `site_code` given and its `site_type` not mapped to `MINI_GRID`: `RECON_SITE_TYPE {site}` (D-3A7.11).
4. `currency` not `[A-Z]{3}`: `RECON_CURRENCY`.
5. `revenue` or `fuel_cost` not `(0|[1-9][0-9]{0,11})\.[0-9]{2}` (ASCII): `RECON_AMOUNT {heading}`.
6. `source_ref`: 1 to 200 characters, equal to its strip, no control character (`has_control_character`):
   `RECON_SOURCE_REF`.
7. The month is not closed for the scope (any of its Site-months `closed` false; an organisation with no mini-grid
   Site is `RECON_SITE_UNKNOWN`): `RECON_MONTH_OPEN {period}`.

`recorded_at` is `months.clock()` at the call.

Then the live check (§2.2, `known_at` None) and one `add_accounts_statement` row with `result_at_record` and
`tolerance_at_record`.
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
    tolerance: Decimal; state: str; opens: bool; headings: tuple[HeadingCheck, HeadingCheck]
    recorded_by: UUID; recorded_at: datetime; recorded_by_script: bool; source_ref: str
    words: Message; text: str

@dataclass(frozen=True)
class MoneyStanding:
    tenant_id: UUID; site_id: UUID | None; period: str; known_at: datetime | None
    reconciled: bool
    reason: str                      # RECONCILED | THIS_MONTH_NOT_MATCHED | THIS_MONTH_NOT_COMPARABLE | NO_STATEMENT | NONE_MATCHED
    this_month: StatementCheck | None
    cited: StatementCheck | None     # the month the sentence names (RECONCILED only)
    tolerance: Decimal
    words: Message; text: str

class CommercialReconciliation:
    def __init__(self, months: CommercialMonths, store: CommercialStore) -> None
    def record(...) -> StatementCheck                         # §2.5
    def check(self, tenant_id, statement: StatementRow, *, known_at=None) -> StatementCheck
    def statements(self, tenant_id, *, known_at=None) -> tuple[StatementCheck, ...]   # current at k, by (period, org first, site code)
    def standing(self, tenant_id, site_id: UUID | None, period: str, *, known_at=None) -> MoneyStanding
    def tolerance(self, tenant_id, *, known_at=None) -> Decimal
    def set_tolerance(self, tenant_id, tolerance: str, owner_ref: str) -> None
def money_word(base: str, standing: MoneyStanding) -> str
```

The clock is the months service's (`months.clock`, exposed as a read-only property if it is not public). Reads per
`standing` call: §2.3 (it does not call `statements`). Module functions used by the tests: `_compare(accounts,
recorded, tolerance) -> str` (the state of §2.2 rule 4) and `heading_words(heading, state, reason, accounts, recorded,
tolerance, currency, period, record_currencies) -> Message`.

### 2.7 Words (`i18n/messages.py`, a `# 3A7` block; every figure formatted as below)

Formats (D-3A7.10), all in `DISPLAY = Context(prec=34, traps=[InvalidOperation, DivisionByZero, Overflow])`, each
figure `quantize(Decimal("0.01"), rounding=R)` then `f"{q:,.2f}"` (display only; the JSON keeps exact values):

| Figure | `MATCHED` sentence | `NOT_MATCHED` sentence |
|---|---|---|
| accounts, recorded | `ROUND_HALF_EVEN` | `ROUND_HALF_EVEN` |
| `d` = `abs(difference)` | `ROUND_DOWN` | `ROUND_UP` |
| allowed | `ROUND_UP` | `ROUND_DOWN` |
| share = `d_exact / accounts * 100`, `%` | not shown | `ROUND_UP`; omitted when `accounts` is 0 |

Tolerance `format((tolerance * 100).normalize(), "f") + "%"` (`1%`, `0.5%`); month `"October 2026"` (English month
name); scope: the Site code, or `the organisation`; heading names `Revenue`, `Fuel cost`; heading words `revenue`,
`fuel cost`; record nouns `billing records` (revenue), `fuel invoices` (fuel cost); currencies listed `A`, `A and B`,
`A, B and C`. `{gap}` is `"the same"` when `difference` is exactly 0; else, with `q` the displayed `d`, `"{q} more"` or
`"{q} less"` by the sign, and `"less than 0.01 more"` / `"less than 0.01 less"` when `q` displays `0.00`.

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
| `reconciliation.standing.none_matched` | Not yet reconciled: no month's recorded revenue and fuel cost both match the management accounts within {tolerance} yet. |
| `reconciliation.suffix` | not yet reconciled |
| `reconciliation.refused.<code lower>` | `recon_role` Only the finance lead records the management accounts. · `recon_period` Write the month as YYYY-MM, like 2026-10. · `recon_site_unknown` This Site is not one of this organisation's: {site}. · `recon_currency` Write the currency as three capital letters, like USD. · `recon_amount` Write the {heading_words} with two decimals and no separators, like 1200.00. · `recon_site_type` Only mini-grid Sites are compared with the management accounts for now: {site}. · `recon_source_ref` Say where the figures come from, in at most 200 characters. · `recon_month_open` {period} is not closed yet: record a closed month. |

`{share}` is `" (" + share + ")"` or `""`. `money_word` composes with `render(message("reconciliation.suffix"))`.

## 3. Code

| File | Holds |
|---|---|
| `backend/migrations/versions/0069_commercial_reconciliation.py` | §4 |
| `backend/assetops_backend/commercial/model.py`, `store.py`, `adapters/postgres_commercial_store.py` | `StatementRow`, `ToleranceRow`, `SiteRow`; `add_accounts_statement`, `accounts_statements`, `add_tolerance`, `tolerances`, `site_rows` |
| `backend/assetops_backend/commercial/reconciliation.py` | §2.1 to §2.6 |
| `backend/assetops_backend/commercial/composition.py` | `build_commercial_reconciliation(database_url) -> (CommercialReconciliation, dispose)`, on `build_commercial_reads` |
| `backend/assetops_backend/reconcile_month.py` | §5 |
| `backend/assetops_backend/accounts/permissions.py` | `"commercial.accounts_statement": (FINANCE,)` |
| `backend/assetops_backend/i18n/messages.py` | §2.7 |
| `tools/checks/configuration-persistence.ps1` | both new tables join `$commercialTables` (same writer, plain-INSERT shape) |

## 4. Migration `0069_commercial_reconciliation`

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
    tolerance text NOT NULL CHECK (CASE WHEN tolerance ~ '^0\.[0-9]{1,4}$'
                                        THEN tolerance::numeric > 0 AND tolerance::numeric <= 0.05
                                        ELSE false END),
    owner_ref text NOT NULL CHECK (owner_ref ~ '^owner/owner-[a-z0-9-]+\.md$'),
    owner_ref_sha256 text NOT NULL CHECK (owner_ref_sha256 ~ '^[0-9a-f]{64}$'),
    set_at timestamptz NOT NULL
);
```
Both append-only (`ledger_append_only` triggers); no defaults; downgrade refused if a row exists (0065's pattern).
Reads: `accounts_statements(tenant)` every row `ORDER BY recorded_at, id`; `tolerances(tenant)` every row `ORDER BY
set_at, id` (the service picks the one at `k`, §2.4); `site_rows(tenant)`: `SELECT id, site_code, site_type FROM site
WHERE tenant_id = :t ORDER BY site_code` as `SiteRow(site_id, site_code, site_type)`. The memory store mirrors them.

## 5. The command (D-3A7.5)

`python -m assetops_backend.reconcile_month {record,show,set-tolerance} --tenant SLUG ...`; `build_parser()` public;
`main(argv, *, reconciliation=None, accounts=None, owner_root: Path | None = None)` (injected services skip the
composition; `owner_root` None is the repository root resolved from the module's path; tests pass a temporary folder).
- Before any connection: `DATABASE_URL` unset `DATABASE_URL_REQUIRED`; `commercial_upload_settings(url)` (a
  `ConfigurationError` is `CONFIGURATION <message>`), exit 2. The tenant from `--tenant` through `AccountService.tenant_by_slug`
  (3A6, D-3A6.17; None is `TENANT_NOT_FOUND`, exit 2).
- `record --as EMAIL --period P [--site CODE] --currency C --revenue R --fuel-cost F --source-ref TEXT`: the person
  as 3A3 §2.6 step 5 (`PERSON_NOT_FOUND`, `PERSON_ROLE_REQUIRED` for `commercial.accounts_statement`), exit 2; a
  `ReconRefused` prints `{"state": "REFUSED", "code", "params", "text"}`, exit 3; else one JSON line, the statement
  check (§6.1's shape) with `"recorded_by_script": true`, exit 0.
- `show --period P [--site CODE] [--known-at ISO]`: one JSON line, the standing (§6.1's shape) at `known_at` (an ISO
  instant with an offset; malformed is `KNOWN_AT_INVALID`, exit 2), exit 0.
- `set-tolerance --tolerance T --owner-ref PATH`: `TOLERANCE_INVALID` or `OWNER_REF_INVALID` (pattern; the file absent
  under the owner root; or its text missing the tenant's slug or the tolerance as written or as a percentage, §2.4),
  exit 2; else `{"state": "SET", "tolerance", "owner_ref_sha256"}`.

### 6.1 JSON shapes (stable; `5c` reads the service, the command prints these)

Decimals as strings in plain notation (`format(d, "f")`, exact, unquantised); `words` omitted, `text` kept.
- Heading: `{"heading", "state", "reason", "accounts", "recorded", "difference", "allowed", "record_currencies",
  "sources", "origins", "text"}`.
- Statement: `{"statement_id", "site_code", "period", "currency", "tolerance", "state", "opens", "headings": [<2>],
  "recorded_by", "recorded_at", "recorded_by_script", "source_ref", "text"}`.
- Standing: `{"site_code", "period", "known_at": <ISO> | null, "reconciled", "reason", "tolerance", "this_month":
  <statement> | null, "cited": <statement> | null, "text"}`. `recorded_by` stays a person ID; `5c` resolves the name
  through the accounts service (handshake R11).

## 6. Fixtures (hand-computed; the tests write these literals, W2)

### 6.1 3A4's `commercial_months_kobo.json`, reused (never edited)

Kobo `2026-10`. After A to D (read clock `2026-11-20T08:00:00+00:00`): revenue lines 120.00, 300.00, 75.50 and the
FIXED 10.00 → **505.50**; fuel cost lines PAID 500.00, INVOICED 262.50 → **762.50** (the 900.00 QUOTE is a REPAIR
expense and not fuel; it is excluded either way). After E and F: revenue **495.50** (FIXED moved to November); fuel
**775.00** (262.50 corrected to 275.00).

Statement K (Site KOBO-001, `2026-10`, USD, revenue `500.00`, fuel cost `780.00`, tolerance 0.01):
- After A to D: revenue `NOT_MATCHED`: "Revenue: the accounts say 500.00 USD and the records say 505.50 USD, 5.50
  more (1.10%), beyond the 5.00 allowed (1%)." Fuel `NOT_MATCHED`: "Fuel cost: the accounts say 780.00 USD and the
  records say 762.50 USD, 17.50 less (2.25%), beyond the 7.80 allowed (1%)." (17.50 / 780.00 = 2.2436%, rounded up,
  D-3A7.10.) Statement `NOT_MATCHED`.
- After E and F: revenue `MATCHED` (4.50 less, within 5.00); fuel `MATCHED` (5.00 less, within 7.80); statement
  `MATCHED`: "October 2026 (KOBO-001) matches the management accounts within 1%."
- Same statement in EUR: both `CURRENCY_MISMATCH`: "Revenue: the accounts are in EUR, but the records are in USD."

### 6.2 `backend/tests/fixtures/3a7/reconciliation_two_sites.json` (3A4's format)

Tenant `lakeside-power`, Sites `KOBO-001` and `MTO-001` (both `Africa/Nairobi`, `site_type` `MINIGRID`) and, rev 2,
`FRZ-001` (`Africa/Nairobi`, `site_type` `COLDCHAIN`; D-3A7.11), provenance `source-emulated`, USD, `source_version`
"1", period `2026-10`, read clock `2026-11-20T08:00:00+00:00`. `ReconMemoryStore(MonthsMemoryStore)`, defined in
`test_3a7_reconciliation.py` (3A4's file is not edited), adds §4's tables and `site_rows` with these types.

**Clock rule (handshake R3).** One settable clock is shared by the months service and the reconciliation service.
Each batch is loaded stamped at its step's `at`; a statement is recorded with the clock set to its `recorded_at`
below; a tolerance is set with the clock at its `set_at`; every read is made with the clock at the read clock. Step C
is loaded only after T1's reads.

| Step, `at` | Batch | Records |
|---|---|---|
| A, `2026-11-03T06:00:00+00:00` | `billing_export`, `kobo-vending` | CHARGEs, effective `2026-10-01` to `2026-11-01`, USAGE, `tariff_code` `T-RES`: `KOBO-CH-1001` KOBO-001 300.00, 750 kWh, `C-0001`; `KOBO-CH-1002` KOBO-001 200.00, 500 kWh, `C-0002`; `MTO-CH-1001` MTO-001 250.00, 625 kWh, `C-0101`; `FRZ-CH-1001` FRZ-001 999.00, 100 kWh, `C-0201` (excluded from every figure below) |
| B, same | `expense_ledger`, `lakeside-accounts` | EXPENSEs, occurred `2026-10-14T11:00:00+03:00`, `counterparty_ref` `SUP-X`, `document_ref` the ID, subject SITE: `KOBO-EX-F-1` KOBO-001 FUEL PAID 400.00, 320 L; `KOBO-EX-F-2` KOBO-001 FUEL INVOICED 100.00, 80 L; `KOBO-EX-F-Q` KOBO-001 FUEL QUOTE 900.00, 720 L; `MTO-EX-OM-1` MTO-001 OM PAID 120.00 |
| C, `2026-11-10T09:00:00+00:00` | `expense_ledger`, `lakeside-accounts` | `KOBO-EX-F-3` KOBO-001 FUEL INVOICED 12.50, 10 L (late) |

Recorded: organisation revenue **750.00** (300.00 + 200.00 + 250.00); fuel cost **500.00** after A and B (QUOTE
excluded), **512.50** after C. KOBO-001: revenue 500.00, fuel 500.00 then 512.50. MTO-001: revenue 250.00, no fuel
line.

| Case | Statement (USD, tolerance 0.01 unless stated) | Expected |
|---|---|---|
| T1 | S1 organisation, revenue `755.00`, fuel `505.00`, recorded at `2026-11-05T10:00:00+00:00` after A, B | revenue MATCHED (5.00 less, within 7.55); fuel MATCHED (5.00 less, within 5.05); stored `result_at_record` MATCHED. Standing KOBO-001 and MTO-001 `2026-10`: reconciled, `RECONCILED`, "Reconciled: October 2026 (the organisation) matches the management accounts within 1%." |
| T2 | after C, S1 read again | fuel NOT_MATCHED: "Fuel cost: the accounts say 505.00 USD and the records say 512.50 USD, 7.50 more (1.49%), beyond the 5.05 allowed (1%)." Standing KOBO-001 and MTO-001 `2026-10`: `THIS_MONTH_NOT_MATCHED`, text "Not yet reconciled: October 2026 (the organisation) does not match the management accounts within 1%. Fuel cost: the accounts say 505.00 USD and the records say 512.50 USD, 7.50 more (1.49%), beyond the 5.05 allowed (1%)."; `money_word("Recorded", ...)` is "Recorded, not yet reconciled"; S1's stored `result_at_record` still MATCHED |
| T3 | after T2, tolerance set to 0.02 (owner ref) at `set_at` `2026-11-15T10:00:00+00:00` | S1 fuel MATCHED (7.50 more, within 10.10 (2%)); standing reconciled, text ends "within 2%." |
| T4 | after T2 (tolerance 0.01), S2 organisation revenue `755.00`, fuel `510.00`, recorded at `2026-11-12T10:00:00+00:00` | S2 current, supersedes S1: fuel 2.50 more, within 5.10; standing reconciled |
| T5 | S3 MTO-001 revenue `250.00`, fuel `0.00`, recorded at `2026-11-13T10:00:00+00:00` | revenue MATCHED "Revenue: the accounts say 250.00 USD and the records say 250.00 USD, the same, within the 2.50 allowed (1%)."; fuel MATCHED `NONE_RECORDED_ZERO_STATED`: "Fuel cost: the accounts say 0.00 USD and no fuel invoices are recorded."; statement MATCHED, `opens` false |
| T6 | S4 MTO-001 revenue `250.00`, fuel `40.00`, recorded at `2026-11-14T10:00:00+00:00` (S4 is current for MTO-001) | fuel NOT_COMPARABLE `NOT_RECEIVED`: "Fuel cost: the accounts say 40.00 USD, but no fuel invoices are recorded for October 2026."; statement NOT_COMPARABLE; standing MTO-001 `2026-10` `THIS_MONTH_NOT_COMPARABLE`, text "Not yet reconciled: October 2026 (MTO-001) cannot be compared with the management accounts yet. Fuel cost: the accounts say 40.00 USD, but no fuel invoices are recorded for October 2026." |
| T7 | no statement at all | standing KOBO-001 `2026-10`: `NO_STATEMENT`, "Not yet reconciled: no closed month has been compared with the management accounts." |
| T8 | only S1 after C (unmatched); standing KOBO-001 `2026-09` (not covered) | `NONE_MATCHED`, "Not yet reconciled: no month's recorded revenue and fuel cost both match the management accounts within 1% yet." |
| T9 | period `2026-11` at the read clock | `RECON_MONTH_OPEN`, nothing written |
| T10 | fresh world, A and B only, S3 alone (as T5) | S3 MATCHED, `opens` false; standing KOBO-001 `2026-10` and MTO-001 `2026-10` both `NONE_MATCHED` (D-3A7.8) |

**Boundary (pure, `_compare(accounts, recorded, tolerance)` and `heading_words` for `revenue`, USD, `2026-10`):**
accounts 505.00, tolerance 0.01: recorded 510.05 MATCHED, 510.06 NOT_MATCHED, 499.95 MATCHED, 499.94 NOT_MATCHED.
Accounts 0.00, recorded 3.00: NOT_MATCHED, "Revenue: the accounts say 0.00 USD and the records say 3.00 USD, 3.00
more, beyond the 0.00 allowed (1%)." (no share). Rev 2 (D-3A7.10): accounts 501.50, recorded 506.52: NOT_MATCHED
(allowed exactly 5.015), "Revenue: the accounts say 501.50 USD and the records say 506.52 USD, 5.02 more (1.01%),
beyond the 5.01 allowed (1%)."; accounts 500.00, recorded 500.004: MATCHED, "Revenue: the accounts say 500.00 USD and
the records say 500.00 USD, less than 0.01 more, within the 5.00 allowed (1%)." Accounts 1,234,567.89 renders
`1,234,567.89`.

## 7. Tests

**Service, no database** (`backend/tests/test_3a7_reconciliation.py`; `ReconMemoryStore`, §6.2; Fiona FINANCE, Ana
ANALYST):
- R1 §6.1 K before and after E and F, and in EUR (literals above).
- R2 §6.2's cases, each text literal compared in full: T1, T2, T4, T5, T6 in that order on one world; T3 on its own
  world brought to T2's state; T7, T8, T9 and T10 each on a fresh world in the state the row names.
- R3 Boundary cases.
- R4 Refusals of §2.5, one each, nothing written: Ana `RECON_ROLE`; `2026-13` `RECON_PERIOD`; `NOPE-001`
  `RECON_SITE_UNKNOWN`; `usd` `RECON_CURRENCY`; `755` and `1,200.00` `RECON_AMOUNT revenue`; `""` and a 201-character
  ref `RECON_SOURCE_REF`; T9; `FRZ-001` `RECON_SITE_TYPE`.
- R5 Latest wins: two statements for one `(site, period)` with equal `recorded_at` resolve by `id` text order.
- R6 `money_word`: "Recorded" and "Emulated" bases, reconciled and not.
- R7 **Same definition as the screen (D-3A7.1).** On §6.2 after C, 4b's `CommercialLeafSource.stated(ctx,
  "revenue")` and `stated(ctx, "fuel_cost")` for KOBO-001 `2026-10` equal this unit's KOBO-001 recorded figures
  (500.00, 512.50); for MTO-001 revenue 250.00, and 4b's `fuel_cost` is absent exactly where this unit's fuel heading
  has no used line. Built with 4b's test world (`test_4b_money_leaves.py`).
- R8 Reads per standing (spies; §2.3): after T4, standing KOBO-001 `2026-10`: `accounts_statements` 1, `tolerances` 1,
  `site_rows` 1, `site_month` 2 (KOBO-001 and MTO-001 `2026-10`); after T6, standing MTO-001 `2026-10`: `site_month` 2
  (S4 and S2 share MTO-001's month through the memo); T8's standing KOBO-001 `2026-09`: `site_month` 2 (the gate walks
  S1 and stops); two consecutive standings read the months afresh (4, no cross-call cache).
- R9 The instant (D-3A7.9): fresh world, A and B loaded, S1 recorded at `2026-11-05T10:00:00+00:00`, C loaded; standing
  KOBO-001 `2026-10` with `known_at` `2026-11-06T00:00:00+00:00` is `RECONCILED` (fuel 500.00 within 5.05), with None
  `THIS_MONTH_NOT_MATCHED`, with `2026-11-04T00:00:00+00:00` `NO_STATEMENT`; T3's tolerance (set at
  `2026-11-15T10:00:00+00:00`) is not used by a standing at `2026-11-14T00:00:00+00:00`.
- R10 Scope (D-3A7.11): after T1, the organisation's revenue is 750.00 (FRZ-001's 999.00 excluded) and
  `site_month` is never called for FRZ-001.

**Command, no database** (`backend/tests/test_3a7_reconcile_command.py`, injected services): M1 `record` as Fiona
prints the statement JSON with `recorded_by_script` true, exit 0; M2 as Ana `PERSON_ROLE_REQUIRED`, exit 2; M3 a
refused amount prints REFUSED with its text, exit 3; M4 `show` prints the standing, and `show --known-at` R9's instant
prints R9's `RECONCILED`; M5 (owner root a temporary folder) `set-tolerance 0.06` `TOLERANCE_INVALID`, `--owner-ref
owner/nope.md` `OWNER_REF_INVALID`, `owner/owner-tol-2026-11-20.md` holding "lakeside-power 2%" and 0.02 `SET` with
the file's SHA-256, the same file without the slug `OWNER_REF_INVALID`, holding "lakeside-power 3%" with 0.02
`OWNER_REF_INVALID`.

**Postgres** (`backend/tests/test_3a7_reconciliation_postgres.py`, pooled `--db`, `*_test` only): Q1 upgrade and the
chain link; UPDATE and DELETE refused by the triggers; downgrade refused with a row; tolerances `'0.06'`, `'abc'` and
`'0.0000'` each refused by the CHECK (a check violation, not a cast error). Q2
§6.2 loaded through 3A1's service on the routed database; T1, T2 and T4 give the same literals as R2. Q3 the
statement FK refuses another tenant's Site.

**Regression:** `test_3a4_*`, `test_4b_*`, the 3A6 and 3A3 service files, check-all.

## 8. Done (questions; each can fail)

1. Do the recorded figures equal what the screen shows (R7), summed exactly over the scope (R1, R2)?
2. Is money "not yet reconciled" until a current statement opens the gate within the tenant's tolerance, and does
   the standing say which month reconciled it (T1, T7, T8, T10)?
3. Does a month whose own statement does not match, or cannot be compared, read "not yet reconciled" even when another
   month matched, saying exactly what did not match (T2, T6)?
4. Does a late record change the standing in both directions, because the check is live (R1, T2)?
5. Is every sentence the literal of §2.7 and §6, with the share omitted for a zero figure (R2, R3)?
6. Is a statement refused for an open month, a wrong role, a malformed amount and a foreign Site, writing nothing
   (R4, Q3)?
7. Is the tolerance 1% unless a row citing an owner file that names the tenant and the figure sets it, and is it read
   at the check's instant (T3, M5, R9)?
8. Does each planted violation in the reviewer guide fail its named test?
9. Is nothing changed beyond §3's files, the fixture and tests of §6 and §7, `test_3c1a_person_work.py` (`SPEC_ROLES`
   gains `"commercial.accounts_statement": (FINANCE,)`, one line), and the packet?
10. Does only a statement compared on both headings open the gate (T10), and does the standing at a `known_at` label
    the figure of that instant (R9)?

Packet: `specs/3A7-month-reconciled/packet.md`.

## 9. Units

| Unit | Content | Commit |
|---|---|---|
| 1 | Migration 0069, store and adapter, `reconciliation.py`, words, guard, R1 to R10 | 1 |
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
| Q6 | An operator with no fuel at all (solar only): can it ever open the gate? (D-3A7.8) | No: the gate needs both headings compared against recorded lines, so such an operator's money stays "not yet reconciled". **Owner to weigh in** only if a pilot operator has no generator (then a revenue-only gate for a tenant with no fuel records at all is a one-line rule) |
