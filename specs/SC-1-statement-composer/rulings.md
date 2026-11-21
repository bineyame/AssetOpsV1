# SC-1 rulings

Architect (Claude), 2026-11-21, rev 1. Each ruling states the decision and its reason. Index lines:
`.ai/decisions/index-rulings-15.md`. Owner words: `owner/owner-text-composition-clean-2026-11-21.md`.

## D-SC1.1 Extend the existing message seam; one renderer

- **Ruling.** SC-1 extends `assetops_backend/i18n` (the `Message` contract, the catalogue, `render`). It adds no
  parallel composer. `i18n.render` stays the single entry point for every server word, flat or structured.
- **Reason.** The seam already holds the two properties the owner asks for: words are data, and they are rendered at
  read from structured input, never stored composed (D-I18N.1). The owner's rule "extend aligned existing constructs,
  don't drop" applies. A second renderer would be the "if/else mess" at the architecture level.

## D-SC1.2 Facts are typed; every figure carries its evidence; absence is explicit

- **Ruling.** Callers hand over §3.1's fact classes only. `Money`, `Quantity` and `Percent` cannot be built without an
  `Evidence`. A missing figure is `Absent(reason)`; `None`, `0` and raw strings are refused.
- **Reason.** The catalogue can only format, choose and check what it can see. A pre-formatted string hides the
  currency, rounding and evidence; `None` invites "0" or "null of null". Owner rules: every figure carries its
  evidence class; missing data is never shown as zero.

## D-SC1.3 The catalogue is pure literal data in Python modules, one per area

- **Ruling.** `i18n/statements/<locale>/<area>.py`, each one `STATEMENTS = {...}` (or `VOCABULARY = {...}`) whose
  source passes `ast.literal_eval`; the load check refuses anything else (`NOT_DATA`).
- **Reason.** JSON would need package-data configuration and loses comments; a free Python module invites helper
  functions, which is code per statement again. A literal-checked module is data with the same packaging and review
  ergonomics as today's `messages.py`.

## D-SC1.4 Templates hold words and bare fields; formatting belongs to the slot

- **Ruling.** No format spec, conversion or index in a field. A slot declares its type and options; a variant may
  override options.
- **Reason.** `{x:,.2f}` in a template is how two screens drift into two money forms. One format per type (D-SC1.10)
  is only enforceable if templates cannot format.

## D-SC1.5 Conditions are declared data over one small operator set, evaluated by one function

- **Ruling.** §3.4's eight operators; ordered variants, first match; a terminal variant or a proved `exhaustive` set.
  No statement-specific code.
- **Reason.** This is the owner's "not if/else mess" made concrete: the choice still exists, but it is declared next
  to the sentences it chooses between, validated at load, and covered by a case per variant. Eight operators cover
  every choice in 3A7 §2.7, 5c §2.5 and the mock's decision text surveyed; a new operator is a spec change.

## D-SC1.6 Word choices are picks over a declared domain

- **Ruling.** "below/above", "more/less" and the like are `pick` slots on a state or a figure's sign, with words for
  every value of the declared domain; a value outside the domain at render is an error.
- **Reason.** A pick keeps one sentence instead of duplicating variants for one word, and the domain makes the
  impossible case (a zero gap in a "below/above" sentence) fail loudly instead of reading "above".

## D-SC1.7 Fragments and sub-sentences are parts

- **Ruling.** Optional fragments ("(1.01%)", " Compared for 2 of 3 Sites.") and reused sentences are `part` slots
  rendering another statement with the same facts and the parent variant's options. Cycles and depth over 4 are
  refused.
- **Reason.** 3A7 assembled `{gap}` and `{share}` in code, and 5c "appended" a sentence by rule; parts put both in data
  and let a rounding direction chosen by the parent's state reach the fragment.

## D-SC1.8 Vocabulary forms are declared, never derived by letter rules

- **Ruling.** Labels, in-sentence forms, articles and plural forms are written per entry. No vowel rule, no
  capitalisation rule, no `replace("_", " ")`.
- **Reason.** 5c's `lower(label)` already needed an exception (O&M), the mock's `LINE_WORD` needed three regex fixes
  (Ruiru, SMS, kWh), and `asset_words.py` falls back to capitalising codes. Declared forms cost one line each and never
  surprise; a letter rule is a hidden branch.

## D-SC1.9 No number reaches text except through a fact

- **Ruling.** Template literals and vocabulary words hold no digit and no `$ € £ %`. Digits appear only through
  figure, count, date and name slots, the money format's own precision (`tiny`) and declared `example` slots. 3A7's
  "less than 0.01" becomes `tiny`; its "the accounts say 0.00" prints the `Money` fact.
- **Reason.** The owner's honesty rule ("every number honest with its basis") as a machine check: a reviewer no longer
  has to read every sentence to know it invents no figure. The mock's typed "61 days", "95% load", "$70" are exactly
  the class this stops.

## D-SC1.10 One format per fact type, product-wide; money is 5c's form

- **Ruling.** Money reads `$1,200.00` for USD and `KES 1,200.00` otherwise, with U+2212 for negatives (5c §2.1), on
  every screen and in every command's printed sentence. Options change only rounding direction, magnitude, sign,
  `tiny` and inline evidence. This amends 3A7 §2.7's `{figure} {currency}` form (decision queue Q2).
- **Reason.** Two money forms in one product (3A7's `505.00 USD` beside 5c's `$505.00` on the same drawer) is a class
  defect (W6). Directed rounding (D-3A7.10) is kept: it is an option, not a second format.

## D-SC1.11 Render is strict; there is no fallback sentence

- **Ruling.** A missing, unknown or mistyped fact, a printed absence, or a pick outside its domain raises
  `StatementError`. Nothing catches it to substitute text.
- **Reason.** A fallback would show a plausible sentence that the facts do not support, which is worse than an error
  the cases catch before merge. Every variant has a case (D-SC1.12), so a raise in production is a code defect.

## D-SC1.12 Every variant has a hand-written case; adoption is a ratchet

- **Ruling.** The guard fails a variant without a case, a new legacy key, and a hand-built sentence in an `ADOPTED`
  module. Cases are written by hand from the spec (W2), never by calling the renderer. An area joins `ADOPTED` in the
  commit that adopts.
- **Reason.** "Tests per kind" only holds if the guard proves coverage, and "clean" only stays clean if adopted code
  cannot regress to f-strings. The ratchet lets the rest of the product move over area by area without a big-bang
  rewrite.

## D-SC1.13 Statements name kinds, never instances; stored prose is never rewritten by pattern

- **Ruling.** No key, variant id or vocabulary key names a Site, option, decision or person. No module rewrites stored
  or manifest prose by regular expression to make a sentence (the mock's `REASON_RULES`, `analytics/plain.py`'s
  restating); the prose's source must become codes and facts.
- **Reason.** The mock's `decText` has one hand-written function per decision; a product serving 300 Sites cannot.
  General over particular (owner): one statement per kind of decision, fed by the evaluation. Regex restating silently
  breaks when the stored wording changes and can move numbers between sentences unchecked.

## D-SC1.14 3A7 and 5c adopt from the start when SC-1a is in; nothing on the deep-dive path waits

- **Ruling.** SC-1a builds now, in a free lane, with no dependency. If it has merged when 3A7's code starts, 3A7
  writes its §2.7 as statements (§5.1 exactly for the heading) and adds `commercial/reconciliation.py` to `ADOPTED`;
  if it has merged when 5c's unit 1 starts, 5c writes its §2.5 as statements (§5.2 exactly for the headline), reads
  §2.2 to §2.4 from the shared vocabulary, and adds `deep_dive/words.py` and `deep_dive/view.py` to `ADOPTED`.
  Otherwise each ships its spec's flat entries, adds them to the legacy baseline, and converts in SC-1b. The amendments
  in 3A7's and 5c's `rulings.md` say this.
- **Reason.** The owner's fortnight puts the deep-dive path first. SC-1a costs about one builder-day off that path;
  adopting costs 3A7 and 5c nothing (their display logic becomes data), and the fallback costs 0.25 each later.

## D-SC1.15 The LLM phrasing layer is a contract, not a build

- **Ruling.** §3.10 fixes the acceptance test for any later rephrasing (same digit runs, same names, words and
  evidence words verbatim, nothing added, at most twice as long; else the template text). `rephrase` defaults to
  `never` and must be `never` for money, evidence, reconciliation and refusals until the owner decides (Q1).
- **Reason.** The owner allowed an LLM only as a checked phrasing layer over computed facts. Fixing the contract now
  keeps the catalogue shape ready without spending fortnight time or adding a model dependency.

## D-SC1.16 The evidence word has one home

- **Ruling.** 5c §2.4's evidence-word rule and 3A7's `money_word` suffix live as data in vocabulary `evidence` and are
  applied by the `evidence` format. 3A7's `money_word` and 5c's `word` become thin callers of it (or are replaced by
  an `evidence` slot) when they adopt.
- **Reason.** Two places computing "Recorded, not yet reconciled" is the drift class of D-SC1.10; the word is the
  product's honesty marker and must read the same everywhere. "Verified" is refused by the vocabulary schema (5c §2.4).

## Handshake answers

(none yet)
