# DS1b handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Reviewer (Claude), 2026-11-20, on `main` at `2edd204f4` (the dispatch named `184dc509e`; `main` moved during the
review, and the only change in the inputs read is the manifest, whose `factor_map`, `leaf_sources`, `coverage` and
view are unchanged: the fixture still equals the manifest's view). Findings were checked against the code and the
pack, not only the spec. Severity: High blocks the handshake; Medium needs an answer before code; Low is a wording or
a test addition. **(done)** marks an answer that changes what counts as done.

**R1 (High) (done). Plan side: "first present" writes budget lines the demonstration says were not received.**
- *Why it matters.* Spec §2.2 (`spec.md:78-80`) and D-DS1B.4 (`rulings.md:30-37`) write a BUDGET_LINE from the first
  present alternative. The evaluator does not treat a fallback alternative as a target line. `leaf_values`
  (`evaluate_structure.py:637-650`) marks a leaf `own` only when its leftmost alternative is filled.
  `target_side_entries` (`:667-680`) then reports every other leaf as `PLAN_LINE ... NOT_RECEIVED`, carried as
  ASSUMPTION. `missing-records.json` says so for the October plan: Kobo, Kisiwa and Mto list `delivered_kwh` and
  `necessary_l` among others, and Embakasi lists `kwh_2200_2400`. DS1b as specified would write these lines:
  - `delivered_kwh` = plan `billed_kwh` (8,550 at Kobo; `billed_kwh` is a node, manifest `:818`);
  - `necessary_l` = plan `diesel_l` (a node, `:821`);
  - `kwh_2200_2400` = `offpeak_kwh` at Embakasi, and = `kwh` at Kasarani (37,200, all of its energy, recorded as a
    22:00-24:00 target).

  A store read would find target lines the pack says were never received. The ASSUMPTION label disappears, against
  D-DS1B.4's own last sentence ("a leaf with no line reads as the owner's labelled assumption").
- *Proposed answer.* Write a BUDGET_LINE only when the leaf's **first** alternative is present (the evaluator's `own`
  rule). When a later alternative fills the leaf, write nothing and list the field with reason `NOT_OWN_LINE` (this
  replaces `ALTERNATIVE_NOT_FIRST`). The fallback fields (`billed_kwh`, `diesel_l`, `offpeak_kwh`, `kwh`) are
  node-level targets, which are 5a's.
  - On the fixture, the plan then writes: MINI_GRID `om` and `staff`; COLD_CHAIN `crate_days`, `staff`, `maint` and
    `liability`; EV `peak_kwh`, `max_kw` and `maintenance`.
  - Add a check that is independent of DS1b's own rule: for every October Site, no BUDGET_LINE names a leaf that
    `missing-records.json` lists as a plan ASSUMPTION.
  - Reviewer-guide P3 then becomes "no BUDGET_LINE `kwh_2200_2400` at Embakasi or Kasarani".

**R2 (High) (done). October cost lines with coverage ESTIMATED become paid invoices.**
- *Why it matters.* §2.1 (`spec.md:61-64`) writes an EXPENSE whenever the field is present, with status `PAID` and a
  `document_ref`. Three October lines are present only as estimates, each with a coverage note in the manifest:
  - Kisiwa `om` (manifest `:191-192`, "O&M invoice for October not received; plan amount carried as ESTIMATED");
  - Thika `maint` (`:472-473`);
  - Kasarani `maintenance` (`:647-648`).

  `missing-records.json` lists all three as `NOT_RECEIVED`, carried as TARGET, and the disorder test GAP-1 (`:1811`)
  expects "line ESTIMATED; coverage below 100%; never zero". DS1b would fabricate a received, paid invoice and erase
  GAP-1 from the store. This answers the gate question "never invented beyond the declared inputs" with a no. The
  view already carries `coverage` (`view.py:20`, `PERIOD_KEYS`).
- *Proposed answer.* A §2.1 field whose October `coverage` line of the same name is `ESTIMATED` writes nothing,
  reason `ESTIMATED_NOT_RECEIVED`. Coverage line names equal the field names for `om`, `staff`, `maint`,
  `maintenance` and `liability`.
  - History months are not affected: their `coverage` reads RECORDED (D-DS1.10), and the evaluator drops ESTIMATED for
    history (`evaluate_structure.py:812-813`).
  - Update T4 and T5. The three October fields are listed with this reason. T5's "no money field present and
    non-zero" excepts this reason.

**R3 (High) (done). T3's derivation of `ACTUAL_WRITERS` does not give §2.1's table.**
- *Why it matters.* T3 (`spec.md:145-146`) derives the writers as "leaves whose `leaf_sources` kind starts with
  `EXPENSE` or `ADJUSTMENT` and that appear in some history side". On the manifest:
  - MINI_GRID `adjustments_kwh` has kind `ADJUSTMENT` (`:1644`) and is in every MINI_GRID history month, so it is
    derived, but §2.1 excludes it.
  - MINI_GRID `liability` is in no MINI_GRID history side; only Thika's history has `liability`. Read per structure,
    it is dropped, although §2.1 includes it. Read across all structures, it is kept.

  So T3 either fails or has to be bent to pass, and the W2 independent check is lost.
- *Proposed answer.* Derive the writers as the `leaf_sources` rows whose kind starts with `EXPENSE` or `ADJUSTMENT`,
  whose `absent` is not `OPTION_ONLY`, and whose catalogue factor is money (`LEAF_FACTORS[leaf].money`). Drop the
  history clause.
  - This gives exactly §2.1: MINI_GRID `om`, `staff` and `liability`; COLD_CHAIN `staff`, `maint` and `liability`;
    EV `maintenance`. `adjustments_kwh` is kWh, `diesel_price` is MONEY/L, and `collection_cost` and `handling` are
    option-only.
  - T3 also asserts that the kind's parenthesis matches the category: `EXPENSE (OM)` gives OM, `EXPENSE (STAFF)` gives
    STAFF, and `ADJUSTMENT (credit note)` gives ADJUSTMENT.

**R4 (Medium) (done). COLD_CHAIN plan `kwh` is read by a leaf but labelled `NOT_READ_BY_A_LEAF`.**
- *Why it matters.* `excess_kwh` is `record.kwh - (base + k * record.crate_days)` (manifest `:910`), so the evaluator
  reads plan `kwh` for a leaf. It is not a whole alternative, so §2.2 does not pass it through, and §2.3
  (`spec.md:92`) gives it a false reason. Done question 3 asks for every unwritten field with its reason. `kwh` is
  also a COLD_CHAIN node (`:837`). The October plan `excess_kwh` is 0 at all three rooms: plan kWh equals
  1550 + 0.25 x plan crate-days, which is 3,410, 3,720 and 4,030.
- *Proposed answer.* Add the reason `READ_IN_AN_EXPRESSION` for a field that the `factor_map` reads outside a whole
  alternative. T3 can derive these fields by regex (`record\.([a-z0-9_]+)` anywhere, minus the pass-through fields).
  Leave the `excess_kwh` target to 5a, and say so in D-DS1B.4.

**R5 (Medium) (done). Honesty: one figure, two evidence words, and constant references.**
- *Why it matters.* D-DS1.10 rev 2 (`DS1 rulings.md:99-105`) says that a month total generated by rule is not a
  source record, so *Emulated* claims too much. DS1b's July to September lines are exactly such totals, labelled
  `source-emulated` (D-DS1B.5). That label is consistent with the design
  (`integration-source-to-canonical-design.md:703`, `:726`: a generator writing native-shape records is
  *source-emulated*, shown as Emulated). The consequence still needs stating: the same July `om` reads Simulated on
  the history path and Emulated on the store path.
  - The history blocks also carry `coverage: RECORDED` (`history.py:416`), which must never reach a record.
  - `authorised_by_ref finance-lead` and `counterparty_ref om-contractor` / `payroll` are generator constants.
- *Proposed answer.*
  - D-DS1B.5 adds: the evidence word follows the path (a store record is Emulated, a history leaf is Simulated), and no
    screen shows both words for one figure.
  - T1 adds a byte check: no output contains `RECORDED`, `Recorded`, `field-integrated`, `observed-financial` or
    `bench-tested`.
  - 3A5 shows the constant references as source text, never as a named approver.

**R6 (Medium) (done). Zero liability and "held": nothing DS1b writes makes a source held.**
- *Why it matters.* D-DS1B.3 (`rulings.md:24-28`) reads a missing row as zero only for a held source. DS1b writes no
  `billing_export` batch at all for lakeside-power, since no MINI_GRID Site has `liability`. For harvest-cold, the
  `customer_invoicing` batch holds only Thika's October row. Thika July to September (liability 0) and Mwea and
  Kirinyaga (no field) therefore look the same in the store. Without a held signal, a reader takes MISSING, while the
  evaluator takes `record.liability | 0` = 0. The plan side is also unclear: Thika's plan `liability` is `"0.0"` in
  October and 0 from July to September, and §2.3 lists `ZERO_NO_ROW` without a side.
- *Proposed answer.*
  - Being held is DS3's to declare (from `coverage` per Site and month), not DS1b's, and §2.3 says so. DS1b writes no
    empty batches.
  - `ZERO_NO_ROW` applies to the actual side only. Thika's plan writes a BUDGET_LINE `liability` of `0.00` (a received
    zero target; under R1 it is the leaf's own line).
  - The Architect confirms what Mwea and Kirinyaga's absent `liability` reads as (3B6).
  - Reviewer-guide P5 names the side.

**R7 (Medium). Overlap with 3A3 and DS2 on the same months.**
- *Why it matters.* Spec §1 (D-DS1.1) says 3A3's emulators turn these records into native files. The reviewer guide
  (`reviewer-guide.md:46`) says 3A3 and DS2 will add customer-level records for the same months. If 3A3 emits
  customer-level credit notes for Thika in October and DS1b's Site-level ADJUSTMENT is also loaded, their
  `source_record_id`s differ and −108.00 counts twice. The EXPENSE lines are not customer-level; only DS2's day split
  touches them (Q2: totals unchanged).
- *Proposed answer.* Rule now that DS1b's month record is the only canonical record for each (Site, month, field)
  until a named later slice replaces it, and that the replacing slice either removes it from DS3's load or reconciles
  to it, with its sum equal to the month line. This is a sentence in §7 and in 3A3's spec. It does not block DS1b.

**R8 (Medium) (done). The test-run gap is wider than this merge.**
- *Why it matters.* `tools/select-tests.py:37` (`TEST_DIR = "backend/tests"`) and `check-all` run no `simulator/tests`.
  Beyond DS1b's own merge:
  - DS1a's tests have been unguarded since DS1a merged.
  - T3 reads the pack manifest. A later pack change to `factor_map` or `leaf_sources` runs 2a's backend parity test but
    not T3, so `PASS_THROUGH` can drift silently.
  - A change under `contracts/assetops_contracts/canonical` never reruns `test_records.py`.
- *Proposed answer.* D-DS1B.6's tools item becomes a precondition of DS1b's merge, not a follow-up. Until it lands,
  the packet records the coordinator's by-hand `simulator/tests/world` run with its revision, and the reviewer reruns
  it on that revision.

**R9 (Low). The 17:00 last-day timestamp and the 06:00 `as_of`: not a real problem.**
- Nairobi is UTC+03:00 with no daylight saving. `zoneinfo` on this host gives `2026-10-31T17:00:00+03:00`.
  `produced_at` is `2026-11-06T06:00:00+03:00`, after every `occurred_at`. Keep Q2.
- Proposed: T4 asserts `produced_at` is later than every `occurred_at`, so that a later `as_of` (DS6) cannot date
  records after their batch.

**R10 (Low). `EV_DEPOT` versus `EV_DEPOT_CAPTIVE`: not a real problem.**
- The evaluator maps the same way (`evaluate_structure.py:187`, `:708`, `:785`). Only the manifest's prose
  `business_model` names "CAPTIVE", and the view does not carry it.
- Proposed: T3 asserts that `set(STRUCTURE_KEY.values())` equals `canonical.STRUCTURE_KEYS`, and that
  `STRUCTURE_KEY`'s keys equal `history.rules`' keys.

**R11 (Low). A field in both an alternative list and `MONEY_LEAVES`: not real today; the wording is.**
- Every money pass-through is a one-field list. Derived from the manifest, no list mixes money and non-money fields,
  and no field appears in two leaves' lists.
- But `spec.md:81-83`, read literally ("A field in `MONEY_LEAVES` must map to such a leaf"), fails for `energy_cost`
  and `total`, which map to no leaf. It also says "money" here and "a `MONEY` exponent" two lines above.
- Proposed wording: a `PASS_THROUGH` or `ACTUAL_WRITERS` field in `MONEY_LEAVES` must map to a leaf whose
  `Factor.money` is true, and a field mapped to such a leaf must be in `MONEY_LEAVES`. `currency` stays on 2a's
  MONEY-exponent rule.

**R12 (Low). Pass-through table at test time only; no run-time derivation.**
- This is real, and the spec's choice is right. `factor_map` is not in the view (`view.py:17`, `TOP_KEYS`). Adding it
  changes `view_digest`, and so `history.json`'s `meta.view_digest`, which breaks byte-identity (D-DS1B.2). Keep the
  literal table and T3.
- T3 splits on top-level `|` (the evaluator's `BitOr`, `evaluate_structure.py:110-114`). A plain split gives the
  same table today, because `(record.nights | period_days)` and `(record.failed_chargers | 0)` do not fullmatch.
  Checked: the derived table equals §2.2's.
- Site `factor_sources` (`evaluate_structure.py:166`; manifest `:178`, `:231`) can override a leaf per Site, and the
  view drops them. T3 adds: no Site's `factor_sources` holds a `record.<field>` alternative.

## Implementer pre-flight

The same Reviewer acting as Implementer, against `main` at `2edd204f4`. 2a is not on `main`, so items about its API
are checked against `specs/2a-canonical-format/spec.md` only. The dispatch asked for P numbers rather than the I
numbers in this file's header.

**P1 (Medium). The records CLI would import the wrong copy of `contracts`.**
- *Why.* `tools/world_history.py:4` puts only `simulator` on `sys.path`, and DS1a's CLI test helper removes
  `PYTHONPATH` (`test_cli.py:18`). `assetops_contracts` then resolves through the venv's editable install to
  `/opt/assetecon/AssetOpsV1/contracts`, the coordinator's `main` checkout (verified with `env -u PYTHONPATH`), not
  the worktree. T2 would run the CLI against `main`'s 2a while T1 runs in-process against the worktree's.
- *Proposed.* The CLI also inserts `parents[1] / "contracts"`. The file is already in §4.

**P2 (Medium) (done). Two T7 refusals cannot be reached through `generate_history`.**
- *Why.* Verified on the fixture:
  - `vertical: EV_FLEET` makes `generate_history` raise `HISTORY_RULE_UNKNOWN metro-bus/Embakasi/2026-07 EV_FLEET`.
  - The 33-character `crate_days` raises `HISTORY_NUMBER harvest-cold/Room A · Mwea/2026-07 crate_days`, because
    `history.py:52-56` applies the same 32-character and exponent bound as 2a.

  From a consistent view and history, `DS1B_FORMAT` is unreachable (it is defensive). The October `om` of `"10.005"`
  passes the history on either side.
- *Proposed.*
  - T7 calls `build_records(planted view, history of the unplanted fixture)`. `build_records` makes no view/history
    digest check; if one is wanted, it runs after `DS1B_VERTICAL` and T7 bypasses it.
  - T7 names the side: `crate_days` must be the plan side, because the actual side is `NOT_A_MONTH_RECORD`.
  - The `DS1B_MONEY` text gains `<side>`, since `om` exists on both sides.

**P3 (Medium) (done). T6's "before and after importing `records`" cannot be observed in one process.**
- *Why.* `test_records.py` imports `records` when it is collected, so there is no "before" in-process (`spec.md:152`).
- *Proposed.* Hash `generate_history(fixture)` in two fresh interpreters, one that has imported
  `assetops_simulator.world.records` first and one that has not. Alternatively, drop the clause: DS1a T2 (golden) and
  T1 (CLI digest) already pin the bytes.

**P4 (Medium) (done). What `<field>` is in a budget line's `source_record_id` and sort key.**
- *Why.* `spec.md:98` uses `<field>`. For a budget line, the record field and the leaf differ: `unexplained_loss_kwh`
  comes from `unexplained_kwh`, `unmapped_kwh` from `unbilled_mapping_kwh`, `dawn_days_below` from
  `dawn_days_below_safeguard`, and `nights_in_period` from `nights`. The choice changes the golden digests.
- *Proposed.* For a BUDGET_LINE, `<field>` is the `factor_id` (unique per leaf by construction), and
  `body.line_ref` (an optional field in 2a §6.4) holds the plan record's field, so the line shows where its value came
  from. EXPENSE and ADJUSTMENT keep the field, which equals the leaf.

**P5 (Medium). `--update-golden` and `conftest.py` are outside the scope list.**
- *Why.* `conftest.py:3` says `--update-golden` rewrites `golden/history_v1.json` and "nothing else does". T1 makes it
  rewrite `records_v1.json` too, which needs a docstring and help change in `conftest.py`. That file is not in
  `reviewer-guide.md`'s scope list (lines 13-20).
- *Proposed.* Add `simulator/tests/world/conftest.py` (docstring and help text only) to §4 and to the scope list.

**P6 (Medium). The CLI output directory is not enforced.**
- *Why.* §4 says output is "never in the repository", but nothing enforces it. If `DIR` already holds files from an
  earlier run, for example with other tenants, they stay, and DS3 would load them. Exit code 2 is also argparse's
  usage-error code.
- *Proposed.*
  - The CLI creates `DIR`. It refuses `DS1B_OUT <reason>` when `DIR` resolves inside the repository root or already
    holds any file.
  - `DS1B_*` failures exit 3; argparse keeps 2.
  - T2 adds both refusals.
  - The coordinator writes to scratch, or to `/opt/assetecon/generated/ds1b-<rev>/`.

**P7 (Low). DS1a's guards scan `records.py` and the CLI.**
- `test_core.py:120-137` greps every file in `world/` for `\b31\b`, `.now(`/`.today(`, `os.environ|getenv` and
  `float(`. `test_history.py:83-89` greps `world/` and `tools/world_history.py`, case-insensitively, for the private
  block's name.
- So: no `31` anywhere in `records.py`, docstrings included (no `2026-10-31` example; take the last day from
  `months.period_end`). Do not copy spec §2's "Nothing is read from `oracle` ..." into a docstring or the CLI help.

**P8 (Low). `world/__init__.py` says "Standard library only".**
- *Why.* `__init__.py:3-4` says so, but `records` imports `assetops_contracts.canonical`, which is itself standard
  library only. The spec changes only the module list.
- *Proposed.* Reword that sentence too, for example "standard library and `assetops_contracts` only".

**P9 (Low). Value types are wider than the spec says.**
- *Why.* `spec.md:101-104` says the view admits only an int or decimal text. `view.py:21-44` admits any string, dict
  or list: Embakasi's actual `note` is free text. Only written fields are converted, so the fixture is fine, but a
  non-number in a written field would raise a bare `InvalidOperation`.
- *Proposed.* `DS1B_NUMBER <tenant>/<site>/<month> <side> <field>` for a written field that is not an int or a
  decimal, and `DS1B_AS_OF` when `as_of` is not a date.

**P10 (Low). Negative money text.**
- *Why.* §3 defines a negative text only for an ADJUSTMENT. Python's `c // 100` and `c % 100` give `"-2.50"` for
  −150 cents. October view values may be negative (Kisiwa's `contribution` is −250.0, though it is not written).
- *Proposed.* Define `text(c)` as `"-" + text(-c)` for any negative `c`.

**P11 (Low). The unwritten list's `site`.**
- *Why.* The spec does not say whether `site` is the name (`Room A · Mwea`, as history keys use) or the code. The
  choice affects the sort order and `unwritten.json`.
- *Proposed.* Use the Site code, as the record IDs do.

**P12 (Low). The view and the 2a points to confirm when 2a lands.**
- `build_records` applies `ManifestView.from_document` itself. It is idempotent (`view.py` docstring), so a caller
  passing a raw manifest cannot reach a private key; this supports probe P1.
- A BUDGET_LINE carrying `site_code` relies on 2a §6.2 making `site_code` optional for that kind. T1 catches it if
  not.
- `zoneinfo` depends on system tzdata (and on `PYTHONTZPATH`). This is acceptable for Nairobi.
