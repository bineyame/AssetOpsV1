# SC-1 reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a new mechanism every server sentence will pass through,
and money in words. Read `spec.md`, `rulings.md`, today's `backend/assetops_backend/i18n/` (four files), 3A7
`spec.md` §2.7 and 5c `spec.md` §2, then the diff. Done means every question in spec §7 answers yes with evidence,
and every plant in spec §6 fails with its named code.

## What to check, and how

1. **Hand values (W2).** Every expected English string in `backend/tests/statement_cases/` and in T2 and T4 is a
   literal from spec §5 or §6. An expected string produced by calling `render` or a format function is High.
2. **No statement-specific code.** Read `formats.py`, `conditions.py`, `catalogue.py` and `render.py`: no key, variant
   id, vocabulary key or English word appears in them (the words `less than`, `and`, `of` and `UTC` come from
   vocabulary `format`; symbols `$`, `−`, `+`, `%`, `,` and `.` are the formats' own). Any `if` on a statement's key or a slot's name is High.
3. **The load check is complete.** For each code in spec §3.7, find the plant or test that triggers it. A code with no
   failing test is Medium.
4. **Strict render.** T6 asserts each code. Look for any `try`/`except` around `render` in the diff: none may
   substitute text (D-SC1.11).
5. **Facts.** `Money(Decimal("1"), "USD")` without evidence raises; a float raises; `Absent` never prints. `i18n`
   imports nothing from `assetops_backend` outside `i18n` (dependency direction).
6. **Kinds, not instances (D-SC1.13).** No key or vocabulary key in the diff names a Site code, option, decision or
   person (P17 is this check, by eye).
7. **Formats match 5c §2.1 byte for byte**, including U+2212, `$0.00` for negative zero, `KES ` with a space, and
   commas on quantities' integer part only. Directed rounding: C1 and C2.
8. **Parts.** C2's `less than $0.01 less` proves the parent variant's `round` and the slot's `tiny` reach the part; C4
   proves an absent optional part renders empty.
9. **Legacy unchanged.** T7's five literals are today's outputs; `git diff` of `messages.py` touches only `Param`.
10. **The guard.** Run `python tools/checks/statement_catalogue.py` and `--self-test`; P12 to P14 each fail with their
    code. The baseline equals `main`'s legacy keys at branch time (compare with `sorted(CATALOGUE["en"])` on `main`).
    The check-all lines are present.
11. **Scope.** No file outside spec §4's table changes. No database, server or Docker use.

## Severity

High: a hand value computed by code; statement-specific code in the mechanism; a fallback sentence; a digit allowed
in a literal; a legacy render that changed. Medium: a §3.7 code without a test; a format differing from 5c §2.1.
Low: naming and comments.

## Packet

Spec §8's units, the check outputs (pytest, the guard and its self-test, check-all fast), the count of mid-build
questions, and the list of `ADOPTED` paths (empty in SC-1a).
