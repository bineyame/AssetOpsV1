# SC-1 reviewer guide

Architect (Claude), 2026-11-21, rev 3 (handshake round 1 and review answers D-SC1.32 to D-SC1.39 folded in; the
fix-round re-review reads items 2, 10, 14 and 15 first). Discovery review (W5): a new mechanism every server sentence will pass through,
and money in words. Read `spec.md`, `rulings.md`, today's `backend/assetops_backend/i18n/` (four files), 3A7
`spec.md` §2.7 and 5c `spec.md` §2, then the diff. Done means every question in spec §7 answers yes with evidence,
and every plant in spec §6 fails with its named code.

## What to check, and how

1. **Hand values (W2).** Every expected English string in `backend/tests/statement_cases/` and in T2 and T4 is a
   literal from spec §5 or §6. An expected string produced by calling `render` or a format function is High.
2. **No statement-specific code.** The guard's mechanism scope (spec §3.8.4 (1)) proves `i18n/*.py` holds no
   English and that `formats.py`, `conditions.py`, `render.py` and `wire.py` branch on no string; confirm it runs on
   the real modules and that `schema.py` equals spec §3.12 exactly (T12). Read the four files anyway: dispatch by
   table, no key, variant id or slot name. Any `if` on a statement's key or a slot's name is High; any addition to a
   §3.12 set not in the spec is High.
3. **The load check is complete.** For each code in spec §3.6, §3.7, §3.8 and §3.11, find the plant or test that
   triggers it. A code with no failing test is Medium, except `PICK_DOMAIN` and `NO_VARIANT` (defences a loaded
   catalogue cannot reach; each must say so in a comment).
4. **Strict render.** T6 asserts each code. Look for any `try`/`except` around `render` in the diff: none may
   substitute text (D-SC1.11).
5. **Facts.** `Money(Decimal("1"), "USD")` without evidence raises; a float raises; `Evidence("NOT_AVAILABLE")`
   raises; `Absent` never prints; facts are not dataclasses (`json.dumps` raises). `i18n` imports nothing from
   `assetops_backend` outside `i18n` (dependency direction).
6. **Kinds, not instances (D-SC1.13).** `KEY_INSTANCE` (P17) catches Site codes; by eye, no key or vocabulary key
   in the diff names an option, decision or person.
7. **Formats match 5c §2.1 byte for byte**, including U+2212, `$0.00` for negative zero, `KES ` with a space, and
   commas on quantities' integer part only. Directed rounding: C1 and C2.
8. **Parts.** C2's `less than $0.01 less` proves the parent variant's `round` and the slot's `tiny` reach the part; C4
   proves an absent optional part renders empty.
9. **Legacy unchanged.** T7's five literals are today's outputs; `git diff` of `messages.py` touches only `Param`,
   plus 3A6's keys if 3A6 merged in between (each in the legacy baseline with its hash, D-SC1.27).
10. **The guard.** Run `python tools/checks/statement_catalogue.py` and `--self-test`; every guard plant fails with
    its code and N1 to N4 pass. The legacy baseline equals `main`'s legacy keys and template hashes at the last merge of
    `main`; the hand-built baseline was produced by `--write-baseline` from `main` (re-run it on a clean checkout of the
    merge base and compare). In any later unit, an **added** hand-built fingerprint is High unless that unit's spec
    names it (served English goes to statements, D-SC1.34); removals are expected. Each new entry in
    `statement-handbuilt-allow.json` is a code string of its stated class (`SQL`, `HASH`, `CODE`) and not text a
    person reads; a served string allowed under a class is High. A class added to `schema.UNSERVED` is named by the
    unit's spec. The check-all lines are present.
11. **Scope.** No file outside spec §4's table changes. No database, server or Docker use.
12. **Claims and preconditions (D-SC1.20).** For each variant of §5's statements and of the shipped `common.py`, read
    its text against its `when` and `requires`: a relation the words assert (same sign, at most, equal counts, on
    target) that neither selects nor requires is High.
13. **Evidence on the page (D-SC1.18).** Every figure in a case's English is followed by or covered by its evidence
    word, or the case lists the word in `evidence`; a figure stated only by a condition (H4, SH4) still has its word.
14. **Number words (D-SC1.32).** `NUMBER_WORDS` equals §3.12's pairs exactly; T12b's sixteen literals fail and its
    fourteen ordinary words load; `TOKENS` holds no suffix such as `s` or `d`.
15. **The served-text rules (D-SC1.33, D-SC1.35 to D-SC1.37).** Re-run the review's replay (`main`'s last 90
    first-parent commits, new fingerprints per backend merge) with the shipped guard: expect about 112 fingerprints
    with about 2 code strings among them, against 208 with 37 before; a materially higher code-string count, or a
    replay sentence the rules drop (rulings, D-SC1.33's measured losses aside), is Medium. P57a to P57e prove the
    narrowing still catches; N5 to N12 prove the replay's false positives pass; P51a to P51d and P49a to P49d close
    M1 and M2.

## Severity

High: a hand value computed by code; statement-specific code in the mechanism; a fallback sentence; a digit, currency
sign or number word allowed in a literal; a legacy render that changed; a stated figure without its evidence; a scan
scope that does not run on real code; an added baseline fingerprint not named by the spec; a served string in the allow
file; a file under `i18n/` no scope reads. Medium: a §3.7 code without a test; a format differing from 5c §2.1.
Low: naming and comments.

## Packet

Spec §8's units, the check outputs (pytest, the guard and its self-test, check-all fast), the count of mid-build
questions, the list of `ADOPTED` paths (empty in SC-1a), and the hand-built baseline's size (paths and fingerprints).
