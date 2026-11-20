# 5b: attribution, the gap explained by its drivers (implementer spec)

Status: rev 2, handshake round 1 answered (`rulings.md` "Handshake answers (round 1)", D-5B.11 to D-5B.14).
Architect (Claude), 2026-11-20. Lane B, on the deep-dive path's critical chain (`5a` → `5b` → `5c`;
`two-week-build-plan.md` §0.1 row 11; D-BW1.8, D-BW1.10). **3.25 units** (rev 1: 3; +0.25 for the SUM-only rule,
`carried`, the pinned instant and the tolerance). Discovery review (W5):
money figures and a new mechanism.
- **Structure:** P5 rules 3, 4, 6, 7 and 8 (`specs/5a-targets/structure-page-P5.md`, approved 20 Nov): "the gap is
  split, never invented. Sums split exactly; a product (price times volume) splits by a declared rule; a residual
  appears only beside a factor that is not observed. A missing actual line is carried at its own target only where
  one exists, *Estimated*, naming the missing record." Attribution rules AR1 and AR2 and vectors AT-1 to AT-3
  (`economic-metric-and-effect-contracts.md` §4.2). Structure specification §3 rule 3 (lines carried at target).
- **Owner rules kept:** unknown is never zero; the weakest part sets the label; a target with no line is a labelled
  assumption (5a); "k of n sites" (`owner/owner-k-of-n-sites-2026-11-20.md`); origins, `unknown` weakest (D-4B.18,
  D-5A.16).
- **Builds on (merged; `main` at `8fddb2bba`):** `3B3` (`evaluate`, `compose`, `FactorValue`, `LeafValue`, `Missing`,
  `SiteStructure`, `weakest`, `ORIGIN_ORDER`, `blocks_of`, `site_count`, `NOT_DECLARED`, `SITE_TYPE_TO_STRUCTURE`),
  `4b` (`CommercialLeafSource`, stated nodes, `computed`, `detail_missing`, `origins`, D-4B.8: "`5b` applies it"),
  `5a` (`TargetRead`, `SiteTargets`, `PortfolioTargets`, `TargetCheck`, `BudgetLineReader`), `3B1` (`REGISTRIES`,
  `FactorRow.home`, `parsed`), and the seam `SiteInputs` / `StructureRead.site_inputs` / `evaluate_inputs` (3B7a spec
  §2.1, D-3B7A.7).
- **Decisions:** `rulings.md` (D-5B.1 to D-5B.14). **Reviewer guide:** `reviewer-guide.md`.

## 0. Before you start

- **Branch** `task/5b-attribution` off `main`, worktree `/opt/assetecon/AssetOpsV1-5b`. Start when the handshake has
  no open question. Unit 1 needs only `main`. **Unit 2 starts only after 3B7a unit 0 (the seam) is merged to
  `main`**; merge `main` into this branch then (D-3B7A.10).
- **Read:** `rulings.md`; P5; 5a `spec.md` §3 and §5 and its `rulings.md` D-5A.13 to D-5A.16; 4b `spec.md` §3 and
  §4.1; 3B3 `spec.md` §2; 3B7a `spec.md` §2.1; `structure/evaluate.py`, `structure/expressions.py`,
  `structure/registry.py`, `structure/targets/read.py`; `backend/tests/test_4b_money_leaves.py:77-140`,
  `backend/tests/test_5a_targets.py:36-60` and `:595-610` (`_toy`).
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- <command>`. Never ports 5490 or 8990, the
  walkthrough database or Docker. **No migration.**
- **Collisions.** Your code lives in the new package `structure/attribution/`. You never write the seam (3B7a spec
  §2.1): 3B7a unit 0 does, alone, and this branch has no diff in `structure/read.py`. No other existing module is
  edited.

## 1. Outcome and why

For a mini-grid Site and a month, and for the portfolio: the gap between the actual and the target, explained factor
by factor. Each row gives the factor, its target, its actual, the gap in its own unit, its effect on contribution in
money, its evidence word, its origins and its heading (home category). Sums split exactly; a price-times-volume
splits into a volume effect at target price and a price effect at actual volume; the split goes as far down as both
sides are observed and stops, saying why, where they are not. A missing cost line is carried at its own budget line,
*Estimated*, naming the missing invoice. Cash is a second tree beside it. `5c` shows this on the one screen.

Gate questions (`delivery-plan.md` §3, step 5): is Lakeside's October contribution 1,443.00 against 2,295.00, gap
−852.00, to the cent? Does Kobo's −562.00 split into revenue +38.00 and fuel cost −600.00 from records alone? Is
Kisiwa's O&M *Estimated*, never zero? Does Kisiwa's budget contribution line (−60.00) stay visible beside the computed
target (−65.00)?

## 2. Unit 1: the split rules (`structure/attribution/rules.py`, `bridge.py`; pure; needs only `main`)

### 2.1 Literals (`rules.py`)

```python
BRIDGE_ROOTS: Mapping[str, tuple[str, ...]] = {"MINI_GRID": ("contribution", "collected")}  # outcome first, cash second
KINDS = ("ROOT", "TERM", "VOLUME", "PRICE", "RESIDUAL")
SPLITS = ("SPLIT", "LEAF", "NOT_SPLIT")
GAP_NOT_AVAILABLE, DETAIL_NOT_AVAILABLE = "GAP_NOT_AVAILABLE", "DETAIL_NOT_AVAILABLE"
RECORD_AND_FACTORS_DIFFER, RULE_NOT_DECLARED = "RECORD_AND_FACTORS_DIFFER", "RULE_NOT_DECLARED"
PRICE_NOT_DECLARED, SPLIT_INEXACT = "PRICE_NOT_DECLARED", "SPLIT_INEXACT"
CURRENCY_MISMATCH = "CURRENCY_MISMATCH:"          # + sorted currencies, comma-joined
UNPLACED = "UNPLACED"                              # by_home key for a row whose factor has no home
SOLVE_TOLERANCE = Decimal("1E-12")                 # D-5B.14: agreement in steps 4 and 6; never a quantum
```
Two values *agree* when `abs(x − y) <= SOLVE_TOLERANCE` (helper `agree(x, y) -> bool` in `rules.py`).

### 2.2 The row (`bridge.py`)

```python
@dataclass(frozen=True)
class BridgeRow:
    factor_id: str | None          # None only for RESIDUAL
    parent: str | None             # the factor this row splits; None for ROOT
    kind: str                      # KINDS
    rule: str | None               # "AR1" (TERM, RESIDUAL), "AR2" (VOLUME, PRICE), None (ROOT)
    home: str | None               # the factor's home category (RESIDUAL: the parent's); None when the row has none
    actual: Decimal | None; target: Decimal | None    # the factor's own values (None for RESIDUAL)
    gap: Decimal | None            # actual − target, in the factor's unit; None when either is None, and for RESIDUAL
    scale: Decimal | None          # money on the root per unit of gap; None for RESIDUAL
    effect: Decimal | None         # scale × gap; RESIDUAL: the remainder; None only when gap is None (not RESIDUAL)
    currency: str | None           # the root's currency (every effect is in it)
    evidence: str                  # §2.4; NOT_AVAILABLE when effect is None
    origins: tuple[str, ...]       # §2.4, in ORIGIN_ORDER
    carried: bool                  # a leaf whose actual is carried at its target (missing.carried_as == "TARGET")
    split: str                     # SPLITS
    reason: str | None             # None unless NOT_SPLIT
    unobserved_actual: tuple[str, ...]   # §2.3 step 6: the inputs (leaves, or stated nodes whose record is
    unobserved_target: tuple[str, ...]   # missing) that would fill this side; sorted as the side gives them
    rows: tuple["BridgeRow", ...]  # the split, in expression order; RESIDUAL last

def bridge(registry: Registry, actual: Mapping[str, FactorValue], target: Mapping[str, FactorValue],
           root: str) -> BridgeRow
def by_home(row: BridgeRow) -> Mapping[str, Decimal]
def lowest(row: BridgeRow) -> tuple[BridgeRow, ...]   # depth-first: rows with split LEAF or NOT_SPLIT, and RESIDUALs
```
All arithmetic under `Context(prec=34, rounding=ROUND_HALF_EVEN)`; nothing quantised; a zero `gap` or `effect` is
`copy_abs()`-normalised (never `-0`). No `float`.

### 2.3 The rules (D-5B.2 to D-5B.5), applied from the root down

The root row: `kind` ROOT, `scale` `Decimal(1)`. For every row of factor `f` with `scale` `m`, `a = actual[f]`,
`t = target[f]`:
1. **Gap.** `a.value` or `t.value` None: `gap`, `effect` None, `NOT_SPLIT`, `GAP_NOT_AVAILABLE`. If the row's unit
   has the money dimension and `a.currency != t.currency`: the same, reason `CURRENCY_MISMATCH:` + the sorted non-None
   currencies. Else `gap = a.value − t.value`, `effect = m × gap`.
2. **Leaf.** `f` a leaf: `LEAF`.
3. **Shape.** Flatten the node's parsed expression into signed terms: `Bin("+")` and `Bin("-")` and `Neg` at the top
   give `(±1, term)`; a term is a `Ref` or `Bin("*", Ref, Ref)`. Any other shape (a `Num`, `Call`, `/`, a product of
   more than two factors or of a non-`Ref`): `NOT_SPLIT`, `RULE_NOT_DECLARED`. In a product, the *price* is the
   factor whose unit has `("MONEY", 1)` and is not `is_money`, the *quantity* the other; none or both:
   `NOT_SPLIT`, `PRICE_NOT_DECLARED`.
4. **A record that its factors do not explain.** For each side whose `stated` is True with `computed` not None and
   `not agree(computed, value)`: `NOT_SPLIT`, `RECORD_AND_FACTORS_DIFFER` (5c shows both figures). A solved target
   (5a's 34-digit quotient) agrees with its record (D-5B.14).
5. **Terms.** A term is *neutral* when any of its factors has evidence `NEUTRAL` on both sides: it gives no row (an
   option-only factor; it cannot move outside an option, D-5B.5). A term is *computable* when every factor in it has a
   value on both sides. For a computable term with sign `s`:
   - `Ref g`: a TERM row of `g`, AR1, `scale = m × s`.
   - `q × p`: a VOLUME row of `q`, AR2, `scale = m × s × t[p].value` (target price), then a PRICE row of `p`, AR2,
     `scale = m × s × a[q].value` (actual volume). Volume first, always (AT-3).
   Each child row is built by these same rules (it splits further if it is a node).
6. **The split.** All terms neutral or computable: `SPLIT`, children as step 5; if `not agree(Σ child effects,
   effect)`, `NOT_SPLIT`, `SPLIT_INEXACT` with no children. Otherwise (some term not computable; possible only for a stated
   node): with at least one computable non-neutral term, `SPLIT` with those children and one RESIDUAL row last
   (`effect` = the row's `effect` − Σ children), else `NOT_SPLIT`, `DETAIL_NOT_AVAILABLE` with no children.
   `unobserved_actual` / `unobserved_target`: for `GAP_NOT_AVAILABLE`, the side's `missing_leaves`; for
   `DETAIL_NOT_AVAILABLE` and the RESIDUAL row, the side's `detail_missing` when that side is stated, else `()`;
   otherwise `()`.

### 2.4 Labels and headings (D-5B.6, D-5B.8)

`evidence` is `weakest(...)` and `origins` the union in `ORIGIN_ORDER` over the values the amount rests on: ROOT and
TERM `a, t`; VOLUME `a[q], t[q], t[p]`; PRICE `a[p], t[p], a[q]`; RESIDUAL the parent's `a, t`. `home` is
`registry.row(f).home.category` (None when `home` is None). `by_home(root)`: the effects of `lowest(root)` with an
effect, summed per home (RESIDUAL: its parent's; None: `UNPLACED`), keys in `CATEGORIES` order then `ABOVE`,
`CALENDAR`, `UNPLACED`; empty when the root's effect is None. Σ `by_home` equals the root's effect.

## 3. Unit 2: carrying a missing cost at its target, and the Site bridge (`carry.py`, `site.py`; needs the seam)

### 3.1 `carry.py` (D-5B.7)

```python
CARRY_AT_TARGET: Mapping[str, tuple[str, ...]] = {"MINI_GRID": ("om", "staff")}
CARRIED_TEXT = "Not received: taken at its budget line for the month (estimate)"
NO_TARGET_LINE = "NO_TARGET_LINE"

@dataclass(frozen=True)
class Carried:
    inputs: SiteInputs                     # the actual inputs with the carried leaves replaced
    carried: tuple[str, ...]               # registry order
    not_carried: Mapping[str, str]         # leaf -> reason, registry order

def carry_at_target(inputs: SiteInputs, target: Mapping[str, FactorValue]) -> Carried
```
For each leaf `f` of `CARRY_AT_TARGET[key]` whose actual input `x` has no value, judged in this order:
1. `x.missing.cause` is `NOT_CONNECTED` or `NOT_CALCULATED_YET`: not carried, reason the cause.
2. `x.missing.note` not None (e.g. `MONTH_OPEN`): not carried, reason the note.
3. The target `t = target[f]` has no value, or evidence not `DECLARED`, or a source not starting `"budget:"`: not
   carried, `NO_TARGET_LINE` (an assumed target is never carried: that would be an assumption standing in for a
   record).
4. Carried: `LeafValue(t.value, "ESTIMATED", tuple(f"target:{s}" for s in t.sources), None, Missing(
   x.missing.record_kind, x.missing.source_family, "NOT_RECEIVED", "TARGET", (), x.missing.record_words,
   CARRIED_TEXT, None), t.currency, t.origins)`.
Leaves with a value, leaves outside the list, and every stated heading are left exactly as given (D-5B.7: a heading
is never carried). `inputs.stated` is unchanged.

### 3.2 `site.py`: the Site bridge

```python
@dataclass(frozen=True)
class SiteBridge:
    site_code: str; month: str; structure_key: str; structure_version: int
    roots: Mapping[str, BridgeRow]        # BRIDGE_ROOTS order: "contribution", then "collected"
    by_home: Mapping[str, Decimal]        # by_home(roots["contribution"])
    carried: tuple[str, ...]; not_carried: Mapping[str, str]
    actual: SiteStructure                 # evaluate_inputs(carried.inputs): the actual side the bridge used
    targets: SiteTargets                  # as given; its `checks` are 5a's, never used as a target (D-5B.1)

def site_bridge(inputs: SiteInputs, targets: SiteTargets) -> SiteBridge
```
`inputs` and `targets.structure` must share `structure_key` and `structure_version` and the month, else
`StructureError("STRUCTURE_COMPOSE", key, site_code)`. Then `c = carry_at_target(inputs, targets.structure.values)`,
`actual = evaluate_inputs(c.inputs)`, and for each root `bridge(reg, actual.values, targets.structure.values, root)`.

## 4. Unit 3: the portfolio, the read and its wiring (`portfolio.py`, `read.py`, `composition.py`)

### 4.1 `portfolio.py` (D-5B.9)

```python
@dataclass(frozen=True)
class PortfolioRow:
    key: str                     # the factor id; "residual:<parent>" for residual rows
    kind: str                    # the Sites' row kind (ROOT, TERM, VOLUME, PRICE, RESIDUAL)
    actual: Decimal | None; target: Decimal | None; gap: Decimal | None   # sums, only when the factor's row has
                                 # composes == "SUM" (D-5B.11); else None; None for RESIDUAL
    effect: Decimal | None       # sum (always: money on the root); None only on a currency mismatch
    currency: str | None; note: str | None     # note: "CURRENCY_MISMATCH:<a>,<b>" or None
    evidence: str; origins: tuple[str, ...]
    k: int; n: int
    out: tuple[tuple[str, tuple[str, ...]], ...]   # Sites not in k, in `asked` order, with their reasons
    carried: tuple[str, ...]     # included Sites (asked order) whose own row rests on a carried leaf: the row's
                                 # `carried`, or any descendant's (D-5B.12)

@dataclass(frozen=True)
class PortfolioBridge:
    month: str; structure_key: str; structure_version: int
    asked: tuple[str, ...]                          # every Site code asked, in order
    sites: Mapping[str, SiteBridge]                 # the MINI_GRID Sites, in `asked` order
    rows: Mapping[str, Mapping[str, PortfolioRow]]  # root -> key -> row, keys in first-seen depth-first order
    by_home: Mapping[str, Decimal]                  # Σ of the included Sites' by_home, same key order
    disagreements: tuple[tuple[str, TargetCheck], ...]   # every check with agrees False, `asked` order
    portfolio_lines: BudgetLines                    # operator-level lines, listed, never added (D-5A.8)

def portfolio_bridge(sites: Mapping[str, SiteBridge], asked: Sequence[str],
                     sites_excluded: Mapping[str, tuple[str, ...]], portfolio_lines: BudgetLines,
                     month: str, structure_key: str, structure_version: int) -> PortfolioBridge
```
For each root and each key seen in any Site's tree (a key repeated within one Site's tree under one root raises
`ValueError("REPEATED_FACTOR:<factor_id>")`): the *included* Sites are those whose tree has that row with an effect.
`effect` is the sum over the included Sites only; `actual`, `target` and `gap` are too when the key's factor has
`composes == "SUM"`, else None (D-5B.11: a price or a rate never adds). A total is never one set minus another
(D-5B.9). `k` = included count, `n = len(asked)`. Each Site not included is in `out` with: its
`sites_excluded` reasons (another type: `("STRUCTURE_NOT_DECLARED",)`); else, when its root has no effect,
`tuple(f"actual:{l}" for l in root.unobserved_actual) + tuple(f"target:{l}" for l in root.unobserved_target)`; else
`("NOT_SPLIT",)` (its figure is not split this far). Two or more currencies among the included: sums and effect None,
`note` `CURRENCY_MISMATCH:` + sorted currencies. `evidence` is the weakest and `origins` the union over the included
rows. `by_home` sums over the Sites included in the `contribution` root.

### 4.2 `read.py` and `composition.py`

```python
class BridgeRead:
    def __init__(self, actual: StructureRead, targets: TargetRead, clock: Callable[[], datetime]) -> None
    def site(self, site: SiteRef, month: str, known_at: datetime | None = None) -> SiteBridge
    def portfolio(self, tenant_id: UUID, sites: Sequence[SiteRef], month: str,
                  known_at: datetime | None = None) -> PortfolioBridge
```
Each call first pins `k = known_at if known_at is not None else clock()` (UTC), once, and passes `k` to every read
below (D-5B.13). `site`: `site_bridge(actual.site_inputs(site, month, k), targets.site(site, month, k))`.
`portfolio`: `pt = targets.portfolio(tenant_id, sites, month, k)` (its refusals are the read's), then `site_bridge(
actual.site_inputs(s, month, k), pt.sites[s.site_code])` for each MINI_GRID Site, then `portfolio_bridge(...,
pt.structure.composition.sites_excluded, pt.portfolio_lines, ...)`. From a snapshot, `5c` calls `site_bridge(
snap.inputs, snap.targets)` and `portfolio_bridge` on the snapshot's Sites (3B7a D-3B7A.4): the same functions.

`build_bridge_read(database_url) -> BridgeReadService(read, dispose)`: `actual = build_structure_read(url)`; `reads =
build_commercial_reads(url)`; `BridgeRead(actual.read, TargetRead(BudgetLineReader(reads.months, reads.store),
actual.read), _utc_now)`; a failure in the second disposes the first; `dispose` disposes both. `composition.py` is
the one module under `structure/attribution/` that may import `commercial` (wiring; handshake R6).

**What a screen shows (D-5B.12; `5c` inherits).** A month's money for a structure is shown from these rows only: a
Site's from `SiteBridge.roots`, the portfolio's from `PortfolioBridge.rows`, each with its "k of n", its `out` and its
`carried` Sites. `StructureRead.portfolio`, `TargetRead.portfolio(...).structure` and 3B7a's
`PortfolioMonthSnapshot.actual()`/`targets()` are inputs, never screen figures.

## 5. Fixtures (hand-computed; the tests write these literals, W2)

### 5.1 Unit 1 vectors (no records; hand-built leaves, evaluated with `evaluate`, no `stated`)

Every leaf not named: absent `NOT_CONNECTED` (its `filled_by`), except the OPTION_ONLY leaves (their neutral) and
`period_days` 31 `DERIVED` (no origins: CALENDAR). Named values: actual `RECORDED`, target `DECLARED`, origins
`("source-emulated",)`, money and prices in USD.

| Leaf | Actual | Target |
|---|---|---|
| `delivered_kwh`, `technical_loss_kwh`, `unexplained_loss_kwh`, `adjustments_kwh`, `unmapped_kwh` | 9100, 410, 0, 45, 0 | 8550, 0, 0, 0, 0 |
| `tariff`, `productive_kwh`, `productive_tariff` | 0.40, 0, 0.30 | 0.40, 0, 0.30 |
| `necessary_l`, `candidate_l`, `unexplained_l`, `diesel_price` | 730, 330, 120, 1.25 | 700, 0, 0, 1.25 |
| `om`, `staff`, `in_transit`, `outstanding` | 600.00, 500.00, 0, 278.00 | 600.00, 500.00, 0, 0 |

Hand computation (Kobo's pack figures; AT-1, AT-2): actual billed 9100 − 410 − 0 − 45 − 0 = 8645, revenue
8645 × 0.40 = 3458.00, diesel 1180 L, fuel cost 1180 × 1.25 = 1475.00, cost to serve 2575.00, contribution 883.00;
target billed 8550, revenue 3420.00, 700 L, 875.00, 1975.00, contribution 1445.00.

**Expected `bridge(..., "contribution")`** (effect; scale in brackets):
- ROOT contribution: gap −562.00, effect −562.00, SPLIT, evidence DECLARED.
  - TERM revenue [1]: +38.00, SPLIT.
    - VOLUME billed_kwh [0.40]: gap 95, +38.00, SPLIT.
      - TERM metered_kwh [0.40]: gap 140, +56.00: TERM delivered_kwh [0.40] gap 550 +220.00; TERM
        technical_loss_kwh [−0.40] gap 410 −164.00; TERM unexplained_loss_kwh [−0.40] 0.
      - TERM adjustments_kwh [−0.40]: gap 45, −18.00. TERM unmapped_kwh [−0.40]: 0.
    - PRICE tariff [8645]: 0. VOLUME productive_kwh [0.30]: 0. PRICE productive_tariff [0]: 0.
  - TERM cost_to_serve [−1]: gap 600.00, −600.00, SPLIT; children exactly fuel_cost, om, staff (no row for
    `collection_cost` or `battery_wear`: neutral).
    - TERM fuel_cost [−1]: −600.00, SPLIT: VOLUME diesel_l [−1.25] gap 480 −600.00 (SPLIT: TERM necessary_l [−1.25]
      gap 30 −37.50; candidate_l gap 330 −412.50; unexplained_l gap 120 −150.00; no `extra_l` row); PRICE
      diesel_price [−1180] 0.
    - TERM om [−1] 0.00; TERM staff [−1] 0.00.
- `by_home`: `{"GROW_REVENUE": 220.00, "OPTIMIZE_COST": −782.00}` (−164 − 18 − 37.50 − 412.50 − 150; the losses and
  adjustments are Optimize lines under revenue, design §2.0).
- `bridge(..., "collected")`: ROOT gap −240.00 (3180.00 − 3420.00); TERM revenue +38.00; TERM in_transit [−1] 0;
  TERM outstanding [−1] gap 278.00, −278.00.
- **AT-3** (actual `diesel_price` 1.30): actual fuel cost 1534.00; fuel_cost TERM −659.00 = VOLUME diesel_l −600.00 +
  PRICE diesel_price [−1180] gap 0.05 −59.00.

### 5.2 Lakeside (unit 2 and 3): `backend/tests/fixtures/attribution_lakeside_mto.json`

The world: 3A4's `new_world()`; every step of 4b's `money_leaves_lakeside.json` (4b §4.1); then steps 1 and 2 of
5a's `targets_lakeside.json` with their `at` and `entered_by`; then this file's one step. Read through 4b's test
reader (`CommercialLeafSource(months, store, fallback())`, `StructureRead(src, stated=src)`) and `TargetRead(
BudgetLineReader(months, store), that read)`, all at `known_at = READ_AT` (3A4's clock, 2026-11-20T08:00Z, so
October is closed and every record is known): unit 2's tests call `site_bridge(read.site_inputs(s, OCT, READ_AT),
targets.site(s, OCT, READ_AT))`; unit 3's go through `BridgeRead(..., clock=lambda: READ_AT)` with `known_at` None.

```json
{"_note": "5b spec §5.2: Mto's October billing, receipts and fuel invoice; loaded after money_leaves_lakeside.json and targets_lakeside.json",
 "steps": [{"at": "2026-11-07T12:00:00+00:00", "entered_by": "service:test-5b", "batch":
   {"format_version": 1, "tenant_code": "lakeside-power", "source_type": "billing_export", "source_system": "mto-billing",
    "provenance": "source-emulated", "produced_at": "2026-11-07T09:00:00+03:00", "records": [
     {"format_version": 1, "kind": "CHARGE", "source_record_id": "MTO-CH-1001", "source_version": "1", "site_code": "MTO-001",
      "clocks": {"effective_from": "2026-10-01", "effective_to": "2026-11-01", "recognition_period": "2026-10"},
      "amount": {"value": "2160.00", "currency": "USD"}, "quantity": {"value": "5400", "unit": "kWh"},
      "body": {"account_ref": "C-3001", "line_type": "USAGE", "tariff_code": "T-MTO", "tariff_class": "STANDARD"}},
     {"format_version": 1, "kind": "RECEIPT", "source_record_id": "MTO-RC-1001", "source_version": "1", "site_code": "MTO-001",
      "clocks": {"occurred_at": "2026-10-26T10:00:00+03:00", "recognition_period": "2026-10"},
      "amount": {"value": "1890.00", "currency": "USD"}, "status": "COLLECTED", "body": {"payer_ref": "C-3001", "method": "MOBILE_MONEY"}},
     {"format_version": 1, "kind": "RECEIPT", "source_record_id": "MTO-RC-1002", "source_version": "1", "site_code": "MTO-001",
      "clocks": {"occurred_at": "2026-10-30T10:00:00+03:00", "recognition_period": "2026-10"},
      "amount": {"value": "150.00", "currency": "USD"}, "status": "PAID_IN_TRANSIT", "body": {"payer_ref": "C-3001", "method": "MOBILE_MONEY"}}]}},
  {"at": "2026-11-07T12:00:00+00:00", "entered_by": "service:test-5b", "batch":
   {"format_version": 1, "tenant_code": "lakeside-power", "source_type": "expense_ledger", "source_system": "lakeside-accounts",
    "provenance": "source-emulated", "produced_at": "2026-11-07T09:00:00+03:00", "records": [
     {"format_version": 1, "kind": "EXPENSE", "source_record_id": "MTO-EX-FUEL-1012", "source_version": "1", "site_code": "MTO-001",
      "clocks": {"occurred_at": "2026-10-12T11:00:00+03:00", "recognition_period": "2026-10"},
      "amount": {"value": "400.00", "currency": "USD"}, "status": "PAID",
      "body": {"counterparty_ref": "SUP-F", "category": "FUEL", "document_ref": "MTO-EX-FUEL-1012"},
      "quantity": {"value": "320", "unit": "L"}}]}}]}
```
(Record shapes copy 4b's `KISIWA-CH-1001`, `KISIWA-RC-1001` and `KISIWA-EX-FUEL-1010`.)

**Hand computation.** Mto actual: revenue 2160.00; in transit 150.00; outstanding 2160.00 − (1890.00 + 150.00) =
120.00; collected 2160.00 − 150.00 − 120.00 = 1890.00; diesel price 400.00 ÷ 320 = 1.25 (DERIVED); fuel cost
400.00; cost to serve 400.00 + 500.00 + 450.00 = 1350.00; contribution 810.00. Kisiwa actual with O&M carried at its
budget line 700.00: cost to serve 3120.00 + 700.00 + 500.00 = 4320.00; contribution 4070.00 − 4320.00 = −250.00.
Kobo: 4b §4.1 (883.00). Targets: 5a §5 (1445.00, −65.00, 915.00).

| Site | Root `contribution` (actual, target, gap) | Evidence | Revenue TERM | Cost to serve TERM (fuel, om, staff) |
|---|---|---|---|---|
| KOBO-001 | 883.00, 1445.00, −562.00 | DECLARED | +38.00 `NOT_SPLIT` `DETAIL_NOT_AVAILABLE` | −600.00 (−600.00 `NOT_SPLIT` `DETAIL_NOT_AVAILABLE`, 0.00, 0.00) |
| KISIWA-001 | −250.00, −65.00, −185.00 | ESTIMATED | −55.00 `NOT_SPLIT` | −130.00 (−130.00, 0.00 ESTIMATED `carried` True, 0.00) |
| MTO-001 | 810.00, 915.00, −105.00 | DECLARED | −80.00 `NOT_SPLIT` | −25.00 (−25.00, 0.00, 0.00) |

- Kobo revenue: `unobserved_actual == ("adjustments_kwh", "delivered_kwh", "productive_tariff", "tariff",
  "technical_loss_kwh", "unexplained_loss_kwh", "unmapped_kwh")`, `unobserved_target == ("delivered_kwh",
  "productive_tariff", "tariff")`. Kobo fuel_cost: `unobserved_actual == ("candidate_l", "necessary_l",
  "unexplained_l")`, `unobserved_target == ()`. Kobo root origins `("observed-financial", "source-emulated")`.
- Kisiwa and Mto revenue and fuel cost (handshake R9): `NOT_SPLIT`, `DETAIL_NOT_AVAILABLE`, with exactly Kobo's
  `unobserved_actual` and `unobserved_target` tuples above, written out per Site (same 4b readers on the same record
  shapes; 5a's target rules are per factor). A run that differs is a mid-build question.
- `by_home`: Kobo `{"GROW_REVENUE": 38.00, "OPTIMIZE_COST": −600.00}`; Kisiwa `{−55.00, −130.00}`; Mto `{−80.00,
  −25.00}`.
- Cash roots (actual, target, gap; in_transit, outstanding effects): Kobo 3180.00, 3420.00, −240.00 (0, −278.00);
  Kisiwa 3800.00, 4125.00, −325.00 (0, −270.00); Mto 1890.00, 2240.00, −350.00 (−150.00, −120.00). Every cash root is
  ESTIMATED (the target's leaks are zero assumptions) with `weakest_origin(origins) == "unknown"`.
- Kisiwa: `carried == ("om",)`, `not_carried == {}`; the carried leaf is exactly §3.1 step 4 with sources
  `("target:budget:<Kisiwa om revision id>",)`, origins `("source-emulated",)`; `actual.values["om"].missing.blocks ==
  ("cost_to_serve", "contribution")`; `targets.checks == (TargetCheck("contribution", Decimal("-60.00"),
  Decimal("-65.00"), "USD", False),)` and the root's target is −65.00.

**Portfolio** (Kobo, Kisiwa, Mto asked in that order), `contribution` root:

| Key | Actual | Target | Gap | Effect | k of n | Evidence |
|---|---|---|---|---|---|---|
| contribution | 1443.00 | 2295.00 | −852.00 | −852.00 | 3 of 3 | ESTIMATED |
| revenue | 9688.00 | 9785.00 | −97.00 | −97.00 | 3 of 3 | DECLARED |
| cost_to_serve | 8245.00 | 7490.00 | 755.00 | −755.00 | 3 of 3 | ESTIMATED |
| fuel_cost | 4995.00 | 4240.00 | 755.00 | −755.00 | 3 of 3 | DECLARED |
| om | 1800.00 | 1800.00 | 0.00 | 0.00 | 3 of 3 | ESTIMATED |
| staff | 1450.00 | 1450.00 | 0.00 | 0.00 | 3 of 3 | DECLARED |

`carried == ("KISIWA-001",)` on `om`, `cost_to_serve` and `contribution`, `()` on `revenue`, `fuel_cost` and
`staff`. `by_home == {"GROW_REVENUE": −97.00, "OPTIMIZE_COST": −755.00}`; `disagreements == (("KISIWA-001",
TargetCheck("contribution", Decimal("-60.00"), Decimal("-65.00"), "USD", False)),)`; `portfolio_lines.lines` one line,
`staff` 1200.00 (not added). Cash root: collected 8870.00 against 9785.00, −915.00; in_transit effect −150.00;
outstanding −668.00. These equal the pack's `portfolio.lakeside-power` and `sites.lakeside-power/<Site>` values in
`derived-values.json` (tests 6 and 7 read the file). **Pack comparison (handshake R13):** Site name map `{"Kobo":
"KOBO-001", "Kisiwa": "KISIWA-001", "Mto": "MTO-001"}`; nodes `revenue`, `collected`, `in_transit`, `outstanding`,
`fuel_cost`, `om`, `staff`, `cost_to_serve`, `contribution`; the row's `actual` against the pack's `actual` (`nodes`;
`sums` for the portfolio) and `target` against `plan`, as `Decimal(str(x)) == value`. Gaps, effects and evidence are
checked against this section's literals only; `NONE` keys are never compared (the pack sums them, D-5B.11).

**Without this file's step** (4b and 5a only): Mto's root `GAP_NOT_AVAILABLE`, `unobserved_actual` = 4b §4.1's
thirteen Mto leaves, `unobserved_target == ()`; portfolio `contribution`: actual 633.00, target 1380.00, gap and
effect −747.00 (−562.00 − 185.00), 2 of 3, `out == (("MTO-001", tuple(f"actual:{l}" for l in MTO_MISSING)),)` (`MTO_MISSING`: 4b's test literal, imported).

## 6. Tests (written first)

**No database** (`backend/tests/test_5b_attribution.py`; the world helpers of 3A4, 4b and 5a imported, never edited):
1. *(unit 1)* §5.1's contribution tree, every row: factor, kind, rule, scale, gap, effect (as `Decimal` and
   `format(v, "f")` for money), split, reason, child order; `by_home`; the collected tree.
2. *(unit 1)* AT-3 (price 1.30): volume −600.00 and price −59.00, never 35.00 and 624.00.
3. *(unit 1)* The stops, (a) to (c) rooted at `revenue`: (a) a stated `revenue` of 3458.00 with `delivered_kwh` absent on both sides
   (`NOT_RECEIVED`) and target stated 3420.00: SPLIT with VOLUME `productive_kwh` 0, PRICE `productive_tariff` 0 and
   a RESIDUAL +38.00 whose `unobserved_actual == ("delivered_kwh",)`; (b) the same with `productive_tariff`
   absent on both sides: `NOT_SPLIT`, `DETAIL_NOT_AVAILABLE`, no children; (c) §5.1's leaves with a stated actual
   revenue of 3500.00 (`computed` 3458.00): `NOT_SPLIT`, `RECORD_AND_FACTORS_DIFFER`; (d) `_toy("p * x")`
   (price first): VOLUME on `x`, PRICE on `p`; (e) `_toy`-style `y = x * z` with `z` in KWH: `PRICE_NOT_DECLARED`;
   (f) `y = x / z`: `RULE_NOT_DECLARED`; (g) actual `contribution` absent: ROOT `GAP_NOT_AVAILABLE`, effect None,
   evidence NOT_AVAILABLE, never 0; (h) target money in KES: ROOT `CURRENCY_MISMATCH:KES,USD`; (i) the solve
   (D-5B.14): §5.1's leaves, but target `diesel_price` 1.27, target `necessary_l` from 5a's `solve_main(reg,
   target_leaves, "fuel_cost", "necessary_l", Decimal("875.00"), currency="USD")[0]`, target evaluated with `stated=
   {"fuel_cost": LeafValue(Decimal("875.00"), "DECLARED", ("budget:test",), None, None, "USD", ("source-emulated",))}`;
   `bridge(reg, a, t, "fuel_cost")`: ROOT gap 600.00, effect 600.00, `SPLIT` (not `RECORD_AND_FACTORS_DIFFER`, not
   `SPLIT_INEXACT`); PRICE `diesel_price` scale 1180, gap −0.02, effect −23.60 exactly; VOLUME `diesel_l` scale 1.27
   with `effect.quantize(Decimal("0.01")) == Decimal("623.60")`; Σ children `!=` 600.00 and `agree(Σ, 600.00)` (the
   case exercises the tolerance); (j) §5.1's leaves with a stated actual revenue of 3458.01 (`computed` 3458.00):
   `NOT_SPLIT`, `RECORD_AND_FACTORS_DIFFER` (a cent is never within the tolerance).
4. *(unit 1)* Invariants over every tree built in tests 1 to 3 and 6: each SPLIT row's children effects sum to its
   effect exactly (`==`) on every tree but 3(i), and within `SOLVE_TOLERANCE` on 3(i); Σ `by_home` equals the root
   effect the same way; no `-0`; no row for a neutral term.
5. *(unit 2)* Carrying (pure; Kisiwa's real inputs and targets from §5.2, then one field replaced): (a) as given:
   carried `("om",)`, the leaf field by field; (b) `om`'s note set to `MONTH_OPEN`: not carried, reason `MONTH_OPEN`,
   root `GAP_NOT_AVAILABLE`; (c) cause `NOT_CONNECTED`: reason `NOT_CONNECTED`; (d) target `om` replaced by an
   `ESTIMATED` value with source `assumption:at-actual`: `NO_TARGET_LINE`; (e) the stated `fuel_cost` absent
   (`NOT_RECEIVED`, note None) with its DECLARED target: still absent, in neither `carried` nor `not_carried`;
   (f) `diesel_price` absent: untouched.
6. *(unit 2)* §5.2's three Site bridges: the table, every named field (Kisiwa's and Mto's revenue and fuel cost
   literals included), the cash roots, origins, Kisiwa's carried leaf and check, and the pack comparison per Site
   (§5.2's named fields).
7. *(unit 3)* §5.2's portfolio: the table, `carried` on every row of the table, `by_home`, cash, `disagreements`,
   `portfolio_lines`, the pack comparison (`SUM` keys only); every `NONE` row present in the trees has `actual`,
   `target` and `gap` None.
8. *(unit 3)* Never one set minus another, never a summed price: (a) §5.2 without the step: Mto `GAP_NOT_AVAILABLE`;
   the portfolio row −747.00, 2 of 3, `out` as stated; (b) two hand-built Site bridges in USD and KES: `effect` None,
   `note "CURRENCY_MISMATCH:KES,USD"`; (c) two Site bridges from §5.1's leaves (as given, and AT-3's actual price
   1.30) through `portfolio_bridge`: `diesel_price` row `actual`, `target`, `gap` None, `effect` −59.00, `k` 2;
   `tariff` row None, None, None, `effect` 0.00; `diesel_l` row 2360, 1400, 960, `effect` −1200.00 (D-5B.11).
9. *(unit 3)* (a) `BridgeRead.portfolio` makes `TargetRead.portfolio`'s refusals (another tenant, a repeated Site:
   `STRUCTURE_COMPOSE`); a COLDCHAIN `SiteRef` is in `out` of every row with `("STRUCTURE_NOT_DECLARED",)` and in
   `n`. (b) One instant (D-5B.13): recording wrappers around the `StructureRead` and `TargetRead` record every call's
   `known_at`; `BridgeRead(..., clock=lambda: READ_AT)` with `known_at` None, for `site` and for `portfolio`, records
   only `READ_AT`.
10. Grep: no `float(` under `structure/attribution/`; no module under it but `composition.py` imports a `commercial`
    module, and none imports a `snapshot` module; the packet lists every file changed; `git diff main...HEAD --
    backend/assetops_backend/structure/read.py` is empty.
11. *(unit 3)* A hand-built `SiteBridge` whose `contribution` tree holds `om` twice: `portfolio_bridge` raises
    `ValueError("REPEATED_FACTOR:om")`.

**Postgres** (pooled, `--db`; `backend/tests/test_5b_attribution_postgres.py`; Sites by 3A4's `NairobiSeeder`;
fixtures through `PostgresCommercialStore` as `test_5a_targets_postgres.py`):
1. Tests 6 and 7 against it (`BridgeRead` with clock `READ_AT`).
2. `build_bridge_read(url).read.portfolio(tid, [kobo, kisiwa, mto], "2026-10")`: `contribution` effect −852.00;
   `dispose()` runs.

**Regression:** `test_3b3_structure_evaluate.py`, `test_4b1_stated_nodes.py`, `test_4b_money_leaves.py`,
`test_5a_targets.py` unchanged and green. Commands as 3B3 §6; check-all once at the end; `select-tests` before review.

## 7. Done (questions; each can fail)

1. Is Lakeside's October contribution 1,443.00 against 2,295.00, −852.00, 3 of 3, to the cent, and each Site's as
   §5.2?
2. Does Kobo's −562.00 split into revenue +38.00 and fuel cost −600.00 from records alone, each saying why it is not
   split further and naming the leaves that would split it?
3. With the litres and kWh observed (§5.1), does the split go down to them exactly, volume at target price first
   (AT-1, AT-2, AT-3)?
4. Is Kisiwa's O&M carried at its budget line, *Estimated*, naming the service contractor invoice, never zero, and
   never carried in an open month, from an assumption, or for a heading?
5. Does every row carry the weakest evidence and the union of origins of what it rests on, with `unknown` weakest?
6. Is a residual shown only beside unobserved leaves, and never when the split is complete?
7. Is the portfolio gap always one set of Sites against the same set, with "k of n" and the Sites left out named,
   does a price or rate never add across Sites, and does each row name the Sites whose figure is carried?
8. Does Kisiwa's budget contribution line (−60.00) stay listed as a disagreement while the target is −65.00?
9. Is nothing changed outside `structure/attribution/` (new), the fixture, the two test files and the packet (no
   diff in `structure/read.py`)?

Packet: `specs/5b-attribution/packet.md`, with module paths and the mid-build count.

## 8. Out of scope

The screen and its words, including how the disagreement and each `NOT_SPLIT` reason read (`5c`, which must show
every disagreement, D-5B.10); the litre split (`4d`: once it fills `necessary_l`, `candidate_l` and `unexplained_l`,
fuel cost splits by §2.3 with no change here); kWh and tariff leaves (`4a`); carrying a heading at its target (queue
Q1); time-of-use mix (AR3) and ratios (AR5): no MINI_GRID node needs them; storing the bridge (D-3B7A.4); cold-chain
and EV (RC5).

## 9. Units

| Unit | Content | Needs | Commits |
|---|---|---|---|
| 1 | §2: rules, the engine, `by_home`, the tolerance; tests 1 to 4 (§5.1, 3(i), 3(j)) | `main` | 1 |
| 2 | §3: carrying, the Site bridge; the fixture; tests 5, 6 | 3B7a unit 0 (the seam) merged to `main` | 1 |
| 3 | §4: portfolio (SUM-only, `carried`), read (pinned instant), composition; tests 7 to 11; Postgres; check-all; packet (1.25) | unit 2 | 1 |

## 10. Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 (owner) | Carry a missing heading (revenue, fuel cost) at its budget line | No (D-5B.7): its gap would be zero by construction, hiding the very answer the executive asks; it reads "not available yet" |
| Q2 (owner) | Carry a missing cost in a month still open | No: every record is still due; the month reads as open |
| Q3 | Which cost lines may be carried | O&M and staff (the cost lines a budget states); others as they gain budget lines |
| Q4 | Order of the product split | Volume at target price, then price at actual volume (AR2, decision A13); never reversed |
| Q5 (owner) | When a Site's actual is missing, show the full target over every Site with one (P5 rule 7: 2,295.00, 3 of 3) beside the like-for-like figures (1,380.00, 2 of 3)? | No (D-5B.12): the gap view shows only like-for-like figures, with the Site left out named and its own target beside ("Mto not compared: billing not received; its target 915.00"); no second contribution target appears |
| Q6 | The pack sums prices (`derived-values.json` portfolio `sums`) | Pack fix queued for the pack lane (`evaluate_structure.py:562` sums only `SUM` factors; regenerate); no screen shows a summed price; not blocking 5b |
