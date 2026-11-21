# SC-1a handoff (PARTIAL: units 1 and 2 done, unit 3 not started)

Branch `task/SC-1a-composer`, worktree `/opt/assetecon/AssetOpsV1-sc1a`, off `main` 8805ee169.
Python: `/opt/assetecon/AssetOpsV1/.venv/bin/python` (the worktree has no `.venv`); PYTHONPATH =
worktree `backend:backend/tests:contracts:simulator:gateway:field:host:tools` (verified: `assetops_backend` and
`assetops_contracts` load from the worktree).

## Done

- `5e91634ac` unit 1: `i18n/schema.py`, `facts.py`, `formats.py`, `conditions.py`, `catalogue.py`, `render.py`,
  `wire.py`, `messages.py` (`Param` only), `__init__.py`; `statements/en/vocabulary.py`, `common.py`;
  `backend/tests/statement_cases/{__init__,common,worked}.py`; tests T1-T3, T7, T8, T10-T12, load and fact plants.
- `a96e1eaab` unit 2: T4, T5, T6, T9, T10 over every case, T13, render plants.
- `tools/heavy-slot.sh -- python -m pytest backend/tests/test_sc1_statements.py -q`: **338 passed in 1.32s**.
- Mid-build questions: 3 (`mid-build-questions.md`), each built with a stated choice. Q1 decides the guard's
  mechanism file list (below).
- Process note for the packet: the mechanism was drafted before its tests in the interrupted-session restart; each
  plant was then run and fails with its code (none was weakened to pass).

## Next: unit 3 (spec §3.8, §3.8.4, §4 rows for `tools/checks/*`, `check-all.ps1`; then packet, status, state)

Design already fixed by the code (keep it):

- **Mechanism scope (Q1 choice):** `i18n/{schema,facts,formats,conditions,catalogue,render,wire,__init__}.py`;
  `messages.py` and `locale.py` go to the ratchet scope and its baseline. `MECH_BRANCH` files: formats, conditions,
  render, wire (already free of `"x" in d` / `== "x"`; `catalogue.py`, `facts.py`, `schema.py` use string compares and
  are exempt from `MECH_BRANCH` only). Allowed constants: in `schema.TOKENS` first, else upper snake (then
  `MECH_INSTANCE` if it is a state value, absent reason or vocabulary entry key: take these from the shipped catalogue
  **plus** `statement_cases.worked.WORKED`, else P47's `"MATCHED"` has nothing to match), else `schema.SYMBOLS`,
  else `^\d+(\.\d+)?$`; f-string literal parts must be in `SYMBOLS`; format-spec constants match `^,?(\.\d+)?[fd]?$`;
  `__all__`, docstrings, logging-call args and `raise <UNSERVED>(...)` args exempt.
- **Coverage:** render each case with `assetops_backend.i18n.render._render(msg, None, case.evidence is not None,
  trace)`; skip cases whose key is not in the shipped catalogue (the worked ones); `CASE_MISSING`, `CASE_UNKNOWN`,
  `CASE_VARIANT` per §3.8 (2); `part_only` covered through parents.
- **Self-test:** copy `backend/assetops_backend`, `backend/tests/statement_cases`, `config`, `backend/conversions`
  and the two baselines to a temp root once; per plant write/restore one file and run the guard in a subprocess with
  `--root <tmp>` (and `--adopt <path>` for P13, P13a-q, N1-N3, since `ADOPTED` is empty). P44: empty one baselined
  leaf module. P50: `--write-baseline` with the file present.
- **Baselines:** produce the hand-built one from `main`: `git archive 8805ee169 backend config | tar -x -C <scratch>`,
  run `--write-baseline --root <scratch>`, copy the JSON in. Legacy baseline: SHA-256 first 16 hex of each
  `messages.CATALOGUE["en"]` template, sorted.
- **KEY_INSTANCE:** token set from `site_id`/`site_code` keys in `config/**/*.{yaml,yml,json}` and
  `backend/conversions/*.json`; check the set before relying on it (the noun key `site` must not be a token, or the
  rule needs the 3-letter floor plus a look at real codes); a test asserts `kisiwa` and `kobo` are in it.
- `I18N_PRIVATE` / `I18N_BYPASS` over python outside `backend/assetops_backend/i18n/`, `backend/tests/`,
  `tools/checks/`; P48/P49 planted in a backend module.
- `tools/checks/test_statement_catalogue.py`: guard clean on the real tree, `--self-test` passes, rule functions on
  source strings for P13a-q and N1-N4, the token-set assertion. Wire two `Add-Guard` lines next to the fuel wording
  guard (`tools/check-all.ps1` ~line 331).

Then: focused tests, i18n + refusal-message + 3A2/3C1a regression, `check-architecture.ps1`,
`check-agent-workflow.ps1`, fast check-all; `packet.md` (2.5k; reviewer guide "Packet" list); spec `Status:
in_review`; `.ai/state/` entry and index line. `USER_REVIEW_REQUIRED: false`.

## Risks

- Ratchet-scope speed: the scan parses every backend module per subprocess; time the self-test before wiring it.
- `KEY_INSTANCE` false positives from generic tokens in Site codes (see above).
