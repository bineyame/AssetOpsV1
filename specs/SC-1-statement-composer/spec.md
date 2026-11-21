# SC-1: the statement composer (implementer spec)

Status: **in_review** (SC-1a built, units 1-3; `packet.md`; review round 1 ACCEPT WITH FIXES; fix round r1 built). Rev 3: handshake
round 1 answered (D-SC1.17 to D-SC1.27); mid-build answers D-SC1.29 to D-SC1.31; review answers D-SC1.32 to
D-SC1.39 (fix round 0.75 units, §8).
Code starts when the handshake has no open question. Questions during the build: `mid-build-questions.md`.
Reviewer: `reviewer-guide.md` rev 3. Decisions with reasons: `rulings.md` (D-SC1.1 to D-SC1.39).

Architect (Claude), 2026-11-21. Owner words (verbatim, `owner/owner-text-composition-clean-2026-11-21.md`): "if that
application could do it reaptedly, make sure it uses clean way to do it (not brittle hard coding and if else mess)".
Standing rules applied: fundamental mechanics first, general over particular (`owner/SUMMARY.md`); honesty rules
(`.ai/RULES.md` §1: missing never 0, every figure carries its evidence class, "Not analysed yet" only while work is
pending, claim only what was tested); W1 to W6 (`.ai/RULES.md` §4).

Non-screen. **SC-1a: 3.5 units, three commits** (rev 1: 2.0; the handshake made the scan real, put evidence on the
page, fixed the wire form and moved two runtime guarantees to load). Discovery review (W5): a new mechanism every
sentence passes through, and money figures in words. `USER_REVIEW_REQUIRED: false` for SC-1a (no English the owner
sees changes; D-SC1.10's money form and D-SC1.18's evidence words reach screens only through 3A7 and 5c, which carry
their own review).

## 0. Before you start

- **Branch** `task/SC-1a-statement-composer` off `main`; worktree `/opt/assetecon/AssetOpsV1-sc1a`. Code starts when
  the handshake has no open question.
- **Python, PYTHONPATH:** as 3A3 §0; check `.venv/bin/python --version` first. Pure Python; no database, no server,
  no Docker. The tests are **backend-suite tests that need no database** (not T2: `backend/tests/conftest.py` imports
  `estate.coverage`). Run `tools/heavy-slot.sh -- .venv/bin/python -m pytest backend/tests/test_sc1_statements.py -q`
  and `.venv/bin/python -m pytest tools/checks/test_statement_catalogue.py -q`.
- **Read:** this spec and `rulings.md`; `backend/assetops_backend/i18n/` (all four files, 312 lines: the seam this
  extends, D-I18N.1 to D-I18N.3); 3A7 `spec.md` §2.7 and `rulings.md` D-3A7.10; 5c `spec.md` §2 (all of it);
  `tools/checks/fuel_wording.py` (the AST-scan pattern to copy) and how `tools/check-all.ps1` line 331 wires it;
  `chain/period_read.py` `is_message` and `commercial_upload_api.py` `_refusal` (the wire they must not meet, §3.11).
- **Collisions.** `3A6` (in build) adds flat entries to `i18n/messages.py`: they stay legal (§3.9) and join the
  legacy baseline, with their hashes, in whichever of 3A6's and SC-1a's merges is later (D-SC1.27). `3A7` and `5c`
  start their code only after SC-1a merges, and adopt it (D-SC1.26, §8).

## 1. Outcome and why

**What exists, and what it already does well.** The live product already has the right seam: a server word is a
`Message` (a catalogue key and its params), the catalogue is data (`i18n/messages.py`, 123 English templates), and
words are rendered at read for the request's locale, never stored composed (D-I18N.1). Refusals, upload states and
account words go through it. The specs in flight (3A7 §2.7, 5c §2) write their sentences as key tables.

**What is missing.** The seam carries text, not facts. Every param is a string the caller already formatted, so the
catalogue cannot know that `{accounts}` is money, what currency it is in, how it rounds, or what its evidence is.
Every choice between sentences (matched or not, below or above, one Site or three, "a" or "an", with or without the
share) is made in the caller's code by `if`. Numbers can enter as literal text ("less than 0.01 more", "within 1%",
the mock's "61 days" and "95% load"). Nothing checks that a sentence says only what the computed structure says.

**What SC-1 adds, on top of the same seam (one renderer, `i18n.render`, with `i18n.served` as its second return
shape).**

1. **Typed facts in.** The caller hands over facts taken from the computed structure (money, price, quantity and
   share with their evidence, count, k of n, month, day, instant, a vocabulary word, a name from a record, a state, an
   explicit absence with its reason), never formatted strings. A fact that cannot be true cannot be built.
2. **Statements as data.** A catalogue entry declares its slots (each with a type and display options), its variants
   (each with a declared condition and, where its words assert more, a declared precondition), its parts and its
   fallback. No code per statement.
3. **One renderer** chooses the variant by evaluating the conditions with one evaluator, formats every slot by its
   type with one format per type, product-wide, fills the template, and puts every printed figure's evidence word on
   the page: in the sentence, or handed back with the text for the screen's chip.
4. **Checks.** At load, every statement is proved well-formed: no digit, currency sign or number word in any literal,
   every field a declared slot, every condition over declared slots, a fallback or an exhaustive set, every pick
   reachable only inside its domain, every printed figure's evidence shown, every offered locale complete. At render,
   every printed slot is filled from a fact of its declared type, an absent fact never prints, and a precondition that
   the facts contradict raises. A guard proves every variant has a hand-written case, pins the legacy entries, scans
   the mechanism and adopted modules positively for anything but codes, and stops any module of the backend from
   gaining a hand-built sentence.
5. **Later, optional:** an LLM may rephrase a rendered statement only where the catalogue allows it, and only when
   the rephrasing keeps every figure, name and evidence word; otherwise the template text stands (§3.10, not built).

**Value.** Every sentence on a screen is reproducible from its facts and checkable against them: an operator
executive reading "Contribution is $562.00 below target in October" gets the same sentence from the same facts every
month, for every Site and vertical, with the figure's evidence beside it. No number is written in any wording: every
digit on screen comes from a fact (a computed figure, a count, a date) or is copied verbatim from a record (a name) or
a declared example. Adding a vertical, a Site or a language adds catalogue data, not branches. This is the honesty
claim the demo sells ("every number with its basis") made mechanical.

**Person in the loop.** No one sees the mechanism. The Architect writes statements in specs; builders transcribe
them as data; reviewers check cases; the owner reads the sentences on screen.

## 2. Survey: what already fits, and what is hard-coded

| Where | Today | Verdict |
|---|---|---|
| `i18n/messages.py`, `render.py`, `locale.py` | Catalogue of `str.format` templates, rendered at read per locale | **Fits.** The base SC-1 extends (D-SC1.1). Its 123 flat entries stay legal as legacy (§3.9) |
| `commercial_upload.reason.*`, `reading_upload.refused.*`, `accounts.*`, `person.*` | One key per refusal code or state | **Fits** the key-per-state shape. Params are pre-formatted strings: typed in SC-1b |
| 3A7 §2.7 (not built) | Key per state, with formatting rules and `{gap}`, `{share}` assembled in code | **Fits in shape; logic moves.** State choice becomes `exhaustive` variants; `{gap}` and `{share}` become parts; directed rounding becomes slot options; "less than 0.01" becomes the money format's `tiny` option (§5.1) |
| 5c §2.2 to §2.4 (not built) | Factor labels, record words, the evidence-word rule, as tables | **Fits.** Moves to the shared vocabulary (§3.5), used by every later screen |
| 5c §2.5 (not built) | Sentence table with choices inline: `{below\|above}`, `{subject} {verb}`, one / two or three / more Sites, `{a\|an}`, "appended when k < n" | **Hard-coded choice; moves.** Picks, variants and parts (§5.2) |
| `frontend/src/ui/productWords.ts`, `outcomes/asset_words.py`, `structure/registry.py` `words`, `structure/sources.py` ASSUMED words | Code-to-words maps with a neutral fallback | **Fits** as vocabulary. Stays where it is until its area adopts (SC-1c) |
| `analytics/plain.py` (583 lines) | f-string sentences, `if` chains, regex restating of stored prose | **Hard-coded; moves** (SC-1c). Stored prose read by pattern is the worst class: it must become stored codes and figures |
| `fuel_balance/night_text.py`, `finding_api.py`, `mini_decisions_api.py`, `outcomes/price_action.py`, `actions/verification.py` | f-strings with units and figures | **Hard-coded; moves** (SC-1c) |
| Frontend TSX (`LedgerSiteEvidence.tsx`, `SiteFinancials.tsx` `PRODUCTIVE_NOT_DECLARED`, `RunIngestionOverview.tsx`, about 110 files with template literals) | "Not available yet: …" and figure sentences typed in components | **Hard-coded; moves** (SC-1d): sentences with figures or states come from the server as rendered statements; static chrome (headings, button labels) stays in the frontend |
| Mock vNEXT `loop-decisions.js` `decText` (one function per decision: `kobo-generator`, `kisiwa-genset` …), `NOACT_WHY` (per option), `WHY_PICK` | Hand-written per-decision sentences with typed figures ("a forward replay of 61 days", "95% load", "possible $70", "35% at 5 am") | **Hard-coded, by instance; never copied.** The mock stays the content reference. Step 6's specs write one statement per *kind of decision* (lever and basis), fed by the evaluation's facts (§9) |
| Mock `REASON_RULES` (regex rewriting of manifest reasons), `uxNoRecReason` and `VIS` (plural ternaries), `SWITCH_WORD`, `PKEY`, `VNAME`, `CLAIM_WORD`, `RIGHT_WORD` | Pattern rewrites, inline plurals, word maps | Regex rewriting: **forbidden class** (D-SC1.13). Plurals: the `count` format. Word maps: **fit** as vocabulary |

## 3. The mechanism

Names (one per meaning): a **fact** is one typed value from the computed structure; a **figure** is a `Money`,
`Price`, `Quantity` or `Percent` fact; a **message** is what code hands over (a key and its facts); a **statement**
is the catalogue entry for a key; a **variant** is one of its sentences with its condition; a **slot** is a named,
typed field; a **part** is a slot filled by rendering another statement; the **vocabulary** is the catalogue's words;
**render** is the one function that turns a message into text (`served` is the same function returning the text with
its evidence words). Every closed list the mechanism uses lives in `i18n/schema.py` (§3.12).

### 3.1 Facts (`i18n/facts.py`; constructors validate; D-SC1.2, D-SC1.18, D-SC1.19)

Facts are plain classes with `__slots__`, immutable (`__setattr__` after `__init__` raises `AttributeError`), with
value equality, a hash over their fields and a `repr`. They are **not dataclasses**, so no generic encoder can walk
them (`json.dumps` raises `TypeError`, FastAPI's `jsonable_encoder` raises): they leave `i18n` only rendered or as
`to_wire` (§3.11). A constructor refuses with `TypeError` (wrong class) or `ValueError` (wrong value); `bool` is never
accepted where an `int` is asked.

| Fact | Fields | Constructor refuses |
|---|---|---|
| `Evidence` | `evidence: str` (in `schema.EVIDENCES` = `EVIDENCE_ORDER` without `NOT_AVAILABLE`), `origin: str \| None` (in `schema.ORIGINS`; the weakest origin, the caller computes it with `weakest_origin`), `reconciled: bool \| None` (3A7's standing; None: no reconciliation applies) | unknown evidence or origin; `NOT_AVAILABLE`, `NEUTRAL` (a figure with no value is `Absent`) |
| `Money` | `value: Decimal`, `currency: str` (three capitals), `evidence: Evidence` | non-Decimal, NaN or infinite value, None; missing evidence |
| `Price` | `value: Decimal`, `currency: str`, `unit: str` (a key of vocabulary `unit`, checked at render), `evidence: Evidence` | as `Money`; `evidence.reconciled` not None |
| `Quantity` | `value: Decimal`, `unit: str`, `evidence: Evidence` | as `Price` |
| `Percent` | `value: Decimal` (a fraction: 0.0101 is 1.01%; any finite value), `evidence: Evidence` | as `Price` |
| `Count` | `n: int` (≥ 0), `noun: str` (a key of vocabulary `noun`) | bool, negative |
| `KOfN` | `k: int`, `n: int` (0 ≤ k ≤ n, n ≥ 1), `noun: str` | out of order |
| `Month` | `year: int` (`datetime.MINYEAR` to `MAXYEAR`), `month: int` (1 to 12) | out of range |
| `Day` | `day: datetime.date` | a `datetime.datetime` (a subclass of `date`) |
| `Instant` | `at: datetime.datetime` (aware) | naive |
| `Word` | `vocabulary: str`, `key: str` | empty (unknown vocabulary or key is checked at render: the vocabulary is per locale) |
| `Name` | `text: str`, `source: str` (the record field it came from, e.g. `site.code`, `action.title`) | empty `text` or `source`; a control character in `text` |
| `State` | `value: str` (upper snake case) | another form |
| `Flag` | `value: bool` | non-bool |
| `Items` | `items: tuple[Fact, ...]` (one fact class throughout) | empty (no items is `Absent`); mixed classes; a repeated item (by equality); an `Absent` item |
| `Absent` | `reason: str` (upper snake case, e.g. `ACCOUNTS_ZERO`) | empty or another form |

A figure cannot be built without its evidence (owner: every figure carries its evidence class). A missing figure is
`Absent`, never `None` and never zero. `Evidence` is a field of figures, never a message param (`FACT_TYPE`).

### 3.2 A statement (data; `i18n/statements/<locale>/<area>.py`, one module per area)

Each module's body is an optional docstring and exactly one `Assign` to the name `STATEMENTS`; `ast.literal_eval` of
that assignment's value node succeeds (D-SC1.3). Shape:

```python
STATEMENTS = {
    "<area>.<name>": {
        "slots": {"<slot>": {"type": "<type>", "<option>": <value>, "absent": ["<REASON>", ...], "optional": False}},
        "variants": [
            {"id": "<variant id>", "when": <condition>, "requires": <condition>,
             "options": {"<slot>": {"<option>": <value>}}, "text": "<template>"},
        ],
        "exhaustive": "<state slot>",   # optional: the variants' conditions cover every value of that state
        "evidence": "inline",           # or "served" (D-SC1.18); default "inline"
        "rephrase": "never",            # or "allowed" (§3.10); default "never"
    },
}
```

- **Keys** are `<area>.<name>`, lower snake case, and name a kind of statement, never an instance: no Site code,
  option ID, decision ID or person in a key (D-SC1.13; `KEY_FORM` and the guard's `KEY_INSTANCE`).
- **Templates** hold literal words and bare fields `{slot}` only: no format spec (`{x:,.2f}`), no conversion
  (`{x!r}`), no index (`{x[0]}`), no literal brace. The format is the slot's, never the template's (D-SC1.4).
- **Variants** are tried in order; the first whose `when` holds is chosen. A variant without `when` holds always and
  must be last. A statement has either a last variant without `when`, or `exhaustive` (§3.7, `NOT_EXHAUSTIVE`).
- **`requires`** (optional) is a condition the chosen variant's words assert but do not select on; it is evaluated
  after the choice and must hold (`REQUIRES_FAILED`, D-SC1.20). Rule for authors: if the words claim a relation
  between facts (same sign, at most, equal counts), the relation is in `when` or in `requires`.
- **Variant ids** are unique within the statement, lower snake case. Cases and coverage name them (§3.8).
- **`options`** on a variant override the slot's display options for that variant, parts included (§3.6 step 6).
  Options keyed by slot name apply to every statement in the tree that declares that slot.
- **`part_only: true`** marks a statement that exists to be a part (§5.1's `reconciliation.gap`): it is never
  rendered directly (`PART_ONLY`), it is analysed at load only inside the chains that include it, and its
  `derived_from` may name figure slots declared by every statement that includes it.
- **Absence** (D-SC1.23). A slot may receive an `Absent` only if it declares `absent` (a list of upper snake reason
  codes). `optional: true` also lets the caller omit the fact, read as `Absent("OMITTED")` (`OMITTED` is then
  implicitly in its list). `pick`, `part`, `example` and `evidence` slots take no fact and declare neither.

### 3.3 Slot types and their one format each (`i18n/formats.py`; D-SC1.10, D-SC1.24, D-SC1.25)

Formats only display: they quantize, take the magnitude, add a sign. They never add, divide or compare figures; a
share, a difference, an allowed amount is computed by the caller and handed over as a fact. Every quantize uses
`DISPLAY = Context(prec=34, rounding=ROUND_HALF_EVEN, traps=[InvalidOperation, DivisionByZero, Overflow])`, with the
slot's rounding where it has one. Formats dispatch by table (`FORMATS[type]`, `ROUNDINGS[name]`), never by comparing
a string (§3.8.4, `MECH_BRANCH`).

| Type | Fact | English format | Options (default first) |
|---|---|---|---|
| `money` | `Money` | 5c §2.1 exactly: `q = value.quantize(Decimal("0.01"), rounding)`; magnitude `f"{abs(q):,.2f}"`; prefix `$` for USD, else `f"{currency} "`; negative `−` (U+2212) before the prefix; zero is prefix and `0.00` unsigned; never `-0` | `round`: `half_even` \| `down` \| `up` (`ROUND_DOWN` and `ROUND_UP` are toward and away from zero); `abs`: false \| true (print the magnitude); `signed`: false \| true (`+` before a positive); `evidence` (§3.3.1) |
| `price` | `Price` | money of `value` at 2 places when `value.normalize()` has at most 2 decimal places, else at 4 places half even; then ` ` + vocabulary `format` `per` + ` ` + the unit's `symbol` (`$1.25 per L`, `$0.4321 per kWh`) | `abs`; `evidence` |
| `quantity` | `Quantity` | 5c §2.1: `format(value.normalize(), "f")` (or quantized half even to `places`), thousands commas on the integer part, then ` ` + the unit's `symbol` (`L`, `kWh`) | `places`: `normal` \| an int; `abs`; `signed`; `evidence` |
| `percent` | `Percent` | `(value * 100)` quantized to `places`, then `%`; `normal` is `format(x.normalize(), "f")` (3A7's tolerance) | `places`: 0 \| 1 \| 2 \| `normal`; `round` as money; `evidence` |
| `count` | `Count` | `f"{n:,}"` + ` ` + the noun's `one` form when n == 1, else `other` | `bare`: false \| true (the number alone) |
| `k_of_n` | `KOfN` | `f"{k:,}"` + ` ` + vocabulary `format` `of` + ` ` + `f"{n:,}"` + ` ` + the noun's form by `n` (5c: `1 of 1 Site`, `2 of 3 Sites`) | — |
| `month` | `Month` | `month_year`: `October 2026`; `month`: `October` (vocabulary `month`) | `form`: `month_year` \| `month` |
| `day` | `Day` | `15 December 2026` | — |
| `instant` | `Instant` | `20 November 2026, 08:00 UTC` (converted to UTC; `UTC` from vocabulary `format`) | — |
| `word` | `Word` | the entry's form from its vocabulary | `vocabulary` (required: the vocabulary the fact must come from), `form`: `label` \| `in_sentence`; `article`: false \| true (the entry's declared `article` + ` ` first) |
| `name` | `Name` | `text` verbatim | — |
| `items` | `Items` | each item by `of` (a nested slot spec), joined `A`, `A and B`, `A, B and C` (vocabulary `format` `and`) | `of` (required), `order`: `given` \| `vocabulary` (items that are `Word`s, in their vocabulary's declared order) |
| `evidence` | none (reads figures) | the distinct evidence words (§3.5) of the covered figures that are present, in `of` order of first appearance, joined as `items`; none present is an absent field (`ABSENT_PRINTED`) | `of` (required: figure slots), `money`: false \| true (a `Money` whose `reconciled` is false reads its word + `, ` + the money suffix; 3A7 `money_word`) |
| `pick` | none (reads another slot) | one word chosen by a declared domain: `{"type": "pick", "on": "<state slot>", "words": {"<value>": "<word>", ...}}`, or `"on": {"sign": "<figure slot>"}` with `words` over `negative`, `zero`, `positive` | `domain` (default: every value of the state, or all three signs); proved at load (`PICK_REACH`, §3.7.1) |
| `part` | the same facts | renders statement `key` with this message's facts | `key` (required) |
| `example` | none | the declared `text` verbatim: a format example in a refusal (`like 2026-10`) | `text` (required) |
| `state`, `flag` | `State`, `Flag` | never printed (conditions and picks only) | `values` (required for `state`: the full list, no repeats) |

**Tiny** (D-SC1.24; always on, not an option): a non-zero `money`, `price`, `quantity` (integer `places`) or
`percent` (integer `places`) value that displays as zero reads vocabulary `format` `less_than` + ` ` + the smallest
displayed unit in magnitude (`less than $0.01`, `less than 0.1 L`, `less than 1%`, `less than $0.0001 per kWh`);
when the value is negative and the slot prints with `abs: false`, it reads `more_than` + ` ` + the smallest unit with
its sign (`more than −$0.01`). A `tiny` key in a slot is `SLOT_OPTION`.

#### 3.3.1 A figure's evidence on the page (D-SC1.18)

In an `inline` statement every figure slot declares `evidence`, one of:

- `"inline"`: the figure prints ` (` + its evidence word + `)` after itself (`$5.02 (Calculated)`);
- `{"with": "<evidence slot>"}`: an `evidence` slot whose `of` lists this figure is printed in the same rendered
  sentence (the chosen variant, or a variant above it on the chain of parts);
- `{"derived_from": ["<figure slot>", ...]}`: the figure is computed from those figures, each stated (below) with its
  own evidence shown in the same rendered sentence; at render its evidence must be no stronger than `DERIVED` and than
  its weakest present input (by `EVIDENCE_ORDER`), and its origin must equal the weakest of its present inputs'
  origins (by `ORIGIN_ORDER`, None weakest), else `EVIDENCE_DERIVED`.

A figure is **stated** by a rendering when a chosen variant on its chain prints it or reads it in its `when` or
`requires` (an earlier variant's failed `when` states nothing): "on target" states the gap as much as "$562.00 below
target" does. Missing `evidence`, or a stated figure whose evidence is not shown so: `EVIDENCE_UNSHOWN` at load (the
check runs over every chain, as §3.7.1 enumerates them). There is no `none`.

In a `served` statement figure slots declare no `evidence` (`SLOT_OPTION`); `render` refuses the statement
(`EVIDENCE_UNSERVED`) and `served` returns the evidence words of every figure stated: printed figures in text order,
then figures only read by conditions in slot declaration order, distinct. A statement and every part it
reaches have one mode (`EVIDENCE_MODE` at load).

### 3.4 Conditions (data; `i18n/conditions.py`, one evaluator; D-SC1.5, D-SC1.23)

A condition is a dict with one operator key. Operands are a slot path (a string: `gap`, `sites.k`, `sites.n`,
`budgets.count`), `{"abs": <operand>}`, or `{"const": <int or decimal string>}`. Constants appear only in
conditions, never in text. The evaluator dispatches by `OPERATORS[op]`.

| Operator | Form | Holds when |
|---|---|---|
| `present` | `{"present": "slot"}` | the fact is given and is not `Absent` |
| `absent` | `{"absent": "slot"}` | not `present` |
| `reason` | `{"reason": ["slot", "CODE"]}` | the fact is `Absent` with that reason (`CODE` in the slot's `absent` list, `OMITTED` for an optional slot) |
| `is` | `{"is": ["slot", VALUE]}` | a `State` equals VALUE (a string in its `values`), or a `Flag` equals VALUE (Python `True` or `False`) |
| `sign` | `{"sign": ["slot", "negative" \| "zero" \| "positive"]}` | the figure's exact value has that sign |
| `cmp` | `{"cmp": [<operand>, "<" \| "<=" \| "==" \| ">=" \| ">", <operand>]}` | the exact values compare so. Integer paths (`Count`, `.k`, `.n`, `.count`) compare with each other and with a const; a figure compares with a const or with a figure of the same class and currency or unit, else `CONDITION_TYPE` at render |
| `all`, `any` | `{"all": [c, ...]}` | every / some condition holds |
| `not` | `{"not": c}` | c does not hold |

Paths: `x` is the fact's exact value (`Money.value`, `Count.n`, `Percent.value`); `x.k` and `x.n` on `KOfN`;
`x.count` on `Items` (number of items). A condition over an `Absent` fact other than `present`, `absent` and `reason`
is false.

### 3.5 Vocabulary (data; `i18n/statements/<locale>/vocabulary.py`, `VOCABULARY = {...}`, a pure literal)

`VOCABULARY = {"<vocabulary>": {"forms": [...], "order": [<keys>], "entries": {"<key>": {"label": ..., "in_sentence":
..., "article": ..., "one": ..., "other": ..., "symbol": ...}}}}`. Each vocabulary declares which forms its entries
carry; every entry carries each declared form (`VOCABULARY_FORM`). Forms are declared, never derived by a letter rule
(D-SC1.8). Vocabulary words are literals under §3.7's digit, symbol and number-word rules; only the `unit`
vocabulary's `symbol` form may hold `²` or `³` (D-SC1.21).

SC-1a ships these English vocabularies, transcribed exactly:

| Vocabulary | Source | Forms |
|---|---|---|
| `factor` | 5c §2.2 `FACTOR_LABELS` (every key, in that order); `in_sentence` is 5c's `lower(label)` applied once by hand; `article` `a` or `an` by the in-sentence word's sound (`an O&M`, `an unexplained fuel`, `a fuel cost`) | label, in_sentence, article |
| `heading` | 5c §2.2 `HEADINGS` (four keys = `CATEGORIES`' names), plus 3A7's heading names and words: `revenue` (`Revenue` / `revenue`), `fuel_cost` (`Fuel cost` / `fuel cost`) under keys `REVENUE`, `FUEL_COST` | label, in_sentence |
| `headline_subject` | 5c §2.5: `OPTIMIZE_COST` "cost and efficiency explain", `GROW_REVENUE` "Grow revenue explains" | in_sentence |
| `record` | 5c §2.3 `RECORDS`, its order, its words (BUDGET_LINES excluded: it is a statement, `common.budget_lines`, §5.3) | in_sentence |
| `record_noun` | 3A7: `REVENUE` "billing records", `FUEL_COST` "fuel invoices" | in_sentence |
| `evidence` | 5c §2.4, special shape (below) | special |
| `unit` | `L` → `L`, `kWh` → `kWh` | symbol |
| `noun` | `site` Site / Sites; `budget_disagreement` budget disagreement / budget disagreements; `reading` reading / readings | one, other |
| `month` | January … December | label |
| `format` | `less_than` "less than", `more_than` "more than", `and` "and", `of` "of", `per` "per", `utc` "UTC" (the only words the formats print) | in_sentence |

The `evidence` vocabulary holds the words and tables of 5c §2.4 as data:
`{"by_evidence_first": {"ESTIMATED": "Estimated", "MODELLED": "Modelled"}, "by_origin": {"source-emulated":
"Emulated", "demo-simulated": "Simulated", "unknown": "Estimated"}, "no_origin": "Estimated", "observed_by_evidence":
{"RECORDED": "Recorded", "DECLARED": "Recorded", "MEASURED": "Measured", "DERIVED": "Calculated"}, "money_suffix":
"not yet reconciled"}`. The `evidence` format applies them by a fixed three-step algorithm (it is a format, not data):
(1) the evidence in `by_evidence_first`; else (2) origin None reads `no_origin`, an origin in `by_origin` reads its
word; else (3) `observed_by_evidence[evidence]`. `VOCABULARY_SCHEMA` proves the tables cover the schema exactly:
`by_evidence_first` and `observed_by_evidence` keys partition `schema.EVIDENCES`; `by_origin` keys and the three
observed origins partition `schema.ORIGINS`; no word reads "Verified" (5c §2.4). A figure whose origin is None or
`unknown` reads "Estimated" whatever its evidence: a figure whose source cannot be named is not claimed as recorded.
`NOT_AVAILABLE` has no word here: an absent figure is worded by `common.not_available`.

### 3.6 Render (`i18n/render.py`; one function, two return shapes; D-SC1.1, D-SC1.18)

`render(msg: Message, locale: str | None = None) -> str` stays the entry point; `served(msg, locale=None) ->
Served` (a `TypedDict` `{"text": str, "evidence": list[str]}`) is the same internal function returning the evidence
words too. Neither takes a catalogue (D-SC1.22). For a structured statement:

1. **Locale.** The statements of the request's locale if `statements/<locale>/` exists (load proved it complete,
   `LOCALE_INCOMPLETE`), else English. No per-key fallback (D-SC1.20). Unknown key: `KeyError` (as today).
   `render` of a `served` statement: `EVIDENCE_UNSERVED`; `served` of an `inline` one: `EVIDENCE_MODE`.
2. **Facts against slots.** The statement's slots are its own and those of every part it reaches. Every fact names
   one of them (`FACT_UNKNOWN`); every slot that takes a fact and is not `optional` has one (`FACT_MISSING`); every
   fact is of its slot's class, or an `Absent` for a slot that declares `absent` (`FACT_TYPE`), whose reason is in
   the list (`ABSENT_REASON`); a raw `str`, `int`, `float`, `Decimal` or an `Evidence` is never a fact
   (`FACT_TYPE`); a `word` fact comes from the slot's `vocabulary` and exists in it, a unit or noun exists in its
   vocabulary (`VOCABULARY_UNKNOWN`); every given figure whose slot declares `derived_from` passes §3.3.1
   (`EVIDENCE_DERIVED`).
3. **Choose** the first variant whose `when` holds (§3.4). None holds: `NO_VARIANT` (a defence: load and step 2 make
   it unreachable).
4. **Require.** The chosen variant's `requires`, if any, holds, else `REQUIRES_FAILED`.
5. **Fill** each field of the chosen variant, and only those (a pick or part in a variant not chosen is never
   evaluated): the slot's format with the slot's options, overridden by the variant's `options`, and its evidence per
   §3.3.1. An `Absent` fact in a printed field: `ABSENT_PRINTED`. A pick value outside its domain: `PICK_DOMAIN` (a
   defence: `PICK_REACH` makes it unreachable).
6. **Parts** render their statement through steps 3 to 6 with the same facts and the parent variant's `options` for
   facts of the same name (a part's own slot declarations decide which facts it reads; facts it does not declare are
   ignored for that part). Depth at most 4.
7. Return the text (and, for `served`, the evidence words of the stated figures, §3.3.1). A `part_only` key
   rendered directly: `PART_ONLY`. Errors are `StatementError(code, key, variant, slot)`, a `ValueError` subclass, carrying codes
   only. There is no fallback text: a statement that cannot be rendered truthfully raises (D-SC1.11).

For a legacy entry (a plain string, §3.9) render does exactly what it does today, including its per-key English
fallback.

`message(key, **facts)` keeps its signature; `Param` becomes `str | int | float | Fact`. A structured statement
refuses `str`/`int`/`float` params; a legacy entry refuses `Fact` params (`FACT_TYPE`), so the two never mix.

### 3.7 The load check (`i18n/catalogue.py`; runs once at import, and in the guard)

Loading merges `messages.CATALOGUE` (legacy strings, untouched) and every `i18n/statements/<locale>/*.py` module
into the catalogue `render` reads (`render.py` imports from `catalogue`, not `messages`), then validates. Any failure
raises `CatalogueError(code, key, detail)` (detail: a slot, variant, path or value, never prose) at import, so a bad
catalogue never serves. Tests build catalogues only through `catalogue._build(statements, vocabulary)`, the same
validator, and install one with `catalogue._use(cat)` (D-SC1.22).

| Code | Fails when |
|---|---|
| `NOT_DATA` | a statements or vocabulary module's body is anything but an optional docstring and one `Assign` to `STATEMENTS` / `VOCABULARY` whose value passes `ast.literal_eval` |
| `KEY_DUPLICATE` | a key appears twice across modules or in both a module and `messages.CATALOGUE`; or any `ast.Dict` in a module's value repeats a constant key (statement keys, slots, options, entries; detail: the dict's path) |
| `KEY_FORM` | a key is not `<area>.<name>` lower snake case (no digits) |
| `SLOT_TYPE`, `SLOT_OPTION`, `SLOT_CONFLICT` | an unknown type; an option not in §3.3 for that type, a bad or repeated option value, a required option missing, a `tiny` key, an `evidence` option in a `served` statement, a bad `absent` list, or a variant `options` naming a slot that neither the statement nor its parts declare; one name declared with two types or option sets across a statement and its parts |
| `FIELD_UNDECLARED`, `FIELD_FORM` | a template field that is not a declared slot; a field with a format spec, conversion or index, or a stray brace |
| `LITERAL_DIGIT`, `LITERAL_SYMBOL`, `LITERAL_NUMBER_WORD` | in a template's literal text or any vocabulary word: a character of Unicode category `Nd`, `No` or `Nl` (`²`, `³` allowed in `unit` `symbol` only); a character of category `Sc` or one of `% ‰ ‱ ٪ ﹪ ％`; a token (the literal split on non-letters), case-folded, that is a root joined to a suffix of one of
`schema.NUMBER_WORDS[locale]`'s `(roots, suffixes)` pairs (D-SC1.21, D-SC1.32). Digits reach text only through figure, count, date and name slots, the formats' own precision (tiny) and `example` slots |
| `STATE_PRINTED` | a `state` or `flag` slot used as a template field |
| `CONDITION_OPERATOR`, `CONDITION_SLOT`, `CONDITION_VALUE` | (in `when` and `requires`) an unknown operator or extra key; a path to an undeclared slot or field; an `is` value outside the state's `values` or not a bool for a `Flag`, a `sign` word outside the three, a `reason` code not in the slot's list |
| `NO_FALLBACK` | the last variant has a `when`, and no `exhaustive` (depends on the last variant only) |
| `NOT_EXHAUSTIVE` | with `exhaustive`, a variant whose `when` is not `is` on that slot or `any` of such; or the union of their values misses a declared value |
| `VARIANT_ID` | a missing, repeated or badly formed id; a variant without `when` that is not last |
| `PICK_INCOMPLETE` | a pick whose `words` miss a value of its domain, or name one outside it |
| `PICK_REACH` | a pick is reachable for a value outside its domain (§3.7.1) |
| `PART_UNKNOWN`, `PART_CYCLE` | a part key that is not a structured statement; a cycle, or depth over 4 |
| `EVIDENCE_UNSHOWN`, `EVIDENCE_MODE` | §3.3.1: a figure slot in an `inline` statement without `evidence`, or printed in a variant chain that does not show it as declared; a statement and a part it reaches with different modes, or `evidence` not `inline`/`served` |
| `VOCABULARY_FORM`, `VOCABULARY_SCHEMA` | an entry missing a declared form; an `order` that is not exactly the entries' keys; a bad `evidence` shape, tables not partitioning the schema (§3.5), or the word "Verified" |
| `LOCALE_INCOMPLETE` | a `statements/<locale>/` other than `en` lacks an English key, or one of its statements differs from English in variant ids, slot names, slot types or mode; or `schema.NUMBER_WORDS` has no entry for it |
| `REPHRASE` | `rephrase` not `never` or `allowed`; `part_only` not a bool |

#### 3.7.1 `PICK_REACH`: the reachability analysis

For every structured statement that is not `part_only`, taken as a root (any such key can be rendered directly),
and every chain of variants from
the root down through parts to a variant V that prints a pick reading slot X:

- the **path condition** is the conjunction, over each variant W on the chain, of `when(W)` (true when absent),
  `requires(W)`, and `not when(U)` for every variant U before W in its statement;
- the **values** of X are the three signs (for `{"sign": X}`) or the state's `values`, plus `ABSENT` when X declares
  `absent` or `optional`;
- for each value v outside the pick's domain, evaluate the path condition in three-valued (Kleene) logic with X fixed
  to v and every atom not about X `Unknown`. Atoms about X: `present`/`absent` decided; `reason` false for a present
  v and `Unknown` for `ABSENT`; `sign` and `is` decided (false for `ABSENT`); `cmp` of X or `{"abs": X}` against
  `{"const": 0}` decided from the sign; any other atom `Unknown`;
- if the result is not `False`, fail `PICK_REACH key variant slot value`.

§5.2's `direction` passes: on `gap_only`, `more_than_gap` and `share_of_gap`, `not absent gap` and `not sign gap zero`
are on every path. §5.1's `reconciliation.gap` passes by `same`.

### 3.8 The guard (`tools/checks/statement_catalogue.py`; check-all, with `--self-test`; D-SC1.12, D-SC1.17)

The guard puts `backend` on `sys.path` itself (as `neutral_tests.py` does), so the `Add-Guard` lines need no
environment.

1. **Load.** Imports the catalogue; a `CatalogueError` fails the guard with its code and key.
2. **Coverage.** Every variant id of every structured statement has at least one case in
   `backend/tests/statement_cases/*.py` (each module `CASES = [Case(key, variant, facts, english, evidence=None),
   ...]`; `evidence` is the expected list for a `served` statement and must be None for an `inline` one; `Case` from
   `backend/tests/statement_cases/__init__.py`). Missing: `CASE_MISSING key variant`. A case naming an unknown key or
   variant, or with `evidence` set wrongly for the mode: `CASE_UNKNOWN`. A case covers its root variant and every
   part variant its rendering chooses: the guard renders each case through the internal function with a trace of the
   chosen chain (coverage only; whether the text equals the case's English is T9's job). A case whose root variant is
   not the one named: `CASE_VARIANT`. A `part_only` statement is covered through its parents' cases.
3. **Legacy ratchet** (D-SC1.27). `tools/checks/statement-legacy-baseline.json` maps each legacy key (plain string in
   `messages.CATALOGUE["en"]`) to the first 16 hex of the SHA-256 of its UTF-8 template, sorted. A legacy key not in
   it: `LEGACY_NEW key`. A template whose hash differs: `LEGACY_CHANGED key`. A baseline key that is no longer legacy
   is removed in the same commit (`LEGACY_STALE` until it is).
4. **Hand-built text scan**, three scopes (below).
5. **Instances in keys.** `KEY_INSTANCE key token`: a statement key segment, variant id or vocabulary key, split on
   `_` and `.`, holds a token (case-folded, 3 or more letters) found under a JSON or YAML key named `site_id`
   or `site_code` at any depth in `config/**/*.{yaml,yml,json}` and `backend/conversions/*.json`, split on
   non-letters. A test asserts the token set contains `kisiwa` and `kobo` (else the source is wrong: a mid-build
   question).
6. `--self-test` runs plants P12 to P14, P13a to P13q, P17, P42 to P49, P49a to P49d, P51 to P53, P51a to P51d,
   P55a to P55c, P56, P57a to P57e and the negative plants N1 to N13 (§6) against temporary copies and passes only if
   each plant fails with its code and each negative plant passes.

Wire in `tools/check-all.ps1` next to the fuel wording guard: `Add-Guard "Statement catalogue (SC-1)" $Python
@("tools/checks/statement_catalogue.py")` and the `--self-test` line.

#### 3.8.4 The scan

All three scopes read Python through `ast`, as `fuel_wording.py` does (reuse `_bare_strings` for docstrings).
**Exempt everywhere:** docstrings and bare string statements; the arguments of logging calls (a call whose function
is an attribute `debug`, `info`, `warning`, `error`, `exception`, `critical` or `log` of a name `logger`, `log`,
`logging`, `_log`, `_logger`, `_LOGGER` or `LOG`, of an attribute with one of those names (`self.logger`), or of a
`logging.getLogger(...)` call; logs are never served, D-SC1.33); the arguments of `raise U(...)` where `U` is in
`schema.UNSERVED` (`ValueError`, `TypeError`, `KeyError`, `LookupError`, `RuntimeError`, `AssertionError`,
`NotImplementedError`, `StatementError`, `CatalogueError`, `WireError`, and any backend class a unit's spec adds,
D-SC1.34). For each backend class in `UNSERVED`, a handler naming it whose body reads the caught name other than in
`raise ... from e`, `isinstance(e, ...)` or a logging call is `UNSERVED_SERVED path:line class` (P56). Any other raised call (`HTTPException`, a
`_refuse(...)`, an `APIError`) is scanned like any call. **Served exception text** is a hit in every scope: `str(e)`,
`e.args` or an f-string field `{e}`, where `e` is bound by `except ... as e`, anywhere but a logging call or a
`raise U(...)` of an `UNSERVED` type.

**(1) Mechanism** (the modules SC-1 writes in `backend/assetops_backend/i18n/`: `__init__`, `schema`, `facts`, `formats`,
`conditions`, `catalogue`, `render`, `wire`; not `statements/`; D-SC1.29). `messages.py` and `locale.py` are the two
pre-existing modules, named in the guard as `LEGACY_I18N` and read by scope (3). The guard walks `i18n/**/*.py`
(D-SC1.35): each file is a mechanism module (directly in `i18n/`), `LEGACY_I18N` (directly in `i18n/`), a package
marker (`statements/__init__.py`, `statements/<locale>/__init__.py`: this scope's literal rule, no `MECH_BRANCH`), or a
data module directly in `statements/<locale>/` for a package the loader reads (proved by the load, `NOT_DATA`);
anything else, at any depth, is `MECH_UNSCOPED path` (P51, P51a to P51c). Every string constant, outside the
exemptions and `__all__`, is one of: an upper snake code (`^[A-Z][A-Z0-9_]*$`) that is not a state value, absent
reason or vocabulary entry key of the loaded catalogue (else `MECH_INSTANCE`); a member of `schema.TOKENS` (§3.12);
a member of `schema.SYMBOLS`; a decimal literal (`^\d+(\.\d+)?$`); or an f-string field's format spec matching
`^,?(\.\d+)?[fd]?$`. Anything else, including an f-string literal part outside `SYMBOLS`: `MECH_LITERAL path:line`.
In `formats.py`, `conditions.py`, `render.py` and `wire.py`, a `Compare` with a string constant operand, a `match`
with a string pattern, or an `IfExp` with a string constant branch is `MECH_BRANCH path:line`: they dispatch by table.
(`catalogue.py`, `facts.py` and `schema.py` validate shapes and are exempt from `MECH_BRANCH` only.)

**(2) Adopted** (`ADOPTED`, a tuple of repo paths in the guard; empty in SC-1a, proved on plants; 3A7 adds
`commercial/reconciliation.py`, 5c adds `deep_dive/words.py` and `deep_dive/view.py`). A positive rule; each of these
is `HAND_BUILT path:line`:

- a string constant that is not code-form. Code-form: matches `^[A-Za-z0-9_.\-]*$` and has no capital followed by a
  lower-case letter. A plain lower-case word (`^[a-z]+$`) is code-form only as a dict-literal key, a subscript index,
  the second argument of `getattr`/`hasattr`, or an argument of `message`, `Word`, `Count`, `KOfN`, `Quantity`,
  `Price`, `Absent`, `State`, `Evidence` or `Name`'s `source` (keys, not words); a single non-letter character is
  code-form;
- a `Compare` with a string constant operand that is not upper snake (a branch on wording);
- any f-string; `%` with a string left operand; a `.format` or `.format_map` call; `string.Template` or `Template`;
  any `textwrap` call; `.capitalize`, `.title`, `.swapcase`; `.replace` with two string constant arguments;
  `re.sub`, `re.subn`; `.join` on a string constant receiver; `+` or `+=` with a string constant, f-string or
  `str(...)` operand; an `IfExp` with a string constant branch; served exception text.

**(3) Ratchet** (every other `.py` under `backend/assetops_backend/`, outside `i18n/` and `ADOPTED`, plus `LEGACY_I18N`;
the plain-string template values of `messages.CATALOGUE[locale]` are judged by the legacy ratchet alone, §3.8.3,
D-SC1.37). Served text is defined in D-SC1.33. Negative rules, where *prose* (D-SC1.33) is a literal that does not
lead with SQL (its first word, after spaces and an optional `(`, is not one of `SQL_LEAD`: `SELECT INSERT UPDATE
DELETE WITH CREATE ALTER DROP FROM WHERE AND OR JOIN LEFT INNER ORDER GROUP SET VALUES RETURNING ON LIMIT OFFSET CASE
HAVING UNION`, upper case) and, split on whitespace, has a prose pair: two adjacent tokens, the first not ending in
punctuation, that are both *words* with a lower-case letter in either, or a word of three or more letters with a
lower-case letter beside an *identifier*. A word is a token of letters (inner `'` or `-` allowed; a trailing `(s)`
ignored) once opening quotes or brackets and closing quotes, brackets and `.,;:!?` are stripped, and is not in
`SQL_WORDS` (upper case) nor `asc`, `desc`, `nulls` (any case). An identifier is letters and digits joined by `_` or
`.` (`site_id`, `u.reader`), the same stripping applied. `SQL_LEAD` and `SQL_WORDS` are constants of the guard, not
of `schema` (`SQL_WORDS`: `SELECT FROM WHERE JOIN LEFT RIGHT INNER OUTER FULL CROSS ON USING AND OR NOT NULL IS IN AS
BY ORDER GROUP HAVING LIMIT OFFSET DISTINCT INSERT INTO VALUES UPDATE SET DELETE RETURNING WITH CREATE ALTER DROP
TABLE INDEX CASE WHEN THEN ELSE END EXISTS ANY ALL UNION BETWEEN LIKE ILIKE ASC DESC CONFLICT DO NOTHING CAST COALESCE
COUNT SUM MIN MAX FOR SKIP LOCKED NULLS FIRST LAST INTERVAL TRUE FALSE PRIMARY KEY REFERENCES DEFAULT UNIQUE CONSTRAINT
LATERAL OVER PARTITION FILTER`). (a) an f-string with a prose literal part; (b) `%` or `.format`/`.format_map` on a prose constant; (c)
`string.Template`, `textwrap.fill`/`wrap`/`shorten`; (d) `+` or `+=` with a prose constant or an (a) operand; (e)
`.join` on a constant receiver holding a letter or whitespace, unless the join's result is immediately `.encode(...)`d,
or any `.join` whose argument is a list or tuple literal holding a string constant with a letter; (f) an `IfExp` with a
string constant branch that is prose, or holds two adjacent lower-case letters, is not code-form for this rule
(`^[A-Za-z0-9_.\-/+:]*$` with no capital followed by a lower-case letter) and does not lead with SQL; (g) a prose string constant anywhere, except the keyword arguments `help`, `description`,
`epilog`, `usage`, `summary` of `add_argument`, `ArgumentParser`, `add_parser`, `APIRouter`, `FastAPI` and route
decorators (static chrome, Q3); (h) `.capitalize`, `.title`; `.replace` or `re.sub`/`re.subn` whose replacement
constant holds a letter or whitespace; (i) in a dict literal with two or more string values matching `^[A-Z][a-z]` (a
word map), each such value that is not prose, one hit per entry (D-SC1.37); (j) served exception text. Each hit is
fingerprinted `<rule>:<enclosing qualified name or <module>>:<sha1 of ast.unparse(node)>[:12]` (for (i), the sha1 of the
entry's key source, a NUL and its value); `tools/checks/statement-handbuilt-baseline.json` maps each path to its
sorted fingerprints (repeats kept, compared as multisets). A hit not in the baseline: `HAND_BUILT_NEW path:line
fingerprint`. A baseline fingerprint with no hit, or an entry for an `ADOPTED` path: `HAND_BUILT_STALE`.
`--write-baseline` writes the file only when it does not exist (`BASELINE_EXISTS` otherwise); `--prune` removes stale
entries and never adds. Adding a served fingerprint is a hand edit its unit's spec names (D-SC1.34; reviewer guide
10). A code string the scan misreads goes in `tools/checks/statement-handbuilt-allow.json` (`{path: [{"fingerprint",
"class", "why"}]}`, class `SQL`, `HASH` or `CODE`, `why` one line of at most 200 characters); an allowed fingerprint
counts as baselined; `ALLOW_CLASS` (other class or empty `why`), `ALLOW_STALE` (no hit; `--prune` removes it),
`ALLOW_SCOPE` (an `ADOPTED` or `i18n/` path). The file starts as `{}`.

**Known holes, stated** (ratchet scope only; neither the mechanism nor `ADOPTED` has them, because their positive
rule leaves no string to compose with): variable-plus-variable concatenation; a join of a computed list with a
separator holding no letter or space, or encoded at once; a single word outside a word map or a display conditional;
an identifier beside one short word (`"policy_version required"`); a sentence whose first word is an upper-case SQL
word; prose assembled from non-prose pieces; text reaching a person through one of the 229 handlers already in the
baseline that show an exception's text (rule (j); a new one is caught; SC-1b and SC-1c convert them). The frontend is SC-1d's
(`frontend-hardwiring.mjs`).

**Imports from outside `i18n/`** (D-SC1.22, D-SC1.36). Each of `messages`, `locale`, `render`, `facts`, `wire` declares
`__all__` (else `I18N_SURFACE module`). A name imported from one of them, or read as an attribute of a name bound to one
or of its full dotted path, that is in neither that module's `__all__` nor `i18n.__all__` is `I18N_BYPASS` (P49a to
P49c); a reference to a `_` name stays `I18N_PRIVATE`.

### 3.9 Legacy entries

A plain string in `messages.CATALOGUE` is a legacy statement: one variant, untyped params, rendered as today, not
checked for digits (its params are already text), pinned by hash (§3.8.3). They stay legal so nothing breaks. No new
legacy key is added except those of 3A6 (D-SC1.27). SC-1b converts the rest.

### 3.10 The rephrase layer (contract only; not built in SC-1; D-SC1.15)

A later `i18n/rephrase.py` may offer an LLM rewording of a rendered statement whose `rephrase` is `allowed`. The
renderer passes the template text and the facts' rendered forms; the result is accepted only if (a) the multiset of
digit runs in it equals the template text's, (b) every `name`, `word` and `evidence` rendering in the template text
appears verbatim in it, (c) it adds no digit, currency symbol or `%`, and (d) it is at most twice the template text's
length. Otherwise the template text is shown. Default `never`. `never` is mandatory for `reconciliation.*`, refusals,
and any statement with a figure or `evidence` slot, until the owner says otherwise (decision queue Q1).

### 3.11 The wire form (`i18n/wire.py`; D-SC1.19)

`to_wire(msg) -> dict` and `from_wire(obj) -> Message` are exact inverses; `from_wire` is strict and raises
`WireError(code, path)` (`ValueError`; code `WIRE_FORM`) on a fact name that is not a string (checked first, P40b), an
unknown fact name, a missing or extra field, or a value
of the wrong JSON type, then runs the fact's own constructor. Form: `{"key": k, "params": {name: <wire>}}`, where a
legacy `str`/`int`/`float` param stays itself and a fact is an object with `"fact"` (its type name in §3.3) and:

| Fact | Fields (JSON) |
|---|---|
| `money` | `value` (`str(Decimal)`, exponent and trailing zeros kept), `currency`, `evidence` |
| `price` | `value`, `currency`, `unit`, `evidence` |
| `quantity` | `value`, `unit`, `evidence` |
| `percent` | `value`, `evidence` |
| evidence object | `{"evidence": str, "origin": str \| null, "reconciled": bool \| null}` |
| `count` / `k_of_n` | `n`, `noun` / `k`, `n`, `noun` (JSON integers) |
| `month` / `day` / `instant` | `year`, `month` / `day` (`YYYY-MM-DD`) / `at` (`isoformat()`, offset kept) |
| `word` / `name` / `state` / `flag` | `vocabulary`, `key` / `text`, `source` / `value` / `value` (bool) |
| `items` / `absent` | `items` (a list of wire facts) / `reason` |

`chain/period_read.is_message` and the refusal envelopes (`commercial_upload_api._refusal`, `work_api._refuse`) do not
change in SC-1a: they refuse a structured message (its params are objects), which is correct while nothing structured
is stored or sent. The first unit that stores or sends one makes them accept `to_wire` output (a `wire.is_wire` check)
and renders with `from_wire` at read; that unit's spec says so.

### 3.12 The schema (`i18n/schema.py`; the closed lists, written from this section exactly)

`TYPES` (§3.3's types); `OPTIONS` (per type, each option with its allowed values); `FIELDS` (`slots`, `variants`,
`exhaustive`, `evidence`, `rephrase`, `part_only`, `id`, `when`, `requires`, `options`, `text`, `type`, `absent`, `optional`,
`forms`, `order`, `entries`, and §3.5's form and `evidence` table names); `OPERATORS` (§3.4's nine) and `COMPARATORS`
(`<`, `<=`, `==`, `>=`, `>`); `SIGNS`; `MODES` (`inline`, `served`); `REPHRASE` (`never`, `allowed`); `EVIDENCES`;
`EVIDENCE_ORDER`, `ORIGINS` (= `ORIGIN_ORDER`), copied from `structure.evaluate` (no import; T12 proves parity);
`FORMAT_VOCABULARIES` (`format`, `unit`, `noun`, `month`, `evidence`); `FORMAT_WORDS` (§3.5 `format` keys);
`NUMBER_WORDS` (D-SC1.32; a tuple of `(roots, suffixes)` pairs; a number word is a root joined to a suffix of its
pair: `{"en": ((("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
"twelve", "hundred", "thousand", "million", "billion", "trillion"), ("", "s", "th", "ths", "fold")), (("thir", "four",
"fif", "six", "seven", "eigh", "nine"), ("teen", "teens", "teenth", "teenths")), (("twen", "thir", "for", "fif", "six",
"seven", "eigh", "nine"), ("ty", "ties", "tieth", "tieths", "tyfold")), (("first", "second", "third", "fifth",
"eighth", "ninth", "twelfth"), ("", "s")), (("once", "twice", "thrice", "single", "both", "pair", "couple", "dozen",
"half", "quarter", "percent"), ("", "s")), (("double", "triple", "quadruple", "halve"), ("", "s", "d")))}`); `UNSERVED` (§3.8.4); `SYMBOLS` (`""`, `" "`, `", "`, `"$"`,
`"−"`, `"+"`, `"%"`, `","`, `"."`, `"("`, `")"`, `" ("`, `"{"`, `"}"`, `":"`, `"-"`, `"T"`); `SYSTEM` (`STATEMENTS`,
`VOCABULARY`, `statements`, `vocabulary`, `utf-8`, `en`, `USD`, `OMITTED`, `ABSENT`). `TOKENS` is the union of
every set above except `SYMBOLS` and `NUMBER_WORDS` (D-SC1.32: a suffix such as `s` must never be a legal mechanism
constant). Adding to any of them is a spec change; T12 asserts each equals this section.

**Names read as identifiers, never written as strings (D-SC1.30).** The mechanism needs names no set above holds; it
reads them from code, so none is written as a string constant; whether a name is also in `TOKENS` through another set
does not matter (`abs` is a money option and `key` a part option, §3.3; D-SC1.38): the condition operand keys `abs` and
`const` (the annotation names of `conditions._Operand`, a private `TypedDict`); the `Message` keys `key` and `params`
(`Message.__annotations__`); the wire envelope's key `fact` (`wire._Envelope`'s annotations); and each fact's field names (`value`, `currency`, `origin`, `reconciled`, `n`, `k`, `year`, `at`,
`source`, and the rest of §3.1), which are its constructor's parameter names (`facts._FactMeta` builds `__slots__`
from them). A new such name is a new annotation or parameter, not a string. T12 asserts these sets equal this
paragraph; a plant writing one as a string constant is `MECH_LITERAL` (P52).

## 4. Code (SC-1a)

| File | Holds |
|---|---|
| `backend/assetops_backend/i18n/schema.py` | §3.12 |
| `backend/assetops_backend/i18n/facts.py` | §3.1; `__all__` |
| `backend/assetops_backend/i18n/formats.py` | §3.3 (one function per type, dispatched by table, reading vocabulary words; no English literal of its own; `DISPLAY`) |
| `backend/assetops_backend/i18n/conditions.py` | §3.4, and §3.7.1's three-valued evaluation over the same operator table |
| `backend/assetops_backend/i18n/catalogue.py` | loading, merging, §3.7; `CatalogueError`, `StatementError`; `_build`, `_use` |
| `backend/assetops_backend/i18n/render.py` | §3.6 (extends today's function; same signature) and `served`; `__all__` |
| `backend/assetops_backend/i18n/wire.py` | §3.11; `WireError`; `__all__` |
| `backend/assetops_backend/i18n/messages.py` | `Param` widened; `__all__` (D-SC1.36); `CATALOGUE` unchanged otherwise |
| `backend/assetops_backend/i18n/locale.py` | `__all__` only (D-SC1.36) |
| `backend/assetops_backend/i18n/__init__.py` | exports the fact classes, `served`, `Served`, `StatementError`, `to_wire`, `from_wire`, `WireError` (the public surface, D-SC1.22) |
| `backend/assetops_backend/i18n/statements/__init__.py`, `statements/en/__init__.py` | empty |
| `backend/assetops_backend/i18n/statements/en/vocabulary.py` | §3.5 |
| `backend/assetops_backend/i18n/statements/en/common.py` | §5.3 |
| `backend/tests/statement_cases/__init__.py`, `common.py` | `Case`; §5.3's cases |
| `backend/tests/statement_cases/worked.py` | §5.1, §5.2 and §5.4's cases, rendered through the test catalogue (`_build` of the worked statements, installed with `_use`); the guard's coverage skips keys absent from the shipped catalogue |
| `backend/tests/test_sc1_statements.py` | §6 T1 to T13 and the T-plants |
| `tools/checks/statement_catalogue.py`, `tools/checks/test_statement_catalogue.py` | §3.8, the guard plants and N1 to N13 |
| `tools/checks/statement-handbuilt-allow.json` | `{}` (D-SC1.34) |
| `tools/checks/statement-legacy-baseline.json`, `tools/checks/statement-handbuilt-baseline.json` | §3.8.3 and §3.8.4 (3), written once from `main` at branch time and rewritten from `main` after each merge of `main` into the branch (never by hand-adding) |
| `tools/check-all.ps1` | two `Add-Guard` lines |

No other file changes. `i18n` imports nothing from `assetops_backend` outside `i18n` (dependency direction).

## 5. Worked statements (the form every adopter follows)

Hand-computed (W2). §5.1, §5.2 and §5.4 are written by 3A7 and 5c in their own modules (D-SC1.26); SC-1a's tests use
copies of them in a test catalogue (`catalogue._build` and `_use`, tests only, D-SC1.22), so the mechanism is proved
on the real shapes before they land.

### 5.1 3A7's heading sentence (`i18n/statements/en/reconciliation.py`)

```python
"reconciliation.heading": {
    "slots": {
        "state": {"type": "state", "values": ["MATCHED", "NOT_MATCHED", "ZERO_STATED", "NOT_RECEIVED",
                                              "CURRENCY_MISMATCH", "MONTH_OPEN"]},
        "heading": {"type": "word", "vocabulary": "heading", "form": "label"},
        "records": {"type": "word", "vocabulary": "record_noun", "form": "in_sentence", "optional": True},
        "accounts": {"type": "money", "optional": True, "evidence": {"with": "basis"}},
        "recorded": {"type": "money", "optional": True, "evidence": {"with": "basis"}},
        "allowed": {"type": "money", "optional": True, "evidence": {"derived_from": ["accounts", "tolerance"]}},
        "tolerance": {"type": "percent", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
        "basis": {"type": "evidence", "of": ["accounts", "recorded", "tolerance"]},
        "month": {"type": "month", "optional": True},
        "record_currencies": {"type": "items", "of": {"type": "name"}, "optional": True},
        "currency": {"type": "name", "optional": True},
        "gap_words": {"type": "part", "key": "reconciliation.gap"},
        "share_words": {"type": "part", "key": "reconciliation.share"},
    },
    "variants": [
        {"id": "matched", "when": {"is": ["state", "MATCHED"]},
         "options": {"difference": {"round": "down"}, "allowed": {"round": "up"}},
         "text": "{heading} ({basis}): the accounts say {accounts} and the records say {recorded}, {gap_words}, within the {allowed} allowed ({tolerance})."},
        {"id": "not_matched", "when": {"is": ["state", "NOT_MATCHED"]},
         "options": {"difference": {"round": "up"}, "allowed": {"round": "down"}, "share": {"round": "up"}},
         "text": "{heading} ({basis}): the accounts say {accounts} and the records say {recorded}, {gap_words}{share_words}, beyond the {allowed} allowed ({tolerance})."},
        {"id": "zero_stated", "when": {"is": ["state", "ZERO_STATED"]},
         "text": "{heading} ({basis}): the accounts say {accounts} and no {records} are recorded."},
        {"id": "not_received", "when": {"is": ["state", "NOT_RECEIVED"]},
         "text": "{heading} ({basis}): the accounts say {accounts}, but no {records} are recorded for {month}."},
        {"id": "currency_mismatch", "when": {"is": ["state", "CURRENCY_MISMATCH"]},
         "text": "{heading}: the accounts are in {currency}, but the records are in {record_currencies}."},
        {"id": "month_open", "when": {"is": ["state", "MONTH_OPEN"]}, "text": "{heading}: {month} is not closed yet."},
    ],
    "exhaustive": "state",
    "rephrase": "never",
},
"reconciliation.gap": {
    "part_only": True,
    "slots": {"difference": {"type": "money", "abs": True, "optional": True,
                             "evidence": {"derived_from": ["accounts", "recorded"]}},
              "direction": {"type": "pick", "on": {"sign": "difference"}, "domain": ["negative", "positive"],
                            "words": {"negative": "less", "positive": "more"}}},
    "variants": [{"id": "same", "when": {"sign": ["difference", "zero"]}, "text": "the same"},
                 {"id": "differs", "requires": {"present": "difference"}, "text": "{difference} {direction}"}],
},
"reconciliation.share": {
    "part_only": True,
    "slots": {"share": {"type": "percent", "places": 2, "optional": True, "absent": ["ACCOUNTS_ZERO"],
                        "evidence": {"derived_from": ["difference", "accounts"]}}},
    "variants": [{"id": "shown", "when": {"present": "share"}, "text": " ({share})"},
                 {"id": "omitted", "text": ""}],
},
```

`zero_stated` prints `{accounts}` (a `Money` of 0.00: `$0.00`), not 3A7's literal "0.00" (D-SC1.9). `({basis})` is
the evidence word of the accounts, records and tolerance stated (D-SC1.18); the difference, allowed amount and share
are derived from figures in the same sentence, so their evidence is theirs. Cases (evidence: accounts `DECLARED`,
recorded `RECORDED`, tolerance `DECLARED`, allowed and difference and share `DERIVED`; origin `observed-financial`
unless the row says otherwise; `reconciled` None):

| # | Facts | English |
|---|---|---|
| C1 | NOT_MATCHED, `REVENUE`; accounts 501.50 USD; recorded 506.52; difference 5.02; allowed 5.015; share 0.0100099700897308; tolerance 0.01 | `Revenue (Recorded): the accounts say $501.50 and the records say $506.52, $5.02 more (1.01%), beyond the $5.01 allowed (1%).` |
| C2 | MATCHED, `FUEL_COST`; accounts 505.00 USD; recorded 504.996; difference −0.004; allowed 5.05; tolerance 0.01 | `Fuel cost (Recorded): the accounts say $505.00 and the records say $505.00, less than $0.01 less, within the $5.05 allowed (1%).` |
| C3 | MATCHED, `REVENUE`; accounts 1200.00; recorded 1200.00; difference 0; allowed 12.00; tolerance 0.005 | `Revenue (Recorded): the accounts say $1,200.00 and the records say $1,200.00, the same, within the $12.00 allowed (0.5%).` |
| C4 | NOT_MATCHED, `REVENUE`; accounts 0.00 KES; recorded 10.00 KES; difference 10.00; allowed 0.00; share `Absent("ACCOUNTS_ZERO")`; tolerance 0.01 | `Revenue (Recorded): the accounts say KES 0.00 and the records say KES 10.00, KES 10.00 more, beyond the KES 0.00 allowed (1%).` |
| C5 | CURRENCY_MISMATCH, `FUEL_COST`; currency Name `KES`; record_currencies `USD`, `EUR` | `Fuel cost: the accounts are in KES, but the records are in USD and EUR.` |
| C6 | MONTH_OPEN, `REVENUE`; month 2026-11 | `Revenue: November 2026 is not closed yet.` |
| C7 | ZERO_STATED, `FUEL_COST`; accounts 0.00 USD; records `FUEL_COST` | `Fuel cost (Recorded): the accounts say $0.00 and no fuel invoices are recorded.` |
| C8 | NOT_RECEIVED, `REVENUE`; accounts 900.00 USD; records `REVENUE`; month 2026-10 | `Revenue (Recorded): the accounts say $900.00, but no billing records are recorded for October 2026.` |
| C9 | C3's facts, with recorded and difference of origin `source-emulated` | `Revenue (Recorded and Emulated): the accounts say $1,200.00 and the records say $1,200.00, the same, within the $12.00 allowed (0.5%).` |

`difference` is optional because the heading's other states carry no difference; `differs` requires it, which is
also what keeps `ABSENT` out of `direction`'s reach (§3.7.1). C2 proves the always-on tiny and the variant's rounding reaching the part; C4 an absent optional part with a declared
reason; C9 two evidence words under one `basis` and a derived figure taking the weakest origin.

### 5.2 5c's headline (`i18n/statements/en/deep_dive.py`)

The view computes which heading is named and `big` (D-5C.15: the heading whose sum has the gap's sign); the
statement only words it, and its `requires` makes the sign relation its words assert a checked precondition.

```python
"deep_dive.headline": {
    "evidence": "served",
    "slots": {
        "gap": {"type": "money", "abs": True, "optional": True},
        "big": {"type": "money", "abs": True, "optional": True},
        "subject": {"type": "word", "vocabulary": "headline_subject", "form": "in_sentence", "optional": True},
        "month": {"type": "month", "form": "month"},
        "sites": {"type": "k_of_n"},
        "direction": {"type": "pick", "on": {"sign": "gap"}, "domain": ["negative", "positive"],
                      "words": {"negative": "below", "positive": "above"}},
        "compared": {"type": "part", "key": "deep_dive.compared"},
    },
    "variants": [
        {"id": "not_available", "when": {"absent": "gap"}, "text": "Contribution for {month} is not available yet."},
        {"id": "on_target", "when": {"sign": ["gap", "zero"]}, "text": "Contribution is on target in {month}.{compared}"},
        {"id": "gap_only", "when": {"absent": "big"}, "text": "Contribution is {gap} {direction} target in {month}.{compared}"},
        {"id": "more_than_gap", "when": {"cmp": [{"abs": "big"}, ">", {"abs": "gap"}]}, "requires": SAME_SIGN,
         "text": "Contribution is {gap} {direction} target in {month}; {subject} {big}, more than the whole gap.{compared}"},
        {"id": "share_of_gap", "requires": SAME_SIGN,
         "text": "Contribution is {gap} {direction} target in {month}; {subject} {big} of it.{compared}"},
    ],
},
"deep_dive.compared": {
    "evidence": "served",
    "slots": {"sites": {"type": "k_of_n"}},
    "variants": [{"id": "some", "when": {"cmp": ["sites.k", "<", "sites.n"]}, "text": " Compared for {sites}."},
                 {"id": "all", "text": ""}],
},
```

`SAME_SIGN` is written out in both variants (the module is a pure literal; no names):
`{"any": [{"all": [{"sign": ["gap", "negative"]}, {"sign": ["big", "negative"]}]}, {"all": [{"sign": ["gap",
"positive"]}, {"sign": ["big", "positive"]}]}]}`.

Cases (money evidence `DERIVED`, origin `source-emulated`; sites noun `site`; rendered with `served`):

| # | Facts | English | Evidence |
|---|---|---|---|
| H1 | gap −562.00 USD; big −412.00; subject OPTIMIZE_COST; month 2026-10; sites 3 of 3 | `Contribution is $562.00 below target in October; cost and efficiency explain $412.00 of it.` | `["Emulated"]` |
| H2 | gap −562.00; big −700.00; subject OPTIMIZE_COST; sites 2 of 3 | `Contribution is $562.00 below target in October; cost and efficiency explain $700.00, more than the whole gap. Compared for 2 of 3 Sites.` | `["Emulated"]` |
| H3 | gap 150.00; big omitted; sites 1 of 1 | `Contribution is $150.00 above target in October.` | `["Emulated"]` |
| H4 | gap 0.00; sites 1 of 2 | `Contribution is on target in October. Compared for 1 of 2 Sites.` | `["Emulated"]` (the gap is stated by `on_target`'s `when`) |
| H5 | gap omitted; sites 0 of 3 | `Contribution for October is not available yet.` | `[]` |
| H6 | gap 80.00; big 80.00; subject GROW_REVENUE; sites 3 of 3 | `Contribution is $80.00 above target in October; Grow revenue explains $80.00 of it.` | `["Emulated"]` |

H7 (gap −562.00, big +412.00) and H8 (gap −562.00, big +700.00) must raise `REQUIRES_FAILED` (P36).

### 5.3 Shared statements SC-1a ships (`i18n/statements/en/common.py`)

```python
"common.not_available": {
    "slots": {"needs": {"type": "items", "of": {"type": "word", "vocabulary": "record", "form": "in_sentence"},
                        "order": "vocabulary", "optional": True},
              "pending": {"type": "flag"}},
    "variants": [{"id": "analysing", "when": {"is": ["pending", True]}, "text": "Not analysed yet."},
                 {"id": "needs", "when": {"present": "needs"}, "text": "Not available yet: it needs {needs}."},
                 {"id": "plain", "text": "Not available yet."}],
},
"common.budget_lines": {
    "slots": {"factors": {"type": "items", "of": {"type": "word", "vocabulary": "factor", "form": "in_sentence"},
                          "order": "vocabulary"}},
    "variants": [{"id": "one", "when": {"cmp": ["factors.count", "==", {"const": 1}]}, "text": "a budget line for {factors}"},
                 {"id": "many", "text": "budget lines for {factors}"}],
},
```

`common.not_available` puts the honesty rule in data: "Not analysed yet" only while `pending` (system work) is true.
Cases: N1 pending true → `Not analysed yet.`; N2 pending false, needs `FUEL_INVOICES`, `BILLING` → `Not available
yet: it needs the billing export and fuel invoices with litres.` (vocabulary order); N3 pending false, needs omitted →
`Not available yet.`; B1 factors `om` → `a budget line for O&M`; B2 factors `staff`, `om` → `budget lines for O&M and
staff` (5c §2.2 order: `om` before `staff`).

### 5.4 Further worked shapes 5c and 3A7 need (test catalogue; R11)

```python
"deep_dive.share": {
    "evidence": "served",
    "slots": {"share": {"type": "percent", "places": 0}},
    "variants": [{"id": "widens", "when": {"sign": ["share", "positive"]}, "text": "{share} of what widens the gap"},
                 {"id": "offsets", "when": {"sign": ["share", "negative"]}, "text": "Offsets it"},
                 {"id": "no_effect", "requires": {"sign": ["share", "zero"]}, "text": "No effect"}],
},
"deep_dive.status_disagreement": {
    "slots": {"sites": {"type": "items", "of": {"type": "name"}, "order": "given", "absent": ["NONE"]},
              "total": {"type": "count", "absent": ["NONE"]}},
    "variants": [
        {"id": "none", "when": {"absent": "sites"}, "requires": {"absent": "total"}, "text": ""},
        {"id": "one", "when": {"cmp": ["sites.count", "==", {"const": 1}]},
         "text": "{sites}'s budget disagrees with its own lines."},
        {"id": "few", "when": {"all": [{"cmp": ["sites.count", ">=", {"const": 2}]},
                                       {"cmp": ["sites.count", "<=", {"const": 3}]}]},
         "text": "The budgets of {sites} disagree with their own lines."},
        {"id": "many", "requires": {"cmp": ["total", "==", "sites.count"]},
         "text": "The budgets of {total} disagree with their own lines."},
    ],
},
"reconciliation.scope": {
    "slots": {"scope": {"type": "state", "values": ["SITE", "ORGANISATION"]},
              "site": {"type": "name", "absent": ["ORGANISATION"]}},
    "variants": [{"id": "site", "when": {"is": ["scope", "SITE"]}, "text": "{site}"},
                 {"id": "organisation", "when": {"is": ["scope", "ORGANISATION"]},
                  "requires": {"reason": ["site", "ORGANISATION"]}, "text": "the organisation"}],
    "exhaustive": "scope",
},
```

The scope is a `State` with a `Name`, never one slot holding two classes; the possessive is the template's literal
`'s` after a name field, never a rule in code; "two or three" is `all` of two `cmp`; the count printed for "more" is
tied to the listed Sites by `requires`; "No effect" states the share through its `requires`, so its evidence is
served. Cases (share evidence `DERIVED`, origin `source-emulated`; Names from `site.name`, `site.code`):

| # | Facts | English | Evidence |
|---|---|---|---|
| SH1 | share 0.3333 | `33% of what widens the gap` | `["Emulated"]` |
| SH2 | share 0.125 | `12% of what widens the gap` (half even) | `["Emulated"]` |
| SH3 | share −0.2 | `Offsets it` | `["Emulated"]` |
| SH4 | share 0 | `No effect` | `["Emulated"]` |
| SH5 | share 0.004 | `less than 1% of what widens the gap` | `["Emulated"]` |
| SD1 | sites `Kisiwa`; total 1 site | `Kisiwa's budget disagrees with its own lines.` | — |
| SD2 | sites `Kisiwa`, `Mto`; total 2 | `The budgets of Kisiwa and Mto disagree with their own lines.` | — |
| SD3 | sites `Kisiwa`, `Mto`, `Kobo`, `Thika`; total 4 | `The budgets of 4 Sites disagree with their own lines.` | — |
| SD4 | sites `Absent("NONE")`; total `Absent("NONE")` | `` (empty) | — |
| SC1 | scope SITE; site `KOBO-001` | `KOBO-001` | — |
| SC2 | scope ORGANISATION; site `Absent("ORGANISATION")` | `the organisation` | — |

SD5 (four Sites, total 5) must raise `REQUIRES_FAILED` (P36). Prices are format rows (T2 F1 to F5).
`drawer_values` and `tile2_rest` (5c §2.5) use only these operators (`sign` of a derived figure against the gap's,
`requires` for the offsetting reading) and get their cases in 5c.

## 6. Tests (written first; `backend/tests/test_sc1_statements.py`; backend suite, no database)

- **T1 facts:** each constructor's refusals in §3.1, and P15, P37.
- **T2 formats** (hand literals): money `−1,234.50` → `−$1,234.50`, `0` → `$0.00`, `-0.001` → `less than $0.01` with
  `abs` and `more than −$0.01` without, KES prefix, `signed` `+$5.00`, `round` down/up on 5.015 (`$5.01`, `$5.02`),
  tiny on 0.004; price F1 1.25 USD per L → `$1.25 per L`, F2 0.4321 per kWh → `$0.4321 per kWh`, F3 1.2 → `$1.20 per
  L`, F4 KES 12.34567 per L → `KES 12.3457 per L`, F5 0.00004 USD per kWh → `less than $0.0001 per kWh`; quantity
  `1200.500` L → `1,200.5 L`, 100 and 1200 (exponent forms) → `100 L`, `1,200 L`, places 1 on 0.04 L → `less than 0.1
  L`; percent places 0/1/2/normal on 0.0101 and 0.005 (`1%`, `1.0%`, `1.01%`, `0.5%`), 1 → `100%`, places 0 on 0.004
  → `less than 1%`; count 1 and 2 Sites; k_of_n `1 of 1 Site`; month both forms; day; instant from UTC+3 to `… UTC`;
  items one, two, three, and `vocabulary` order; the evidence word for all 42 (evidence, origin) pairs (6 evidences x
  6 origins and None), by a hand table built from §3.5's three steps, and the money suffix.
- **T3 conditions:** each operator true and false, `reason` included; `abs`; dotted paths; integer paths against
  each other; a condition over `Absent` is false; comparing money in two currencies raises `CONDITION_TYPE`.
- **T4 render choice:** C1 to C9, H1 to H6, SH1 to SC2 through the test catalogue, exact strings and evidence lists.
- **T5 parts:** the parent variant's options reach the part (C2); a part ignores facts it does not declare.
- **T6 strictness:** `FACT_UNKNOWN`, `FACT_MISSING`, `FACT_TYPE` (a `str` for money; a `Word` from the wrong
  vocabulary; a `Fact` to a legacy key; an `Evidence` as a param), `ABSENT_PRINTED` (P16), `ABSENT_REASON`,
  `REQUIRES_FAILED`, `EVIDENCE_DERIVED`, `EVIDENCE_UNSERVED`, `EVIDENCE_MODE`, `PART_ONLY`, `CONDITION_TYPE`, each with
  its code.
- **T7 legacy unchanged:** 5 keys with params render exactly as before (today's outputs copied as literals), and a
  legacy key asked in a locale without it falls back to English as today.
- **T8 load:** the shipped catalogue loads; the load evaluates the assignment's value node (a module with a docstring
  loads).
- **T9 cases:** every `Case` in `backend/tests/statement_cases/` renders its English (and evidence) exactly.
- **T10 wire:** every case's message through `to_wire` → `json.dumps` → `json.loads` → `from_wire` renders the same;
  P40.
- **T11 reach:** §3.7.1 on §5.2 (passes), on P35 (fails `gap` `zero`), and on a state pick whose earlier variant
  removes one value (passes) and without it (fails).
- **T12 schema:** `schema.EVIDENCE_ORDER` and `ORIGINS` equal `structure.evaluate`'s; each §3.12 set equals the
  spec's list, as a hand literal; `TOKENS` holds no `NUMBER_WORDS` root or suffix that no other set holds.
- **T12b number words** (D-SC1.32): each alone in a test template fails the load with `LITERAL_NUMBER_WORD` (P28b):
  "sixty days", "Ninety", "thirteen sites", "the tenth site", "hundreds of sites", "dozens", "a couple of sites",
  "twenty-five", "two-thirds", "tenfold", "doubled", "halved", "Seventieth", "millionths", "fourteenth", "eleventh";
  each alone loads (N-T12): "tend", "often", "attend", "tone", "someone", "everyone", "forth", "content", "tenant",
  "coupled", "secondary", "quarterly", "several", "doubt".
- **T13 evidence on the page:** §3.3.1's stated rule (H4 `["Emulated"]`, H5 `[]`, SH4 `["Emulated"]`); C9's two words.

**Plants.** Each must fail with its code. T-plants run over test catalogues in `test_sc1_statements.py`; guard
plants run in the guard's `--self-test` over temporary copies.

| # | Plant | Code |
|---|---|---|
| P1 | `"within 1%"` in a template | `LITERAL_DIGIT` (and `LITERAL_SYMBOL`) |
| P2 | a vocabulary word `"35% at 5 am"` | `LITERAL_DIGIT` |
| P3 | `{allowd}` (typo) in a template | `FIELD_UNDECLARED` |
| P4 | `{accounts:,.2f}` | `FIELD_FORM` |
| P5 | `{state}` printed | `STATE_PRINTED` |
| P6 | `{"gt": ...}` / a path `gapp` / `is` value `MATCH` | `CONDITION_OPERATOR` / `CONDITION_SLOT` / `CONDITION_VALUE` |
| P7, P7b | §5.1 without `month_open`; §5.1 with `month_open`'s `when` as `all[is MONTH_OPEN, present month]` | `NOT_EXHAUSTIVE` |
| P8 | §5.2 with `share_of_gap` given a `when` | `NO_FALLBACK` |
| P9 | `reconciliation.gap` with `positive` removed from `words` | `PICK_INCOMPLETE` |
| P10 | a part pointing at itself | `PART_CYCLE` |
| P11 | a statements module with `STATEMENTS = dict(...)`, a lambda, or a second assignment | `NOT_DATA` |
| P12 (guard) | a variant with no case | `CASE_MISSING` |
| P13 (guard) | an f-string sentence in a file listed in `ADOPTED` | `HAND_BUILT` |
| P13a to P13q (guard) | in an `ADOPTED` file, each alone: a `"Not available"` constant; `" ".join([...])`; `"".join(["Not ", "available"])`; `"a" if x else "an"`; `string.Template("$x")`; `textwrap.fill(s)`; `str(x) + unit`; `s += "x"`; `{"A": "Recorded", "B": "Measured"}`; `raise HTTPException(409, detail=f"...")`; `_refuse(409, "X", f"...")`; `detail=str(e)` after `except Exception as e`; `code.replace("_", " ")`; `code.capitalize()`; `"%s left" % x`; `"{} left".format(x)`; `if word == "below":` | `HAND_BUILT` |
| P14 (guard) | a new plain-string key in `messages.CATALOGUE` | `LEGACY_NEW` |
| P15 | `Money(Decimal("5"), "USD")` without evidence | `TypeError` |
| P16 | C1's facts with `accounts` omitted, rendered (`not_matched` prints it) | `ABSENT_PRINTED` |
| P17 (guard) | a key `reconciliation.kobo_heading` | `KEY_INSTANCE` |
| P18 | the `evidence` vocabulary with a word "Verified" | `VOCABULARY_SCHEMA` |
| P19 | `reconciliation.share` declaring `share` as `money` beside a parent declaring it `percent` | `SLOT_CONFLICT` |
| P20 | two variants with id `same` | `VARIANT_ID` |
| P21 | a part key `reconciliation.gapp` | `PART_UNKNOWN` |
| P22 | a `factor` entry without `article` | `VOCABULARY_FORM` |
| P23 | `"rephrase": "sometimes"` | `REPHRASE` |
| P24 | H1's facts with `big` in KES | `CONDITION_TYPE` |
| P25 | a module source with one statement key twice; a vocabulary with one entry key twice | `KEY_DUPLICATE` |
| P26 | `"within ٣ days"` in a template; `"m³"` in a `noun` word | `LITERAL_DIGIT` |
| P27 | `"¥"` in a template; `"‰"` in a vocabulary word | `LITERAL_SYMBOL` |
| P28 | `"twice the gap"`; `"both match"` | `LITERAL_NUMBER_WORD` |
| P28b | T12b's sixteen literals, each alone | `LITERAL_NUMBER_WORD` |
| P29 | `{"is": ["pending", "true"]}` | `CONDITION_VALUE` |
| P30 | §5.1 `matched` with `({basis})` removed | `EVIDENCE_UNSHOWN` |
| P31, P31b, P31c | a money slot without `evidence` in an `inline` statement; `"tiny": True` on a slot; an `evidence` option in a `served` statement | `EVIDENCE_UNSHOWN`; `SLOT_OPTION`; `SLOT_OPTION` |
| P32 | C9 with the difference of origin `observed-financial` | `EVIDENCE_DERIVED` |
| P33, P33b | `render` of `deep_dive.headline`; `served` of `reconciliation.heading` | `EVIDENCE_UNSERVED`; `EVIDENCE_MODE` |
| P34 | `deep_dive.compared` (served) as a part of an `inline` statement | `EVIDENCE_MODE` |
| P35 | §5.2 without `on_target` | `PICK_REACH` |
| P36 | H7, H8, SD5 | `REQUIRES_FAILED` |
| P37 | `Evidence("NOT_AVAILABLE")`, `Evidence("NEUTRAL")`; `Items(())`, repeated or with an `Absent`; `Name("", "site.code")`; `Day(datetime(...))`; `Quantity` with `reconciled=True`; `State("matched")`; `Absent("x")`; `Month(2026, 13)`; `Count(True, "site")` | `ValueError` / `TypeError` |
| P38 | `{"reason": ["share", "ACCOUNT_ZERO"]}`; C4 with `share` `Absent("OTHER")` | `CONDITION_VALUE`; `ABSENT_REASON` |
| P39 | a test catalogue with an `xx` locale lacking `reconciliation.share` | `LOCALE_INCOMPLETE` |
| P40 | `from_wire` of an unknown fact, an extra field, a float `value`; `json.dumps` and `jsonable_encoder` of a raw fact | `WIRE_FORM`; `TypeError` / raises |
| P40b | `from_wire({"key": "k", "params": {"m": {"fact": ["money"]}}})` | `WIRE_FORM` (never `TypeError`) |
| P41 | `render` of `reconciliation.gap` | `PART_ONLY` |
| P42 (guard) | a legacy template edited | `LEGACY_CHANGED` |
| P43 (guard) | a new prose f-string in a ratchet-scope module | `HAND_BUILT_NEW` |
| P44 (guard) | a baseline fingerprint whose hit was removed | `HAND_BUILT_STALE` |
| P45 (guard) | a `"less than"` constant in a copy of `formats.py` | `MECH_LITERAL` |
| P46 (guard) | `if spec["type"] == "money":` in a copy of `render.py` | `MECH_BRANCH` |
| P47 (guard) | a `"MATCHED"` constant in a copy of `catalogue.py` | `MECH_INSTANCE` |
| P48 (guard) | a module outside `i18n` calling `catalogue._use` | `I18N_PRIVATE` |
| P49 (guard) | a module outside `i18n` importing `assetops_backend.i18n.formats` | `I18N_BYPASS` |
| P49a, P49b, P49c (guard) | outside `i18n`: `from assetops_backend.i18n.render import formats`; `import assetops_backend.i18n.render as r` then `r.formats.money(x)`; `from assetops_backend.i18n import render` then `render.formats` | `I18N_BYPASS` each |
| P49d (guard) | a copy of `render.py` without `__all__` | `I18N_SURFACE` |
| P50 (guard) | `--write-baseline` with the baseline present | `BASELINE_EXISTS` |
| P51 (guard) | a new `i18n/extra.py` that is neither in the mechanism list nor `LEGACY_I18N` | `MECH_UNSCOPED` |
| P51a, P51b, P51c (guard) | a prose f-string in a new `i18n/helpers/words.py`; in `i18n/statements/words.py`; in `i18n/statements/en/extra/words.py` | `MECH_UNSCOPED` each |
| P51d (guard) | a prose constant in a copy of `i18n/statements/en/__init__.py` | `MECH_LITERAL` |
| P52 (guard) | `"const"` or `"params"` written as a string constant in a copy of `conditions.py` | `MECH_LITERAL` |
| P53 (guard) | a new template string added to `CATALOGUE` in a copy of `messages.py`; a new prose f-string outside `CATALOGUE` in `messages.py`, and one in a copy of `locale.py`; an edited existing template | `LEGACY_NEW`; `HAND_BUILT_NEW` each; `LEGACY_CHANGED` (D-SC1.37) |
| P55a, P55b, P55c (guard) | an allow entry with class `SERVED` or an empty `why`; an allow entry with no hit; an allow entry for an `ADOPTED` path | `ALLOW_CLASS`; `ALLOW_STALE`; `ALLOW_SCOPE` |
| P56 (guard) | a backend class `PlantRefused(ValueError)` added to `UNSERVED` in a copy of `schema.py`, and a ratchet-scope handler `except PlantRefused as e: return {"detail": e.args[0]}` | `UNSERVED_SERVED` |
| P57a to P57e (guard; the narrowing still catches) | in a ratchet-scope module, each alone: `LABELS = ("PV array",)`; `f"Unknown change_kind {k!r}."`; `"Yes" if ok else "No"`; `", ".join(day_texts)`; a new entry `"SHUT": "Shut"` in an existing word map | `HAND_BUILT_NEW` each (P57e exactly one) |

**Negative plants** (guard self-test; each must pass): N1 a logging f-string in an `ADOPTED` file; N2 `raise
ValueError(f"...")` in an `ADOPTED` file; N3 a docstring and `message("deep_dive.headline", gap=...)` in an `ADOPTED`
file; N4 a new f-string `f"SELECT id FROM site WHERE code = {p}"` in a ratchet-scope module. N5 to N13 come from the
review's replay (D-SC1.33, D-SC1.36), each new in a ratchet-scope module: N5 `text("SELECT " + _COLUMNS + " FROM
structure_snapshot WHERE tenant_id = :t AND site_id IS NULL ")`; N6 `"u.id, u.tenant_id, u.file_name, u.reader, " + "
FROM commercial_upload u JOIN operator_account sa ON sa.tenant_id = u.tenant_id "`; N7 `hashlib.sha256("\n".join(lines).encode("utf-8"))`;
N8 `"LIVE" if real else "SIMULATED"`, `"application/json" if j else "text/csv"` and `"keep" if kept else "grant"`; N9
`self.logger.info(f"loaded {n} rows from the file")`; N10 `ORDER = "episode_start desc nulls last, site_code_key asc"`;
N11 `raise ValueError("expression is not text")`; N12 `" AND e.recorded_at <= :k" if known else ""`; N13 outside
`i18n`, an import of a name in `render.__all__`.

`PICK_DOMAIN` and `NO_VARIANT` are defences a loaded catalogue cannot reach; they have no plant, each says so in a
comment, and reviewer guide 3 exempts them by name.

## 7. Done (questions; each can fail)

1. Does every sentence a structured statement produces come from facts alone, with no digit, currency sign or number
   word in any template or vocabulary literal? (P1, P2, P26 to P28, P28b, T8, T12b)
2. Is every choice between sentences or words made by a declared condition or pick, evaluated by one function? Does
   the scan prove, from day one, that the mechanism holds no English and no branch on a string (P45 to P47), that no
   backend module gained a hand-built sentence while code strings pass (P43, P44, P57a to P57e, N4 to N12), that no
   file under `i18n/` escapes the scans (P51 to P51d) and no internal is reached from outside (P48, P49 to P49d), and that an adopted module can hold only codes (P13,
   P13a to P13q, N1 to N3)?
3. Is every figure formatted by its type's one format, the same on every screen, and does every stated figure's
   evidence reach the page, in the sentence or served with it? (T2, T13, P15, P30 to P34)
4. Can an absent figure ever print, a fact of the wrong type fill a slot, a pick read outside its domain, or a
   sentence assert what its facts contradict? (T6, P16, P35, P36)
5. Does every variant of every statement have a hand-written case that passes? (T9, P12)
6. Does every legacy message render exactly as before, and can no new or changed untyped one be added? (T7, P14, P42)
7. Can a message holding facts be stored or sent without loss, and only so? (T10, P40)
8. Do 3A7 and 5c have the shapes they need (§5.1, §5.2, §5.4) and a ruling that tells them how to adopt? (D-SC1.26
   and the two amendments)

## 8. Units and the fortnight

| Unit | Content | Commit |
|---|---|---|
| 1.5 | schema, facts, formats, conditions (with §3.7.1), catalogue and load check, render and `served`, wire, vocabulary, common statements; T1 to T3, T5 to T8, T10 to T12; the load and fact plants | 1 |
| 0.75 | the worked statements' test catalogue and cases (§5.1, §5.2, §5.4); T4, T9, T13; the render plants | 2 |
| 1.25 | the guard (coverage with trace, legacy hashes, the three scan scopes, private and bypass, key instances) with its self-test and negative plants, both baselines, check-all wiring; packet | 3 |
| 0.75 | review fix round (D-SC1.32 to D-SC1.39): number-word class, `i18n/**` classification, `__all__` surfaces, served-text rules (prose pairs, SQL lead, joins, conditionals, loggers, per-entry word maps, `CATALOGUE` by the legacy ratchet), allow file, `UNSERVED_SERVED`, L4; the new plants and negatives; both baselines regenerated from `main` | 4 (and 5 if split) |

**Fit (D-SC1.26).** The deep-dive path is: 3A6 (in build) → 3A7 (lane A, gated on 3A6 and SC-1a) → 5c (UI lane,
gated on 3A7, 3B7a and SC-1a) → DDR. SC-1a has no dependency and touches only `i18n` and the guard, so it builds now
in whichever lane is free while 3A6 builds (about 1.75 builder-days). 3A7 writes §2.7 as `reconciliation.py`
statements (its heading exactly §5.1, its scope as §5.4, the rest by the same rules) and joins `ADOPTED`; 5c writes
§2.5 as `deep_dive.py` statements (its headline exactly §5.2, its share and disagreement rows as §5.4), takes §2.2 to
§2.4 from the shared vocabulary, keeps in `words.py` only the functions that build facts, and joins `ADOPTED`. Net cost
to each: none (display code shrinks to building facts); the wait, if any, is the part of SC-1a left when 3A6 merges.

## 9. What moves later, and in what order

| Step | Scope | Size | When |
|---|---|---|---|
| SC-1b | the 123 legacy entries plus 3A6's: params typed, refusal examples as `example` slots, number words reworded (P1's 12 keys); `ADOPTED` grows by `commercial_upload_api.py`, `reading_upload/service.py`, `accounts_api.py`; the refusal envelopes and `period_read.is_message` take `to_wire` (§3.11); each converted module leaves the hand-built baseline | 1.25 units | first free lane after day 14 |
| SC-1c | the backend plain-language modules of §2 (`analytics/plain.py` with its regex restating replaced by stored codes, `night_text.py`, finding and decision APIs, `price_action.py`, `verification.py`); word maps to vocabulary (an unmapped code is `VOCABULARY_UNKNOWN`, never a capitalised code); each leaves the hand-built baseline and joins `ADOPTED` | about 3 units, split per module | with each area's Layer 4 rework, never before |
| SC-1d | frontend sentences that carry a figure or a state come from the server as rendered statements; `frontend-hardwiring.mjs` gains the class | 2 to 4 units, sized at its spec | after SC-1c's first module |
| Step 6 (decisions and options) | the mock's decision text, by kind: `decision.factor`, `decision.change`, `decision.why.<lever kind>` (fuel avoidable, restore path, evidence for a right, judgement for a person), `decision.no_recommendation`, `option.condition`, `option.no_action_why.<lever kind>`, `verify.row`, `sensitivity.row`; every figure a fact from the evaluation (the mock's "61 days", "35%", "95% load", "$70" become facts) | inside step 6's specs | when step 6 is specified |
| SC-2 (optional) | §3.10 | 1 unit | only if the owner asks (Q1) |

## 10. Out of scope

Locales other than English (D-I18N.3); Babel or locale-aware number formats (UQ-4, after this, behind the same
format functions); changing any English the owner has seen; the frontend; the mock-up; storing rendered text
(D-I18N.1 forbids it); building the rephrase layer.

## 11. Decision queue (W3; defaults applied)

| # | Question | Default applied |
|---|---|---|
| Q1 | Build the LLM phrasing layer at all, and where may it rephrase? | Not in the fortnight. Contract fixed now (§3.10); when built, never for money, reconciliation, refusals or evidence words. **Owner to weigh in** |
| Q2 | One money form everywhere: 5c's `$1,200.00` / `KES 1,200.00`, or 3A7's `1,200.00 USD`? | 5c's, everywhere (D-SC1.10). 3A7's sentences read `$505.00` instead of `505.00 USD`. **Owner to weigh in** if code-after is preferred; a "yes" changes one format function and every case at once |
| Q3 | Should static frontend copy (headings, button labels) move to the catalogue too? | No: only sentences that carry a figure or a state (SC-1d). Static chrome is not composed |
| Q4 | Should the mock-up be rewritten to compose its text this way? | No: the mock is the content reference; its sentences become statements, by kind, when step 6 is specified |
| Q5 | Strict render raises rather than showing a fallback sentence. Acceptable on a live screen? | Yes: a sentence that cannot be composed truthfully is a defect caught by the cases and the load proofs; a fallback would hide it (D-SC1.11, D-SC1.20) |
| Q6 | 3A7 and 5c wait for SC-1a's merge instead of shipping flat entries and converting later (D-SC1.26) | Yes: the expected wait is zero (SC-1a builds while 3A6 does) and the fallback was the way hand-built text came back. **Owner to weigh in** if any wait on the deep-dive path is unacceptable; the alternative is D-SC1.14's fallback, which ships a second money form for a time |
| Q7 | Evidence words in sentences: 3A7's heading reads "Revenue (Recorded): ..."; 5c's headline carries its words to the chip (D-SC1.18) | Yes, by the owner's rule "every figure carries its evidence class". The owner sees both in the 3A7 and 5c walkthroughs; wording of the bracket is a one-line template change |
