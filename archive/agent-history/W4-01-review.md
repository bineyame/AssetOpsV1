# W4-01 independent review (first review): work-case core and thin Site lists

Branch `task/W4-01-work-case-core`, head `afa35e79` (code `0e77205d` plus the packet). I read it through git objects only.
I did not modify the review5 worktree or run tests in it. Authority: `tasks/W4-01-work-case-core.md`,
`.agent/W4-01-build-spec.md` (closures 1-3, q1-q7, the commit-4/5 dry-reads), the packet, the v69 mock
(`screens.js:186-195`, `tabRow` at `:956`) and the captures in `.agent/W4-01-evidence/`.

## Verdict: REVISE

The backend core is sound and follows the spec closely. The migration, the sole writer, the clocks, the refusal
order, the pins, the cursor and fence, and the W3 reuse all check out (details below). The UI has three user-visible
departures from the mock that no ruling covers (High under ROLE_CONFIG "Mockup drives the design"). There is also a
set of unruled builder decisions (Medium). The two q8 items with the Architect, the check-all failures and the
registry panel paths, also block merge. I note them below but do not rule on them.

## Findings

### High (user-visible, differs from the mock, no ruling)

**H1. The Work subtabs drop the mock's counts.** `frontend/src/shell/SiteAnalyticsFrames.tsx` (Work subrow). The
mock renders `Actions (2) · Incidents (0) · Maintenance (0)` (`screens.js:956` `scope-count`; captured in
`evidence.json` `subrow.labels`). The app renders `Actions · Incidents · Maintenance`. This is commit-5 reading 4, and
no ruling covers it. The spec slot table lists only the bare labels, so the Architect may simply confirm the
omission. Failure scenario: a user on the live Incidents tab cannot see how many cases sit behind Maintenance. Every
other v69 scope-count is shown, so this subrow is now inconsistent with the rest. Fix: either an Architect ruling
that records the omission as an honest gap, or counts from the full `total_count` of each list (Actions already has
one).

**H2. The empty block drops the mock icon.** `frontend/src/sites/siteWorkCases.tsx:559-562`. The mock's `empty()`
is `icon('evidence')` + h3 + p (`screens.js:43`). The spec says "Keep mock empty block". This is commit-5 reading 5,
justified by the "svg guard". The guard does not force this: `tools/checks/shell-overflow.ps1` allows fixed-size
icons from `frontend/src/ui/RailIcon.tsx`, which already has an `evidence` path. Failure scenario: the
empty-incidents capture (`sitework-incidents-empty-1440-app.png`) and the mock differ in the panel's primary visual.
Fix: render `<RailIcon name="evidence" />` (or get a ruling).

**H3. The status strip gains a fourth slot whose copy no ruling or reading covers.** `siteWorkCases.tsx:202-215,
233-237`. The mock strip has three parts: lead, detail, Manage. The app inserts a status phrase, `Read in full`, in
every normal (CURRENT) state. It is visible in all four stocked and empty captures. The spec maps `status` to the
strip but gives no copy, and the packet's readings do not list this phrase. Failure scenario: every user sees
`Read in full` beside `Scoped to Kobo · 7 incidents`. That suggests completeness of evidence when it describes only
the link status, and it is not in the mock. Fix: Architect copy for each status (or no visible word for CURRENT),
then amend the spec.

### Medium (unruled implementer decisions, or acceptance gaps)

**M1. Page two flips the visible status.** `siteWorkCases.tsx:495,509,519` (commit-5 reading 7). Next and Previous
send an explicit `known_at = body.known_at`, so the server returns `HISTORICAL`
(`site_index.py:307,323-324`). The strip then changes from `Read in full` to `Read as of 2026-...` while the user is
still paging through one snapshot, including after Previous returns to page 1. Ruling r4 allows omitting `known_at`
on page two (the cursor binds K), and that keeps `CURRENT`. Fix: omit `known_at` when a cursor is present, or get a
ruling.

**M2. The spec-named fixture artifact is missing.** The spec section "Fixture and exact test contract" and B7/B11
require `backend/tests/fixtures/w4/w401-work.json` (schema `w401-work/1`, sorted keys, final LF). The branch has no
such file (commit-5 reading 13 says "earlier commits"), and no ruling drops it. The packet also does not record
"fixture exact IDs", which the closeout requires. Failure scenario: W5/W6 consumers and the frozen contract have no
static fixture input to replay. Fix: add the file, or get an Architect ruling that the F01 harness supersedes it.

**M3. Unruled UI copy and decisions beyond H3.**
- `siteWorkCases.tsx:211`: `Linked evidence source is out of date` (reading 3).
- `:532-533`: the two CoverageLine sentences `The cases are listed in full; ...` (not declared as readings).
- `:228`: `Reading work records`.
- `:275`: refusal shows `As of: time not recorded` (reading 12).
- `:499`: `Showing {n} of {total}` for a shared cursor link (reading 6).
- `site_index.py:196`: Action label `Action {8}` (run-9 reading 1).

Each is user-visible copy that is not in the mock or the spec. Fix: Architect copy, or confirmation.

**M4. The run-9 commit-4 readings 1-5, 8 and 11 have no ruling.** The spec ends at the commit-5 dry-read. No
"Run 8/9 rulings" section exists, and none appears in `W4-01-pending-rulings.md`. The substantive ones:
- #2: fence state excludes HISTORICAL (`site_index.py:170-180`).
- #3: a lineage-valid pin whose reduced state is UNKNOWN gets a null token.
- #4: the `wce1-` basis uses the snapshot's raw state.
- #5: zero-case list provenance has `basis_sha256:null`. The literal list body shows a computed digest.
- #8: a cursor K later than the new `read_at` is 409.

I think #2 and #8 follow from r4. Each still needs a confirm line.

**M5. The cherry-picked W3 money prerequisites contradict the literal q3-6.** q3 ruling 6 says "Do not cherry-pick
the W3 money prerequisites or unreviewed estate core". The branch carries `aff24bbd` (prereq 0a,
`ConsequenceReadService.select_consequence_on`) and `9a5756f9` (prereq 0b, `MoneyEligibility.for_finding_on`):
about 400 lines plus their tests. W4 code calls neither function. The coordinator ruling (handoff, run 5) covered
only the `configuration-persistence.ps1` conflict. These commits were probably needed as ancestors of the reviewed
q5/q6 range (W3 moved them forward in its Run 6). Even so, merging W4 now ships W3 money code under W4's review. Fix:
a one-line Architect confirmation that the nine-commit range is the intended reviewed W3 unit.

### Low

- **L1.** `backend/assetops_backend/work/service.py:243-251`: `post_event` returns 409 for reserved and outcome
  kinds before it authorizes the actor (`_actor`). With an injected principal, a USER actor posting
  `OPEN_VERIFICATION` gets 409, not 403 `WORK_USER_AUTH_REQUIRED`. That departs from the q2 reading-2 order. Nothing
  leaks.
- **L2.** `postgres_work_store.py:317-318`: two identical idempotent retries that race end in a unique violation, so
  the loser gets 409 `WORK_EVENT_DUPLICATE_KEY`, not the B6 200 replay. A narrow race.
- **L3.** Residual: `recorded_at` is `command_now`, taken at the start of the transaction. A reader whose `read_at`
  falls between a writer's `command_now` and its commit can see a snapshot that later changes at the same K. This
  fails closed (409 on page two), but an explicit historical re-read at that K is not reproducible.
- **L4.** `siteWorkCases.tsx:301-313`: the "What this list is based on" disclosure shows raw `COMPLETE`,
  `(LINK_SELECTION_MISSING)` and the `sha256:` fence. That is system vocabulary under the client-facing rule. It can
  go to the W1 UX pass.
- **L5.** Residual: under q6-2 every KOBO case that pins a mini-grid Finding lists `UNKNOWN`. The strip then says
  `No selected source for linked evidence` and the CoverageLine repeats it. The owner will see this on the primary
  positive path. It is ruled behaviour, but the owner walkthrough should be told.
- **L6.** The packet neither runs `tools/layout-evidence.mjs` nor records it as `not run` with its precondition
  (standing reviewer brief). The bespoke `capture.mjs` evidence (126 checks) is good, but the omission should be
  recorded.

## Verified (no finding)

- **Migration 0027.** It is byte-identical to the spec literal (non-blank lines diffed): 11 tables, 11 append-only
  triggers, 7 explicit indexes, 1 sequence, 1 function. `down_revision="0026_w2_ev_money"` is the only child of 0026,
  so there is one head. The downgrade refuses non-empty tables and drops in dependency order. The upgraded-head
  literals change only where they assert the head.
- **Append-only, sole writer.** `postgres_work_store.py` is INSERT-only, with one statement per table for all 11
  targets. Rule 8 passes (run by me, below). `postgres_work_read.py` reads under `SET TRANSACTION READ ONLY`.
- **Clocks.** `test_db_clock_override` and `test_read_clock_override` are constructor-only. `git grep` finds them
  only in their own adapters. `composition.py` and `main.py` never pass them, and `main.py` injects no principal, so
  every write is 403. One `command_now` per command survives a SERIALIZABLE retry and is bound to every
  `created_at`/`recorded_at`.
- **Authorization and refusal order** (`work_api.py:71-95`, `service.py`): access 401/403, then scope 503/404, then
  write grant 403, then principal 403, then closed shape 422, then USER 403, then attestation 422, then hash, then
  idempotent replay before the time bounds. This matches q2 reading 2, except L1.
- **Pins.** Finding pairs need `created_at <= command_now`. Action pairs are joined to their own Action, with
  `recorded_at <= command_now` (q4-2). Copied links on a correction are re-checked. Evidence needs
  `received_at <= command_now`.
- **Detail and list.** One REPEATABLE READ snapshot with one `read_at`. Every predicate cuts off at K. Incidents
  belong to the window by `occurred_at` and requests by `created_at`. The sort is time DESC then UUID ASC, and the
  keyset matches. `total_count`, provenance (with the q7-4 guard, including off-page rows) and status are computed
  over the full set before paging. The cursor binds scope, K and token; any change is 409, and a malformed cursor is
  422.
- **W3 reuse.** `PublicProvenance.cited_set`, `build_link_rows_reader`, `ColdReadService/EvReadService._snapshot`,
  `build_cold_ev_selection_pins`, `site_window_on` and `ActionIndexService.fence/index_token` are all used through
  composition. I found no copied SQL and no second DTO.
- **Guard multiset.** It drops exactly `Incidents×1, Maintenance×1`. The rail roots stay. The fixtures add two
  negatives that reintroduce each subtab.
- **UI slots.** Status, panel and notice are in mock order in every state. Headings, the five columns, both empty
  texts, subcopy, the notice, Manage text and chip tones (Incident OPEN red; S21) match the spec. The measured
  pieces are all within their caps (packet table; incidents at 390 is at 460, the cap).
- **Tests are non-vacuous.** Every spec-named backend and frontend node exists. The pending and missing branches
  are driven by real reselection and by a scoped monkeypatch of only the cutoff predicate. The jsdom tests assert
  slots, planted-panel rejection and pinned-revision hrefs.

## Builder readings: classification

- **Covered by a ruling:**
  - commit-1 #1-8, commit-2 #1-8 and commit-3 #1-6 (spec tables);
  - run-5 #1-8 (q4 table) and run-6 r1-r5 (q5);
  - run-9 #6 (q4 r7 by analogy), #7 (commit-4 dry-read), #9 ("a case needs its revision at the cutoff") and #10
    (the literal list body has no fences);
  - commit-5 #1 (the original chip-tone line, OPEN amber; S21 overrides only Incident), #2 (commit-4/5 dry-reads),
    #9 (B10/S20 disclosure), #10 (page files are PascalCase; the shared helper is not a page) and #11 (verified: no
    Site switcher exists in `frontend/src`).
- **Needs the Architect:**
  - run-9 #1-5, #8 and #11 (M3/M4);
  - commit-5 #3 (M3), #4 (H1), #5 (H2), #6 (M3), #7 (M1), #8 (layout; Low) and #12 (M3);
  - commit-5 #13 (M2);
  - undeclared: `Read in full` (H3), the CoverageLine sentences and `Reading work records` (M3), and the money
    prerequisite picks (M5).
- **With the Architect now (q8, not ruled here):**
  - q8-1: the missing-claim scan fails on `siteWorkCases.tsx:105` (notice) and `:240` (`· Not available yet`);
  - q8-2: the registry panel paths are still open. Only task tags were added.

## Checks I ran (from an extracted `git archive afa35e79` in my scratchpad; not in review5)

- `tools/check-architecture.ps1`: **passed**. Rule 8 needed `ASSETOPS_GUARD_PYTHON` pointed at the main `.venv`.
- `tools/check-agent-workflow.ps1`: **passed**.
- `tools/check-all.ps1`: **8/10**. These pass: architecture, navigation truthfulness, workflow, registry, delivery
  and mock-gap fixtures, evidence width, screen ledger. These fail: the missing-claim orphan scan and its fixture
  self-check, with exactly the two q8-1 strings. The merge-base baseline comparison was skipped in my snapshot
  (no `main`).
- `npx.cmd tsc --noEmit` (frontend): **exit 0**.
- `npx.cmd vitest run src/sites/__tests__/siteWorkCases.test.tsx`: **4/4 passed**.
- The other updated UI files (`operatorSiteTabs`, `operatorRouteFrames`, `w1f4ChangesWorkStructure`,
  `siteWorkActions`, `sourceProvenance`): 20 of 114 failed in my snapshot, all on
  `Invalid Chai property: toBeInTheDocument`. That is a jest-dom setup failure from my junctioned `node_modules`,
  not product behaviour. Their pass is **unverified** by me (the packet claims 100 passed).
- **Not run:** backend pytest (a full suite is running on this machine, and the brief forbids running tests in
  review5); `npm.cmd test` and the build; `tools/layout-evidence.mjs`. The same-revision full backend suite result is
  pending and must be cited at `0e77205d` with JUnit 0 failed/skipped before merge.
