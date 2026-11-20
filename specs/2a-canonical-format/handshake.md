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
