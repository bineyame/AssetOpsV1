# Architect follow-up: run the focused verification you could not start

Your three documents in `Docs/demo-sprint/` record every test as "not executed" because the system Python has no pytest. The project Python works:

- From this worktree, run: `PYTHONPATH="backend;." C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe -m pytest <files> -q -p no:cacheprovider`.
- Use the `;` separator. The venv's own install points at an older checkout, so PYTHONPATH is required.
- The coordinator already ran `backend/tests/test_w403_scenario_rules.py`, `test_s6_verification_rules.py`, `test_w207_ev_money.py` and `host/tests/test_s6_verification_replay.py` at 63f9f8e5: 76 passed, 2 skipped.

Do this:
1. Run the other non-Postgres tests you cite (backend, host, simulator), in small groups. Postgres tests that skip or need a DB stay "test present but not executed".
2. Run the short simulator benchmark that `simulation-evolution-assessment.md` proposes, with the existing simulator entry points: a few simulated days, under ~5 minutes and ~2 GB. Record runtime, memory, observation volume, and determinism (same seed twice, digest equal). Label these as observed, and label 60–90-day figures as extrapolated estimates.
3. Update only the verification columns and notes, and any maturity or conclusion the results change, in the three documents. Keep them concise.

Same limits as before: no full suites, no `vite build`, no dev servers, no DB creation, and no product code, test or `.gitignore` edits.
