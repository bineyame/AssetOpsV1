# DS1b: the generator's canonical record writers (implementer spec)

Architect (Claude), 2026-11-20. Rev 1, spec handshake step 1 (`.ai/RULES.md` §4). Lane A (sources and money), first
unit of the third build lane (owner, 20 Nov, item 3; `specs/BW1-build-wave1/rulings.md` D-BW1.7). Decisions with
reasons: `rulings.md` (D-DS1B.1 to D-DS1B.6). Reviewer: `reviewer-guide.md`. Questions: `handshake.md`, then
`mid-build-questions.md`.

Non-screen: simulator and tools only. 1 unit (D-DS1.14). Standard review depth is not enough here because the unit
writes money records: discovery review (W5).

## 0. Before you start

- **Depends on `2a`** (`assetops_contracts.canonical`). Code starts when `2a` is merged to `main` and this handshake
  has no open question. The handshake runs now, while `2a` is built.
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

- An EXPENSE is written when the field is present on the side (it may be 0: a held source with a zero cost line is a
  recorded zero). An ADJUSTMENT is written only when `liability` is present and not 0 (ZERO_WHEN_HELD: a held source
  with no credit note means zero; D-DS1B.3). A field absent from the side writes nothing (D-DS1.12: absent is
  missing, never 0).
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

- For each plan side (Site, month) and each leaf in table order, the **first present** field of its list gives one
  BUDGET_LINE with `factor_id` = the leaf and `value` = that field's value (the evaluator's own first-present rule,
  DS1 handshake P1). The other present fields of that list are not written (§2.3, `ALTERNATIVE_NOT_FIRST`).
- `currency` (the view's `currency`) is set if and only if the leaf's catalogue unit has a `MONEY` exponent. A field
  in `leaves.MONEY_LEAVES` (money in cents in the history) must map to such a leaf, and a money leaf's field must be in
  `MONEY_LEAVES`; otherwise `DS1B_MONEY_MISMATCH <structure key> <field>`.
- Plan fields that no leaf passes through (`contribution`, `revenue`, `diesel_cost`, `energy`, `occupancy_pct`,
  `peak_share`, `demand_cost`, `offpeak_cost`, `peak_cost`, `energy_cost`, `departures_required`, `total` and the rest)
  are not written: they are stated or derived figures, or targets above factor level that `5a` rules (D-DS1B.4).

### 2.3 The unwritten list

`build_records` also returns every present field it did not write, as `(tenant, site, month, side, field, reason)`,
sorted; reasons: `NOT_A_MONTH_RECORD` (actual fields other than §2.1's: readings, observers, receipts and
settlements, derived nodes; their records come with `DS2`'s day split and `3A3`), `NOT_READ_BY_A_LEAF` (plan fields
§2.2 does not pass through), `ALTERNATIVE_NOT_FIRST`, `ZERO_NO_ROW` (a `liability` of 0). The packet quotes the
counts by reason; T5 pins the list for the fixture.

## 3. Record content (all values exact)

- **Identity.** `source_record_id` = `gen:<site code>:<month>:<side>:<field>` (`side` is `actual` or `plan`; the code
  is the view's site `code`); `source_version` `"1"`; `site_code` the site `code`.
- **Money text.** Cents `c` (an int) become `"<c // 100>.<c % 100:02d>"` for `c >= 0`, and `"-" + text(-c)` for a
  negative ADJUSTMENT amount. October money is the view value as a `Fraction` times 100, which must be a whole
  number (`DS1B_MONEY <tenant>/<site>/<month> <field>`).
- **Other numbers.** History integers are `str(n)`. An October view value (an int, or decimal text, which is all the
  view admits) is written as `format(Decimal(str(value)), "f")`; if `2a` refuses it (length or exponent bound), the
  batch fails `DS1B_FORMAT` (§3, last bullet).
- **Clocks** (story time, the view's `timezone_default`, offset from `zoneinfo` for that date; Nairobi is `+03:00`):
  - EXPENSE: `occurred_at` = the month's last day at `17:00:00` local; `recognition_period` = the month.
  - ADJUSTMENT: `effective_from` = the month's first day; `recognition_period` = the month.
  - BUDGET_LINE: `recognition_period` = the month.
- **Other fields.** EXPENSE: `amount` (money text, `currency`), `status` `PAID`, `subject` `{SITE, <site code>}`,
  `document_ref` = the record ID. ADJUSTMENT: `amount` = minus the liability, `subject` `{SITE, <site code>}`,
  `authorised_by_ref` `finance-lead`, `document_ref` = the record ID. BUDGET_LINE: `value`, `version_ref`
  `budget-2026-v1`, `currency` per §2.2.
- **Batches.** One batch per (tenant, source type) that has records, in tenant order then §2.1's source-type order
  (`expense_ledger`, `billing_export`, `customer_invoicing`, `budget_workbook`); records sorted by
  `(site code, month, side, field)`. Envelope: `format_version` 1, `tenant_code`, `source_type`, `source_system`
  `assetops-world-generator`, `provenance` `source-emulated` (D-DS1.10: *Emulated* arrives with these source-shaped
  records), `produced_at` = the view's `as_of` at `06:00:00` local.
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
- `simulator/assetops_simulator/world/__init__.py`: the module list names `records`.
- `tools/world_history.py`: a new sub-command `records --manifest M --out DIR` (it generates the history from the
  view itself): writes each batch as `to_canonical_json` bytes to `DIR/<tenant>.<source_type>.json`, and
  `DIR/unwritten.json` (`canonical.file_bytes` of the list); exit 0, or 2 with the `DS1B_*` text on stderr. Output
  directories are never in the repository (generated data; evidence rules, RULES §9).

## 5. Tests (`simulator/tests/world/test_records.py`; written first)

On the fixture view (`conftest.FIXTURE`) and its generated history:
- **T1** Every batch re-parses with `parse_batch` with no refusal; `batch_digest` of each equals
  `golden/records_v1.json` (a new golden: `{file name: digest}` plus the unwritten counts by reason), rewritten only
  with `--update-golden` (the conftest option DS1a defined).
- **T2** Determinism: the `records` CLI run in two processes (`PYTHONHASHSEED` 1 and 2) writes identical bytes.
- **T3** `PASS_THROUGH` equals the derivation from the manifest's `factor_map` (read with `yaml` in the test; whole
  `|` alternatives matching `record\.[a-z0-9_]+`), and `ACTUAL_WRITERS`' fields are exactly the leaves whose
  `empty_states.leaf_sources` kind starts with `EXPENSE` or `ADJUSTMENT` and that appear in some history side.
- **T4** Sums: for each Site-month, each EXPENSE amount equals its field (cents), each ADJUSTMENT equals minus
  `liability`, each BUDGET_LINE value equals its first-present field, October included.
- **T5** The unwritten list for the fixture equals the golden's counts, and contains no money field of §2.1 that is
  present and non-zero.
- **T6** `history.json` is unchanged: the DS1a golden test still passes, and `generate_history` output bytes are equal
  before and after importing `records`.
- **T7** Refusals, each asserting the full text: an EV tenant with `vertical: EV_FLEET` (`DS1B_VERTICAL`); an October
  `om` of `"10.005"` (`DS1B_MONEY`); an October `crate_days` of `"0.3333333333333333333333333333333"` (33 characters, over 2a's
  bound: `DS1B_FORMAT CANONICAL_NUMBER record.body.value`); a `MONEY_LEAVES` field mapped to a non-money leaf by a
  patched table (`DS1B_MONEY_MISMATCH`).
- **T8** Neutrality: `records.py` imports nothing from `assetops_backend` (the dependency-direction guard also checks).

Commands:
```bash
cd /opt/assetecon/AssetOpsV1-ds1b
export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
$PY -m pytest simulator/tests/world -q          # T1-T8 and DS1a's tests (regression)
$PY -m pytest backend/tests/test_2a_canonical_v1.py backend/tests/test_2a_canonical_manifest_parity.py -q
pwsh -NoProfile -File tools/check-all.ps1      # fast mode, once, at the end
```
`simulator/tests` is in no merge runner (the same gap D-2A.10 closed for `2a`; D-DS1B.6): the packet asks the
coordinator to run `simulator/tests/world` at the merge, by hand, until the tools item lands.

## 6. Done (acceptance as questions)

1. Does every written record pass `2a`'s format, in batches whose digests are golden and identical across processes?
2. Does every cost line and budget line equal its input to the cent, for July to October at all nine Sites?
3. Is nothing written that the evaluator does not read from a record, and is every unwritten field listed with its
   reason?
4. Is `history.json` byte-identical, and does nothing outside §4's files and the golden change?
5. Are the records labelled `source-emulated` and never anything stronger?

Packet: `specs/DS1b-canonical-writers/packet.md`, with the mid-build question count and the unwritten counts.

## 7. Out of scope

Customer-level charges, receipts and settlements, telemetry envelopes and day splits (`DS2`, `3A3`); utility invoice
lines and fuel purchases (`3A3`); native export files (`3A3`); loading (`DS3`); targets above factor level, including
Ruiru's stated total (`5a`); November rolling records (`DS6`).

## 8. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | Budget lines only for leaves the evaluator fills from the plan record (D-DS1B.4) | Yes; node-level stated plan figures stay unwritten until `5a` |
| Q2 | Month cost lines dated the month's last day 17:00 local, paid | Yes; `DS2` may spread them over days later without changing totals |
| Q3 | `simulator/tests` and `contracts/tests` join the merge runner as a small tools item (D-DS1B.6) | Yes, proposed to the coordinator; until then, run by hand at merge |
