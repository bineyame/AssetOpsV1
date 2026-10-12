# S4-01 phase 2 (`I-finding-read`) independent review

Reviewer: a fresh Claude reviewer (no part in authoring), 2026-10-12.
Branch `task/S4-01-finding-identity`, diff `0484268..HEAD` (1e24e4d, 72aec76, 2d980db, ef1adc6).
Spec: `tasks/S4-01-finding-identity.md` phase 2 and "Detail read and visible states"; decisions
`D-2026-10-12-finding-episode-and-revisions`, phase-1 and phase-1-fix clarifications,
`D-2026-10-09-pre-s3-claim-routes-and-actor`; carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`.

## Verdict

**Accept with findings fixed on the branch.** B1 and B2 must be fixed before phase 3 starts, because phase 3
renders these states directly. Both are small and local to `finding_read.py`. The C items carry. Q17 and Q19
need an Architect ruling before I-S4-01 closes.

## Findings

### B1 (block): an Indeterminate or ambiguous-cohort window reads as assessed `NO_FINDING`
`backend/assetops_backend/analytics/finding_read.py:254-257`. `window_state` returns `NO_FINDING` whenever the
window is CURRENT, has no Candidate segment and has no Finding. It never looks at the window assessment's
`claim_level` or its limitations. A `dispatch-3.1` window with an AMBIGUOUS or absent cohort, or with
GENERATOR_SERIES_AMBIGUOUS, is `INDETERMINATE` and has no intervals at all. So the read calls it "the current
selected assessment has no Candidate segment and no Finding".

I reproduced this on Postgres with the fixture's own F08 day: I ran F01 and F08 into an isolated
`assetops_s4p2rev_test` database, which I dropped afterwards.
`GET /api/sites/KOBO-001/finding-windows/2026-10-19` returned `NO_FINDING`, assessment status CURRENT, while the
selected window revision was `claim_level INDETERMINATE` with
`AMBIGUOUS_COHORT: a source reports the same time span under more than one sequence epoch ...`.

This contradicts the task ("no current assessed basis cannot become NO_FINDING", F08 "ambiguous cohort does not
create or close a Finding"). It also contradicts the matcher, which treats an INDETERMINATE window as UNCONFIRMED
rather than closure (`finding_episode.py:396-397`). The Postgres test only asserts
`"NO_FINDING" in states.values()` over 10-05..10-23 (`test_s4_finding_read_postgres.py:153-156`), which passes
with this defect.

Fix:
- Return `NO_FINDING` only for a CURRENT window whose window revision is not INDETERMINATE. Give an INDETERMINATE
  window its own typed state, for example `NOT_DETERMINABLE` with its limitations.
- Include `claim_level` and `limitations` in the body, so a LIMITED no-Candidate window discloses what limits it.
- Pin each day's expected state in the test, at least 10-06 FINDINGS_RECORDED, 10-19 not NO_FINDING, one complete
  no-Candidate day NO_FINDING, and 09-01 NOT_ASSESSED.

### B2 (block): a pinned historical revision is labelled `FINDING_MATCH_PENDING`
`finding_read.py:140-143, 205-206`. For an exact older `revision_id`, `revision.currentness` is computed against
that revision's own windows. Those windows are CURRENT but no longer the cited selection, so the state becomes
`FINDING_MATCH_PENDING`. That is wrong: the Finding has already matched the newer assessment, and this revision
is simply superseded by a later recorded revision.

Reproduced on Postgres with F01 and F04: pinned r1 gave `revision.currentness FINDING_MATCH_PENDING`, while the
same body says `state.projection CURRENT` and `claim_is_current True`. A phase-3 page pinned to r1 would show
"assessment newer than the Finding" next to "current claim". That is a misleading state on exactly the
old-revision URL the owner walkthrough shows.

Fix: for `selected is not latest`, report e.g. `SUPERSEDED_BY_LATER_REVISION` with `latest_revision_id`, keep the
per-window detail, and make the top-level `claim_is_current` explicitly the Finding's (latest) state, not the
pinned revision's. Add an assertion on the pinned F04 r1 body.

### C1 (carry): Q19, the read is not behind the Performance cutover gate
`finding_api.py:72-76`, `main.py:339-344`. The default is defensible for the claim itself: no file-backed Finding
detail is being cut over, and currentness catches model and config changes. But the gate also enforces
lineage-break and other-model-head checks (`performance_comparison.py:201-208`) that the Finding read does not.
The Finding body also emits `links.assessment_revisions` and `links.windows` to
`/api/sites/{code}/performance/dispatch/...`, which return 409 `PERFORMANCE_CUTOVER_CLOSED` while the gate is
closed, so drill-down breaks silently.

Minimum before phase 3: report the gate's `permitted`/`reason` in the Finding body and mark those links as closed
when it is shut, or gate the Finding read. Architect to rule.

### C2 (carry): Q17, the stop bridge only partly meets the Q11 rule
`finding_episode.py:233-242`. The default is safe against false claims, since a bridge adds 0 Candidate minutes.
The worst case is joining two episodes that a contrary report should have separated: a lost recurrence, not a
false Candidate.

The question overstates the cost of failing closed. The window result already carries timed generator cohort
limits and `GENERATOR_SERIES_AMBIGUOUS` (`dispatch_v3.py:526-548`), and `WindowBasis.window_claim` is already
loaded. The matcher could refuse an `OBSERVED_STOP` bridge over a window that is INDETERMINATE or has a generator
limit overlapping the stop, with no S3 model change. Recommend that rule. Architect to rule before I-S4-01
closeout.

### C3 (carry): Q16, the access seam admits everything by default
`finding_api.py:29-30`. 401 and 403 only come from a test-injected seam. The default admits any caller for any
Site of the configured tenant. This is parity with S3 Performance, Site resolution stays inside the configured
tenant via `ledger_scope` (no client-supplied tenant, no global authority), and `access_basis` is in every body.
Safe for development. It must be replaced before any non-development exposure. Accept the default.

The 401/403/404/503 matrix is tested for `/findings/{id}` only. The extra `/finding-windows/{day}` route has no
matrix test (`test_s4_finding_api.py`).

### C4 (carry): Q20, relation records sit outside every digest
`claim.continuity` and `claim.recurrence` are in the immutable revision row but in neither `support_sha256` nor
`basis_sha256`. OFF evidence IDs are resolved at read time by role and exact instant
(`postgres_finding_store.py:282-290`), which may list a non-OFF generator report at the same instant. The claim
schema grew without a `MATCHER_VERSION` bump (`finding-episode-1`). Acceptable as the default. Phase 3 should
label OFF evidence as "reports at the recorded OFF time".

### C5 (carry, low): merge canonical is one hop
`finding_read.py:175, 218`. `canonical_finding_id` follows one `finding_merge` row. If a canonical is later itself
merged, the superseded Finding points at an intermediate MERGED Finding. Resolve the chain, or assert that it
cannot happen.

### C6 (carry, low): window read cost and boundary
`postgres_finding_store.py:297-312`. `findings_over` loads the latest revision of every Finding on the Site and
filters in Python, with one query per row (N+1), and `lo <= episode_end` counts an episode ending exactly at
midnight as overlapping the next day. Phase 3 also calls the S3 window read once per cited window
(packet-named). Fine at fixture scale; S4-04 should replace it.

## What I verified

- **Route scoping:** Site resolution goes through `registry.ledger_scope`, the same as Performance. Every store
  query filters `tenant_id`/`site_id`. A revision of another Finding is 404, because it is looked up within this
  Finding's revisions only. Malformed IDs are 422.
- **Revision pinning:** omitted `revision_id` gives the latest recorded revision, and an exact ID pins it. There
  is no `knowledge_at` parameter, and `selection.replay` says so.
- **Currentness:** it uses the revision's own WINDOW citations, which meets the phase-1 carry. The mislabel on
  non-latest revisions is B2.
- **States:** MERGED gives `MERGED_INTO_CANONICAL` with `claim_is_current` false. UNCONFIRMED and
  NO_LONGER_SUPPORTED are kept separate from projection. `BASIS_REFRESHED` revisions each keep their own ID with
  `support_changed:false`, `revision_groups` is only a hint, and `revisions` is never squashed.
- **Read-only:** the new store methods run in REPEATABLE READ read transactions. The architecture guard flags a
  write in `finding_read.py`; that is the packet's proof, and I did not rerun it.
- **Provenance:** `PROVENANCE_STATEMENT` keeps manifest case labels apart from central gateway, source, epoch and
  batch provenance. A gateway case is labelled only when it is opt-in `gateway_sealed` and not `fault_fixture`.
- **Typed unavailable:** money, recommendation, Evidence tab, History tab, Site list and control route are all
  present.

## Checks run by this reviewer

- `tools/check-architecture.ps1`: Architecture check passed.
- `tools/check-agent-workflow.ps1`: Agent workflow check passed.
- `pytest backend/tests/test_s4_finding_api.py backend/tests/test_s4_finding_episode.py`: 27 passed.
- Two scratch Postgres probes (B1, B2) in isolated `assetops_s4p2rev_test` on the Compose Postgres (55432). The
  database was dropped afterwards; probe files live only in the scratchpad.

## Not verified

- The full backend, host, gateway and simulator suites, check-all, and the producer run with VERIFY PASSED. These
  are the packet's numbers, taken as reported; per the dispatch, I did not rerun them.
- Frontend: no frontend change, so no frontend checks were run. Layout evidence is not applicable (no UI).

## Residual risk not named in the packet

B1 is reachable with the committed fixture (F08, 10-19), and the existing test cannot catch it. The pinned-URL
mislabel (B2) sits on the exact path the owner checkpoint will exercise.
