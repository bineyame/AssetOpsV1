# Architect request: W2-07 R7 (q2)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`, the "implementers never decide" and "Token Efficiency" sections;
- `.agent/W2-07-build-spec.md`, especially q1 R1;
- R7 in `.agent/W2-07-pending-rulings.md` on branch `task/W2-07-ev-site-evidence-money` at `3bb11d36` (use `git show`).

Your q1 R1 ruling assumed the link and the accepted rows are written in one transaction. The builder showed they are not:
- `open_batch` (`evidence/adapters/postgres_evidence_ledger.py:287`, link at `:336`) and `decide_chunk` (`:430`/`_persist :531`) commit separately;
- see also `_run :145-149` and `ledger_service.py:147`/`:183`.

R1's exact trigger left the SOURCE_GATE row for the late batch's 08:00–09:05 window uncreated.

Check how the merged W2-06 P7 trigger (`0025_w2_ev_session.py`) and the cold `0023_w2_cold_consequence.py:cold_consequence_dirty_on_source_gate` handle the same ordering. Then rule R7 as concrete artifacts:
- the literal trigger function body (SQL);
- the trigger timing and target table;
- the exact `test_0026_trigger_only_work_and_exact_conflict_constraint` assertions.

Option C, which changes the ledger, is out of W2-07 scope unless you show it is required.

Also dry-read commits 2–3 against the code as it is now, and answer anything else open. If nothing else is open, say so in one line.

Append to `.agent/W2-07-build-spec.md` as "Run 2 rulings (q2)", superseding q1 R1. Write nothing else. Do not commit.
