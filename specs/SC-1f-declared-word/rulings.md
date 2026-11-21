# SC-1f rulings

Architect (Claude), 2026-11-21, owner in session. Owner words: `owner/owner-decisions-list-2026-11-21.md`, items 7
("give declared settings their own word") and 8 ("approve both": `_LOG` counted as a logger name; the P55 allow
helper adds to the real allow file). Read on `main` `27434fe33`: `i18n/statements/en/vocabulary.py` `evidence`,
`i18n/formats.py` `evidence_word`, `i18n/render.py` `_statement`/`_fill_evidence`/`_served_words`,
`i18n/catalogue.py` `_check_evidence_table`, `structure/reconciliation.py`, `i18n/statements/en/reconciliation.py`,
`tools/checks/statement_catalogue.py` `LOG_NAMES`/`_logger`/`_plants_r1`, both hand-built JSON files.

## D-SC1F.1 A declared setting reads "Declared", whatever its origin (owner item 7; amends SC-1 §3.5 and D-3A7.17)

- **Ruling.** In the `evidence` vocabulary, `DECLARED` moves from `observed_by_evidence` to `by_evidence_first`, with
  the word `Declared`. It is then step 1 of `evidence_word`, so the word is the same for every origin, `None`
  included. `observed_by_evidence` keeps `RECORDED` "Recorded", `MEASURED` "Measured" and `DERIVED` "Calculated".
  `VOCABULARY_SCHEMA`'s partition rule holds unchanged.
- **How a figure gets it (per figure, by its producer).** `DECLARED` is for a value a person sets or states as a
  choice: a tolerance, a target or objective, a declared tariff or price, a reserve floor, an assumption an operator
  enters. A figure taken from a system of record, such as management accounts, invoices, billing or meter records,
  is `RECORDED`, even when a person types it in. The producer chooses; the vocabulary only words the choice.
- **Why this word.** The live mock already uses it. `frontend/mockups/v70/index.html` tags settings `declared`
  ("Fuel price: Declared at $1.20 per litre", source tag `declared`; the reserve floor `30%` with `tag('declared')`),
  and the product already says "declare" for objectives (`declare_objective`; "no target declared"). It is honest
  in the owner's sense (`owner/SUMMARY.md` §4): it says a person chose the value and claims no record or
  measurement. "Set" was rejected: "within 1% (Set)" reads as a verb, and the mock does not use it. "Assumed" was
  rejected: a tolerance or a target is a choice, not a belief about the world, and the owner's "assumed" class is
  the estimates (`ESTIMATED`, `MODELLED`).
- **Why step 1.** Origin says where observed data came from. A setting is not observed, so an origin word
  ("Emulated", or "Estimated" for no origin) would misstate it. A setting on a simulated Site still reads
  "Declared". The sentence's observed figures still carry "Simulated", so nothing synthetic reads as observed.
- **Reverse.** Put `DECLARED` back into `observed_by_evidence` with another word.

## D-SC1F.2 3A7's management-accounts figure is `RECORDED`; the tolerance stays `DECLARED` (the class sweep, W6)

- **Ruling.** `structure/reconciliation.py` has one `DECLARED` constant for two figures. It splits in two:
  `ACCOUNTS = Evidence("RECORDED", FINANCIAL)` for `accounts` in `heading_words`, and `SETTING =
  Evidence("DECLARED", FINANCIAL)` for `_tolerance`. The comment above them states D-SC1F.1's rule.
- **The sweep.** On `main`, `structure/reconciliation.py` is the only module that builds SC-1 `Evidence`
  (`grep -rn "Evidence(" backend/assetops_backend` outside `i18n/`). Its `DECLARED` figures are the tolerance (a
  setting) and the accounts (the finance lead's transcription of the operator's management accounts, a record). The
  other `"DECLARED"` strings in the backend are structure-row sources (`rows_*.py`, `targets/`), `declare_objective`
  and `foundation_api`. None of them is an SC-1 fact today. 5c maps them when it adopts SC-1, under D-SC1F.1's rule.
- **Said plainly.** The coordinator's gloss on item 7 says "no 3A7 code change". That holds for the tolerance, whose
  word changes through the vocabulary alone. The accounts constant is a one-line 3A7 change. Without it, every
  heading would call the management accounts "Declared", which is untrue. That is why it is made.

## D-SC1F.3 A `with` evidence word names only the figures its sentence states (render)

- **Ruling.** `_fill_evidence` counts a slot of its `of` list only when that slot's figure is printed by the chosen
  variant, in its own text or in a part chosen under it, or is read by that variant's `when` or `requires`. This is
  `_served_words`' rule, so one definition covers both evidence modes. `_statement` fills a variant's fields in two
  passes. First every field except `evidence` slots, recording what this variant (and its parts) printed and read.
  Then the `evidence` slots, from that record. A basis with no counted slot stays `ABSENT_PRINTED`.
- **Why.** `reconciliation.heading`'s `basis` is `of: [accounts, recorded, tolerance]`, and 3A7 always passes the
  tolerance. The `zero_stated` and `not_received` sentences do not print it. While `DECLARED` read "Recorded", the
  extra word was invisible. With D-SC1F.1, "Fuel cost (Recorded and Declared): the accounts say $0.00 and no fuel
  invoices are recorded." would name a figure that is not in the sentence. D-SC1.18 asks for the evidence of every
  printed figure. It does not ask for the evidence of a figure that is not printed.

## D-SC1F.4 A logger is recognised by its name's stem or by its `getLogger` binding (owner item 8a; amends D-SC1.33 rule 5)

- **Ruling.** `_logger(receiver, bound)` is true for any of these three:
  1. An `ast.Name` id or `ast.Attribute` attr whose name, with leading underscores stripped and case-folded, is
     `log`, `logger` or `logging` (`LOG_STEMS`; this replaces `LOG_NAMES`; it covers `_LOG`, `LOGGER`, `self._log`).
  2. A name or attribute that the same module binds to a `getLogger` call (`ast.Assign` or `ast.AnnAssign`, any
     scope, `logging.getLogger(...)` or a bare `getLogger(...)`), collected in `bound` in one pass over the module.
  3. A receiver that is itself a `getLogger(...)` call (kept).

  Both call sites (the exemption at `_Scan` and the `UNSERVED_SERVED` check) use it. A name imported from another
  module, or bound to any other call, is not a logger, so its strings stay scanned.
- **Consequence.** Two baseline fingerprints go stale and are pruned with `--prune`:
  `commercial_upload_api.py` `g:build_commercial_upload_router.run:395904969735` (`_LOG.warning`, line 151) and
  `estate/index.py` `g:opportunity_read:693eaf7b776b` (`_LOG.exception`, line 132). ENV-1 has not renamed `_LOG`:
  it is `_LOG` on `main` and on every `task/ENV1-*` branch. Either name is a logger after this ruling.
- **Why.** The owner approved it. The stem rule is the class (W6): logger naming varies by module, and a list of
  spellings missed `_LOG`. The binding rule catches loggers with any name, such as `audit = logging.getLogger(...)`.

## D-SC1F.5 The P55 plants add to the real allow file; the date-format tokens move to it as `CODE` (owner item 8b)

- **Ruling.** In `_plants_r1`, `allow(entry, path)` reads the copied base's `ALLOW` file and returns it with `entry`
  appended to `path`'s list (a new list; the base file is not edited), instead of a one-entry file. Then
  `commercial/profiles.py`'s two `_swap_day_month` fingerprints (`h:_swap_day_month:052fded502f9`,
  `h:_swap_day_month:d40e38ccee22`) leave `statement-handbuilt-baseline.json` and become allow lines `{"fingerprint":
  <fp>, "class": "CODE", "why": "date-format tokens DD and MM swapped in a layout's format string; not served"}`.
- **The third print.** It is not restored. `commercial_upload_api.py:151` is a `_LOG.warning` call, so under D-SC1F.4
  it is no hit at all. An allow line for it would be `ALLOW_STALE`.
- **Why.** SC-1a moved the three into the baseline only because the replacing helper wiped the allow file in every
  P55 run (`e25709246`, then `e6404c1e4`). With the merge, the allow file holds what it is for, classed and printed
  by `ALLOWED` notes, and the baseline holds only real legacy prose.

## D-SC1F.6 Size and order: 1.0 unit in two commits, one build; text reviewed at the 5c walkthrough

- **Ruling.** Commit 1 (0.5): D-SC1F.1 to .3 and their tests. Commit 2 (0.5): D-SC1F.4 and .5 and the guard's
  plants. One Opus build, a fresh Claude review, then merge on ACCEPT. The owner sees "Declared" at the 5c
  walkthrough, as with 3A7's wording (`USER_REVIEW_REQUIRED: true`, not merge-blocking: owner, 3A7 merge, "merge
  on ACCEPT, wording at the 5c walkthrough").
- **Gate.** SC-1f starts on `main` now. It touches 3A7's merged files, so a lane holding 3A7 or 5c files merges
  `main` after SC-1f lands. 5c unit 1 starts on or after SC-1f.

## D-SC1F.7 A `with` basis counts only the figures its variant prints or reads (review L1, KD1)

- **Ruling.** A `with` basis counts only the `of` figures its variant prints or reads; a statement that words a figure
  printed elsewhere (`money_word`) reads it with `requires: present`.
- **Built.** `reconciliation.money_word`'s variant carries `"requires": {"present": "figure"}`; the KD1 fallback in
  `_fill_evidence` is removed. Pinned by `test_sc1f_a_with_basis_counts_only_the_figures_its_variant_states`.
