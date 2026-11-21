# 3B7a mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **3** (spec rev 2; units 1 to 3 build, 2026-11-20).

## Q1 (§2.5 and §4.2): `structure_snapshot/rules_digest.py` is storage technology above the adapter layer once the
domain entry exists

- **What.** With the §4.2 domain entry applied (scratch copy of the guard; the repo file is not edited), rule 2 of
  `configuration-persistence.ps1` refuses `structure_snapshot/rules_digest.py:15: from pathlib import Path` ("Storage
  technology above the adapter layer"). The digest must read source bytes, and §2.5 fixes the path and a `Path`
  signature. It is the only failure left with the block applied (packet "Guard").
- **Stopped.** The final form of the guard block only. Everything else is built and green; `rules_digest.py` stays at
  the spec's path. Not worked around (no `pathlib`-free or `open(`-free rewrite to slip past the pattern).
- **Options.** (a) Move it to `structure_snapshot/adapters/code_digest.py`: only `composition.py` imports it, which
  already computes the digest once and passes the string (§2.5), so no rule changes; tests 10 and 11 follow the path.
  (b) Keep the path and add a one-file rule-2 allowance to the block (no longer purely additive; owner approval).
  (c) Move it out of the domain package (`assetops_backend/code_digest.py`). Builder's view: (a). Precedent: ON1
  mid-build Q2 (`onboarding_may_grant` and the `open\(` pattern).

## Q2 (§0 "Migration number", §6 regression): 3A2's migration test asserts 0065 is head

- **What.** `test_3a2_commercial_upload_postgres.py::test_6_downgrade_refused_with_an_upload_then_down_and_up`
  asserts `script.revision == get_current_head()`; with 0066 it fails (`'0065_commercial_upload' ==
  '0066_structure_snapshot'`). Its down/up still works through 0066 (3A1's downgrade test, which also passes 0066,
  is green).
- **Stopped.** That file is outside this slice's declared scope, so it is not edited. Precedent: 3A2 unit 1 edited
  3A1's downgrade test under a pre-flight answer (P2).
- **Ask.** Authorise the one-line change (assert 0065 is an ancestor of head, e.g. it is in `walk_revisions()` and
  0066's `down_revision`), or name another fix.

## Q3 (§4.4): `verify` of an id that is not a portfolio snapshot of the tenant

- **What.** §4.4 lists no code for an unknown snapshot id or a Site row's id.
- **Default applied (not blocking).** Exit 2 `UNKNOWN_SNAPSHOT` "No portfolio snapshot of this organisation has that
  id." (refused before any rebuild). A malformed UUID is argparse's own exit 2. Confirm or rename.
