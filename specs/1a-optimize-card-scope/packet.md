# 1a review packet: the Optimize card states its day and scope

Implementer (Claude, fresh), 2026-11-21. Branch `task/1a-optimize-card-scope` (worktree `/opt/assetecon/AssetOpsV1-1a`),
off `main` `e39a5d2fa`. Spec rev 2 with `rulings.md` (D-1A.1-11), `handshake.md`, `handshake-I.md`, `reviewer-guide.md`.
Every R1-R4 and I1-I3 question had its answer before code. `USER_REVIEW_REQUIRED: true` (screen unit): review now, and
hold the merge for the owner's walkthrough.

## Commits

| Commit | Content |
|---|---|
| `b414d4b7a` 1a commit 1 | Tests only: P1-P4 in `backend/tests/test_1a_optimize_scope.py`, green on its parent |
| ``41dee463b`` 1a commit 2 | `CostScope`, `cost_scope_text`, `scope_text`, the statement, `noun.day`, the face line, the tests, the sweep, the golden, the capture tool and its fixtures, the register row. P4 now expects the eighth key (the commit message says so) |
| ``93f0447ea` + `382707e17`` docs | Packet, spec status `in_review`, `specs/INDEX.md` row, the `.ai/state/estate.md` entry and its index line |

## Files

- Product: `backend/assetops_backend/site_outcomes/read.py` (`CostScope`; `_summary` fills it per Site;
  `cost_scope_text`; keyword `scope` on `_optimize_card` and `portfolio_cards`), new
  `i18n/statements/en/portfolio_card.py` (the §3.2 literal, verbatim), `i18n/statements/en/vocabulary.py` (`noun.day`),
  `frontend/src/estate/estateClient.ts` (one field), `frontend/src/estate/PortfolioOutcomes.tsx` (one field, the
  `<small className="ob-days oc-pfdays" data-portfolio-card-scope>` after the figure).
- Tests: `test_1a_optimize_scope.py` (P1-P4, S1-S9 with S5b and S5c, the case render test), new
  `tests/statement_cases/portfolio_card.py` (six cases), `estatePortfolio.test.tsx` (F1-F3).
- Sweep (`grep -rn "OPTIMIZE_COST\|_optimize_card\|portfolio_cards(" backend/tests tools/checks`). Only these
  exact-equality card expectations changed:
  - `test_ch5d1_optimize_card.py`: three expected dicts gain `"scope_text": None`.
  - `test_ch6b_estate_postgres.py:238`: it now expects `_optimize_card(sites, scope=CostScope({KOBO: d13}, {KOBO: 7}))`.
  - The golden `ch5a2_chain_contract/estate_week_2026-10-25.json` was regenerated. Its whole diff is one line:
    `+   "scope_text": "Cost of Kobo's lead issue on 31 October 2026, the last of the 7 days shown, not their total",`
  - Not a card dict: `test_sc1_statements.py` T8 lists the shipped statements exactly, so it gains
    `portfolio_card.cost_scope`. This is the same edit each earlier adopter made.
- Evidence tooling: `tools/optimize_card_capture.cjs` and `frontend/e2e-fixtures/1a/{one,two}/*.json`, generated from
  `portfolioFixtures.ts` plus the S1 and S4 cards.
- Register: `.agent/mock-departure-register.md` row R757 (MOCK DEVIATION MD-1A-1, format).
- Not touched: `chain/vocabulary.py`, `tools/checks/*`, `tools/demo_combined_rows.py`, legacy card texts and baselines.

## Acceptance (spec §4)

1. **Pins first.** P1-P4 passed on `e39a5d2fa` with no product edit (`4 passed`), in commit 1 alone.
2. **The 30-day face.** S1 checks that the card reads "Cost of Kobo's lead issue on 30 October 2026, the last of the 30
   days shown, not their total". `value`, `detail`, `basis_text` and `claim` are byte-equal to ch5d1's. No new figure
   is added, and S7 finds no amount in the line.
3. **Variants.** One day (S2), latest in range (S3), several Sites (S4) and mixed days (S5, S5b, S5c) each read their
   own variant. S8 checks the wiring through `summary()` for 1 Oct-31 Oct and for 30 Oct-31 Oct.
4. **SC-1 only.** All six variants are in `portfolio_card.cost_scope`, each with a case. The case English is rendered,
   and the chosen variant checked, in `test_cost_scope_cases_render_their_english_through_their_variant`. No legacy
   text was changed.
5. **Existing checks unchanged.** COH-17 O1 returns `[]` on three summaries (S9). `test_demo_combined_finish_rows`
   (the demo prepare's `optimize_card` self-check) and every card test pass, with no guard edit.
6. **Plants:** see the table below.

## Checks run (`41dee463b` content unless stated)

| Check | Result |
|---|---|
| P1-P4 on `e39a5d2fa` (commit 1 tree) | `4 passed` |
| `test_1a_optimize_scope.py` red before the product edit | `12 failed, 3 passed` (P4 and S1-S9) |
| `test_1a_optimize_scope.py` | `22 passed` |
| Focused pure backend: 79 files matching `site_outcomes\|i18n\|statement_cases\|chain_coherence\|outcome-summary\|estate/chain` (not postgres), plus `tools/checks/test_chain_coherence.py` and `test_statement_catalogue.py`, `-n 4` | `1 failed, 2474 passed` in 199 s. The failure is `test_demo_combined_finish_rows.py::test_kis8_protect_passes_on_the_node_line_and_fails_otherwise`, which **fails the same way on `main`** (checked with the changes stashed: `1 failed, 2 passed`). It is not 1a's |
| `tools/checks/statement_catalogue.py` | `OK statement catalogue: load, coverage, legacy, scan (2 adopted), keys, imports` (no `HAND_BUILT_NEW`) |
| vitest `estatePortfolio.test.tsx`, red before the edit (F1-F3 only) | `2 failed, 1 passed`. F1 and F3 failed, and F2 passed with nothing to check |
| vitest `estatePortfolio.test.tsx` | `94 passed (94)` |
| `tsc -b --noEmit` (heavy slot) | exit 0 |
| `test_ch6b_estate_postgres.py -k optimize_card_is_the_one_builder` (`--db`, `assetops_test` base) | **not run**: `MechanismRefused: TEMPLATE_STALE: template inputs a15afccd6b4c != this checkout 8648de978cbe`. A `states` template rebuild keeps only the two newest templates, so it could prune one another lane is using. I left the rebuild for the coordinator's slice-end or full run |
| Fast check-all | The first run (`93f0447ea`) failed 1 of 42: `specs/INDEX.md:45: names a missing file packet.md`. The row was fixed in `382707e17`. The rerun at `382707e17` passed **All 42 guards** in 138.6 s check-all wall (178 s with the slot wait). Logs: `/opt/assetecon/evidence/1a/check-all.log`, `check-all-2.log` |

## Plants (each alone, then reverted)

Backend plants ran in a scratch copy of `backend/` and `tools/checks` (`git archive HEAD`), so the queued postgres run
could not read a planted tree.

| # | Plant | Failed |
|---|---|---|
| PL1 | `_summary` scope day = `lo.date()` | S8, S9 |
| PL2 | `n == {30}` treated as ONE_DAY | S1, S4, S7, S8, S9 |
| PL3 | claim `text` added to the statement as a declared `name` slot | S1, S7, S8, every case render, and the guard (`CASE_MISSING` x3). Undeclared, the guard reports `LOAD FIELD_UNDECLARED portfolio_card.cost_scope amount` |
| PL4 | `each_differ` case deleted | guard `CASE_MISSING portfolio_card.cost_scope each_differ` |
| PL5 | `scope` read from the Optimize card on every card | F3 only (`1 failed | 3 passed`; F1, F2 and the uqfi3 five-hook test pass), in the worktree, then `git checkout` |
| PL6 | (commit 1 tree) `window_day` rule 3 returns `lo`'s date | P1, and P2 too |
| PL7 | `each_differ` reads "... on the last day it shows, not their total" | S5, S5b, S5c, S7, case render `[each_differ]`. The catalogue guard stays OK: it proves coverage, not words |

## Captures (`/opt/assetecon/evidence/1a/captures/`)

The run was `tools/heavy-slot.sh -- node tools/optimize_card_capture.cjs /opt/assetecon/evidence/1a/captures` on the
`41dee463b` build (`npm run build`, then `vite preview` on 5496, fixtures through `page.route`). It produced 12 card
PNGs and 12 viewport PNGs, `{one,two}-{390,1280,1440}-{light,dark}-{card,page}.png`, plus `summary.json`.
- Every capture had 0 console errors, no horizontal overflow and no unlisted API path.
- `one`: "Cost of Kobo's lead issue on 30 October 2026, the last of the 30 days shown, not their total".
- `two`: "Cost at each Site of its lead issue on 30 October 2026, the last of the 30 days shown, not their total".
- The line sits under the figure and above the sentence (for example `one-1440-light-page.png`,
  `two-390-light-card.png`). The other three cards have no line.
- Dark captures equal the light ones: the app has no dark theme (Q-M4).

## Known deviations and mid-build questions (each with the default applied)

- **Q-M1, the case module's English was never rendered.** T9 renders only the `common` and `worked` cases, so PL7 did
  not fail "the case module". *Default:* a parametrised render-and-variant test over `portfolio_card.CASES` in 1a's own
  test file. No guard change.
- **Q-M2, the T8 exact statement set.** `test_sc1_statements.py` T8 is not in §0's Files list, but it must list the new
  key. *Default:* add the key, as earlier adopters did.
- **Q-M3, the postgres card test was not run** (`TEMPLATE_STALE`). *Default:* the coordinator runs it after a template
  `ensure` at the slice-end run. S8 and S9 prove the same wiring without a database.
- **Q-M4, there is no dark theme.** The app has no `prefers-color-scheme` rule in `frontend/src`, so the dark captures
  (`colorScheme: dark`) render the light design. *Default:* take them as the dispatch asks and note this here.
- **Captures cover more than §3.6.** The dispatch asks for 390, 1280 and 1440 in light and dark, for both cases. That
  is a superset of §3.6.
- **Outside the spec's examples.** For several Sites with `n == {1}` on one shared day, step 4 gives `each_one_day`. No
  S case drives that through `cost_scope_text` (only its statement case covers it).

## Review focus

The face order and the hooks (F1, F3, captures), the golden's one-line diff, and the `CostScope` day rule for a
one-day PERIOD window (`wd[0]`).
