# SC-1: the statement composer (implementer spec)

Status: **rev 1, handshake pending** (`handshake.md`). Questions during the build: `mid-build-questions.md`.
Reviewer: `reviewer-guide.md`. Decisions with reasons: `rulings.md` (D-SC1.1 to D-SC1.16).

Architect (Claude), 2026-11-21. Owner words (verbatim, `owner/owner-text-composition-clean-2026-11-21.md`): "if that
application could do it reaptedly, make sure it uses clean way to do it (not brittle hard coding and if else mess)".
Standing rules applied: fundamental mechanics first, general over particular (`owner/SUMMARY.md`); honesty rules
(`.ai/RULES.md` §1: missing never 0, every figure carries its evidence class, "Not analysed yet" only while work is
pending, claim only what was tested); W1 to W6 (`.ai/RULES.md` §4).

Non-screen. **SC-1a: 2.0 units, two commits.** Discovery review (W5): a new mechanism every sentence passes through,
and money figures in words. `USER_REVIEW_REQUIRED: false` for SC-1a (no English the owner sees changes, except
D-SC1.10's one money form, which is in the decision queue).

## 0. Before you start

- **Branch** `task/SC-1a-statement-composer` off `main`; worktree `/opt/assetecon/AssetOpsV1-sc1a`. Code starts when
  the handshake has no open question.
- **Python, PYTHONPATH:** as 3A3 §0. Pure Python; no database, no server, no Docker. Tests are neutral (T2).
- **Read:** this spec and `rulings.md`; `backend/assetops_backend/i18n/` (all four files, 312 lines: the seam this
  extends, D-I18N.1 to D-I18N.3); 3A7 `spec.md` §2.7 and `rulings.md` D-3A7.10; 5c `spec.md` §2 (all of it);
  `tools/checks/fuel_wording.py` (the AST-scan pattern to copy) and how `tools/check-all.ps1` line 331 wires it.
- **Collisions.** `3A6` (in build) adds flat entries to `i18n/messages.py`: they stay legal (§3.9) and join the
  legacy baseline when 3A6 merges. `3A7` and `5c` adopt SC-1 by D-SC1.14 (§8).

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

**What SC-1 adds, on top of the same seam (one renderer, `i18n.render`).**

1. **Typed facts in.** The caller hands over facts taken from the computed structure (money with currency and
   evidence, quantity with unit, share, count, k of n, month, day, instant, a vocabulary word, a name from a record,
   a state, an explicit absence), never formatted strings.
2. **Statements as data.** A catalogue entry declares its slots (each with a type and display options), its variants
   (each with a declared condition, as data), its parts (fragments and sub-sentences) and its fallback. No code per
   statement.
3. **One renderer** chooses the variant by evaluating the conditions with one evaluator, formats every slot by its
   type with one format per type, product-wide, and fills the template.
4. **Checks.** At load, every statement is proved well-formed: no digit in any literal, every field a declared slot,
   every condition over declared slots, a fallback or an exhaustive set. At render, every printed slot is filled from a
   fact of its declared type; an absent fact can never print. A guard proves every variant has a hand-written case,
   stops new untyped entries, and scans adopted modules for hand-built sentences.
5. **Later, optional:** an LLM may rephrase a rendered statement only where the catalogue allows it, and only when
   the rephrasing keeps every figure, name and evidence word; otherwise the template text stands (§3.10, not built).

**Value.** Every sentence on a screen is reproducible from its facts and checkable against them: an operator
executive reading "Contribution is $562.00 below target in October" gets the same sentence from the same facts every
month, for every Site and vertical, and a reviewer can prove it contains no number the structure did not compute.
Adding a vertical, a Site or a language adds catalogue data, not branches. This is the honesty claim the demo sells
("every number with its basis") made mechanical.

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

Names (one per meaning): a **fact** is one typed value from the computed structure; a **message** is what code hands
over (a key and its facts); a **statement** is the catalogue entry for a key; a **variant** is one of its sentences
with its condition; a **slot** is a named, typed field; a **part** is a slot filled by rendering another statement;
the **vocabulary** is the catalogue's words; **render** is the one function that turns a message into text.

### 3.1 Facts (`i18n/facts.py`; frozen dataclasses; constructors validate)

| Fact | Fields | Constructor refuses (`TypeError` or `ValueError`) |
|---|---|---|
| `Evidence` | `evidence: str` (one of `structure.evaluate.EVIDENCE_ORDER`, copied as a tuple, no import), `origin: str \| None` (the weakest origin, the caller computes it with `weakest_origin`), `reconciled: bool \| None` (3A7's standing; None when not money) | unknown evidence or origin |
| `Money` | `value: Decimal`, `currency: str` (three capitals), `evidence: Evidence` | non-Decimal value, NaN or infinite, None, missing evidence |
| `Quantity` | `value: Decimal`, `unit: str` (a key of vocabulary `unit`), `evidence: Evidence` | as `Money`; unknown unit |
| `Percent` | `value: Decimal` (a fraction: 0.0101 is 1.01%), `evidence: Evidence` | as `Money` |
| `Count` | `n: int` (≥ 0), `noun: str` (a key of vocabulary `noun`) | bool, negative |
| `KOfN` | `k: int`, `n: int` (0 ≤ k ≤ n, n ≥ 1), `noun: str` | out of order |
| `Month` | `year: int`, `month: int` | out of range |
| `Day` | `day: datetime.date` | — |
| `Instant` | `at: datetime.datetime` (aware) | naive |
| `Word` | `vocabulary: str`, `key: str` | unknown vocabulary or key (checked at render, the vocabulary is per locale) |
| `Name` | `text: str`, `source: str` (the record field it came from, e.g. `site.code`, `action.title`) | empty `source`; a control character in `text` |
| `State` | `value: str` | — |
| `Flag` | `value: bool` | non-bool |
| `Items` | `items: tuple[Fact, ...]` (one fact class throughout) | mixed classes |
| `Absent` | `reason: str` (a code, e.g. `ACCOUNTS_ZERO`) | empty |

A figure (`Money`, `Quantity`, `Percent`) cannot be built without its evidence (owner: every figure carries its
evidence class). A missing figure is `Absent`, never `None` and never zero.

### 3.2 A statement (data; `i18n/statements/<locale>/<area>.py`, one module per area)

Each module holds one assignment, `STATEMENTS = {...}`, whose value is a pure literal (`ast.literal_eval` of its
source succeeds; D-SC1.3). Shape:

```python
STATEMENTS = {
    "<area>.<name>": {
        "slots": {"<slot>": {"type": "<type>", "<option>": <value>, "optional": False}},
        "variants": [
            {"id": "<variant id>", "when": <condition>, "options": {"<slot>": {"<option>": <value>}},
             "text": "<template>"},
        ],
        "exhaustive": "<state slot>",   # optional: the variants' conditions cover every value of that state
        "rephrase": "never",            # or "allowed" (§3.10); default "never"
    },
}
```

- **Keys** are `<area>.<name>`, lower snake case, and name a kind of statement, never an instance: no Site code,
  option ID, decision ID or person in a key (D-SC1.13).
- **Templates** hold literal words and bare fields `{slot}` only: no format spec (`{x:,.2f}`), no conversion
  (`{x!r}`), no index (`{x[0]}`), no literal brace. The format is the slot's, never the template's (D-SC1.4).
- **Variants** are tried in order; the first whose `when` holds is rendered. A variant without `when` holds always and
  must be last. A statement has either a last variant without `when`, or `exhaustive` (§3.7, `NOT_EXHAUSTIVE`).
- **Variant ids** are unique within the statement, lower snake case. Cases and coverage name them (§3.8).
- **`options`** on a variant override the slot's display options for that variant, parts included (§3.6 step 5).

### 3.3 Slot types and their one format each (`i18n/formats.py`; D-SC1.10)

Formats only display: they quantize, take the magnitude, add a sign. They never add, divide or compare figures; a
share, a difference, an allowed amount is computed by the caller and handed over as a fact.

| Type | Fact | English format | Options (default first) |
|---|---|---|---|
| `money` | `Money` | 5c §2.1 exactly: `q = value.quantize(Decimal("0.01"), rounding)`; magnitude `f"{abs(q):,.2f}"`; prefix `$` for USD, else `f"{currency} "`; negative `−` (U+2212) before the prefix; zero is prefix and `0.00` unsigned; never `-0` | `round`: `half_even` \| `down` \| `up` (`ROUND_DOWN` and `ROUND_UP` are toward and away from zero); `abs`: false \| true (print the magnitude); `signed`: false \| true (`+` before a positive); `tiny`: false \| true (a non-zero value that displays as zero reads `less than` + the smallest displayed unit in this format, `less than $0.01`; the words from vocabulary `format`); `evidence`: `none` \| `inline` (append ` (` + the evidence word + `)`) |
| `quantity` | `Quantity` | 5c §2.1: `format(value.normalize(), "f")`, thousands commas on the integer part, then ` ` + the unit's vocabulary symbol (`L`, `kWh`) | `places`: `normal` \| an int (quantize half even); `abs`; `signed`; `evidence` |
| `percent` | `Percent` | `(value * 100)` quantized, then `%` | `places`: 0 \| 1 \| 2 \| `normal` (`format(x.normalize(), "f")`, 3A7's tolerance); `round` as money; `evidence` |
| `count` | `Count` | `f"{n:,}"` + ` ` + the noun's `one` form when n == 1, else `other` | `bare`: false \| true (the number alone) |
| `k_of_n` | `KOfN` | `f"{k:,} of {n:,} "` + the noun's form by `n` (5c: `1 of 1 Site`, `2 of 3 Sites`) | — |
| `month` | `Month` | `month_year`: `October 2026`; `month`: `October` (vocabulary `month`) | `form`: `month_year` \| `month` |
| `day` | `Day` | `15 December 2026` | — |
| `instant` | `Instant` | `20 November 2026, 08:00 UTC` (converted to UTC) | — |
| `word` | `Word` | the entry's form from its vocabulary | `vocabulary` (required: the vocabulary the fact must come from), `form`: `label` \| `in_sentence`; `article`: false \| true (the entry's declared `article` + ` ` first) |
| `name` | `Name` | `text` verbatim | — |
| `items` | `Items` | each item by `of` (a nested slot spec), joined `A`, `A and B`, `A, B and C` (vocabulary `format` `and`) | `of` (required), `order`: `given` \| `vocabulary` (items that are `Word`s, in their vocabulary's declared order, repeats removed) |
| `evidence` | `Evidence` | §3.5's evidence word | `money`: false \| true (append `, not yet reconciled` when `reconciled` is false; 3A7 `money_word`) |
| `pick` | none (reads another slot) | one word chosen by a declared domain: `{"type": "pick", "on": "<state slot>", "words": {"<value>": "<word>", ...}}`, or `"on": {"sign": "<figure slot>"}` with `words` over `negative`, `zero`, `positive` | `domain` (default: every value of the state, or all three signs); a value outside it at render is `PICK_DOMAIN` |
| `part` | the same facts | renders statement `key` with this message's facts | `key` (required) |
| `example` | none | the declared `text` verbatim: a format example in a refusal (`like 2026-10`) | `text` (required) |
| `state`, `flag` | `State`, `Flag` | never printed (conditions and picks only) | `values` (required for `state`: the full list) |

`optional: true` on a slot lets the caller omit the fact; an omitted optional fact behaves as `Absent`.

### 3.4 Conditions (data; `i18n/conditions.py`, one evaluator; D-SC1.5)

A condition is a dict with one operator key. Operands are a slot path (a string: `gap`, `sites.k`, `sites.n`,
`budgets.count`), `{"abs": <operand>}`, or `{"const": <int or decimal string>}`. Constants appear only in
conditions, never in text.

| Operator | Form | Holds when |
|---|---|---|
| `present` | `{"present": "slot"}` | the fact is given and is not `Absent` |
| `absent` | `{"absent": "slot"}` | not `present` |
| `is` | `{"is": ["slot", "VALUE"]}` | a `State` equals VALUE (VALUE in its `values`), or a `Flag` equals `true`/`false` |
| `sign` | `{"sign": ["slot", "negative" \| "zero" \| "positive"]}` | the figure's exact value has that sign |
| `cmp` | `{"cmp": [<operand>, "<" \| "<=" \| "==" \| ">=" \| ">", <operand>]}` | the exact values compare so (figures compare only with figures of the same class and currency or unit, else `CONDITION_TYPE` at render) |
| `all`, `any` | `{"all": [c, ...]}` | every / some condition holds |
| `not` | `{"not": c}` | c does not hold |

Paths: `x` is the fact's exact value (`Money.value`, `Count.n`, `Percent.value`); `x.k` and `x.n` on `KOfN`;
`x.count` on `Items` (number of items). A condition over an `Absent` fact other than `present`/`absent` is false.

### 3.5 Vocabulary (data; `i18n/statements/<locale>/vocabulary.py`, `VOCABULARY = {...}`, a pure literal)

`VOCABULARY = {"<vocabulary>": {"order": [<keys>], "entries": {"<key>": {"label": ..., "in_sentence": ..., "article":
..., "one": ..., "other": ...}}}}`. Each vocabulary declares which forms its entries carry (`"forms": [...]`); every
entry carries each declared form (`VOCABULARY_FORM`). Forms are declared, never derived by a letter rule (D-SC1.8).

SC-1a ships these English vocabularies, transcribed exactly:

| Vocabulary | Source | Forms |
|---|---|---|
| `factor` | 5c §2.2 `FACTOR_LABELS` (every key, in that order); `in_sentence` is 5c's `lower(label)` applied once by hand; `article` `a` or `an` by the in-sentence word's sound (`an O&M`, `an unexplained fuel`, `a fuel cost`) | label, in_sentence, article |
| `heading` | 5c §2.2 `HEADINGS` (four keys = `CATEGORIES`' names), plus 3A7's heading names and words: `revenue` (`Revenue` / `revenue`), `fuel_cost` (`Fuel cost` / `fuel cost`) under keys `REVENUE`, `FUEL_COST` | label, in_sentence |
| `headline_subject` | 5c §2.5: `OPTIMIZE_COST` "cost and efficiency explain", `GROW_REVENUE` "Grow revenue explains" | in_sentence |
| `record` | 5c §2.3 `RECORDS`, its order, its words (BUDGET_LINES excluded: it is a statement, `common.budget_lines`, §5.3) | in_sentence |
| `record_noun` | 3A7: `REVENUE` "billing records", `FUEL_COST` "fuel invoices" | in_sentence |
| `evidence` | 5c §2.4: `NOT_AVAILABLE` "Not available yet", `ESTIMATED` "Estimated", `MODELLED` "Modelled"; by origin `source-emulated` "Emulated", `demo-simulated` "Simulated", `unknown` or none "Estimated"; by evidence for `observed-financial`, `field-integrated`, `bench-tested`: `RECORDED`, `DECLARED` "Recorded", `MEASURED` "Measured", `DERIVED` "Calculated"; the money suffix "not yet reconciled". The rule's order is data: `{"by_evidence_first": {...}, "by_origin": {...}, "observed_by_evidence": {...}, "money_suffix": "not yet reconciled"}` | special shape (validated by its own schema) |
| `unit` | `L` → `L`, `kWh` → `kWh` | symbol |
| `noun` | `site` Site / Sites; `budget_disagreement` budget disagreement / budget disagreements; `reading` reading / readings | one, other |
| `month` | January … December | label |
| `format` | `less_than` "less than", `and` "and", `of` "of", `utc` "UTC" (the only words the formats print) | in_sentence |

The `evidence` word never reads "Verified" (5c §2.4); the vocabulary schema refuses that word.

### 3.6 Render (`i18n/render.py`; one function, D-SC1.1)

`render(msg: Message, locale: str | None = None) -> str` stays the only entry point. For a structured statement:

1. Find the statement for the locale, else English (as today). Unknown key: `KeyError` (as today).
2. **Facts against slots.** The statement's slots are its own and those of every part it reaches (a name declared
   twice must carry the same type and options, else `SLOT_CONFLICT` at load). Every fact names one of them (`FACT_UNKNOWN`); every non-optional slot that is not a
   `pick`, `part` or `example` has a fact (`FACT_MISSING`); every fact is of its slot's class or `Absent`
   (`FACT_TYPE`); a `word` fact comes from the slot's `vocabulary` and exists in it (`VOCABULARY_UNKNOWN`). A raw
   `str`, `int`, `float` or `Decimal` is never a fact (`FACT_TYPE`).
3. **Choose** the first variant whose `when` holds (§3.4). None holds: `NO_VARIANT` (only reachable for an
   `exhaustive` statement handed a value its slot did not declare, which step 2 already refuses; kept as a guard).
4. **Fill** each field of the chosen variant, and only those (a pick or part in a variant not chosen is never
   evaluated): the slot's format with the slot's options, overridden by the variant's `options`. An `Absent`
   fact in a printed field: `ABSENT_PRINTED`.
5. **Parts** render their statement with the same facts and the parent variant's `options` for facts of the same name
   (a part's own slot declarations decide which facts it reads; facts it does not declare are ignored for that part,
   not refused). Depth at most 4.
6. Return the text. Errors are `StatementError(code, key, variant, slot)`, a `ValueError` subclass. There is no
   fallback text: a statement that cannot be rendered truthfully raises (D-SC1.11).

For a legacy entry (a plain string, §3.9) render does exactly what it does today.

`message(key, **facts)` keeps its signature; `Param` becomes `str | int | float | Fact`. A structured statement
refuses `str`/`int`/`float` params; a legacy entry refuses `Fact` params (`FACT_TYPE`), so the two never mix.

### 3.7 The load check (`i18n/catalogue.py`; runs once at import, and in the guard)

Loading merges `messages.CATALOGUE` (legacy strings) and every `i18n/statements/<locale>/*.py` module, then validates.
Any failure raises `CatalogueError(code, key, detail)` at import, so a bad catalogue never serves.

| Code | Fails when |
|---|---|
| `NOT_DATA` | a statements or vocabulary module holds anything but its one literal assignment (and the module docstring) |
| `KEY_DUPLICATE` | a key appears twice across modules or in both a module and `messages.CATALOGUE` |
| `KEY_FORM` | a key is not `<area>.<name>` lower snake case |
| `SLOT_TYPE`, `SLOT_OPTION`, `SLOT_CONFLICT` | an unknown type; an option not in §3.3 for that type, a bad option value, a required option missing, or a variant `options` naming a slot that neither the statement nor its parts declare; one name declared with two types or option sets across a statement and its parts |
| `FIELD_UNDECLARED`, `FIELD_FORM` | a template field that is not a declared slot; a field with a format spec, conversion or index, or a stray brace |
| `LITERAL_DIGIT`, `LITERAL_SYMBOL` | a digit `0-9`, or one of `$ € £ %`, in a template's literal text or in any vocabulary word (D-SC1.9). Digits reach text only through figure, count, date and name slots, the format's own precision (`tiny`) and `example` slots |
| `STATE_PRINTED` | a `state` or `flag` slot used as a template field |
| `CONDITION_OPERATOR`, `CONDITION_SLOT`, `CONDITION_VALUE` | an unknown operator or extra key; a path to an undeclared slot or field; an `is` value outside the state's `values`, a `sign` word outside the three |
| `NO_FALLBACK` | no last variant without `when`, and no `exhaustive` |
| `NOT_EXHAUSTIVE` | with `exhaustive`, a variant whose `when` is not `is` on that slot or `any` of such; or the union of their values misses a declared value |
| `VARIANT_ID` | a missing, repeated or badly formed id; a variant without `when` that is not last |
| `PICK_INCOMPLETE` | a pick whose `words` miss a value of its domain, or name one outside it |
| `PART_UNKNOWN`, `PART_CYCLE` | a part key that is not a structured statement; a cycle, or depth over 4 |
| `VOCABULARY_FORM`, `VOCABULARY_SCHEMA` | an entry missing a declared form; an `order` that is not exactly the entries' keys; a bad `evidence` shape or the word "Verified" |
| `REPHRASE` | `rephrase` not `never` or `allowed` |

### 3.8 The guard (`tools/checks/statement_catalogue.py`; check-all, with `--self-test`)

1. **Load.** Imports the catalogue (PYTHONPATH `backend`); a `CatalogueError` fails the guard with its code and key.
2. **Coverage.** Every variant id of every structured statement has at least one case in
   `backend/tests/statement_cases/*.py` (each module `CASES = [Case(key, variant, facts, english), ...]`; `Case` from
   `backend/tests/statement_cases/__init__.py`). Missing: `CASE_MISSING key variant`. A case naming an unknown key or
   variant: `CASE_UNKNOWN`. (Whether each case renders its English is the pytest's job, §6 T9.)
3. **Legacy ratchet.** The legacy keys (plain strings in `messages.CATALOGUE`) are a subset of
   `tools/checks/statement-legacy-baseline.json` (a sorted JSON list, written once by the builder from `main`'s
   catalogue at branch time). A new legacy key: `LEGACY_NEW key`. A baseline key that is no longer legacy is removed
   from the file in the same commit (`LEGACY_STALE` until it is).
4. **Hand-built sentence scan** over `ADOPTED` (a tuple of repo paths in the guard; SC-1a's value is empty: the
   mechanism's own modules build figures with `format()` and symbols, and are held to "no English word" by review
   instead, reviewer guide 2; the self-test proves the scan on a planted file). Through `ast`, as
   `fuel_wording.py` reads literals: an f-string (`JoinedStr`) anywhere, a `str.format` or `%` call on a string, a `+`
   with a string literal operand, or a string constant with two or more spaces is `HAND_BUILT path:line`. Exempt:
   docstrings and bare string statements; `raise` statements' arguments (developer errors, never shown); the first
   argument of `message(...)`. An area joins `ADOPTED` when it adopts (D-SC1.12): 3A7 adds
   `commercial/reconciliation.py`, 5c adds `deep_dive/words.py` and `deep_dive/view.py`.
5. `--self-test` runs plants P12 to P14 (§6) against temporary copies and passes only if each fails with its code.

Wire in `tools/check-all.ps1` next to the fuel wording guard: `Add-Guard "Statement catalogue (SC-1)" $Python
@("tools/checks/statement_catalogue.py")` and the `--self-test` line.

### 3.9 Legacy entries

A plain string in `messages.CATALOGUE` is a legacy statement: one variant, untyped params, rendered as today, not
checked for digits (its params are already text). They stay legal so nothing breaks. No new legacy key is added
except those of 3A6 and, under D-SC1.14's fallback only, 3A7 and 5c (each added to the baseline in its own merge). SC-1b
converts the rest.

### 3.10 The rephrase layer (contract only; not built in SC-1; D-SC1.15)

A later `i18n/rephrase.py` may offer an LLM rewording of a rendered statement whose `rephrase` is `allowed`. The
renderer passes the template text and the facts' rendered forms; the result is accepted only if (a) the multiset of
digit runs in it equals the template text's, (b) every `name`, `word` and `evidence` rendering in the template text
appears verbatim in it, (c) it adds no digit, currency symbol or `%`, and (d) it is at most twice the template text's
length. Otherwise the template text is shown. Default `never`. `never` is mandatory for `reconciliation.*`, refusals,
and any statement with a `money` or `evidence` slot, until the owner says otherwise (decision queue Q1).

## 4. Code (SC-1a)

| File | Holds |
|---|---|
| `backend/assetops_backend/i18n/facts.py` | §3.1 |
| `backend/assetops_backend/i18n/formats.py` | §3.3 (one function per type, reading vocabulary words; no English literal of its own) |
| `backend/assetops_backend/i18n/conditions.py` | §3.4 |
| `backend/assetops_backend/i18n/catalogue.py` | loading, merging, §3.7; `CatalogueError`, `StatementError` |
| `backend/assetops_backend/i18n/render.py` | §3.6 (extends today's function; same signature) |
| `backend/assetops_backend/i18n/messages.py` | `Param` widened; `CATALOGUE` unchanged otherwise |
| `backend/assetops_backend/i18n/__init__.py` | exports the fact classes, `StatementError` |
| `backend/assetops_backend/i18n/statements/__init__.py`, `statements/en/__init__.py` | empty |
| `backend/assetops_backend/i18n/statements/en/vocabulary.py` | §3.5 |
| `backend/assetops_backend/i18n/statements/en/common.py` | §5.3 |
| `backend/tests/statement_cases/__init__.py`, `common.py` | `Case`; §5.3's cases |
| `backend/tests/test_sc1_statements.py` | §6 T1 to T9, plants P1 to P11 and P15 to P18 |
| `tools/checks/statement_catalogue.py`, `tools/checks/test_statement_catalogue.py`, `tools/checks/statement-legacy-baseline.json` | §3.8, P12 to P14 |
| `tools/check-all.ps1` | two `Add-Guard` lines |

No other file changes. `i18n` imports nothing from `assetops_backend` outside `i18n` (dependency direction).

## 5. Worked statements (the form every adopter follows)

Hand-computed (W2). §5.1 and §5.2 are written by 3A7 and 5c in their own modules (D-SC1.14); SC-1a's tests use
copies of them in a test-only catalogue (`render` and `load` accept an injected catalogue: `catalogue=` keyword,
tests only), so the mechanism is proved on the real shapes before they land.

### 5.1 3A7's heading sentence (`i18n/statements/en/reconciliation.py`)

```python
"reconciliation.heading": {
    "slots": {
        "state": {"type": "state", "values": ["MATCHED", "NOT_MATCHED", "ZERO_STATED", "NOT_RECEIVED",
                                              "CURRENCY_MISMATCH", "MONTH_OPEN"]},
        "heading": {"type": "word", "vocabulary": "heading", "form": "label"},
        "records": {"type": "word", "vocabulary": "record_noun", "optional": True},
        "accounts": {"type": "money", "optional": True},
        "recorded": {"type": "money", "optional": True},
        "allowed": {"type": "money", "optional": True},
        "tolerance": {"type": "percent", "places": "normal", "optional": True},
        "month": {"type": "month", "optional": True},
        "record_currencies": {"type": "items", "of": {"type": "name"}, "optional": True},
        "currency": {"type": "name", "optional": True},
        "gap_words": {"type": "part", "key": "reconciliation.gap"},
        "share_words": {"type": "part", "key": "reconciliation.share"},
    },
    "variants": [
        {"id": "matched", "when": {"is": ["state", "MATCHED"]},
         "options": {"difference": {"round": "down"}, "allowed": {"round": "up"}},
         "text": "{heading}: the accounts say {accounts} and the records say {recorded}, {gap_words}, within the {allowed} allowed ({tolerance})."},
        {"id": "not_matched", "when": {"is": ["state", "NOT_MATCHED"]},
         "options": {"difference": {"round": "up"}, "allowed": {"round": "down"}, "share": {"round": "up"}},
         "text": "{heading}: the accounts say {accounts} and the records say {recorded}, {gap_words}{share_words}, beyond the {allowed} allowed ({tolerance})."},
        {"id": "zero_stated", "when": {"is": ["state", "ZERO_STATED"]},
         "text": "{heading}: the accounts say {accounts} and no {records} are recorded."},
        {"id": "not_received", "when": {"is": ["state", "NOT_RECEIVED"]},
         "text": "{heading}: the accounts say {accounts}, but no {records} are recorded for {month}."},
        {"id": "currency_mismatch", "when": {"is": ["state", "CURRENCY_MISMATCH"]},
         "text": "{heading}: the accounts are in {currency}, but the records are in {record_currencies}."},
        {"id": "month_open", "when": {"is": ["state", "MONTH_OPEN"]}, "text": "{heading}: {month} is not closed yet."},
    ],
    "exhaustive": "state",
    "rephrase": "never",
},
"reconciliation.gap": {
    "slots": {"difference": {"type": "money", "abs": True, "tiny": True},
              "direction": {"type": "pick", "on": {"sign": "difference"}, "domain": ["negative", "positive"],
                            "words": {"negative": "less", "positive": "more"}}},
    "variants": [{"id": "same", "when": {"sign": ["difference", "zero"]}, "text": "the same"},
                 {"id": "differs", "text": "{difference} {direction}"}],
},
"reconciliation.share": {
    "slots": {"share": {"type": "percent", "places": 2, "optional": True}},
    "variants": [{"id": "shown", "when": {"present": "share"}, "text": " ({share})"},
                 {"id": "omitted", "text": ""}],
},
```

`zero_stated` prints `{accounts}` (a `Money` of 0.00: `$0.00`), not 3A7's literal "0.00" (D-SC1.9). Cases
(evidence: accounts `DECLARED`, recorded `RECORDED`, allowed and difference and share `DERIVED`, tolerance
`DECLARED`; origin `observed-financial`):

| # | Facts | English |
|---|---|---|
| C1 | NOT_MATCHED, `REVENUE`; accounts 501.50 USD; recorded 506.52; difference 5.02; allowed 5.015; share 0.0100099700897308; tolerance 0.01 | `Revenue: the accounts say $501.50 and the records say $506.52, $5.02 more (1.01%), beyond the $5.01 allowed (1%).` |
| C2 | MATCHED, `FUEL_COST`; accounts 505.00 USD; recorded 504.996; difference −0.004; allowed 5.05; tolerance 0.01 | `Fuel cost: the accounts say $505.00 and the records say $505.00, less than $0.01 less, within the $5.05 allowed (1%).` |
| C3 | MATCHED, `REVENUE`; accounts 1200.00; recorded 1200.00; difference 0; allowed 12.00; tolerance 0.005 | `Revenue: the accounts say $1,200.00 and the records say $1,200.00, the same, within the $12.00 allowed (0.5%).` |
| C4 | NOT_MATCHED, `REVENUE`; accounts 0.00 KES; recorded 10.00 KES; difference 10.00; allowed 0.00; share `Absent("ACCOUNTS_ZERO")`; tolerance 0.01 | `Revenue: the accounts say KES 0.00 and the records say KES 10.00, KES 10.00 more, beyond the KES 0.00 allowed (1%).` |
| C5 | CURRENCY_MISMATCH, `FUEL_COST`; currency Name `KES`; record_currencies `USD`, `EUR` | `Fuel cost: the accounts are in KES, but the records are in USD and EUR.` |
| C6 | MONTH_OPEN, `REVENUE`; month 2026-11 | `Revenue: November 2026 is not closed yet.` |
| C7 | ZERO_STATED, `FUEL_COST`; accounts 0.00 USD; records `FUEL_COST` | `Fuel cost: the accounts say $0.00 and no fuel invoices are recorded.` |
| C8 | NOT_RECEIVED, `REVENUE`; accounts 900.00 USD; records `REVENUE`; month 2026-10 | `Revenue: the accounts say $900.00, but no billing records are recorded for October 2026.` |

C2 proves `tiny` and the variant's rounding reaching the part; C4 proves an absent optional part.

### 5.2 5c's headline (`i18n/statements/en/deep_dive.py`)

The view computes which heading is named and `big` (D-5C.15); the statement only words it.

```python
"deep_dive.headline": {
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
        {"id": "more_than_gap", "when": {"cmp": [{"abs": "big"}, ">", {"abs": "gap"}]},
         "text": "Contribution is {gap} {direction} target in {month}; {subject} {big}, more than the whole gap.{compared}"},
        {"id": "share_of_gap", "text": "Contribution is {gap} {direction} target in {month}; {subject} {big} of it.{compared}"},
    ],
},
"deep_dive.compared": {
    "slots": {"sites": {"type": "k_of_n"}},
    "variants": [{"id": "some", "when": {"cmp": ["sites.k", "<", "sites.n"]}, "text": " Compared for {sites}."},
                 {"id": "all", "text": ""}],
},
```

Cases (money evidence `DERIVED`, origin `source-emulated`; sites noun `site`):

| # | Facts | English |
|---|---|---|
| H1 | gap −562.00 USD; big −412.00; subject OPTIMIZE_COST; month 2026-10; sites 3 of 3 | `Contribution is $562.00 below target in October; cost and efficiency explain $412.00 of it.` |
| H2 | gap −562.00; big −700.00; subject OPTIMIZE_COST; sites 2 of 3 | `Contribution is $562.00 below target in October; cost and efficiency explain $700.00, more than the whole gap. Compared for 2 of 3 Sites.` |
| H3 | gap 150.00; big absent; sites 1 of 1 | `Contribution is $150.00 above target in October.` |
| H4 | gap 0.00; sites 1 of 2 | `Contribution is on target in October. Compared for 1 of 2 Sites.` |
| H5 | gap absent; sites 0 of 3 | `Contribution for October is not available yet.` |
| H6 | gap 80.00; big 80.00; subject GROW_REVENUE; sites 3 of 3 | `Contribution is $80.00 above target in October; Grow revenue explains $80.00 of it.` |

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
yet: it needs the billing export and fuel invoices with litres.` (vocabulary order); N3 pending false, needs absent →
`Not available yet.`; B1 factors `om` → `a budget line for O&M`; B2 factors `staff`, `om` → `budget lines for O&M and
staff` (5c §2.2 order: `om` before `staff`).

## 6. Tests (written first; `backend/tests/test_sc1_statements.py`, neutral)

- **T1 facts:** each constructor's refusals in §3.1 (a `Money` of `None`, of a float, without evidence; a `KOfN` of
  4 of 3; a naive `Instant`; a `Name` without source).
- **T2 formats:** money `−1,234.50` → `−$1,234.50`, `0` → `$0.00`, `-0.001` → `$0.00` (never `−$0.00`), KES prefix,
  `signed` `+$5.00`, `round` down/up on 5.015 (`$5.01`, `$5.02`), `tiny` on 0.004; quantity `1200.500` L → `1,200.5 L`;
  percent places 0/1/2/normal on 0.0101 and 0.005 (`1%`, `1.0%`, `1.01%`, `0.5%`); count 1 and 2 Sites; k_of_n
  `1 of 1 Site`; month both forms; day; instant from UTC+3 to `… UTC`; items one, two, three, and `vocabulary` order
  with a repeat removed; evidence word for every row of 5c §2.4 and the money suffix.
- **T3 conditions:** each operator true and false; `abs`; dotted paths; a condition over `Absent` is false;
  comparing money in two currencies raises `CONDITION_TYPE`.
- **T4 render choice:** §5.1 C1 to C8 and §5.2 H1 to H6 through the injected test catalogue, exact strings.
- **T5 parts:** the parent variant's options reach the part (C2's `less than $0.01 less` needs `round` and `tiny`);
  a part ignores facts it does not declare.
- **T6 strictness:** `FACT_UNKNOWN`, `FACT_MISSING`, `FACT_TYPE` (a `str` for money; a `Word` from the wrong
  vocabulary; a `Fact` to a legacy key), `ABSENT_PRINTED`, `PICK_DOMAIN` (H-shaped facts with gap 0 forced into
  `gap_only`), each with its code.
- **T7 legacy unchanged:** every key of today's `messages.CATALOGUE` renders exactly as before for a sample of 5 keys
  with params (copy today's outputs as literals).
- **T8 load:** the shipped catalogue loads; `vocabulary.py` and `common.py` pass `ast.literal_eval`.
- **T9 cases:** every `Case` in `backend/tests/statement_cases/` renders its English exactly.

**Plants** (each must fail with its code; P1 to P11 and P15 to P18 in T-plant tests over injected catalogues; P12 to
P14 in the guard's self-test):

| # | Plant | Code |
|---|---|---|
| P1 | `"within 1%"` in a template | `LITERAL_DIGIT` (and `LITERAL_SYMBOL`) |
| P2 | a vocabulary word `"35% at 5 am"` | `LITERAL_DIGIT` |
| P3 | `{allowd}` (typo) in a template | `FIELD_UNDECLARED` |
| P4 | `{accounts:,.2f}` | `FIELD_FORM` |
| P5 | `{state}` printed | `STATE_PRINTED` |
| P6 | `{"gt": ...}` / a path `gapp` / `is` value `MATCH` | `CONDITION_OPERATOR` / `CONDITION_SLOT` / `CONDITION_VALUE` |
| P7 | §5.1 without `MONTH_OPEN`'s variant | `NOT_EXHAUSTIVE` |
| P8 | §5.2 with `share_of_gap` given a `when` | `NO_FALLBACK` |
| P9 | `reconciliation.gap` with `positive` removed from `words` | `PICK_INCOMPLETE` |
| P10 | a part pointing at itself | `PART_CYCLE` |
| P11 | a statements module with `STATEMENTS = dict(...)` or a lambda | `NOT_DATA` |
| P12 | a variant with no case | `CASE_MISSING` |
| P13 | an f-string sentence in a file listed in `ADOPTED` | `HAND_BUILT` |
| P14 | a new plain-string key in `messages.CATALOGUE` | `LEGACY_NEW` |
| P15 | `Money(Decimal("5"), "USD")` without evidence | `TypeError` |
| P16 | `gap` given as `Absent` to a variant forced to print it (§5.2 `gap_only` with `not_available` removed) | `ABSENT_PRINTED` |
| P17 | a key `reconciliation.kobo_heading` naming an instance | not machine-checkable: reviewer check (reviewer guide 6) |
| P18 | the `evidence` vocabulary with a word "Verified" | `VOCABULARY_SCHEMA` |

## 7. Done (questions; each can fail)

1. Does every sentence a structured statement produces come from facts alone, with no digit in any template or
   vocabulary literal? (P1, P2, T8)
2. Is every choice between sentences or words made by a declared condition or pick, evaluated by one function, with no
   `if` on wording in any adopted module? (§3.4, P13, review of `formats.py` and `render.py`)
3. Is every figure formatted by its type's one format, the same on every screen, with its evidence carried? (T2, P15)
4. Can an absent figure ever print, or a fact of the wrong type fill a slot? (T6, P16)
5. Does every variant of every statement have a hand-written case that passes? (T9, P12)
6. Does every legacy message render exactly as before, and can no new untyped one be added? (T7, P14)
7. Do 3A7 and 5c have a ruling that tells them how to adopt, without waiting? (`rulings.md` D-SC1.14 and the two
   amendments)

## 8. Units and the fortnight

| Unit | Content | Commit |
|---|---|---|
| 1.25 | facts, formats, conditions, catalogue and load check, render, vocabulary, common statements, T1 to T9, plants P1 to P11, P15 to P18 | 1 |
| 0.75 | the guard (coverage, ratchet, scan) with its self-test, the baseline, check-all wiring; packet | 2 |

**Fit (D-SC1.14).** The deep-dive path is: 3A6 (in build) → 3A7 (lane A, gated on 3A6) → 5c (UI lane, gated on 3A7
and 3B7a) → DDR. SC-1a has no dependency and touches only `i18n` and the guard, so it builds now in whichever lane is
free while 3A6 builds (lanes B and C finish 4d and 3C2's handshake; 3C2 is gated on 3A6 too), about one builder-day.

- **If SC-1a has merged when 3A7's code starts:** 3A7 writes §2.7 as `reconciliation.py` statements (its heading
  sentence exactly §5.1, the rest by the same rules) and joins `ADOPTED`. Net cost to 3A7: none (its display code
  shrinks to building facts).
- **If SC-1a has merged when 5c's unit 1 starts:** 5c writes §2.5 as `deep_dive.py` statements (its headline exactly
  §5.2), takes §2.2 to §2.4 from the shared vocabulary, and its `words.py` keeps only the functions that build facts.
  Net cost to 5c: none to −0.25.
- **Otherwise** neither waits: each ships its words as legacy flat entries exactly as its spec says, adds its keys to
  the baseline, and converts in SC-1b (+0.25 each, after day 14).

## 9. What moves later, and in what order

| Step | Scope | Size | When |
|---|---|---|---|
| SC-1b | the 123 legacy entries plus 3A6's: params typed, refusal examples as `example` slots; `ADOPTED` grows by `commercial_upload_api.py`, `reading_upload/service.py`, `accounts_api.py` | 1 unit | first free lane after day 14 |
| SC-1c | the backend plain-language modules of §2 (`analytics/plain.py` with its regex restating replaced by stored codes, `night_text.py`, finding and decision APIs, `price_action.py`, `verification.py`); word maps to vocabulary | about 3 units, split per module | with each area's Layer 4 rework, never before |
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
| Q5 | Strict render raises rather than showing a fallback sentence. Acceptable on a live screen? | Yes: a sentence that cannot be composed truthfully is a defect caught by the cases; a fallback would hide it (D-SC1.11) |
