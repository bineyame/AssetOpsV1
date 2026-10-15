# S4-04 phase 1 review - Site Finding index read

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review4`, branch `review/S4-04-phase-1` at `6ddde94a`, diff `f8a131e3..6ddde94a`.

## Verdict

**Reject until H1 is fixed on the branch.** One High finding: the index can return `CURRENT` with `total_count: 0` (an assessed no-Findings claim) for a day on which the matcher deferred a real Candidate cluster. This is the main thing the slice must not do. The rest of phase 1 is sound and matches the contract.

## Findings

### H1 (High, acceptance gap) - a deferred cross-midnight cluster produces a false `CURRENT` zero

`backend/assetops_backend/analytics/finding_index.py:169-193` (`reaches` / `discover`) and `:215` (`matched`).

**What is wrong.** Discovery only grows across a UTC edge when a *stored* canonical episode lies within 20 minutes of it. The handoff says an unmatched cross-midnight candidate "is already blocked by MATCH_PENDING". That is not true:

- `finding_episode.plan` (`finding_episode.py:709`) skips any cluster whose `margin_ok` fails. That happens whenever a selected neighbouring window within 20 minutes is not CURRENT. The existing test `test_s4_finding_episode.py:191-193` (`test_a_stale_neighbouring_window_skips_the_episode`) proves this.
- `PostgresFindingStore.apply` (`postgres_finding_store.py:134`) still records a completed `finding_match_pass` at the Site-wide fence `selection_seq`, even though a group was deferred.
- So day D reads as matched (pass seq >= D's seq). No stored episode reaches the edge, so D+1 is never inspected, and the index reports `CURRENT` and 0.

**Reproduced on real Postgres.** The probe used only CaseRunner (S2 ingest, S3 worker, S4 matcher) and was deleted afterwards:
1. D+1 (2026-10-26) assessed, then matched.
2. D (2026-10-25) gets a Candidate run 23:10-23:45 and is assessed CURRENT.
3. Late evidence arrives for D+1 (now STALE), then the matcher runs. It plans 0 writes, with statuses `{'2026-10-25': 'CURRENT', '2026-10-26': 'STALE_PROJECTION'}`.
4. Index `[2026-10-25, 2026-10-26)` returns **`CURRENT`, total_count 0**, discovery days `['2026-10-25']`, and no reasons.
5. D+1 is reassessed CURRENT and the matcher has not run yet. The index still returns **`CURRENT` 0**. This is the second form of the gap: a neighbour selection newer than the last pass is never compared, because only the inspected days' seqs are checked.
6. The matcher runs. The same window now returns `CURRENT` with 1 row, episode 23:10-23:45.

D's own basis did not change between steps 4 and 6, so the earlier `CURRENT` zero was false.

**Why it matters.** This is the packet's first rule: no false "no Findings". `CURRENT` needs complete discovery including continuity neighbours (`D-2026-10-15-a-finding-index`, `D-2026-10-15-s404-contract` item 3). The deviation is not equivalent to the ruled "actual S4 20-minute continuity bridge" closure. Stored episodes miss exactly the clusters the matcher deferred because of the neighbour's state.

**Fix.** Derive edge reachability from the selected S3 basis of each inspected day as well as from stored episodes. If an inspected day's selected intervals have a Candidate segment within `CONTINUITY_TOLERANCE` of an edge (the dispatch window read already returns the intervals), add the adjacent day and iterate to the fixed point under the same 62-day cap. That neighbour's own status, and its `matched` against its seq, then block `CURRENT` (STALE or MATCH_PENDING). A simpler conservative alternative is to always inspect the immediate neighbours of every inspected day that has any selection; it blocks more often. Add the probe sequence above as a real-Postgres test with both forms: a stale neighbour, and a newer unmatched neighbour selection.

No Medium or Low findings block. Notes, not required:

- **N1.** The 62-day cap proof (pure `discover` test at exactly 62, plus an injected cap of 2 on real data) is adequate for the cap arithmetic. Once H1 changes the reachability source, the injected-cap real test should exercise the new source as well.
- **N2.** The documented deviations are within the contract: a cursor on a non-current basis gets 409 `BASIS_NOT_CURRENT`; the Site-wide pass in the token restarts cursors conservatively; `display_timezone` is UTC; copy is engineering wording deferred to the W1 plain-language task.

## Verified as correct

- **Check order** (`finding_index_api.py:44-79`): 401/403/404/503, then typed 422 (`UNSUPPORTED_DOMAIN`, `INVALID_WINDOW`, `INVALID_LIMIT`, `INVALID_CURSOR`), then the gate. A closed gate returns 409 `PERFORMANCE_CUTOVER_CLOSED` with its reason before any `index.read`. No refusal carries a status, rows or count.
- **Domain mapping.** `mini-grid-dispatch` maps to `mini_grid`/`dispatch` plus `MATCHER_VERSION`, and is echoed in the response. Any other token is 422, which the test proves on an assessed day.
- **Statuses.** Only `CURRENT` carries rows and a count. Every other status returns `rows: []`, a null count, a null cursor and the not-a-verdict statement. Rows are never reconstructed from heads.
- **Cursor.** A malformed cursor is 422. A well-formed cursor whose scope (including tenant or Site), basis or currentness changed is 409 `INDEX_BASIS_CHANGED` with a reason, `REQUEST_FIRST_PAGE_WITHOUT_CURSOR`, and no rows, count or cursor. The token binds the per-day S3/S4 basis and the exact (finding, revision) row set, so pages cannot splice.
- **Snapshot.** `index_snapshot` runs in one REPEATABLE READ transaction (`_read`). The writer fence (max selection seq, recompute-job marker, revision count) is compared after the per-day dispatch reads; a moved fence gives STALE.
- **Rows.** Order is `episode_start` descending, then UUID ascending, the same rule as S5-01 `choose` (UUID-tie unit test). Intersection is strict half-open. Merged-away IDs appear as relations only. Links are exact revision pins. Amount is UNAVAILABLE.
- **Reads unchanged.** `findings_over` is unchanged. The new store methods are SELECT only, and statement-level rule 8 passes.
- **Isolation.** All queries are tenant- and Site-filtered; the sibling Site and the foreign tenant read UNASSESSED in the test.

## Checks run

- Focused real Postgres, private DB `assetops_r404p1rv_test`, with `assetops_backend` resolved from this worktree: `pytest backend/tests/test_s4_finding_index_postgres.py backend/tests/test_s4_finding_read_postgres.py backend/tests/test_s4_finding_episode.py -q` gave **49 passed in 76.6 s**.
- H1 probe (temporary test file, deleted afterwards): reproduced as described above.
- `tools/check-architecture.ps1`: first run **failed** because this worktree has no `.venv` ("Rule 8 cannot run its SQL statement extractor"). With `ASSETOPS_GUARD_PYTHON` set to the main venv python it **passed**.
- `tools/check-agent-workflow.ps1`: **passed**.
- Not run: the full backend suite (phase 1 requires none; the implementer reports 49 passed in 388 s for the focused set at `ae526aae`, and later commits only touch TESTING.md and the handoff); frontend checks (phase 1 has no frontend change); layout evidence (not applicable to phase 1).

## Residual risk

- S5-01's `discovery_complete` comes from the upstream eligibility, not from this read. Whether S5-01 has a similar deferred-cluster exposure was not reviewed here.
