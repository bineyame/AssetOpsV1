# 3A4: amounts by month (implementer spec)

Status: live, spec (handshake step 1; `.ai/RULES.md` §4).

Architect (Claude), 2026-11-20. Lane B, on the deep-dive path's critical chain (`3B3` → `3A4` → `4b` and `5a`;
`two-week-build-plan.md` §0.1 row 3; D-BW1.8 to D-BW1.12; owner RC1 to RC9 accepted).
- **Structure:** page P3A (`specs/3A1-commercial-record-store/structure-page-P3A.md`, approved 20 Nov): rules 2
  ("a late record changes its own month ... marked for recalculation"), 5 ("not received is not zero") and 7
  (evidence words come from the record).
- **Builds on (merged):** `3A1` (`CommercialStore.latest_revisions`, `record_history`, `intake`, `RevisionRow`,
  D-3A1.8 "latest before any filter"), `2a` (`loads_canonical`, `parse_record`, `LEAF_FACTORS`, `PROVENANCES`).
  **Read by** `4b` and `5a` (through 3B3's `LeafSource` port: `structure/sources.py` `ReadContext`, `LeafSource`,
  `SOURCE_STATE`, on `task/3B3-structure-read`) and `3B7a` (the month stamps).
- **Decisions:** `rulings.md` (D-3A4.1 to D-3A4.9). **Reviewer guide:** `reviewer-guide.md`.

Non-screen. **2 units, two commits.** Discovery review (W5): money figures and a new read seam.

## 0. Before you start

- **Branch** `task/3A4-amounts-by-month` off `main` **after `3B3` merges** (lane B's order; the parity test of §6
  imports 3B3's `month_window`). Worktree `/opt/assetecon/AssetOpsV1-3a4`. Code starts when the handshake has no
  open question.
- **Python:** as 3A1 §0; record the module paths in the packet.
- **Read:** `rulings.md`; P3A; 3A1 `spec.md` §2 to §4 and `rulings.md` (D-3A1.8); 2a `spec.md` §6.2 to §6.5;
  `backend/assetops_backend/commercial/` (all); `structure/sources.py` (`month_window`, `ReadContext`) and
  `structure/evaluate.py` (`LeafValue`, `Missing`) on `main` after 3B3; `backend/tests/test_3a1_commercial_service.py:
  46-230`.
- **Databases:** `*_test` only, through the harness, Postgres runs as `tools/heavy-slot.sh --db -- <command>`.
  Never ports 5490 or 8990, the walkthrough DB or Docker. **No migration.**
- **Collisions.** `3A2` (lane A, same days) adds write methods to `commercial/store.py`, the adapter and
  `commercial/composition.py`; you add read methods. Whichever merges second merges `main` first. You do not touch
  `structure/` (D-3A4.8).

## 1. Outcome and why

One service reads the commercial store as money by month: for a Site (or the portfolio) and a month, every heading
the operator's records name, summed exactly, kept apart by currency, unit and evidence origin, with no line where no
record exists. A record placed in a month counts there once, in its latest revision, so a late invoice or a
correction moves money to its own month. Each month read carries a stamp; a later record that changes the month makes
the stamp stale, which is how dependent reads learn they are out of date.

Why next: `4b` (money leaves into the structure read) and `5a` (targets from budget lines) read this, and `3B7a`
rebuilds snapshots from its stale stamps. It is the critical chain's second link.

## 2. Store additions (3A1 code; read only)

Add to `CommercialStore`, the Postgres adapter and a test subclass of the in-memory store:

1. `latest_revisions(..., known_at: datetime | None = None)`. When given, only revisions with `recorded_at <=
   known_at` are candidates; "latest" is then picked per record over those, and only then the filters apply
   (D-3A1.8, D-3A4.7). SQL: in the inner query's `WHERE`, `AND (CAST(:known AS timestamptz) IS NULL OR v.recorded_at
   <= CAST(:known AS timestamptz))`. A record with no revision by `known_at` does not appear.
2. `intake_revisions(tenant_id, intake_id) -> tuple[tuple[RevisionRow, RevisionRow | None], ...]`: each revision the
   intake wrote, with the revision it supersedes (`None` for revision 1), sorted by `(source_system, source_record_id)`
   byte-wise. At most two statements: the intake's revisions, then the superseded ones by ID.
3. `site_zones(tenant_id) -> Mapping[UUID, str]`: `SELECT id, timezone FROM site WHERE tenant_id = :t`.

No write, no lock, no guard change.

## 3. Rules

### 3.1 Which records (D-3A4.1)

`MONEY_KINDS = ("CHARGE", "RECEIPT", "SETTLEMENT", "ADJUSTMENT", "EXPENSE", "BUDGET_LINE")`, in this order. Every
other kind is ignored here (tariffs, meter reads, rosters and the rest are read by their own slices). Only latest
revisions count, per D-3A1.8, as of `known_at` when given.

### 3.2 Placing a revision in a month (D-3A4.2)

- `recognition_period` present: that month, basis `RECOGNITION_PERIOD`.
- A `SETTLEMENT` without it: the month of `settled_at` in the Site's time zone (`site_zones`), basis `SETTLED_AT`.
- `month_bounds(period, tz) -> (lo, hi)`: `[local midnight of day 1, local midnight of day 1 of the next month)` in
  `tz`, as UTC instants; the same rule as 3B3's `month_window` (P3), written here, not imported (D-3A4.8).
  Portfolio-level records use `UTC`.
- A revision is in the month of the bucket `(site_id, period)`; a portfolio-level record has `site_id = None`.

### 3.3 Lines (D-3A4.3, D-3A4.4, D-3A4.5)

Each placed revision is parsed once from its `canonical` (`parse_record(loads_canonical(text.encode("utf-8")))`; a
failure is a `RuntimeError("stored canonical does not parse")`, a bug). It contributes to lines keyed by
`(kind, dims, measure, currency, unit, provenance)`:

| Kind | `dims` (names in order; value `None` when absent) | Measures |
|---|---|---|
| `CHARGE` | `line_type`, `tariff_class` | AMOUNT; QUANTITY when `quantity` is present (its unit) |
| `RECEIPT` | `status`, `method` | AMOUNT |
| `SETTLEMENT` | `provider` | AMOUNT |
| `ADJUSTMENT` | `reason_code` | AMOUNT when `amount`; QUANTITY when `quantity` |
| `EXPENSE` | `category`, `status` | AMOUNT; QUANTITY when `quantity` (litres, FUEL) |
| `BUDGET_LINE` | `factor_id`, `version_ref`, `line_ref` | DECLARED: `body.value`, `currency` = `body.currency` or None, `unit` = `str(LEAF_FACTORS[factor_id].unit)` for a catalogue leaf, else None |

`status` is the record's `status`; the other dims are body fields. `dims` is a tuple of `(name, value)` pairs.

- **Sums are exact** (D-3A4.9): inside `decimal.localcontext(Context(prec=200, traps=[Inexact, Rounded,
  InvalidOperation]))`; nothing is quantised; a zero result is normalised with `copy_abs()`. No `float` anywhere.
- **Never across currency, unit or provenance** (D-3A4.3): they are part of the key. Nothing is converted.
- **Budget lines are never summed** (D-3A4.4): a DECLARED key with one record has its value; with two or more,
  `value = None`, `note = "DUPLICATE_DECLARATION"`, `record_count` the number.
- **No record, no line** (D-3A4.5): a heading with no placed record is absent, never 0. A line whose records sum to
  0 is a recorded 0 and is shown.
- `MonthLine` sort: `(MONEY_KINDS.index(kind), [(v is not None, v or "") for _, v in dims], MEASURES.index(measure),
  currency or "", unit or "", PROVENANCE_ORDER.index(provenance))` with `MEASURES = ("AMOUNT", "QUANTITY",
  "DECLARED")` and `PROVENANCE_ORDER = ("observed-financial", "field-integrated", "bench-tested", "source-emulated",
  "demo-simulated")`. Strings compare by code point.

### 3.4 Stamps and "out of date" (D-3A4.6)

- `MonthKey(site_id: UUID | None, period: str)`. `MonthStamp(site_id, period, digest)`.
- `digest = sha256(head + "\n" + "\n".join(sorted(f"{record_id}:{revision_id}" for each placed money revision)))`
  over UTF-8, lower-case hex, with `head = f"{site_id or '-'}|{period}"`. An empty month has the digest of `head +
  "\n"`. The digest depends only on which revisions are placed there, so a new record, a revision, or a record that
  moves in or out each changes it, and nothing else does.
- `stale(tenant_id, stamps) -> tuple[MonthStamp, ...]`: the given stamps whose current digest (`known_at` None)
  differs, in input order.
- `months_touched(tenant_id, intake_id) -> tuple[MonthKey, ...]`: for each money revision the intake wrote, its
  bucket and, when it supersedes one, the superseded revision's bucket; distinct; sorted with `site_id None` first,
  then by `(str(site_id), period)`.
- No table records staleness: a reader keeps its stamp and asks. `3B7a` stores the stamps of what it read.

### 3.5 The service

`commercial/months.py`:

| Name | Holds |
|---|---|
| `MonthLine` | frozen: `kind`, `dims: tuple[tuple[str, str \| None], ...]`, `measure`, `value: Decimal \| None`, `currency`, `unit`, `provenance`, `record_count: int`, `basis` (`RECOGNITION_PERIOD` or `SETTLED_AT`), `source_systems: tuple[str, ...]` (sorted, distinct), `note: str \| None` |
| `Received` | frozen: `source_system`, `provenance`, `record_count` (records placed in the month from that system and origin) |
| `MonthAmounts` | frozen: `tenant_id`, `site_id: UUID \| None`, `period`, `closed: bool` (`clock() >= hi`), `known_at`, `lines: tuple[MonthLine, ...]`, `received: tuple[Received, ...]` (sorted by `(source_system, PROVENANCE_ORDER index)`), `stamp: MonthStamp` |
| `CommercialMonths(store, *, clock)` | `site_month(tenant_id, site_id, period, *, known_at=None) -> MonthAmounts`; `portfolio_month(tenant_id, period, *, known_at=None) -> MonthAmounts` (portfolio-level records only); `months_touched`; `stale` |
| `month_bounds(period, tz)` | §3.2 |

- `site_month` reads `latest_revisions(tenant_id, site_id=site_id, known_at=known_at)` once, keeps money kinds placed
  in `period` (by columns only), and parses only those. `portfolio_month` reads `latest_revisions(tenant_id,
  kind="BUDGET_LINE", recognition_period=period, known_at=known_at)` and keeps `site_id is None`.
- `period` must fullmatch `[0-9]{4}-(0[1-9]|1[0-2])` (ASCII), else `ValueError`. An unknown `site_id` (not in
  `site_zones`) is `LookupError`.
- `commercial/composition.py`: `build_commercial_months(database_url) -> CommercialMonths` with the UTC clock.

No route and no stored figure: `3B7a` serves reads; `4b` and `5a` turn lines into leaves.

## 4. Fixture: `backend/tests/fixtures/commercial_months_kobo.json`

`{"_note": "3A4 spec §4", "steps": [{"at": <instant>, "batch": <canonical batch>}, ...]}`, tenant
`lakeside-power`, currency USD, every record `source_version` `"1"` unless stated, Site `KOBO-001` unless stated,
time zone `Africa/Nairobi`. Each step is ingested with the store clock at `at`.

| Step, `at` | Batch (`source_type`, `source_system`, provenance `source-emulated`) | Records |
|---|---|---|
| A, `2026-11-02T06:00:00+00:00` | `billing_export`, `kobo-vending` | `KOBO-CH-0001` CHARGE: period `2026-10`, effective `2026-10-01` to `2026-11-01`, 120.00, 400 kWh, USAGE, `tariff_code` `T-RES`, no `tariff_class`, `account_ref` `C-0001`. `KOBO-CH-0002` CHARGE: as 0001 but 75.50, 250 kWh, `tariff_class` STANDARD, `C-0002`. `KOBO-CH-0003` CHARGE: 300.00, 1000 kWh, `T-PROD`, PRODUCTIVE, `C-0003`. `KOBO-CH-0004` CHARGE: 10.00, FIXED, no quantity, `T-RES`, `C-0001`. `KOBO-RC-0001` RECEIPT: `2026-10-30T19:00:00+03:00`, period `2026-10`, 100.00, COLLECTED, MOBILE_MONEY, `payer_ref` `C-0001`. `KOBO-RC-0002` RECEIPT: same day, 60.00, PAID_IN_TRANSIT, MOBILE_MONEY, `C-0002` |
| B, same | `mobile_money_statement`, `kobo-mm` | `KOBO-ST-1031` SETTLEMENT: `settled_at` `2026-10-31T22:30:00+00:00` (1 Nov 01:30 in Nairobi), no period, 60.00, `provider` `mobile-money`, `batch_ref` `SB-1031`, `receipts` `["KOBO-RC-0002"]`. `KOBO-ST-1030` SETTLEMENT: `2026-10-30T12:00:00+03:00`, no period, 100.00, `SB-1030`, `["KOBO-RC-0001"]` |
| C, same | `expense_ledger`, `lakeside-accounts` | EXPENSEs, period `2026-10`, occurred `2026-10-14T11:00:00+03:00`, `counterparty_ref` `SUP-X`, `document_ref` = the ID: `KOBO-EX-FUEL-1014` 500.00, 400 L, PAID, FUEL. `KOBO-EX-FUEL-1028` 262.50, 210 L, INVOICED, FUEL. `KOBO-EX-OM-1001` 180.00, PAID, OM. `KOBO-EX-Q-1019` 900.00, QUOTE, REPAIR. `KOBO-EX-STAFF-10` 450.00, PAID, STAFF |
| D, same | `budget_workbook`, `lakeside-budget-2026` | BUDGET_LINEs, period `2026-10`, `version_ref` `budget-2026-v1`: `BUD-2026-10:KOBO-001:diesel_l` `diesel_l` 700. `BUD-2026-10:KOBO-001:diesel_price` `diesel_price` 1.25 USD. `BUD-2026-10:PORTFOLIO:staff`, no Site, `staff` 1200.00 USD |
| E, `2026-11-06T09:00:00+00:00` | `expense_ledger`, `lakeside-accounts` | `KOBO-EX-OM-1029` EXPENSE: period `2026-10`, 95.00, INVOICED, OM (late). `KOBO-EX-FUEL-1028` v`2`: 275.00, 220 L, INVOICED, FUEL (corrected) |
| F, `2026-11-07T09:00:00+00:00` | `billing_export`, `kobo-vending` | `KOBO-CH-0004` v`2`: period `2026-11`, effective `2026-11-01` to `2026-12-01`, 10.00, FIXED (moved to November) |

Read clock `2026-11-20T08:00:00+00:00`.

**Expected (hand-computed; the test writes these literals, W2).** Kobo, `2026-10`, after F (19 lines, all
`source-emulated`; AMOUNT in USD unless a unit is named):

| Kind | dims | Measure, value | Count, basis |
|---|---|---|---|
| CHARGE | USAGE, None | AMOUNT 120.00; QUANTITY 400 kWh | 1 each |
| CHARGE | USAGE, PRODUCTIVE | AMOUNT 300.00; QUANTITY 1000 kWh | 1 each |
| CHARGE | USAGE, STANDARD | AMOUNT 75.50; QUANTITY 250 kWh | 1 each |
| RECEIPT | COLLECTED, MOBILE_MONEY | AMOUNT 100.00 | 1 |
| RECEIPT | PAID_IN_TRANSIT, MOBILE_MONEY | AMOUNT 60.00 | 1 |
| SETTLEMENT | mobile-money | AMOUNT 100.00 | 1, SETTLED_AT |
| EXPENSE | FUEL, INVOICED | AMOUNT 275.00; QUANTITY 220 L | 1 each |
| EXPENSE | FUEL, PAID | AMOUNT 500.00; QUANTITY 400 L | 1 each |
| EXPENSE | OM, INVOICED | AMOUNT 95.00 | 1 |
| EXPENSE | OM, PAID | AMOUNT 180.00 | 1 |
| EXPENSE | REPAIR, QUOTE | AMOUNT 900.00 | 1 |
| EXPENSE | STAFF, PAID | AMOUNT 450.00 | 1 |
| BUDGET_LINE | diesel_l, budget-2026-v1, None | DECLARED 700, no currency, unit None | 1 |
| BUDGET_LINE | diesel_price, budget-2026-v1, None | DECLARED 1.25 USD, unit `MONEY/L` | 1 |

`received`: `kobo-mm` 1, `kobo-vending` 5, `lakeside-accounts` 6, `lakeside-budget-2026` 2. `closed` true.
- Kobo `2026-10` with `known_at = 2026-11-05T00:00:00+00:00`: as above, except a `CHARGE FIXED, None` AMOUNT 10.00
  line (first), `EXPENSE FUEL, INVOICED` 262.50 and 210 L, and no `OM, INVOICED` line (19 lines; `kobo-vending` 6,
  `lakeside-accounts` 5).
- Kobo `2026-11` after F: `CHARGE FIXED, None` AMOUNT 10.00, and `SETTLEMENT mobile-money` 60.00 SETTLED_AT;
  `closed` false. After D only: the settlement line alone.
- Portfolio `2026-10`: `BUDGET_LINE staff, budget-2026-v1, None` DECLARED 1200.00 USD, unit `MONEY`.
- Stamps: take October and November after D (`S10`, `S11`). After E, `stale([S10, S11]) == (S10,)`. After F, with
  October re-stamped after E (`S10e`), `stale([S10e, S11]) == (S10e, S11)`.
- `months_touched`: B is `[(KOBO, 2026-10), (KOBO, 2026-11)]`; D is `[(None, 2026-10), (KOBO, 2026-10)]`; E is
  `[(KOBO, 2026-10)]`; F is `[(KOBO, 2026-10), (KOBO, 2026-11)]`.

## 5. Out of scope

Structure providers and any change to `structure/` (`4b`, `5a`; D-3A4.8); routes and snapshots (`3B7a`); labels
(`3A5`); reconciliation against management accounts (`3A7`); cold-chain and EV kinds (RC5); a staleness table or
trigger (`3B7b`).

## 6. Tests

**No database** (`backend/tests/test_3a4_commercial_months.py`): a subclass `MonthsMemoryStore` of 3A1's
`MemoryCommercialStore` (imported from `test_3a1_commercial_service`, never edited) adds §2's three methods, every
Site in `Africa/Nairobi`; the world is 3A1's `make_world`.
1. The fixture's expected tables of §4, line by line, every field (`value` compared as `Decimal` and as
   `format(value, "f")` text).
2. The `known_at` read, the November reads, the portfolio read, the stamps and `months_touched`, as §4.
3. Settlement placement at the boundary: `KOBO-ST-1031` is in November, never October.
4. Currency apart: a KES OM expense beside the USD one gives a second line.
5. Provenance apart: an `observed-financial` OM PAID expense from `kobo-ledger` gives its own line, after the
   emulated one.
6. Exact: two ADJUSTMENTs of one `reason_code`, `"1000000000000"` and `"0.000000000001"`, sum to
   `"1000000000000.000000000001"`; two of `"5.00"` and `"-5.00"` give a line `0.00` (a recorded zero, not absent).
7. No line without a record: an empty month gives `lines == ()`, `received == ()` and the empty digest; a month with
   only a FUEL expense has no OM line.
8. Budget duplicates: two records of one `(factor_id, version_ref, line_ref)` give `value None`, `note
   "DUPLICATE_DECLARATION"`, `record_count 2`; distinct `line_ref`s give two lines.
9. A non-money kind (`METER_ASSIGNMENT`) in the month changes neither lines nor stamp.
10. `month_bounds` equals 3B3's `month_window`'s first two values for every month of 2026 in `Africa/Nairobi`,
    `UTC` and `America/New_York` (a daylight-saving zone).
11. A bad period is `ValueError`; an unknown Site is `LookupError`.
12. A grep test: no `float(` in `commercial/months.py`; no `structure` import in `commercial/**`.

**Postgres** (pooled, `--db`; `backend/tests/test_3a4_commercial_months_postgres.py`): the fixture ingested through
`PostgresCommercialStore` (Sites inserted with `timezone` `Africa/Nairobi`), then tests 1 to 3 and 6 against it;
`latest_revisions(known_at=...)` against the in-memory store on the same data; `intake_revisions` round-trips;
`site_zones` returns the Sites.

**Regression:** `test_3a1_commercial_service.py`, `test_3a1_commercial_postgres.py`, `test_pg_harness.py`.

Commands as 3A1 §6 with these files; check-all once at the end; `select-tests` before review.

## 7. Done (questions; each can fail)

1. Does each heading of a month sum exactly, in its latest revisions, kept apart by currency, unit and origin?
2. Does a correction that moves a record's month count it once, in the new month, and a late record count in its
   own month?
3. Is a heading with no record absent, never 0, and a recorded zero shown as 0?
4. Are budget lines listed and never summed, with a duplicate declaration giving no value?
5. Does a settlement without a recognition month fall in its Site-local settlement month?
6. Does a month's stamp go stale exactly when a record placed in it, or moved out of it, changes, and is
   `months_touched` right for every fixture step?
7. Does `known_at` give the month as it was known then?
8. Is nothing changed beyond `commercial/store.py`, `commercial/months.py`, `commercial/composition.py`, the
   adapter's three read methods, the fixture, the two test files and the packet?

Packet: `specs/3A4-amounts-by-month/packet.md`, with module paths and the mid-build count.

## 8. Units

| Unit | Content | Commit |
|---|---|---|
| 1 | §2's three store methods (adapter, port, test subclass); the fixture; Postgres tests | 1 |
| 1 | `months.py`, composition; no-database tests; check-all; packet | 2 |

## 9. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | A CHARGE without `tariff_class` is kept apart from STANDARD | Yes; `4b` decides how to read it, with its label |
| Q2 | A record is not flagged "late" by itself; staleness is by stamp | Yes; every October bill is recorded after October closes, so "late" alone says nothing |
| Q3 | A QUOTE expense is listed like any other status | Yes; `4b` counts INVOICED and PAID as cost, never QUOTE |
