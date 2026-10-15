# S6-01b phase 1 - independent review

Reviewer: fresh Claude reviewer (did not author S6-01b). Worktree `AssetOpsV1-review4`, branch `review/S6-01b-phase-1` at `21aabfed`; diff `c341599b..21aabfed` (frontend only, plus task status and missing-claim baseline).

## Verdict

**Accept with M1 fixed on the branch** (can ride with phase 2). L1-L5 are Low and do not block.

The core of the phase holds: commands render only on a server grant (`allowed === true` and the command), every control and actor is labelled SYSTEM demonstration, "already accepted" (409 `ACTION_ACCEPTANCE_CONFLICT` + `action_id`), FAILED-stays-pending, same-key replay, and `ACTION_ALREADY_APPLIED` ("nothing was attempted") are each shown truthfully; the selector rides every section link and reload; both selectors show the typed 422 with two explicit choices; events render in server order with both timestamps on the backdated OBSERVED; no Action revision is invented; money is a link with no amount; no savings, approval or Lab-effect claim.

## Findings

### M1 (Medium) - an unknown `event_id` on a real Action is shown as "Action not found"

- Where: `frontend/src/sites/actionPresentation.tsx:118-133` (`RefusalPanel` heading/text for 404), reached from `frontend/src/sites/SiteAction.tsx:142-153`.
- What: the server answers `?event_id=<unknown>` with 404 `ACTION_EVENT_NOT_FOUND` / "No such event for this Action." (fixture `action-history:1#a/unknown_event_404`). The panel heading is "Action not found" and its first sentence is "This site has no such action.", followed by the server's correct code and reason, so the page contradicts itself and asserts that an existing Action does not exist. The body-null branch also offers no way back to the latest record (the section links keep the bad selector).
- Why it matters: the brief requires every refusal to be stated truthfully; a stale or hand-edited event link is the ordinary way to reach this. The recorded fixture case exists but is not tested.
- Fix: for `ACTION_EVENT_NOT_FOUND` (or any 404 while a selector is present) say the event/cutoff was not found for this Action and link to the latest (`links.view(view, LATEST)`); add a test serving `unknown_event_404` (and the events read's 404) asserting the heading and the latest link.

### L1 (Low, test teeth) - the `effective_from` default is not pinned

`SiteAction.tsx:345-349` is correct today (next UTC midnight after `read_at`, never backdated by default), but the apply test only matches `/T00:00:00\+00:00$/` (`siteAction.test.tsx:358`). Mutation `getUTCDate() + 1` -> `- 1` (a backdated default) survives all 22 tests. Assert the exact value `2026-11-02T00:00:00+00:00` (the fixture's own apply request) and that it is after `application_basis.read_at`.

### L2 (Low, test teeth) - the exact-command half of `granted()` is untested

Mutation removing `&& capability.command === command` (`actionPresentation.tsx:85`) survives. The server keys capabilities per command so the risk is small, but Q4 says "exact command"; one test with an allowed capability for a different command would pin it.

### L3 (Low) - Apply can be a silent no-op

`SiteAction.tsx:376`: if `application_basis` is null or its `current_foundation_revision_id` is null, the Apply button still renders and clicking it does nothing (only "Expected current Foundation version none" is shown). Hide the control with a read-only reason in that case.

### L4 (Low, packet accuracy) - test derivations understated, one comment wrong

The file header and handoff say two bodies are derived. There are more, undeclared: `accepted_pending` served with `events_latest.slice(0, 2)` under a LATEST 6/6 selection (`:326`), `accepted_pending` with the denied capability spliced in (`:390`), and a synthetic 503 `STORE_UNAVAILABLE` (`:368`). The `:389` comment says "The recorded denied read is of an applied Action"; the recorded `action-overview:1#a/capability_denied` is PENDING with one event, so it could be served as recorded. The documented ACCEPTED-event derivation is faithful in `events` and `selection` (the server's events prefix through ACCEPTED is exactly `[ACCEPTED]`, matching `events_event_id_observed`'s prefix behaviour) but carries the latest read's APPLIED `state`; the UI does not render `events.state`, so no assertion is wrong. Declare the derivations, fix the comment, and prefer the recorded denied read.

### L5 (Low, coverage) - recorded cases not exercised by the UI tests

`unknown_event_404` (see M1), `apply_wrong_site_404`, `apply_invalid_value_failed`, `apply_no_change_failed`, `apply_backdate_failed`, `accept_replayed`, `latest_revision_after_apply`, and the `links.recommendation` absent branch of `SiteFinding` "What to do next". They go through the same generic paths as tested cases, so this is coverage, not a defect; phase 2 can add the 422 FAILED variants cheaply.

## Focus items checked

- **Grant guard**: `granted()` requires `allowed === true` and the command; Recommendation uses the ACCEPT capability, Application uses `system_demo_capability.apply`. Absent and denied are read-only with the server reason at both widths (jsdom width only; rendered layout is phase 2). Apply is additionally hidden on non-LATEST selections (the as-of reads carry `allowed: true` and `PENDING`, so this matters) and once APPLIED.
- **Labels**: "Accept trial (SYSTEM demonstration)", "Apply trial (SYSTEM demonstration)", panel headings, actor column; no operator approval wording (test asserts `/approv/i` absent).
- **Refusals/replays**: 403 denied, 409 stale + FAILED (first and same-key replay), 409 already applied (no FAILED), 409 already accepted with `action_id` link, read failure keeping the last good read - all shown typed. Exception: M1.
- **No effect claims**: Overview/Apply/Change copy says no effect or saving is stated or measured; outcome is "Pending. Nothing has been verified yet". "Applied to the Site Foundation" describes the configuration publish, which is true.
- **Money**: a labelled link to the Finding's financials at the exact revision, no amount, "The trial predicts no saving".
- **Selectors**: carried in every section link, both reload tests, row links for event and cutoff, 422 conflict with two single-selector links and no preference.
- **Order and backdated OBSERVED**: server order rendered without re-sorting; recorded and happened columns with "(recorded later than it happened)".
- **No invented revision**: none rendered.
- **Vocabulary**: "Application" for `execution` (banned word in `productVocabulary.json`), URL segment kept; own limitation copy matches the server's `POLICY_SENSITIVITY_TRIAL_ONLY` text except "running" -> "generator time", unknown codes fall back to server text. Honest.
- **Missing-claim baseline**: the removed entry's text was removed from `SiteFinding.tsx` and replaced by a real link to a delivered view; total 12 -> 11 is justified.
- **`effective_from` default**: next UTC midnight after server `read_at`, editable, never backdated by default; the server still rejects a backdated or past value with typed 422 (+FAILED), which the UI shows. Acceptable (L1 for test teeth).

## Checks run (this review, on `21aabfed`)

- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run` siteAction, siteFinding, foundationScreen: 3 files, 102 passed.
- siteFindingHistory, siteFindingEvidence, siteFinancials: 3 files, 79 passed.
- siteFindingEvidence, t028Screens, t028Vocabulary, siteDetail, cockpitLayout: 5 files, 112 passed.
- `tools/check-agent-workflow.ps1`: passed.
- `tools/check-architecture.ps1`: passed (temporary `.venv` junction to the main checkout, removed afterwards).
- Mutations (both reverted, tree clean): backdated default and command-agnostic grant each survived all 22 siteAction tests (L1, L2).
- Not run: full frontend suite, `npm run build`, backend tests (no backend change; the contract fixture was read directly and the UI shapes match it), layout evidence (phase 2; not claimed by the handoff).

## Residual risk

- Action CSS classes have no rules yet; the side-by-side "pairs" stack as blocks until phase 2.
- A page left open across UTC midnight keeps a now-past default `effective_from`; an Apply then records a FAILED attempt (typed, honest, but audit noise).
- The Recommendation for a newer Finding revision (`latest_revision_after_apply`) is AVAILABLE with an ACCEPT grant and does not mention the Action already accepted on the earlier revision; this is server behaviour from S6-01a, displayed faithfully, worth the owner seeing in the walkthrough.
