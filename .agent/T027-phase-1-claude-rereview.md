# T027 phase 1 fix round: re-review

Reviewer: Claude (independent of the Implementer's fix round; Reviewer is Claude under
`.ai/ROLE_CONFIG.md` until the Codex reset 2026-10-03 21:23). Range `ab0b2cd..24bc13e`.

## Verdict: accept (one trivial hygiene finding, optional)

## Findings from review 1

| Finding | Status | Evidence checked |
| --- | --- | --- |
| B1 AC15 isolation | Resolved | `t027_isolated_probe.py` and `TestRebuildIsolated`: subprocess is `python -I`, cwd is a tmp dir outside the repo, a `MetaPathFinder` raises on `assetops_simulator`, `host`, `lab_execution`, `source_stages`, `kobo`, `lab_app`, `fixtures`, and the child reports `leaked` modules (asserted `[]`). It compares evidence, records, per-record details and rejections against an in-process build (audit times excluded) and asserts the Lab route is 404. Scratch mutation: appending `import assetops_simulator` to `evidence/read_model.py` made the test fail (`ImportError: blocked`); reverted, tree clean. Fixture is two artifacts, 5 records, one null value; small but not trivial. |
| N1 registry is configuration | Resolved (location carried) | `TestRebuildAfterFoundationEdit` (registry kept rebuilds after an edit at v2; empty store refused `CONFIGURATION_UNRESOLVED`); docstring in `json_evidence_store.py` and packet state it. Location question carried in the backlog with trigger T034. |
| N2 | Carried correctly | Backlog entry has what, why safe, what would change the answer, and the fix. |
| N3 retry control | Resolved | `RunCommitPanel.tsx:157-165` shows "Retry release" for REFUSED (same POST, refusal still shown); test clicks it and asserts one POST and the success message. |
| N4 batch id scope | Resolved | `service.py` refuses a batch id already released at another Site; the lookup only runs when the batch has no record at this Site, so same-Site idempotent re-posts are untouched (existing idempotency tests pass). `test_a_batch_id_used_at_another_site_is_refused`. |
| N5 refusal count | Resolved | `_conflict` records one rejection per (batch id, digest); test posts three times and gets 1, then a different content adds a second (2). The Evidence count reads the same rejection list. |
| N6 | Carried correctly | Backlog entry in the required format, with the two-process risk named. |
| N7 rules | Resolved | Scratch mutations, each reverted: unfiltered inventory fails; an added `Operator home` rail item fails with two messages (Operator home and 2 items); replacing the `/` `Navigate` fails. Each rule has a presence check against vacuity. `1c63032` regex repair works (the rule passes on the real tree and fails on mutation M1). |
| N8 | Resolved | Duplicate comment removed; AC23 row cites `operatorSiteTabs.test.tsx:353`. |
| N9 | Carried correctly | Note in `.agent/T027-phase-1-handoff.md`. |

## New findings

- N10 (nit, hygiene, `tools/__pycache__/run-store-evidence.cpython-312.pyc`): a compiled
  bytecode file was committed in `c9fb412` or a following commit, although `__pycache__/` is
  in `.gitignore` (it was force-added). It is the only tracked `.pyc`. Fix: `git rm --cached`
  it. Not blocking.
- Note (not a finding): the isolated fixture exercises no rejected record, so the compared
  `rejections` payload is empty in that test. Rejection rebuild is covered by the in-process
  rebuild tests.

No regression and no scope beyond the findings found in the diff.

## Checks (all run by me, serially)

- backend pytest: 1417 passed
- host pytest: 602 passed
- simulator pytest (from `simulator/`): 244 passed
- frontend `npx.cmd tsc --noEmit`: clean
- frontend `npm.cmd test`: 42 files, 1056 passed (it ran in this session, unlike the usual sandbox gap)
- frontend `npm.cmd run build`: built
- `check-architecture.ps1`: passed; `check-agent-workflow.ps1`: passed

Not run: `tools/layout-evidence.mjs` (needs Chrome, backend and dev server). The fix round
changed no layout, so the first review's layout evidence stands.

## Processes

`Get-Process` shows python PIDs 11336, 12008 (started 9/24), 13284, 31760 (10/3 07:19); node
PIDs 6692, 33832 (9/30), 28208, 32872 (10/1), 29796, 37372 (10/3 06:59); many chrome. All
started before this review; I cannot attribute them to the fix round and killed nothing.
