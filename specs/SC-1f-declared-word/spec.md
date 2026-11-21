# SC-1f: a word for declared settings, and two guard fixes (implementer spec)

Status: **in_review** (rev 1; built `task/SC-1f-declared-word`, packet `packet.md`). Architect (Claude), 2026-11-21, owner in session. Rulings with reasons:
`rulings.md` (D-SC1F.1 to D-SC1F.6). Owner words: `owner/owner-decisions-list-2026-11-21.md` items 7 and 8 (row 51,
D-3A7.17's D4; the two SC-1 guard fixes, approved). Parent: `specs/SC-1-statement-composer/spec.md` §3.5, §3.6, §3.8.4,
§5.1. Non-screen. **1.0 unit, two commits, one build.** `USER_REVIEW_REQUIRED: true` for the word only, seen at the 5c
walkthrough; it does not block the merge (D-SC1F.6).

## 1. Outcome and why

A value a person sets, such as the owner's 1% reconciliation tolerance, reads "Declared" on the page, not "Recorded".
The management-accounts figure, a record, reads "Recorded". An evidence word never names a figure its sentence does
not state. The statement guard stops counting logger messages as served text, and its self-test stops wiping the
real allow file. The mechanism stays the same: one vocabulary entry, one render rule, one evidence constant, one
logger predicate, one plant helper.

## 2. Structure (factors and records)

| Factor | Record (where) | Rule |
|---|---|---|
| Evidence class of a figure | `Evidence(evidence, origin)` on each fact, chosen by its producer | `DECLARED` = a value a person sets or states as a choice; `RECORDED` = taken from a system of record (D-SC1F.1) |
| Its word | `VOCABULARY["evidence"]` (`i18n/statements/en/vocabulary.py`) | `by_evidence_first`: `{"ESTIMATED": "Estimated", "MODELLED": "Modelled", "DECLARED": "Declared"}`; `observed_by_evidence`: `{"RECORDED": "Recorded", "MEASURED": "Measured", "DERIVED": "Calculated"}`; the rest unchanged |
| A `with` basis | `render._fill_evidence` | counts an `of` slot only if the chosen variant (or a part under it) prints it, or its `when`/`requires` reads it (D-SC1F.3) |
| 3A7's two figures | `structure/reconciliation.py` | `ACCOUNTS = Evidence("RECORDED", FINANCIAL)` (accounts); `SETTING = Evidence("DECLARED", FINANCIAL)` (tolerance); `DECLARED` constant removed (D-SC1F.2) |
| A logger receiver | `tools/checks/statement_catalogue.py` `_logger` | stem in `LOG_STEMS = {"log", "logger", "logging"}` after `lstrip("_").casefold()`; or bound in the module to `getLogger(...)`; or a `getLogger(...)` call (D-SC1F.4) |
| A P55 plant's allow file | `_plants_r1.allow` | the real `ALLOW` file plus the plant's entry (D-SC1F.5) |
| Classed code strings | `statement-handbuilt-allow.json` | `commercial/profiles.py`: the two `_swap_day_month` fingerprints, class `CODE` (D-SC1F.5) |

## 3. What changes, by file

**Commit 1 (0.5): the word.**
- `i18n/statements/en/vocabulary.py`: the two tables as in §2.
- `i18n/render.py`: in `_statement`, fill the chosen text's fields in two passes. Pass 1 fills every field whose slot
  type is not `evidence`, and records the figures printed and the slots read from the start of this variant's fill
  (the `r.printed` and `r.read` lengths taken before it). Pass 2 fills the `evidence` fields. `_fill_evidence` takes
  `of` slots that are non-absent figures and are in that variant's printed-or-read record. Keep the text order of
  the output. `ABSENT_PRINTED` stays for a basis with no counted slot.
- `structure/reconciliation.py`: `ACCOUNTS` and `SETTING` as in §2, with the comment rewritten to D-SC1F.1's rule.
  `heading_words` uses `ACCOUNTS` for `accounts`, and `_tolerance` uses `SETTING`.
- Text docs: SC-1 spec §3.5's evidence paragraph carries an "Amended by SC-1f (D-SC1F.1)" line (done in this spec's
  commit); 3A7's `D-3A7.17` likewise.

**Commit 2 (0.5): the guard.**
- `tools/checks/statement_catalogue.py`:
  - `LOG_STEMS` replaces `LOG_NAMES`.
  - `_logger(receiver, bound)` implements D-SC1F.4. `Tree` collects `bound` (names and attribute names assigned
    from a `getLogger` call) in its existing walk, and `unserved_served` does the same over its own tree.
  - In `_plants_r1`, `allow(entry, path=leaf)` returns `{ALLOW: json.dumps(merged)}`, where `merged` is the base
    allow file (`_read_json(base / ALLOW) or {}`) with `entry` appended to `merged.get(path, [])`.
  - The plants in §4.
  - The module docstring's rule 5 reworded.
- `tools/checks/statement-handbuilt-baseline.json`: run `python tools/checks/statement_catalogue.py --prune`. Then
  remove the two `commercial/profiles.py` fingerprints by hand (prune removes only stale ones; these are live).
  Expected removals: those two, `commercial_upload_api.py` `g:build_commercial_upload_router.run:395904969735` and
  `estate/index.py` `g:opportunity_read:693eaf7b776b`, and nothing else. Any other removal is a stop (§6).
- `tools/checks/statement-handbuilt-allow.json`: `{"backend/assetops_backend/commercial/profiles.py":
  [{"fingerprint": "h:_swap_day_month:052fded502f9", "class": "CODE", "why": "date-format tokens DD and MM swapped in
  a layout's format string; not served"}, {... "h:_swap_day_month:d40e38ccee22" ... same class and why}]`.

## 4. Tests (written first; red before the code)

**`backend/tests/test_sc1_statements.py` and `backend/tests/statement_cases/` (`reconciliation.py`, `worked.py`).**
The cases' evidence becomes: accounts `RECORDED`, recorded `RECORDED`, tolerance `DECLARED`, the derived figures
`DERIVED`, origin `observed-financial` unless the row says otherwise. SC-1 §5.1's cases then read:

| # | English (only the changed ones; C5, C6, C7, C8 are unchanged) |
|---|---|
| C1 | `Revenue (Recorded and Declared): the accounts say $501.50 and the records say $506.52, $5.02 more (1.01%), beyond the $5.01 allowed (1%).` |
| C2 | `Fuel cost (Recorded and Declared): the accounts say $505.00 and the records say $505.00, less than $0.01 less, within the $5.05 allowed (1%).` |
| C3 | `Revenue (Recorded and Declared): the accounts say $1,200.00 and the records say $1,200.00, the same, within the $12.00 allowed (0.5%).` |
| C4 | `Revenue (Recorded and Declared): the accounts say KES 0.00 and the records say KES 10.00, KES 10.00 more, beyond the KES 0.00 allowed (1%).` |
| C9 | `Revenue (Recorded, Emulated and Declared): the accounts say $1,200.00 and the records say $1,200.00, the same, within the $12.00 allowed (0.5%).` |

New cases:
- **C10 (D-SC1F.3).** C7's facts plus tolerance 0.01 `DECLARED` give C7's sentence, `Fuel cost (Recorded): the
  accounts say $0.00 and no fuel invoices are recorded.`, with no "Declared".
- **C11 (D-SC1F.1, origin None).** `reconciliation.statement` `MATCHED`, month 2026-10, scope `SITE` `KOBO-001`,
  tolerance 0.01 `Evidence("DECLARED", None)`: `October 2026 (KOBO-001) matches the management accounts within 1%
  (Declared).`
- **C12 (D-SC1F.1, simulated origin).** The same with origin `demo-simulated`: the same sentence.
- **V1.** `formats.evidence_word` of `DECLARED` with each of the six `schema.ORIGINS` and `None` is `Declared`.

**3A7's tests** (`test_3a7_reconciliation_words.py`, `test_3a7_reconcile_command.py`,
`test_3a7_reconciliation_postgres.py`). Expected strings change by exactly three rules:
- (R1) a `matched` or `not_matched` heading: `(Recorded and Emulated)` becomes `(Recorded, Emulated and Declared)`,
  and `(Recorded)` becomes `(Recorded and Declared)`.
- (R2) a `zero_stated` or `not_received` heading: unchanged.
- (R3) a statement or standing sentence: `within N% (Recorded)` becomes `within N% (Declared)`.

The module docstrings that quote the old words are updated to match. Any other changed string is a stop (§6).

**Guard self-test (`_plants_r1`; run by `tools/checks/test_statement_catalogue.py::test_guard_self_test`).** Each
negative must pass and each positive must fail with its code:
- N14 `import logging\n_LOG = logging.getLogger(__name__)\ndef f(x):\n    _LOG.warning(f"read {x} rows from the file")\n`.
- N15 `LOGGER = object()\ndef f(x):\n    LOGGER.info(f"loaded {x} rows from the file")\n` (the stem rule alone).
- N16 `import logging\naudit = logging.getLogger("a")\ndef f(x):\n    audit.error(f"the gap is {x} today")\n` (the
  binding rule).
- N17 `class C:\n    def f(self, n):\n        self._log.info(f"loaded {n} rows from the file")\n`.
- P58a `def f(report, x):\n    report.warning(f"the gap is {x} today")\n`: `HAND_BUILT_NEW`.
- P58b `def make():\n    return None\naudit = make()\ndef f(x):\n    audit.info(f"the gap is {x} today")\n`:
  `HAND_BUILT_NEW` (only `getLogger` binds).
- P55a to P55c are unchanged in their expectations. Under the merged helper they now prove the real allow lines
  survive: with the replacing helper, the moved `profiles.py` fingerprints read `HAND_BUILT_NEW`, outside each
  plant's allowed set, so the plant fails.

**Plants the reviewer runs (each must turn a test red; revert after).**
- P59a: `DECLARED` back in `observed_by_evidence` (C11 and C12 fail).
- P59b: `_fill_evidence` over every `of` slot (C10 fails).
- P59c: `accounts` with `SETTING` (3A7's R1 headings fail).
- P59d: `LOG_STEMS` without `lstrip("_")` (N14 and N17 fail).
- P59e: `allow()` replacing the file (P55a to P55c fail).

## 5. Checks

`tools/heavy-slot.sh --` the backend no-DB tests for `test_sc1_statements.py` and the two no-DB 3A7 files. Then
`test_3a7_reconciliation_postgres.py` through `tools/heavy-slot.sh --db`. Then `python
tools/checks/statement_catalogue.py` and `--self-test`. Then the fast check-all. Report in the packet
`specs/SC-1f-declared-word/packet.md`: every changed expected string (old, new), the baseline diff, and the
allow-file `ALLOWED` notes.

## 6. Done (questions; each can fail) and stops

- Does every `DECLARED` figure read "Declared" for every origin (V1, C11, C12)?
- Does the accounts figure read "Recorded" and the tolerance "Declared" in every 3A7 sentence that prints them?
- Does any sentence name the evidence of a figure it does not print (C10)?
- Do `_LOG`, `LOGGER`, `self._log` and a `getLogger`-bound name all pass, while `report.warning` and a
  non-`getLogger` binding are still caught (N14 to N17, P58a, P58b)?
- Do the P55 plants run on the real allow file, and does it hold exactly the two `profiles.py` lines?
- **Stop and ask the Architect** if a changed expected string falls outside §4's rules, if a baseline removal falls
  outside §3's four, or if any statement outside `reconciliation.*` changes its English.

## 7. Out of scope

5c's evidence mapping of structure rows (D-SC1F.2 names the rule it follows); any change to `money_suffix`,
`by_origin` or the join; ENV-1's files beyond the baseline line that D-SC1F.4 prunes.
