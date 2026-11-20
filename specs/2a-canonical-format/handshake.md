# 2a handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Reviewer (Claude), 2026-11-20, at `2a56ed99c`. Read: `spec.md`, `rulings.md`, `reviewer-guide.md`, the BW1
rulings, the fixture, the manifest's `factor_map` and `empty_states.leaf_sources`, `integration-source-to-canonical-design.md`
§6.1, `tools/select-tests.py`, `tools/run-backend-suite-in-container.sh`. Checked by script: the §5 table's 73 IDs and
their structure keys equal the manifest's `factor_map` keys exactly (77 key-entries, 4 shared IDs); no difference. The
fixture parses as JSON, has no JSON number in a decimal place, and covers all 14 kinds in 13 of the 17 source types.

**The decision queue (§13).** Q1 is real (the owner's W1 gate; nothing for the handshake). Q2 is real and correctly
deferred: the literal-unit cases are `3B1`'s. Q3 is real; the answer is sound, with one cost the spec should state: a
mistyped node ID in a budget line passes the format and is only caught at `3A2`'s intake against the registry.

Severity: **High** blocks coding until answered; **Medium** changes what is built or tested; **Low** is a wording or
coverage fix. **(done)** marks a question whose answer changes what counts as done.

- **R1 (High, done) — §9 commands, §10 Q4-Q5: the contracts tests never run at merge or in a later slice.**
  `tools/select-tests.py` only selects files under `backend/tests` (`TEST_DIR`), so a change to `contracts/` selects
  nothing and a change to the manifest (`Docs/*` is `NO_BACKEND`) selects nothing. The merge runner
  (`tools/run-backend-suite-in-container.sh:93`) targets `backend/tests` only. So T1-T10 run once, in this slice, by
  hand, and never again: not when `DS1b` or `3A1` touch the package, not when the pack edits the manifest's
  `factor_map`. For a protected seam (D-2A.2) whose whole guarantee is "the store, the registry and the generator
  cannot drift", that leaves the guarantee unguarded. *Proposed:* this slice either (a) puts the two test files in
  `backend/tests/test_2a_canonical_*.py` (they then run in every merge tier; the container already copies `contracts/`
  and `Docs/demo-sprint/` and has `pyyaml`), or (b) adds `contracts/tests` to the merge runner's default targets and
  teaches `select-tests` to select `contracts/tests` for a `contracts/` change and the parity test for a change to
  `demo-site-scenario-manifest.yaml`. (a) is the smaller change and needs no tool edit; it widens §10 Q6's file list.
  Either way §10 gains "the canonical tests are in the merge tier", with the evidence.

- **R2 (High, done) — §6.5, §6.6: decimal round trip is not exact as specified.** `CanonicalRecordV1.amount` is
  `tuple[Decimal, str]` (value, currency); there is no slot for "the original text of each decimal". If the
  implementer prints with `str(Decimal)`, inputs inside the allowed bound come out in scientific notation:
  `str(Decimal("0.0000001"))` is `1E-7` and `str(Decimal("0.0000000"))` is `0E-7` (checked; both adjusted -7, inside
  [-12, 12]), which fail §6.3's own decimal pattern on re-parse. Also `Decimal("1.50") == Decimal("1.5")`, so P4's
  "re-parse equals r" passes even when the bytes changed: object equality is weaker than byte equality. *Proposed:*
  state that the canonical text of a decimal is `format(d, "f")` (exact for every plain-notation input: keeps `1.50`,
  prints `0.0000001`), never `str(d)`; make T5 assert bytes, not only object equality; add to the fixture or T5 a
  value with adjusted exponent below -6 (`"0.0000001"`), one at -12, one at +12, and `"1.50"`. Settle it now: under
  D-2A.2, fixing the canonical text after merge is a version 2.

- **R3 (Medium, done) — §6.3, §6.4, §6.7: the code and path of many refusals are not fixed, but T6 asserts the full
  text.** Unassigned cases: `records` over 10,000; an element of `records` that is not an object (row outcome or
  envelope failure; path `batch.records[3]` or `record`?); a missing `format_version` (`CANONICAL_FIELD` or
  `CANONICAL_VERSION`?); a missing `kind`; an integer out of range (`pages` 0 or 10,001: §6.3 says `CANONICAL_TYPE,
  CANONICAL_SIGN`); a string over its length (`source_version` > 64, `band` > 40); `bands` empty or over 24;
  `receipts` empty; `soc_pct` over 100; a wrong JSON type for an object-valued key (`amount: "x"`); a `subject.kind`
  the kind does not allow (`ENUM` or `FORBIDDEN`?); a `site_code` or tenant slug not matching its pattern (`REF`?);
  and, inside "the top-level key set", whether an unknown key is reported before a missing one. Each becomes part of
  v1 under D-2A.2. *Proposed:* a short list after §6.7 giving each check its code; suggested: lengths and patterns
  of refs, codes and slugs `CANONICAL_REF`; integer and array-size ranges `CANONICAL_RANGE`; wrong JSON type
  `CANONICAL_TYPE`; disallowed subject kind `CANONICAL_ENUM`; missing `format_version` `CANONICAL_FIELD`; unknown keys
  before missing keys, each in sorted key order; a non-object record element is that record's outcome,
  `CANONICAL_TYPE record`.

- **R4 (Medium, done) — §6.2: which top-level keys are required?** The list names eleven keys but says which are
  optional only for `site_code`. Not stated for `source_record_id`, `source_version`, `clocks`, `body` (presumably
  required), or how `subject`, `status`, `amount` and `quantity` follow the kind's row. *Proposed:* one line:
  "`format_version`, `kind`, `source_record_id`, `source_version`, `clocks` and `body` are required for every kind;
  `site_code`, `subject`, `amount`, `quantity` and `status` follow the kind's row."

- **R5 (Medium, done) — §4, §5, §6.3: regular expressions must be full-string, ASCII matches.** With Python's
  `re.match` and `$`, `FACTOR_ID_PATTERN` accepts `"diesel\n"` (checked); `\d` matches non-ASCII digits, so the period
  pattern `^\d{4}-(0[1-9]|1[0-2])$` accepts `"٢٠٢٦-01"` (checked; `date.fromisoformat` rejects such text for dates, but a
  period is checked by pattern only). Affected: factor ID, tenant slug, `site_code`, currency, `document_sha256`,
  period, local time, unit text. *Proposed:* every pattern is applied with `re.fullmatch` and `re.ASCII` (or `\Z` and
  `[0-9]`), and `FACTOR_ID_PATTERN` is published that way; T6 gains a trailing-newline factor ID and a
  non-ASCII-digit period.

- **R6 (Medium) — §6.3 ref, §6.6: a lone surrogate passes parsing and crashes the output.** `json.loads('"a\\ud800"')`
  gives a string with a lone surrogate; it passes the ref rule (no character below U+0020, no U+007F), and
  `to_canonical_json` then raises `UnicodeEncodeError` on encoding to UTF-8 (checked). §6.7's "nothing but
  `CanonicalRefused` escapes" covers only the parsers, and T7 only `parse_record`. *Proposed:* a ref (and every
  string) containing a code point U+D800-U+DFFF is `CANONICAL_REF`; say whether C1 controls (U+0080-U+009F) are
  refused, and that "whitespace" means `str.strip()`'s set; T7 also calls `to_canonical_json` on every record that
  parsed. State that refs are compared as given, with no Unicode normalisation (NFC and NFD forms are different refs).

- **R7 (Medium) — §6.6: duplicate JSON keys are silently lost.** `parse_record` takes an already-decoded object, and
  `json.loads('{"value":"1","value":"2"}')` keeps the last value (checked), so a row with a duplicated key is accepted
  with one of its values and the digest hides it. *Proposed:* either add `loads_canonical(data: bytes)` (decodes with
  an `object_pairs_hook` that refuses a repeated key as `CANONICAL_DUPLICATE` with the key's path) as the one public
  entry for bytes, or state that the duplicate-key check is the intake's (`3A2`) and name it there. The first is
  cheaper now.

- **R8 (Medium, done) — §6.6: the canonical JSON shape of a `BatchResult`, and its equality.** `CanonicalBatchV1` has
  no `format_version` field, yet re-parsing the output needs `"format_version": 1` in the envelope; not stated.
  "Parsing the output again gives an equal object" is false whenever a record was refused (the refused outcome is
  dropped, and `CanonicalRefused` instances compare by identity). And `batch_digest` of a batch with refused rows
  equals that of the batch without them. *Proposed:* state the envelope keys written (`format_version`, the five
  fields, `records`); restrict the round-trip clause to "the valid records re-parse to equal records, in order, with
  the same bytes"; say explicitly that the batch digest covers valid records only.

- **R9 (Medium) — §4: unit text with no numerator, and whether `parse_unit` accepts only canonical text.** The grammar
  admits `1/KWH`, but the text rule says only "`1` for `ONE`", leaving `str(ONE / KWH)` undefined. The grammar also
  admits `KWH/KWH` and `MONEY*HOUR/KWH`, which P5 and T8 expect refused. *Proposed:* "a unit with no positive exponent
  writes `1` as its numerator (`1/KWH`)", and "`parse_unit` refuses any text that is not `str()` of the unit it
  denotes (dimensions in name order, no dimension on both sides)".

- **R10 (Medium) — §6.2, §8: quantity units and catalogue units are two vocabularies with no mapping.** Records carry
  `kWh`, `kW`, `L`, `crate`, `crate_day`; leaves carry `KWH`, `KWH/HOUR`, `L`, `1`, `DAY`. `3B3` reads by factor ID and
  must turn one into the other; with no mapping in the format, `3A2`, `3B3` and `DS1b` will each write their own, which
  is the drift the format exists to stop. *Proposed:* add `QUANTITY_UNITS: Mapping[str, Unit]` (`kWh` KWH, `kW` KW,
  `L` L, `crate` ONE, `crate_day` DAY) and `BAND_UNITS` (`per_kWh` MONEY/KWH, `per_crate_day` MONEY/DAY, `per_L`
  MONEY/L) to the public API, with a T8 line.

- **R11 (Medium) — §6.4, §5: `penalty_rate` has no field to come from.** The manifest fills `penalty_rate` (EV,
  `ZERO_WHEN_HELD`, not option-only) from family `DOCUMENT`, "CONTRACT_DOCUMENT (service contract penalty term)", but
  the v1 `CONTRACT_DOCUMENT` body holds no term or amount (hash, counterparty, type, pages, parties). `contract_rate`
  and `contract_crate_days` (CC, option-only) are in the same position, and the design's §6.1 lists a "term" for
  contract documents. T3 checks only the COMMERCIAL_RECORD and OPERATIONAL_RECORD families, so it cannot catch this.
  *Proposed:* either add an optional `terms` array to `CONTRACT_DOCUMENT`'s body (`{factor_id, value, currency?}`, the
  budget line's value shape) so a document can carry the numbers a leaf reads, or rule that `penalty_rate` and the
  contract leaves are DECLARED from a reviewed document by `3B6`/`9e` and say so in §5. Either way extend T3 to the
  `DOCUMENT` family. Under D-2A.2 the first choice is a version 2 if made later.

- **R12 (Low) — §6.4: instants compare as moments; equal moments may have different text.** `departure_at` after
  `return_at` and ticket times "not before `occurred_at`" must compare aware datetimes, not text (offsets may differ in
  one record). Two submissions of one moment with different offsets give different bytes and digests. *Proposed:* say
  "compared as instants"; accept that digests are of the text as sent (the format never converts zones, §8); add one
  T6 case where text order and instant order differ.

- **R13 (Low) — §6.6: the duplicate rule when the first copy was refused.** "The first stays valid" does not say what
  happens when the first record with a key is refused and the second is fine, or whether the source-type check runs
  before the duplicate check. *Proposed:* duplicates are counted among records that parsed and passed the source-type
  check; a refused record does not claim its key.

- **R14 (Low) — the fixture and T5 coverage.** The fixture has no batch for `storage_rate_card`, `tariff_sheet`,
  `electricity_bill` or `penalty_statement`, so no example shows a `per_crate_day` or `per_L` band, a cold-room
  electricity CHARGE, or a `PENALTY` expense. *Proposed:* one small batch per missing source type, so T5 shows every
  source type of §7 parses (the gate's first question) and §10 Q1 has evidence per source type.

- **R15 (Low) — §6.4 tariff bands.** Local band times are ambiguous on a daylight-saving day. None of the three
  demonstration time zones observes it. *Proposed:* one sentence, "bands are wall-clock times; a daylight-saving day is
  the reader's (`3B3`) to resolve", no code.

## Implementer pre-flight questions

(none yet)

## Implementer pre-flight

Implementer (Claude), 2026-11-20. Pre-flight of `spec.md` rev 1 against `main` at `e3052032d`, read-only; no code.
**(done)** marks an answer that changes what counts as done. Each item has its evidence and a proposed answer.

**Checked and true as the spec says:** `contracts/pyproject.toml` has `dependencies = []`; the venv has pytest
9.2.0 and pyyaml 6.0.3 (Python 3.12.16); `contracts/tests` runs on its own with no conftest (6 passed); the manifest
path resolves from `parents[2]`; `factor_map` holds 73 IDs, and for each structure key the set equals spec §5's
rows (4 shared IDs, 9 money leaves, money flag equals unit `MONEY` on every row); T3 passes on today's
`leaf_sources` with spec §6.4's kinds; the fixture has 13 batches and all 14 kinds; tenant slug rule
`0001_foundation_identity.py:54`; `site.timezone` `0001:67`; the DS1 bound `world/history.py:57`;
`world/leaves.py`, `source_envelope_v4.py` and `operational_records.py` exist; `dependency-direction.ps1:141-165`
scans `contracts/`; `tracked_evidence.py` allows a `fixtures/` folder.

- **P1 (done) The spec folder is not on `main`.** §0 says branch off `main` at or after `56300a810`, but
  `specs/2a-canonical-format/` (the fixture source, the packet's home) exists only on `task/build-wave1-specs`
  (`git ls-tree main specs/` has no such folder; `git merge-base main 2a56ed99c` is `56300a810`). A build branch cut
  from `main` cannot `cmp` the fixture or hold the packet. *Proposed:* the coordinator merges `task/build-wave1-specs`
  into `main` when the handshake closes, and the build branch is cut after that merge. §0 says so.
- **P2 (done) `select-tests` does not select "no backend file".** A non-Python file under `contracts/` makes it
  select everything (`tools/select-tests.py:178-180`). Measured with `--files`: with the fixture, `mode: full (510 of
  510) ... full because: contracts/tests/fixtures/canonical_v1_examples.json (run-time data the import graph cannot
  trace)`; without it, `mode: none`. *Proposed:* §9 expects "full, for the fixture alone". The packet cites that output
  and does not run the full suite, because no backend module reads the file. Exempting `contracts/tests/fixtures/*`
  would be a change to `tools/`, so it is a separate small item and not part of 2a.
- **P3 Nothing runs `contracts/tests` after the merge.** No runner, check-all mode, `select-tests` (`TEST_DIR =
  "backend/tests"`, `select-tests.py:37`) or full-suite tier collects `contracts/tests`. Grepping `tools/`,
  `backend/TESTING.md` and `backend/pyproject.toml` for `contracts/tests` finds nothing. So T1 (parity with the
  manifest) would not catch a later manifest edit. *Proposed:* the Architect decides between adding `contracts/tests`
  to check-all's fast mode (a small change to `tools/`, not part of 2a) and recording it as a known risk in the packet.
  2a does not edit `tools/`.
- **P4 (done) The refusal code is not fixed for several cases T6 must assert in full.** §6.3 and §6.7 leave these
  open. *Proposed mapping:*
  - A whole-number violation (`STORAGE_MOVEMENT` quantity `"120.5"`) is `CANONICAL_NUMBER record.quantity.value`.
  - `factor_id` failing `FACTOR_ID_PATTERN` (`"Diesel"`) is `CANONICAL_FACTOR record.body.factor_id`.
  - An integer or bounded decimal outside its range (`pages` 0 or 10,001; `soc_pct` 100.5) is `CANONICAL_SIGN`,
    the one code for "outside the table's range".
  - Every pattern-checked identifier fails as `CANONICAL_REF`: `site_code`, `tenant_code`, `document_sha256`, and a
    ref over its own length limit (`band` 40, `reason_code` 40, `source_version` 64).
  - A `subject.kind` the kind does not allow (`VEHICLE` on a `CHARGE`) is `CANONICAL_ENUM record.subject.kind`.
    `subject` present where the table says F is `CANONICAL_FORBIDDEN record.subject`. A `status` outside the kind's
    enum is `CANONICAL_ENUM`.
  - A quantity unit wrong for the kind or `line_type` (`DEMAND` with `kWh`), and a band `unit` outside the three, are
    `CANONICAL_UNIT`.
  - A currency failing `^[A-Z]{3}$`, in `amount` or in `body.currency`, is `CANONICAL_CURRENCY`. On
    `STORAGE_MOVEMENT`, `currency` without `rate` is `CANONICAL_FORBIDDEN`, and `rate` without `currency` is
    `CANONICAL_FIELD record.body.currency`.
  - A duplicate band name is `CANONICAL_DUPLICATE record.body.bands[n].band`. `acknowledged_at` or `restored_at`
    before `occurred_at` is `CANONICAL_RANGE`. `restored_at` absent with status `RESTORED` is `CANONICAL_FIELD`.
  - On the envelope: an unknown `source_type` is `CANONICAL_SOURCE_TYPE batch.source_type`; a batch that is not an
    object is `CANONICAL_TYPE batch`; `records` that is not an array is `CANONICAL_TYPE batch.records`; more than
    10,000 records is `CANONICAL_RANGE batch.records` (add "batch size" to `CANONICAL_RANGE`'s definition).
- **P5 (done) The order inside "the top-level key set" and "the body's keys" is not fixed.** §6.6 does not say
  whether an unknown key or a missing required key is reported first, or in what order several unknown keys are
  reported. It also does not say whether an absent required top-level field is reported at the key-set step or at its
  own step. *Proposed:* the key-set step reports only keys that are present and not allowed (`CANONICAL_FORBIDDEN`,
  the first in sorted key order). An absent required key is reported at its own step, in §6.6's order
  (`CANONICAL_FIELD`). The body follows the same rule: forbidden keys first (sorted), then each field in table order.
- **P6 The path of a refusal inside a batch.** §6.6 gives record-relative paths (`CANONICAL_SOURCE_TYPE
  record.kind`), while §6.5's examples include `batch.records[3]`. *Proposed:* every record outcome carries a
  `record.`-relative path, including a non-object element (`CANONICAL_TYPE record`). No v1 refusal produces
  `batch.records[n]`, so that example is removed from §6.5.
- **P7 Canonical unit text with no numerator, and non-reduced input.** §4's rule gives `"/DAY"` for `ONE / DAY`,
  which its own grammar refuses. The grammar also admits non-reduced text (`KWH*L/KWH`). *Proposed:* the numerator is
  `1` when no exponent is positive (`1/DAY`). `parse_unit` accepts a text only when `str(parse(text)) == text`, so
  out-of-order, non-reduced and repeated forms all raise `ValueError("CANONICAL_UNIT <text>")`.
- **P8 T4's terms are not the manifest's text.** Seven of the fourteen listed products do not occur in the manifest
  as written. For example, the manifest has `battery_throughput_kwh * wear_rate` (manifest line 823) and
  `departures_missed * penalty_rate` (863); `spare_bus_nights * penalty_rate` does not occur. *Proposed:* T4
  hand-lists the fourteen terms and checks units only. It does not assert that they occur in the manifest.
- **P9 `leaves_of("COLD_CHAIN")` order.** "The table's order" puts `outstanding`, `staff`, `liability` and
  `period_days` at their MG rows (10, 19, 27, 28), before `crate_days`, which differs from the manifest's
  `factor_map` order. The sets are equal (checked). *Proposed:* keep the table's order (T1 compares sets) and note it
  in the docstring so DS1b does not rely on manifest order.
- **P10 (done) Finish bookkeeping falls outside §10 Q6's scope.** The standing brief requires a `.ai/state/` entry and
  its `index-*.md` line, plus the spec's status. The specs have no `Status:` line; the status lives in the
  `specs/INDEX.md` row (line 72). Q6 and reviewer-guide check 2 allow only `contracts/` and the packet. *Proposed:*
  those three bookkeeping files are allowed and are excluded from the scope check, and "Status: in_review" means the
  `specs/INDEX.md` row.
- **Estimate.** 1.5 units holds if P4 and P5 are ruled before code: the per-kind table as data and the 17-code mapping
  are the bulk, and the open mappings are the main risk of rework at review.
