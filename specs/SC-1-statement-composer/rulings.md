# SC-1 rulings

Architect (Claude), 2026-11-21, rev 2 (handshake round 1 answered: D-SC1.17 to D-SC1.27); D-SC1.28 added 2026-11-21 (owner away). Each ruling states the decision and its reason. Index lines:
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

- **Ruling.** §3.4's operators (eight in rev 1; `reason` is the ninth, D-SC1.23); ordered variants, first match; a terminal variant or a proved `exhaustive` set.
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
  `tiny` and inline evidence (rev 2: `tiny` is always on, D-SC1.24; evidence display is D-SC1.18). This amends 3A7 §2.7's `{figure} {currency}` form (decision queue Q2).
- **Reason.** Two money forms in one product (3A7's `505.00 USD` beside 5c's `$505.00` on the same drawer) is a class
  defect (W6). Directed rounding (D-3A7.10) is kept: it is an option, not a second format.

## D-SC1.11 Render is strict; there is no fallback sentence

- **Ruling.** A missing, unknown or mistyped fact, a printed absence, or a pick outside its domain raises
  `StatementError`. Nothing catches it to substitute text.
- **Reason.** A fallback would show a plausible sentence that the facts do not support, which is worse than an error
  the cases catch before merge. Every variant has a case (D-SC1.12), so a raise in production is a code defect.

## D-SC1.12 Every variant has a hand-written case; adoption is a ratchet

- **Ruling.** The guard fails a variant without a case, a new legacy key, and a hand-built sentence in an `ADOPTED`
  module (rev 2: three scan scopes, all live from SC-1a, D-SC1.17). Cases are written by hand from the spec (W2), never by calling the renderer. An area joins `ADOPTED` in the
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

**Amended by D-SC1.26 (handshake, 2026-11-21): the fallback clause is withdrawn; 3A7 and 5c start after SC-1a merges.**

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


## D-SC1.17 Hand-built text is scanned from day one, in three scopes (R1)

- **Ruling.** The guard's scan (spec §3.8.4) has three scopes, all live in SC-1a. (1) **Mechanism** (`i18n/*.py`
  except `statements/`): every string constant is a member of `i18n/schema.py`'s closed sets or a format spec, and
  `formats.py`, `conditions.py`, `render.py` and `wire.py` compare no value with a string constant: they dispatch by
  table (`MECH_LITERAL`, `MECH_BRANCH`, `MECH_INSTANCE`). (2) **Adopted** (`ADOPTED`): a positive rule, every string
  constant is code-form, no f-string, no composition call (`HAND_BUILT`). (3) **Ratchet** over every other module of
  `backend/assetops_backend/`: the negative rules of §3.8.4, each hit fingerprinted; a hit not in
  `tools/checks/statement-handbuilt-baseline.json` is `HAND_BUILT_NEW`, a baseline entry with no hit is
  `HAND_BUILT_STALE`. The `raise` exemption covers only `UNSERVED` exception types; logging calls are exempt by
  receiver name. Each rule and each evasion R1 lists has a plant (§6 P13a to P13p, P42 to P49).
- **Reason.** An empty `ADOPTED` made the owner's "no if/else mess" a policy. The mechanism itself is the first code
  that must be clean, so it is scanned positively; the rest of the backend cannot be converted in SC-1a, but it can be
  stopped from growing, which is the only honest claim for it today. A positive rule (what is allowed) cannot be walked
  around by a new idiom; a negative rule can, so it is used only where the ratchet makes its holes visible.

## D-SC1.18 Every printed figure's evidence reaches the reader; impossible facts cannot be built (R2)

- **Ruling.** A statement's `evidence` is `inline` (default) or `served`. Inline: every figure slot declares how its
  evidence is shown in the same sentence (`inline`, `{"with": <evidence slot>}`, `{"derived_from": [<figure
  slots>]}`); a printed figure without it is `EVIDENCE_UNSHOWN` at load; there is no `none`. Served: `render` refuses
  the statement (`EVIDENCE_UNSERVED`) and `served(msg)` returns `{"text", "evidence"}`, the evidence words of every
  figure it printed, which the screen shows (5c's chip). A derived figure is never stronger than `DERIVED` or than its
  weakest input, and its origin is the weakest of its inputs' (`EVIDENCE_DERIVED` at render). `Evidence` refuses
  `NOT_AVAILABLE` and `NEUTRAL`: a figure with no value is `Absent`. Swept to every fact (spec §3.1): no empty name,
  no empty or repeated items, no datetime as a day, no `reconciled` on a quantity, percent or price.
- **Reason.** The owner's rule is "every figure carries its evidence class" on the page, not in memory. A default of
  "not shown" is the door this closes; `served` covers the screens whose mock shows the word as a chip beside the
  sentence, without letting the serving code drop it, because the words come out of the same call as the text.

## D-SC1.19 Facts travel only in the wire form; no generic encoder can walk a fact (R3)

- **Ruling.** `i18n/wire.py`: `to_wire(msg)` and `from_wire(obj)` give a lossless JSON form for every fact (spec
  §3.11), with a round-trip test per class. Facts are `__slots__` classes, not dataclasses, so `json.dumps` and
  FastAPI's `jsonable_encoder` raise on them instead of flattening a `Decimal` to a float. `period_read.is_message` and
  the refusal envelopes are unchanged in SC-1a: they refuse a structured message today, which is correct, and the first
  unit that stores or sends one switches them to `i18n.wire` in that unit.
- **Reason.** D-I18N.1 stores messages and renders at read, so a structured message must survive storage exactly. A
  silent `asdict` would lose the currency's precision and the evidence class, which is the failure the owner's
  honesty rule forbids; a loud refusal plus one wire form leaves no third path.

## D-SC1.20 What can be proved at load is proved at load (R4, R5)

- **Ruling.** (a) A pick is reachable only for values in its domain: `PICK_REACH` at load, by the three-valued
  analysis of spec §3.7.1 over each variant's path condition. (b) A variant whose words assert a relation its `when`
  does not select on declares it in `requires`; it is evaluated after the choice and `REQUIRES_FAILED` raises.
  (c) Structured statements have no per-key locale fallback: a locale with a `statements/<locale>/` folder must hold
  every English key with the same variant ids and slots (`LOCALE_INCOMPLETE`); a locale without one is not offered and
  renders English, as D-I18N.3. Legacy entries keep today's per-key fallback until SC-1b.
- **Reason.** A guarantee that only a well-chosen case can catch is a hope. The pick domain and the locale set are
  finite and decidable, so they are proved; the sign relation in 5c's headline is caller knowledge the facts can still
  contradict, so it is declared and checked at every render.

## D-SC1.21 Literal ban by Unicode class and by number word (R7)

- **Ruling.** `LITERAL_DIGIT`: any character of category `Nd`, `No` or `Nl`. `LITERAL_SYMBOL`: category `Sc`, or one
  of `% ‰ ‱ ٪ ﹪ ％`. `LITERAL_NUMBER_WORD`: a whole word, case-folded, in `schema.NUMBER_WORDS[locale]`. Unit symbols
  are vocabulary words under the same rule; only the `unit` vocabulary's `symbol` form may hold `²` or `³`.
- **Reason.** The reason for the ban is that no number enters text except through a fact; `٣`, `¥` and "twice" are
  numbers. The list of number words is closed per locale and lives with the schema, so a word is banned by data.

## D-SC1.22 One public surface; internals are private and scanned (R9)

- **Ruling.** `render` and `served` take no catalogue. Tests inject one through `i18n.catalogue._use(cat)` (a context
  manager over a `ContextVar`) built by `catalogue._build(statements, vocabulary)`, the same validator. Outside
  `backend/assetops_backend/i18n/`, `backend/tests/` and `tools/checks/`, a reference to a `_` name of
  `assetops_backend.i18n` is `I18N_PRIVATE`, and an import of `i18n.formats`, `conditions`, `catalogue`, `schema` or
  `render`'s internals is `I18N_BYPASS`.
- **Reason.** A `catalogue=` keyword or an imported `formats.money` is a second renderer with one more step.

## D-SC1.23 Absence carries a declared reason that conditions can read (R10)

- **Ruling.** A slot that may be absent declares `"absent": [<reason codes>]`; `optional: true` also allows
  omission, read as `Absent("OMITTED")`. Operator `{"reason": ["slot", "CODE"]}` holds when the fact is `Absent` with
  that reason (`CODE` in the slot's list, else `CONDITION_VALUE`). An `Absent` with an undeclared reason is
  `ABSENT_REASON` at render. Reasons are upper snake case.
- **Reason.** 5c's causes (not received, not connected, not calculated yet) need different words; without an operator
  the caller would choose the key by `if`, which D-SC1.5 removes.

## D-SC1.24 A non-zero figure never reads as zero (R12)

- **Ruling.** `tiny` is not an option: it is always on, for `money`, `price`, `quantity` (integer `places`) and
  `percent` (integer `places`). A non-zero value that displays as zero reads `less than` + the smallest displayed
  unit, in magnitude; a negative one printed with `abs: false` reads `more than` + the smallest unit with its sign
  (`more than −$0.01`). Both words come from vocabulary `format`.
- **Reason.** "Missing or zero never confused" is an honesty rule for every figure, not for money; an option that can
  be left off is the door.

## D-SC1.25 Price is a fact type (R11a)

- **Ruling.** `Price(value, currency, unit, evidence)` and the `price` format: money of `value` at 2 places when its
  normalised value has at most 2, else 4 places half even; then ` ` + vocabulary `format` `per` + ` ` + the unit
  symbol (5c §2.1: `$1.25 per L`, `$0.4321 per kWh`).
- **Reason.** 5c ships prices; a money slot cannot carry the per-unit and the 4-place rule without a second format.

## D-SC1.26 3A7 and 5c adopt; their code starts after SC-1a merges (amends D-SC1.14; R18)

**Amended by D-SC1.28 (owner away, 2026-11-21): code starts on the unit's other gates; only the text, and the merge, wait for SC-1a.**

- **Ruling.** The legacy fallback of D-SC1.14 is withdrawn. 3A7's code starts when both 3A6 and SC-1a have merged;
  5c's unit 1 when SC-1a has (its other gates stand). The coordinator checks `git merge-base --is-ancestor <SC-1a merge>
  main` when dispatching each and says so in the builder's brief. If 3A6 merges first, SC-1a takes the next free lane
  ahead of other work. 3A7's and 5c's amendments say this.
- **Reason.** The fallback was the door: flat entries with `{gap}` and `{share}` assembled in code, and 3A7's
  `505.00 USD` beside 5c's `$505.00`, shipped and then converted. SC-1a is about 1.75 builder-days and starts now,
  while 3A6 still builds, so the expected wait is zero and the worst case is the part of SC-1a left when 3A6 merges.
  **Owner to weigh in** if a wait on the deep-dive path is not acceptable (decision queue Q6).

## D-SC1.27 The legacy baseline pins each template (R17)

- **Ruling.** `statement-legacy-baseline.json` maps each legacy key to the SHA-256 (first 16 hex) of its English
  template. A changed template is `LEGACY_CHANGED`; a new key `LEGACY_NEW`. Keys 3A6 adds join the baseline in 3A6's
  merge (or SC-1a's, whichever is later, from `main` at that merge); no other unit adds one.
- **Reason.** A ratchet by name alone lets a legacy template take a digit or a new field unseen.

## D-SC1.28 Text waits for SC-1a; code does not (amends D-SC1.26; owner away, Architect on the owner's behalf)

Decided 2026-11-21 under `owner/owner-away-architect-decides-2026-11-21.md`; logged as row 1 of
`specs/OWNER-AWAY/decisions-2026-11-21.md` for the owner's review. This answers decision queue Q6.

- **Scope.** Every unit not merged when SC-1a merges whose code adds served text: a sentence, a display word, a
  refusal sentence or a message key. Today: 3A7, 3C2 (D-3C2.14) and 5c; any tail unit that starts before SC-1a merges
  (3B2, 3C1b, 4a, 3B4 and the rest). 3A6 keeps D-SC1.27.
- **Code starts on the unit's other gates.** Until SC-1a has merged, the branch adds no served text in any form: no
  `messages.CATALOGUE` key, no prose constant, f-string sentence, word map, `.join` of words or placeholder. What will
  be shown leaves the service as codes and typed values (`Decimal`, a state code such as `OPEN`, a refusal code), and
  the tests assert those, never words.
- **The text commit.** After SC-1a merges, the branch merges `main` first, then writes all of its text as SC-1
  structured statements (by that unit's SC-1 amendment) in its own last commit: its modules join `ADOPTED`, every
  variant has a hand-written case (D-SC1.12), and SC-1a's guard reports no `HAND_BUILT_NEW` and no `LEGACY_NEW` for
  the unit. Word and exact-string assertions are written in that commit.
- **3A7's split.** Commit 1: migration 0068, store and adapter, `reconciliation.py`'s standing as codes and
  `Decimal`s (§2.1 to §2.6), the guard's table list, R1 to R10 without word assertions. Commit 2 (after SC-1a):
  §2.7 as statements (its SC-1 amendment), composition, the command, M1 to M5, Q1 to Q3, the word assertions,
  check-all, packet. 5c is unchanged in effect: its unit 1 already needs 3A7 merged.
- **Merge and review.** The unit merges only after SC-1a (the coordinator checks
  `git merge-base --is-ancestor <SC-1a merge> main` at the text commit's dispatch and at merge). One review of the
  whole unit, after the text commit.
- **Agents.** The builder stops after the non-text commit with a handoff, freeing its slot; the text commit is a
  fresh builder from that handoff.
- **Reason.** The owner asked for text composed "the clean way ... not brittle hard coding and if else mess"
  (`owner/owner-text-composition-clean-2026-11-21.md`) and, for the absence, that "nothing is stuck". The fallback
  ships hand-built text and converts it later, which is what the owner ruled out. Strict-on-code idles lane A on the
  critical chain (3A6 → 3A7 → 5c → DDR) for most of SC-1a's 3.5 units. Gating the text, not the code, keeps every
  served word composed by SC-1 from the first line that reaches any branch, and moves about one lane-day of 3A7 and
  3C2 into SC-1a's build time. The non-text commit does not depend on SC-1a, so a change in SC-1a's review touches
  only the text commit.
- **Reverse.** Withdraw this ruling and D-SC1.26 stands again; a non-text commit already made stays valid under it
  (it is the first part of the same unit, made earlier).

## Handshake answers (round 1)

Answered 2026-11-21 against `handshake.md` at 76cdf962a. Spec rev 2 folds every answer in. "Plant" names the spec §6
row that fails the gate.

- **R1 (High).** D-SC1.17. SC-1a now scans real code: the mechanism (positive, by `schema.py`'s closed sets, and
  table dispatch: P45 to P47), the whole backend by ratchet (P43, P44), and `ADOPTED` by the positive rule, proved on
  plants until 3A7 joins (P13, P13a to P13p, one per evasion: one-space constant, `" ".join`, `"".join` of literals,
  short ternary, `string.Template`, `textwrap`, `str(x) + unit`, `+=`, a word map, `HTTPException` detail f-string,
  `_refuse(...)` f-string, `str(exc)` served, `replace("_", " ")`, `.capitalize()`, `%`, `.format`). The `raise`
  exemption is restricted to `UNSERVED` types (spec §3.8.4); a served call is never exempt, and serving an exception's
  text (`str(e)`, `e.args`, `{e}`) is `HAND_BUILT` (P13l). Logging calls on receivers `logger`, `log`, `logging`,
  `_log`, `_logger`, `LOG` are exempt (logs are never served); negative plants N1 to N3 prove the exemptions do not
  over-reach. Known holes, stated in spec §3.8.4: in the ratchet scope, variable-plus-variable concatenation and joins
  of computed lists; neither can occur in `ADOPTED` or the mechanism, where the positive rule leaves no string to join.
  Done question 2 is reworded to say what each scope proves.
- **R2 (High).** D-SC1.18. §5.1's heading now prints `({basis})`, the evidence words of the figures it states;
  derived figures (difference, allowed, share) declare `derived_from`; §5.2's headline is `served` and its cases carry
  the evidence list. Plants: P30, P31 (`EVIDENCE_UNSHOWN`), P32 (`EVIDENCE_DERIVED`), P33 (`EVIDENCE_UNSERVED`), P34
  (`EVIDENCE_MODE`), P37 (constructors, including `Money(..., Evidence("NOT_AVAILABLE"))` and `Evidence("NEUTRAL")`).
  The `NOT_AVAILABLE` row leaves the evidence vocabulary: an absent figure is worded by `common.not_available`.
- **R3 / P3 (High).** D-SC1.19, spec §3.11. Structured messages may be stored or sent only as `to_wire(msg)`; T10
  round-trips every case through `json.dumps`/`json.loads`; P40 proves an unknown fact name, an extra field and a
  float value refuse (`WIRE_FORM`), and that `json.dumps` and `jsonable_encoder` raise on a raw fact. P3's plan stands
  for SC-1a: nothing structured is stored or served yet; `is_message` and `_refusal` stay as they are.
- **R4 (Medium).** (a) D-SC1.20(c): no per-key fallback for structured statements; `LOCALE_INCOMPLETE` (P39); legacy
  keeps today's fallback (T7 asserts it for a non-English locale). (b) D-SC1.20(a): `PICK_REACH` at load (P35: §5.2
  without `on_target`). `PICK_DOMAIN` stays in render as a defence that a loaded catalogue cannot reach; like
  `NO_VARIANT` it is exempt from reviewer guide 3 and says so in a comment.
- **R5 (Medium).** D-SC1.20(b). `more_than_gap` and `share_of_gap` declare `requires` (same sign, spec §5.2); H7
  (opposite signs) must raise `REQUIRES_FAILED` (P36). The class: any variant whose words assert a relation its `when`
  does not select on; reviewer guide 12 checks each variant's text against `when` plus `requires`.
- **R6 (Medium).** Reworded (spec §3.5): the words and the tables are data; the three-step order is the `evidence`
  format's fixed algorithm. T2 covers all 42 pairs (6 evidences x 7 origins including None) by a hand table built from
  the rule's three steps. `RECORDED` with origin None or `unknown` reads "Estimated": intended (a figure whose source
  cannot be named is not claimed as recorded).
- **R7 (Medium).** D-SC1.21; P26 (`٣`, `m³` outside `unit`), P27 (`¥`, `‰`), P28 ("twice", "both"). `kWh`, `L` and
  any unit symbol are under the rule; `m³` is legal only as a `unit` `symbol`. The rule reaches adopters' words: 3A7's
  `standing.none_matched` ("both") and 5c's `SITE_SETUP` ("one ... one of each") are reworded in their amendments.
- **R8 (Medium).** The load reads each module with `ast.parse`: the body is an optional docstring and one `Assign` to
  `STATEMENTS` or `VOCABULARY`; `ast.literal_eval` runs on that assignment's value node; every `ast.Dict` in it is
  checked for repeated constant keys (`KEY_DUPLICATE`, with the dict's path). P25 plants a repeated statement key and a
  repeated vocabulary entry. A repeated value in a state's `values` or an `order` list is `SLOT_OPTION` /
  `VOCABULARY_SCHEMA`.
- **R9 (Medium).** D-SC1.22; P48 (`I18N_PRIVATE`), P49 (`I18N_BYPASS`).
- **R10 (Medium).** D-SC1.23; T3 rows for `reason`; P38 (an undeclared reason in a condition: `CONDITION_VALUE`; an
  `Absent` with an undeclared reason: `ABSENT_REASON`).
- **R11 (Medium).** Spec §5.4 adds worked statements with hand cases: (a) `price` (D-SC1.25, F1 to F5); (b)
  `deep_dive.share`, places 0 and the three-way sign variant (SH1 to SH5); (c) `deep_dive.status_disagreement`, `all`
  of two `cmp` on `sites.count` plus a `requires` tying the count (SD1 to SD5); (d) `reconciliation.scope`: the scope is
  a `State` (`SITE`, `ORGANISATION`) with a `Name`, never one slot of two classes (SC1, SC2); (e) the possessive is the
  template's literal `'s` after a name field (SD1), no rule in code; (f) `drawer_values` and `tile2_rest` use only the
  operators shown (`sign`, `cmp`, `requires`) and get their cases in 5c. Done question 7 now points at §5.4.
- **R12 (Medium).** D-SC1.24; T2 rows for quantity and percent; P-free (no option exists to plant against: T2 proves
  the behaviour, and `SLOT_OPTION` refuses a `tiny` key, P31b).
- **R13 (Medium).** P7 gains P7b (`all` containing the `is`). P8: `NO_FALLBACK` depends only on the last variant
  (an earlier `when`-less variant is `VARIANT_ID`), so P8 always fails with it. P16's exact edit: C1's facts with
  `accounts` omitted (optional, so `Absent("OMITTED")`), rendered: `not_matched` prints `{accounts}` →
  `ABSENT_PRINTED`. P17 becomes machine-checked: `KEY_INSTANCE` in the guard (a key segment, variant id or vocabulary
  key equal, case-folded, to the first hyphen-separated token of a `config/scenarios/*.yaml` file name; digits and
  UUIDs are already `KEY_FORM`). New plants P19 `SLOT_CONFLICT`, P20 `VARIANT_ID`, P21 `PART_UNKNOWN`, P22
  `VOCABULARY_FORM`, P23 `REPHRASE`, P24 `CONDITION_TYPE`.
- **R14 (Medium).** A `Flag` operand is a Python `True`/`False` (what `literal_eval` yields); a `State` operand a
  string in its `values`. `{"is": ["pending", "true"]}` is `CONDITION_VALUE` (P29).
- **R15 (Low).** §1's value sentence reworded: no number is written in any wording; every digit on screen comes from
  a fact (a computed figure, a count, a date) or is copied verbatim from a record (`name`) or a declared example.
- **R16 (Low).** `Items` refuses an empty tuple and repeated items (by fact equality) in its constructor, for every
  order; "repeats removed" is deleted. No items is `Absent`.
- **R17 (Low).** D-SC1.27. Guide 9 now reads: `messages.py` changes only in `Param`, plus 3A6's keys if 3A6 merged
  in between (each in the baseline with its hash).
- **R18 (Low).** D-SC1.26: the merge condition, checked by the coordinator at dispatch, told to each builder in the
  brief. Q2 stays the owner's; with the fallback gone, one money form ships either way.
- **P1.** Noted for SC-1b's sizing.
- **P2.** Confirmed: `messages.CATALOGUE` stays the legacy dict untouched; the merged view lives in `catalogue.py`;
  `render.py` imports from `catalogue` only.
- **P4.** Confirmed, with D-SC1.18: both tuples are copied into `i18n/schema.py`; T12 asserts parity with
  `structure.evaluate` (tests may import it); `Evidence` accepts `EVIDENCE_ORDER` without `NOT_AVAILABLE`.
- **P5.** Not T2: the tests are backend-suite tests needing no database. The file stays in `backend/tests/` (the cases
  live beside it). Run them as your plan says; §0 and §6 are corrected.
- **P6, P7, P10, P11, P14.** Confirmed as planned.
- **P8.** Recorded for SC-1c/SC-1d: an unmapped asset type is `VOCABULARY_UNKNOWN`, never a capitalised code;
  `UNRECOGNISED_SENTENCE` becomes a refusal in SC-1d.
- **P9.** Confirmed: `formats.DISPLAY = Context(prec=34, rounding=ROUND_HALF_EVEN, traps=[InvalidOperation,
  DivisionByZero, Overflow])`; every quantize passes `context=DISPLAY`.
- **P12.** `Name.text` empty refused; `Percent` any finite Decimal; `Month` 1 to 12 and a year `datetime.date`
  accepts; see D-SC1.18's sweep for the rest.
- **P13.** Confirmed: a variant's `options` keyed by slot name apply to every statement in the tree that declares that
  slot; two declarations differing in type or options are `SLOT_CONFLICT` (P19).

## Mid-build answers (SC-1a, 2026-11-21; Architect, owner away; against `mid-build-questions.md` at 74825a551)

## D-SC1.29 The two pre-existing `i18n` modules sit in the ratchet, named, pinned and unable to grow (Q1)

- **Ruling.** The ratchet is the honest place; no refactor in SC-1a. Spec §3.8.4 (1) now names the mechanism modules
  (`__init__`, `schema`, `facts`, `formats`, `conditions`, `catalogue`, `render`, `wire`) instead of the glob, and
  names `messages.py` and `locale.py` as `LEGACY_I18N`, scanned by scope (3). A new `.py` under `i18n/` in neither
  list is `MECH_UNSCOPED` (P51), so no file is ever unscanned and none can slip out of the positive scope by being
  added. What stops new hand-built text entering them: `messages.py`'s 123 templates are pinned by hash
  (`LEGACY_CHANGED`, D-SC1.27), a new template is `HAND_BUILT_NEW`, a removed one `HAND_BUILT_STALE`; `locale.py`'s
  hits are fingerprinted in the hand-built baseline, any new prose, f-string or composition is `HAND_BUILT_NEW`, and
  the baseline is written once and never hand-extended (`BASELINE_EXISTS`). P53 plants both. `messages.py` shrinks as
  units convert (D-SC1.14, SC-1b); it never grows except by 3A6's keys (D-SC1.27).
- **Reason.** The owner asked for clean composition, not a clean past. `messages.py` is exactly the debt D-SC1.17 says
  the ratchet exists to freeze: moving 123 templates to statements is SC-1b's job, and the positive rule cannot pass
  them by construction. `locale.py` holds ASGI protocol strings (`"http"`, `"latin-1"`), which are not served wording;
  forcing them into `SYMBOLS` would pollute the closed set that is the mechanism's proof, or force a rewrite of
  working middleware for no reader's benefit. Narrowing the positive scope to the files SC-1 writes keeps its claim
  true (the mechanism has no English and no branch on a string) and keeps the two legacy files visible and frozen.
- **Not accepted as written.** The builder's version left the scope as a statement of intent; the named lists and
  `MECH_UNSCOPED` make the boundary checkable. Sweep: any future `i18n/` module is covered by that rule.

## D-SC1.30 Names the mechanism needs are read as identifiers, not added to `SYSTEM` (Q2)

- **Ruling.** Confirmed. `const`, `abs`, `params`, `key`, `fact`, `v` and every fact field name are read from code
  (annotations of private `TypedDict`s, `Message.__annotations__`, constructor parameters), never written as strings;
  `SYSTEM` is unchanged. §3.12 now lists them in its own paragraph ("Names read as identifiers"), T12 asserts the
  set, and a string-constant plant fails (P52).
- **Reason.** A closed set that grows each time the mechanism needs a key is an allow-list that erodes; identifiers
  tie the names to the code that uses them, so a rename cannot leave a stale string, and the scan stays literal-free.
  Cost is none: no schema change, no wire change.

## D-SC1.31 `records` reads the in-sentence form; §5.1 and 3A7 corrected (Q3)

- **Ruling.** Confirmed: §5.1's `records` slot declares `"form": "in_sentence"`; `record_noun` keeps only its
  `in_sentence` form (§3.5). 3A7's rulings (amendment on SC-1) now say the heading transcribes §5.1 rev 2 including
  that form; 3A7's builder copies the slot as written.
- **Reason.** §3.3's `label` default fails the load against §3.5 (`SLOT_OPTION`); the text reads "no billing records
  are recorded", mid-sentence, which is the in-sentence form. Giving `record_noun` a `label` would add a form no
  sentence uses. Sweep: every other `word` slot in §5 was checked against its vocabulary's forms; only `records` was
  wrong.

## Review answers (round 1)

Answered 2026-11-21 (Architect, owner away, under `owner/owner-away-architect-decides-2026-11-21.md`) against
`review.md` at e641526e0. Spec rev 3 and reviewer guide rev 3 fold every answer in. Nothing here widens an
authorisation: the two check-all lines stay held for the owner at merge (owner-away row 5); the definition of served
text is logged as owner-away row 24.

Owner approved both check-all lines (scan and self-test), 2026-11-21 (`owner/owner-approve-sc1a-3c2-guards-2026-11-21.md`).

**For the owner: the two check-all lines in one read.**

- **What the guard catches.** Any new sentence or phrase written into backend code: a string of two or more words,
  an f-string, `%` or `.format` on words, a join with a word separator, a conditional that picks between display
  words, a word map, an exception's text handed to a person; any new or edited template in `messages.py`; any English
  or string branch inside the composer itself; any file under `i18n/` that escapes the scans (M1); any reach into
  the composer's private parts (M2); any number written as a word in a statement ("sixty days", M3).
- **What it does not catch, stated.** Text built by joining two variables or a computed list of lines; a single
  word on its own (`"keep"`); an identifier plus one word (`"policy_version required"`); text that reaches a person
  through one of the 229 places that already show an exception's text (the debt SC-1b and SC-1c convert; a new
  such place is caught); the frontend (SC-1d).
- **False positives.** Replayed over `main`'s last 90 first-parent commits (19 to 21 Nov; the reviewer's replay,
  reproduced exactly: 208 new fingerprints, 14 backend merges failing). **Before:** 37 of 208 were code strings
  (SQL 20, hash or code joins 4, code-valued conditionals 9, the whole-catalogue fingerprint re-firing 4), 18%.
  **After these rulings** (prototyped in scratch, not in the branch): 112 fingerprints, of which **2 are code
  strings** (about 2%: a newline join later hashed, a `", "` join building expression code). 11 are exception
  messages in English, which fail on purpose (write a code, or the unit's spec declares the exception class
  unserved, D-SC1.34); 99 are served English the merges really added. The 57 `messages.py` templates are reported
  once each by key (`LEGACY_NEW` or `LEGACY_CHANGED`) instead of as fingerprints. All 14 merges would still fail: 12 on served English,
  one (3A1) on an exception message, one (3A4) on one code string.
- **Cost per merge.** A backend unit that adds served English writes it as SC-1 statements (D-SC1.28 already says so
  from SC-1a's merge). A code string the scan misreads takes one reviewed line in an allow file with its class and
  reason: on the replay rate about one line per seven backend merges. Runtime about 20 s for both lines together
  (5 s scan, the rest the self-test), as measured by the reviewer plus the new plants.
- **Owner's choice.** Approve both lines at merge, or decline the scan line and keep only the self-test (then nothing
  stops new hand-built text outside the adopted modules).

## D-SC1.32 Number words are a derived class, not a list (M3)

- **Ruling.** `schema.NUMBER_WORDS[locale]` becomes a tuple of `(roots, suffixes)` pairs; a number word is any root
  joined to any suffix of its pair, and nothing else. English (spec §3.12, exactly):
  cardinals `zero` to `twelve`, `hundred`, `thousand`, `million`, `billion`, `trillion` with `""`, `s`, `th`, `ths`,
  `fold`; teen roots `thir four fif six seven eigh nine` with `teen`, `teens`, `teenth`, `teenths`; tens roots
  `twen thir for fif six seven eigh nine` with `ty`, `ties`, `tieth`, `tieths`, `tyfold`; irregular ordinals `first
  second third fifth eighth ninth twelfth` with `""`, `s`; multipliers `once twice thrice single both pair couple
  dozen half quarter percent` with `""`, `s`; multiplier verbs `double triple quadruple halve` with `""`, `s`, `d`.
  `LITERAL_NUMBER_WORD` splits a literal on non-letters, case-folds each token and refuses one in the derived set,
  so compounds (`twenty-five`, `two-thirds`) fail by their parts. `TOKENS` no longer includes `NUMBER_WORDS` (else a
  suffix such as `s` would become a legal mechanism constant and pluralising by letter rule would pass the scan).
- **Reason.** The list missed whole classes (teens, sixty to ninety, ordinals past fifth, plural magnitudes). The
  classes are generated by a handful of English rules; writing the rules as roots and suffixes covers every member
  of each class, and a missing member can only be a missing root, which T12 shows by its table.
- **Accepted costs, stated.** `ones`, `seconds`, `pairs`, `couples`, `singles`, `quarters` are refused (a statement
  says them another way; units and nouns come from the vocabulary). Not covered: Roman numerals in ASCII (`XII`),
  Latin prefixes (`biweekly`, `triennial`), vague quantities (`several`, `few`, `many`), which state no number, and
  period words (`quarterly`).
- **Tests.** T12 asserts the literal; T12b rejects, each alone in a template: "sixty days", "Ninety", "thirteen
  sites", "the tenth site", "hundreds of sites", "dozens", "a couple of sites", "twenty-five", "two-thirds", "tenfold",
  "doubled", "halved", "Seventieth", "millionths", "fourteenth", "eleventh" (`LITERAL_NUMBER_WORD`, P28b); and loads,
  each alone: "tend", "often", "attend", "tone", "someone", "everyone", "forth", "content", "tenant", "coupled",
  "secondary", "quarterly", "several", "doubt" (N-T12).
- **Amended by D-P6.81** (`specs/6f-decisions-screen/rulings.md`): `NUMBER_WORD_IDIOMS` exempts only `one` joined by
  a single `-` or `_` to `off`/`offs` ("one-off", `ONE_OFF`), an idiom that states no count.

## D-SC1.33 What counts as served, and how the scan tells served text from code strings

- **Served text** is text a person can read from the product: an HTTP body, a page, a stored value a page or export
  reads, a file the product writes for a person, a shipped command's terminal output, and an exception's text
  wherever a handler shows it. **Not served:** SQL, bytes and hash input, logging calls, code values, the text of an
  exception of an `UNSERVED` type, docstrings, and the static chrome keywords of §3.8.4 (g).
- **The scan's rules, by class** (ratchet scope; spec §3.8.4 (3)):
  1. *Prose is two adjacent words, not two letter runs.* The text is split on whitespace. A **word** is a token of
     letters (inner `'` or `-` allowed, a trailing `(s)` ignored), stripped of opening quotes or brackets and of
     closing quotes, brackets and `.,;:!?`. An **identifier** is a token like `site_id` or `u.reader` (letters and
     digits joined by `_` or `.`). Two tokens are a prose pair when both are words with a lower-case letter in
     either, or one is a word of three or more letters with a lower-case letter and the other an identifier; the
     first token must not end in punctuation. Upper-case SQL keywords (spec §3.12 `SQL_WORDS`) and `asc`, `desc`,
     `nulls` in any case are not words.
  2. *SQL is recognised by its lead:* a string whose first word (after spaces and an optional `(`) is an upper-case
     SQL clause word (`SELECT INSERT UPDATE DELETE WITH CREATE ALTER DROP FROM WHERE AND OR JOIN LEFT INNER ORDER
     GROUP SET VALUES RETURNING ON LIMIT OFFSET CASE HAVING UNION`) is not prose. Column lists and aliases fall out of
     rule 1 (identifiers, one- and two-letter aliases).
  3. *A join is wording when its separator spaces words:* rule (e) keeps a constant separator holding a letter or
     whitespace, except when the join's result is immediately `.encode(...)`d (bytes are never shown).
  4. *A conditional is wording when a branch is a display form:* rule (f) hits when a branch is prose or holds two
     lower-case letters and is not code-form (`^[A-Za-z0-9_.\-/+:]*$` with no capital before a lower-case letter)
     and does not lead with SQL. `"LIVE" if real else "SIMULATED"`, `"keep" if kept else "grant"` and media types
     pass; `"Yes" if ok else "No"` and `" (deferred)" if d else ""` hit.
  5. *Logging is any logger:* the logging exemption also covers a call whose receiver is an attribute named in the
     logger names (`self.logger.info`, `cls._log.warning`) or `logging.getLogger(...)`, and adds `_LOGGER`.
  6. *Word maps are fingerprinted per entry* (D-SC1.37).
  7. *Exception text keeps its rule:* only a `raise` of an `UNSERVED` type is exempt (D-SC1.34 for adding a class).
- **Reason.** Each false positive in the replay was one of four classes (SQL, hash joins, code-valued conditionals,
  the whole-catalogue fingerprint), and each rule removes its class by structure, not by a name a builder could
  borrow. No rule exempts a string because of where it is assigned or what it is called. Measured on `main`'s whole
  tree (5,900 fingerprints become about 5,190), the narrowing loses SQL, code and identifier-only strings plus the
  stated holes, and gains 36 hits: 31 real (single display words in word maps, now per entry, and identifier
  sentences such as "Duplicate 'x' in"), 5 code strings in graph and redaction output (baselined at merge).
- **Not accepted.** Inferring that a custom exception is unserved from its base class: 229 existing handlers show an
  exception's text, several catch `Exception` (source health, the workers' `last_error`, gateway provisioning), so a
  `ValueError` subclass's message can reach a person; in the prototype, derivation hid over a hundred English
  messages on `main` that such handlers can show.
  An allow-list by variable name (`*_SQL`) was rejected as a loophole.

## D-SC1.34 What a unit does when it adds a string

- **Served English:** an SC-1 statement (D-SC1.28). It is never added to the hand-built baseline, except where the
  unit's spec names the text and the reason with a D-ID (none is foreseen); the reviewer treats any other added
  fingerprint as High.
- **A code string the scan misreads:** one entry in `tools/checks/statement-handbuilt-allow.json`, `{path: [{"fingerprint":
  f, "class": c, "why": text}]}`, `class` one of `SQL`, `HASH`, `CODE`; `why` one line, at most 200 characters. The
  guard treats an allowed fingerprint as baselined; reports `ALLOW_CLASS` (a class outside the three, or an empty
  `why`), `ALLOW_STALE` (an entry with no hit; `--prune` removes it) and `ALLOW_SCOPE` (an entry for an `ADOPTED` or
  `i18n/` path). Served English has no class, so it cannot be allowed. The reviewer checks each new entry's class
  is true.
- **An exception class whose text no handler shows:** its unit's spec adds it to `schema.UNSERVED` (a §3.12 change,
  T12). The guard then proves it: a handler naming that class whose body reads the caught name other than in
  `raise ... from e`, `isinstance(e, ...)` or a logging call is `UNSERVED_SERVED path:line class` (built-in types
  are exempt from this check, as today). Otherwise the message is a code (`raise X("PROBE_COUNT")`), which the scan
  passes as an upper snake code.
- **Reason.** Three routes, one per kind of string, each checkable: statements for words people read; a reviewed,
  classed line for structure the scan misreads; a declared class for diagnostics. No route asks a builder to
  restate a reason the guard can check itself.

## D-SC1.35 Every file under `i18n/` is classified (M1)

- **Ruling.** The guard walks `i18n/**/*.py` (no `__pycache__`). Each file is exactly one of: a mechanism module
  (directly in `i18n/`, stem in `MECHANISM`; scope 1); `LEGACY_I18N` (directly in `i18n/`; scope 3); a package
  marker (`statements/__init__.py`, `statements/<locale>/__init__.py`; scope 1's literal rule, no `MECH_BRANCH`); a
  data module directly in `statements/<locale>/`, where `<locale>` is a package the loader reads (the load proves
  it is pure data, `NOT_DATA`, and `LOCALE_INCOMPLETE` refuses a folder with no `NUMBER_WORDS` entry). Anything else,
  at any depth, is `MECH_UNSCOPED path`.
- **Reason.** D-SC1.29 promised no file is unscanned; a glob of one level kept that promise only for one level.
  Sweep: `_ratchet_paths` and the loader agree with this table (the loader ignores non-package files in
  `statements/` and subpackages of a locale, which are exactly the files now `MECH_UNSCOPED`).
- **Plants.** P51a `i18n/helpers/words.py`, P51b `i18n/statements/words.py`, P51c `i18n/statements/en/extra/words.py`,
  each with a prose f-string (`MECH_UNSCOPED`); P51d a prose constant in `i18n/statements/en/__init__.py`
  (`MECH_LITERAL`).

## D-SC1.36 Public `i18n` modules declare their surface; anything else reached through them is a bypass (M2)

- **Ruling.** Each module in `PUBLIC_MODULES` (`messages`, `locale`, `render`, `facts`, `wire`) declares `__all__`;
  one without it is `I18N_SURFACE module`. Outside `i18n/` (same file set as today), a name imported from a public
  module, or read as an attribute of a name bound to one (`import ...render as r; r.formats`, `from ...i18n import
  render; render.formats`, or the full dotted path), that is not in that module's `__all__` or in `i18n.__all__` is
  `I18N_BYPASS`. `__all__` lists the names `i18n.__init__` re-exports from that module plus those imported from it
  outside `i18n/` on `main` at the fix commit; never `formats`, `conditions`, `schema`, `catalogue`. Aliasing the
  private imports with `_` is not required.
- **Reason.** D-SC1.22's contract is about the surface, not the spelling of an import; a declared surface makes
  every path to an internal the same violation and needs no second convention.
- **Plants.** P49a `from assetops_backend.i18n.render import formats`; P49b `import assetops_backend.i18n.render as r`
  then `r.formats.money(x)`; P49c `from assetops_backend.i18n import render` then `render.formats` (each
  `I18N_BYPASS`); P49d `render.py` without `__all__` (`I18N_SURFACE`); negative N13 an import of a name in
  `render.__all__` passes.

## D-SC1.37 `messages.CATALOGUE` is governed by the legacy ratchet alone; word maps are fingerprinted per entry (L1; now)

- **Ruling.** Now, in SC-1a's fix round, not before SC-1b. The plain-string template values of
  `messages.CATALOGUE[locale]` (and their enclosing dicts) are not fingerprinted by the scan: `LEGACY_NEW`,
  `LEGACY_CHANGED` and `LEGACY_STALE` already judge each template by key and hash, and no key is added except 3A6's.
  Code elsewhere in `messages.py` stays in scope (3). Rule (i) fingerprints each entry of a word map whose value
  matches `^[A-Z][a-z]` and is not already prose: `i:<qualified name>:<sha1 of the entry's key source and value>[:12]`,
  so adding or removing one entry changes one fingerprint. Amends D-SC1.29's "a new template is `HAND_BUILT_NEW`":
  it is `LEGACY_NEW` (P14).
- **Reason.** One fingerprint per dict made every removal look like an addition, which SC-1b would have had to clear
  by hand-added fingerprints at each conversion; two checks on the same template was the noise.
- **Plants.** P53 amended: a new template in `messages.py` is `LEGACY_NEW`, an edited one `LEGACY_CHANGED`, a prose
  f-string outside `CATALOGUE` in `messages.py` and one in `locale.py` `HAND_BUILT_NEW`; P57e a new entry in an
  existing word map is one `HAND_BUILT_NEW`.

## D-SC1.38 D-SC1.30's wording (L3)

- **Ruling.** §3.12's paragraph now reads "none is written as a string constant; whether a name is also in `TOKENS`
  through another set does not matter (`abs` is a money option and `key` a part option, §3.3)". §3.11 has no `v`; it
  leaves the list. The code is unchanged.

## D-SC1.39 The fix round, and the Lows

- **Scope.** M1 to M3 and D-SC1.33 to D-SC1.37 in the guard, `schema.py` and `catalogue.py`; `__all__` in the five
  public modules; L4 (`from_wire` checks the fact name is a `str` first: `WireError`, plant P40b); the new plants
  (P28b, P49a to P49d, P51a to P51d, P55a to P55c, P56, P57a to P57e) and negatives (N5 to N13, N-T12); T12 and T12b;
  both baselines regenerated from `main` at the fix commit with `--write-baseline` (the re-review regenerates and
  compares). L2 is not adopted: the one name-bound compare is generic option logic in a file the reviewer reads whole,
  and flagging it would force a table over a two-way option for no reader. L5 stands as judged.
- **Size.** 0.75 units, one or two commits on `task/SC-1a-composer`; SC-1a is 4.25 units. A verification re-review
  (fresh Claude reviewer) checks M1 to M3, the replay figures above (re-run with the shipped guard) and each plant.
