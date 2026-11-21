# 3C2 mid-build questions

Questions raised during the build about something the spec did not fix (spec rev 2). Count: 1 (answered).

## MB1 (answered, D-3C2.15: alternative B). The adapter-isolation rule admits only `actions/composition.py` as the importer of `actions/adapters/`

- **What.** Spec §2.4 makes `actions/agreed_composition.py` "the only importer of the adapter", and test 5 asserts it.
  `tools/checks/configuration-persistence.ps1` (the domain table, `Name = "actions"`, and the adapter-import rule
  at lines 270-305) admits exactly one composition module per package: `actions/composition.py`. On the branch the
  guard reports one failure: `Banned adapter import in backend/assetops_backend/actions/agreed_composition.py:11`.
- **Why it is open.** Fixing it in the guard changes a rule other than the writer block, which the dispatch forbids
  and owner-away row 5 holds for the owner. Fixing it in the code moves the import away from the spec's file.
- **Stopped.** Only this one guard line. Everything else is built; the guard's other output is unchanged by it.
- **Proposed default (A).** In the held guard commit (beside the writer block, same owner question at merge), the
  `actions` domain entry admits a second composition module, `actions/agreed_composition.py`, for the adapter
  import rule only (the anti-vacuity count unchanged: either module importing an adapter counts). Code and test 5
  stay as the spec has them.
- **Alternative (B), no guard change.** `build_agreed_actions` and `AgreedActionsService` move into
  `actions/composition.py`; `actions/agreed_composition.py` re-exports them, so DDR G10's
  `build_agreed_actions(url).service.for_tenant(tenant)[0]` and 9(e)'s import rule hold. Test 5's "only
  `agreed_composition.py` imports the adapter" becomes "only `actions/composition.py`"; importing the composition
  then loads the S6-01a composition's modules too (no call into them).

- **Answer.** B, no guard change: `D-3C2.15` in `rulings.md`. Spec rev 3, reviewer guide, handoff and packet amended. The held writer block (`42de02e06`) is still needed and stays held for the owner.
