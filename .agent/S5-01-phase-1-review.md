# S5-01 phase 1 - independent review (scoped selected-window Overview read)

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review2`, branch
`review/S5-01-phase-1` at `91415b18`. Diff reviewed: `3b360af5..91415b18`, S5-01 part only (LR-01 underneath).

## Verdict

**Accept with findings fixed on the branch.** M1 and M2 are small fixes to the pin path in `site_overview/read.py`.
M3 needs an Architect ruling before the phase-2 owner walkthrough, but it does not block building phase 2.
The money composition fails closed in every case I traced. Gate order is correct, and a closed Performance
gate cannot bypass S2. The `main.py` move changes no other route.

## Findings

### M1 (Medium) - a pinned Finding is not checked against the selected day
`backend/assetops_backend/site_overview/read.py:147-149, 208-220`. `_pin` checks tenant and Site scope only. The pin
is then retained as the day's `known_finding` while discovery is incomplete or the source is closed, even when its
episode does not intersect the selected day. Probe result: with a pending S4 match on 2026-10-24, a pin of a Finding
whose episode is 2026-10-19 00:00-02:00Z comes back as the 10-24 `known_finding`, with `selected_by:
PINNED_RETAINED_WHILE_BASIS_INCOMPLETE` and money `UPSTREAM_PENDING`. Source-closed behaves the same way.

**Why it matters:** phase 2 writes `finding_id`/`finding_revision_id` into the URL. On a date change the old day's
pin rides along, and an incomplete basis on the new day is common (unassessed, pending, stopped schedule). The card
for the new day would then name another day's Finding. That breaks the ruled one-Finding-per-selected-day contract
(`D-2026-10-15-s501-finding-choice`). It is not a tenant leak, because the scope check holds.

**Fix:** in `_pin`, require `intersects(rev.episode_start, rev.episode_end, start, end)` for the pinned revision.
If it fails, drop the pin and report it, for example `previous_pin {finding_id, reason: "NOT_IN_SELECTED_DAY"}`.
Add a unit test.

### M2 (Medium) - while the source is closed, a pin with only `finding_id` resolves the latest revision
`read.py:216` (`revisions[-1] if rid is None`); `test_s5_overview_read.py:251` encodes this behaviour. The packet says
to reuse the Finding source-gate pattern: a closed source permits pinned audit material and no unpinned current
claim. `finding_api.py:115-117` answers 409 `PERFORMANCE_CUTOVER_CLOSED` for a Finding read with no `revision_id`
while closed. S5 instead serves the latest revision ID, its episode, the head consequence ID and the eligibility
lineage. Also while closed, `known_finding.excluded` and `several_intersect` (`read.py:196-198`) come from the
unpinned *current* discovery.

**Fix:** while `source_open` is false, honour only an exact `(finding_id, finding_revision_id)` pin. For an ID-only
pin, return no `known_finding` plus a typed reason, or the Finding API's 409. Blank `excluded`/`several_intersect`
when the pin is retained. Update the test at line 251.

### M3 (Medium, route to Architect) - authored P02 demonstration money has no demonstration label
`read.py:251` uses `demonstration_case`, which reads only `s4-power-demo-cases-v1.json` (P01, KOBO-001, 2026-10-23).
P02 (`s4-power-late-demo-cases-v1.json`, KOBO-001, 2026-10-24) is also authored demonstration content. For P02,
`demonstration_case` returns `None`, so provenance counts as "resolved". `test_s5_overview_postgres.py:170-182` proves
P02 reaches `PRICED` 15.82 with `money.demonstration` = null. The packet walkthrough has the owner see P02's new
current amount after `tick`.

This gap sits in the shared label (LR-01/S4-02b), not in an implementer error. The packet only names P01, and N2 only
covers the unverified case. The S4-02b owner ruling, however, requires authored content to be visibly labelled.

**Fix:** needs a decision. Either extend the provenance input to declare the LR-01 late spec, or treat it as
`MIXED_OR_UNKNOWN_SOURCE` until S4-05. Resolve this before the phase-2 owner walkthrough.

### Low

- **L1 - typed-error regression on the existing route.** `route.py:222` calls `scope()` outside any handler. A
  Foundation-store outage (`SiteStoreUnavailable`) now returns **500** for legacy and imported Sites alike. Before,
  `site_or_404` returned a typed **503 `SITE_STORE_UNAVAILABLE`**. Probe: before 503, after 500. Fix: wrap `scope`
  and map the error to the same 503. This is cheap, so fix it in the same round.
- **L2 - `except LookupError` is too broad** (`route.py:246`). `KeyError`/`IndexError` are subclasses of
  `LookupError`. Probe: a missing `schedule` key in the seam result returns 404 `FINDING_PIN_NOT_FOUND`, message
  `'schedule'`, with no pin present. Fix: raise and catch a dedicated `PinNotFound(LookupError)`.
- **L3 - `previous_pin` is not fully honest** (`read.py:199-200`). The reason is always `BASIS_CHANGED_CHOICE`, even
  when the pin never was the choice. When settled discovery finds nothing, the pin is dropped silently (`ABSENT`, no
  `previous_pin`). A same-Finding pin on a different revision is replaced without a note. M1's fix should set these
  reasons properly.
- **L4 - "one seam per process", disposal.** `SiteOverviewRead.dispose` (`read.py:90-91`) disposes only the
  upstream seam. `composition.py` also builds a second `ConsequenceReadService` (consequence store, assumption store,
  and the eligibility gate's dispatch read and Finding store) and a second `PostgresFindingStore`. Each lazily owns an
  engine that is never disposed at shutdown. Fix: reuse `upstream.consequence_read` and `upstream.findings`, or
  `release(...)` them in `dispose`.
- **L5 - the closing fence comes before the Finding and money reads.** `fp_after` (`read.py:116`) is taken before
  `finding_detail`, `_pin` and `consequences.read` (`:141-159`). The head fence (seam head == exact head, same
  revision) and `is_latest` keep an amount consistent with the seam snapshot, so this is not a mixed-CURRENT hole.
  The packet wording ("before/after composition") is still only partly met. Either document this or move `fp_after`
  after `_money`.
- **L6 - proof gaps against the phase-1 row.** These are named as *Postgres* cases but proved only with fakes
  (deviation 7): exact-midnight end, merge-superseded, several Findings, unknown minor unit, failed upstream, moved
  selection/head. I judge the risk low. The fakes match the real adapter shapes I checked (`finding_detail`
  `relations.merged_into` at `postgres_finding_store.py:259-262`, and `findings_over`'s closed lower test at `:428`,
  which S5 re-filters). The packet asked for Postgres proof, so record this as an accepted deviation or add a merge
  and midnight case to the Postgres walk in phase 2. Also untested:
  - the S2 "no comparison reader" 409 path (`imported_reads=None`) at the route;
  - legacy `date=` through the route (only the helper function is tested);
  - a foreign-tenant Site Overview read beyond the pin 404.

  The handoff line "Focused and adjacent tests ... see the result below" has no result under it.
- **L7** - `read.py:142` labels a seam Finding that `finding_detail` cannot find as `SUPERSEDED_BY_MERGE`. It
  should get its own reason.

## Focus items judged

- **Fail-closed money:** sound. `PRICED` requires all of: source open; upstream `CURRENT` (consequence-only codes fall
  through, and `money_state.py:101` still blocks non-CURRENT); fences unmoved; raw gate `ELIGIBLE`; latest revision,
  not merged; exact read `CURRENT`; head == seam head on the same revision; quantity and price present;
  `ROUNDED_OUTWARD`; provenance resolved; and `presented_as_current && current_amount_shown`. The provenance
  exception is M3.
- **Gate order:** access 401/403, then scope, then S2 409 (an absent reader is also 409), then day 422, then pin 422,
  then 503 when there is no DB, then the Performance gate, then the read. A closed Performance gate cannot bypass S2,
  because S2 runs first and the gate is never called (`test_route_s2...` asserts `calls == []`).
- **Finding choice:** half-open intersection, merge exclusion, no lifecycle filter, greatest start then smallest
  UUID - correct. Pin handling: see M1, M2, L3.
- **Fingerprint:** sound for an append-only accepted ledger. It is the ID set plus count over the S3 bracket with the
  same overlap test, and heartbeat time is not used. Timing: L5.
- **One service per process:** one `SiteOverviewRead` and one upstream seam, disposed at shutdown; leak noted in L4.
- **`main.py` move:** no behaviour change for other routes. `performance_gate` is the same closure, and every object it
  captures (`assessments`, `lineage`, reports) is defined before it. The Performance and Finding routers receive the
  same objects. Legacy Overview and app tests pass (below). The one route-level change is L1.
- **Dependency guard:** it has teeth. Adding a foreign `scheduling.composition` import to `money_state.py` failed
  `check-architecture` with the S5 message; reverted.
- **Deviations:**
  1. Accepted, with M1, M2 and L3 fixed.
  2. Accepted. It is proved on Postgres: a stopped schedule leaves the raw gate `ELIGIBLE` and the state
     `UPSTREAM_STALE`.
  3. Accepted, and it follows packet precedence. The owner walkthrough wording must name both states.
  4. Accepted.
  5. Accepted.
  6. Accepted for the unverified case; M3 for P02.
  7. See L6.

## Checks I ran (this worktree, `assetops_backend.__file__` confirmed in `AssetOpsV1-review2`)

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `pytest test_s5_overview_read.py test_s5_overview_postgres.py` on private DB `assetops_s501rv_test`: **28 passed**
  (38.8 s).
- Adjacent, `-n 2 --dist loadfile`: `test_s4_schedule_health_postgres`, `test_s4_consequence_read`,
  `test_s4_evidence_consequence_work_postgres`, `test_lr01_cohort_v4`, `test_lr01_money_eligibility_postgres`,
  `test_s2_site_evidence_postgres`, `test_s3_dispatch_read_postgres`: **87 passed** (240 s).
- Legacy Overview and composition (no DB URL): `test_t027_overview`, `test_s1_cutover`, `test_sites_api`,
  `test_health`: **107 passed**.
- Behaviour probes, using fakes from the unit test module, run from scratchpad: M1, L1 and L2 confirmed as described.
- Guard mutation as above, reverted. The worktree is clean apart from this file.
- Review DBs dropped (`assetops_s501rv_test`; none left).

## Not verified

- I did not run the full backend suite; phase 1 has none by plan. The full suite is due in phase 2.
- No frontend changes are in phase 1, so I ran no frontend checks. Layout evidence is not applicable yet.
- The implementer's 9 mutation results: I did not rerun them; I spot-checked the guard only.
