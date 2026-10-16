# S5-02 slice review - Finding list in the Site Overview

Reviewer: fresh Claude reviewer (did not author the slice). Reviewed revision `10e804f8` (head of
`task/S5-02-overview-finding-list`), diff `git diff a88d3e8a..HEAD -- ':!.agent'`, against
`tasks/S5-02-overview-finding-list.md`, Architect `D-2026-10-16-s502-parity` (`.agent/architect-S5-02-answers.md`),
`.agent/S5-02-plan-review.md`, `.agent/S5-02-build-brief.md`, `.agent/S5-02-review-packet.md` and
`.agent/S5-02-owner-walkthrough.md`. Wording and visual polish are out of scope (W1-conclusion task).

## Verdict: RETURN (one Medium)

The slice is sound apart from one point. Count and empty claims are gated on the index's own `CURRENT`/`is_current`
read with a count. Refusals and non-current reads show no rows and no count. An older day's late answer is dropped.
Links open exact revisions. Enter, Back, reload and the full-list link all behave as specified. There is no backend
change, and the S5-01 and S4-04 suites still pass. The one Medium is a parity claim that the ruling's literal text
excludes, and the live walkthrough makes that claim. It can be fixed with a one-line code gate, or with an Architect
confirmation of the ruling's meaning plus a disclosure in the packet. Either one closes it.

## Findings

### M1 (Medium; ruling conformance, fail-closed) - parity says "same" while the Overview reports itself not current

`frontend/src/sites/OverviewFindingList.tsx:65-111` (`compareParity`) checks that the index is `CURRENT`/`is_current`.
It also checks that the card is `DISCOVERED`, that `source_open` holds, that `audit_only` is not set, and the
intersections and the comparable fields. It never reads `summary.freshness.state`. `D-2026-10-16-s502-parity`
paragraph 2 says: "If **either read is non-current**, the Overview choice is a retained pin, comparable fields are
missing or differ, or the IDs differ, show each read's own basis and a reload affordance without a parity claim."

- Scratch unit check (written to the worktree, run, then deleted): a `day()` summary with
  `freshness.state = "STALE_PROJECTION"`, a `DISCOVERED` card, an open source and an aligned index body returns
  `{ state: "same" }`.
- In the live walkthrough I reproduced, the positive day 2026-10-15 Overview reads `freshness.state = STALE_PROJECTION`
  (reasons `CONSEQUENCE_PENDING, WORK_OUTSTANDING, SCHEDULE_STOPPED, SITE_NOT_OBSERVED`). The panel still shows
  `data-overview-finding-parity="same"` ("the same Finding version ... on the same assessment and matching basis").
  This happens both before and after `settle`. The packet records "live positive `same`" as Met and does not mention
  that the Overview read beside it is not current.
- Why it matters: the page claims equality next to a freshness strip that calls the Overview not current. The ruling
  names "either read non-current" as a no-claim condition separate from the retained-pin and differing-field
  conditions. The backend can choose `DISCOVERED` while the Overview is stale for other reasons
  (`read.py:157-177`: `moved`/fingerprint error, or upstream non-current). None of the compared fields detects an
  accepted-source move, and the ruling forbids comparing the fingerprints.
- Fix: either (a) add `summary.freshness.state !== "CURRENT"` as a not-compared reason, add a focused UI test, and
  update the walkthrough's expected "same" step, which can no longer show "same" while no schedule runs; or (b) get an
  Architect confirmation that "non-current" for the Overview means only the paragraph-1 conditions (`DISCOVERED`
  under an open gate, comparable S3/S4 fields equal), and record that and the live STALE_PROJECTION context in the
  review packet. This is an acceptance gap against the ruling text, not a preference. Option (b) is a decision for
  the Architect, so it is not mine to make.

### L1 (Low) - a positive count with an empty first page would read "Showing the first 0 of N"

`frontend/src/sites/OverviewFindingList.tsx:207-244`. If a `CURRENT` read has `total_count > 0` and `rows` is empty
(a malformed or racing page), the panel states the count with no rows. That count is still the index's own current
count, so this is not fail-open. A guard that routes `rows.length === 0 && total_count > 0` to the "incomplete" state
would mirror the zero-count guard at `:190`. Non-blocking.

No other findings. Request scope (served `window.start/end`, domain, limit 2, cursor null), legacy isolation
(`SiteWindowOverview.tsx:632` renders the list only for imported summaries when the shell supplies both the client
and `findingList`), stale-response suppression (the `active` flag plus key check, `OverviewFindingList.tsx:276-296`),
the zero-claim guard (`:188-205`), refusal mapping, and the reload (`SiteOverview.tsx:118-123` clears `result`, which
remounts the list and re-reads the index) all match the packet.

## Checks run (this worktree, revision `10e804f8`)

- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run` on s502OverviewFindingList, s5SiteWindowOverview and s404SiteFindingIndex: 3 files, 65 tests
  passed (22/28/15). Vitest ran fine here; the known esbuild sandbox failure did not appear. I did not run the full
  frontend suite or `npm.cmd run build`, so the packet's 1594-test and build numbers are not independently verified.
- S5-01 test diff: 14 cases before and after. One assertion changed from the placeholder text to the list's no-claim
  state, which is the intended replacement.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
  `check_v69_dependency_registry.cjs`: exit 0.
- No change under `backend/`, `gateway/`, `contracts/` or `simulator/`, so no backend suite was run (per the packet).
- Walkthrough on a private fixture (`assetops_s404_owner_s502rv`, `var/s404_owner_s502rv`, API 8962, web 5462,
  CDP 9462; `kobo-001.yaml` copied in and removed): `prepare` ended with `0 Overview check(s) failed` and
  `positive_parity.equal: true`. Evidence script results: `initial` 60/60, `late` 8/8, `settled` 8/8 (parity `same`,
  first row now the late Finding), `closed` 16/16, then `gate --open`. After that, `drop` dropped the DB and work
  folder, and I removed the copied yaml. The owner steps were reachable as written, adjusted only for the DB name and
  ports.
- Screenshots exist locally (`%TEMP%\s502rv-evidence`), but I did not compare them visually against the mock (visual
  review belongs to the owner).

## Residual risk not named in the packet

- Every live "same" observation was made while the Overview read was `STALE_PROJECTION` (see M1). The walkthrough
  never shows parity beside a `CURRENT` Overview.
