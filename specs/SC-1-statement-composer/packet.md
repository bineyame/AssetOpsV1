# SC-1a review packet

Branch `task/SC-1a-composer`, built off `main` 8805ee169; main merged in through 8eff70625 (3B2, 0K1, DS3, 4a docs; owner-away row for the Q1 ruling is now row 21); head is the commit that updates this packet. Spec rev 2 with mid-build
answers D-SC1.29 to D-SC1.31 (merged from `task/SC-1a-midbuild-answers` 74e74ca9c). Non-screen.
`USER_REVIEW_REQUIRED: false` (spec header). **Owner approval needed at merge:** the two new check-all lines (guard
changes are held for the owner, `specs/OWNER-AWAY/decisions-2026-11-21.md` row 5).

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
