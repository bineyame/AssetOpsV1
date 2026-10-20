# OPS-01 post-W2 review (ca2e4aef, fc23fb19, 06b049ad vs main)

Verdict: ACCEPT

Scope: diff is tests, .gitattributes, backend/TESTING.md and .agent only; no backend/src change.

## Checks run (private DB ops01r_test, created then dropped)
- Four refusal tests (s6, s7, w203, w206): 8 passed in 88 s; each still asserts its 503 code, refusal now in ~2 s.
- w205b six_registered/second_release + w206 vector-cases subset: 8 passed (217 s), exercising the cache and LF goldens.
- Not run: full suite (per brief). Acceptance numbers (2 runs, 3268/0/0, peaks 62/67, identical node IDs) are the report's claims, not re-verified.

## Findings
High: none.
Medium: none.
Low:
1. connect_timeout=2 proves "connection refused -> 503" only; it cannot distinguish refusal from a 2 s timeout, but port 1 is refused locally, so equivalent. Informational.
2. scenario_cache is per process (lru_cache), read-only (frozen dataclasses per its docstring; no test mutates scenarios found by grep), failures not cached. Import `from scenario_cache` relies on tests dir on sys.path; it worked under pytest. If a future test rewrites shipped YAML mid-run, the memo would be stale; documented in TESTING.md.
3. .gitattributes scope is narrow (two explicit patterns, 7 files, already LF in index, so no renormalization of other files). Other worktrees need re-checkout, as the report states.
4. TESTING.md edits are consistent with the report; serial timing is stated as not re-measured. Fine.
