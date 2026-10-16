# S5-01 deferred-cluster check (S4-04 phase-1 H1 applied to the Site Overview)

Targeted investigation, not a full review. Fresh Claude reviewer, worktree `AssetOpsV1-review4`, branch
`review/S5-01-deferred-cluster` cut from `main` at `28324074` (after the OPS-02 merge). `assetops_backend` was
resolved from this worktree (`AssetOpsV1-review4\backend\assetops_backend\__init__.py`), using the main venv
python. The private DB `assetops_s501dc_test` was dropped afterwards. The probe was a temporary test file that
has been deleted. It used only the existing `CaseRunner` (S2 ingest, S3 worker, S4 matcher), `make_tick`, the
consequence worker, and the production `build_site_overview_read`. Large health thresholds were passed so that
a single early tick keeps the schedule observation healthy without the tick doing the work itself.

## Verdict

**Exposed (High, same class as S4-04 H1).** While the matcher has deferred a Candidate cluster near a day
edge, S5-01's selected-day Overview reports `freshness: CURRENT`, `known_finding: null` and money `ABSENT`.
That is an assessed "no Finding" claim, which the S5 packet forbids. A related form shows the wrong Finding
(not the one the ruling picks) under `CURRENT`. In neither form did I see a wrong amount for the Finding that
is shown. See Severity.

## Why

- `UpstreamCurrentness.window` (`scheduling/upstream.py:91-130`) runs the S3 status read only for the window
  days (`days`). For the bracket days it reads only `match_state` and blocks only on
  `window_selection_seq is not None and not matched`.
- In the deferred case, D+1 still has its old selection and the matcher's pass is recorded at the Site-wide seq
  (`postgres_finding_store.apply`), so `matched` is true for D+1. D+1's new recompute job
  (`[D+1 09:55, D+1 10:35)`) does not overlap D's snapshot range, so D reads S3 `CURRENT` with no live job. The
  result is no blocker, and eligibility is `CURRENT`.
- `read.py:120` sets `discovery_complete` from those upstream reasons alone. With no intersecting stored
  Finding, `money_state` returns `ABSENT` (`money_state.py`, step 3).

## Reproduction (real Postgres): D = 2026-10-25, D+1 = 2026-10-26

Scenario A, the same sequence as the S4-04 probe:

| Step | S3 D / D+1 | match (D+1 seq / pass seq) | Overview freshness | known_finding | money |
|---|---|---|---|---|---|
| D+1 assessed and matched, tick; D gets Candidate 23:10-23:45 and is assessed; no match yet | CURRENT / CURRENT | 3 / 1, not matched | STALE_PROJECTION (S4 `MATCH_PENDING`) | null | UPSTREAM_STALE |
| Late D+1 evidence (D+1 stale), matcher runs: `planned=0`, statuses `{25: CURRENT, 26: STALE_PROJECTION}` | CURRENT / STALE_PROJECTION | 3 / 3, matched | **CURRENT, no reasons** | **null** | **ABSENT** |
| D+1 reassessed, no rematch | CURRENT / CURRENT | 4 / 3, not matched | STALE_PROJECTION (`MATCH_PENDING`) | null | UPSTREAM_STALE |
| Rematch | CURRENT / CURRENT | 4 / 4, matched | STALE_PROJECTION (consequence pending) | 23:10-23:45, DISCOVERED | WITHHELD_GENERATOR_SERIES |

D's own basis (selection seq 2) is the same in rows 2 and 4, so the row-2 ABSENT is false. **Form 2** of H1
(the neighbour is reassessed after the pass) is *not* exposed in S5-01. The seam's bracket-day `MATCH_PENDING`
check catches it, which is where S5 is stronger than the S4-04 phase-1 index.

Scenario B: an existing Finding on D, then a later deferred cluster.

| Step | Overview freshness | known_finding | money |
|---|---|---|---|
| D Candidate 23:10-23:30 matched with D+1 current, consequences settled, tick | CURRENT | 23:10-23:30 | QUANTITY_UNAVAILABLE |
| More D evidence 23:31-23:45, D assessed; late D+1 evidence; matcher runs (`planned=1`: it revises only the earlier Finding, and defers the new cluster ending 19 min before midnight); consequences settled | **CURRENT, no reasons** | **23:10-23:25** | PENDING_REASSESSMENT |
| D+1 reassessed, rematch, consequences settled | CURRENT | **23:36-23:41** (a different Finding, greatest start) | WITHHELD_GENERATOR_SERIES |

While the cluster was deferred, the Overview showed an earlier Finding as the ruled choice under `CURRENT`, and
`several_intersect` was false. After the rematch the ruling picks a different Finding for the same D basis.

## Severity

- **Proven:** a false `ABSENT` with freshness `CURRENT` (scenario A), and a wrong Finding choice under
  `CURRENT` (scenario B). Neither showed an amount: the fixture's money gate stops at `QUANTITY_UNAVAILABLE`,
  `PENDING_REASSESSMENT` or `WITHHELD`.
- **Not proven, inferred:** in scenario B, with a fixture that reaches `PRICED`, the card could show a current
  amount for the earlier Finding. That amount would be the correct, exact-head amount *for that Finding*. The
  read's own gates (latest revision, consequence basis CURRENT, seam head match) would all pass, because nothing
  about that Finding changed. So the exposure is "a current amount on the wrong Finding card", not a wrong
  number. The card already says it is not a Site total. I found no path where the deferred cluster turns an
  amount into a wrong value. The S4 matcher defers whole groups, so a stored revision whose support has changed
  is not left behind as current with a new basis. I did not prove this exhaustively.
- Rated **High**: it is the packet's first rule (no false "no Finding" or `ABSENT`), the same class as S4-04 H1,
  and S5-01 is already merged on main.

## Minimal fix direction

1. **Root fix, preferred:** make the matcher's pass honest. When `finding_episode.plan` skips a group because
   `margin_ok` or `covered` fails, `PostgresFindingStore.apply` should not record those windows as matched. It
   could store the deferred window days on the pass, or record `matched_through_selection_seq` per window, so
   that `match_state(D).matched` is false (`MATCH_DEFERRED`). That fixes S4-04 H1 and S5-01 in one place, and
   both reads already block on not-matched.
2. **Seam-only alternative (S5 side, conservative):** in `UpstreamCurrentness.window`, also run the S3 status
   read for the bracket neighbour days. Block with `("S4", "NEIGHBOUR_NOT_CURRENT")` when a bracket neighbour
   that has evidence or a selection is not S3 CURRENT. A narrower version blocks only when the selected day has a
   Candidate interval within `CONTINUITY_TOLERANCE` of that edge. Either version blocks `discovery_complete`,
   which turns `ABSENT` into `UPSTREAM_STALE`.
3. Add scenarios A and B above as a real-Postgres S5 test: `ABSENT` must never appear while D+1 is stale after
   a pass, and the chosen Finding must not be presented under `CURRENT` while a deferral is outstanding.

## Checks run

- The probe (two scenarios) on real Postgres, private DB, passed and printed the tables above: 12.3 s and 16.0 s.
- Not run: the guard scripts, focused suites and the full suite (not needed for this question); frontend (no
  frontend question).
