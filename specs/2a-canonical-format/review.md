# 2a review, round 1 (discovery, W5): canonical format v1 and the leaf factor IDs

Reviewer: fresh Claude reviewer, 2026-11-20. Branch `task/2a-canonical-format` at `15e803265` (commits
`071096546` tests first, `ce7a7221f` the package, `15e803265` packet and bookkeeping). Read against spec rev 2,
`rulings.md` (D-2A.1 to D-2A.10, handshake round 1), `reviewer-guide.md` rev 2 and `packet.md`. Reran everything in
my own detached scratch worktree at `15e803265`, which I removed afterwards. No database, server or Docker touched.

## Summary (round 1)

- **Verdict: REVISE.** This is a small fix round, two Mediums and no High. The contract is otherwise sound and
  faithful to the spec. I checked the 73-row catalogue against spec §5 by machine (0 mismatches), and all 14
  `KIND_SPECS` rows against §6.4 by hand.
- **M1.** A lone surrogate in an object key is not refused as `CANONICAL_REF`. It goes into the refusal path, and
  `str(refused)` then cannot be UTF-8 encoded. This breaks R6 ("any string anywhere") and will crash intake when it
  writes the refusal.
- **M2.** The packet says the check order for a missing controlling value is "quantity shape only, then the body
  refuses". EXPENSE does not do this: a missing or invalid `category` gives `CANONICAL_FORBIDDEN record.quantity`.
  The kinds are inconsistent, and no test pins the order.
- **Lows.** Three test gaps: `fullmatch` is pinned only for `factor_id`, nothing pins "no normalisation", and nothing
  pins the controlling-value order. There are also spec-text items for the Architect: where `FORMAT_VERSION` is
  defined, whether batch and record order agree, null versus F, and R12's "text as sent".
- **Four filled gaps.** Gaps 1, 2 and 4 are sound and should be ratified. Gap 3 is not implemented as described
  (M2). All four go to the Architect for a ruling, plus a fifth the packet also lists: batch key set before
  `format_version`.
- **Checks.** Focused 2a tests: 162 passed. `contracts/tests`: 6 passed. check-architecture and check-agent-workflow
  both passed. Tests-first commit: 2 collection errors. 11 planted violations: 9 caught, 2 survivors explained (Lows).
- **Merge evidence.** The focused tests are enough. No backend module imports the package, and select-tests
  answers "full" only because of the fixture path.

## Reviewer-guide walk

| Item | Result |
|---|---|
| Gate | The handshake closed (rev 2) and P2 was approved on 20 Nov (spec §0). The first commit `071096546` holds only the two test files and the fixture. Running it gives `ModuleNotFoundError` (2 collection errors; I reran it). The test files are byte-identical from `071096546` to the head |
| Scope | `git diff --name-only 184dc509e 15e803265` lists 5 files in `contracts/assetops_contracts/canonical/`, 2 `backend/tests/test_2a_canonical_*.py` files, the fixture, `packet.md`, the `.ai/state/` entry and its 2 index lines, and the `specs/INDEX.md` row. That matches §0 plus P10, and D-2A.10 is followed. No simulator, manifest or tools change |
| Fixture | `cmp examples-v1.json.txt backend/tests/fixtures/canonical_v1_examples.json` reports no difference |
| §10 Q1 to Q7 | Yes to each, verified independently. Q3 holds apart from M1 (R6 for keys) |
| Catalogue | Parsed spec §5's table and compared it with `LEAF_FACTORS` row by row on ID, structures, `str(unit)`, display and money: **0 mismatches**. 73 IDs. `leaves_of` gives 31, 23 and 23. 9 money leaves. The 4 shared IDs are `outstanding`, `staff`, `liability` and `period_days`. T1 and T2 pass |
| §6.4 as data | `KIND_SPECS` (`records_v1.py:158-297`) is one table, read by one generic parser with no per-kind branch. All 14 rows match §6.4: clocks R and O, site, subject, amount and quantity presence, sign, units, status, and body R and O with lengths, bounds and `after` orderings. The two kind-specific behaviours are named `_rules` (`amount_or_quantity`, `budget_currency`, `bands_overlap`), as §6.4's cross-field rules require |
| Refusal paths | Every row of §6.7 and §6.8 has a T6 case asserting the full `str(refused)`. I checked entry by entry; the list is under "Coverage" below |
| `format(d,"f")` | The writer uses `format(..., "f")` only, at `records_v1.py:799,821,823`. There is no `str(` on a `Decimal`. T5 asserts bytes for the edge list |
| D-2A.10 | Tests are in `backend/tests`. The packet cites select-tests "full" and why the full suite was not run |
| P1 Floats | `8.4` and `"1.5e0"` both give `CANONICAL_NUMBER` (T6) |
| P2 Closed schema | Unknown key at record, body, subject, band and batch level gives `CANONICAL_FORBIDDEN <path>.<key>`. The first unknown key in sorted order wins (T6 `zeta` and `alpha`) |
| P3 Per-row independence | T6 runs `[valid, "not a record", valid]`. The canonical batch omits only element 2 |
| P4a and P4b | Duplicate key gives `CANONICAL_DUPLICATE json.a`. NaN and ±Infinity give `CANONICAL_NUMBER json`. Bad UTF-8, a BOM, truncated input and 100k-deep nesting give `CANONICAL_TYPE json`; I probed the last two myself. `"diesel\n"` and a period in Arabic-Indic digits are refused |
| P4 Round trip | T5 asserts equal records and equal bytes for every record and batch. `1.50` stays `1.50`, `0.0000001` stays plain, and `Z` becomes `+00:00` |
| P5 Units | `parse_unit` refuses out-of-order, repeated, non-reduced, lower-case, space, `^`, `1/1`, double-slash and empty texts (T8) |
| P6 No escape | Reran T7 with seeds 1, 7 and 99 at 3,000 mutations each: 3 passed |
| P7 Neutrality | The only imports are the standard library (`re`, `json`, `hashlib`, `dataclasses`, `datetime`, `decimal`, `types`, `collections.abc`) and `assetops_contracts`. T9 passes |
| P8 Checker independence | The parity test imports only public names and reads the manifest. It copies no list from `factors.py` |

## Exactness (dispatch item 2)

- **Decimals.** `_DECIMAL.fullmatch` is applied first. Then the length is capped at 32, the adjusted exponent must
  be in [-12, 12], and `format(d,"f") == text` is required. That last check means the canonical text is the input
  text, so R2 holds by construction. `-0` and `-0.00` are refused. -12 and +12 round-trip to identical bytes (T5),
  and -13 and +13 give `CANONICAL_NUMBER`. Edge seen: zero written with 13 decimal places (`"0.0000000000000"`,
  adjusted -13) is refused, while 12 places is accepted. That is consistent with the literal bound and harmless.
- **Instants.** They are parsed to aware `datetime` values, and the ordering checks (`departure_at`,
  `acknowledged_at`, `restored_at`) compare the `datetime`, not the text (`records_v1.py:644-653`). The R12 case is
  accepted. When I planted a text comparison, 6 tests failed.
- **`loads_canonical`.** `object_pairs_hook` refuses repeated keys and `parse_constant` refuses NaN and Infinity
  (`records_v1.py:338-364`).
- **Lone surrogates.** In string values they are refused as `CANONICAL_REF` (`_string`, line 370), also inside
  decimals and enums. **Not in keys: see M1.**
- **C0 and C1 controls in refs.** `[\x00-\x1f\x7f-\x9f]` is refused. Whitespace uses `str.strip()`'s set, so U+0085
  is refused too.
- **No normalisation.** Refs are stored and compared exactly as given (correct; Low 2 covers the missing test).
- **Patterns.** Every pattern is compiled with `re.ASCII` and applied with `fullmatch`. The two `search` uses are
  for the banned-character classes, where `search` is correct.

## Coverage (dispatch item 3)

- **Kinds and source types.** 14 kinds and 17 source types, one fixture batch per type, 23 records (T5 and T10).
- **Leaf IDs.** The 73 IDs equal the manifest's `factor_map` as sets per structure key (T1). The 4 shared IDs are
  one `Factor` each (T2). There are 9 money leaves.
- **Unit maps.** `QUANTITY_UNITS` and `BAND_UNITS` match R10 exactly (T8).
- **`penalty_rate`.** It is in the catalogue as `MONEY/DAY`, family DOCUMENT. It is not a field of any v1 body; I
  grepped `KIND_SPECS`. The docstring and T3's DOCUMENT row, which names `CONTRACT_DOCUMENT`, carry R11.
- **§6.8, row by row.** Each row has a T6 case with the full text:
  - key sets: record, body, subject, band, batch and clocks;
  - required key absent;
  - `format_version` for a record and for a batch;
  - `kind` absent and `kind` not a v1 kind;
  - wrong JSON type, with a decimal place holding a non-string giving NUMBER;
  - a non-object record element;
  - a batch that is not an object, and `records` that is not an array;
  - range limits: 10,001 records, 0 and 25 bands, empty `receipts`, `pages` 0 and 10,001, `soc_pct` 100.5;
  - signs;
  - a whole number breached, and decimal syntax, length and exponent;
  - ref patterns: tenant, site, sha, `band` over 40, `reason_code` over 40, `source_version` over 64, surrogates;
  - `factor_id`, and the currency rule both ways;
  - enums, including `subject.kind` and `status`;
  - F breaches on subject, status, amount and quantity;
  - units by kind, by `line_type` and by band;
  - currency in `amount` and in `body`;
  - STORAGE `rate` and `currency`, both directions;
  - duplicates: band name and a set of refs;
  - ranges: ticket times, departure, `effective_to`, register, band `to`, overlap;
  - `restored_at` with RESTORED;
  - `source_type`, `provenance` and `produced_at`;
  - record outcomes `CANONICAL_SOURCE_TYPE record.kind` and `CANONICAL_DUPLICATE record.source_record_id`, the
    latter including the case where the first record is refused (R13).

## Findings

### M1 (Medium, acceptance gap against R6): a lone surrogate in a key escapes as a path

- **Where.** `contracts/assetops_contracts/canonical/records_v1.py:460-463` (`_check_keys`) and `:338-344`
  (`_pairs`).
- **What.** A key containing U+D800 to U+DFFF is never checked. `parse_record` raises
  `CANONICAL_FORBIDDEN record.body.x\ud800`, and `loads_canonical(b'{"\\ud800":1,"\\ud800":2}')` raises
  `CANONICAL_DUPLICATE json.\ud800`. I reproduced both. In both cases `str(refused).encode("utf-8")` raises
  `UnicodeEncodeError`; my first probe crashed on exactly that print.
- **Why it matters.** R6 says "any string anywhere" holding a surrogate is `CANONICAL_REF at its path`. A JSON key is
  such a string. Intake (`3A2`) will record per-row refusals in Postgres text or JSON responses. A crafted upload,
  where `\ud800` in an object key is valid JSON, then fails at the point where the refusal is written, not with a
  refusal. This is a non-`CanonicalRefused` failure one step downstream, which is the class T7 exists to exclude.
  T7 mutates values only, never keys, so it missed this.
- **Fix.** Check keys for surrogates before reporting them:
  - In `_check_keys`, any key matching `_SURROGATE` gives `CANONICAL_REF <path>`, the container's path with the key
    left out. This needs an Architect ruling on the path text: the container path or an escaped key.
  - In `_pairs`, do the same before the duplicate check, giving `CANONICAL_REF json`.
  - Add T6 cases for both, and a key-insertion mutation to T7.
- **Same class elsewhere.** Swept the other places a key text can reach a path:
  - `_present` paths use only key names from the spec, so they are safe.
  - An unknown key with control characters (`"\n"`) or of any length is put into the path verbatim. It encodes, so it
    is not a crash. But a 1 MB key gives a 1 MB refusal path. Put it to the Architect whether to cap or escape the
    key text in paths.

### M2 (Medium): the check order for a missing controlling value is inconsistent, and the packet misstates it

- **Where.** `records_v1.py:202`: EXPENSE quantity is `_When("body","category",{"FUEL":"R"},"F")`, with default
  `"F"`. Compare CHARGE (`:163-166`) and CUSTOMER_METER_READ (`:231`), whose default is `""`. The undecidable
  branch is at `:553-555`. The claim is at `specs/2a-canonical-format/packet.md:68`.
- **What.** The packet's reading 3 says that when `line_type`, `read_type` or `category` is absent or invalid, the
  quantity step checks only the quantity's shape and the body then refuses the controlling value. Probed:
  - CHARGE with `line_type` absent gives `CANONICAL_FIELD record.body.line_type`, and invalid gives
    `CANONICAL_ENUM record.body.line_type`, as stated.
  - CUSTOMER_METER_READ with `read_type` absent gives `CANONICAL_FIELD record.body.read_type`, as stated.
  - EXPENSE with a fuel quantity and `category` absent, `"fuel"`, `5`, or the whole body absent gives
    **`CANONICAL_FORBIDDEN record.quantity`** every time, not FIELD or ENUM on `record.body.category`.
- **Why it matters.** The set of accepted records is unaffected: all of these are refused either way. But the code
  and path are what intake shows the operator, and what `3A2` and `DS1b` tests will pin. Under D-2A.2 they are
  effectively frozen once merged. "Category missing" reported as "quantity forbidden" misleads the person correcting
  the export. Two kinds following one rule and the third another is the drift that §6.4-as-data is meant to prevent.
  No test pins any of these orders, so the inconsistency is invisible.
- **Fix.** Let the Architect choose one rule; gap 3 below has my recommendation. Then make the table follow it. With
  the packet's rule, EXPENSE's default becomes `""` and the unit check uses the unconditional `("L",)`. Add one T6
  case per conditional kind (CHARGE, EXPENSE, CUSTOMER_METER_READ), each with the controlling value absent and
  invalid. Sweep (W6): every `_When` default in `_SPECS` (lines 163-166, 202, 225, 231, 234-235, 282) must follow
  the same rule. The STORAGE `currency` and SERVICE_TICKET `restored_at` defaults are keyed on presence or status,
  which are always decidable at that step, so they are fine.

### Low 1 (test gap): `fullmatch` is pinned only for `factor_id`

- **Where.** `backend/tests/test_2a_canonical_v1.py:194-337`.
- **What.** I planted `match` in place of `fullmatch` in `_check_pattern`. Only the `"diesel\n"` case failed.
  `site_code`, `tenant_code`, `currency`, `document_sha256` and `recognition_period` with trailing junk such as
  `"MTO-001 x"` would then be accepted and pass every test. Planting `match` for `_TIME` (line 449) survived
  entirely: a band `from` of `"05:00x"` would be accepted and written back. Planting `match` for `_DECIMAL` also
  survived, but that one is benign, because the `format(d,"f") == text` check refuses the same inputs.
- **Why it matters.** R5 is a stated rule, and only one of seven pattern sites has a test.
- **Fix.** Add one trailing-character case per pattern site: site, tenant, currency, sha, period, date, time and
  instant.

### Low 2 (test gap): nothing pins "no Unicode normalisation"

- **What.** I planted `unicodedata.normalize("NFC", ...)` in `_check_ref`, and all 162 tests passed.
- **Fix.** Add a T5 case: a ref written in NFD (`"Café"`) round-trips byte-identical and does not equal its
  NFC form.

### Low 3 (spec text, Architect): small inconsistencies to fold into the spec

1. Spec §3 puts `FORMAT_VERSION = 1` in `__init__.py`. The code defines it in `records_v1.py:35` and re-exports it
   (gap 4).
2. **Batch and record order differ.** A batch checks its key set before `format_version` (`records_v1.py:743-746`).
   A record checks `format_version`, then `kind`, then the key set (§6.6). So a batch with version 2 and an unknown
   key gives `CANONICAL_FORBIDDEN`, while a record with the same faults gives `CANONICAL_VERSION`. The spec fixes
   only the record order; the packet lists the batch order as a reading (`packet.md:71`).
3. **Null versus F.** `"subject": null` on a kind whose row says F gives `CANONICAL_FORBIDDEN record.subject`,
   because the F check comes before the null check (`_present`, `:495-504`). §6.2 says "a `null` anywhere is
   `CANONICAL_TYPE`". Both readings are defensible; the spec should say which wins.
4. **R12 and §6.3 disagree.** §6.3 and R12 (spec line 267) say "digests are of the text as sent". But the digest is
   of canonical bytes, and canonical instants are normalised: `.1` becomes `.100000`, `Z` and `-00:00` become
   `+00:00`. The code follows §6.3's `isoformat()` rule, which is the right one. R12's sentence should read "of the
   canonical text; the format never converts zones".

## The four filled gaps (dispatch item 4)

RULES says a choice the spec did not fix is a spec defect to raise, not to decide. All four should have gone to
`mid-build-questions.md`, so the "0 questions" count understates the spec's terseness. Each is flagged for an
Architect ruling either way.

1. **A quantity unit outside the five gives `CANONICAL_UNIT`.**
   - **Sound; ratify.** §6.8's row "quantity unit wrong for the kind" covers it naturally, because a unit not among
     the five is wrong for every kind. The band-unit row gives UNIT for the same fault on bands. T6 already plants
     `"MWh"`, so the spec expected some code.
   - The alternative is `CANONICAL_ENUM` ("an enum value outside its set"). That would split one class of fault
     across two codes.
   - The code checks this at `records_v1.py:548`, so the order is consistent with the band check.
2. **An array fault points at the element; overlapping bands point at the later band's `.from`.**
   - **Sound; ratify.** The spec's own path example, `record.body.bands[1].to`, indexes elements. The element path
     is what an operator needs to find the row.
   - One point for the ruling: for an overlap, the index is the later band's **input** index, where "later" means
     in sorted-by-`from` order (`:669-671`). Pointing at the input position is right, but the ruling should say so.
3. **Check order when `line_type`, `read_type` or `category` is missing or invalid.**
   - **Sound as described, but not as built (M2).** The stated rule is to check the quantity's own shape, then let
     the body refuse the controlling value. It is the better rule, because the operator is told the root cause.
   - I recommend the Architect rule it for all conditional fields and the implementer apply it to EXPENSE.
4. **`FORMAT_VERSION` is defined in `records_v1.py`.**
   - **Sound; ratify, and amend spec §3's table.** Defining it in `__init__.py` would make `records_v1` import its
     own package's `__init__`, which is circular.
   - The public name `assetops_contracts.canonical.FORMAT_VERSION` is unchanged, and T10 asserts it.

A fifth reading, which the packet lists but the dispatch did not name, is that a batch checks its key set before
`format_version`. It needs the same ruling; see Low 3.2.

## What I reran (dispatch item 5)

All commands ran in my scratch worktree at `15e803265`, with
`PYTHONPATH=<scratch>/backend:<scratch>/backend/tests:<scratch>/contracts:...` and
`/opt/assetecon/AssetOpsV1/.venv/bin/python` (3.12.16). These tests take no database and the spec says they are not
pooled, so I ran them directly.

- **Module path.** `assetops_contracts.__file__` and `assetops_contracts.canonical.__file__` both resolved to the
  scratch worktree's `contracts/`.
- **Focused tests.** `pytest backend/tests/test_2a_canonical_v1.py backend/tests/test_2a_canonical_manifest_parity.py
  -q`: **162 passed in 2.40s**.
- **Package tests.** `pytest contracts/tests -q`: **6 passed**.
- **Tests first.** At `071096546`: **2 errors during collection** (package absent), as the packet says.
- **Guards.** `pwsh tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the shared venv): "Architecture
  check passed." `pwsh tools/check-agent-workflow.ps1`: "Agent workflow check passed." I did not rerun check-all.
  The packet's run ("All 37 guards passed") was at `ce7a7221f` plus the bookkeeping; the head differs only in the
  bookkeeping commit.
- **T7 with other seeds.** Seeds 1, 7 and 99 at 3,000 mutations each: 3 passed.
- **Probes.** I probed the check order, instants (`.1`, `24:00`, `-00:00`, `+23:59`, `+24:00`, year 0000), zero
  scales, a non-string `kind`, a BOM, deep nesting, a `1e400` float, and keys containing surrogates. Findings M1, M2
  and Low 3 come from these.

**Planted violations.** Each was applied to a scratch copy, the focused tests were run, and the copy was reverted.

| # | Violation | Result |
|---|---|---|
| 1 | `str(d)` in the writer (`_plain`, amount) | caught: 2 failed (T5 `0.0000001`, `0.000000000001`) |
| 2 | Duplicate key accepted in `_pairs` | caught: 1 failed (`CANONICAL_DUPLICATE json.a`) |
| 3a | `match` for `fullmatch` in `_check_pattern` | caught: 1 failed (`diesel\n`), but only that one (Low 1) |
| 3b | `match` for `_DECIMAL` | survived; benign (the `format` equality check refuses the same inputs) |
| 3c | `match` for `_TIME` | **survived** (Low 1) |
| 4 | Leaf ID `kwh_0000_0500` dropped | caught: T1 and T2 failed |
| 5 | Instants compared as text | caught: 6 failed, including the R12 moment case and ticket ranges |
| 6 | Exponent bound widened to ±13 | caught: 2 failed |
| 7 | C1 range dropped from `_REF_BANNED` | caught: 1 failed (U+0085) |
| 8 | Surrogate check dropped from `_string` | caught: 3 failed (two T6 cases and T7) |
| 9 | Refs NFC-normalised | **survived** (Low 2) |
| 10 | `penalty_rate` unit changed to `MONEY/L` | caught: T4 failed |
| 11 | Record key-set check removed | caught: 3 failed |

## Does the merge need more than the focused tests? (dispatch item 6)

**No.** The only importers of `assetops_contracts.canonical` in the tree are the package itself and the two 2a test
files: I grepped `*.py`, `*.ps1` and `*.toml` for the module name and the fixture name. Nothing in `backend/app`,
`simulator/` or `tools/` imports it, and nothing reads the fixture. `select-tests --base 184dc509e` answers
`mode: full ... full because: backend/tests/fixtures/canonical_v1_examples.json`, which is caused only by the fixture
path. The focused files plus `contracts/tests` are the complete evidence, and the merge's full fast tier collects
`backend/tests` anyway (D-2A.10). A full-suite run would prove nothing more. The fixture exemption in
`select-tests` remains the separate tools item the handshake named.

## Residual risk the packet does not name

- **Unhashable records.** `CanonicalRecordV1` is frozen but cannot be hashed, because it holds `MappingProxyType`
  values: `hash(record)` raises `TypeError`. The spec does not require hashing, but `3A2` and `DS1b` must not put
  records in sets or use them as dict keys. Use `record_digest` instead.
- **Unbounded refusal paths.** Unknown-key paths carry the key verbatim and at any length (see M1's sweep).
- **Version drift.** The packet suggests no later in-place edits of v1, which is good under D-2A.2. Once the M1 and
  M2 fixes merge, refusal codes and paths become de facto contract for `3A2` and `DS1b` tests. That is why I rate
  M2 Medium rather than Low.

## Conflict noted

The standing brief says to write reviews to `specs/<ID>/review.md` and never to `.agent/`. The dispatch named
`.agent/review-2a-r1.md`; I followed the dispatch. The coordinator may wish to copy this file to
`specs/2a-canonical-format/review.md`.
# 2a review round 2 (verification, b916ac2c1..d29e436ee): ACCEPT

1. M1 confirmed. Surrogate key: CANONICAL_REF at the container path (`record.body`) from _check_keys, `json` from loads_canonical. Unknown/duplicate keys use _key_text (ASCII-escaped, 64 chars + "..."). T7 now asserts ASCII and bounded path; both T11 key tests pass. Plants: removing the container check fails 12 tests; removing the cap fails 2.
2. M2 confirmed. EXPENSE map has FUEL:R and OM, STAFF, REPAIR, ENERGY, PENALTY, COLLECTION, HANDLING:F, default "" (undecidable, shape only). Matches the spec's eight categories; none missing or mis-mapped. CHARGE and CUSTOMER_METER_READ already default "" / "O". T11 pins CANONICAL_FIELD / CANONICAL_ENUM on the control for CHARGE, EXPENSE, METER_READ. Plant (default "F") fails the EXPENSE case.
3. Batch order confirmed: format_version before _check_keys. Plant (keys first) fails test_t11_version_before_envelope_keys.
4. Lows 1-2 confirmed. Plant fullmatch->match fails 7 tests (site_code, currency, sha256, recognition_period, bands from, tenant_code, factor_id). NFC-normalising plant fails the NFD test. Note: occurred_at/effective_from junk cases do not fail under the pattern plant because fromisoformat rejects the trailing newline anyway; behaviour is still refused correctly, so those two cases are not pattern-specific. Not a finding.
5. Clumsy assertion is correct: 64 escaped chars = 10 x "é" (60) + "\u00" (4), then "...". The `"..."[:0]` is a no-op. Worth a cosmetic tidy (Low, optional): `("\\u00e9"*11)[:64] + "..."`. Not blocking.
6. Reruns: PYTHONPATH = scratch worktree contracts/ and backend/ (module path verified inside the scratch worktree). backend/tests/test_2a_canonical_v1.py + contracts/tests: 181 passed. Scratch worktree removed; no DB, server or Docker touched. Architecture/workflow checks not rerun.

New issues from the fixes: none. Residual: a refusal path cut mid-escape (e.g. `\u00`) is per spec but cosmetically odd for operators.
