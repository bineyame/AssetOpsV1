# S4-03 phase 1 fix - fresh re-review

Reviewer: fresh Claude (did not author the work), 2026-10-13. Branch `task/S4-03-finding-evidence-history`, HEAD `91dea16`. Scope: diff `a145ca9..91dea16` against F1 in `.agent/S4-03-phase1-review.md`.

## Verdict: ACCEPT

F1 is closed. No new findings.

## F1 verification

- `finding_read.py:574-577`: History `cited_evidence` is now `{count, resolved, accepted_rows: ALL_RESOLVED|UNRESOLVED_PRESENT, note}`. The History row no longer uses COMPLETE or BROKEN. `accepted_rows` is computed exactly as before (`cited == resolved`, the accepted-row join), so the label now matches what is checked. The note says it counts accepted-evidence rows only, and that batch, envelope, basis and digest lineage is checked in the Evidence read. That is accurate: Evidence `_record_breaks` and the set-level checks are unchanged.
- Remaining consumers: I grepped `backend`, `frontend/src` and `tools` for `cited_evidence`, `lineage`, `COMPLETE`/`BROKEN` and the history route. The only `COMPLETE`/`BROKEN` left are the Evidence read's own `lineage.status` and per-record status (`finding_read.py:147, 530`), and those are correct. Every frontend `cited_evidence` hit is the S4-01 root revision's list or the count (`findingClient.ts`, `SiteFinding.tsx`). No frontend or tool code calls the Finding History route yet (that is phase 3), so nothing reads the old field.
- Non-vacuity: I restored `finding_read.py` from `a145ca9` and ran `-k envelope_only`. It failed with `KeyError: 'accepted_rows'` at `test_s4_finding_evidence_history_postgres.py:299`. The old reader also returns `lineage: COMPLETE` for that row, which line 300 would reject. The Evidence half of the test (BROKEN with `ENVELOPE_DIGEST` only) already passed under the old code, as expected, because F1 concerned History only. I then restored the file with `git checkout HEAD --`, and `git status` was clean apart from the coordinator handoff.
- No other behaviour changed. The diff is the one dict entry in `finding_read.py`, test assertions updated to match, one new test, and handoff text. The broken-join test still asserts the same count and resolved values.

## Checks run

- These five Finding files ran against `assetops_test` on 127.0.0.1:55432: `test_s4_finding_evidence_history_postgres.py`, `test_s4_finding_evidence_history_api.py`, `test_s4_finding_api.py`, `test_s4_finding_read_postgres.py` and `test_s4_finding_store_postgres.py`. Result: 34 passed, 0 skipped, 240.85s.
- `tools/check-all.ps1`: all 9 guards passed.
- Not run, as the dispatch scoped them out: the full backend suite and the frontend test, build and tsc. The fix touches no frontend code.

## Carries

- Carries C1-C5 from the phase 1 review are unchanged.
- New, low: when phase 3 renders History it must show `accepted_rows` as a row-existence count and link to Evidence for lineage. It must not convert `ALL_RESOLVED` into a "lineage complete" badge. The API note makes this explicit, but the UI wording is still unreviewed.
