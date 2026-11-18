# S4-01 phase 1 review - `I-finding-store`, `D-finding-revisions`

Reviewer: a fresh Claude reviewer (independent; did not author the slice). 2026-10-12.
Target: branch `task/S4-01-finding-identity`, diff `5f7cd4c..49c85b3` (`bcbc3f4`, `91d20bc`, `6b891ef`, `49c85b3`).
Authority: `tasks/S4-01-finding-identity.md` phase 1, `D-2026-10-12-finding-episode-and-revisions`,
`.agent/architect-A-finding-episode-answers.md`, backlog "A-finding-episode review carries".

## Verdict

**Accept with findings fixed on the branch.** The store, migration, append-only guarantees, guard, fixture
specification and producer are sound and the specified F01-F06/F08 cases behave as claimed. Three matcher/store
defects (B1-B3) violate the decision in paths the fixture does not exercise; each is small and must be fixed on the
branch, with pure `plan` unit tests (B4), before phase 2 builds reads on these rows. Re-review can be a focused fresh
Claude pass over the fix diff plus the S4 Postgres test file.

## Block (fix on the branch before phase 2)

### B1 - Split hands the original ID to a part that does not contain its anchor (decision violation)

`backend/assetops_backend/analytics/finding_episode.py:414-422`. Cluster ownership is greedy in cluster start order:
`owner = next((e for e in over if e.finding_id not in owners), None)`. The sort key only prefers anchor-containing
episodes *within one cluster's overlap list*; it does not stop an earlier cluster from claiming an episode whose
anchor lies in a later cluster. The task and decision require: "retain the original ID for the part containing its
immutable anchor". This occurs naturally after F04-style late earlier evidence (bounds move before the anchor) followed
by a split.

Reproduced with a pure probe (episode `F-orig` anchored 08:30, bounds 08:00-09:00; reassessment yields Candidate
08:00-08:15 and 08:25-09:00 around a contradiction):

```
SPLIT: F-orig SPLIT 08:00:00 08:15:00 None ["ANCHOR_OUTSIDE_SUPPORT: ..."]
SPLIT: afe4cc27-... OPENED 08:25:00 09:00:00 F-orig []
```

The original ID keeps the anchor-free part (with an `ANCHOR_OUTSIDE_SUPPORT` limitation) and the anchor-containing
part gets a new ID. Because `finding.split_from_finding_id` and the key are immutable, a wrong assignment cannot be
corrected later. Fix: assign owners in two passes - first each episode to the cluster containing its anchor, then
remaining clusters greedily - and add a unit test for this case.

### B2 - Concurrent match passes can open duplicate Findings; the fence does not cover Finding state

`backend/assetops_backend/analytics/adapters/postgres_finding_store.py:136-144,163-177` with
`finding_service.py:42-49`. `episodes()` is read outside the advisory lock, and the fence is only
`analytic_run_selection` max seq plus `recompute_job` count/marker. Two passes on one Site (two operators, or the
producer plus a later automated trigger) both plan `OPENED` for the same cluster with different `uuid4` IDs; the second
takes the lock after the first commits, finds the fence unchanged (Finding writes do not move it), and inserts a second
Finding for the same episode. Idempotency `(finding_id, basis, transition)` cannot catch it because the IDs differ. This
breaks "allocate `finding.id` ... once" and the packet's "no partial writes" framing hides it: the writes are atomic
but planned from stale episodes. By inspection (not reproduced; it needs two interleaved processes). Fix: include the
Site's Finding state in the fence (e.g. `count(*)`/max `revision_no` sum or max `created_at` of `finding_revision` for
the Site) so a pass planned before another pass's commit re-plans; add a Postgres test that interleaves a stale plan
after another apply.

### B3 - `recurs_after_finding_id` is set across unassessed time (immutable link without an evidenced separation)

`finding_episode.py:402-409`. The link condition is only `off_before >= prior.episode_end` where `off_before` is the
OFF report immediately before the new interval. It does not require the separation itself to be assessed. Probe:
episode on 10-06, day 10-07 never assessed, Candidate on 10-08 -> `OPENED` with `recurs_after = F-6`. If 10-07 is
assessed later and opens its own episode, the 10-08 Finding's immutable link still points at 10-06. The decision says
"an *evidenced* separation greater than 20 minutes" creates the linked Finding; an OFF 5 minutes before the new run is
not evidence about the preceding day. The packet's residual-risk note (fixture Findings chain across case days) is a
symptom of this, not a benign Q3 consequence. Fix: link only when `site.covered(prior.episode_end, c.start)` and the
prior's own `off_after` is observed (otherwise open unlinked, as the F06 13:00 case already does); adjust the
spec/test expectations if fixture chains change.

### B4 - No pure unit tests for `finding_episode.plan`

The matcher is the core of the slice and is only exercised through the slow Postgres end-to-end fixture, which covers
two-way split/merge in the anchor-first order only. B1 and B3 were found with ten-line pure probes. Given the immutable
columns involved, the absence of unit tests is not acceptable for this slice. Add DB-free tests for at least: split
with the anchor in a later cluster (B1), recurrence across an unassessed gap (B3), 3-way merge, mixed split+merge,
NO_LONGER_SUPPORTED -> Indeterminate (see C3), stale margin skip, cross-midnight bridge with and without observed OFF.
(My probes of a 3-way merge and a mixed split+merge behaved correctly.)

## Carry (Architect / later phase; not blocking phase 1)

- **C1 (Q5) collateral revisions are labelled `SUPPORT_CHANGED` when support did not change.** A backdated control
  at 10-21 appended 8 revisions to Findings on *earlier* days (10-06..10-19) because the Foundation split re-IDs the
  open control revision for every window from 10-03. The packet's residual-risk line and `.ai/CODE_STATE.md` say
  "every later Finding"; the spec's `collateral` note correctly says earlier days - fix the wording. The default is
  honest (it keeps citing the selected revision) and not unsafe, but phase 2/3 History will show "support changed"
  noise on every Finding after any control edit. Recommend a distinct `BASIS_REFRESHED` transition now (one CHECK value
  in 0009, cheap before merge) or an explicit Architect ruling.
- **C2 (Q1) idempotency skips a non-latest identical basis.** `_insert_revision` returns `None` when
  `(finding, basis, transition)` exists anywhere in history, so an A -> B -> A selection (possible if an explicit
  cohort `assess` re-selects an earlier run) leaves the latest revision at B while the current basis is A. The Q1
  default is otherwise safer than the technical design's `UNIQUE(finding_id, assessment_revision_id)`, which would
  refuse genuine cross-window support changes; I agree with the default. Ask the Architect whether reselection of an
  earlier run is reachable; if so, key idempotency on the latest revision only.
- **C3 closed Findings reopen silently.** An Indeterminate reassessment over a `NO_LONGER_SUPPORTED` episode appends
  `UNCONFIRMED` (probe confirmed), and a Candidate over it appends `SUPPORT_CHANGED`/`SUPPORTED`. Neither is a named
  "reopened" transition; the UNCONFIRMED title reads as an active candidate. Architect to rule whether a closed episode
  may be re-limited, and whether reappearance over the same span is a reopen or a recurrence.
- **C4 (Q4) window revision excluded from the basis** means the latest revision can cite a window AssessmentRevision
  that is no longer selected. This contradicts the Q5 rationale ("would leave the Finding citing a non-selected
  revision"). Not unsafe for phase 1; phase 2's read must show the currently selected window revision rather than the
  revision's stored one when they differ.
- **C5 (Q8) fixture control provenance.** The producer and test publish minimum-runtime 0/120 with
  `"source": "TEMPLATE", "source_version": 2`, though these are authored fixture values overriding the Kobo template's
  30. The label rides only in the note. `SITE` is the more honest source value; low severity, fixture-only.
- **C6 merge canonical choice** prefers an anchor-inside-cluster episode over an earlier anchor
  (`finding_episode.py:417-418`), whereas the decision says "earlier stable anchor (then UUID)". Edge case; align or
  record.
- **C7 `test_a_moved_fence_writes_nothing`** applies an empty write list, so "writes nothing" is vacuous; pass real
  planned writes.
- F07 is correctly test-scoped: `dispatch-3.1-s4-test-upgrade` exists only in the test via `monkeypatch`; no product
  code or spec path can produce it. The owner must be told at the checkpoint (task requires it).

## Q1-Q9 defaults

None is unsafe as a fail-closed default for phase 1. Q3's default is unsafe in its current *implementation* (B3), not
its intent. Q5 and Q4 interact (C1, C4). Q2 (modelling-reason Indeterminate may bridge <=20 min) is reasonable and
consistent with "coherent, noncontradictory"; the stricter alternative is not needed. Q6/Q8/Q9 labelling is honest in
the spec, producer docstring and run artifact.

## What I checked and found sound

- Migration 0009: tenant/Site-composite FKs on every relation, immutable creation links with `finding_one_origin`,
  bounds CHECK, transition/lifecycle CHECKs, primary `assessment_revision_id` FK kept (technical design), all five
  tables under `ledger_append_only` (row-level; TRUNCATE is outside triggers, same as earlier ledgers).
- Guard: only `postgres_finding_store.py` may write Finding tables and only via INSERT INTO them.
- Only `status == "CURRENT"` windows with `model_version == dispatch_v3.MODEL_VERSION` count; groups touching a
  non-usable window within +/-20 min are skipped (no create, extend or close). Intervals are owned by the window
  containing `first_on` (`dispatch_v3.py:396`), so cross-midnight intervals are not double-counted.
- Bridge rule: overlap/adjacency joins; a <=20 min gap needs window coverage, coherent non-Candidate segments, and
  observed OFF on both sides between intervals; contradiction/ambiguity/unobserved never bridges.
- Unconfirmed vs no-longer-supported: any Indeterminate/unobserved segment, Indeterminate interval or window claim ->
  UNCONFIRMED; otherwise NO_LONGER_SUPPORTED; neither says repaired or saved. STALE/FAILED/unassessed write nothing.
- Basis hash covers matcher, model, lifecycle, interval revision IDs, bounds, minutes and cited evidence IDs; the
  fence re-check under a Site advisory lock aborts the whole transaction on a moved selection/job.
- Cited accepted evidence is distinguished from the full input set (digest of window `input_sha256`s plus
  `analytic_run_evidence` via the cited runs).

## Checks run (by this reviewer)

- `tools/check-architecture.ps1`: "Architecture check passed." `tools/check-agent-workflow.ps1`: "Agent workflow check
  passed."
- Producer rerun on `49c85b3`: `tools/s4_finding_cases.py run --work <scratchpad>` (DB `assetops_s4cases`, TLS 8763):
  every match step OK, 0 check failures, produced in 130 s; fresh-process verify: all 7 case digests match, 10
  Findings / 25 revisions reloaded match, replay `match-findings` planned 0 -> `VERIFY PASSED`, exit 0. This confirms
  the packet's counts. F05's collateral step planned 9 (1 named + 8 collateral).
- Live confirmation of B3 from that run: `recurs_after` links are 10-08 23:20 -> 10-06 08:00 (10-07 never assessed),
  10-11 08:00 -> 10-08 23:20, 10-15 08:00 -> 10-13 08:30, 10-21 08:00 -> 10-15 12:00, besides the intended F03/F06 links.
- Afterwards: `DROP DATABASE assetops_s4cases` done; no listener on 8763; the TLS server was stopped by the script.
- Pure `plan` probes (scratchpad, no DB): B1 and B3 reproduced; 3-way merge and mixed split+merge correct; C3
  confirmed.
- Not rerun (Implementer-reported green, no specific doubt beyond the findings): backend Postgres 1841, host 667,
  gateway 164, simulator 265, check-all, and `test_s4_finding_store_postgres.py`. No frontend change in this phase,
  so `npm.cmd test`/`build`/`tsc` were not run; layout evidence is not applicable (no UI).
