# DS1b: the generator's canonical record writers (implementer spec)

Status: in_review (built 2026-11-20 on `task/DS1b-canonical-writers`; packet `packet.md`).

Architect (Claude), 2026-11-20. **Rev 2** (handshake round 1 folded in; `rulings.md` "Handshake answers (round 1)", D-DS1B.7, D-DS1B.8). Rev 1 was spec handshake step 1 (`.ai/RULES.md` §4). Lane A (sources and money), first
unit of the third build lane (owner, 20 Nov, item 3; `specs/BW1-build-wave1/rulings.md` D-BW1.7). Decisions with
reasons: `rulings.md` (D-DS1B.1 to D-DS1B.8). Reviewer: `reviewer-guide.md`. Questions: `handshake.md`, then
`mid-build-questions.md`.

Non-screen: simulator and tools only. 1 unit (D-DS1.14). Standard review depth is not enough here because the unit
writes money records: discovery review (W5).

## 0. Before you start

- **Depends on `2a`** (`assetops_contracts.canonical`). Code starts when `2a` is merged to `main` (the handshake is
  closed, rev 2). **DS1b merges only after `T2`** (`specs/T2-neutral-package-tests/`, the check-all guard that runs
  `simulator/tests` and `contracts/tests`; D-DS1B.6 amended).
- **Branch** `task/DS1b-canonical-writers` off `main` after `2a` merges; worktree `/opt/assetecon/AssetOpsV1-ds1b`.
- **Read:** this spec; `rulings.md`; `specs/2a-canonical-format/spec.md` §5 to §7 (the kinds, the catalogue, the source
  types); `specs/DS1-history-generator/rulings.md` D-DS1.1, D-DS1.4, D-DS1.10, D-DS1.12; the modules of
  `simulator/assetops_simulator/world/` (`history.py` §`_Scope.october`, `view.py`, `canonical.py`, `leaves.py`,
  `months.py`); `tools/world_history.py`; `simulator/tests/world/conftest.py`.
- **Python:** `PYTHONPATH` as the lane rules (worktree `backend:backend/tests:contracts:simulator:...`, absolute) and
  `/opt/assetecon/AssetOpsV1/.venv/bin/python`.
- **Databases:** none. Nothing here is pooled except check-all. Never touch ports 5490 or 8990, the walkthrough DB or
  Docker.
- **Collisions.** DS1m (mock-up files) and the UI lanes (`interactive-mockup-vNEXT/`, `Docs/design-system/`): none.
  `2a` must be merged first (you import it). `3A1` (lane A's next) does not touch the simulator. Do not edit the pack,
  the manifest, `history.json` or `world/history.py`.

## 1. Outcome and why

The world generator writes its money records as canonical v1 batches: the month cost lines (O&M, staff, maintenance,
customer compensation) and the operator's budget lines, for July to October, for the nine demonstration Sites. Every
batch passes `2a`'s `parse_batch`, and the same inputs give the same bytes. This is what the bulk loader (`DS3`)
loads and what `3A3`'s emulators turn into native files (D-DS1.1), so the commercial store holds the same records the
demonstration's figures were evaluated from. Gate question (strategy §8, "generation"): is every generated record
in the canonical format, labelled with its origin, and never invented beyond the declared inputs?

## 2. What is written, and what is not

**Inputs.** The manifest view (`ManifestView`, the October `period` records under `actual` and `plan`, `currency`,
`timezone_default`, `as_of`) and the generated history (`generate_history(view)`: July to September, money in
cents). October is read from the view; history months from the history. Nothing is read from `oracle`, `checks`,
`expectations` or any other key (the view's allowlist already ensures it).

**Structure keys.** Tenant `vertical` to structure key: `MINI_GRID` to `MINI_GRID`, `COLD_CHAIN` to `COLD_CHAIN`,
`EV_DEPOT` to `EV_DEPOT_CAPTIVE` (the demonstration's only EV business model). Any other vertical is refused
`DS1B_VERTICAL <tenant>`.

### 2.1 Actual side: month cost lines

| Structure key | Record field | Kind | Body | Source type |
|---|---|---|---|---|
| MINI_GRID | `om` | EXPENSE, category OM | `counterparty_ref` `om-contractor` | `expense_ledger` |
| MINI_GRID | `staff` | EXPENSE, category STAFF | `counterparty_ref` `payroll` | `expense_ledger` |
| MINI_GRID | `liability` | ADJUSTMENT | `reason_code` `CUSTOMER_COMPENSATION` | `billing_export` |
| COLD_CHAIN | `maint` | EXPENSE, category OM | `counterparty_ref` `om-contractor` | `expense_ledger` |
| COLD_CHAIN | `staff` | EXPENSE, category STAFF | `counterparty_ref` `payroll` | `expense_ledger` |
| COLD_CHAIN | `liability` | ADJUSTMENT | `reason_code` `CUSTOMER_COMPENSATION` | `customer_invoicing` |
| EV_DEPOT_CAPTIVE | `maintenance` | EXPENSE, category OM | `counterparty_ref` `om-contractor` | `expense_ledger` |

- An EXPENSE is written when the field is present on the side (it may be 0: a recorded zero) **and**, for October, the
  view's `coverage` entry of the same name is not `ESTIMATED`. An ESTIMATED field writes nothing, listed
  `ESTIMATED_NOT_RECEIVED` (D-DS1B.7; today Kisiwa `om`, Thika `maint`, Kasarani `maintenance`; history months carry
  RECORDED). An ADJUSTMENT is written only when `liability` is present, not 0 and not ESTIMATED. A zero `liability`
  on the actual side is listed `ZERO_NO_ROW` (D-DS1B.3). A field absent from the side writes nothing (D-DS1.12).
- Whether a source counts as *held* for a Site and month is `DS3`'s to declare from coverage, not DS1b's; DS1b writes
  no empty batches (R6).
- Every other actual field is not written (§2.3).

### 2.2 Plan side: budget lines, one per leaf the evaluator fills from the plan record

`PASS_THROUGH` is a literal table in the new module: for each structure key, each leaf whose `factor_map` expression
has one or more whole `|` alternatives of the form `record.<field>`, with those fields in order. It must equal this
(T3 derives it independently from the manifest):

| Structure key | Leaf: record fields, in order |
|---|---|
| MINI_GRID | `delivered_kwh`: delivered_kwh, billed_kwh · `technical_loss_kwh`: technical_loss_kwh, expected_technical_loss_kwh · `unexplained_loss_kwh`: unexplained_kwh · `adjustments_kwh`: adjustments_kwh · `unmapped_kwh`: unbilled_mapping_kwh · `in_transit`: in_transit · `outstanding`: outstanding · `necessary_l`: necessary_l, diesel_l · `candidate_l`: candidate_l · `unexplained_l`: unexplained_l · `om`: om · `staff`: staff · `hours_per_day`: reduced_hours_per_day · `major_assets`: major_assets · `unserved_critical_kwh`: unserved_critical_kwh · `customer_hours_interrupted`: customer_hours_interrupted · `field_visits`: field_visits · `liability`: liability · `dawn_days_below`: dawn_days_below_safeguard |
| COLD_CHAIN | `crate_days`: crate_days · `staff`: staff · `maint`: maint · `liability`: liability · `outstanding`: outstanding · `excursion_crates`: excursion_crates · `excursion_days`: excursion_days · `batches_exposed`: batches_exposed · `cooling_minutes_unavailable`: cooling_minutes_unavailable |
| EV_DEPOT_CAPTIVE | `nights_in_period`: nights · `peak_kwh`: peak_kwh · `kwh_2200_2400`: kwh_2200_2400, offpeak_kwh, kwh · `kwh_0000_0500`: kwh_0000_0500 · `max_kw`: max_kw · `maintenance`: maintenance · `spare_bus_nights`: spare_bus_nights |

- For each plan side (Site, month) and each leaf in table order, a BUDGET_LINE is written **only when the first field
  of the leaf's list is present** (the evaluator's `own` rule, `evaluate_structure.py:637-650`), with `factor_id` =
  the leaf, `value` = that field's value and `body.line_ref` = the field. A later field that is present writes nothing
  and is listed `NOT_OWN_LINE` (R1): a leaf with no own line stays the owner's labelled assumption (20 Nov, item 6).
  On the fixture this writes MINI_GRID `om`, `staff`; COLD_CHAIN `crate_days`, `staff`, `maint`, `liability` (Thika's
  0 as `0.00`); EV `peak_kwh`, `max_kw`, `maintenance`.
- `currency` (the view's `currency`) is set if and only if the leaf's catalogue unit has a `MONEY` exponent. A
  `PASS_THROUGH` or `ACTUAL_WRITERS` field in `leaves.MONEY_LEAVES` must map to a leaf whose `Factor.money` is true,
  and a field mapped to such a leaf must be in `MONEY_LEAVES`; otherwise `DS1B_MONEY_MISMATCH <structure key> <field>`
  (R11).
- Plan fields that no leaf passes through (`contribution`, `revenue`, `diesel_cost`, `energy`, `occupancy_pct`,
  `peak_share`, `demand_cost`, `offpeak_cost`, `peak_cost`, `energy_cost`, `departures_required`, `total` and the rest)
  are not written: they are stated or derived figures, or targets above factor level that `5a` rules (D-DS1B.4).

### 2.3 The unwritten list

`build_records` also returns every present field it did not write, as `(tenant, site code, month, side, field,
reason)`, sorted (P11). Reasons:
- `NOT_A_MONTH_RECORD`: actual fields other than §2.1's (readings, observers, receipts and settlements, derived nodes;
  their records come with `DS2`'s day split and `3A3`);
- `ESTIMATED_NOT_RECEIVED`: an October §2.1 field whose coverage is ESTIMATED (D-DS1B.7);
- `ZERO_NO_ROW`: an actual `liability` of 0 (actual side only);
- `NOT_OWN_LINE`: a plan field that is a later alternative of a leaf (R1);
- `READ_IN_AN_EXPRESSION`: a plan field the `factor_map` reads outside a whole alternative (COLD_CHAIN `kwh`, through
  `excess_kwh`; R4);
- `NOT_READ_BY_A_LEAF`: any other plan field (stated or derived figures, targets above factor level; `5a`'s).

The packet quotes the counts by reason; T5 pins the list for the fixture.

## 3. Record content (all values exact)

- **Identity.** `source_record_id` = `gen:<site code>:<month>:<side>:<name>`, where `<name>` is the record field for
  EXPENSE and ADJUSTMENT and the `factor_id` for a BUDGET_LINE (P4); `side` is `actual` or `plan`; `source_version`
  `"1"`; `site_code` the view's site `code`.
- **Money text.** For any int `c` of cents: `"<c // 100>.<c % 100:02d>"` when `c >= 0`, else `"-" + text(-c)` (P10).
  October money is the view value as a `Fraction` times 100, which must be a whole number
  (`DS1B_MONEY <tenant>/<site code>/<month> <side> <field>`).
- **Other numbers.** History integers are `str(n)`. An October written field must be an int or decimal text (else
  `DS1B_NUMBER <tenant>/<site code>/<month> <side> <field>`, P9) and is written as `format(Decimal(str(value)), "f")`;
  if `2a` refuses it (length or exponent bound), the batch fails `DS1B_FORMAT` (last bullet).
- **Clocks** (story time, the view's `timezone_default`, offset from `zoneinfo` for that date; Nairobi is `+03:00`; the
  month's last day from `months.period_end`, P7):
  - EXPENSE: `occurred_at` = the month's last day at `17:00:00` local; `recognition_period` = the month.
  - ADJUSTMENT: `effective_from` = the month's first day; `recognition_period` = the month.
  - BUDGET_LINE: `recognition_period` = the month.
  - `as_of` must be a date (`DS1B_AS_OF`, P9); `produced_at` is later than every `occurred_at` (R9).
- **Other fields.** EXPENSE: `amount` (money text, `currency`), `status` `PAID`, `subject` `{SITE, <site code>}`,
  `document_ref` = the record ID. ADJUSTMENT: `amount` = minus the liability, `subject` `{SITE, <site code>}`,
  `authorised_by_ref` `finance-lead`, `document_ref` = the record ID. BUDGET_LINE: `value`, `line_ref` = the plan
  field, `version_ref` `budget-2026-v1`, `currency` per §2.2. The constant references are source text; `3A5` never
  shows them as a named person or counterparty (R5).
- **Batches.** One batch per (tenant, source type) that has records (no empty batches), in tenant order then this
  source-type order: `expense_ledger`, `billing_export`, `customer_invoicing`, `budget_workbook`; records sorted by
  `(site code, month, side, name)`. Envelope: `format_version` 1, `tenant_code`, `source_type`, `source_system`
  `assetops-world-generator`, `provenance` `source-emulated` (D-DS1B.5: the evidence word follows the path, so a store
  record is *Emulated* and a history leaf *Simulated*; no screen shows both for one figure), `produced_at` = the
  view's `as_of` at `06:00:00` local.
- **One record per (Site, month, field)** (D-DS1B.8): a later slice writing finer records for the same key removes the
  month record from `DS3`'s load or reconciles to it.
- **Validation.** Each batch object is passed through `parse_batch`; any refused record raises
  `DS1B_FORMAT <code> <path>` (a generator defect; never written out).

## 4. Code

- `simulator/assetops_simulator/world/records.py` (new): `STRUCTURE_KEY`, `ACTUAL_WRITERS`, `PASS_THROUGH`,
  `RecordsResult` (frozen dataclass: `batches: tuple[BatchResult, ...]`, `unwritten: tuple[tuple[str, str, str, str,
  str, str], ...]`), `build_records(view: dict, history: dict) -> RecordsResult`, `batch_file_name(b) -> str`
  (`<tenant>.<source_type>.json`). It imports `assetops_contracts.canonical` and the world modules only.
- `simulator/assetops_simulator/world/leaves.py`: no behaviour change (history stays byte-identical, D-2A.8 as amended
  by D-DS1B.2). Its docstring now says that `MONEY_LEAVES` are history *record field* names, not factor IDs, and that
  factor IDs come from `assetops_contracts.canonical`.
- `simulator/assetops_simulator/world/__init__.py`: the module list names `records`, and "Standard library only" becomes
  "standard library and `assetops_contracts` only" (P8).
- `simulator/tests/world/conftest.py`: docstring and `--update-golden` help text name `records_v1.json` too (P5).
- `tools/world_history.py`: also inserts the repository's `contracts` on `sys.path` (P1), and gains a sub-command
  `records --manifest M --out DIR` (it generates the history from the view itself). It creates `DIR`, refusing
  `DS1B_OUT inside-repository` when `DIR` resolves inside the repository root and `DS1B_OUT not-empty` when it already
  holds a file (P6); writes each batch as `to_canonical_json` bytes to `DIR/<tenant>.<source_type>.json` and
  `DIR/unwritten.json` (`canonical.file_bytes` of the list); exit 0, or 3 with the `DS1B_*` text on stderr (argparse
  keeps 2). The coordinator writes to `/opt/assetecon/generated/ds1b-<rev>/`. No `31` and no private-block name in
  `records.py`, the CLI or its help (DS1a's grep guards, P7).

## 5. Tests (`simulator/tests/world/test_records.py`; written first)

On the fixture view (`conftest.FIXTURE`) and its generated history:
- **T1** Every batch re-parses with `parse_batch` with no refusal; `batch_digest` of each equals
  `golden/records_v1.json` (a new golden: `{file name: digest}` plus the unwritten counts by reason), rewritten only
  with `--update-golden`. No output byte string contains `RECORDED`, `Recorded`, `field-integrated`,
  `observed-financial` or `bench-tested` (R5).
- **T2** The `records` CLI run in two processes (`PYTHONHASHSEED` 1 and 2), into two fresh scratch directories,
  writes identical bytes; it refuses `DS1B_OUT inside-repository` and `DS1B_OUT not-empty` with exit 3.
- **T3** Independent derivations from the manifest (read with `yaml`):
  - `PASS_THROUGH` equals the whole top-level `|` alternatives matching `record\.[a-z0-9_]+` (R12); no Site's
    `factor_sources` holds a `record.<field>` alternative;
  - `ACTUAL_WRITERS`' (structure key, field) pairs equal the `leaf_sources` rows whose kind starts with `EXPENSE` or
    `ADJUSTMENT`, whose `absent` is not `OPTION_ONLY` and whose catalogue `Factor.money` is true; the kind's
    parenthesis matches the category (`(OM)` OM, `(STAFF)` STAFF, `(credit note)` ADJUSTMENT) (R3);
  - the `READ_IN_AN_EXPRESSION` fields equal `record\.([a-z0-9_]+)` anywhere in `factor_map` minus the pass-through
    fields (R4);
  - `set(STRUCTURE_KEY.values()) == canonical.STRUCTURE_KEYS` and `STRUCTURE_KEY`'s keys equal `history.rules`' keys
    (R10).
- **T4** Sums: for each Site-month, each EXPENSE amount equals its field (cents), each ADJUSTMENT equals minus
  `liability`, each BUDGET_LINE value equals its own field, October included; `produced_at` is later than every
  `occurred_at`.
- **T5** The unwritten list for the fixture equals the golden's counts; it lists Kisiwa `om`, Thika `maint` and
  Kasarani `maintenance` for October as `ESTIMATED_NOT_RECEIVED`; apart from that reason, it contains no §2.1 money
  field that is present and non-zero.
- **T6** `history.json` is unchanged: DS1a's T1 and T2 (golden and CLI digest) still pass (P3).
- **T7** Refusals through `build_records(planted view, history of the unplanted fixture)` (P2), each asserting the full
  text: `vertical: EV_FLEET` (`DS1B_VERTICAL metro-bus`); an October actual `om` of `"10.005"` (`DS1B_MONEY
  lakeside-power/KOBO-001/2026-10 actual om`); an October plan `crate_days` of `"0.3333333333333333333333333333333"`
  (`DS1B_FORMAT CANONICAL_NUMBER record.body.value`); an October plan `om` of `"abc"` (`DS1B_NUMBER ...`); `as_of`
  `"soon"` (`DS1B_AS_OF`); a `MONEY_LEAVES` field mapped to a non-money leaf by a patched table (`DS1B_MONEY_MISMATCH`).
- **T8** Neutrality: `records.py` imports nothing from `assetops_backend` (the dependency-direction guard also checks).
- **T9** Independent of DS1b's rule (R1): for every October Site, no BUDGET_LINE names a leaf that
  `missing-records.json` lists on the target side carried as ASSUMPTION; in particular no `delivered_kwh`,
  `necessary_l` or `kwh_2200_2400` budget line exists.

Commands:
```bash
cd /opt/assetecon/AssetOpsV1-ds1b
export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
$PY -m pytest simulator/tests/world -q          # T1-T8 and DS1a's tests (regression)
$PY -m pytest backend/tests/test_2a_canonical_v1.py backend/tests/test_2a_canonical_manifest_parity.py -q
pwsh -NoProfile -File tools/check-all.ps1      # fast mode, once, at the end
```
`T2` (the check-all guard over `simulator/tests` and `contracts/tests`) must be merged before DS1b merges (R8). If the
builder finishes first, the packet records a by-hand `simulator/tests/world` run with its revision.

## 6. Done (acceptance as questions)

1. Does every written record pass `2a`'s format, in batches whose digests are golden and identical across processes?
2. Does every cost line and budget line equal its input to the cent, for July to October at all nine Sites?
3. Is nothing written that the evaluator does not read from a record, and is every unwritten field listed with its
   reason?
4. Is `history.json` byte-identical, and does nothing outside §4's files and the golden change?
5. Are the records labelled `source-emulated` and never anything stronger?
6. Is no estimate written as a record (October ESTIMATED lines listed, GAP-1 intact), and is no budget line written
   for a leaf the demonstration carries as a labelled assumption (T9)?
7. Is `T2` merged, so `simulator/tests` runs in check-all at this merge?

Packet: `specs/DS1b-canonical-writers/packet.md`, with the mid-build question count and the unwritten counts.

## 7. Out of scope

Customer-level charges, receipts and settlements, telemetry envelopes and day splits (`DS2`, `3A3`); utility invoice
lines and fuel purchases (`3A3`); native export files (`3A3`); loading (`DS3`); targets above factor level, including
Ruiru's stated total (`5a`); November rolling records (`DS6`).

## 8. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | Budget lines only from a leaf's own field (D-DS1B.4 as amended by R1) | Yes; fallbacks and node-level plan figures stay unwritten until `5a` |
| Q2 | Month cost lines dated the month's last day 17:00 local, paid | Yes; `DS2` may spread them over days later without changing totals |
| Q3 | `simulator/tests` and `contracts/tests` gated at every merge | `T2`, a precondition of this merge (R8) |
