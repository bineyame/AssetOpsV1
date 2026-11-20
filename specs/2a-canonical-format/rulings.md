# 2a rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-7.md`. Handshake
answers are added below under "Handshake answers (round 1)" and folded into `spec.md`.

## D-2A.1 The format lives in `assetops_contracts.canonical`, standard library only

- **Ruling.** One package in the neutral contracts, as D-DS1.1 recommended.
- **Why.** The store (backend) and the generator (simulator) must share one definition, and the dependency-direction
  guard forbids either importing the other (`tools/checks/dependency-direction.ps1`). The contracts package is the
  only place both may import, and it has no dependencies by design (`contracts/pyproject.toml`).

## D-2A.2 The package is a protected seam; a change is a new format version

- **Ruling.** From this unit on, what counts as a valid version-1 record, and every leaf ID and unit, change only by a
  version 2 beside version 1.
- **Why.** Records are stored with their format version (`3A1`). Editing version 1 in place would silently change
  what earlier intake accepted. Design D1 expects a version 2 when the first operator sample is pinned.

## D-2A.3 Leaf IDs are the manifest's `factor_map` keys; filling rules stay in the registry

- **Ruling.** The 73 IDs are exactly the `factor_map` keys of the three structure keys. `filled_by` and `absent` are
  not in the catalogue.
- **Why.** `integration-design.md` §3 names `factor_map` as the starting set, and the evaluator and the independent
  model already use these names, so the registry's parity with the demonstration (3B) needs no renaming. Filling
  rules are the registry row's fields (`decision-loop-specification.md` §3), which `3B1` and `3B6` declare; putting
  them here would give two owners.
- **Shared IDs.** `staff`, `outstanding`, `liability` and `period_days` appear in two verticals with the same quantity
  and unit, so each is one ID ("a quantity has one ID"). `om`, `maint` and `maintenance` stay three IDs: renaming
  them would break evaluator parity, and whether they are one quantity is a version-2 question.

## D-2A.4 Six dimensions; counts dimensionless; nights are days

- **Ruling.** `KWH`, `L`, `MONEY`, `DAY`, `HOUR`, `MINUTE`. Counts (assets, buses, chargers, crates, batches, visits)
  are dimensionless. A night, a bus-night and a missed departure are `DAY`.
- **Why.** The registry's start-up check refuses a structure whose units do not compose (`decision-loop-specification.md`
  §3). Checked against every manifest node: with counts as dimensions, `asset_days_total - asset_days_out_of_service`
  and `nights_in_period = record.nights | period_days` would not compose. With these six they do, except where a
  literal `0` or `1` sits inside `min`, `max` or a subtraction (`shortfall_backed`, `buses_short_per_night`,
  `contribution = 0 - cost_to_serve`). How a literal takes a unit is the expression language's rule, so `3B1` rules
  it, not the format.

## D-2A.5 A budget line may name a node

- **Ruling.** `BUDGET_LINE.factor_id` is any ID with the factor-ID syntax. The currency rule is enforced here only for
  catalogue leaves; nodes are checked at intake against the registry.
- **Why.** B2 accepts a target declared above leaf level and stops attribution there (`decision-loop-specification.md`
  §5). The format cannot know node IDs before `3B1` exists.

## D-2A.6 `SERVICE_TICKET` is an operational record; `BUDGET_LINE` replaces the old `PLAN_LINE`

- **Ruling.** The service ticket's canonical body is defined here, with store family OPERATIONAL_RECORD. The
  operator's budget lines are kind `BUDGET_LINE`.
- **Why.** The manifest's `leaf_sources` and `integration-design.md` §4 put tickets with the version-chained
  operational records, not the money store. `PLAN_LINE` in `integration-source-to-canonical-design.md` §6.1 predates
  OD-6, under which "plan" names only the new construct. `integration-design.md` §3 already says `BUDGET_LINE`.
- **Not in version 1:** QA inspection notes and the asset register. No leaf reads them (the asset register fills a
  DECLARED leaf through Site configuration). They come with a version 2 if a leaf needs them.

## D-2A.7 Readings and fuel records keep their formats

- **Ruling.** `EXISTING_FORMATS` points at `source_envelope_v4` and `operational_records`. Neither changes.
- **Why.** First write wins suits telemetry, and the fuel records' version chain already works. The design changes
  only bills and their kin (`integration-design.md` §4).

## D-2A.8 `world/leaves.py` switches in DS1b, not here

- **Ruling.** 2a does not edit the simulator.
- **Why.** DS1's history must stay byte-identical, and `world/leaves.py`'s money set differs from this catalogue's
  (it holds `energy_cost` and `total`, which are nodes or stated totals, and lacks the option-only leaves
  `collection_cost` and `handling`). DS1b makes the switch with its parity test. Keeping 2a inside `contracts/` also
  keeps it clear of DS1m.

## D-2A.9 Exact decimal text, with the DS1 magnitude bound

- **Ruling.** Decimals are JSON strings in plain notation, at most 32 characters, with the adjusted exponent within
  [-12, 12]. No JSON number is accepted for a decimal.
- **Why.** The design requires exact amounts (`integration-design.md` §3, "exact decimal text"), and the strategy's
  scale foundation forbids floats (strategy §7). The bound is the one DS1 already ruled, so the generator and the
  format refuse the same inputs.

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling.

### Highs

- **R1 / P3 (High): the tests move to `backend/tests`; no tool changes.** Option (a). The files are
  `backend/tests/test_2a_canonical_v1.py` and `backend/tests/test_2a_canonical_manifest_parity.py`, and the fixture is
  `backend/tests/fixtures/canonical_v1_examples.json`. The merge's full fast tier collects `backend/tests`, so every
  merge runs them: one that edits `contracts/`, and one that edits the manifest's `factor_map`. `select-tests` also
  selects them for any later `.py` change in `contracts/`, because they import the package. Option (b) would change
  `tools/` (the runner, `select-tests` and check-all) for one package. The container already has `contracts/`,
  `Docs/demo-sprint/` and `pyyaml`. **New ruling D-2A.10.**
- **P2: the full selection caused by the fixture.** `select-tests` answers "full" because of the fixture (run-time
  data). The packet cites that output and does not run the full suite: no backend module reads the fixture, and the
  merge runs the full fast tier anyway. That fast tier is now the evidence for §10 Q4 and Q5. Exempting fixtures in
  `tools/select-tests.py` is a separate small tools item, not part of 2a.
- **R2 (High): the canonical text of a decimal is `format(d, "f")`.** It is never `str(d)`. Every accepted input is in
  plain notation, so `format(Decimal(text), "f") == text` for every accepted text: `"1.50"` stays `1.50` and
  `"0.0000001"` stays `0.0000001`. No separate kept text is needed, so §6.5's "original text" clause is removed.
  - T5 asserts bytes, not only object equality.
  - T5 adds a value list that each round-trips to the same bytes inside an ADJUSTMENT amount: `"1.50"`,
    `"0.0000001"` (adjusted -7), `"0.000000000001"` (adjusted -12), `"1000000000000"` (adjusted +12) and `"-108.00"`.
  - Two values are refused with `CANONICAL_NUMBER`: `"0.0000000000001"` (-13) and `"10000000000000"` (+13).
  - This is final for version 1 (D-2A.2).

### Mediums and Lows

- **R3 / P4 / P5 / P6: the refusal mapping is fixed in spec §6.8.** Its main rules are below.
  - **The key set.** Unknown keys are reported first, as `CANONICAL_FORBIDDEN`, the first in sorted key order. A
    missing required key is reported at its own step, as `CANONICAL_FIELD`.
  - **`format_version`.** Absent or not 1 is `CANONICAL_VERSION`.
  - **Ranges, bounds and sizes** are `CANONICAL_RANGE`; `CANONICAL_SIGN` is only for a negative value, or zero where
    "positive" is required. This takes R3's proposal over P4's.
  - **A whole-number breach** (`"120.5"` crates) is `CANONICAL_NUMBER`.
  - **Identifier patterns and lengths** are `CANONICAL_REF`, except `factor_id`, which is `CANONICAL_FACTOR`.
  - **A non-object record element** is that record's outcome, `CANONICAL_TYPE record`.
  - **Every record outcome's path starts at `record`.** No v1 refusal produces `batch.records[n]`.
- **R4: adopted.** `format_version`, `kind`, `source_record_id`, `source_version`, `clocks` and `body` are required for
  every kind. The others follow the kind's row.
- **R5: adopted.** Every pattern is ASCII and is applied with `re.fullmatch`. `FACTOR_ID_PATTERN` is published compiled
  with `re.ASCII` and documented as used with `fullmatch`. T6 gains `"diesel\n"` and a period written in Arabic-Indic
  digits.
- **R6: adopted.**
  - Any string anywhere containing a code point in U+D800 to U+DFFF is `CANONICAL_REF` at its path.
  - A ref also refuses U+0080 to U+009F.
  - "Whitespace" means `str.strip()`'s set.
  - Refs are compared exactly as given, with no Unicode normalisation.
  - T7 also calls `to_canonical_json` on every record that parsed.
- **R7: adopted, as `loads_canonical(data: bytes) -> object`.** It is the one public entry for bytes.
  - Bytes that are not UTF-8 or not JSON: `CANONICAL_TYPE json`.
  - A key repeated in one object: `CANONICAL_DUPLICATE json.<key>`. The hook does not know the full path, so the key
    alone is the path.
  - `NaN`, `Infinity` or `-Infinity`: `CANONICAL_NUMBER json`.
  - Intake (`3A2`) calls it on every upload.
- **R8: adopted.**
  - The canonical batch envelope holds `format_version` (1), `tenant_code`, `source_type`, `source_system`,
    `provenance`, `produced_at` and `records`.
  - Round trip means the valid records re-parse to equal records, in order, with the same bytes.
  - `batch_digest` covers the valid records only, and the docstring says so.
- **R9 / P7: adopted.**
  - A unit with no positive exponent writes `1` as its numerator (`1/DAY`).
  - `parse_unit` accepts a text only when `str(parse_unit(text)) == text`. Out-of-order, repeated, non-reduced and
    both-sides forms all raise `ValueError("CANONICAL_UNIT <text>")`.
- **R10: adopted.** `QUANTITY_UNITS` and `BAND_UNITS` are public mappings to `Unit`, in `units.py`, with a T8 line:
  - `QUANTITY_UNITS`: `kWh` is `KWH`, `kW` is `KW`, `L` is `L`, `crate` is `ONE`, `crate_day` is `DAY`;
  - `BAND_UNITS`: `per_kWh` is `MONEY/KWH`, `per_crate_day` is `MONEY/DAY`, `per_L` is `MONEY/L`.
- **R11: the contract leaves are not v1 record fields.**
  - `penalty_rate` is family DOCUMENT. Its value comes from a person's reviewed extraction rows, which are the rights
    register (`integration-source-to-canonical-design.md` §6.3) built by `9a`: a store and contract of their own, not
    a commercial record. The same holds for the remedy and notice terms.
  - `contract_crate_days` and `contract_rate` are option-only: an option's parameters supply them.
  - So `CONTRACT_DOCUMENT` stays the document's identity record. This does not force a version 2, because the
    extracted rows were never going to be part of this format.
  - T3 is extended to the DOCUMENT family: each such row names `CONTRACT_DOCUMENT`, a v1 kind, as its source.
  - Spec §5 states this.
- **R12: adopted.** Instants are compared as moments. Digests are of the text as sent. T6 gains a case where the text
  order and the moment order differ: `return_at` `2026-10-15T00:30:00+03:00` against `departure_at`
  `2026-10-14T22:00:00+00:00`, which is accepted.
- **R13: adopted.** Duplicates are counted only among records that parsed and passed the source-type check, so a
  refused record does not claim its key. The order is parse, then source type, then duplicate.
- **R14: adopted.** The fixture gains four batches, so all 17 source types parse: a `storage_rate_card`
  (`per_crate_day`), a `tariff_sheet`, a cold-room `electricity_bill` and a `penalty_statement`. There is still no
  `per_L` band, so T6 covers that unit.
- **R15: adopted.** One sentence: bands are wall-clock times, and a daylight-saving day is the reader's (`3B3`) to
  resolve.
- **The decision queue's Q3 cost: stated.** A mistyped node ID in a budget line passes the format and is refused only
  at intake, against the registry (`3A2`).
- **P1: adopted.** The coordinator merges `task/build-wave1-specs` into `main` when this round closes. The build branch
  is cut from `main` after that merge.
- **P8: adopted.** T4 checks units only, on a hand-listed set of terms, and does not assert that they occur in the
  manifest. The list now uses the manifest's own terms: `battery_throughput_kwh * wear_rate` and
  `departures_missed`-shaped `spare_bus_nights * penalty_rate` kept as a unit check only.
- **P9: adopted.** `leaves_of` keeps the table's order, and the docstring says it is not the manifest's order.
- **P10: adopted.** The `.ai/state/` entry, its index line and the `specs/INDEX.md` status row are allowed, and the
  scope check excludes them.
- **Estimate.** 1.5 units still holds. The mapping is now fixed, and `loads_canonical`, the unit maps and the four
  fixture batches are small.

**Open after round 1:** none. One owner item remains: the approval of P2. If it is not given when this round closes,
lane B builds `DS2` first (D-BW1.1).

## D-2A.10 The canonical tests live in `backend/tests`

- **Ruling.** The canonical tests are `backend/tests/test_2a_*.py`, with their fixture in `backend/tests/fixtures/`.
- **Why.** They are the only guard on a protected seam and its parity with the manifest. Only `backend/tests` runs at
  every merge.

## Review round 1 answers (2a, 2026-11-20; `review.md`, REVISE: 2 Mediums, 3 Lows)

Folded into `spec.md` rev 3 (§3, §6.2, §6.3, §6.5, §6.6, §6.8, the new §6.8a, T7, the new T11 and done question 8).
One Sonnet fix round builds them. A verification re-review then checks the named items only.

### Mediums

- **M1: a surrogate key is refused with `CANONICAL_REF` at the container path.**
  - A key holding a code point U+D800 to U+DFFF is refused as `CANONICAL_REF <container path>`, with the key left
    out of the path. In `loads_canonical` the refusal is `CANONICAL_REF json`.
  - Keys are checked for surrogates before unknown, missing and duplicate keys.
  - **The class.** Any other unknown or duplicate key enters a path escaped to ASCII and capped at 64 characters (§6.8a,
    D-2A.11). Every refusal text is then encodable and bounded. This also closes the review's unbounded-path risk.
  - **Tests.** T7 adds key mutations, and asserts that every refusal text encodes as ASCII. T11 adds the full-text
    cases.
- **M2: one order, the root cause first** (§6.8a, D-2A.12).
  - When a controlling value is absent or not in its enum, the fields that depend on it get only their shape checks.
    The controlling field's own refusal is reported at its step.
  - **EXPENSE changes.** Its `quantity` default becomes the undecided state, as CHARGE's does, and its unit check uses
    the unconditional `("L",)`.
  - **The sweep (W6).** Every `_When` default in `_SPECS` follows the rule. The reviewer's list is lines 163-166,
    202, 225, 231, 234-235 and 282. STORAGE `currency` and SERVICE_TICKET `restored_at` are keyed on presence and
    status, which are always decided by then, so they stay.
  - **Tests.** T11 adds the absent and the invalid control case for CHARGE, EXPENSE and CUSTOMER_METER_READ.

### The four filled gaps

The packet records 4 mid-build questions: these four choices should have been raised.
- **Gap 1: ratified.** A quantity unit outside the five is `CANONICAL_UNIT`.
- **Gap 2: ratified, with the index stated.** An array fault points at the element. An overlap points at the later
  band's `from`, where "later" is by `from` order and the index is that band's input index.
- **Gap 3: settled by M2.**
- **Gap 4: ratified.** `FORMAT_VERSION` is defined in `records_v1.py` and re-exported. Spec §3 is amended.

### Lows

- **Low 1: adopted.** T11 adds one trailing-junk case per pattern site: site, tenant, currency, sha, period, date,
  time and instant.
- **Low 2: adopted.** T11 adds an NFD ref that round-trips byte-identical and does not equal its NFC form.
- **Low 3, spec text:**
  1. `FORMAT_VERSION`, as gap 4.
  2. **One order for batch and record.** `format_version` comes first, then the key set, then the fields. The batch
     code changes to match (`records_v1.py:743-746`). The reason: a version-2 batch's new keys are expected, so the
     version is the root cause.
  3. **A null on an F row is `CANONICAL_FORBIDDEN`.** The key's presence is the fault. §6.2 now says a null where the
     field is allowed is `CANONICAL_TYPE`. The code already does this.
  4. **R12 is corrected:** digests are of the canonical text. The code is right.

### The residual risks

- **Unhashable records.** Stated in §6.5: callers key records by `record_digest`. `3A2` and `DS1b` follow this.
- **Unbounded paths.** Closed by D-2A.11.
- **Contract freeze.** Stated in §6.8a: the codes and paths are part of version 1, so changing one is a version 2.
  That is why the M1 and M2 fixes land now, before `3A2` and `DS1b` pin them.

## D-2A.11 Key text in refusal paths is ASCII-escaped and capped; surrogate keys are `CANONICAL_REF`

- **Ruling.** As M1.
- **Why.** Intake stores refusals as text. A refusal that cannot be encoded, or a key a megabyte long, would fail
  intake one step downstream, outside the format's own refusal codes.

## D-2A.12 Conditional fields report the root cause

- **Ruling.** As M2.
- **Why.** The operator correcting an export is told what is wrong (the missing category), not a consequence of it
  (a forbidden quantity). One rule across the kinds keeps §6.4 as data.
