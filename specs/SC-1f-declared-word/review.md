# SC-1f review

## Round 1 (fresh Claude reviewer, 2026-11-21; discovery review, head `5c235f5c8`)

Summary:
- **Verdict: ACCEPT.** No High or Medium finding. Two Low findings and one spec-text note; none blocks the merge.
- Commit 1 does what D-SC1F.1-3 say: `DECLARED` is step 1 ("Declared", any origin, `None` included); 3A7's accounts
  are `RECORDED` and its tolerance `DECLARED`; a `with` basis names only the figures its variant prints or reads.
- Every changed expected string follows R1, R3 or KD3 (tally below). R2 holds on the real 3A7 path (`T6_FUEL` and the
  zero-stated fuel heading still read "(Recorded)" with the tolerance passed). No stale old string outside docs.
- Honesty: only the tolerance is `DECLARED`; no recorded figure lost its word; `allowed` stays `DERIVED`, outside `of`.
- KD1 is honest today but broader than needed (L1). I recommend a data-only form of it; tried, 512 pass.
- KD2 is the guard's intended remedy ("they dispatch by table"), not an evasion.
- Commit 2: the logger rule is exact-stem, so `catalog`, `blog`, `dialog`, `LOG__` stay scanned; the only widening is
  the module-wide attribute binding (L2, already named in the packet). Allow and baseline diffs are exactly as ruled.
- P59d's N17-only result is correct: N14's `_LOG` is caught by the binding rule without `lstrip`.
- Check-all on the branch merged with main `0ead104e9`: all 42 guards passed.

### Findings

**L1 (Low, preference with a latent-risk reason). `backend/assetops_backend/i18n/render.py:243-245`, the KD1
fallback.** `if not any(isinstance(r.facts.get(n), FIGURES) for n in stated): stated = set(spec["of"])` applies to
any variant of any statement. Today only two statements have an `evidence` slot (`reconciliation.heading`,
`reconciliation.money_word`), and every heading variant with `{basis}` prints `accounts`, so no live sentence is
wrong. A future variant such as `"{heading} ({basis}): no records yet."` would still word figures it does not state,
which is exactly what D-SC1F.3 forbids, and no test or guard would notice. Fix (smallest, and keeps D-SC1F.3 literal):
give `money_word`'s one variant `"requires": {"present": "figure"}` in `i18n/statements/en/reconciliation.py:117`, so
the figure is read (the `_served_words` rule the ruling cites), and delete the three fallback lines and the last
docstring sentence. I applied that as a trial: the four focused files pass (512 passed), then reverted. Not an
acceptance gap; the Architect decides (KD1 below).

**L2 (Low, residual risk). `tools/checks/statement_catalogue.py:158-165`, `_bound_loggers`.** Attribute targets are
collected by attribute name for the whole module, so `self.audit = logging.getLogger(...)` exempts any `x.audit.info(...)`
in that module, e.g. `report.audit.info(f"...")`. Probed: it is exempt. The packet names this. The exposure is small
(the method must also be in `LOG_METHODS`, and the module must bind that attribute to `getLogger`). Optional
tightening: bind attributes only as `self.<attr>` and match only `self.<attr>` receivers. Not blocking.

**Note (spec text, no code change). `specs/SC-1f-declared-word/spec.md` §4, P59d** says "N14 and N17 fail". With
`lstrip` removed, `_LOG` (N14) is still a logger through rule 2 (`_LOG = logging.getLogger(__name__)` binds it), and
`LOGGER` (N15) casefolds to `logger`; only `self._log` (N17) loses its exemption. I confirmed this directly
(N14 planted True, N15 True, N17 False) and by the self-test (77 of 78). The builder's packet line is right; the spec
line could read "N17 fails" when the spec is next touched.

### KD answers

- **KD1 (recommendation).** The built rule is correct and honest for `money_word` (its sole job is the word of a
  figure printed beside it, D-SC1.16), but it is a general escape hatch keyed on "no figure stated", which is the
  case D-SC1F.3 exists to catch. Recommend the ruling read: "A `with` basis counts only the `of` figures its variant
  prints or reads; a statement that words a figure printed elsewhere (`money_word`) reads it with `requires: present`."
  That needs no render special case. If the Architect prefers to keep the render rule, it should at least be narrowed
  to a statement none of whose variants print any `of` slot (a load-time property, true only of `money_word`).
- **KD2.** Sound. SC-1 spec §3.8 says the four mechanism files "dispatch by table"; `_LATE` sits beside `_FILL` and
  is the same pattern. It is not the L2-of-SC-1 evasion (a string bound to a name to dodge the compare): the slot
  type is a table key, as for every other per-type behaviour in `render.py`.
- **KD3.** Correct: R1's rule applied to the third origin word; the tolerance is printed in that heading.

### Checks run (reviewer)

- `tools/heavy-slot.sh -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- test_sc1_statements.py
  test_3a7_reconciliation_words.py test_3a7_reconcile_command.py test_3a7_reconciliation.py -q`: **512 passed in
  3.54s** at `5c235f5c8`.
- `python3 tools/checks/statement_catalogue.py`: `OK statement catalogue: ...`, `ALLOWED entries: 2` (the two
  `profiles.py:124` `CODE` lines). `--self-test`: `OK ... 78 of 78 plants behave`.
- Diffs: allow file holds exactly the two `profiles.py` `CODE` entries; the baseline loses exactly four fingerprints
  (`profiles.py` x2, `commercial_upload_api.py` `g:build_commercial_upload_router.run:395904969735`, `estate/index.py`
  `g:opportunity_read:693eaf7b776b`), nothing else.
- String tally over commit 1's test diff: removed `(Recorded)` x32 = added `(Recorded and Declared)` x10 (headings) +
  `(Declared)` x22 (every one `within N% (Declared)`); `(Recorded and Emulated)` x23 -> `(Recorded, Emulated and
  Declared)` x23; `(Recorded and Estimated)` x1 -> `(Recorded, Estimated and Declared)` x1 (KD3). `git grep` finds no
  `% (Recorded)` or `Recorded and Emulated)` outside `specs/`, `.ai/`, `.agent/` (only the historical 3A7 packet).
- Plants (applied, run, reverted; tree clean after each):
  - P59b (`_fill_evidence` over every `of` slot): 4 failed (`zero_stated1` x2 parametrisations, T13,
    `test_r2_words_t1_t2_t4_t5_t6`), as the packet says.
  - P59d (no `lstrip("_")`): self-test `77 of 78`; direct probe shows N17 is the one.
  - Reviewer plants PRV1 `def f(catalog, x): catalog.info(f"the gap is {x} today")` and PRV2
    `self.dialog.warning(f"the gap is {x} today")`, expected `HAND_BUILT_NEW`: self-test `80 of 80 plants behave`
    (both caught). Direct probe: `catalog`, `blog`, `dialog`, `LOG__` scanned; `report.audit` exempt (L2).
  - KD1 alternative (`requires` on `money_word`, fallback removed): 512 passed.
- Check-all, scratch worktree, branch merged with main `0ead104e9` (contains `41425318f`), merge not committed:
  `bash tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1` ->
  `check-all: 148.1 s wall (0.2 s waiting for a slot), 4 jobs at once.` / `All 42 guards passed (blocking; 0 advisory,
  0 warned).` Two self-tests skipped by design (estate guard and heavy-slot pool: unchanged files, run with `-Full`).

### Not verified

- `test_3a7_reconciliation_postgres.py` not rerun; cited from the packet (3 passed on `assetops_test`, at `031f874fa`,
  before the `_LATE` rewrite). The rewrite is behaviour-neutral and the no-DB files cover the same sentences; the
  residual is small.
- The owner has not yet seen "Declared" (5c walkthrough, D-SC1F.6).

### Residual risk not in the packet

- After a part returns, `r.stated` holds the part's set until the parent's late pass resets it. Correct today because
  only `evidence` reads it and parts fill in the first pass; a future late slot type reading `r.stated` would need
  the same reset.
