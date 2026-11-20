# 5a: targets per factor, declarer recorded (implementer spec)

Status: in_review (unit 1 built; units 2 and 3 wait for `4b1`). Spec rev 2, handshake round 1 answered (`rulings.md` "Handshake answers (round 1)"; D-5A.13 to D-5A.15).
P5 approved by the owner on 20 Nov (`owner/owner-p5-approved-and-defaults-2026-11-20.md`), so D-5A.12 is met: no 5a
code is written before that approval, and unit 1 starts when the handshake has no open question.

Architect (Claude), 2026-11-20. Lane C, on the deep-dive path's critical chain (`5a` → `5b` → `5c`;
`two-week-build-plan.md` §0.1 row 9; D-BW1.8 to D-BW1.12; owner RC1 to RC9 accepted).
- **Structure:** P5 (this folder) rules 1 to 7. P3B: "a target with no line of its own is a labelled assumption"
  (owner, 20 Nov, item 6). Owner: "k of n sites" (`owner/owner-k-of-n-sites-2026-11-20.md`).
- **Builds on (merged; `main` at `5a2ea9974`):** `3B1` (`REGISTRIES`, `FactorRow`), `3B3` (`evaluate`, `compose`, `LeafValue`,
  `Missing`, `SiteStructure`, `PortfolioStructure`, `StructureRead.site`, `site_count`, `SITE_TYPE_TO_STRUCTURE`,
  `NOT_DECLARED`), `3A4` (`CommercialMonths.site_month`, `.portfolio_month`, `MonthLine`, `MonthStamp`,
  `DUPLICATE_DECLARATION`), `3A1` (`CommercialStore.latest_revisions`, `.intake` returning `IntakeSummary | None`, whose
  `.intake.entered_by`/`.intake.entered_at` are read), `2a` (`loads_canonical`, `parse_record`, the BUDGET_LINE body). **And on `4b1`** once merged
  (`FactorRow.stated_by`, `evaluate(..., stated=)` with D-4B.16's blocking row, `LeafValue.origins`,
  `build_commercial_reads`; D-5A.11).
- **Decisions:** `rulings.md` (D-5A.1 to D-5A.15). **Reviewer guide:** `reviewer-guide.md`.

Non-screen. **3 units.** Discovery review (W5): money figures and a new read.

## 0. Before you start

- **Branch** `task/5a-targets` off `main`, worktree `/opt/assetecon/AssetOpsV1-5a`. Unit 1 starts when the handshake
  has no open question (P5 is approved); units 2 and 3 start after `4b1` merges (merge `main` first).
- **Python:** as 3B3 `spec.md` §0.
- **Read:** `rulings.md`; P5; 4b `spec.md` §2 (the seam you build on); 3B3 `spec.md` §2 to §5; 3A4 `spec.md` §3;
  `structure/` (all); `commercial/months.py`; `backend/tests/test_3a4_commercial_months.py:27-115`.
- **Databases:** `*_test` only, through the harness (`tools/heavy-slot.sh --db -- <command>`). Never ports 5490 or
  8990, the walkthrough database or Docker. **No migration.**
- **Collisions.** Your code lives in the new package `structure/targets/`; you edit no existing module. `4b2` (lane
  B) edits `structure/{sources,money,composition}.py`; `3A2` edits `commercial/`. None of those is yours.

## 1. Outcome and why

For a mini-grid Site and a month, the target side of the structure: every factor's target, from the operator's
budget lines, each naming its line and the person who declared it; every factor with no line of its own carrying a
labelled assumption by a stated rule; every target that cannot be set reading "not available yet" with the budget
line that would set it. The portfolio target is composed per factor, "k of n sites". `5b` splits the gap from this
and the actual side; `5c` shows it.

Gate questions (`delivery-plan.md` §3, step 5, the part 5a answers): is Lakeside's October target contribution
2,295.00 to the cent? Is the declarer of each target recorded?

## 2. Unit 1: budget lines (`structure/targets/lines.py`; needs only `main`)

```python
@dataclass(frozen=True)
class TargetLine:
    factor_id: str; value: Decimal; currency: str | None; unit: str | None
    version_ref: str; line_ref: str | None; provenance: str; source_system: str
    revision_id: UUID; intake_id: UUID
    declared_by: str            # the intake's entered_by
    person_id: UUID | None      # from "person:<uuid>", else None
    declared_at: datetime       # the intake's entered_at
    place: str                  # "LEAF" or "NODE"

@dataclass(frozen=True)
class UnusedLine:
    factor_id: str; version_ref: str; line_ref: str | None; reason: str; source_systems: tuple[str, ...]

@dataclass(frozen=True)
class BudgetLines:
    site_id: UUID | None; period: str
    version_ref: str | None     # the governing version; None with no lines or a version problem
    problem: str | None         # "BUDGET_VERSIONS:<a>,<b>" or None
    lines: tuple[TargetLine, ...]          # sorted by factor_id
    blocked: Mapping[str, str]             # factor_id -> note; a factor with a line that cannot be used
    unused: tuple[UnusedLine, ...]         # sorted by (factor_id, version_ref, line_ref or "", reason)
    stamp: MonthStamp

class BudgetLineReader:
    def __init__(self, months: CommercialMonths, store: CommercialStore) -> None
    def site(self, tenant_id: UUID, site_id: UUID, period: str, *, structure_key: str,
             known_at: datetime | None = None) -> BudgetLines
    def portfolio(self, tenant_id: UUID, period: str, *, structure_key: str,
                  known_at: datetime | None = None) -> BudgetLines
```

**Rules, in order** (D-5A.1, D-5A.3, D-5A.4). `amounts` is `months.site_month(...)` (Site) or
`months.portfolio_month(...)` (portfolio); its `BUDGET_LINE` lines are the candidates, `dims` `(factor_id,
version_ref, line_ref)`; `reg = REGISTRIES[structure_key]`.
1. **Versions.** The distinct `version_ref`s of the candidates, sorted. Two or more: `problem =
   "BUDGET_VERSIONS:" + ",".join(versions)`, `version_ref = None`, every candidate unused with reason
   `BUDGET_VERSIONS`, and `blocked[f] = "BUDGET_VERSIONS"` for every candidate whose `f` is a registry row. Stop.
2. **Not a factor.** A candidate whose `factor_id` is not a row of `reg`: unused, `NOT_A_FACTOR`.
3. **One per factor.** For each remaining factor, two or more candidates, or one whose `value` is None (3A4's
   `DUPLICATE_DECLARATION`): all unused with reason `DUPLICATE_DECLARATION`, `blocked[f] =
   "DUPLICATE_DECLARATION"`.
4. **Currency.** A single candidate for a row whose unit has the money dimension and `currency` None: unused and
   blocked `CURRENCY_MISSING`; for a row without it and a currency: unused and blocked `CURRENCY_ON_QUANTITY`.
5. **Used.** Each remaining candidate is a `TargetLine`, `place` `LEAF` if the row is a leaf, else `NODE`.

**Declarer join** (D-5A.2). One read: `store.latest_revisions(tenant_id, site_id=site_id, kind="BUDGET_LINE",
recognition_period=period, known_at=known_at)`; for the portfolio, the same with no `site_id` filter, then keep
`site_id is None`. Parse each revision's `canonical` (`parse_record(loads_canonical(text.encode("utf-8")))`) and key
it by `(factor_id, version_ref, line_ref, currency, provenance)`. Each used line matches exactly one revision (else
`RuntimeError("budget line without its revision")`, a bug). Then `summary = store.intake(tenant_id, rev.intake_id)` once
per distinct intake (`IntakeSummary | None`; `None` raises `RuntimeError("budget line without its intake")`, a bug):
`declared_by = summary.intake.entered_by`, `declared_at = summary.intake.entered_at`, `person_id =
UUID(m.group(1))` when `re.fullmatch(r"person:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
entered_by)` matches, else None. `stamp = amounts.stamp`. No `float`; values are 3A4's Decimals.
The declarer is the intake of the line's latest revision: an unchanged re-upload writes no revision and does not
re-declare (D-5A.14). The reader never reads `amounts.closed`: a target exists for an open or future month (budgets
are declared ahead); an `AT_ACTUAL` target follows the actual side's answer for that month (handshake R5).

## 3. Unit 2: the target rules and the Site read (needs `4b1`)

### 3.1 `structure/targets/rules.py` (literals)

```python
TARGET_KIND, TARGET_FAMILY = "BUDGET_LINE", "COMMERCIAL_RECORD"
TARGET_WORDS = "Budget line for the month"
LEAK_TEXT = "No target line: taken at zero (assumption)"
AT_ACTUAL_TEXT = "No target line: taken at this month's actual, so no gap is put on it (assumption)"
MAIN_TEXT = "No target line: the rest of the heading's target, on its main factor (assumption)"
RULES = ("LEAK_ZERO", "AT_ACTUAL", "MAIN", "OPTION", "CALENDAR")
TARGET_RULE: Mapping[str, Mapping[str, str]]   # structure key -> leaf -> rule
MAIN_OF: Mapping[str, Mapping[str, str]]       # structure key -> MAIN leaf -> its stated heading
```

MINI_GRID, every one of the 31 leaves:

| Rule | Leaves |
|---|---|
| `LEAK_ZERO` | `technical_loss_kwh`, `unexplained_loss_kwh`, `adjustments_kwh`, `unmapped_kwh`, `in_transit`, `outstanding`, `candidate_l`, `unexplained_l`, `reduced_days`, `unserved_critical_kwh`, `customer_hours_interrupted`, `field_visits`, `liability`, `dawn_days_below` |
| `AT_ACTUAL` | `tariff`, `productive_kwh`, `productive_tariff`, `diesel_price`, `wear_rate`, `om`, `staff`, `hours_per_day`, `major_assets`, `standby_kw`, `lost_unit_kw` |
| `MAIN` | `delivered_kwh` (of `revenue`), `necessary_l` (of `fuel_cost`) |
| `OPTION` | `extra_l`, `battery_throughput_kwh`, `collection_cost` |
| `CALENDAR` | `period_days` |

`solve_main(registry, leaves, heading, leaf, target) -> tuple[Decimal | None, str | None]` (D-5A.6): with `leaves`
holding every leaf (the main one is replaced), evaluate three times (no `stated`), the main leaf set to
`LeafValue(Decimal(k), "DECLARED", ("solve",), None, None, <heading currency if the leaf is money, else None>)` for
`k` in 0, 1, 2; `v_k = values[heading].value`. Any `v_k` None: `(None, f"MAIN_FACTOR_UNSOLVED:{heading}")`. `a = v1 −
v0`; `v2 − v1 != a`: `(None, f"MAIN_FACTOR_NONLINEAR:{heading}")`; `a == 0`: `(None,
f"MAIN_FACTOR_ZERO_SLOPE:{heading}")`; else `((target − v0) / a, None)` under `Context(prec=34,
rounding=ROUND_HALF_EVEN)`, not quantised.

### 3.2 `structure/targets/read.py`: `TargetRead.site`

```python
@dataclass(frozen=True)
class TargetCheck:
    factor_id: str; stated: Decimal; computed: Decimal | None; currency: str | None; agrees: bool

@dataclass(frozen=True)
class SiteTargets:
    structure: SiteStructure      # the target side, same key and version as the actual side
    lines: BudgetLines
    checks: tuple[TargetCheck, ...]   # registry order
    currency: str | None          # the Site's target currency

class TargetRead:
    def __init__(self, lines: BudgetLineReader, actual: StructureRead) -> None
    def site(self, site: SiteRef, month: str, known_at: datetime | None = None) -> SiteTargets
    def portfolio(self, tenant_id: UUID, sites: Sequence[SiteRef], month: str,
                  known_at: datetime | None = None) -> PortfolioTargets   # §4
```

`site` (a Site type without a structure raises `StructureError("STRUCTURE_NOT_DECLARED", ...)` as 3B3; a bad month
`ValueError`):
1. `bl = lines.site(site.tenant_id, site.site_id, month, structure_key=key, known_at=known_at)`;
   `act = actual.site(site, month, known_at).values`.
2. `currency` = the one currency among `bl.lines`' non-None currencies; None when there are none or several.
3. Each leaf, in registry order. An *absent target* is `LeafValue(None, "NOT_AVAILABLE", (), None,
   Missing(TARGET_KIND, TARGET_FAMILY, cause, None, (), TARGET_WORDS, None, note), None)`, `cause`
   `NOT_CALCULATED_YET` for a blocked factor (D-5A.13) and `NOT_RECEIVED` otherwise. An *assumption*
   is `LeafValue(value, "ESTIMATED", sources, None, Missing(TARGET_KIND, TARGET_FAMILY, "NOT_RECEIVED",
   "ASSUMPTION", (), TARGET_WORDS, <text>, None), currency)`.
   The bullets apply in this order; the first that matches decides.
   - In `bl.blocked`: absent (`NOT_CALCULATED_YET`), note the blocked note.
   - A `LEAF` line (a `MAIN` leaf with its own line included): `LeafValue(line.value, "DECLARED", (f"budget:{line.revision_id}",), None, None, line.currency,
     (line.provenance,))`.
   - `OPTION`: `LeafValue(row.neutral, "NEUTRAL", ("option-only neutral",), None, None, None)`.
   - `CALENDAR`: the actual leaf's value and evidence, sources `("calendar",)`, no missing, no currency.
   - `LEAK_ZERO`: an assumption of `Decimal("0")`, `LEAK_TEXT`, sources `("assumption:zero",)`; a money row takes
     `currency`, and with `currency` None it is absent, note `TARGET_CURRENCY_UNKNOWN`.
   - `AT_ACTUAL`: `act[leaf].value` None: absent, note `ACTUAL_NOT_AVAILABLE`. Else an assumption of that value,
     `AT_ACTUAL_TEXT`, sources `("assumption:at-actual",)`, currency `act[leaf].currency`.
   - `MAIN` with no line of its own: decided in step 5.
4. Each stated heading (rows with `stated_by`): in `bl.blocked`, absent (`NOT_CALCULATED_YET`, D-5A.13) with that
   note, so 4b1's blocking row keeps the heading absent whatever its expression; a `NODE` line: the
   `LEAF`-line form above (DECLARED); else absent, note None.
5. Each `MAIN` leaf without a line, in registry order: with its heading's stated target absent, absent with
   `MAIN_FACTOR_UNSOLVED:<heading>`; else `solve_main` over the leaves so far (a later main leaf still unset counts
   as absent): a value gives an assumption, `MAIN_TEXT`, sources `(f"assumption:main-factor:{heading}",)`, currency
   as `solve_main`'s; a note gives absent with it.
6. `values = evaluate(reg, leaves, stated)`.
7. `checks`: each `NODE` line whose row has no `stated_by`: `TargetCheck(f, line.value, values[f].value,
   line.currency, agrees = values[f].value is not None and values[f].value == line.value and values[f].currency ==
   line.currency)`.
8. `SiteTargets(SiteStructure(site.site_code, month, key, reg.version, values), bl, checks, currency)`.

## 4. Unit 3: the portfolio and the composition

```python
@dataclass(frozen=True)
class PortfolioTargets:
    structure: PortfolioStructure            # site_count(structure, f) is 3B3's "k of n"
    sites: Mapping[str, SiteTargets]         # by site_code, the MINI_GRID Sites asked, in order
    portfolio_lines: BudgetLines             # operator-level lines, listed, never composed (D-5A.8)
```
`portfolio` makes the same refusals as `StructureRead.portfolio` (another tenant, a repeated Site:
`STRUCTURE_COMPOSE`; a bad month: `ValueError`), reads `site()` for each MINI_GRID Site, composes with `compose`,
sets `sites_excluded` for the other types to `NOT_DECLARED`, and reads `portfolio_lines = lines.portfolio(...)`.

`structure/targets/composition.py`: `build_target_read(database_url) -> TargetReadService(read: TargetRead, dispose)`
from `build_structure_read(database_url)` (the actual side, whatever `main` wires) and `build_commercial_reads(
database_url)`; `dispose` disposes both; a failure in the second disposes the first.

## 5. Fixture: `backend/tests/fixtures/targets_lakeside.json` (hand-computed; tests write the literals, W2)

`{"_note": "5a spec §5; Kisiwa's contribution line -60.00 is a deliberate disagreement with the computed -65.00 (the pack's plan), so the check reads False; do not correct it", "steps": [{"at": ..., "entered_by": ..., "batch": ...}]}`. Tenant `lakeside-power`, USD,
every Site in `Africa/Nairobi`, `recognition_period` `2026-10`, `source_version` `"1"`.

| Step, `at`, `entered_by` | Batch | Records |
|---|---|---|
| 1, `2026-11-06T09:00:00+00:00`, `loader:ds3` | DS1b's `lakeside-power.budget_workbook` envelope (`assetops-world-generator`, `source-emulated`) | Its October `plan` records only, verbatim: Kobo `om` 600.00, `staff` 500.00; Kisiwa `om` 700.00, `staff` 500.00; Mto `om` 500.00, `staff` 450.00 (IDs `gen:<SITE>:2026-10:plan:<leaf>`) |
| 2, `2026-11-07T09:00:00+00:00`, `person:5a000000-0000-4000-8000-000000000001` | `budget_workbook`, `lakeside-budget-2026`, `source-emulated`, `produced_at` `2026-11-07T09:00:00+03:00` | BUDGET_LINEs, `version_ref` `budget-2026-v1`, `currency` USD, `line_ref` = the factor, IDs `BUD-2026-10:<SITE>:<factor>`: KOBO-001 `revenue` 3420.00, `fuel_cost` 875.00, `contribution` 1445.00, `diesel_cost` 875.00; KISIWA-001 `revenue` 4125.00, `fuel_cost` 2990.00, `contribution` -60.00; MTO-001 `revenue` 2240.00, `fuel_cost` 375.00, `contribution` 915.00; no Site, ID `BUD-2026-10:PORTFOLIO:staff`, `staff` 1200.00 |

**The actual side** is `StructureRead(FakeActual())`: October, per Site: `om` (Kobo 600.00, Mto 500.00; Kisiwa
absent `NOT_RECEIVED`) and `staff` (500.00, 500.00, 450.00) `RECORDED` USD; `diesel_price` 1.25, 1.30, 1.25 as 3B3's
ASSUMED form (`ESTIMATED`, `carried_as` ASSUMPTION, USD); `productive_kwh` 0 `RECORDED`; `period_days` 31 `DERIVED`;
the OPTION_ONLY leaves their neutral; every other leaf absent, `NOT_CONNECTED`, with its `filled_by`. Read clock
`2026-11-20T08:00:00+00:00`.

**Expected, Kobo `2026-10`.** `lines`: `contribution`, `fuel_cost`, `om`, `revenue`, `staff`; `unused`:
`diesel_cost` `NOT_A_FACTOR`; `version_ref` `budget-2026-v1`; `currency` USD. `om`'s line: `declared_by`
`loader:ds3`, `person_id` None, `declared_at` `2026-11-06T09:00:00+00:00`; `revenue`'s: `person_id`
`5a000000-0000-4000-8000-000000000001`, `declared_at` `2026-11-07T09:00:00+00:00`.

| Factor | Target | Evidence | Assumed leaves or note |
|---|---|---|---|
| `revenue` (stated) | 3420.00 | DECLARED | `detail_missing == ("delivered_kwh", "productive_tariff", "tariff")` |
| `fuel_cost` (stated) | 875.00, `computed` 875.00 | DECLARED | `detail_missing == ()` |
| `om`, `staff` | 600.00, 500.00 | DECLARED | sources `budget:<revision id>` |
| `necessary_l` (MAIN) | 700 | ESTIMATED | `MAIN_TEXT` |
| `diesel_l` | 700 | ESTIMATED | `("candidate_l", "necessary_l", "unexplained_l")` |
| `in_transit`, `outstanding` | 0 USD | ESTIMATED | `LEAK_TEXT` |
| `collected` | 3420.00 | ESTIMATED | `("in_transit", "outstanding")` |
| `cost_to_serve` | 1975.00 | DECLARED | `()` |
| `contribution` | 1445.00 | DECLARED | `()`; origins `("source-emulated",)` |
| `tariff` | none | NOT_AVAILABLE | note `ACTUAL_NOT_AVAILABLE` (never 0) |
| `delivered_kwh` (MAIN) | none | NOT_AVAILABLE | note `MAIN_FACTOR_UNSOLVED:revenue` |
| `diesel_price` | 1.25 | ESTIMATED | `AT_ACTUAL_TEXT`, USD |
| `productive_kwh` | 0 | ESTIMATED | `AT_ACTUAL_TEXT`, sources `("assumption:at-actual",)`, currency None (the actual is RECORDED) |
| `period_days` | 31 | DERIVED | none |

`checks == (TargetCheck("contribution", 1445.00, 1445.00, "USD", True),)`.

**Expected, Kisiwa and Mto.** Kisiwa: revenue 4125.00, fuel_cost 2990.00, om 700.00 (its own line, though the
actual is absent), staff 500.00, `necessary_l` 2300, cost_to_serve 4190.00, contribution −65.00 DECLARED;
`checks == (TargetCheck("contribution", Decimal("-60.00"), Decimal("-65.00"), "USD", False),)`. Mto: revenue
2240.00, fuel_cost 375.00, om 500.00, staff 450.00, `necessary_l` 300, cost_to_serve 1325.00, contribution 915.00;
its check agrees.

**Expected, portfolio** (Kobo, Kisiwa, Mto): `contribution` 2295.00, 3 of 3, DECLARED; `revenue` 9785.00;
`fuel_cost` 4240.00; `om` 1800.00; `staff` 1450.00 (not 2650.00: the operator-level line is only in
`portfolio_lines`); `cost_to_serve` 7490.00; `diesel_l` and `necessary_l` 3300; `collected` 9785.00 ESTIMATED.
`portfolio_lines.lines` holds one line, `staff` 1200.00, `person_id` the step-2 person. These equal the pack's
`portfolio.lakeside-power.plan.sums` for those factors (test 6 reads the file).

## 6. Tests (written first)

**No database** (`backend/tests/test_5a_targets.py`; the world is 3A4's `new_world`, imported, never edited):
1. *(unit 1)* (a) §5's Kobo `BudgetLines` field by field: lines, declarers, unused, version, `stamp ==
   site_month's`. (b) Re-ingest step 1's batch unchanged at `2026-11-08T09:00:00+00:00` with `entered_by`
   `person:5a000000-0000-4000-8000-000000000002`: Kobo `om`'s line still has `declared_by` `loader:ds3`, `person_id`
   None, `declared_at` `2026-11-06T09:00:00+00:00` (D-5A.14).
2. *(unit 1)* Rules 1 to 4 of §2, one case each: (a) a step 3 at `2026-11-08T09:00:00+00:00` adding
   `BUD-2026-10:MTO-001:revenue-v2` (`version_ref` `budget-2026-v2`, `revenue` 2300.00): Mto `problem ==
   "BUDGET_VERSIONS:budget-2026-v1,budget-2026-v2"`, `lines == ()`, `blocked` = `om`, `staff`, `revenue`,
   `fuel_cost`, `contribution` each `BUDGET_VERSIONS`; (b) `BUD-2026-10:KOBO-001:om-extra` (`om` 50.00, `line_ref`
   `om-extra`): Kobo `blocked == {"om": "DUPLICATE_DECLARATION"}`; (c) a `revenue` line without currency: blocked
   `CURRENCY_MISSING`; (d) the portfolio read: one line, `staff`.
3. *(unit 2)* (a) §5's Kobo, Kisiwa and Mto tables, every named field (values as `Decimal`; sums also as
   `format(v, "f")`), and the `Missing` of every absent and assumed target field by field. (b) A cost at its actual
   (D-5A.15): the §5 world without `gen:MTO-001:2026-10:plan:staff`: Mto `staff` 450.00 `ESTIMATED`,
   `AT_ACTUAL_TEXT`, sources `("assumption:at-actual",)`, USD; `cost_to_serve` 1325.00 and `contribution` 915.00,
   both `ESTIMATED`; Mto's check still agrees.
4. *(unit 2)* The rules: `TARGET_RULE["MINI_GRID"]` and `MAIN_OF` equal the test's own literals (W2) and cover the 31
   leaves exactly; `OPTION` is exactly the OPTION_ONLY rows, `CALENDAR` exactly NEVER_EMPTY; each MAIN heading has
   `stated_by` and the heading is in `blocks_of(reg, (leaf,))`.
5. *(unit 2)* The main solve: (a) `FakeActual` with `tariff` 0.40 and `productive_tariff` 0.30 (ASSUMED, USD): Kobo
   `delivered_kwh` target 8550, ESTIMATED, and `revenue.computed == 3420.00`; (b) a planted two-leaf registry
   (`x` KWH, `p` MONEY/KWH, `y = x * x * p`, `stated_by` set, built without `check`): `MAIN_FACTOR_NONLINEAR:y`;
   (c) the same with `y = x * p` and `p` 0: `MAIN_FACTOR_ZERO_SLOPE:y`.
6. *(unit 3)* §5's portfolio, with `site_count` per factor, and the pack comparison (read
   `derived-values.json`, compare to the cent).
7. *(unit 3)* "k of n" with a gap: with 2(a)'s step 3, `contribution` 1380.00, 2 of 3, out `(("MTO-001",
   ("delivered_kwh", "fuel_cost", "necessary_l", "om", "productive_tariff", "revenue", "staff", "tariff")),)`.
8. *(unit 3)* Unknown is never zero: with 2(b), Kobo `om` target absent (`DUPLICATE_DECLARATION`, no assumption) and
   Kobo `contribution` absent with `missing_leaves == ("om",)`; with Kobo's actual `diesel_price` absent, `necessary_l`
   absent `MAIN_FACTOR_UNSOLVED:fuel_cost` and `fuel_cost` still 875.00. (c) A blocked heading stays absent
   (D-5A.13): with `FakeActual`'s `tariff` 0.40 and `productive_tariff` 0.30 (as 5(a)) and a step adding
   `BUD-2026-10:KOBO-001:delivered_kwh` (`delivered_kwh` 8550, no currency, `budget-2026-v1`, `line_ref`
   `delivered_kwh`): control, Kobo `revenue` 3420.00 with `computed` not None (the expression has a value); then
   adding `BUD-2026-10:KOBO-001:revenue-extra` (`revenue` 100.00 USD, `line_ref` `revenue-extra`): `revenue` has no
   target, `missing.cause == "NOT_CALCULATED_YET"`, note `DUPLICATE_DECLARATION`, `computed` None.
9. *(unit 3)* `known_at = 2026-11-06T12:00:00+00:00` (after step 1, before step 2): Kobo has `om` and `staff` lines
   only, `revenue` and `fuel_cost` absent, contribution absent.
10. *(unit 1)* DS1b parity: step 1's records equal, as parsed objects, those `build_records(view,
    generate_history(view))` writes for those IDs.
11. Grep: no `float(` under `structure/targets/`; `structure/targets/` edits no other module (the packet lists files).

**Postgres** (pooled, `--db`; `backend/tests/test_5a_targets_postgres.py`; Sites by 3A4's `NairobiSeeder`):
1. §5 through `PostgresCommercialStore`, `TargetRead(BudgetLineReader(months, store), StructureRead(FakeActual()))`:
   tests 1, 3 and 6 against it.
2. `build_target_read(url).read.site(kobo, "2026-10")`: `contribution` 1445.00 DECLARED; `dispose()` runs.

**Regression:** `test_4b1_stated_nodes.py`, `test_3b3_structure_evaluate.py`, `test_3a4_commercial_months.py`.
Commands as 3B3 §6 with these files; check-all once at the end; `select-tests` before review.

## 7. Done (questions; each can fail)

1. Is Lakeside's October target contribution 2,295.00 to the cent, 3 of 3 sites, and each Site's as §5?
2. Does every used target name its budget line and its declarer, and say when no person declared it?
3. Is every target without a line of its own a labelled assumption by its literal rule, *Estimated*, with its
   words, and never presented as declared?
4. Is every target that cannot be set "not available" with the budget line that would set it, never 0, and are two
   versions or two lines for one factor never picked or summed?
5. Is a stated heading's target *Declared* whatever is assumed below it, and is a budget contribution that disagrees
   shown as a check, never used instead?
6. Does the portfolio name every Site left out per factor, and keep operator-level lines out of the totals?
7. Is the main factor solved only for a linear heading with a slope, through the evaluator?
8. Is nothing changed outside `structure/targets/` (new), the fixture, the two test files and the packet?

Packet: `specs/5a-targets/packet.md`, with module paths, the mid-build count, and P5's approval reference.

## 8. Out of scope

The gap and its split, and carrying a missing actual at its target (`5b`); the screen and its words (`5c`); the
Assure relabel (`5d`); choosing between budget versions and entering a target on screen (P5 questions; queue Q1,
Q2); objectives as factor targets (queue Q4); snapshots and routes (`3B7a`); reconciliation (`3A7`); cold-chain and
EV targets (RC5).

## 9. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 1 | §2 `lines.py`; fixture; tests 1, 2, 10 | `main`, P5 approved (met) | 1 |
| 2 | §3 `rules.py`, `read.py` (`site`); tests 3 to 5 | `4b1` merged | 1 |
| 3 | §4 `portfolio`, composition; tests 6 to 9, 11; Postgres; check-all; packet | unit 2 | 1 |

## 10. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner, P5) | Two budget versions in one month | No target for the headings they cover until one is chosen; the analyst loads one; an "adopt this budget" command next fortnight |
| Q2 (owner, P5) | A target typed on screen by the site manager or finance lead | Through the budget file this fortnight; on screen after `5c` |
| Q3 | Two lines for one additive factor (e.g. O&M contract and O&M spares) | Not summed: no target (D-5A.3); summing by line for `SUM` rows can follow |
| Q4 | "Objectives become factor targets" (`delivery-plan.md` §2 row `5a`) | Not this fortnight: the deep-dive's targets are the operator's budget |
| Q5 | A price target with no line is taken at the actual | Yes (D-5A.5): no price gap is claimed without a stated price |
| Q6 | A person re-accepting an unchanged budget becomes its declarer | Not this fortnight (D-5A.14): the declarer is the intake of the latest revision; needs a 3A1 read of intakes that carried a record unchanged |
| Q7 (owner) | A cost with no budget line (O&M, staff) | Taken at this month's actual, labelled; the headings above it read *Estimated* (D-5A.15). Alternative: no target, which removes the Site's contribution target |
