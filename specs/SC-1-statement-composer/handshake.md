# SC-1 handshake (one combined round, RULES §4 items 6-7)

**Round 1 answered** (Architect, 2026-11-21): `rulings.md` "Handshake answers (round 1)", folded into spec rev 2.
No question is open.

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a pre-flight
of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and I1, I2 .... Each
question cites the spec section, says what is unclear and what answer the writer expects, and is marked **(done)**
when its answer changes what counts as done. The Architect answers every question once, in `rulings.md` under
"Handshake answers", and folds the answers into `spec.md`. The handshake ends when neither section has an open
question; coding starts only then.

## Reviewer questions

## Implementer pre-flight

(Reviewer: Claude, 2026-11-21. Severity High / Medium / Low. **(done)** = the answer changes what counts as done.
Judged above all on the owner's test: are conditions and word choices truly data, is `i18n.render` the only
renderer, and can a sentence say anything the facts do not.)

**R1 (High, done). The hand-built-sentence scan is vacuous in SC-1a and easy to walk around.** §3.8.4 scans
`ADOPTED`, which is empty in SC-1a, and D-SC1.14 makes adoption by 3A7 and 5c conditional on merge timing, so done
question 2 ("no `if` on wording in any adopted module") has nothing to check and the owner's "no if/else mess" is
unenforced on every existing module. Then the rule itself: it flags f-strings, `.format`, `%`, `+` with a literal and
a constant with two or more spaces. It misses `"Not available"` (one space), `" ".join([...])`, `"".join`,
`"a" if x else "b"` (each branch short), `string.Template`, `textwrap`, `str(x) + unit` (no literal operand on the
sentence side), `+=` on a variable, a sentence assembled from dict lookups. And it exempts all `raise` arguments, but
`raise HTTPException(409, detail=f"...")` and `_refuse(...)`-style raises are the served text (work_api, accounts_api).
Also logging f-strings in an adopted module are false positives. Expected answer: say plainly that SC-1a proves the
scan on plants only; add a positive scan of the shipped mechanism (`i18n/formats.py`, `conditions.py`, `render.py`,
`catalogue.py`: no string constant containing a letter run of two or more words, no `if` comparing to a string
literal other than the closed vocabularies of operators, types and codes); list the evasions above as plants (P13b,
P13c) or state them as known holes; restrict the `raise` exemption to exception types that are never served (and
say how the scan tells); decide logging calls. Without this the claim in §1.4 and done 2 is only a policy.

**R2 (High, done). Where is a figure's evidence ever shown?** `Money` carries `Evidence`, but the default option is
`evidence: none`, so "Contribution is $562.00 below target" prints a DERIVED, source-emulated figure with no word.
Nothing in the load check or guard requires a statement that prints a money/quantity/percent slot to also print its
evidence word, or to declare that the screen shows it elsewhere. The owner's rule is "every figure carries its
evidence class", and the spec makes that mechanical only inside the fact, not on the page. Expected: either a
statement-level declaration (`"evidence": "inline" | "elsewhere:<where>"`, checked at load: no figure slot without
one) or an explicit ruling that evidence display belongs to the screen (5c's chip) and the claim in §1 value is cut
back. Also `Money(…, evidence=NOT_AVAILABLE)` (and `NEUTRAL`) is constructible per §3.1, but a not-available figure
has no value; the constructor must refuse those evidences so "missing" can only be `Absent`.

**R3 (High, done). Typed facts versus the wire.** Messages are not only rendered in-process: `chain/period_read.py`
`is_message` accepts only `{key, params}` with `params` of `str|int|float`; refusals return `"words"` and `"params"`
in JSON (`commercial_upload_api.py:51`, `work_api.py:157`); `response_store` stores bodies with the locale in the
key (D-I18N.1: stored as message, rendered at read). A `Fact` param is not JSON, so any message that is stored or
sent fails or silently loses its type. §3.6 says only that `Param` widens. Expected: say which messages are
structured (render-in-process only, never stored or sent), or specify a lossless `to_json`/`from_json` for every fact
with a round-trip test, and say what `is_message` and the refusal `params` field do with a `Fact`.

**R4 (Medium, done). Fallbacks that are not "fallback sentences" but have the same effect.** (a) §3.6.1: a missing
statement in a non-English locale falls back to the English statement. D-SC1.11 says there is no fallback text; say
whether this one stays (it is today's behaviour, D-I18N.3 offers only complete locales) and test it. (b) The pick
domain: `direction` excludes zero by relying on an earlier `on_target` variant. Nothing at load proves the earlier
conditions exclude zero, so the guarantee is a runtime `PICK_DOMAIN`, which D-SC1.11 treats as "a code defect the
cases catch". Cases catch it only if a case has gap 0 at `gap_only`. Expected: either a load check that a variant
using a `pick` is reachable only for values in the domain (conditions imply it), or a rule that each pick has a
declared case at the boundary value.

**R5 (Medium, done). `rendered ≠ computed` is not checked.** The renderer proves the sentence is filled from facts of
the right type, but not that the facts match the claim the wording makes. §5.2: `more_than_gap`'s "more than the
whole gap" and `share_of_gap`'s "of it" assume `big` has the gap's sign and `abs big <= abs gap`; the caller computes
which heading is named (5c D-5C.15), so a wrong `big` of the opposite sign prints "explain $412.00 of it" for a
widening driver. The statement's `when` only compares magnitudes. Expected: the condition set should include the
sign relation (`cmp` of signed values is allowed; add `all[sign gap negative, sign big negative]`) or the statement
should declare the precondition and refuse at render; add a case for opposite signs that must raise, not read.

**R6 (Medium). Conditions are data, but the evidence rule is not.** §3.5 says the evidence word rule's order is
data (`by_evidence_first`, `by_origin`, `observed_by_evidence`). The order in which those three are consulted, and
the "money suffix" rule, live in `formats.py`, a fixed three-step algorithm. That is acceptable (it is a format), but
the sentence "the rule's order is data" overstates it and §3.7's `VOCABULARY_SCHEMA` cannot prove the algorithm.
Expected: reword; have T2 cover every (evidence, origin) pair of `EVIDENCE_ORDER x ORIGIN_ORDER (+None)` by hand
table, since a pair with no entry today (e.g. `RECORDED` with origin `None`) falls to "Estimated" by 5c's "unknown or
none". Say whether that is intended for a RECORDED figure.

**R7 (Medium, done). The digit and symbol ban is narrower than its reason.** `LITERAL_DIGIT` is "0-9" and
`LITERAL_SYMBOL` is four symbols. Unicode digits (superscripts as in `m³`, fullwidth, Arabic-Indic), `¥ ₹ ₦ ‰ ¢`
and any `Sc` symbol pass. Number words pass too: "twice", "both", "half", "one of", "two", "first" in a template are
numbers by word (D-SC1.9's own class, the mock's "61 days"). Expected: scan with `unicodedata` (`Nd`/`No`, `Sc`, `%`,
`‰`), and either ban a closed list of number words in literals or record it as a residual that review checks. State
that `unit` symbols (`kWh`, `L`) and a unit like `m³` fall under the rule.

**R8 (Medium). Duplicate keys inside one literal are silent.** `ast.literal_eval` of `{"a": 1, "a": 2}` returns the
second. `KEY_DUPLICATE` is across modules and `messages.CATALOGUE`; within one dict, a duplicate statement key, slot,
variant `options` entry or vocabulary entry silently overwrites. Expected: `NOT_DATA`/`KEY_DUPLICATE` computed from
the `ast.Dict` key list, and a plant. Also §3.2 says "`ast.literal_eval` of its source succeeds" but a module with a
docstring and an assignment is not a literal; say it is the assigned value node that is evaluated.

**R9 (Medium). A back door around the one renderer.** §4/§5 let `render` and `load` take `catalogue=` "tests only";
nothing enforces it. Any module can pass a catalogue, or import `i18n.formats.money` and compose by hand, which is
the second renderer D-SC1.1 forbids. Expected: make it private (`_catalogue`) or a context-var set only by test
helpers, and have the guard's scan flag `catalogue=` and imports of `i18n.formats`/`conditions` outside `i18n` and
`tests` (add a plant).

**R10 (Medium, done). `Absent` has a reason no statement can use.** `Absent(reason)` ("ACCOUNTS_ZERO") is never
printed and no condition reads it. 5c needs different words for different causes (`NOT_RECEIVED`, `NOT_CONNECTED`,
`NOT_CALCULATED_YET`: 3B7a `CAUSES`); with no `reason` operator the caller picks a statement key by `if` on the
cause, which is the mess D-SC1.5 removes. Expected: an operator `{"reason": ["slot", "CODE"]}` (or `is` on `Absent`),
`reasons` declared on the slot, checked at load, or a ruling that causes are passed as a `State` fact.

**R11 (Medium). The worked statements do not cover what 5c and 3A7 actually need, so "adopt without waiting"
(done 7) is unproved.** Checked against 5c §2.1 and §2.5: (a) `Price` (`$1.25 per L`, `$0.4321 per kWh`: 4 places
when more than 2, then "per" + unit) has no format; `money` has no `places`. (b) 5c `pct0(a, t)` and the `share`
table (`{n}% of what widens the gap | Offsets it | No effect`) need `percent places 0` plus a three-way variant on
sign and magnitude; no case. (c) `status_disagreement` "two or three" needs `all[cmp >= 2, cmp <= 3]` on a count;
allowed by §3.4 but not shown. (d) 3A7 §2.7's `{scope}` is "the Site code, or the organisation": a `Name` or a
`Word`? (e) `{site}'s` possessive of a `Name`. (f) `drawer_values` ("only for a SUM factor with both values") and
`tile2_rest` use sign of a derived figure and an offsetting case. Expected: add at least one worked case each for
(a), (b), (c), (d) or cut (a) from the adoption promise and say 5c ships those as legacy.

**R12 (Medium). Money has no `places`, while `percent` and `quantity` do; `tiny` is defined on money only.** A
quantity or percent of 0.004% rounds to `0%` and reads as zero: the `tiny` honesty case applies equally. Expected:
`tiny` on `quantity` and `percent`, or a ruling that only money needs it (and why).

**R13 (Medium). Plants that cannot fail or do not prove what they claim.** P7: removing the `MONTH_OPEN` variant also
removes the only `is` for that value, so `NOT_EXHAUSTIVE` is the only possible code (good), but add a plant where a
variant's `when` is an `all` containing the `is` (must also refuse). P8: `share_of_gap` given a `when` fails
`NO_FALLBACK` only if no earlier variant is terminal; say so. P16 ("`gap` Absent to a variant forced to print it")
needs the variant order changed in the plant or `not_available` would catch it; write the plant's exact edit. P17 is
reviewer-by-eye; add a cheap machine check for key and vocabulary-key tokens that look like instances (a Site code
from `config/`, a UUID, a digit) since digits are already banned in keys by `KEY_FORM`: say so and drop P17 to a
note. No plant proves `SLOT_CONFLICT`, `VARIANT_ID`, `PART_UNKNOWN`, `VOCABULARY_FORM`, `REPHRASE` or `CONDITION_TYPE`
inside a statement (reviewer guide 3 makes a code without a failing test Medium: add the missing plants P19 to P24).

**R14 (Medium). `Flag` condition form is inconsistent.** §3.4: `is` holds when a `Flag` equals `true`/`false`; §5.3
writes `{"is": ["pending", True]}` (a Python bool) while a `State` takes a string. Pin the operand type for each and
add the `CONDITION_VALUE` case for `{"is": ["pending", "true"]}`.

**R15 (Low). `Name` and `Items` of `Name`.** `Name` checks control characters only. A name containing `{`, a `$` or
digits is fine as data (Names legitimately hold digits), but then `LITERAL_DIGIT` is not a statement about the
output, only about the template; the done question 1 wording ("no digit in any template or vocabulary literal") is
right, but §1's "a reviewer can prove it contains no number the structure did not compute" is wrong for names and
`example` slots. Reword.

**R16 (Low). `Items` order `vocabulary`** removes repeats but `given` does not; say whether `given` repeats are an
error. `items` of zero items (`count == 0`) prints an empty list: require `present` or refuse at render.

**R17 (Low). Legacy ratchet is by key name only.** A legacy key's template can be edited to anything (including a
digit) without the guard noticing. Either record a hash of each legacy template in the baseline (so a changed legacy
template needs a baseline edit) or accept that. Also `i18n/messages.py` "touches only `Param`" (guide 9) while 3A6
adds keys to the same file: say how the guide's check treats 3A6's additions.

**R18 (Low). 5c/3A7 amendments.** D-SC1.14 conditions adoption on merge timing: a lane can start 3A7 a day before
SC-1a merges and end up on the legacy path with 3A7's `505.00 USD` form while the product elsewhere moves to `$505.00`
(Q2 is the owner's). Ask the Architect to give the date or the merge condition that decides, and who tells 3A7's
builder.

## Implementer pre-flight

Checked against `main` at da7140b4a. Python 3.14.4. No code run beyond importing `i18n.messages` read-only.

**P1 (Low).** `i18n/` is 6 + 95 + 196 + 15 = 312 lines (`__init__`, `locale`, `messages`, `render`): matches §0. The
catalogue has exactly 123 `en` entries. 12 contain a digit or `%` (`reading_upload.refused.encoding`,
`invalid_timing`, `span_mismatch`, `invalid_value`, `template_note`, `health_panel`, `accounts.password_policy`,
`bad_name`, `bad_reason`, `commercial_upload.reason.canonical_version`, `canonical_number`, `native_encoding`): they
stay legal as legacy, but SC-1b cannot move them under D-SC1.9 until the policy limits (12 to 128 characters, 15
minutes, 3 decimals) become `Count`/`Quantity` facts or `example` slots. Note for SC-1b's sizing; not SC-1a.

**P2 (Medium).** No legacy template has a format spec, conversion or a literal brace, so §3.9's "rendered as today"
needs no escaping logic. But `render` is `template.format_map(dict(params))` and today's catalogue is
`dict[str, dict[str, str]]` keyed by locale then key; the merged catalogue in §3.7 must keep `CATALOGUE["en"][key]`
a plain string for `test_uq6a_message_seam.py:246` and `test_up1_reading_upload.py:107, 349-350`, which read
`messages.CATALOGUE` directly. Plan: keep `messages.CATALOGUE` untouched (legacy only) and put the merged view in
`catalogue.py` under another name. Confirm `render.py` imports from `catalogue`, not `messages`.

**P3 (High). Wire.** See R3. `chain/period_read.py:66-69` (`is_message`) rejects any param that is not
`str|int|float` and not `bool`; `commercial_upload_api.py:51` and `work_api.py:157` return `params` in JSON. If a
structured message reaches any of these, it fails or is mis-sent. Plan: structured messages are rendered in the
module that builds them and the rendered string is what travels, unless the Architect rules otherwise (R3).

**P4 (Medium).** `EVIDENCE_ORDER` (`structure/evaluate.py:28`) is `RECORDED, MEASURED, DECLARED, DERIVED, ESTIMATED,
MODELLED, NOT_AVAILABLE`; `ORIGIN_ORDER` is `observed-financial, field-integrated, bench-tested, source-emulated,
demo-simulated, unknown`. §3.1 copies the first and says "no import" (dependency direction), but gives no parity test.
`evaluate.py` already does this for `PROVENANCE_ORDER` ("a test proves it equals 3A4's"). Plan: copy both tuples and
add a T1 parity test importing the originals (tests may import). `NEUTRAL` is outside the order: refuse it in
`Evidence` (matches R2). `evidence` 5c §2.4 vocabulary: no entry for `NEUTRAL`.

**P5 (Medium).** §0 and §6 say tests are "neutral (T2)". T2 is `simulator/tests` and `contracts/tests` only
(`tools/checks/neutral_tests.py` `DIRS`); the SC-1 tests live in `backend/tests/` where `conftest.py` has an autouse
fixture importing `estate.coverage`, so they run in the backend suite (no database needed, no `ASSETOPS_TEST_DATABASE_URL`).
Plan: run `tools/heavy-slot.sh -- .venv/bin/python -m pytest backend/tests/test_sc1_statements.py -q` and
`tools/checks/test_statement_catalogue.py`; do not claim T2. Ask whether the file should be in `backend/tests/` or a
new neutral folder.

**P6 (Medium).** Guard wiring. `check-all.ps1:331` wires the fuel guard as `pytest tools/checks/test_fuel_wording.py`;
`:Add-Guard` takes an `-environment` hashtable (line 290). The SC-1 guard imports `assetops_backend`, so it needs
`PYTHONPATH=backend` in that hashtable (as `neutral_tests.py` puts roots on `sys.path` itself). Plan: the guard sets
`sys.path` itself (like `neutral_tests.py`), so the two `Add-Guard` lines in §3.8 work unchanged. `tools/check-architecture.ps1`
registers only `*.ps1` files in `tools/checks`, so the new `.py` and `.json` need no registration.

**P7 (Low).** `tools/checks/fuel_wording.py` `py_hits` is the AST pattern to copy (`_bare_strings`, `ast.walk`,
`JoinedStr`). It treats a docstring as a bare `Expr(Constant)`: `HAND_BUILT` can reuse it. It does not look at
`Call(func=Attribute("format"))` or `BinOp(Mod)`: I will write those; R1 lists the cases I will plant.

**P8 (Medium).** `analytics/plain.py` (583 lines) restates stored prose by `re` (`_basis_line` at 193-212,
`_policy_statement` at 311-317, `_gap` at 543): it confirms D-SC1.13's class and is SC-1c. Out of SC-1a. `night_text.py`
(287 lines) uses f-strings with `L`, `kWh` and `HH:MM` and imports `finding_text.litres1` (half-even on `Fraction`,
one decimal), so `quantity` needs `places: 1` with `Fraction` input handled by the caller, not by the format. SC-1c.
`asset_words.py` (32 lines) is the `replace("_", " ").capitalize()` fallback D-SC1.8 forbids: vocabulary `asset`
needs a declared label per type and a rule for an unmapped type (an `Absent`/error, not a capitalised code): ask in
SC-1c. `frontend/src/ui/productWords.ts` (487 lines) returns `UNRECOGNISED_SENTENCE` for an unknown code: a
fallback sentence by D-SC1.11's definition; SC-1d will have to refuse instead. None of these block SC-1a.

**P9 (Low).** Money format vs 5c §2.1: matches (U+2212 before the prefix, `$` for USD, `KES ` with a space, zero
unsigned). `Context(prec=34, ROUND_HALF_EVEN)` is stated in 5c; §3.3 says `quantize(Decimal("0.01"), rounding)` and
does not say which `Context`. `Decimal.quantize` raises `InvalidOperation` above default 28 digits; plan: a module
`Context(prec=34, traps=[InvalidOperation, DivisionByZero, Overflow])` as 3A7 `DISPLAY`, and use it for every
quantize.

**P10 (Low).** `percent` `places: "normal"` is `format((v*100).normalize(), "f")`: `Decimal("0.01")*100` is
`1.00` and normalizes to `1`; `Decimal("1")*100` normalizes to `1E+2` and `format(..., "f")` gives `100`: fine with
"f". `quantity` has the same shape. Plan: T2 rows for 100 and 1200 (exponent form).

**P11 (Low).** C1 arithmetic: share 0.0100099700897308 x 100 = 1.00099…, `ROUND_UP` at 2 places = `1.01%` (the
variant's `share` option is on the part's slot, reached through §3.6 step 5); allowed 5.015 `ROUND_DOWN` = `5.01`;
difference 5.02 `ROUND_UP` = `5.02`. C2: -0.004 with `down` displays `0.00` so `tiny` prints `less than $0.01`: the
format then prints `less than` (vocabulary `format`) before the money, in a part already preceded by "the records say
$505.00, ": reads as in §5.1. I could not find an arithmetic error in C1-C8 or H1-H6.

**P12 (Medium).** `facts.py` constructors "validate": `Percent` allows any Decimal (a value above 1 is legal for a
growth); `Month` year range unspecified; `Name.text` empty allowed. Plan: refuse `Name.text == ""`; leave the others
and say so.

**P13 (Low).** Slot-name resolution for parts (§3.6.2 "a name declared twice must carry the same type and options"):
in §5.1, `difference` exists only in the part, `share` only in the part, and the heading's variant `options`
(`difference`, `allowed`, `share`) name part slots: allowed by §3.7. `allowed` is also a heading slot. Plan: options
keyed by slot name apply to every statement in the tree that declares it. If two parts declare `share` with different
options, `SLOT_CONFLICT`. Confirm this is the intent (R-free).

**P14 (Low).** Python 3.14.4 is the local interpreter; `.venv/bin/python` is what the repo uses: I will check its
version before coding (I did not run it).

Open for the Architect (R-numbers above): R1, R2, R3, R4, R5, R7, R10, R11 and R14 change what is done; P3 and P5
need a one-line answer.
