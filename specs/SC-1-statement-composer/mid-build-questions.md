# SC-1 mid-build questions

Questions raised during the build about something the spec did not fix (spec rev 2). Count: 3. Each part was built
with the conservative choice below, stated so the Architect can rule; nothing else waits on them.

## Q1. [ANSWERED 2026-11-21, D-SC1.29: ratchet, named and pinned; `MECH_UNSCOPED` closes the boundary] The mechanism scope and the two existing `i18n` modules (spec §3.8.4 (1))

The mechanism scope is "`backend/assetops_backend/i18n/*.py`; not `statements/`", positive: every string constant a
code, a `schema` token or symbol. Two files there predate SC-1 and cannot meet it: `messages.py` holds the 123 legacy
English templates (spec §3.9 keeps them; §4 says `CATALOGUE` is unchanged), and `locale.py` holds the ASGI
middleware's protocol strings (`"http"`, `"headers"`, `"latin-1"`, `"http.response.start"`, `"q="` ...). Run on the
real tree, the scope fails by construction.

**Choice applied:** the mechanism scope reads the modules SC-1 writes (`schema`, `facts`, `formats`, `conditions`,
`catalogue`, `render`, `wire`, `__init__`); `messages.py` and `locale.py` are read by the ratchet scope's rules and
sit in the hand-built baseline like any other backend module (so no module is unscanned), and `messages.py`'s
templates stay pinned by the legacy ratchet. `MECH_BRANCH`'s four files are unchanged. To rule: keep this, or say
how the two files should be scanned.

## Q2. [ANSWERED 2026-11-21, D-SC1.30: confirmed; names read as identifiers, listed in §3.12] Names the spec fixes that §3.12's closed sets do not hold

The mechanism must use names the spec itself fixes but that no §3.12 set contains: the condition operand key
`const` (§3.4); the `Message` key `params`; the wire's `fact` key (§3.11); and the facts' field names that are not
already tokens (`value`, `currency`, `origin`, `reconciled`, `n`, `k`, `year`, `at`, `source`). As string constants
each would be `MECH_LITERAL`; adding them to `SYSTEM` is a spec change (reviewer guide 2: High).

**Choice applied:** §3.12 is unchanged. These names are read as code identifiers, never written as strings: a fact's
fields are its constructor's parameter names (`facts._FactMeta` sets `__slots__` from them), `key`/`params` are
`Message.__annotations__`, `fact` and `abs`/`const` are the annotation names of two private `TypedDict`s
(`wire._Envelope`, `conditions._Operand`). To rule: keep this, or add the names to `SYSTEM` (one line, and T12's
literal) and write them as strings.

## Q3. [ANSWERED 2026-11-21, D-SC1.31: confirmed; `in_sentence`; §5.1 and 3A7 amended] §5.1's `records` slot names no form, and `record_noun` has no `label`

§5.1 declares `"records": {"type": "word", "vocabulary": "record_noun", "optional": True}`; a `word` slot's `form`
defaults to `label` (§3.3), but §3.5 gives `record_noun` only `in_sentence`, so §5.1 as written fails the load
(`SLOT_OPTION`). The text ("no {records} are recorded") reads the in-sentence form.

**Choice applied:** the test catalogue's copy of §5.1 (`backend/tests/statement_cases/worked.py`) adds
`"form": "in_sentence"` to `records`; the shipped vocabulary is §3.5 exactly. 3A7 should transcribe §5.1 with that
form. To rule: confirm, or give `record_noun` a `label` form instead.
