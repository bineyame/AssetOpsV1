# SC-1a review packet

Branch `task/SC-1a-composer`, built off `main` 8805ee169; main merged in through 8eff70625 (3B2, 0K1, DS3, 4a docs; owner-away row for the Q1 ruling is now row 21); head is the commit that updates this packet. Spec rev 2 with mid-build
answers D-SC1.29 to D-SC1.31 (merged from `task/SC-1a-midbuild-answers` 74e74ca9c). Non-screen.
`USER_REVIEW_REQUIRED: false` (spec header). **Owner approval needed at merge:** the two new check-all lines (guard
changes are held for the owner, `specs/OWNER-AWAY/decisions-2026-11-21.md` row 5).

## Fix round r2 (review round 2: M4, L6, L7)

Head: the commit that adds this section (code `c19525123`; `main` 22dc0bbf3 (4a) merged at `b1a55974c`, keeping both
sides of `.ai/state/index-2.md`: SC-1a 168, 3B2 169, 0K1 170, 4a 171; SC-1a's owner-away rows stay **23 and 24**;
`check-decision-index.py` OK, 1,072 IDs). **Owner approval still needed at merge: the two check-all lines** (rows 5, 24).

- **M4.** `import_hits` binds the package object to the surface `""`: `import assetops_backend.i18n as i`, the
  unaliased dotted `assetops_backend.i18n.<x>`, `from assetops_backend import i18n [as j]`, and relative `from . import
  i18n`. Attributes resolve as a chain: on the package, a public module name chains into that module's surface, a
  mechanism module is `I18N_BYPASS`, any other name must be in `i18n.__all__`; on a public module, the name must be in
  its surface or `i18n.__all__`; a `_` name is `I18N_PRIVATE`. A string-literal `importlib.import_module(...)`,
  `import_module(...)` or `__import__(...)` is checked as an `import` (and binds its assigned name). Plants **P49e**
  (`i.render.formats.money`), **P49f** (`from assetops_backend import i18n; i18n.formats`), **P49g** (`from . import
  i18n; i18n.formats`) and **P49h** (`importlib.import_module("assetops_backend.i18n.formats")`) each give
  `I18N_BYPASS`; the round-2 guard (3d82bd510) passed all four (run on the same sources). P49a-d and every round-1
  form still fail. `getattr(...)` and `sys.modules[...]` stay out of scope (the review's "deliberate evasion").
  Guard tests: 10 bypass forms and 4 public forms through the package.
- **L6.** `NUMBER_WORDS["en"]` gains `cent` (row 5: `cent`, `cents`, so `per cent`), the `-ing` forms (row 6 is now
  roots `doubl tripl quadrupl halv` with `e es ed ing`, a superset of the old row) and a zero row (`zero nought` with
  `"" s es`: `zeroes`, `nought`, `noughts`). T12 pins the new literal; T12b refuses `doubling tripling quadrupling
  halving`, `per cent`, `ten per cent`, `zeroes`, `nought`, `noughts`, `doubles`, `halves`, and loads `percentage`,
  `centre`, `recent`, `century`, `doubtful`. No word of the shipped catalogue is refused (the catalogue loads; a grep
  of `i18n/` for the new words is empty). **Deviation:** this extends spec §3.12's literal; the Architect should fold
  it into the spec text (all within D-SC1.32's class, no judgement beyond it).
- **L7.** Each live allow entry prints `ALLOWED <path>:<line> <class> <fingerprint> | <source line>`, then
  `ALLOWED entries: N`, on every plain run (pass or fail). Notes never fail a run; the self-test filters them. The
  allow file is empty, so the real tree prints `ALLOWED entries: 0`; a guard test proves a live entry prints its line
  and still counts as baselined, and a stale one still fails `ALLOW_STALE`.
- **Baseline.** Main's 4a added five hand-built fingerprints in ratchet paths (`minigrid_foundation.py:34`,
  `models.py:294`, `rows_mini_grid.py:107/109`×2), so `--write-baseline` regenerated the hand-built baseline: **300
  paths, 5,190 fingerprints**, exactly those five added, none removed (backend outside `i18n/` and `config` equal
  `main` 22dc0bbf3). Legacy 123 keys, unchanged.
- **Gates** (worktree, code c19525123 + merge b1a55974c + baseline; Python `.venv`; all through `heavy-slot.sh`): guard
  on the real tree `OK` (8s); `--self-test` **72 of 72** (61s); `test_sc1_statements.py` + guard tests **449 passed**
  (70.6s); i18n/refusal/3A2/3C1a regression (same 8 files) **794 passed, 1 warning** (28.0s); `check-architecture.ps1`
  passed (ASSETOPS_GUARD_PYTHON set, 100s); `check-agent-workflow.ps1` passed; fast check-all 06:59-07:20 UTC, 1,253s wall (1,138s waiting for a heavy slot, 114.9s run): **all 43 guards passed**, SC-1 lines `OK` and self-test 72 of 72. The regression ran on the merged code before the baseline commit (the baseline is not read by those tests).

## Fix round r1 (D-SC1.32 to D-SC1.39; spec rev 3)

Head: the commit that adds this section (code `33115e055`, main merged at `55aa7d6ac`: `task/SC-1a-review-answers`
420596391, then `main` f75321b92; SC-1a's owner-away rows are now **23 and 24**, after 3B6's 21 and 22).
**Owner approval still needed at merge: the two check-all lines** (owner-away rows 5 and 24).
After the gates, `main` 12a0c6356 (3B6 handshake, 3B4 spec; docs only) merged at f54d11445: rows 23 and 24 kept (main's are 21, 22, 26 to 28); `index-rulings-17.md` went over its 8,000-byte cap, so D-SC1.32-39's index lines moved to a new `index-rulings-19.md`; `check-decision-index.py` OK (1,061 IDs), guard OK, check-agent-workflow passed.

- **D-SC1.32 (M3).** `schema.NUMBER_WORDS["en"]` is the spec's six `(roots, suffixes)` pairs; `schema.number_words`
  derives the set; the load splits on non-letters and refuses any member. `TOKENS` no longer holds them (T12 proves
  no root or suffix is in it unless another set holds it). T12b: the 16 literals fail `LITERAL_NUMBER_WORD` (P28b),
  the 14 N-T12 words load.
- **D-SC1.33.** `prose` is word pairs (word, identifier, SQL words, `(s)`, trailing punctuation), not led by
  `SQL_LEAD`; rule (e) skips a join that is `.encode()`d; rule (f) hits only a display branch; logging covers any
  logger receiver and `logging.getLogger(...)`.
- **D-SC1.34.** `tools/checks/statement-handbuilt-allow.json` (`{}`), `ALLOW_CLASS`/`ALLOW_STALE`/`ALLOW_SCOPE`,
  `--prune` drops stale entries; `UNSERVED_SERVED` for backend classes in `UNSERVED` (built-ins exempt).
- **D-SC1.35 (M1).** `i18n/**/*.py` walked; mechanism, legacy, package marker (literal rule, no `MECH_BRANCH`), data
  module, else `MECH_UNSCOPED`.
- **D-SC1.36 (M2).** `__all__` in `messages`, `locale`, `render`, `facts`, `wire` (what `i18n.__init__` re-exports
  plus `CATALOGUE` and `locale.using`); a missing one is `I18N_SURFACE`; a name outside it, imported, read through
  a bound name or by dotted path, is `I18N_BYPASS`.
- **D-SC1.37 (L1).** `messages.CATALOGUE` templates and their locale dicts are left to the legacy ratchet; rule (i) is
  one fingerprint per word-map entry. P14/P42/P53/P53c now give their legacy code only.
- **L4.** `from_wire` checks the fact name is a `str` first (P40b, `WIRE_FORM`). L3 wording is the spec's; L2 not
  adopted.
- **Tests first.** The new T12/T12b/P40b tests failed on the old `schema`/`catalogue`/`wire` (16 failed: T12, P40b
  and 14 of the 16 T12b literals; "twenty-five" and "two-thirds" were already refused by parts), then pass.
- **Plants.** Self-test **68 of 68** behave (was 40): adds P49a-d, P51a-d, P53a, P55a/P55a2/P55b/P55c, P56,
  P57a-e (P57e exactly one fingerprint), N5-N13. Guard on the guard (scratch edits, reverted): making the surface check
  always pass, classing unscoped files as data and disabling the `UNSERVED_SERVED` read gave **61 of 68** (P49a-c,
  P51a-c, P56 fail); dropping the encode exception or per-entry word maps fails the unplanted base copy.
- **Baselines** regenerated with `--write-baseline --root <scratch>` on SC-1a's tree with `main`'s own `messages.py`
  and `locale.py` (backend outside `i18n/`, `config` and `conversions` equal `main` f75321b92): hand-built **300
  paths, 5,185 fingerprints** (g 2972, a 1590, j 229, e 114, d 87, f 71, i 67, h 55; was 320 / 5,900); legacy **123
  keys** (unchanged).
- **Replay** (the Architect's script, recreated verbatim after the scratch cleanup removed it; tip `43433bea8`, 90
  first-parent commits, 4.7s): **112 new fingerprints over the 14 backend merges, all 14 fail**, the Architect's
  prototype figure exactly. **False positives (code strings): 2 of 112**, the same two (`a8e1fd2` `months.py:125`
  `"\n".join` later hashed; `081e850` `evaluate.py:223` `", ".join` building expression code). The rest: 13 English
  messages of backend exception classes (Architect: 11; I counted every hit inside a `raise` by AST, which includes
  `expressions.py:148`'s join and the start-up `ConfigurationError`s), 4 served exception texts (j), 93 served English.
- **Gates** (worktree, code 33115e055 + merge 55aa7d6ac + docs): guard on the real tree `OK` (7.9s); `--self-test` 68 of 68; `test_sc1_statements.py` 370 passed; guard tests 48 passed (61.5s); i18n/refusal/3A2/3C1a regression (same 8 files) **778 passed, 1 warning** (28.3s wall); `check-architecture.ps1` passed (ASSETOPS_GUARD_PYTHON set, 100.5s); `check-agent-workflow.ps1` passed; `check-decision-index.py` OK (1,034 IDs); fast check-all 06:04-06:10 UTC, 371s wall (258s waiting for a slot): **all 43 guards passed**, both SC-1 lines among them.
- **Known deviations.** (1) `schema.py`'s `NUMBER_WORDS` literal is read as data by scope (1): its roots and suffixes
  are no longer in `TOKENS`, so the spec's own literal would otherwise be `MECH_LITERAL`. (2) The rulings' "does not
  catch" list names `"policy_version required"`, but rule 1 makes a word of three or more letters beside an
  identifier prose, so the guard catches it; the shipped rule follows D-SC1.33 rule 1 (a short word, `site_id is`,
  passes). (3) P49d also gives `I18N_BYPASS` (without a surface every outside import of `render` is a bypass).

## Units (spec §8)

| Unit | Commit | Content |
|---|---|---|
| 1 | 5e91634ac | facts, formats, conditions, load check, render/served, wire, vocabulary, `common.py`; T1-T3, T7, T8, T10-T12 |
| 2 | a96e1eaab | worked statements' cases (§5.1, §5.2, §5.4) in the test catalogue; T4-T6, T9, T10 on every case, T13 |
| 3 | 53c3ae169 | `tools/checks/statement_catalogue.py` and its test, two baselines, two `Add-Guard` lines; T12 identifier names (D-SC1.30); `facts.py` dunder strings read as identifiers |

## Check outputs (worktree, head 53c3ae169 plus docs)

- `pytest backend/tests/test_sc1_statements.py`: **339 passed** in 1.33s.
- Regression (i18n, refusal messages, 3A2, 3C1a; no database): `test_sc1_statements`, `test_uq6a_message_seam`,
  `test_up1_reading_upload`, `test_on1_key_erasure`, `test_3a3_source_contract`, `test_3a2_commercial_upload_api`,
  `test_3a2_commercial_upload_service`, `test_3c1a_person_work`: **747 passed, 1 warning** in 27.5s (28.8s wall).
- `python tools/checks/statement_catalogue.py`: `OK` (5.4s wall).
- `--self-test`: **40 of 40 plants behave** (12s wall, 4 workers): P12, P13, P13a-P13q, P14, P17, P42-P53 (P52b, P53b,
  P53c are the second halves of P52/P53), N1-N4. Guard on the guard: disabling the adopted `.join` rule and
  `MECH_BRANCH` made P13b and P46 fail the self-test (38 of 40); reverted.
- `pytest tools/checks/test_statement_catalogue.py`: **28 passed** in 18s (rules on source strings for P13a-q and
  N1-N4, ratchet and mechanism rules, imports, the token set holds `kisiwa`/`kobo` and not `site`, the real-tree run,
  the self-test).
- `check-architecture.ps1`: passed. `check-agent-workflow.ps1`: passed. Fast check-all: see the last section.

## Figures the reviewer asked for

- Mid-build questions: **3** (all ruled: D-SC1.29 to D-SC1.31; the builder's choices stood).
- `ADOPTED`: **empty** (proved on plants through `--adopt`, a test-only flag).
- Hand-built baseline: **320 paths, 5,900 fingerprints** (rules g 3214, a 1722, f 309, j 229, d 146, e 117, i 108,
  h 55). Legacy baseline: **123 keys**. Both written by `--write-baseline --root <scratch>` on `git archive 8eff70625
  backend config` with SC-1's new mechanism files and `statement_cases/` laid over (main's own `messages.py` and
  `locale.py` kept). Re-run that to compare. Re-taken from main 8eff70625 after the merge: before 320 paths / 5,900 fingerprints / 123 keys, after 320 / 5,900 / 123, byte-identical, no path or key changed status (main's later changes added no served text under backend or config except 3B2's `structure/` code).
- After merge: guard OK; self-test 40 of 40 plants (P12-P53, N1-N4); SC-1 + guard + i18n/refusal/3A2/3C1a tests 588 passed, 46 skipped; check-architecture and check-agent-workflow pass; fast check-all 43 of 43 passed; `check-decision-index.py` OK.
- `KEY_INSTANCE` tokens from config and conversions: `cold`, `kisiwa`, `kobo`, `lab`. No shipped or worked key holds one.

## Known deviations and choices (each small; none changes a seam)

1. **`facts.py` changed in unit 3.** Scope (1) flagged `"__init__"`, `"__code__"`, `"__slots__"`. They are now read as
   identifiers (`object.__init__.__name__`, `init.__code__`, `namespace.update(__slots__=...)`), per D-SC1.30's rule.
2. **`messages.CATALOGUE` is one word-map hit (rule i), fingerprinted over the whole dict.** So any edit to the
   legacy templates also gives `HAND_BUILT_NEW` plus `HAND_BUILT_STALE` on that fingerprint (P14, P42, P53 allow these
   with their own code). The effect: 3A6's keys, or any `main` merge that touches `messages.py`, need both baselines
   rewritten from `main`, which spec §4 already requires.
3. **Coverage of unknown keys.** Cases whose key is in `statement_cases.worked.WORKED` are skipped (T9 covers them
   through the test catalogue). Any other key the shipped catalogue lacks is `CASE_UNKNOWN`. A case that cannot render
   is `CASE_VARIANT` (it chose no variant).
4. **D-SC1.30 text vs code.** The paragraph says none of the names is in `TOKENS`, but `abs` (money option) and `key`
   (part option) are, through §3.3's options. T12 asserts `const`, `params`, `fact` are absent and pins every name
   set. `v` is not used: `wire._Envelope` holds `fact` only, matching §3.11. Architect to confirm the wording.
5. **Builder choices outside the spec text:** importable `i18n` modules outside `i18n` are `messages`, `locale`,
   `render`, `facts`, `wire` (D-SC1.22 names `catalogue`, `formats`, `conditions`, `schema` private; `statements` is
   also refused). The import scan reads `backend`, `tools`, `simulator`, `contracts`, `gateway`, `host`, `field`, only
   files that mention `i18n`. P48 also gives `I18N_BYPASS` (it has to import `catalogue`). Rule (3)(c) is
   `string.Template` exactly; scope (2) refuses a bare `Template(...)` as well. `SC1_GUARD_CACHE` is a self-test-only
   cache of ratchet scans keyed by path and source hash.
6. **Process.** As in units 1 and 2, the guard was drafted before its tests in this session; each plant was then
   run and fails with its code, and none was weakened to pass.

## Fast check-all

`pwsh -NoProfile -File tools/check-all.ps1` (fast), at 53c3ae169 plus this packet, 04:36-04:38 UTC, 1m42s wall:
**42 of 43 blocking guards pass**, both new lines among them (`Statement catalogue (SC-1)` 5.5s, self-test 15.8s).
The one failure is not SC-1a code. `Decision, state, spec and owner indexes`:

    FAIL specs/OWNER-AWAY/decisions-2026-11-21.md: spec folder has no row in specs/INDEX.md
    FAIL unresolved decision ID <the 21 Nov text-waits ruling, SC-1 number 28> cited in specs/OWNER-AWAY/decisions-2026-11-21.md

The mid-build-answers branch (74e74ca9c) brought in that file without `main`'s `specs/INDEX.md` row or the ruling it cites (both
are on `main`). Merging `main` into this branch fixes it, but the merge has doc conflicts in
`.ai/decisions/index-rulings-15.md` and that owner-away file, and `main`'s `structure/check.py` and `pins.py` would
mean rewriting the hand-built baseline from `main` (spec §4). That is the coordinator's call, so I left it undone.
